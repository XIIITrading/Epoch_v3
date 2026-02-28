# Epoch v3 — Technical Reference

> **Version**: 1.0
> **Generated**: 2026-02-27
> **Files Analyzed**: 563 Python files
> **Lines of Code**: 144,456
> **Python Version**: 3.x (CPython)
> **Key Dependencies**: PyQt6, pandas, numpy, plotly, kaleido, psycopg2, polygon-api-client, anthropic, scipy, pydantic, pillow, pytz

---

## Directory Structure

```
Epoch_v3/
├── launcher.py                    # Master launcher (PyQt6 module selector)
├── requirements.txt               # Dependencies
├── CLAUDE.md                      # AI context / project instructions
│
├── 00_shared/                     # Centralized infrastructure (37 files, 5,120 lines)
│   ├── config/
│   │   ├── credentials.py         # API keys: Polygon, Supabase, Anthropic
│   │   ├── epoch_config.py        # EpochConfig dataclass (timeframes, models, params)
│   │   └── market_config.py       # MarketConfig (market hours, sessions, timezone)
│   ├── data/
│   │   ├── polygon/client.py      # PolygonClient (OHLCV bars, 7 timeframes, rate limiting)
│   │   └── supabase/client.py     # SupabaseClient (zones, setups, trades, bar_data)
│   ├── indicators/
│   │   ├── config.py              # IndicatorConfig (frozen singleton, all indicator params)
│   │   ├── types.py               # Result dataclasses (10 types)
│   │   ├── _utils.py              # Bar accessors, linear regression, array conversion
│   │   ├── core/
│   │   │   ├── volume_delta.py    # Bar position method: delta = vol * (2*position - 1)
│   │   │   ├── volume_roc.py      # (current - avg) / avg * 100
│   │   │   ├── cvd.py             # Cumulative delta + linear regression slope
│   │   │   ├── atr.py             # True Range -> SMA smoothing (14-period)
│   │   │   ├── sma.py             # 9/21 spread, momentum, price position
│   │   │   ├── vwap.py            # Cumulative (TP*V)/V with daily reset
│   │   │   └── candle_range.py    # (high-low)/close*100, absorption detection
│   │   ├── structure/
│   │   │   └── market_structure.py # Fractal-based HH/HL/LH/LL detection
│   │   └── health/
│   │       └── health_score.py    # DEPRECATED — returns None with warning
│   ├── ui/
│   │   ├── base_window.py         # BaseWindow(QMainWindow) — menu, status, clock
│   │   ├── styles.py              # COLORS (44 entries), DARK_STYLESHEET (~740 lines)
│   │   ├── widgets/               # Empty placeholder
│   │   └── charts/                # Empty placeholder
│   ├── charts/
│   │   ├── colors.py              # EPOCH_DARK, TV_DARK, TV_UI, RANK_COLORS, TIER_COLORS
│   │   ├── branding.py            # GrowthHub brand config, export sizes
│   │   └── plotly_template.py     # Registers epoch_dark + tradingview_dark templates
│   ├── models/                    # Empty placeholder (reserved for Pydantic models)
│   └── utils/                     # Empty placeholder
│
├── 01_application/                # Main trading app (50 files, 16,176 lines)
│   ├── app.py                     # PyQt6 entry point
│   ├── config.py                  # Zone params, risk sizing, cache TTL
│   ├── core/
│   │   ├── data_models.py         # 15+ Pydantic models (TickerInput -> AnalysisResult)
│   │   └── pipeline_runner.py     # PipelineRunner: orchestrates 6 stages per ticker
│   ├── calculators/
│   │   ├── market_structure.py    # Stage 1: 4-TF fractal structure + composite direction
│   │   ├── bar_data.py            # Stage 2: OHLC, ATR (5 TFs), Camarilla, overnight
│   │   ├── options_calculator.py  # Stage 2b: Top 10 OI strikes
│   │   ├── hvn_identifier.py      # Stage 3: M1 volume profile -> 10 non-overlapping POCs
│   │   ├── zone_calculator.py     # Stage 4: Zone scoring via confluence weights
│   │   ├── zone_filter.py         # Stage 5: Proximity, overlap, tier classification
│   │   ├── setup_analyzer.py      # Stage 6: Primary/secondary setups, R:R targets
│   │   ├── anchor_resolver.py     # Max-volume anchor date detection
│   │   └── scanner.py             # Two-phase pre-market scanner
│   ├── data/
│   │   ├── polygon_client.py      # Module-specific Polygon wrapper (singleton)
│   │   └── cache_manager.py       # File-based cache (parquet/pickle/JSON, TTL)
│   ├── generators/
│   │   └── discord_post.py        # PNG table + Discord markdown generation
│   ├── scanner/                   # Separate scanner package
│   │   ├── scanner.py             # TwoPhaseScanner class
│   │   ├── filters.py             # FilterPhase, RankingWeights, FilterProfiles
│   │   └── data/                  # overnight_fetcher, short_interest, ticker_manager
│   ├── ui/
│   │   ├── main_window.py         # 10-tab MainWindow with AnalysisResults signal
│   │   └── tabs/                  # 10 tab implementations (scanner through export)
│   ├── visualization_config.py    # Chart dimensions, timeframes, font sizes
│   └── weights.py                 # 60+ confluence weights, rank/tier thresholds
│
├── 02_dow_ai/                     # AI trading assistant (68 files, 15,887 lines)
│   ├── app.py                     # Launcher: Entry Qualifier or DOW Analysis
│   ├── config.py                  # Claude model, Polygon/Supabase credentials
│   ├── ai_context/
│   │   ├── model_stats.json       # EPCH1-4 performance by direction
│   │   ├── indicator_edges.json   # Validated edge conditions with pp improvements
│   │   ├── zone_performance.json  # Win rates by zone type/direction/score
│   │   ├── dow_helper_prompt.py   # v1.x/v2.0 prompt templates
│   │   └── prompt_v3.py           # v3.0 dual-pass: Pass 1 (raw) + Pass 2 (learned)
│   ├── analysis/claude_client.py  # ClaudeClient (anthropic SDK wrapper)
│   ├── data/supabase_reader.py    # SupabaseReader (zones, bar_data, structure)
│   ├── entry_qualifier/           # Tool 1: Live trading
│   │   ├── main.py                # PyQt6 app
│   │   ├── ui/                    # MainWindow, TickerPanel, GlobalControlPanel, Terminal
│   │   ├── data/                  # PolygonClient (M1 bars), DataWorker, MarketHours
│   │   └── ai/                    # AIContextLoader, DualPassQueryWorker
│   ├── dow_analysis/              # Tool 2: Batch analysis GUI
│   │   └── main_window.py         # DOWAnalysisWindow (QProcess + terminal)
│   └── batch_analyzer/            # Batch backend
│       ├── analyzer/              # ClaudeBatchClient, DualPassAnalyzer, ResponseParser
│       ├── models/                # TradeContext, EntryIndicators, AIPrediction
│       ├── prompts/               # BatchPromptBuilder
│       └── data/                  # TradeLoader, PredictionStorage, DualPassStorage
│
├── 03_backtest/                   # Trade simulation (53 files, 11,484 lines)
│   ├── app.py                     # PyQt6 launcher -> BacktestRunnerWindow
│   ├── config.py                  # Entry times, models, DB config
│   ├── engine/
│   │   ├── trade_simulator.py     # TradeSimulator: S15 bar-by-bar entry detection
│   │   └── entry_models.py        # EntryDetector: EPCH1-4 pattern logic
│   ├── data/
│   │   ├── supabase_zone_loader.py # Zone loading from setups table
│   │   ├── s15_fetcher.py         # S15Bar fetcher from Polygon
│   │   └── trades_exporter.py     # Upsert entries to trades_2
│   ├── backtest_gui/
│   │   └── main_window.py         # GUI: date picker, processor checkboxes, terminal
│   └── processor/secondary_analysis/
│       ├── m1_bars/               # Proc 1: Fetch + store M1 bars
│       ├── m1_indicator_bars_2/   # Proc 2: Calculate 22 indicators on M1 bars
│       ├── m1_atr_stop_2/         # Proc 3: M1 ATR stop simulation
│       ├── m5_atr_stop_2/         # Proc 4: M5 ATR stop simulation (canonical)
│       ├── trades_m5_r_win_2/     # Proc 5: Denormalized trade consolidation
│       ├── m1_trade_indicator_2/  # Proc 6: Entry-bar indicator snapshot
│       ├── m1_ramp_up_indicator_2/ # Proc 7: 25-bar pre-entry indicators
│       └── m1_post_trade_indicator_2/ # Proc 8: 25-bar post-entry indicators
│
├── 04_indicators/                 # Edge testing (31 files, 7,465 lines)
│   ├── app.py                     # PyQt6 GUI (5-tab indicator analysis)
│   ├── runner.py                  # CLI scorecard generator
│   ├── config.py                  # Tier thresholds, trade type definitions
│   ├── analysis/
│   │   ├── tier_ranker.py         # Chi-squared + Mann-Whitney U + tier assignment
│   │   ├── scorecard_analyzer.py  # Orchestrator: 4 trade types x 12 indicators
│   │   └── scorecard_exporter.py  # Markdown + JSON output
│   ├── data/
│   │   ├── provider.py            # DataProvider: quintile/state win rates, ramp-up avgs
│   │   └── exporter.py            # GUI export: 5 markdown reports + CSVs
│   └── ui/tabs/                   # RampUp, EntrySnapshot, PostTrade, DeepDive, Composite
│
├── 05_system_analysis/            # Statistical Q&A (140 files, 41,334 lines)
│   ├── app.py                     # PyQt6 entry point
│   ├── config.py                  # Table names, model definitions
│   ├── data/provider.py           # DataProvider: SQL queries, export to sa_question_results
│   ├── questions/
│   │   ├── __init__.py            # Auto-discovery of q_*.py files
│   │   ├── _base.py               # BaseQuestion ABC (query, render, export)
│   │   └── q_model_direction_grid.py # Model x Direction heatmap
│   ├── ui/main_window.py          # Sidebar navigator + content panel
│   └── _archive/                  # Prior Streamlit version (128 files, ~40K lines)
│
├── 06_training/                   # Interactive training (49 files, 14,393 lines)
│   ├── app.py                     # PyQt6 entry -> TrainingWindow
│   ├── config.py                  # Chart config, indicator thresholds, prefetch count
│   ├── models/trade.py            # Trade, OptimalTradeEvent, TradeWithMetrics, Zone, Review
│   ├── data/
│   │   ├── supabase_client.py     # Singleton DB client (trades, events, zones, reviews)
│   │   ├── polygon_client.py      # Bar fetcher (5m, 15m, 1h)
│   │   └── cache_manager.py       # BarCache (in-memory, prefetch 3 upcoming)
│   ├── ui/
│   │   ├── main_window.py         # TrainingWindow: FilterPanel + FlashcardPanel
│   │   ├── flashcard_panel.py     # 11 sub-panels: pre-trade + post-trade views
│   │   ├── filter_panel.py        # Date/ticker/model/unreviewed filters
│   │   ├── review_panel.py        # Structured review form (6 fields + notes)
│   │   └── ...                    # Stats, events, bookmap, indicator, DOW AI panels
│   └── components/                # Chart builders, ramp-up, DOW AI prompt generator
│
├── 07_market_analysis/            # Data-only: monthly PMA text files (0 Python files)
│
├── 08_journal/                    # Real trade journaling (66 files, 16,641 lines)
│   ├── journal_app.py             # Viewer GUI (TradeReelWindow clone)
│   ├── fifo_app.py                # DAS Trader CSV import (FIFO matching)
│   ├── processor_app.py           # 8-stage processor pipeline GUI
│   ├── core/                      # Fill, TradeLeg, Trade, FIFOTrade models
│   ├── data/                      # JournalDB, JournalTradeLoader
│   ├── viewer/                    # Main window, trade adapter
│   └── processor/                 # 8 processors (mirrors 03_backtest)
│
├── 09_results/                    # DOW AI v2.0.1 archive (2 files, 944 lines)
│   └── 02_dow_ai_r/
│       ├── batch_analyze_v2.0.1.py # CLI batch analyzer
│       └── dow_helper_prompt_v2.0.1.py # v2.0.1 prompt template
│
├── 10_machine_learning/           # Edge validation (17 files, 6,545 lines)
│   ├── config.py                  # VALIDATED_EDGES, EDGE_DEFINITIONS, INDICATOR_SCAN_QUERIES
│   ├── scripts/
│   │   ├── run_ml_workflow.py     # 12 CLI modes: daily/weekly/full/validate/hypothesize/...
│   │   ├── analysis_engine.py     # Baseline metrics, indicator breakdowns, drift detection
│   │   ├── edge_validator.py      # Chi-squared validation (HEALTHY/WEAKENING/DEGRADED)
│   │   ├── hypothesis_engine.py   # Scan -> propose -> test -> validate/reject
│   │   ├── state_manager.py       # Dual-format state (JSON + auto-gen MD)
│   │   └── export_for_claude.py   # Trade data export to JSON
│   └── state/                     # system_state.json, hypothesis_tracker.json, pending_edges.json
│
├── 11_trade_reel/                 # Social media export (30 files, 5,724 lines)
│   ├── app.py                     # PyQt6 -> TradeReelWindow
│   ├── config.py                  # TV Dark theme, brand colors, export sizes
│   ├── models/highlight.py        # HighlightTrade dataclass
│   ├── data/highlight_loader.py   # Queries trades_m5_r_win_2 WHERE outcome=WIN, max_r>=N
│   ├── charts/                    # 7 chart builders (weekly through M1 ramp-up)
│   ├── ui/                        # FilterPanel, HighlightTable, ChartPreview, ExportBar
│   └── export/image_exporter.py   # Pillow compositing -> platform-sized PNGs
│
├── 12_system_architecture/        # Documentation + analysis protocols
│   ├── eow_epoch_analysis.md      # THIS protocol's instruction file
│   ├── epoch_system_summary.md    # Human-readable output
│   ├── epoch_technical_reference.md # AI-readable output (this file)
│   └── {module}/                  # Per-module Obsidian docs
│
└── 13_system_improvement/         # System improvement tracking
```

