# Epoch v3 — System Summary

> **Version**: 1.0
> **Generated**: 2026-02-27
> **Files Analyzed**: 563 Python files
> **Lines of Code**: 144,456
> **Active Modules**: 11 (of 13 directories)

---

## System Overview

Epoch v3 is an institutional-grade trading analysis platform built by XIII Trading LLC. Its purpose is to identify high-probability price zones where stocks are likely to react — bounce, reverse, or accelerate — by analyzing where heavy historical volume has traded and how many other significant technical levels converge at the same spot.

The system spans the full trading lifecycle: pre-market scanning to find candidates, zone identification through an 8-stage pipeline, AI-assisted entry qualification during live trading, backtesting to measure historical performance, statistical analysis of edge conditions, interactive training for pattern recognition, and social media export for sharing results.

The architecture follows a modular design with a centralized shared infrastructure (`00_shared`). Each module can run standalone via `python XX_module/app.py` or be launched from a master launcher. All modules share a single indicator library, data layer, UI styling system, and credential store. Data flows through Supabase (PostgreSQL) as the central state layer, with Polygon.io providing real-time and historical market data.

---

## Module Map

### 00_shared — Core Infrastructure
The centralized foundation that every module imports from. Provides API credentials, market data clients (Polygon.io REST API, Supabase PostgreSQL), 7 technical indicators plus market structure detection, a PyQt6 base window with dark terminal aesthetic, Plotly chart themes, and configuration management. Changes here propagate system-wide.

### 01_application — Trading Analysis (Zone Pipeline)
The flagship module. Users enter ticker symbols with anchor dates, and an 8-stage pipeline identifies the highest-probability trading zones by building volume profiles from minute-level data, scoring each high-volume node by how many technical levels converge on it, filtering by proximity and tier, and producing primary/secondary trade setups with R:R targets. Includes a pre-market scanner for gap/volume screening across S&P 500 and NASDAQ 100.

### 02_dow_ai — AI Trading Assistant
A Claude-powered companion for live and batch trading analysis. During market hours, the Entry Qualifier displays rolling 1-minute indicators for up to 6 tickers and lets the trader query Claude for a TRADE/NO_TRADE recommendation backed by backtested statistical edges. The DOW Analysis tool runs Claude against historical trades in dual-pass mode (raw pattern recognition vs. learned context) to validate AI accuracy. Currently achieving 84-86% accuracy.

### 03_backtest — Trade Simulation Engine
Detects trade entries by scanning 15-second bars for 4 pattern types (continuation and rejection through primary and secondary zones), then simulates outcomes using ATR-based stops and R-multiple targets. An 8-processor secondary pipeline enriches each trade with M1 indicator snapshots, ramp-up sequences, and post-trade progressions. The consolidated output (`trades_m5_r_win_2`) is the primary data source for all downstream analysis.

### 04_indicators — Edge Testing Framework
Statistical analysis of which indicator conditions correlate with winning trades. Uses chi-squared tests for categorical indicators and Mann-Whitney U tests for continuous ones, measuring effect size in percentage points of win rate improvement. Produces tiered scorecards (S/A/B/C/Rejected) with binary TAKE/SKIP signals. Key findings: H1 structure alignment is the strongest edge (+36pp), candle absorption zones win at 63.7%, and elevated volume at entry is actually unfavorable.

### 05_system_analysis — Statistical Q&A Framework
A plug-in question-and-answer interface for interrogating the trade database. Users select questions from a sidebar, choose a time period, and get visual answers (Plotly charts, tables, insights). Currently has one implemented question (Model x Direction grid); the framework auto-discovers any `q_*.py` file dropped into the questions directory. Exports results to Supabase as JSON for cross-module consumption.

### 06_training — Interactive Trade Review
A flashcard-based deliberate practice system. Loads historical trades, presents them in a two-phase flow (pre-trade evaluation with hidden outcome, then full reveal with charts and statistics), and collects structured reviews (would-trade, accuracy, quality, stop placement, context). Features 7-timeframe charts, M1 ramp-up visualization, AI prediction display, indicator refinement scoring, and DOW AI prompt generation for deeper analysis.

### 07_market_analysis — Historical Trade Journals
Currently a data-only directory containing text-based pre-market analysis notes organized by month. No Python code — pending migration from a manual workflow.

### 08_journal — Real Trade Journaling
Imports actual trading session fills from DAS Trader CSV exports, processes them into round-trip trades using FIFO matching, stores them in Supabase, and provides a rich chart viewer. Has its own 8-processor secondary pipeline (mirroring 03_backtest) that computes M1/M5 ATR stops, R-level wins, and indicator snapshots for real trades. The primary post-session review tool.

### 09_results — DOW AI Batch Results Archive
Contains the archived v2.0.1 batch analysis scripts for the DOW AI system. A standalone CLI tool that runs Claude against historical trades and stores predictions in the database. This was the production version before the v3.0 dual-pass system in 02_dow_ai superseded it.

### 10_machine_learning — Edge Validation Pipeline
A closed-loop statistical system that continuously discovers, validates, and monitors trading edges. Runs autonomously as a CLI pipeline: exports trade data, validates known edges with chi-squared tests, scans for new hypothesis candidates, and generates narrative reports. Edges passing statistical thresholds get flagged for human approval before being promoted to the live config. The system's scientific method for edge improvement.

### 11_trade_reel — Social Media Export
Browses the system's best winning trades (3R+ winners) and exports them as branded composite images for social media. Fetches 7 timeframes of chart data, renders them with TradingView Dark theme including zone overlays and R-level markers, and composites platform-sized PNGs (Twitter, Instagram, StockTwits, Discord) with GrowthHub branding.

