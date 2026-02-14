# Implementation Plan: Win Condition Update for Indicator Analysis

**STATUS: COMPLETED** (2026-01-11)

## Objective

Update the Indicator Analysis tab to use stop-based win conditions (matching Metrics Overview), with a toggle selector defaulting to **Zone + 5% Buffer**.

## Stop Types Available

1. **Zone + 5% Buffer (Default)** - Stop at zone boundary + 5% buffer
2. **Prior M1 H/L** - Stop at prior M1 bar high/low
3. **Prior M5 H/L** - Stop at prior M5 bar high/low
4. **M5 ATR (Close)** - Stop at 1.1x M5 ATR, triggers on close
5. **M15 ATR (Close)** - Stop at 1.1x M15 ATR, triggers on close
6. **M5 Fractal H/L** - Stop at nearest M5 fractal high/low

## Win Condition Definition

**WIN** = MFE reached (≥1R) before stop hit
**LOSS** = Stop hit before reaching 1R
**PARTIAL** = Stop hit after some MFE but < 1R

## Files to Modify

### 1. config.py
- Add `WIN_CONDITION_CONFIG` with default stop type
- Add stop type display names and keys

### 2. data/supabase_client.py
- Add `fetch_stop_analysis_for_indicator_tab()` method
- Returns trade_id -> outcome mapping for selected stop type

### 3. analysis/trade_stats.py
- REMOVE `_is_winner()` function (mfe_time < mae_time)
- REMOVE temporal win condition logic
- Use stop-based outcomes only

### 4. calculations/model/win_rate_by_model.py
- REMOVE `calculate_win_rate_by_model()` (temporal version)
- REMOVE `render_model_breakdown()` (temporal version)
- Keep only `calculate_win_rate_by_model_with_stop()`
- Keep only `render_model_breakdown_with_stop()`
- Rename to be the primary functions

### 5. calculations/indicator_analysis/health_correlation.py
- Modify to accept stop-based `is_winner` values
- Remove dependency on mfe_mae_potential.is_winner

### 6. calculations/indicator_analysis/factor_importance.py
- Modify to accept stop-based `is_winner` values
- Remove dependency on mfe_mae_potential.is_winner

### 7. calculations/indicator_analysis/rejection_dynamics.py
- Modify to accept stop-based `is_winner` values
- Remove dependency on mfe_mae_potential.is_winner

### 8. calculations/indicator_analysis/indicator_progression.py
- Modify to accept stop-based `is_winner` values
- Remove dependency on mfe_mae_potential.is_winner

### 9. calculations/stop_analysis/stop_selector.py
- Already has stop type selector UI
- Ensure it's used in Indicator Analysis tab
- Verify Zone Buffer is default

### 10. app.py
- Add stop type selector to Indicator Analysis tab
- Load stop_analysis data at tab load
- Merge stop-based outcomes into indicator data
- Pass unified data to all indicator calculations

## Implementation Steps

### Step 1: Update config.py
```python
# Win Condition Configuration
WIN_CONDITION_CONFIG = {
    "default_stop_type": "zone_buffer",
    "stop_types": {
        "zone_buffer": "Zone + 5% Buffer (Default)",
        "prior_m1": "Prior M1 H/L",
        "prior_m5": "Prior M5 H/L",
        "m5_atr": "M5 ATR (Close)",
        "m15_atr": "M15 ATR (Close)",
        "fractal": "M5 Fractal H/L"
    }
}
```

### Step 2: Add data fetching in supabase_client.py
```python
def fetch_stop_outcomes_by_trade(
    self,
    stop_type: str = "zone_buffer",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch stop analysis outcomes indexed by trade_id.

    Returns:
        Dict mapping trade_id to outcome dict with:
        - is_winner: bool (True if outcome == 'WIN')
        - outcome: str ('WIN', 'LOSS', 'PARTIAL')
        - r_achieved: float
    """
```

### Step 3: Update trade_stats.py
- Remove `_is_winner()` function
- Remove `_time_to_minutes()` helper
- Update `get_trade_statistics()` to require pre-computed is_winner
- Update `get_stats_by_model()` similarly

### Step 4: Update win_rate_by_model.py
- Remove temporal functions
- Rename stop-based functions to primary names
- Update docstrings

### Step 5: Update indicator analysis modules
Each module needs:
1. Accept `is_winner` as input column (already computed)
2. Remove any mfe_time/mae_time temporal logic
3. Document win condition in docstring

### Step 6: Update app.py Indicator Analysis tab
```python
# In render_indicator_analysis_tab():

# 1. Add stop type selector at top
selected_stop_type = render_stop_type_selector()

# 2. Fetch stop outcomes for selected type
stop_outcomes = client.fetch_stop_outcomes_by_trade(
    stop_type=selected_stop_type,
    date_from=date_from,
    date_to=date_to
)

# 3. Merge is_winner into entry_indicators data
for record in entry_indicators:
    trade_id = record['trade_id']
    if trade_id in stop_outcomes:
        record['is_winner'] = stop_outcomes[trade_id]['is_winner']
        record['outcome'] = stop_outcomes[trade_id]['outcome']
        record['r_achieved'] = stop_outcomes[trade_id]['r_achieved']

# 4. Pass to all indicator analysis functions
```

## Data Flow

```
User selects stop type (default: Zone + 5% Buffer)
           ↓
Fetch stop_analysis table for selected stop_type
           ↓
Create trade_id -> {is_winner, outcome, r_achieved} mapping
           ↓
Fetch entry_indicators data
           ↓
Merge stop outcomes into entry_indicators by trade_id
           ↓
Pass merged data to all indicator analysis calculations:
  - CALC-001: Win Rate by Model
  - CALC-005: Health Score Correlation
  - CALC-006: Factor Importance
  - CALC-007: Rejection Dynamics
  - CALC-008: Indicator Progression
```

## Verification

After implementation:
1. Win rates in Indicator Analysis should match Metrics Overview for same stop type
2. Changing stop type should update all indicator analysis charts/tables
3. Default (Zone + 5% Buffer) should be pre-selected on page load

## Files to Delete (None)

All files are being modified, not deleted.

## Backward Compatibility

- NONE - completely removing mfe_time < mae_time logic
- Stop analysis table MUST be populated for Indicator Analysis to work
- Add warning message if stop_analysis data not available

## Post-Implementation Fixes (2026-01-11)

### NoneType Error Handling
Trades without stop_analysis data have `is_winner = None`. Added null filtering to all indicator analysis modules:

1. **health_correlation.py** (line 338)
   - Filter: `df['health_score'].notna() & df['is_winner'].notna()`

2. **factor_importance.py** (lines 274, 434-437)
   - Filter: `df[factor_key].notna() & df['is_winner'].notna()`
   - Pre-filter: `df_with_outcome = df[df['is_winner'].notna()].copy()`

3. **rejection_dynamics.py** (lines 277, 360, 438, 535)
   - Added `& df['is_winner'].notna()` to all health score and factor filtering
   - Filter rejection trades before exhaustion analysis
   - Filter entry_df before health score by model calculation

4. **indicator_progression.py** (line 606)
   - Pre-filter entire dataframe: `df = df[df['is_winner'].notna()].copy()`