---

## Module Deep-Dives

### 00_shared — Core Infrastructure

**Entry Points**: N/A (library module — imported by all others)
**Dependencies**: polygon-api-client, psycopg2, pandas, numpy, PyQt6, plotly, pytz
**Database Tables**: N/A (provides clients, not direct table access)

#### Config — `config/`

| Export | File | Type | Purpose |
|--------|------|------|---------|
| `POLYGON_API_KEY` | credentials.py | str | Polygon.io API key |
| `POLYGON_BASE_URL` | credentials.py | str | `https://api.polygon.io` |
| `SUPABASE_DB_CONFIG` | credentials.py | dict | `{host, port, database, user, password, sslmode}` |
| `ANTHROPIC_API_KEY` | credentials.py | str | Claude API key |
| `EpochConfig` | epoch_config.py | dataclass | Singleton `config` — timeframes, models, indicator params |
| `MarketConfig` | market_config.py | dataclass | Singleton `market_config` — hours, sessions, timezone |

**EpochConfig key fields**: `API_RATE_LIMIT_DELAY=0.1`, `FRACTAL_LENGTH=5`, `VOLUME_DELTA_BARS=5`, `VOLUME_ROC_BASELINE=20`, `CVD_WINDOW=15`, `CLAUDE_MODEL="claude-sonnet-4-20250514"`, `CLAUDE_MAX_TOKENS=1500`

