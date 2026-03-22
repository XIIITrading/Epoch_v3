# Method Operational Pipeline
## What Runs When, What Triggers What

**System**: Method Trading System v1.0
**Document Version**: 002
**Last Updated**: 2026-03-22

---

## Daily Trading Cycle

The Method system operates on a five-phase daily cycle aligned with US equity market hours (Eastern Time). Phase 0 (Pre-Computation) runs on schedule or manual trigger. Phases 1-4 follow the original four-phase structure.

---

## Phase 0: Pre-Computation (Scheduled / Manual Trigger)

**Goal**: Pre-compute all higher-timeframe data into Supabase so Phase 1 becomes a query, not a computation. Reduces morning prep from 30-45 minutes to <10 minutes.

**Module**: `01_application/core/bucket_runner.py` (CLI: `python -m core.bucket_runner --bucket <name>`)

### Bucket A — Weekly (Saturday/Sunday, manual trigger)

| Step | Action | Output |
|------|--------|--------|
| A.1 | Load universe from `screener_universe` table or `config/universe_tickers.txt` | 48-ticker list |
| A.2 | Resolve epoch anchors via `find_max_volume_anchor()` (High Volume Day, 6mo lookback) | Anchor dates per ticker |
| A.3 | Calculate W1/M1 market structure (fractal direction + strong/weak levels) | `market_structure` w1/m1 columns |
| A.4 | Run full Bucket B nightly pipeline for all tickers | All 5 Supabase tables populated |

**CLI**: `python -m core.bucket_runner --bucket weekly`

### Bucket B — Nightly (After 20:00 ET, manual trigger)

| Step | Action | Output |
|------|--------|--------|
| B.1 | Resolve epoch anchors for tickers without explicit dates | Anchor dates |
| B.2 | Pre-compute options OI in parallel (4 workers, ~4.7s/ticker) | Options levels per ticker |
| B.3 | Run 6-stage pipeline headless for all universe tickers | Market Structure, Bar Data, HVN POCs, Zones, Setups |
| B.4 | Export to Supabase with per-ticker savepoint isolation | `bar_data`, `hvn_pocs`, `market_structure`, `zones`, `setups` |

**CLI**: `python -m core.bucket_runner --bucket nightly`
**Duration**: ~15 minutes for 48 tickers (parallel options + sequential pipeline).

### Bucket C — Morning (07:00-08:00 ET, manual trigger)

| Step | Action | Output |
|------|--------|--------|
| C.1 | Fetch M1 bars for pre-market window (16:00 ET prior day -> 07:30 ET) | PM bar data |
| C.2 | Calculate PMH, PML, PM volume profile (PMPOC/PMVAH/PMVAL) | Pre-market levels |
| C.3 | Capture current price at trigger time | Price snapshot |
| C.4 | Update `bar_data` pm_* columns in Supabase | PM data ready for screener |

**CLI**: `python -m core.bucket_runner --bucket morning`
**Dependencies**: Bucket B must have run for the prior session (bar_data rows must exist).

### Fallback

If the nightly runner fails, Silva runs the standard Phase 1 process. Check before bed.

---

## Phase 1: Pre-Market (06:00 – 09:30 ET)

**Goal**: Identify in-play tickers, build zones, generate setups, prepare the watchlist.

| Step | Module | Action | Trigger | Output |
|------|--------|--------|---------|--------|
| 1.1 | 01_application | Run market scanner — filter universe by ATR, price, gap | Manual (Silva launches app) | Ranked ticker list |
| 1.2 | 01_application | Structure screener — D1/H4/H1/M15 fractal analysis | Follows 1.1 | Market structure per ticker, composite scores |
| 1.3 | 01_application | Select in-play tickers (25 → 10 shortlist) | Manual selection by Silva | 10-ticker watchlist |
| 1.4 | 01_application | Assign epoch dates → build volume profiles | Manual per ticker | HVN POCs per ticker |
| 1.5 | 01_application | Score zone confluence (60+ levels, bucket-max) | Automatic after 1.4 | Scored zones (L1-L5, T1-T3) |
| 1.6 | 01_application | Filter zones → assign directions → calculate targets | Automatic after 1.5 | Setups with R:R ratios |
| 1.7 | 01_application | Export to Supabase | Automatic after 1.6 | `zones`, `setups`, `bar_data`, `hvn_pocs`, `market_structure` tables updated |

**Dependencies**: Polygon.io API available, prior day data complete.
**Human Gate**: Silva selects tickers (1.3) and assigns epoch dates (1.4).
**Duration**: ~30-45 minutes active work (or <10 minutes if Phase 0 Buckets B+C ran successfully — Steps 1.1-1.7 are pre-computed, morning becomes: run Bucket C -> review screener table -> pick 4 tickers).

