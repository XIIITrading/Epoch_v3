# Method Data Flow
## Supabase Table Schemas, Data Contracts, and Flow Paths

**System**: Method Trading System v1.0
**Database**: Supabase PostgreSQL
**Access Pattern**: V2 shared client via `00_shared/data/supabase/`
**Document Version**: 002
**Last Updated**: 2026-03-22

---

## Access Standards

All modules access Supabase through the shared client:
```python
from shared.data.supabase import get_client
client = get_client()
```

Legacy V1 modules (04_indicators) still use raw `psycopg2`. Do not propagate this pattern to new code. All connections require SSL.

**Write Pattern**: Incremental processors query unprocessed records via LEFT JOIN exclusion, calculate metrics, and upsert with ON CONFLICT handling. Never use delete-then-insert.

---

## Table Registry

### Zone Pipeline Tables (Written by 01_application)

**zones**
| Column | Type | Description |
|--------|------|-------------|
| zone_id | text PK | Unique zone identifier |
| ticker | text | Ticker symbol |
| date | date | Trading date |
| poc_price | numeric | HVN Point of Control price |
| zone_high | numeric | Zone upper boundary (POC + M15_ATR/2) |
| zone_low | numeric | Zone lower boundary (POC - M15_ATR/2) |
| confluence_score | integer | Bucket-max confluence score (0-15+) |
| level_rank | text | L1-L5 classification (thresholds: 3/6/9/12) |
| tier | text | T1-T3 tier classification |
| direction | text | Bull / Bear |

Read by: `03_backtest`

**setups**
| Column | Type | Description |
|--------|------|-------------|
| setup_id | text PK | Unique setup identifier |
| ticker | text | Ticker symbol |
| date | date | Trading date |
| zone_id | text FK | Reference to zones table |
| direction | text | LONG / SHORT |
| zone_type | text | PRIMARY / SECONDARY |
| hvn_poc | numeric | Setup anchor POC price |
| target_id | text | Target zone identifier |
| target_price | numeric | Calculated target price |
| risk_reward | numeric | R:R ratio |

Read by: `03_backtest`

**bar_data**
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| ~70 fields | various | Monthly/weekly/daily OHLC, prior period levels, ATR (M1-D1), Camarilla pivots (S3/S4/S6, R3/R4/R6), options OI levels (op_01-op_10), PDV POC/VAH/VAL |
| pm_high | numeric | Pre-market high (16:00 ET prior day -> 07:30 ET). Written by Bucket C. |
| pm_low | numeric | Pre-market low. Written by Bucket C. |
| pm_poc | numeric | Pre-market volume profile POC. Written by Bucket C. |
| pm_vah | numeric | Pre-market value area high. Written by Bucket C. |
| pm_val | numeric | Pre-market value area low. Written by Bucket C. |
| pm_price | numeric | Current price at Bucket C trigger time. Written by Bucket C. |

Written by: `01_application` (nightly pipeline + Bucket C morning runner)
Read by: `02_dow_ai`, `01_application/data/pre_market_query.py`

**hvn_pocs**
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| poc_1 through poc_10 | numeric | Top 10 ranked HVN POC levels |
| epoch_start | date | Volume profile epoch start date |

Read by: `02_dow_ai`

**market_structure**
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| d1_direction | text | Daily structure direction |
| h4_direction | text | 4-hour structure direction |
| h1_direction | text | 1-hour structure direction |
| m15_direction | text | 15-min structure direction |
| composite | numeric | Weighted composite score (D1:1.5, H4:1.5, H1:1.0, M15:0.5) |
| strong/weak levels | numeric | Per-timeframe strong and weak price levels |
| w1_direction | integer | Weekly structure direction. Written by Bucket A. |
| w1_strong | numeric | Weekly strong level. Written by Bucket A. |
| w1_weak | numeric | Weekly weak level. Written by Bucket A. |
| m1_direction | integer | Monthly structure direction. Written by Bucket A. |
| m1_strong | numeric | Monthly strong level. Written by Bucket A. |
| m1_weak | numeric | Monthly weak level. Written by Bucket A. |

Written by: `01_application` (nightly pipeline + Bucket A weekly runner)
Read by: `02_dow_ai`, `01_application/data/pre_market_query.py`

**screener_universe** *(New — Seed 004)*
| Column | Type | Description |
|--------|------|-------------|
| ticker | text (PK) | Ticker symbol |
| added_date | date | When ticker was added to universe |
| sector | text | Sector classification (optional) |
| avg_volume | numeric | Average daily volume (optional) |
| status | text | 'active' or 'inactive' |
| epoch_anchor_date | date | Resolved epoch anchor date (from High Volume Day 6mo lookback) |