**TIMEFRAMES**: M1(1min/50bars), M5(5min/100), M15(15min/100), H1(1h/100), H4(4h/50), D1(1d/100), W1(1w/52)

**MODELS**: EPCH_01 (Primary Continuation), EPCH_02 (Primary Reversal), EPCH_03 (Secondary Continuation), EPCH_04 (Secondary Reversal)

#### Data Clients — `data/`

**PolygonClient** (`data/polygon/client.py`):
- `get_bars(symbol, timeframe, start, end)` → DataFrame with `timestamp, open, high, low, close, volume, vwap, transactions`
- 7 timeframe aliases: M1/M5/M15/H1/H4/D1/W1 + S15 for backtesting
- Rate limiting (configurable delay), 3 retries with exponential backoff on 429
- Timestamps: UTC → America/New_York conversion

**SupabaseClient** (`data/supabase/client.py`):
- `get_zones(ticker)`, `get_primary_zone(ticker)`, `get_secondary_zone(ticker)`
- `get_bar_data(ticker)`, `get_hvn_pocs(ticker)` (poc1-poc10)
- `get_trades(ticker)`, `get_market_structure(ticker)`
- `execute(query)`, `insert_dataframe(table, df)` — write operations
- Session-date scoping: all queries filter by `session_date`

#### Indicators — `indicators/`