### Planned Additions (Method v1.0)
- **Step 1.2a**: Base ticker universe pre-filter (~250 tickers from SPY/QQQ/DIA) — reduces 1.1 scan time (Seed 001)
- **Step 1.2b**: Benzinga API news integration for top 25 tickers (METHOD.01)
- **Step 1.3a**: AI shortlist check — Claude API down-selects top 25 → 10 (METHOD.01)
- **Step 1.8**: Generate pre-market watchlist report — structured narrative per ticker (METHOD.04)
- **Step 1.9**: Distribute watchlist — Discord Tier 1, email Tier 2, social Tier 3 (METHOD.05)

---

## Phase 2: Live Session (09:30 – 16:00 ET)

**Goal**: Monitor indicators in real-time, support entry/exit decisions, execute trades.

| Step | Module | Action | Trigger | Output |
|------|--------|--------|---------|--------|
| 2.1 | 02_dow_ai | Entry Qualifier starts — polls M1 bars every 60s | Manual launch at market open | Live indicator dashboard |
| 2.2 | 02_dow_ai | 5 indicators calculated per bar per ticker (up to 6 tickers) | Each M1 bar close | Candle %, Vol Delta, Vol ROC, SMA Config, H1 Structure |
| 2.3 | 02_dow_ai | LONG/SHORT composite scores computed (0-7 scale) | Each indicator refresh | Composite scores displayed |
| 2.4 | 02_dow_ai | DOW AI analysis (on demand) | Silva clicks "Ask DOW AI" | Structured TRADE/NO_TRADE recommendation |
| 2.5 | Silva | Execute trade based on setup + indicators + AI recommendation | Manual trading decision | Trade logged externally |

**Dependencies**: 01_application output in Supabase, Polygon.io real-time data.
**Human Gate**: All trading decisions are Silva's. DOW AI recommends; Silva decides.
**Duration**: Full market session (6.5 hours). Active monitoring during high-probability windows.

**H1 Structure Cache**: H1 bars are fetched and cached once per hour, not per minute. Refreshes at the top of each hour during the session.

### Planned Additions (Method v1.0)
- **Step 2.6**: Intraday follow-up posts when trades hit targets (METHOD.13)
- **Step 2.7**: Follow-up "CALLED IT" social cards auto-generated (METHOD.05)

---

## Phase 3: Post-Session (16:00+ ET)

**Goal**: Backtest the day's setups, enrich trades with secondary analytics, update system data.

| Step | Module | Action | Trigger | Output |
|------|--------|--------|---------|--------|
| 3.1 | 03_backtest | Load zones/setups from Supabase for target date | Manual launch by Silva | Zone/setup data loaded |
| 3.2 | 03_backtest | Fetch S15 + M5 bar data from Polygon | Automatic after 3.1 | Historical bar data |
| 3.3 | 03_backtest | Run hybrid simulation (S15 entry / M5 exit) | Automatic after 3.2 | Simulated trades with P&L |
| 3.4 | 03_backtest | Export trades + daily session to Supabase | Automatic after 3.3 | `trades`, `daily_sessions` updated |
| 3.5 | 03_backtest | Run secondary processors (15-step pipeline) | Optional flag or manual | All 15 secondary tables updated |

**Secondary Processor Pipeline** (strict sequential order):
```
Step  Processor               Target Table              Depends On
----  ----------------------  ------------------------  ----------
  1   m1_bars                 m1_bars                   Polygon API
  2   h1_bars                 h1_bars                   Polygon API
  3   mfe_mae                 mfe_mae_potential          trades
  4   entry_indicators        entry_indicators           trades + Polygon
  5   m5_indicator_bars       m5_indicator_bars           Polygon
  6   m1_indicator_bars       m1_indicator_bars           m1_bars
  7   m5_trade_bars           m5_trade_bars              trades + m5_indicator_bars
  8   optimal_trade           optimal_trade              trades + m5_trade_bars
  9   r_level_events          optimal_trade (append)     optimal_trade
 10   options_analysis        options_analysis            trades + Polygon options
 11   op_mfe_mae              op_mfe_mae_potential        options_analysis
 12   stop_analysis           stop_analysis              trades + m5_trade_bars
 13   indicator_refinement    indicator_refinement       trades + m1_indicator_bars
 14   r_win_loss              r_win_loss                 trades + stop_analysis
 15   trades_unified          trades_m5_r_win            r_win_loss
```

**Dependencies**: Market data complete (16:00+ ET), zones/setups in Supabase from Phase 1.
**Human Gate**: Silva launches the backtest. Secondary processors can run automatically with `--secondary` flag.
**Duration**: ~5-15 minutes depending on number of tickers and trades.
**Error Handling**: Stop-on-error by default. Use `--no-stop` to continue past failures.

### Planned Additions (Method v1.0)
- **Step 3.6**: Daily trade recap generation (METHOD.12)
- **Step 3.7**: Best play of the day recap card (METHOD.13)
- **Step 3.8**: Journal entry auto-population (METHOD.11)

