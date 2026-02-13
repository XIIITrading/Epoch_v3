# Optimal Trade Sourcing from Trade Bars

## Overview
Update optimal_trade module to source data from trade_bars worksheet instead of exit_events. This simplifies the architecture and uses the self-contained trade_bars data for MFE/MAE identification.

## Phase 1: Add Date Column to trade_bars (v1.2.0)

### Files to modify:
- `trade_bars_config.py` - Add `date` column (insert at column B, shift others)
- `trade_bars_builder.py` - Extract date from backtest and populate
- `trade_bars_writer.py` - Update column widths
- `__init__.py` - Update version
- `trade_bars_map.json` - Update schema

### New Schema (33 columns, A-AG):

| Column | Name | Description |
|--------|------|-------------|
| A | trade_id | Trade identifier |
| **B** | **date** | **Trade date (NEW)** |
| C | event_seq | Sequence within trade |
| D | event_time | Bar timestamp |
| E | bars_from_entry | Bars since entry |
| F | event_type | ENTRY/IN_TRADE/EXIT |
| G-K | OHLCV | open, high, low, close, volume |
| L | r_at_event | R at bar close |
| M | health_score | 0-10 |
| N-P | Price indicators | vwap, sma9, sma21 |
| Q-S | Volume indicators | vol_roc, vol_delta, cvd_slope |
| T-U | SMA analysis | sma_spread, sma_momentum |
| V-Y | Structure | m5, m15, h1, h4 |
| Z | health_summary | STRONG/MODERATE/WEAK/CRITICAL |
| AA-AG | Trade context | ticker, direction, model, win, actual_r, exit_reason, entry_health |

---

## Phase 2: Update optimal_trade Module (v5.0.0)

### Source Change:
- **Old**: Read from `exit_events` worksheet (deprecated)
- **New**: Read from `trade_bars` worksheet

### Files to modify:
- `optimal_runner.py` - Change data source from exit_events to trade_bars
- `analysis_builder.py` - New MFE/MAE identification logic

### MFE/MAE Identification Logic:

```
For each trade_id group in trade_bars:

    IF same-bar trade (only 1 unique bar):
        MFE_bar = that bar
        MAE_bar = that bar

    ELSE (multi-bar trade):
        IF direction == "LONG":
            MFE_bar = bar with MAX(high_price)
            MAE_bar = bar with MIN(low_price)
        ELSE (SHORT):
            MFE_bar = bar with MIN(low_price)
            MAE_bar = bar with MAX(high_price)

    # For ties, use first occurrence (earliest bars_from_entry)
```

### Output Row Construction:

| Event Type | price_at_event | r_at_event | Other Fields |
|------------|----------------|------------|--------------|
| ENTRY | close_price of ENTRY bar | r_at_event from ENTRY bar | All from ENTRY bar |
| MFE | high_price (LONG) or low_price (SHORT) of MFE bar | r_at_event from MFE bar (at close) | All from MFE bar |
| MAE | low_price (LONG) or high_price (SHORT) of MAE bar | r_at_event from MAE bar (at close) | All from MAE bar |
| EXIT | close_price of EXIT bar | r_at_event from EXIT bar | All from EXIT bar |

### Key Design Decisions:
1. `price_at_event` for MFE/MAE uses the actual high/low that defines the extreme
2. `r_at_event` uses the close-based R from trade_bars (as calculated)
3. All indicator values (health, structure, volume, etc.) come from that bar's snapshot
4. `health_delta` = `health_score` - `entry_health` (both available in trade_bars)

---

## Phase 3: Output Schema (unchanged - 28 columns A-AB)

The optimal_trade output schema remains the same:
- A-F: Trade identification (trade_id, date, ticker, direction, model, win)
- G-K: Event identification (event_type, event_time, bars_from_entry, price_at_event, r_at_event)
- L-N: Health metrics (health_score, health_delta, health_summary)
- O-R: Indicators (vwap, sma9, sma21, sma_spread)
- S-U: Volume (sma_momentum, vol_roc, vol_delta)
- V: CVD (cvd_slope)
- W-Z: Structure (m5, m15, h1, h4)
- AA-AB: Outcome (actual_r, exit_reason)

---

## Implementation Order

1. **trade_bars v1.2.0** - Add date column
   - Update config (33 cols, A-AG)
   - Update builder to extract date
   - Update writer column widths
   - Update __init__ and JSON map

2. **optimal_trade v5.0.0** - Source from trade_bars
   - Update optimal_runner.py to read trade_bars instead of exit_events
   - Rewrite analysis_builder.py with new MFE/MAE logic
   - Update analysis_writer.py if needed
   - Update documentation

---

## Changelog

### trade_bars v1.2.0 (IMPLEMENTED 2025-12-28)
- Added `date` column (B) for trade date
- Schema expanded from 32 to 33 columns (A-AG)
- All subsequent columns shifted by 1

Files updated:
- `trade_bars_config.py` - New column mappings
- `trade_bars_builder.py` - TradeBarRow with date field
- `trade_bars_writer.py` - Column widths for 33 cols
- `trade_bars_runner.py` - Version updated
- `trade_bars_map.json` - Schema documentation
- `__init__.py` - Version 1.2.0

### optimal_trade v5.0.0 (IMPLEMENTED 2025-12-28)
- Changed data source from exit_events to trade_bars
- New MFE/MAE identification using high/low prices:
  - LONG MFE: bar with highest high_price
  - LONG MAE: bar with lowest low_price
  - SHORT MFE: bar with lowest low_price
  - SHORT MAE: bar with highest high_price
- Same-bar trades: MFE and MAE both point to that single bar
- Deprecates dependency on exit_events worksheet

Files updated:
- `analysis_builder.py` - New MFE/MAE logic, sources from trade_bars
- `optimal_runner.py` - Reads trade_bars instead of exit_events
- `analysis_writer.py` - Version updated
- `__init__.py` - Version 5.0.0, exports TRADE_BARS_COLS