**Config** (`config.py`): Frozen `IndicatorConfig` singleton with sub-configs per indicator.

**Result Types** (`types.py`):
| Type | Key Fields |
|------|-----------|
| `VolumeDeltaResult` | `bar_delta`, `bar_position` (0-1), `delta_multiplier` (-1 to +1) |
| `RollingDeltaResult` | `rolling_delta`, `signal` (Bullish/Bearish/Neutral) |
| `VolumeROCResult` | `roc` (%), `signal`, `current_volume`, `baseline_avg` |
| `CVDResult` | `slope` (clamped -2 to +2), `trend` (Rising/Falling/Flat) |
| `ATRResult` | `atr`, `true_range`, `period` |
| `SMAResult` | `sma9`, `sma21`, `spread`, `alignment` (BULLISH/BEARISH) |
| `SMAMomentumResult` | `spread_now`, `spread_prev`, `momentum` (WIDENING/NARROWING/FLAT) |
| `VWAPResult` | `vwap`, `price_diff`, `price_pct`, `side` (ABOVE/BELOW/AT) |
| `CandleRangeResult` | `candle_range_pct`, `classification` (ABSORPTION/LOW/NORMAL/HIGH) |
| `StructureResult` | `direction` (1/-1/0), `label` (BULL/BEAR/NEUTRAL), swing highs/lows |

---

### 01_application — Zone Pipeline

**Entry Point**: `app.py` → `MainWindow` (10-tab PyQt6)
**Config**: `ZONE_ATR_DIVISOR=2.0`, `MAX_ZONES_PER_TICKER=10`, `RISK_PER_TRADE=$20`

#### Pipeline Stages

**Stage 1 — Market Structure** (`calculators/market_structure.py`):
- Fetches D1(250d), H4(100d), H1(50d), M15(15d) bars
- Fractal detection (p=2 bars each side, strict comparison)
- BOS/ChoCH tracking for structure breaks
- Composite: weighted sum (D1=1.5, H4=1.5, H1=1.0, M15=0.5)
- Output: `MarketStructure` with per-TF direction + strong/weak levels

**Stage 2 — Bar Data** (`calculators/bar_data.py`):
- Monthly/Weekly/Daily OHLC from daily/minute bars
- Overnight data (5min, 20:00-12:00 UTC)
- ATR: D1(24 bars), H1(24 bars before 11:00 UTC), M15/M5/M1(prior day market hours)
- Camarilla pivots: S3/R3(±0.500), S4/R4(±0.618), S6/R6(±1.000) × daily/weekly/monthly
- Output: `BarData` with `get_all_levels()` → 60+ standardized keys

**Stage 2b — Options** (`calculators/options_calculator.py`):
- Next 4 Friday expirations, ±15% of price
- Aggregates OI by strike across calls/puts/expirations
- Top 10 by total OI → injected into bar_data

**Stage 3 — HVN POCs** (`calculators/hvn_identifier.py`):
- M1 bars from anchor_date to analysis_date (30-day chunks)
- Volume profile at $0.01 granularity
- 10 non-overlapping POCs (min ATR/2 separation)
- 24h cache

**Stage 4 — Zone Scoring** (`calculators/zone_calculator.py`):
- Zone = POC ± (M15_ATR / 2)
- Confluence: box intersection with every technical level's zone
- Max weight per bucket (no stacking)
- Base weights: poc1=3.0...poc10=0.1
- Rank: L5≥12.0, L4≥9.0, L3≥6.0, L2≥3.0, L1<3.0

**Stage 5 — Filtering** (`calculators/zone_filter.py`):
- Proximity: Group 1(≤1 ATR), Group 2(1-2 ATR), beyond excluded
- Overlap elimination (higher score wins)
- Tier: L4/L5→T3, L3→T2, L1/L2→T1
- Bull/Bear POC identification

**Stage 6 — Setups** (`calculators/setup_analyzer.py`):
- Target: 3R+ HVN POC above/below zone (prefer higher volume), fallback 4R
- Primary aligned with composite direction, Secondary counter-trend
- R:R = target_distance / (zone_width / 2)