Written by: `01_application/core/bucket_a_weekly.py`
Read by: All bucket runners via `core/bucket_runner.py`
Fallback: `config/universe_tickers.txt` (48 tickers) when table is empty

---

### Core Trade Tables (Written by 03_backtest)

**trades**
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text PK | Unique trade identifier |
| ticker | text | Ticker symbol |
| date | date | Trading date |
| model | text | Entry model (EPCH1/EPCH2/EPCH3/EPCH4) |
| direction | text | LONG / SHORT |
| entry_price | numeric | S15 entry price |
| entry_time | timestamp | Entry timestamp |
| exit_price | numeric | Exit price |
| exit_time | timestamp | Exit timestamp |
| exit_reason | text | STOP / TARGET / CHoCH / EOD |
| pnl_r | numeric | P&L in R-multiples |
| pnl_points | numeric | P&L in price points |
| zone_id | text FK | Reference to zones table |
| zone_type | text | PRIMARY / SECONDARY |
| setup_id | text FK | Reference to setups table |

Read by: `04_indicators`, `05_system_analysis`, `06_training`

**daily_sessions**
| Column | Type | Description |
|--------|------|-------------|
| date | date PK | Trading date |
| total_trades | integer | Count of trades for the session |
| wins | integer | Count of winning trades |
| losses | integer | Count of losing trades |
| net_pnl_r | numeric | Net session P&L in R |
| win_rate | numeric | Session win rate |
| export_source | text | Source identifier (backtest_runner) |
| version | text | System version (3.0) |

Read by: `05_system_analysis`

---

### Secondary Processor Tables (Written by 03_backtest processors)

**m1_bars** (Processor Step 1)
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| Raw M1 OHLCV | various | Unprocessed 1-minute bars from Polygon |

**h1_bars** (Processor Step 2)
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| Raw H1 OHLCV | various | Unprocessed 1-hour bars from Polygon |

**mfe_mae_potential** (Processor Step 3)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| mfe_r | numeric | Maximum Favorable Excursion in R |
| mfe_points | numeric | MFE in price points |
| mfe_time | timestamp | Time MFE was reached |
| mae_r | numeric | Maximum Adverse Excursion in R |
| mae_points | numeric | MAE in price points |
| mae_time | timestamp | Time MAE was reached |

Read by: `05_system_analysis`

**entry_indicators** (Processor Step 4)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| Multi-timeframe snapshots | various | SMA, VWAP, Vol ROC, Vol Delta, structure at entry time across M1/M5/M15/H1 |

Read by: `04_indicators`, `05_system_analysis`

**m5_indicator_bars** (Processor Step 5)
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| Full-day M5 bars | various | M5 OHLCV + all 5 indicator calculations for the entire session |

**m1_indicator_bars** (Processor Step 6)
| Column | Type | Description |
|--------|------|-------------|
| ticker | text | Ticker symbol |
| date | date | Trading date |
| Full-day M1 bars | various | M1 OHLCV + all indicator calculations per bar |

Read by: `04_indicators`, `05_system_analysis`

**m5_trade_bars** (Processor Step 7)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| M5 bars during trade | various | Bar-by-bar progression with health scores from entry to exit |

Read by: `05_system_analysis`

**optimal_trade** (Processor Steps 8-9)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| event_type | text | ENTRY / MFE / MAE / EXIT / R1 / R2 / R3 |
| event_time | timestamp | When the event occurred |
| event_price | numeric | Price at the event |
| indicator snapshots | various | All 5 indicator values at each event point |

Read by: `06_training`

**options_analysis** (Processor Step 10)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| Options performance | various | FIRST_ITM contract, premium, Greeks, outcome |

Read by: `05_system_analysis`

**op_mfe_mae_potential** (Processor Step 11)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| Options MFE/MAE | various | Maximum excursion for options contracts |

Read by: `05_system_analysis`

**stop_analysis** (Processor Step 12)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| 6 stop types | various | Outcome simulation for each stop placement method |

Read by: `04_indicators`, `05_system_analysis`

**indicator_refinement** (Processor Step 13)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| continuation_score | integer | 0-10 composite (MTF alignment + SMA momentum + volume thrust + pullback quality) |
| rejection_score | integer | 0-11 composite (structure divergence + SMA exhaustion + delta absorption + volume climax + CVD extreme) |
| cont/rej labels | text | STRONG / GOOD / WEAK / AVOID |

