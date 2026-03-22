# Method System Map
## Module Architecture, Connections, and Data Flow

**System**: Method Trading System v1.0
**Owner**: XIII Trading LLC (Silva)
**Codebase Root**: `C:\XIIITradingSystems\Method_v1\`
**Planning Board**: [XIII Trading LLC — Actions](https://silvawoodholdings.monday.com/boards/18404885417) (Board ID: 18404885417)
**Document Version**: 002
**Last Updated**: 2026-03-22

---

## System Purpose

Method is a closed-loop intraday trading methodology system for volume-based supply and demand zones. The system spans the full trading lifecycle: market screening → ticker selection → zone analysis → entry identification → live session support → backtesting → statistical analysis → training → content generation → system improvement. Each module feeds downstream consumers, and validated findings flow back upstream to improve earlier stages.

---

## Module Architecture

### Module 00 — Shared Infrastructure
**Path**: `00_shared/`
**Status**: V2 Active
**Purpose**: Centralized configuration, credentials, database access, and indicator calculation library used by all other modules.

**Key Components**:
- `data/supabase/` — Shared Supabase client (V2 pattern, all new modules must use this)
- `config.py` — Centralized credentials and settings
- `indicators/` — Standardized calculation library (SMA 9/21, VWAP, Vol ROC, Vol Delta, CVD slope, fractal market structure)

**Upstream**: None (root dependency)
**Downstream**: Every module imports from `00_shared`
**V2 Note**: New modules MUST use `from shared.data.supabase import get_client`. Raw `psycopg2` is V1 legacy debt — do not propagate.

---

### Module 01 — Zone Analysis Application
**Path**: `01_application/`
**Status**: V2 Active
**UI**: PyQt6 desktop application
**Purpose**: Pre-market preparation tool. Screens tickers, constructs volume profiles, identifies high-probability supply/demand zones, scores zone confluence, and exports setups for backtesting.

**Pipeline (6 stages)**:
1. Market Structure — Fractal detection across D1/H4/H1/M15, composite weighted score
2. Bar Data — OHLC, ATR (M1-D1), Camarilla pivots, ~70 technical fields
3. Volume Profile — $0.01-granularity profile, top 10 HVN extraction
4. Zone Confluence — 60+ multi-timeframe levels scored via bucket-max system (L1-L5, T1-T3)
5. Zone Filtering — Proximity filter (2x D1 ATR), deduplication, bull/bear POC anchors
6. Setup Analysis — Direction assignment (weighted composite), 3R/4R target cascade, Supabase export

**Writes To**: `zones`, `setups`, `bar_data`, `hvn_pocs`, `market_structure`, `screener_universe`
**Read By**: `02_dow_ai`, `03_backtest`
**External Data**: Polygon.io REST API (M1, M15, H1, H4, D1 bars)
**Monday.com Groups**: Market Screener, In-Play Ticker Identification, Setup Analysis, Pre-Market Watchlist

**Bucket Runner Subsystem** *(Seed 004 — Built 2026-03-22)*:
- `core/bucket_runner.py` — CLI entry point (`python -m core.bucket_runner --bucket weekly|nightly|morning`)
- `core/bucket_a_weekly.py` — Weekly: epoch anchor auto-detection (High Volume Day), W1/M1 fractal structure, then full nightly pipeline
- `core/bucket_b_nightly.py` — Nightly: parallel options pre-computation (4 workers), headless 6-stage pipeline for full universe, Supabase export with per-ticker savepoint isolation
- `core/bucket_c_morning.py` — Morning: pre-market bars (16:00 ET prior -> 07:30 ET), PMH/PML/PM volume profile (POC/VAH/VAL), price snapshot
- `data/pre_market_query.py` — Read-only Supabase query layer for all 5 tables + pre-market data
- `config/universe_tickers.txt` — 48-ticker universe (fallback until Supabase table is populated)
- `scripts/run_weekly.bat`, `run_nightly.bat`, `run_morning.bat` — Windows CLI launchers

---

### Module 02 — Entry Qualifier + DOW AI
**Path**: `02_dow_ai/`
**Status**: V2 Active
**UI**: PyQt6 desktop application (live session tool)
**Purpose**: Real-time M1 indicator dashboard for up to 6 tickers during active market hours. Integrates DOW AI dual-pass analysis for structured TRADE/NO_TRADE recommendations.

**Live Indicators (5, per bar)**:
- Candle Range % (absorption filter at 0.12%)
- Volume Delta (5-bar rolling close-position-weighted)
- Volume Rate of Change (vs 20-bar trailing average)
- SMA Configuration (SMA9 vs SMA21 spread)
- H1 Market Structure (hourly swing analysis, cached/refreshed per hour)

**Composite Scores**: LONG (0-7) and SHORT (0-7) with deliberate contrarian paradoxes in SHORT scoring

**DOW AI**: Copy-paste prompt generation system (NOT an API integration). Generates structured prompts → user copies to Claude Desktop → pastes response back for storage. Dual-pass: trader perspective + AI evaluation against backtested edges.

**Reads From**: `bar_data` (from 01), `model_stats.json`, `indicator_edges.json`, `zone_performance.json`
**Writes To**: `trade_analysis`
**Read By**: `06_training`
**External Data**: Polygon.io (real-time M1 bars, 60-second polling)
**Monday.com Group**: Entry Identifier

---

### Module 03 — Backtest Engine
**Path**: `03_backtest/`
**Status**: V2 Active
**UI**: PyQt6 desktop application + CLI
**Purpose**: Simulates Method zone-based trade execution against historical data. Hybrid dual-timeframe: S15 bars for entry detection, M5 bars for exit management.

**Entry Models**:
- EPCH1: Primary zone continuation (price traverses through)
- EPCH2: Primary zone rejection (wick in, close back out)
- EPCH3: Secondary zone continuation
- EPCH4: Secondary zone rejection

**Exit Priority Hierarchy**: STOP → TARGET → CHoCH → EOD (15:50 ET)

**Secondary Analysis Processor** (15-step sequential pipeline):
1. M1 bars → 2. H1 bars → 3. MFE/MAE → 4. Entry indicators → 5. M5 indicator bars → 6. M1 indicator bars → 7. M5 trade bars → 8. Optimal trade events → 9. R-level crossings → 10. Options analysis → 11. Options MFE/MAE → 12. Stop analysis (6 types) → 13. Indicator refinement → 14. R win/loss → 15. Unified outcome

**Reads From**: `zones`, `setups` (from 01)
**Writes To**: `trades`, `mfe_mae_potential`, `stop_analysis`, `entry_indicators`, `m5_trade_bars`, `m1_indicator_bars`, `indicator_refinement`, `optimal_trade`, `r_win_loss`, `options_analysis`, `op_mfe_mae_potential`, `trades_m5_r_win`
**Read By**: `04_indicators`, `05_system_analysis`, `06_training`
**External Data**: Polygon.io (S15, M5, M1, H1, H4, D1 bars + options chains)
**Monday.com Groups**: Entry System, Exit Strategy, Backtesting

---

### Module 04 — Indicator Edge Testing
**Path**: `04_indicators/`
**Status**: V2 Active
**UI**: PyQt6 desktop application
**Purpose**: Statistical validation of indicator edges against trade outcomes. Chi-square + Spearman tests across 9 segments per indicator.

**Edge Confirmation Criteria** (all three must be met):
- Statistical significance: p < 0.05
- Practical significance: effect size > 3.0 percentage points
- Sample size: minimum 30 trades/group (MEDIUM), 100+ (HIGH)

**Reads From**: `trades_2`, `m1_indicator_bars_2`, `m5_atr_stop_2`, `m1_trade_indicator_2`, `m1_ramp_up_indicator_2`, `m1_post_trade_indicator_2` (from 03 V2 pipeline)
**Writes To**: Edge results → `02_dow_ai` context files (closes the indicator refinement feedback loop)
**Read By**: `02_dow_ai` (via context JSON files)
**Monday.com Group**: Entry Identifier (Indicator Outcome Analysis item)

---

### Module 05 — System Analysis
**Path**: `05_system_analysis/`
**Status**: V2 Active
**UI**: PyQt6 desktop application
**Purpose**: Analytical hub with 11 CALC modules + 5 options CALC modules. Monte AI prompt generation for Claude-assisted analysis.

**CALC Modules**: CALC-001 (win rate by model) through CALC-011 (indicator edge analysis), plus CALC-O01 through CALC-O09 (options)

**Ramp-Up Analysis**: Separate secondary processor examining 15 M1 bars before entry across 9 analytical dimensions.

**Reads From**: `trades`, `mfe_mae_potential`, `entry_indicators`, `m5_trade_bars`, `stop_analysis`, `indicator_refinement`, `op_mfe_mae_potential`, `trades_m5_r_win` (all from 03)
**Writes To**: Analysis reports, Monte AI prompts, ramp analysis tables
**Read By**: Trader (via Streamlit UI), Claude (via copy-paste prompts)
**Monday.com Group**: (System Analysis items are within Backtesting group)

---

### Module 06 — Training Module
**Path**: `06_training/`
**Status**: V2 Active
**UI**: Streamlit web application
**Purpose**: Interactive flashcard review for deliberate trade evaluation practice. Right-edge simulation (charts stop at entry point) for skill transfer.

**Review Modes**: Pre-Trade (right edge, no outcome) and Post-Trade (full trade with metrics)
**Review Form**: 16 boolean assessment flags + notes → `trade_reviews` table

**Reads From**: `trades`, `trade_analysis` (from 02), `optimal_trade`, `indicator_refinement`, `trades_m5_r_win`, `ai_predictions` (from 03)
**Writes To**: `trade_reviews`
**Monday.com Group**: Trade Journal

---

### Module 07 — Market Analysis
**Path**: `07_market_analysis/`
**Status**: Archive
**Purpose**: Legacy market analysis reference. Contains migration notes only — no active code.

**Monday.com Group**: TradingView Tooling (3 items)
**Note**: TradingView Pine Scripts now live in `14_aux_tools/trading_view/`

---

### Module 08 — Trade Journal
**Path**: `08_journal/`
**Status**: V2 Active
**UI**: 3 PyQt6 desktop applications (FIFO Importer, Processor GUI, Journal Viewer)
**Purpose**: Live trade journaling pipeline. Imports broker CSV data, processes through 8-step parallel pipeline (mirrors backtest processors), and provides interactive trade analysis with indicator overlays.

**Apps**:
1. FIFO Importer — CSV ingestion from broker exports → `journal_trades`
2. Processor GUI — Runs 8 j_ processors sequentially with progress tracking
3. Journal Viewer — Interactive trade analysis with ramp-up/post-trade indicator tables

**8-Step Processor Pipeline**:
1. j_m1_bars → 2. j_m1_indicator_bars → 3. j_m1_atr_stop → 4. j_m5_atr_stop → 5. j_trades_m5_r_win → 6. j_m1_trade_indicator → 7. j_m1_ramp_up_indicator → 8. j_m1_post_trade_indicator

**Reads From**: `zones`, `setups` (from 01 — for zone overlay context)
**Writes To**: `journal_trades`, 8 `j_*` processor tables
**External Data**: Polygon.io (M1 bars for journal trades)
**Monday.com Group**: Trade Journal (5 items)

---

### Module 09 — Results Archive
**Path**: `09_results/`
**Status**: Archive
**Purpose**: Output cache and legacy script archive. Contains archived batch analysis scripts (02_dow_ai batch analyzer v2.0.1) and exported results. Not an active module.

**Notable Legacy Script**: `02_dow_ai_r/batch_analyze_v2.0.1.py` — writes to `ai_predictions` (still functional but superseded by 02_dow_ai dual-pass system)

---

### Module 10 — Machine Learning
**Path**: `10_machine_learning/`
**Status**: V2 Active
**UI**: CLI (autonomous workflow orchestrator)
**Purpose**: Closed-loop ML system for continuous trading edge improvement. Autonomous hypothesis discovery, statistical validation (chi-squared + Fisher's exact), edge health monitoring, and state management.

**Autonomy Model**:
- **Autonomous**: export, analyze, hypothesize, test, validate, status
- **Flag + Pause**: New validated edges, degraded edges → `pending_edges.json`
- **Human Required**: approve-edge, remove-edge (modifies VALIDATED_EDGES)

**CLI Commands**:
- `python scripts/run_ml_workflow.py daily` — Daily trade export
- `python scripts/run_ml_workflow.py weekly` — Weekly aggregation
- `python scripts/run_ml_workflow.py validate-edges` — Edge health check
- `python scripts/run_ml_workflow.py hypothesize` — Discover + test new edges
- `python scripts/run_ml_workflow.py cycle` — Full closed-loop run

**Reads From**: `trades_m5_r_win` (LEGACY — migration gap, should read `trades_m5_r_win_2`), `entry_indicators`, `mfe_mae_potential`, `trade_lifecycle_signals`, `m5_trade_bars`, `m1_indicator_bars`
**Writes To**: Local state files (`system_state.json`, `hypothesis_tracker.json`, `pending_edges.json`), markdown exports
**V1 Debt**: Hardcoded credentials in config.py, direct psycopg2 (not shared client)
**Monday.com Group**: Backtesting (13 items)

---

### Module 11 — Trade Reel
**Path**: `11_trade_reel/`
**Status**: V2 Active
**UI**: PyQt6 desktop application
**Purpose**: Interactive viewer for high-R highlight trades with multi-timeframe charts (M1 through Weekly), volume profiles, and one-click image export for Discord/Twitter/Instagram.

**Chart Types**: M1, M5 Entry, M5 Exit, M15, H1, Daily, Weekly — all with zone overlays and trade markers
**Export Formats**: Discord (1920x1080), Twitter (1600x900), Instagram (1080x1920), StockTwits (1200x630)

**Reads From**: `trades_m5_r_win_2`, `m1_indicator_bars_2`, `setups` (from 01)
**External Data**: Polygon.io (bar data for chart rendering)
**V1 Debt**: Hardcoded credentials and API key in config.py, direct psycopg2

---

### Module 12 — System Architecture (Docs)
**Path**: `12_system_architecture/`
**Status**: Stable (documentation only)
**Purpose**: Obsidian vault containing architecture documentation and design references for all modules. No executable code.

**Contents**: Per-module architecture notes (01-13), system summary, technical reference, end-of-week analysis templates
**Note**: Contains legacy "Epoch" references in filenames (Epoch_3.md, epoch_system_summary.md)

---

### Module 13 — System Improvement
**Path**: `13_system_improvement/`
**Status**: Empty Placeholder
**Purpose**: Reserved for future system improvement tooling. Directory exists but contains no files.

---

### Module 14 — Auxiliary Tools
**Path**: `14_aux_tools/`
**Status**: V2 Active (partial)
**Purpose**: Collection of standalone tools for TradingView indicators and social media content.

**Submodules**:
1. `trading_view/` — Pine Script v5 indicators (market_structure v1-v3, volume_delta v1) + Market Structure v3 Python visualizer
2. `social_media/` — PyQt6 image composition tool (Instagram 50/50 template implemented; Twitter/Discord stubs only)

**Reads From**: Shared indicators library (00_shared) for market structure visualizer
**External Data**: Polygon.io (for structure visualizer)
**V1 Debt**: Hardcoded paths in social_media config.py

---

### Module 15 — System Testing
**Path**: `15_testing/`
**Status**: V2 Active
**Purpose**: Comprehensive test suite for core system validation. 20 core calculation tests (CALC-001 through CALC-020), edge analysis tests, data journal tests, and user journal session tools.

**Test Categories**:
- `core_system_test/` — 20 pytest tests (ATR, SMA, volume delta, zone scoring, entry models, stops, R-levels, EOD cutoff)
- `edge_analysis_test/` — Selection edge validation against backtest data
- `data_journal_test/` — Zone quality, market structure, bar data integrity
- `user_journal_test/` — Daily selection journal Q&A session → `journal_selections`, `journal_daily_context`

**Reads From**: `trades_m5_r_win_2`, `bar_data`, `zones`, `setups` (validation queries)
**Writes To**: `journal_selections`, `journal_daily_context`, JSON test results
**V1 Debt**: Direct psycopg2 database connections

---

## Cross-Module Data Flow

### Core Trade Pipeline
```
01_application                    03_backtest                     04_indicators
  zones ──────────────────────────→ reads zones                    reads trades
  setups ─────────────────────────→ reads setups                   reads m1_indicator_bars
  bar_data ───→ 02_dow_ai         writes trades ──────────────────→ reads entry_indicators
                                   writes 15 secondary tables ────→ reads stop_analysis
                                                                    │
                                                                    ↓
                                                              writes to 02_dow_ai
                                                              context files (JSON)