#### Weights (`weights.py`)
| Category | Weight |
|----------|--------|
| Monthly OHLC | 3.0 |
| Weekly OHLC | 2.0 |
| Daily OHLC | 1.0 |
| Options (top 2) | 2.5 |
| Options (3-4) | 2.0 |
| Options (5-6) | 1.5 |
| Camarilla Monthly | 3.0 |
| Camarilla Weekly | 2.0 |
| Camarilla Daily | 1.0 |
| Structure D1 | 1.5 |
| Structure H4 | 1.25 |
| Structure H1 | 1.0 |
| Structure M15 | 0.75 |

---

### 02_dow_ai — AI Trading Assistant

**Entry Points**: `app.py` (launcher) → `entry_qualifier/main.py` or `dow_analysis/main.py`
**Claude Model**: `claude-sonnet-4-20250514` (both live and batch)
**API Config**: 1500 max tokens (general), 600 (live EQ), 500 (batch), 50 req/min (batch)

#### Prompt Architecture (v3.0 Dual-Pass)

**Pass 1 (Trader's Eye)**: Ticker + direction + entry price + 15 M1 bars with indicators. No backtested context. Tests Claude's native pattern recognition.

**Pass 2 (System Decision)**: Pass 1 data + `indicator_edges.json` + `zone_performance.json` + `model_stats.json`. The authoritative recommendation.

**Live Pass 2 (Entry Qualifier)**: User's typed notes replace Pass 1. Compares trader's perspective against backtested data.

**M1 Bar Table Format**: `Bar | Time | Close | Vol | Delta | ROC% | Range% | Spread | Mom | H1 | M15 | M5 | M1 | L | S`

#### Key Edge Context (from ai_context/)

| Edge | Effect | Source |
|------|--------|--------|
| H1 Structure alignment | +36pp win rate | indicator_edges.json |
| SMA spread alignment | +16.4pp | indicator_edges.json |
| Candle range ≥ 0.15% | +15.7pp | indicator_edges.json |
| Volume delta aligned | +4-10pp | indicator_edges.json |
| H1 B+ + SHORT | 31.8% WR (worst) | Critical conflict |

#### Database Tables
- **Read**: zones, bar_data, market_structure, setups, hvn_pocs, m1_indicator_bars, trades
- **Write**: ai_predictions, dual_pass_analysis

---

### 03_backtest — Trade Simulation

**Entry Point**: `app.py` → `BacktestRunnerWindow` (date picker + 8 processor checkboxes)
**Entry Detection**: S15 bars, 4 patterns (EPCH1-4), entry_price = bar close

#### Entry Models

| Model | Pattern | Zone |
|-------|---------|------|
| EPCH1 | Continuation (through zone) | Primary |
| EPCH2 | Rejection (bounce from zone) | Primary |
| EPCH3 | Continuation | Secondary |
| EPCH4 | Rejection | Secondary |

**Continuation**: Bar opens outside zone, closes through the other side (or opens inside with price origin on entry side)
**Rejection**: Bar approaches zone, wick enters, closes back on entry side (or opens inside with origin on exit side)

#### 8 Secondary Processors

| # | Processor | Input | Output Table | Purpose |
|---|-----------|-------|-------------|---------|
| 1 | M1 Bars | trades_2 | m1_bars_2 | Fetch M1 OHLCV from Polygon |
| 2 | M1 Indicators | m1_bars_2 | m1_indicator_bars_2 | 22 indicators + multi-TF structure |
| 3 | M1 ATR Stop | trades_2 + m1_indicator_bars_2 | m1_atr_stop_2 | ATR(14) M1 stop simulation |
| 4 | M5 ATR Stop | trades_2 + m1_indicator_bars_2 | m5_atr_stop_2 | ATR(14) M5 stop simulation (canonical) |
| 5 | Consolidated | trades_2 + m5_atr_stop_2 | trades_m5_r_win_2 | Flat denormalized table |
| 6 | Entry Indicator | trades_2 + m5_atr_stop_2 + m1_indicator_bars_2 | m1_trade_indicator_2 | Snapshot at entry bar |
| 7 | Ramp-Up | same | m1_ramp_up_indicator_2 | 25 bars before entry |
| 8 | Post-Trade | same | m1_post_trade_indicator_2 | 25 bars after entry |

**Stop Simulation Logic** (M5 ATR):
- Stop = entry_price ± atr_m5 (LONG: minus, SHORT: plus)
- Targets: R1-R5 at 1x-5x stop distance
- Walk M1 bars: R targets = price-based (high/low touch), Stop = close-based
- WIN = R1 hit before stop; LOSS = everything else
- `max_r` = highest R hit; `pnl_r` = max_r (-1 for loss)

**Dependency Chain**:
```
setups → trades_2 → m1_bars_2 → m1_indicator_bars_2
                                       ↓
                              m1_atr_stop_2  +  m5_atr_stop_2
                                                    ↓
                                    trades_m5_r_win_2 + m1_trade_indicator_2
                                                      + m1_ramp_up_indicator_2
                                                      + m1_post_trade_indicator_2
```

---

### 04_indicators — Edge Testing

**Entry Points**: `app.py` (GUI), `runner.py` (CLI scorecards)
**Statistical Methods**: Chi-squared (categorical), Mann-Whitney U (continuous)
**Read-only**: No tables written

#### Tier System

| Tier | Effect Size | p-value | Meaning |
|------|-------------|---------|---------|
| S | ≥ 15pp | < 0.01 | Elite signal |
| A | ≥ 8pp | < 0.05 | Strong filter |
| B | ≥ 4pp | < 0.05 | Useful confirmation |
| C | ≥ 2pp | < 0.10 | Marginal tiebreaker |
| Rejected | Below all | — | Not actionable |

#### Indicators Analyzed (12 columns)
**Continuous**: candle_range_pct, vol_delta_roll, vol_delta_norm, vol_roc, sma_spread_pct, cvd_slope
**Categorical**: sma_config, sma_momentum_label, price_position, m5_structure, m15_structure, h1_structure

#### Setup Score (0-7)
+1 for each: candle_range≥0.15, vol_roc≥30, sma_spread≥0.15, SMA aligned, M5 aligned, H1=NEUTRAL, CVD aligned

---

### 05_system_analysis — Q&A Framework

**Entry Point**: `app.py` → `MainWindow` (sidebar + content panel)
**Architecture**: Plug-in — auto-discovers `q_*.py` files in `questions/`

#### BaseQuestion Interface
```python
class BaseQuestion(ABC):
    id: str          # Unique identifier
    title: str       # Sidebar display
    question: str    # Full text
    category: str    # Sidebar grouping

    def query(provider, time_period) -> DataFrame   # Fetch data
    def render(data) -> QWidget                     # Build visual
    def export(data) -> dict                        # Package as JSON
```

#### Implemented Questions
| ID | Title | Category | Visualization |
|----|-------|----------|---------------|
| `model_direction_grid` | Model x Direction Effectiveness | Model Performance | Plotly heatmap + table + insights |

**Export Table**: `sa_question_results` (question_id, time_period, result_json JSONB, batch_id UUID)

---

### 06_training — Interactive Training

**Entry Point**: `app.py` → `TrainingWindow` (2400x1400)
**Layout**: FilterPanel (280px) + FlashcardPanel (stretches)

#### Two-Phase Flashcard Flow
1. **Pre-Trade**: Charts sliced to entry time. 7-timeframe main chart, M1 ramp-up chart + indicator table, AI prediction display. Future hidden.
2. **Post-Trade**: Full reveal with entry/exit markers, MFE/MAE, R-level crossings, event indicator table (7 events), bookmap image, indicator refinement scores, review form.

#### Indicator Refinement Scores
**Continuation (0-10)**: MTF Alignment(0-4), SMA Momentum(0-2), Volume Thrust(0-2), Pullback Quality(0-2)
**Rejection (0-11)**: Structure Divergence(0-2), SMA Exhaustion(0-3), Delta Absorption(0-2), Volume Climax(0-2), CVD Extreme(0-2)

#### Database Tables
- **Read**: trades, optimal_trade, zones, trade_images, trades_m5_r_win, indicator_refinement, ai_predictions, m1_indicator_bars
- **Write**: trade_reviews (upsert on trade_id), trade_analysis (upsert on trade_id + type)

---

### 08_journal — Real Trade Journaling

**Entry Points**: `journal_app.py` (viewer), `fifo_app.py` (import), `processor_app.py` (pipeline)
**Data Flow**: DAS Trader CSV → FIFO parse → journal_trades → 8 processors → j_trades_m5_r_win → viewer

#### Journal-Specific Tables (j_ prefix)
| Table | Purpose |
|-------|---------|
| `journal_trades` | Imported real trades (FIFO-matched) |
| `j_m1_bars` | Raw M1 bars |
| `j_m1_indicator_bars` | 22 indicators on M1 |
| `j_m1_atr_stop` | M1 ATR stop simulation |
| `j_m5_atr_stop` | M5 ATR stop simulation |
| `j_trades_m5_r_win` | Denormalized (primary viewer source) |
| `j_m1_trade_indicator` | Entry snapshot |
| `j_m1_ramp_up_indicator` | 25-bar pre-entry |
| `j_m1_post_trade_indicator` | 25-bar post-entry |

---

### 10_machine_learning — Edge Validation

**Entry Point**: `scripts/run_ml_workflow.py` (12 CLI modes)
**Autonomy Model**: Fully autonomous except edge approval (human gate)

#### Edge Lifecycle
```
PROPOSED → TESTING → VALIDATED → [pending_edges.json] → APPROVED (human) → config.py
                  → REJECTED
```

#### Statistical Thresholds
- p < 0.05, effect > 3.0pp, N ≥ 30 (MEDIUM confidence), N ≥ 100 (HIGH)
- Chi-squared for categorical, Fisher's exact for small samples
- Drift detection: 2pp threshold from baseline

#### State Files
- `state/system_state.json` — Baseline metrics, edge health, drift alerts
- `state/hypothesis_tracker.json` — All hypotheses with test results
- `state/pending_edges.json` — Edges awaiting human approval

---

### 11_trade_reel — Social Media Export

**Entry Point**: `app.py` → `TradeReelWindow`
**Source**: `trades_m5_r_win_2 WHERE outcome='WIN' AND max_r_achieved >= N`

#### Chart Builders (shared with 08_journal)
Weekly, Daily, H1, M15, M5 Entry, M1 Action, M1 Ramp-Up — all Plotly with TradingView Dark theme

#### Export Platforms
| Platform | Size | Format |
|----------|------|--------|
| Twitter | 1600×900 | PNG |
| Instagram | 1080×1920 | PNG |
| StockTwits | 1200×630 | PNG |
| Discord | 1920×1080 | PNG |

---

## Calculation Logic

### Volume Delta
**File**: `00_shared/indicators/core/volume_delta.py`
```
bar_range = high - low
IF bar_range == 0 (doji):
    IF close >= open: position = 1.0
    ELSE: position = 0.0
ELSE:
    position = (close - low) / bar_range
delta_multiplier = 2.0 * position - 1.0
bar_delta = volume * delta_multiplier
rolling_delta = sum(bar_delta[i-period+1..i])    # period=5
cumulative_delta = cumsum(bar_deltas)
```

### Volume ROC
**File**: `00_shared/indicators/core/volume_roc.py`
```
baseline_avg = mean(volume[i-20..i-1])    # excludes current bar
IF baseline_avg == 0: roc = 0.0
ELSE: roc = ((current_volume - baseline_avg) / baseline_avg) * 100
Classification: > 30% = "Above Avg", < -20% = "Below Avg", else "Average"
```

### CVD Slope
**File**: `00_shared/indicators/core/cvd.py`
```
1. bar_deltas[] = volume_delta per bar (bar position method)
2. cvd_series[] = cumsum(bar_deltas)
3. recent_cvd = cvd_series[-15:]
4. raw_slope = linear_regression_slope(recent_cvd)
5. cvd_range = max(recent_cvd) - min(recent_cvd)
6. normalized = raw_slope / cvd_range * 15    # if range > 0
7. clamped = clip(normalized, -2.0, 2.0)
Classification: > 0.1 = "Rising", < -0.1 = "Falling", else "Flat"
```

### ATR
**File**: `00_shared/indicators/core/atr.py`
```
TR[0] = high[0] - low[0]
TR[i] = max(high[i]-low[i], |high[i]-close[i-1]|, |low[i]-close[i-1]|)
ATR[i] = mean(TR[i-13..i])    # SMA smoothing, period=14
```

### SMA 9/21
**File**: `00_shared/indicators/core/sma.py`
```
SMA9 = mean(close[i-8..i])
SMA21 = mean(close[i-20..i])
spread = SMA9 - SMA21
alignment = "BULLISH" if SMA9 > SMA21 else "BEARISH"
spread_pct = |spread| / price * 100
momentum_ratio = |spread_now| / |spread_10_bars_ago|
momentum = "WIDENING" if ratio > 1.1, "NARROWING" if < 0.9, else "FLAT"
price_position = "ABOVE" if price > max(SMA9,SMA21), "BELOW" if < min, else "BTWN"
```

### VWAP
**File**: `00_shared/indicators/core/vwap.py`
```
TP = (high + low + close) / 3.0
VWAP[i] = sum(TP[0..i] * Volume[0..i]) / sum(Volume[0..i])
Daily reset: cumulative sums reset at each new trading day
side = "ABOVE" if price > VWAP, "BELOW" if < VWAP, "AT" if |diff| < 0.01
```

### Candle Range
**File**: `00_shared/indicators/core/candle_range.py`
```
candle_range_pct = (high - low) / close * 100
< 0.12% = "ABSORPTION" (33% WR — skip trades)
0.12-0.15% = "LOW"
0.15-0.20% = "NORMAL" (trade)
>= 0.20% = "HIGH" (strong)
```

### Market Structure
**File**: `00_shared/indicators/structure/market_structure.py`
```
Fractal High[i] = high[i] > high[i±j] for all j in [1, 5]    # strictly greater
Fractal Low[i] = low[i] < low[i±j] for all j in [1, 5]
swing_highs = high values at fractal high points
swing_lows = low values at fractal low points
IF swing_highs[-1] > [-2] AND swing_lows[-1] > [-2]: BULL (direction=1)
IF swing_highs[-1] < [-2] AND swing_lows[-1] < [-2]: BEAR (direction=-1)
ELSE: NEUTRAL (direction=0)
```

---

## Data Schema

### Supabase Tables

| Table | Module | Purpose | Key |
|-------|--------|---------|-----|
| `zones` | 01 | Zone definitions | date + ticker |
| `setups` | 01 | Primary/secondary setups | date + ticker |
| `bar_data` | 01 | Complete bar data per ticker | date + ticker |
| `hvn_pocs` | 01 | 10 HVN POC prices | date + ticker |
| `market_structure` | 01 | 4-TF structure | date + ticker |
| `daily_sessions` | 03 | Session tracking | date |
| `trades_2` | 03 | Detected trade entries | trade_id |
| `m1_bars_2` | 03 | Raw M1 bars | (ticker, bar_timestamp) |
| `m1_indicator_bars_2` | 03 | M1 bars + 22 indicators | (ticker, bar_date, bar_time) |
| `m1_atr_stop_2` | 03 | M1 ATR stop outcomes | trade_id |
| `m5_atr_stop_2` | 03 | M5 ATR stop outcomes (canonical) | trade_id |
| `trades_m5_r_win_2` | 03 | Consolidated flat trades | trade_id |
| `m1_trade_indicator_2` | 03 | Entry-bar snapshot | trade_id |
| `m1_ramp_up_indicator_2` | 03 | 25-bar pre-entry | (trade_id, bar_sequence) |
| `m1_post_trade_indicator_2` | 03 | 25-bar post-entry | (trade_id, bar_sequence) |
| `ai_predictions` | 02 | AI TRADE/NO_TRADE predictions | trade_id |
| `dual_pass_analysis` | 02 | Dual-pass results | trade_id |
| `sa_question_results` | 05 | System analysis exports | id (serial) |
| `trade_reviews` | 06 | Training review assessments | trade_id |
| `trade_analysis` | 06 | Claude analysis prompts/responses | (trade_id, type) |
| `indicator_refinement` | 06 | Continuation/rejection scores | trade_id |
| `optimal_trade` | 06 | Event indicators (entry, R1-R3, MFE, MAE, exit) | (trade_id, event_type) |
| `trade_images` | 06 | Bookmap screenshot URLs | trade_id |
| `journal_trades` | 08 | Real trades (FIFO-matched) | trade_id |
| `j_m1_bars` through `j_m1_post_trade_indicator` | 08 | Journal secondary pipeline (8 tables) | mirrors backtest |

---

## Config Reference

| Parameter | Default | Location | Affects |
|-----------|---------|----------|---------|
| `FRACTAL_LENGTH` | 5 | EpochConfig | Bars each side for swing detection |
| `VOLUME_DELTA_BARS` | 5 | EpochConfig | Rolling delta window |
| `VOLUME_ROC_BASELINE` | 20 | IndicatorConfig | Volume average lookback |
| `CVD_WINDOW` | 15 | IndicatorConfig | CVD slope regression window |
| `ATR_PERIOD` | 14 | IndicatorConfig | ATR smoothing period |
| `SMA_FAST` | 9 | IndicatorConfig | Fast SMA period |
| `SMA_SLOW` | 21 | IndicatorConfig | Slow SMA period |
| `ABSORPTION_THRESHOLD` | 0.12% | IndicatorConfig | Candle range absorption cutoff |
| `ZONE_ATR_DIVISOR` | 2.0 | 01_application | Zone width = ATR / divisor |
| `MAX_ZONES_PER_TICKER` | 10 | 01_application | Max HVN POCs selected |
| `RISK_PER_TRADE` | $20 | 01_application | Dollar risk for share sizing |
| `CLAUDE_MODEL` | claude-sonnet-4-20250514 | EpochConfig | Claude API model |
| `CLAUDE_MAX_TOKENS` | 1500 | EpochConfig | Max response tokens |
| `REQUESTS_PER_MINUTE` | 50 | 02_dow_ai batch | API rate limit |
| `ENTRY_START_TIME` | 09:30 | 03_backtest | Market open for entries |
| `ENTRY_END_TIME` | 15:30 | 03_backtest | Stop new entries |
| `P_VALUE_THRESHOLD` | 0.05 | 04_indicators | Statistical significance |
| `EFFECT_SIZE_THRESHOLD` | 3.0pp | 04_indicators | Minimum edge to report |
| `PREFETCH_COUNT` | 3 | 06_training | Upcoming trades to prefetch |

---

## Integration Points

### Shared Imports (00_shared → all modules)
```python
from shared.config import POLYGON_API_KEY, EpochConfig
from shared.data.polygon import PolygonClient
from shared.data.supabase import SupabaseClient
from shared.indicators import volume_delta_df, atr_df, sma_df, vwap_df
from shared.indicators.structure import get_market_structure
from shared.ui import BaseWindow, COLORS, DARK_STYLESHEET
```

### Cross-Module Data Flow
- **01 → 03**: Zones/setups stored in Supabase, read by backtest for entry detection
- **03 → 04/05/10**: trades_m5_r_win_2 + indicator tables consumed by analysis modules
- **03 → 02**: Trade records + indicator snapshots feed AI context and batch analysis
- **02 → 06**: ai_predictions table consumed by training module for prediction display
- **06 → 06**: trade_reviews + trade_analysis written back for longitudinal tracking
- **08 mirrors 03**: Journal has identical 8-processor pipeline with `j_` prefix tables
- **11 shares charts with 08**: Trade reel chart builders imported directly by journal viewer

### Supabase as Shared State
All modules connect independently to the same Supabase PostgreSQL instance. There are no inter-process calls — Supabase is the integration bus. Each module reads from upstream tables and writes to its own output tables.

---

## UI Component Map

| Widget | Module | Data Displayed | Refresh Trigger |
|--------|--------|---------------|-----------------|
| PreMarketScannerTab | 01 | Gap/volume rankings | Scan button |
| MarketScreenerTab | 01 | Pipeline progress + console | Run Analysis button |
| DashboardTab | 01 | Metrics, tier breakdown, share sizing | Pipeline completion |
| ZoneResultsTab | 01 | Filtered zones by tier | Pipeline completion |
| ZoneAnalysisTab | 01 | Primary/secondary setups, R:R | Pipeline completion |
| MainWindow (5 tabs) | 04 | Ramp-up, entry, post-trade, deep-dive, composite | Filter change |
| MainWindow (sidebar) | 05 | Question Q&A with Plotly charts | Question/period selection |
| FlashcardPanel | 06 | 11 sub-panels: charts, indicators, review form | Next Trade button |
| JournalViewerWindow | 08 | 7-timeframe charts for real trades | Trade selection |
| TradeReelWindow | 11 | 7-timeframe charts + export controls | Trade selection |

---

## Recent Changes

Initial baseline — no prior version to compare.