---

## Phase 4: Analysis & Review (Periodic / On-Demand)

**Goal**: Validate edges, review trades, improve the system.

| Step | Module | Action | Trigger | Output |
|------|--------|--------|---------|--------|
| 4.1 | 04_indicators | Run indicator edge tests | Manual (weekly or after N new trades) | Edge validation results |
| 4.2 | 04_indicators | Update 02_dow_ai context files with new edges | After 4.1 confirms edges | `model_stats.json`, `indicator_edges.json`, `zone_performance.json` updated |
| 4.3 | 05_system_analysis | Review CALC-001 through CALC-011 dashboards | Manual Streamlit launch | Statistical insights, Monte AI prompts |
| 4.4 | 05_system_analysis | Generate Monte AI prompts → copy to Claude | Manual per analysis type | AI-assisted analytical insights |
| 4.5 | 06_training | Flashcard review of recent trades | Manual Streamlit launch | Trade reviews persisted to `trade_reviews` |
| 4.6 | 06_training | DOW AI review prompts for individual trades | Manual per trade | AI-assisted trade evaluation |

**Dependencies**: Sufficient trade volume (30+ trades minimum for statistical tests).
**Human Gate**: Silva initiates all analysis. Edge threshold changes require explicit approval.
**Cadence**: Weekly edge testing recommended. System analysis on-demand. Training as schedule permits.

### Feedback Loop
```
4.1 (edge tests) → 4.2 (update DOW AI context)
  → 2.4 (improved recommendations next session)
    → 3.3 (better trades backtested)
      → 4.1 (re-validated edges)
        ↻ continuous improvement cycle
```

### Planned Additions (Method v1.0)
- **Step 4.7**: Phase 0 upstream validation — screener/down-selection/indicator accuracy (METHOD.10)
- **Step 4.8**: Entry model comparison analysis (METHOD.10)
- **Step 4.9**: Exit model comparison analysis (METHOD.10)
- **Step 4.10**: Monthly system review with health scorecard (METHOD.14)
- **Step 4.11**: AI review protocol with session data packager (METHOD.14)
- **Step 4.12**: Improvement action generator — auto-surfaces actionable improvements (METHOD.14)

---

## CLI Quick Reference

```bash
# Phase 1: Pre-Market
# Launch 01_application PyQt6 app (GUI)
python 01_application/main.py

# Phase 2: Live Session
# Launch 02_dow_ai Entry Qualifier (GUI)
python 02_dow_ai/main.py

# Phase 3: Post-Session
python 03_backtest/scripts/run_backtest.py 2026-01-20              # Standard run
python 03_backtest/scripts/run_backtest.py 2026-01-20 --secondary  # + secondary processors
python 03_backtest/scripts/run_backtest.py 2026-01-20 --dry-run    # No database writes
python 03_backtest/scripts/run_backtest.py 2026-01-20 --no-export  # Skip Supabase export

# Secondary processors standalone
python 03_backtest/secondary_processor/run_all.py                  # All 15 steps
python 03_backtest/secondary_processor/run_all.py --only STEP      # Single step
python 03_backtest/secondary_processor/run_all.py --start-from 8   # Resume from step

# Phase 4: Analysis
# Launch 04_indicators edge testing (GUI)
python 04_indicators/main.py

# Launch 05_system_analysis Streamlit dashboard
streamlit run 05_system_analysis/app.py

# Launch 06_training Streamlit app
streamlit run 06_training/app.py
```

---

## Timing Constraints

| Constraint | Details |
|------------|---------|
| Polygon.io rate limit | 0.25s between API calls, 3 retry attempts with exponential backoff |
| Polygon.io bar data | 30-day chunks for compliance |
| H1 structure cache | Refreshed once per hour during live session |
| M1 polling | Every 60 seconds, synchronized to minute boundaries |
| Backtest data availability | Wait until 16:00+ ET for complete session data |
| Statistical minimums | 30 trades per group for MEDIUM confidence, 100+ for HIGH |
| EOD forced close | 15:50 ET (10 minutes before close) |

---

## Dependency Graph (Simplified)

```
01_application ──────────────────────────────────┐
  (pre-market, writes zones/setups/bar_data)     │
                                                  ↓
02_dow_ai ←── bar_data ──── 01_application    03_backtest
  (live session)                                  │
                                                  ↓
                                            Secondary Processors
                                            (15 sequential steps)
                                                  │
                              ┌───────────────────┼───────────────────┐
                              ↓                   ↓                   ↓
                        04_indicators       05_system_analysis   06_training
                              │
                              ↓
                        02_dow_ai context files (feedback loop)
```

---

*This document defines the temporal operational flow of the Method system. Updated via the Auto-Update Workflow protocol after every implementation that changes when things run or what triggers what.*