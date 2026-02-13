# Ramp-Up Analysis Module

## Overview

The Ramp-Up Analysis module examines indicator behavior during the **15 M1 bars before trade entry** to identify patterns that correlate with trade outcomes. It answers the question: *"What were the indicators doing in the lead-up to entry, and does that pattern predict success?"*

---

## What It Does

1. **Fetches Trade Data** - Pulls trades, stop analysis outcomes, and M1 indicator bars from Supabase
2. **Calculates Metrics** - Computes averages, trends, and momentum for each indicator across the ramp period
3. **Stores Results** - Writes macro summaries and bar-by-bar progressions to database tables
4. **Supports Analysis** - Enables correlation of pre-entry indicator patterns with win/loss outcomes

---

## Key Calculations

### Entry Bar Snapshot (Bar 0)
Raw indicator values at the exact moment of entry - serves as the baseline reference point.

### Ramp Averages (Bars -15 to -1)
Simple arithmetic mean of each numeric indicator across all ramp bars:
```
ramp_avg = mean(indicator_values[-15:-1])
```

### Ramp Trends (Linear Regression)
Fits a linear regression to indicator values and classifies the slope:
```
normalized_slope = (slope * num_bars) / value_range

RISING   : normalized_slope > 0.05
FALLING  : normalized_slope < -0.05
FLAT     : otherwise
```

### Ramp Momentum (First-Half vs Second-Half)
Compares average of early bars (-15 to -8) against later bars (-7 to -1):
```
pct_change = (second_half_avg - first_half_avg) / |first_half_avg|

BUILDING : pct_change > 0.10
FADING   : pct_change < -0.10
STABLE   : otherwise
```

### Structure Consistency (Categorical)
For M15/H1 structure indicators, classifies the pattern over the ramp period:
- `CONSISTENT_BULL` / `CONSISTENT_BEAR` - Same value 80%+ of bars
- `FLIP_TO_BULL` / `FLIP_TO_BEAR` - Changed from one state to another
- `MIXED` - No clear pattern

---

## Indicators Analyzed

| Indicator | Type | Description |
|-----------|------|-------------|
| `candle_range_pct` | Numeric | Candle range as percentage |
| `vol_delta` | Numeric | Buy/sell volume differential |
| `vol_roc` | Numeric | Volume rate of change |
| `sma_spread` | Numeric | Distance between SMAs |
| `sma_momentum_ratio` | Numeric | SMA momentum relationship |
| `long_score` | Numeric | Aggregate long signal score |
| `short_score` | Numeric | Aggregate short signal score |
| `m15_structure` | Categorical | 15-minute market structure (BULL/BEAR) |
| `h1_structure` | Categorical | 1-hour market structure (BULL/BEAR) |

---

## Output Tables

### `ramp_up_macro`
One row per trade containing:
- Trade identity (trade_id, date, ticker, model, direction)
- Outcome metrics (outcome, mfe_distance, r_achieved)
- Entry bar snapshot (all indicators at bar 0)
- Ramp averages, trends, and momentum for each indicator
- Structure consistency classifications

### `ramp_up_progression`
16 rows per trade (bars -15 through 0) with raw indicator values at each bar - enables detailed time-series analysis.

---

## Usage

```bash
# Process new trades only (incremental)
python run_analysis.py

# Reprocess all trades
python run_analysis.py --full

# Specific trades
python run_analysis.py --trades T001 T002

# Different stop type
python run_analysis.py --stop-type zone_buffer

# Export to CSV
python run_analysis.py --export
```

---

## Configuration (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `STOP_TYPE` | `m5_atr` | Stop type for outcome data |
| `LOOKBACK_BARS` | `15` | Bars before entry to analyze |
| `TREND_THRESHOLD` | `0.05` | Slope threshold for trend classification |
| `MOMENTUM_THRESHOLD` | `0.10` | Change threshold for momentum classification |
| `MIN_BARS_REQUIRED` | `10` | Minimum bars needed for valid analysis |

---

## Analysis Use Cases

1. **Win Rate by Trend** - Do trades with RISING long_score outperform FALLING?
2. **Momentum Patterns** - Does BUILDING volume momentum predict success?
3. **Structure Alignment** - Are CONSISTENT_BULL trades more successful for longs?
4. **Entry Timing** - What entry bar indicator values correlate with wins?

Pre-built views `v_ramp_up_summary_by_trend` and `v_ramp_up_summary_by_momentum` aggregate win rates by pattern combinations.

---

## Derivative Analysis Module

The `analysis/` subdirectory contains tools for systematic analysis of ramp-up data, producing insights for the tradebook decision matrix.

### Analysis Tables (Supabase)

| Table | Description |
|-------|-------------|
| `ramp_analysis_direction` | Win rates by Long vs Short |
| `ramp_analysis_trade_type` | Win rates by Continuation vs Rejection |
| `ramp_analysis_model` | Win rates by EPCH1/2/3/4 |
| `ramp_analysis_model_direction` | Win rates by all 8 model+direction combinations |
| `ramp_analysis_indicator_trend` | Win rates by indicator trend state (RISING/FALLING/FLAT) |
| `ramp_analysis_indicator_momentum` | Win rates by indicator momentum (BUILDING/FADING/STABLE) |
| `ramp_analysis_structure_consistency` | Win rates by structure consistency patterns |
| `ramp_analysis_entry_snapshot` | Win rates by entry bar indicator values (bucketed) |
| `ramp_analysis_progression_avg` | Average indicators at each bar position by outcome |

### Running Analysis

```bash
# Full pipeline: create tables, calculate, export
python run_full_analysis.py

# Specify stop type
python run_full_analysis.py --stop-type zone_buffer

# Only export (skip calculations)
python run_full_analysis.py --export-only

# Run specific analyzers only
python -m analysis.run_analysis --only direction model indicator_trend
```

### Exported Prompt Documents

After running, Claude-readable analysis files are in `outputs/analysis/`:

| File | Content |
|------|---------|
| `01_direction_analysis.md` | Long vs Short performance |
| `02_trade_type_analysis.md` | Continuation vs Rejection performance |
| `03_model_analysis.md` | Individual model performance |
| `04_model_direction_analysis.md` | All 8 combinations |
| `05_indicator_trend_analysis.md` | Win rates by indicator trends |
| `06_indicator_momentum_analysis.md` | Win rates by indicator momentum |
| `07_structure_consistency_analysis.md` | Structure alignment patterns |
| `08_entry_snapshot_analysis.md` | Entry bar value thresholds |
| `09_progression_analysis.json` | Bar-by-bar data for temporal analysis |
| `09_progression_summary.md` | Progression analysis instructions |

### Workflow

1. **Run full pipeline**: `python run_full_analysis.py`
2. **Review exported files** in `outputs/analysis/`
3. **Claude analyzes** the markdown/JSON files and identifies patterns
4. **Iterate** as new trade data accumulates (~750 trades/week)
5. **Build tradebook** decision matrix from validated patterns
