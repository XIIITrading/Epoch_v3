# Implementation Plan: Fix Event Time Anchors

## Status: COMPLETED ✓

**Completed:** 2025-12-27

---

## Issue Summary

The `exit_events` module uses `bar.timestamp.time()` for event times instead of the backtest worksheet's `entry_time` and `exit_time`. This causes ENTRY and MFE/MAE events to display incorrect times (e.g., 16:00, 17:40 from prior-day after-hours bars) instead of the intended trade times.

**Root Cause:** The backtest `entry_time` and `exit_time` are only used to find bar indices, but event recording uses `bar.timestamp.time()` which can be from prior-day after-hours data fetched for indicator calculations.

## Affected Files

| Priority | File | Issue |
|----------|------|-------|
| P1 | `processor/exit_events/exit_event_tracker.py` | ENTRY event uses `bar_time_str` instead of backtest `entry_time` |
| P1 | `processor/exit_events/state_tracker.py` | MFE/MAE time capture uses `bar_time` from iteration |
| P2 | `processor/options_analysis/options_runner.py` | Records bar timestamps instead of requested times |
| P3 | `processor/optimal_trade/` | Downstream - reads from exit_events (auto-fixed when P1 fixed) |

## Design Principle

**Backtest worksheet is the source of truth for entry_time and exit_time.**

- ENTRY event: Always use `trade_data['entry_time']` from backtest
- EXIT event: Always use `trade_data['exit_time']` from backtest (already correct)
- MFE event: Use backtest `entry_time` + bars_from_entry to derive time, OR store the bar's time relative to entry
- MAE event: Same as MFE
- Intermediate events (HEALTH_CHANGE, etc.): Use `bar.timestamp.time()` (this is correct - represents when the change occurred)

---

## Implementation Steps

### Step 1: Fix ENTRY Event Time (exit_event_tracker.py)

**File:** `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\exit_events\exit_event_tracker.py`

**Current Code (lines 761-776):**
```python
# First bar = ENTRY event (use entry_health from entry_events)
if bar_idx == entry_idx:
    entry_event = event_detector.create_entry_event(
        trade_id=trade_id,
        entry_time=bar_time_str,  # <-- WRONG: uses bar timestamp
        entry_price=entry_price,
        health_score=entry_health,
        indicators=indicators
    )
```

**Fixed Code:**
```python
# First bar = ENTRY event (use entry_health from entry_events)
if bar_idx == entry_idx:
    # Use backtest entry_time as source of truth (not bar timestamp)
    backtest_entry_time = str(trade_data['entry_time'])

    entry_event = event_detector.create_entry_event(
        trade_id=trade_id,
        entry_time=backtest_entry_time,  # <-- FIXED: uses backtest time
        entry_price=entry_price,
        health_score=entry_health,
        indicators=indicators
    )
```

**Rationale:** The ENTRY event should reflect the intended entry time from the backtest worksheet, not the bar timestamp which may be from prior-day data.

---

### Step 2: Fix MFE/MAE Time Capture (state_tracker.py)

**File:** `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\exit_events\state_tracker.py`

**Current Behavior:** `update_excursion()` captures `bar_time` which is the bar's timestamp.

**Problem:** MFE/MAE times should be relative to the trade session, not the bar's absolute timestamp.

**Option A - Store bars_from_entry instead of time (Recommended):**

The MFE/MAE events already have `bars_from_entry` which accurately describes WHEN the extreme occurred. The `event_time` for MFE/MAE could be calculated from:
- `entry_time + (bars_from_entry * 5 minutes)`

However, this is complex and may not match actual bar times.

**Option B - Keep bar_time but validate it's from trade day:**

Add validation in `update_excursion()` to ensure the time is reasonable (within RTH 09:30-16:00).

**Option C - Pass backtest entry_time to state_tracker (Recommended):**

Modify `StateTracker` to store the backtest `entry_time` and use it as reference.

**Implementation (Option C):**

1. Add `backtest_entry_time` and `backtest_exit_time` to `TradeState` dataclass
2. Store these in `StateTracker.__init__()`
3. For MFE/MAE, use the bar's time only if it's within the trade window, otherwise derive from bars_from_entry

**Changes to state_tracker.py:**

```python
@dataclass
class TradeState:
    # ... existing fields ...

    # Backtest times (source of truth)
    backtest_entry_time: str = ""  # NEW
    backtest_exit_time: str = ""   # NEW
```