```

### Analytical Pipeline
```
03_backtest (all secondary tables)
  ├──→ 05_system_analysis (reads everything, generates CALC-001..011 + Monte AI prompts)
  ├──→ 06_training (reads trades + trade_analysis + ai_predictions + indicator_refinement)
  └──→ 04_indicators (reads trades + m1_indicator_bars + entry_indicators + stop_analysis)
```

### Feedback Loop (Closed System)
```
01_application (zones/setups)
  → 03_backtest (trade simulation)
    → 04_indicators (edge validation)
      → 02_dow_ai context files (updated edges)
        → 02_dow_ai (improved live recommendations)
          → 03_backtest (re-simulated with improved parameters)
            ↻ cycle continues
```

---

## Key Supabase Tables

| Table | Written By | Read By | Purpose |
|-------|-----------|---------|---------|
| zones | 01_application | 03_backtest | Scored confluence zones |
| setups | 01_application | 03_backtest | Zone setups with direction/targets |
| bar_data | 01_application | 02_dow_ai | ~70 technical fields per ticker |
| hvn_pocs | 01_application | 02_dow_ai | Top 10 HVN POC levels per ticker |
| market_structure | 01_application | 02_dow_ai | MTF structure directions + levels |
| trades | 03_backtest | 04, 05, 06 | Core trade records |
| mfe_mae_potential | 03_backtest | 05 | Maximum favorable/adverse excursion |
| stop_analysis | 03_backtest | 04, 05 | 6 stop type outcome simulations |
| entry_indicators | 03_backtest | 04, 05 | MTF indicator snapshots at entry |
| m5_trade_bars | 03_backtest | 05 | Bar-by-bar trade progression |
| m1_indicator_bars | 03_backtest | 04, 05 | M1 indicator snapshots per bar |
| indicator_refinement | 03_backtest | 05, 06 | Continuation/rejection scores |
| optimal_trade | 03_backtest | 06 | Entry/MFE/MAE/EXIT events |
| trades_m5_r_win | 03_backtest | 05, 06 | Canonical win/loss outcome (M5 ATR 1.1x) |
| trade_analysis | 02_dow_ai | 06 | AI analysis responses per trade |
| trade_reviews | 06_training | — | Human review observations |
| ai_predictions | 02_dow_ai | 06 | Pre-computed AI predictions |
| options_analysis | 03_backtest | 05 | Options performance (FIRST_ITM) |
| op_mfe_mae_potential | 03_backtest | 05 | Options excursion data |
| r_win_loss | 03_backtest | 05 | ATR-based R outcomes (1R-5R) |
| daily_sessions | 03_backtest | 05 | Aggregated session stats |

---

## External Dependencies

| Service | Usage | Modules | Access |
|---------|-------|---------|--------|
| Polygon.io (Massive tier) | Bar data (M1-D1), tick trades, NBBO quotes, options chains | 01, 02, 03 | API key in shared credentials |
| Supabase (PostgreSQL) | Primary data store for all tables | All | Shared client in 00_shared |
| Claude API (Sonnet) | DOW AI recommendations, Monte AI prompts | 02, 05 | API key in shared credentials |
| Benzinga (via Massive) | News headlines for screener | 01 (planned) | API key in shared credentials |

---

## Operational Flow (Daily)

### Pre-Market (06:00-09:30 ET)
1. `01_application` — Run market scanner → filter → structure screen → rank
2. `01_application` — Select in-play tickers → assign timeframes → build volume profiles
3. `01_application` — Score zones → filter → generate setups → export to Supabase
4. Pre-Market Watchlist report generation (METHOD.04, planned)

### Live Session (09:30-16:00 ET)
5. `02_dow_ai` — Entry Qualifier polls M1 bars every 60s, updates indicators
6. `02_dow_ai` — Trader uses DOW AI for TRADE/NO_TRADE decisions
7. Trader executes trades based on zone setups + indicator readings

### Post-Session (16:00+ ET)
8. `03_backtest` — Run backtest for the day's zones against actual price data
9. `03_backtest` — Run secondary processors (15-step pipeline)
10. `04_indicators` — Run edge tests on new trade data (periodic)
11. `05_system_analysis` — Review updated analytics (as needed)
12. `06_training` — Flashcard review of recent trades (as needed)

### Periodic
- Weekly: Edge test refresh, system analysis review
- Monthly: Comprehensive review cadence (METHOD.14, planned)
- As needed: Indicator recalibration, zone scoring weight adjustments

---

## Monday.com Board Reference

**Board**: XIII Trading LLC — Actions
**Board ID**: 18404885417
**Items**: 103 (all Backlog as of 2026-03-21)

| Group | Method | Items |
|-------|--------|-------|
| Market Screener | METHOD.01 | 12 |
| In-Play Ticker Identification | METHOD.02 | 6 |
| Setup Analysis | METHOD.03 | 8 |
| Pre-Market Watchlist | METHOD.04 | 8 |
| Social Media Posting | METHOD.05 | 8 |
| Entry Identifier | METHOD.06 | 8 |
| TradingView Tooling | METHOD.07 | 3 |
| Entry System | METHOD.08 | 6 |
| Exit Strategy | METHOD.09 | 8 |
| Backtesting | METHOD.10 | 13 |
| Trade Journal | METHOD.11 | 5 |
| Education Automation | METHOD.12 | 6 |
| Social Media Automation | METHOD.13 | 6 |
| System Improvement | METHOD.14 | 6 |

---

## Architecture Document Index

| Document | Location | Purpose |
|----------|----------|---------|
| SYSTEM_MAP.md | `_architecture/` | This file — module architecture and connections |
| DATA_FLOW.md | `_architecture/` | Detailed Supabase table schemas and data contracts |
| PIPELINE.md | `_architecture/` | Temporal operational flow — what runs when |
| DECISIONS_LOG.md | `_architecture/` | Dated log of architectural decisions |
| AUTO_UPDATE_WORKFLOW.md | `_architecture/` | Protocol for keeping docs current |
| IDEA_INTAKE_WORKFLOW.md | `_architecture/` | 20/80 seed-to-spec development process |
| METHODOLOGY_ROADMAP.md | `_architecture/` | Local snapshot of Monday.com board for Claude Code |
| MONDAY_INTEGRATION.md | `_architecture/` | Monday.com as planning tool — integration details |
| BACKLOG_INDEX.md | `_architecture/_backlog/` | Development pipeline status for ad-hoc ideas |
| CLAUDE.md | Root | Master AI context for Claude Code |
| Module CLAUDE.md | Each module dir | Local context per module |

---

*This document is the primary architecture reference for the Method system. Updated via the Auto-Update Workflow protocol after every significant implementation. Claude Code reads this file as part of the standard pre-build sequence (Phase 1, Step 2 in root CLAUDE.md).*