---

## Indicator Summary

| Indicator | What It Measures | Trading Question It Answers |
|-----------|-----------------|---------------------------|
| **Volume Delta** | Buying vs. selling pressure per bar (bar position method) | Is the volume supporting the trade direction? |
| **Volume ROC** | Current volume relative to 20-bar average (% above/below) | Is there enough participation to move price, or is it dead? |
| **CVD Slope** | Trend of cumulative buying/selling pressure over 15 bars | Is buying/selling pressure accelerating or fading? |
| **ATR** | Average price movement over 14 bars (true range with gap accounting) | How volatile is this stock? Where should the stop go? |
| **SMA 9/21** | Trend direction and strength via fast/slow moving average spread | Is the trend accelerating (widening) or exhausting (narrowing)? |
| **VWAP** | Volume-weighted fair price for the session | Is the current price above or below where institutions traded? |
| **Candle Range** | Candle size as % of close price | Is price in an absorption zone (<0.12% = skip) or has momentum? |
| **Market Structure** | Fractal-based trend detection (higher highs + higher lows = BULL) | What is the trend across D1/H4/H1/M15 timeframes? |

---

## Scanner Logic

### Pre-Market Scanner (Two-Phase)
**Phase 1 — Hard Filters**: ATR >= $2.00, Price >= $10.00, |Gap%| >= 2.0%. Multi-threaded across S&P 500 or NASDAQ 100.

**Phase 2 — Ranking**: Normalizes overnight volume, relative overnight volume (current/prior), relative volume (overnight vs. prior regular hours), and gap magnitude to 0-100 scales. Composite score determines ranking. Primary sort: overnight volume descending.

### Zone Scanner (Pipeline Stages 1-7)
1. **Structure**: Fractal-based trend across D1/H4/H1/M15 — weighted composite determines direction
2. **Bar Data**: Gathers OHLC, ATR (5 timeframes), Camarilla pivots (3 timeframes), market structure levels
3. **Options Levels**: Top 10 open interest strikes across next 4 expirations
4. **HVN POCs**: 10 non-overlapping high-volume price levels from minute-level volume profile since anchor date
5. **Zone Scoring**: Each POC gets a zone (±M15 ATR/2). Confluence score = base weight + sum of all overlapping technical levels (monthly=3.0, weekly=2.0, daily=1.0, options=0.5-2.5, Camarilla=1.0-3.0, structure=0.75-1.5). Bucket caps prevent stacking.
6. **Filtering**: Proximity grouping (within 1 ATR vs 1-2 ATR), overlap elimination, tier classification (T3 = L4/L5, T2 = L3, T1 = L1/L2)
7. **Setup**: Best bull/bear zones become primary/secondary setups with 3R+ targets from other HVN POCs

---

## Data Flow

```
Polygon.io (Market Data)              Supabase (PostgreSQL)
        |                                    |
        v                                    v
  01_application -----> zones, setups, bar_data, hvn_pocs
        |                                    |
        v                                    v
  03_backtest --------> trades_2 -> 8 processors -> trades_m5_r_win_2
        |                                    |
        +-------> m1_indicator_bars_2        |
        |         m1_atr_stop_2              |
        |         m5_atr_stop_2              |
        |                                    |
        v                                    v
  04_indicators <--- reads trades + indicators (statistical analysis)
  05_system_analysis <--- reads trades_m5_r_win_2 (Q&A framework)
  10_machine_learning <--- reads trades_m5_r_win_2 (edge validation)
        |                                    |
        v                                    v
  02_dow_ai <--- reads zones + indicators + ai_context/*.json
        |        writes ai_predictions
        v
  06_training <--- reads trades + events + indicators + ai_predictions
        |          writes trade_reviews, trade_analysis
        v
  08_journal <--- imports DAS Trader CSV -> journal_trades -> 8 processors
        |
        v
  11_trade_reel <--- reads trades_m5_r_win_2 -> Plotly charts -> branded PNGs
```

---

## Recent Changes

Initial baseline — no prior version to compare.

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Centralized shared infrastructure** | Prevents credential duplication, indicator drift, and UI inconsistency across 11 modules |
| **PyQt6 over Streamlit** | Desktop app allows multi-window workflows, background threads, and sub-second chart interaction that Streamlit's server model cannot support |
| **Module independence** | Each module runs standalone — no dependency on others being available. Supabase is the shared state layer, not inter-process calls |
| **SMA smoothing for ATR (not Wilder/EMA)** | Simpler calculation, consistent with the system's V1 behavior. Preserves 1:1 calculation parity during migration |
| **M5 ATR as canonical stop** | M5 ATR(14) x 1.1 (close-based) is the system's official outcome measure. M1 ATR stop exists as an alternative but M5 is the primary |
| **Bar position method for volume delta** | True tick-level data unavailable at Polygon's pricing tier. Bar position is a validated approximation |
| **Health Score deprecated (SWH-6)** | No validated trading edge found. Function returns None with deprecation warning to prevent silent failures |
| **Plug-in question architecture** | Auto-discovery of `q_*.py` files means zero-config expansion of the analysis framework |
| **Human approval gate for ML edges** | Prevents the system from autonomously modifying live trading parameters. Edges must be explicitly approved |
| **Fractal length = 5** | 5 bars each side for swing point detection balances sensitivity (catching real swings) with noise filtering (ignoring micro-moves) |
