# EPOCH 2.0 - Database Schema Reference

> Database: Supabase PostgreSQL
> Host: db.pdbmcskznoaiybdiobje.supabase.co
> All tables owned by `03_backtest` unless noted.

---

## Core Tables

### trades
Primary trade records.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (PK) | Unique trade identifier |
| date | date | Trading date |
| ticker | text | Ticker symbol |
| model | text | Entry model (EPCH1-4) |
| direction | text | LONG or SHORT |
| entry_price | numeric | Entry price |
| entry_time | timestamp | Entry timestamp |
| exit_price | numeric | Exit price |
| exit_time | timestamp | Exit timestamp |
| exit_reason | text | Why trade was closed |
| zone_high | numeric | Zone upper boundary |
| zone_low | numeric | Zone lower boundary |
| zone_type | text | Zone classification |
| pnl_r | numeric | P&L in R-multiples (LEGACY) |

**Note**: Use `trades_m5_r_win.pnl_r` for canonical outcomes.

### trades_m5_r_win
Canonical trade outcomes using M5 ATR(14) x 1.1 stop.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (PK, FK) | References trades.trade_id |
| is_winner | boolean | **CANONICAL** win/loss |
| outcome | text | WIN or LOSS |
| pnl_r | numeric | **CANONICAL** P&L in R |
| stop_price | numeric | Calculated stop price |
| stop_distance | numeric | Distance from entry to stop |
| r1_price | numeric | 1R target price |
| r2_price | numeric | 2R target price |
| r3_price | numeric | 3R target price |
| reached_2r | boolean | Did price reach 2R? |
| reached_3r | boolean | Did price reach 3R? |
| outcome_method | text | How outcome was determined |

---

## Zone Tables (Owner: 01_application)

### zones
Zone boundaries from volume profile analysis.

| Column | Type | Description |
|--------|------|-------------|
| ticker_id | text | Ticker identifier |
| ticker | text | Ticker symbol |
| date | date | Session date |
| price | numeric | Current price |
| direction | text | Market direction |
| zone_id | text | Unique zone ID |
| hvn_poc | numeric | High Volume Node POC |
| zone_high | numeric | Upper boundary |
| zone_low | numeric | Lower boundary |
| overlaps | integer | Number of overlapping zones |
| score | numeric | Zone quality score |
| rank | integer | Zone rank by score |
| confluences | text | Supporting confluences |

### setups
Primary and secondary zone setups.

| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Session date |
| setup_type | text | PRIMARY or SECONDARY |
| direction | text | Trade direction |
| zone_high | numeric | Zone upper bound |
| zone_low | numeric | Zone lower bound |
| hvn_poc | numeric | Point of control |
| target | numeric | Price target |
| r_r | numeric | Risk-reward ratio |

---

## Indicator Tables

### entry_indicators
Indicator snapshot at time of trade entry.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (PK, FK) | References trades.trade_id |
| health_score | numeric | Composite score (0-10) |
| health_label | text | STRONG/MODERATE/WEAK/CRITICAL |
| h4_structure | text | H4 market structure |
| h1_structure | text | H1 market structure |
| m15_structure | text | M15 market structure |
| m5_structure | text | M5 market structure |
| vol_roc | numeric | Volume rate of change |
| vol_delta | numeric | Buy-sell volume delta |
| cvd_slope | numeric | CVD regression slope |
| sma9 | numeric | 9-period SMA |
| sma21 | numeric | 21-period SMA |
| sma_spread | numeric | SMA spread percentage |
| sma_momentum_label | text | WIDENING/NARROWING/STABLE |
| vwap | numeric | VWAP at entry |

### m1_indicator_bars
M1 (1-minute) bars with calculated indicators.

| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| timestamp | timestamp | Bar timestamp |
| open, high, low, close | numeric | OHLC prices |
| volume | bigint | Bar volume |
| *[indicator columns]* | various | Calculated indicators |

### m5_indicator_bars
M5 (5-minute) bars with calculated indicators.

| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| timestamp | timestamp | Bar timestamp |
| open, high, low, close | numeric | OHLC prices |
| volume | bigint | Bar volume |
| *[indicator columns]* | various | Calculated indicators |

### m5_trade_bars
M5 bars specific to trade lifecycle (entry to exit).

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (FK) | References trades.trade_id |
| bar_number | integer | Sequential bar number |
| timestamp | timestamp | Bar timestamp |
| open, high, low, close | numeric | OHLC prices |
| volume | bigint | Bar volume |
| *[indicator columns]* | various | Calculated indicators |

---

## Analysis Tables

### stop_analysis
Six stop types with simulated outcomes for each trade.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (FK) | References trades.trade_id |
| stop_type | text | zone_buffer/prior_m1/prior_m5/m5_atr/m15_atr/fractal |
| stop_price | numeric | Calculated stop price |
| stop_distance | numeric | Entry to stop distance |
| is_winner | boolean | Win/loss for this stop type |
| pnl_r | numeric | P&L for this stop type |

### mfe_mae_potential
Maximum Favorable/Adverse Excursion data.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (PK, FK) | References trades.trade_id |
| mfe_r_potential | numeric | Max favorable excursion in R |
| mae_r_potential | numeric | Max adverse excursion in R |
| mfe_potential_time | timestamp | When MFE occurred |
| mae_potential_time | timestamp | When MAE occurred |

### optimal_trade
Event indicators marking key trade moments.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (FK) | References trades.trade_id |
| event_type | text | ENTRY/MFE/MAE/EXIT |
| event_time | timestamp | When event occurred |
| event_price | numeric | Price at event |
| *[indicator columns]* | various | Indicators at event time |

### indicator_refinement
Continuation/Rejection scoring for parameter optimization.

| Column | Type | Description |
|--------|------|-------------|
| trade_id | text (FK) | References trades.trade_id |
| *[scoring columns]* | various | Refinement metrics |

---

## Views (Created by 10_machine_learning)

### v_claude_trade_export
Optimized single-query view joining trades + outcomes + indicators + MFE/MAE.
See `sql/v_claude_trade_export.sql`.

### v_edge_summary
Pre-aggregated edge analysis with baseline comparison.
See `sql/v_edge_summary.sql`.

---

## Key Relationships

```
trades (1) -----> (1) trades_m5_r_win    [canonical outcomes]
trades (1) -----> (1) entry_indicators   [indicator snapshot]
trades (1) -----> (N) m5_trade_bars      [bar progression]
trades (1) -----> (6) stop_analysis      [6 stop types]
trades (1) -----> (1) mfe_mae_potential  [excursion data]
trades (1) -----> (4) optimal_trade      [ENTRY/MFE/MAE/EXIT events]
trades (1) -----> (1) indicator_refinement
zones  (1) -----> (N) trades             [via date + zone boundaries]
setups (1) -----> (N) trades             [via date + setup_type]
```

---

## Important Notes

1. **Always use `trades_m5_r_win.is_winner`** for outcome classification
2. **Never use `trades.pnl_r`** directly - use `COALESCE(m.pnl_r, t.pnl_r)`
3. **All JOINs use `trade_id`** as the linking key
4. **Dates are in ET** (Eastern Time) - market date, not UTC
5. **This module is read-only** - no INSERT/UPDATE/DELETE operations