```python
class StateTracker:
    def __init__(self, trade_data: Dict, entry_health: int = 0, verbose: bool = False):
        # ... existing code ...

        self.state = TradeState(
            # ... existing fields ...
            backtest_entry_time=str(trade_data.get('entry_time', '')),  # NEW
            backtest_exit_time=str(trade_data.get('exit_time', '')),    # NEW
        )
```

---

### Step 3: Fix MFE/MAE Event Creation (exit_event_tracker.py)

**File:** `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\exit_events\exit_event_tracker.py`

**Current Code (lines 865-877):**
```python
if excursion.mfe_price is not None:
    mfe_event = event_detector.create_mfe_event(
        trade_id=trade_id,
        event_seq=state_tracker.state.next_event_seq(),
        event_time=excursion.mfe_time or str(exit_time),  # <-- Uses bar time or fallback
        mfe_price=excursion.mfe_price,
        # ...
    )
```

**Fixed Code:**
```python
if excursion.mfe_price is not None:
    # Calculate MFE time from entry_time + bars offset
    # Or validate that mfe_time is within trade session
    mfe_time_str = _format_event_time(
        excursion.mfe_time,
        trade_data['entry_time'],
        excursion.mfe_bar_index - entry_idx
    )

    mfe_event = event_detector.create_mfe_event(
        trade_id=trade_id,
        event_seq=state_tracker.state.next_event_seq(),
        event_time=mfe_time_str,  # <-- FIXED: validated/calculated time
        mfe_price=excursion.mfe_price,
        # ...
    )
```

**Add helper function:**
```python
def _format_event_time(bar_time: str, entry_time, bars_from_entry: int) -> str:
    """
    Format event time, ensuring it's valid for the trade session.

    If bar_time appears to be from after-hours (before 04:00 or after 20:00),
    calculate the time based on entry_time + bars_from_entry * 5 minutes.

    Args:
        bar_time: Time captured from bar.timestamp.time()
        entry_time: Backtest entry_time (source of truth)
        bars_from_entry: Number of bars since entry

    Returns:
        Valid event time string
    """
    from datetime import datetime, timedelta

    # Parse bar_time
    try:
        if isinstance(bar_time, str):
            parts = bar_time.replace(':', '').replace('.', '')[:6]
            hour = int(parts[:2])

            # Check if time is within valid trading session (04:00-20:00)
            if 4 <= hour <= 20:
                return bar_time
    except:
        pass

    # Fallback: calculate from entry_time + offset
    try:
        entry_dt = parse_time_string(entry_time)
        if entry_dt:
            # Create datetime for calculation
            base = datetime(2000, 1, 1, entry_dt.hour, entry_dt.minute, entry_dt.second)
            offset = timedelta(minutes=5 * bars_from_entry)
            result = base + offset
            return result.strftime('%H:%M:%S')
    except:
        pass

    # Last resort: return bar_time as-is
    return str(bar_time) if bar_time else ""
```

---

### Step 4: Fix Options Analysis (options_runner.py)

**File:** `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\options_analysis\options_runner.py`

**Current Code (lines 314-315):**
```python
entry_time=entry_bar.timestamp.strftime('%H:%M:%S'),  # bar timestamp
exit_time=exit_bar.timestamp.strftime('%H:%M:%S'),     # bar timestamp
```

**Fixed Code:**
```python
# Use backtest times as source of truth, not bar timestamps
entry_time=_format_time_for_output(trade['entry_time']),  # backtest time
exit_time=_format_time_for_output(trade['exit_time']),    # backtest time
```

**Add helper function:**
```python
def _format_time_for_output(time_value) -> str:
    """Format time value for output, handling various input formats."""
    if time_value is None:
        return ""

    if isinstance(time_value, datetime):
        return time_value.strftime('%H:%M:%S')

    if isinstance(time_value, time):
        return time_value.strftime('%H:%M:%S')

    # Handle Excel serial time
    if isinstance(time_value, (int, float)):
        total_seconds = int(round(float(time_value) * 24 * 60 * 60))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # String - clean up if needed
    time_str = str(time_value).strip()
    if ':' in time_str:
        return time_str

    return time_str
```

---

## Testing Plan

### Test 1: ENTRY Event Time
1. Run backtest with a trade having `entry_time = 09:35:00`
2. Verify exit_events worksheet shows ENTRY event with `event_time = 09:35:00`
3. NOT a bar timestamp like `16:00:00` or `17:40:00`