Read by: `05_system_analysis`, `06_training`

**r_win_loss** (Processor Step 14)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| ATR-based R outcomes | various | Win/loss at 1R through 5R thresholds |

Read by: `05_system_analysis`

**trades_m5_r_win** (Processor Step 15)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| canonical_outcome | text | WIN / LOSS (M5 ATR 1.1x close-based stop) |
| Method | text | ATR-based or zone-buffer fallback |

Read by: `05_system_analysis`, `06_training`
**Note**: This is the canonical win condition used system-wide. All modules that evaluate outcomes must reference this table.

---

### AI & Review Tables

**trade_analysis** (Written by 02_dow_ai)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| analysis_type | text | pre / post |
| analysis_text | text | Claude's structured analysis response |

Read by: `06_training`

**ai_predictions** (Written by 02_dow_ai)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| decision | text | TRADE / NO_TRADE |
| confidence | text | HIGH / MEDIUM / LOW |
| correct | boolean | Whether prediction matched outcome |

Read by: `06_training`

**trade_reviews** (Written by 06_training)
| Column | Type | Description |
|--------|------|-------------|
| trade_id | text FK | Reference to trades |
| 16 boolean flags | boolean | Assessment flags from review form |
| notes | text | Reviewer notes |
| reviewed_at | timestamp | Review timestamp |

---

### Ramp-Up Analysis Tables (Written by 03_backtest secondary processor)

**9 ramp_analysis_* tables** storing aggregated results from the 9 ramp-up analyzers:
- Direction analysis, trade type, model analysis, model direction
- Indicator trend, indicator momentum, structure consistency
- Entry snapshot, progression average

Each contains aggregated statistics with lift vs baseline win rate, flagged at 30-trade minimum significance threshold.

Read by: `05_system_analysis` (via markdown exports)

---

## Data Flow Diagram

```
Polygon.io API
  │
  ├──→ 01_application
  │     Writes: zones, setups, bar_data, hvn_pocs, market_structure
  │     │
  │     ├──→ 02_dow_ai (reads bar_data, hvn_pocs, market_structure)
  │     │     Writes: trade_analysis, ai_predictions
  │     │
  │     └──→ 03_backtest (reads zones, setups)
  │           Writes: trades, daily_sessions
  │           │
  │           └──→ Secondary Processors (Steps 1-15)
  │                 Writes: m1_bars, h1_bars, mfe_mae_potential,
  │                         entry_indicators, m5_indicator_bars,
  │                         m1_indicator_bars, m5_trade_bars,
  │                         optimal_trade, options_analysis,
  │                         op_mfe_mae_potential, stop_analysis,
  │                         indicator_refinement, r_win_loss,
  │                         trades_m5_r_win
  │
  └──→ Consumers
        04_indicators ← trades, m1_indicator_bars, entry_indicators, stop_analysis
        05_system_analysis ← trades + all secondary tables
        06_training ← trades, trade_analysis, ai_predictions, optimal_trade,
                      indicator_refinement, trades_m5_r_win, trade_reviews

Feedback Loop:
  04_indicators → writes edge results → 02_dow_ai context JSON files
  02_dow_ai → improved TRADE/NO_TRADE → better trade decisions → 03_backtest
```

---

## Data Freshness Expectations

| Data Type | Freshness | Trigger |
|-----------|-----------|---------|
| bar_data, zones, setups | Daily | Pre-market run of 01_application |
| M1 indicator dashboard | Real-time (60s) | Live polling during session |
| trades, daily_sessions | Daily | Post-session backtest run |
| Secondary processor tables | Daily | Post-backtest processor run |
| Edge test results | Weekly/periodic | Manual run of 04_indicators |
| System analysis | On-demand | Manual Streamlit review |
| Trade reviews | On-demand | Manual training session |

---

## Schema Change Rules

1. **New tables**: Require Silva approval. Document in this file and SYSTEM_MAP.md.
2. **New columns on existing tables**: Require Silva approval if production table.
3. **All writes use ON CONFLICT**: Never delete-then-insert.
4. **All reads use LEFT JOIN exclusion**: For incremental processing.
5. **Minimum sample size**: 30 trades before computing statistical results.

---

*This document is the authoritative reference for all Supabase table schemas and data flow paths in the Method system. Updated via the Auto-Update Workflow protocol after every implementation that adds or modifies tables.*