### Test 2: MFE/MAE Event Times
1. Run backtest with a trade
2. Verify MFE event time is within the trade session (between entry_time and exit_time)
3. Verify MAE event time is within the trade session

### Test 3: EXIT Event Time (should already work)
1. Verify EXIT event uses backtest `exit_time`

### Test 4: Optimal Trade Analysis
1. Run optimal_trade after exit_events
2. Verify ENTRY, MFE, MAE, EXIT rows all have valid times
3. No times like 16:00 or 17:40

### Test 5: Options Analysis
1. Run options_analysis
2. Verify option_entry_time matches backtest entry_time
3. Verify option_exit_time matches backtest exit_time

---

## Rollback Plan

If issues arise:
1. Revert changes to exit_event_tracker.py
2. Revert changes to state_tracker.py
3. Revert changes to options_runner.py
4. Re-run backtest pipeline

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `exit_event_tracker.py` | Use `trade_data['entry_time']` for ENTRY event; add `_format_event_time()` helper |
| `state_tracker.py` | Add `backtest_entry_time`, `backtest_exit_time` to TradeState |
| `options_runner.py` | Use backtest times instead of bar timestamps |

---

## Estimated Effort

- Implementation: 1-2 hours
- Testing: 1 hour
- Total: 2-3 hours

---

## Implementation Summary (COMPLETED)

### Phase 1 Changes (Initial Fix)

#### 1. `exit_event_tracker.py`

**Added helper methods:**
- `_format_time_for_event(time_value)` - Formats time values from various input formats (datetime, time, Excel serial, string) to HH:MM:SS
- `_calculate_event_time(entry_time_str, bars_from_entry, fallback)` - Calculates event time from entry_time + (bars * 5 minutes)
- `_interpolate_event_time(entry_time_str, exit_time_str, bars_from_entry, total_bars)` - Interpolates time between entry and exit

**Fixed ENTRY event:**
```python
# Before: entry_time=bar_time_str
# After:  entry_time=self._format_time_for_event(trade_data['entry_time'])
```

**Fixed EXIT event:**
```python
# Before: exit_time=str(exit_time)
# After:  exit_time=backtest_exit_time_str
```

#### 2. `options_runner.py`

**Fixed calculate_options_pnl call:**
```python
# Before: entry_time=entry_bar.timestamp.strftime('%H:%M:%S')
# After:  entry_time=entry_time.strftime('%H:%M:%S') if entry_time else ''
```

---

### Phase 2 Changes (v3.2.0 - Bar High/Low MFE/MAE)

**Problem:** For same-bar or short-duration trades, MFE/MAE times were outside the actual trade window because the bar-finding logic spans many bars but the trade duration is short.

**Solution:** Simplified approach using bar high/low for MFE/MAE prices.

#### 1. `state_tracker.py`

**Updated `TradeState.update_excursion()` method:**
```python
# Added bar_high and bar_low parameters
def update_excursion(self, price, bar_index, bar_time,
                     health_score=None, health_delta=None,
                     bar_high=None, bar_low=None):
    # LONG: MFE uses bar high, MAE uses bar low
    # SHORT: MFE uses bar low, MAE uses bar high
```

**Updated `StateTracker.update_excursion()` wrapper:**
```python
def update_excursion(self, bar_high=None, bar_low=None):
    # Passes bar high/low to TradeState.update_excursion()
```

#### 2. `exit_event_tracker.py`

**Updated excursion tracking call:**
```python
# Before: state_tracker.update_excursion()
# After:  state_tracker.update_excursion(bar_high=bar.high, bar_low=bar.low)
```

**Simplified MFE/MAE time assignment for short trades:**
```python
# For same-bar or adjacent bar trades (total_bars <= 1):
#   MFE time = entry_time (favorable move assumed first)
#   MAE time = exit_time (adverse move assumed before exit)
# For longer trades: interpolated times based on bar position
```

---

## Notes

- The intermediate HEALTH_CHANGE events continue to use `bar.timestamp.time()` since they represent actual state changes at specific bars
- Only ENTRY, MFE, MAE, and EXIT events use backtest time anchoring
- The `bars_from_entry` field provides the accurate bar offset and is preserved
- MFE/MAE now uses bar high/low for accurate intrabar detection:
  - LONG: MFE = bar high (best case), MAE = bar low (worst case)
  - SHORT: MFE = bar low (best case), MAE = bar high (worst case)
