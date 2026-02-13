# EPOCH Trading System - Complete Workflow Guide

**Version:** 2.0 (Supabase-First)
**Last Updated:** 2026-01-21

This document provides step-by-step instructions for the complete EPOCH trading system workflow. All data flows through Supabase - no Excel required.

---

## Table of Contents

1. [Daily Pre-Market Workflow](#1-daily-pre-market-workflow)
2. [Live Trading Workflow](#2-live-trading-workflow)
3. [End-of-Day Backtesting](#3-end-of-day-backtesting)
4. [Daily Results Review](#4-daily-results-review)
5. [System Analysis (Weekly/Monthly)](#5-system-analysis-weeklymonthly)
6. [Training & Calibration](#6-training--calibration)
7. [Indicator Edge Testing](#7-indicator-edge-testing)
8. [DOW AI Continuous Improvement](#8-dow-ai-continuous-improvement)
   - 8.1 [DOW AI Architecture Overview](#81-dow-ai-architecture-overview)
   - 8.2 [The Indicator-to-Prompt Update Cycle](#82-the-indicator-to-prompt-update-cycle)
   - 8.3 [Running Indicator Edge Tests](#83-running-indicator-edge-tests)
   - 8.4 [Interpreting Edge Test Results](#84-interpreting-edge-test-results)
   - 8.5 [Deriving Updated Prompts from Edge Results](#85-deriving-updated-prompts-from-edge-results)
   - 8.6 [Specific Update Procedures](#86-specific-update-procedures)
   - 8.7 [Supabase-Integrated Analysis Queries](#87-supabase-integrated-analysis-queries)
   - 8.8 [Weekly Update Checklist](#88-weekly-update-checklist)
   - 8.9 [Monthly Update Checklist](#89-monthly-update-checklist)
   - 8.10 [Daily DOW AI Usage](#810-daily-dow-ai-usage)
   - 8.11 [EPCH Model Reference](#811-epch-model-reference)
   - 8.12 [Validated Skip Rules](#812-validated-skip-rules-from-edge-testing)
9. [Quick Reference Commands](#9-quick-reference-commands)
10. [Troubleshooting](#10-troubleshooting)
11. [Appendix A: Update Tracking Log Template](#appendix-a-update-tracking-log-template)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EPOCH TRADING SYSTEM                            │
│                        (Supabase-First Architecture)                    │
└─────────────────────────────────────────────────────────────────────────┘

MORNING (Pre-Market)
┌──────────────────────┐
│  05_analysis_tool    │──────► Supabase: zones, setups, daily_sessions
│  (Streamlit)         │
└──────────────────────┘

TRADING (9:30 AM - 4:00 PM)
┌──────────────────────┐     ┌──────────────────────┐
│  04_dow_ai           │     │  Entry Qualifier     │
│  (CLI Analysis)      │◄────│  (PyQt6 Dashboard)   │
└──────────────────────┘     └──────────────────────┘
         │
         ▼
    Reads from Supabase (zones, setups)

END OF DAY (Post-Market)
┌──────────────────────┐
│  05_analysis_tool/   │──────► Supabase: trades
│  backtest            │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Secondary Analysis  │──────► Supabase: entry_indicators, trade_bars,
│  (13 Processors)     │        optimal_trade, mfe_mae_potential,
└──────────────────────┘        stop_analysis, indicator_refinement

ANALYSIS & REVIEW
┌──────────────────────┐     ┌──────────────────────┐
│  12_system_analysis  │◄────│  10_training         │
│  (Streamlit)         │     │  (Streamlit)         │
└──────────────────────┘     └──────────────────────┘
         │                            │
         └────────────────────────────┘
                      │
                      ▼
              All read from Supabase
```

---

## 1. Daily Pre-Market Workflow

**When:** Before 9:30 AM ET (ideally 7:00-8:30 AM)

### 1.1 Launch Analysis Tool

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool
streamlit run app.py
```

**Access:** Browser at `http://localhost:8501`

### 1.2 Configure Tickers

1. Enter up to 10 tickers in the sidebar input form
2. For each ticker, select an anchor date:
   - **Custom:** User-defined start date for HVN epoch
   - **Prior Day:** Previous trading day's close
   - **Prior Week:** Previous Friday's close
   - **Prior Month:** Last day of previous calendar month
3. Index tickers (SPY, QQQ, DIA) are automatically analyzed with prior-month anchor

### 1.3 Run Analysis Pipeline

1. Click **"Run Analysis"** button
2. Pipeline executes:
   - Fetch data from Polygon API
   - Calculate bar data (D1, W1, M1 OHLC, ATR, Camarilla)
   - Calculate market structure (D1/H4/H1/M15)
   - Calculate HVN POCs (volume profile)
   - Calculate confluence zones
   - Filter zones by rank/tier
   - Detect trading setups

### 1.4 Review Results

Navigate through the pages:
- **Market Overview** - Index structure + ticker structure
- **Bar Data** - OHLC, HVN POCs, ATR, Camarilla levels
- **Raw Zones** - All confluence zones (unfiltered)
- **Zone Results** - Filtered zones with Tier (T1-T3) and Rank (L1-L5)
- **Analysis** - Primary/secondary trading setups
- **Pre-Market Report** - Complete visual report

### 1.5 Export to Supabase (CRITICAL)

1. Click **"Export to Supabase"** in the sidebar
2. This saves:
   - Zone records to `zones` table
   - Setup records to `setups` table
   - Session metadata to `daily_sessions` table
3. **This step is required** for backtesting and all downstream analysis

### 1.6 Generate PDF Report (Optional)

1. Navigate to **Pre-Market Report** page
2. Click **"Generate PDF"** button
3. PDF saved to `exports/` directory

---

## 2. Live Trading Workflow

**When:** 9:30 AM - 4:00 PM ET

### 2.1 Entry Qualifier (Real-time Monitoring)

```bash
cd C:\XIIITradingSystems\Epoch\04_dow_ai\entry_qualifier
python main.py
```

**Features:**
- Monitor up to 6 tickers simultaneously
- Rolling 25-bar M1 display with indicators
- Real-time scores: LONG Score (0-7), SHORT Score (0-7)
- Volume delta, SMA configuration, H1 structure
- Refreshes every 60 seconds

**Skip Rule:** If Candle Range < 0.12% = Absorption Zone = **SKIP TRADE**

### 2.2 DOW AI Entry Analysis

When a setup appears at your zone:

```bash
cd C:\XIIITradingSystems\Epoch\04_dow_ai

# Entry analysis (live current price)
python main.py entry NVDA long primary
python main.py entry TSLA short secondary

# Entry analysis (historical)
python main.py entry MSFT long primary -d 2025-12-19-10:00
```

**Output includes:**
- Trade request summary
- Zone data and price-to-zone relationship (from Supabase)
- EPCH model classification (01-04)
- Market structure (4 timeframes)
- Volume analysis (delta, ROC, CVD)
- Claude's 10-step analysis with confidence level
- Entry triggers and invalidation levels

### 2.3 DOW AI Exit Analysis

When exiting a position:

```bash
python main.py exit TSLA sell primary
python main.py exit NVDA cover secondary
```

### 2.4 Debug Files

All DOW AI analyses save debug files:
```
04_dow_ai/debug/debug_20260121_093000_entry_NVDA.txt
```
Contains: Full prompt sent to Claude + complete response

---

## 3. End-of-Day Backtesting

**When:** After market close (4:00 PM - 8:00 PM ET)

### 3.1 Run Primary Backtest

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool\backtest

# Backtest today (default)
python backtest_runner.py

# Backtest specific date
python backtest_runner.py 2026-01-20

# Backtest date range
python backtest_runner.py 2026-01-15 2026-01-20
```

**Prerequisites:**
- Morning analysis must be completed and exported to Supabase
- Polygon API key configured in credentials.py

**What it does:**
- Loads zones from Supabase (`setups` table)
- Fetches M5 bars from Polygon API
- Tests all 4 entry models (EPCH1-4)
- Writes results to Supabase (`trades` table)

**Entry Models Tested:**

| Model | Zone | Pattern | Description |
|-------|------|---------|-------------|
| EPCH1 | PRIMARY | CONTINUATION | Price breaks through zone |
| EPCH2 | PRIMARY | REJECTION | Price rejects from zone |
| EPCH3 | SECONDARY | CONTINUATION | Price breaks through zone |
| EPCH4 | SECONDARY | REJECTION | Price rejects from zone |

### 3.2 Run Secondary Analysis (13 Modules)

This is the critical step that populates all analysis tables in Supabase.

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool\backtest\processor\secondary_analysis

# Full run (all 13 modules) - RECOMMENDED
python run_all.py

# Dry run (preview only)
python run_all.py --dry-run

# Start from specific step (if resuming)
python run_all.py --start-from 3

# Run only specific step
python run_all.py --only 9
```

**Modules & Supabase Tables Populated:**

| Step | Module | Supabase Table |
|------|--------|----------------|
| 1 | M1 bars | `m1_bars` |
| 2 | H1 bars | `h1_bars` |
| 3 | Stock MFE/MAE | `mfe_mae_potential` |
| 4 | Entry indicators | `entry_indicators` |
| 5 | M5 indicator bars | `m5_indicator_bars` |
| 6 | M1 indicator bars | `m1_indicator_bars` |
| 7 | M5 trade bars | `m5_trade_bars` |
| 8 | Optimal trade events | `optimal_trade` |
| 9 | R-level events | `r_level_events` |
| 10 | Options analysis | `options_analysis` |
| 11 | Options MFE/MAE | `op_mfe_mae_potential` |
| 12 | Stop analysis | `stop_analysis` |
| 13 | Indicator refinement | `indicator_refinement` |

### 3.3 Backtest Visualization (Optional)

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool\backtest\visualization
streamlit run backtest_viz_app.py
```

**Features:**
- 4-quadrant trade visualization
- Filter by ticker, model, direction, date range
- Charts: M5 (9:00-16:00), H1 (5 days), M15 (3 days)
- Zone overlays, VWAP, EMA, HVN POC
- PDF export (single trade or batch)

---

## 4. Daily Results Review

**When:** After secondary analysis completes

### 4.1 Launch System Analysis Dashboard

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\12_system_analysis
streamlit run app.py --server.port 8502
```

**Access:** Browser at `http://localhost:8502`

### 4.2 Configure for Single-Day Review

1. Set **Date From** and **Date To** to the same date (today)
2. Leave Models, Direction, Tickers as "All"
3. Data loads automatically from Supabase

### 4.3 Review Key Metrics

**Summary Tab:**
- Total trades, wins, losses
- Win rate %
- Net R (total R-multiple)
- Expectancy

**By Model:**
- EPCH1-4 breakdown
- Win rate per model
- R-multiple per model

**By Direction:**
- LONG vs SHORT performance

### 4.4 Generate Claude-Friendly Summary

1. Navigate to **Monte AI** tab
2. Select "Quick Analysis" or "Full Analysis"
3. Click **"Generate Prompt"**
4. Copy to clipboard
5. Paste into Claude for AI-assisted interpretation

### 4.5 Key Data Available in Supabase

| Analysis Type | Table | Key Fields |
|--------------|-------|------------|
| Trade results | `trades` | pnl_r, is_winner, model, direction |
| Entry quality | `entry_indicators` | health_score, vwap_aligned, structure_aligned |
| MFE/MAE | `mfe_mae_potential` | mfe_r_potential, mae_r_potential |
| Stop performance | `stop_analysis` | outcome, r_achieved, stop_type |
| Optimal exits | `optimal_trade` | mfe_price, mae_price, optimal_pnl_r |

---

## 5. System Analysis (Weekly/Monthly)

**When:** Weekly (Friday/Saturday) or Monthly (end of month)



### 5.1 Launch System Analysis Dashboard

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\12_system_analysis
streamlit run app.py --server.port 8502
```

### 5.2 Configure for Historical Analysis

- **Date Range:** Select full analysis period (e.g., last 30 days)
- **Models:** EPCH1-4 (or filter specific models)
- **Direction:** LONG, SHORT, or both
- **Tickers:** Filter specific symbols or all
- **Outcome:** Winners, Losers, or both

### 5.3 Analysis Tabs

| Tab | Analysis | Purpose |
|-----|----------|---------|ac
| CALC-001 | Win Rate by Model | Which models perform best? |
| CALC-002 | MFE/MAE Distribution | How far do trades move in your favor/against? |
| CALC-003 | MFE/MAE Sequence | Monte Carlo baseline comparison |
| CALC-004 | Simulated Outcomes | Stop/target grid testing |
| CALC-005-008 | Indicator Analysis | Which indicators predict wins? |
| CALC-011 | EPCH Indicators | Edge testing for specific indicators |
| Options | Options Analysis | Options-specific performance |
| Stop Analysis | Stop Type Comparison | Which stop placement works best? |
| Monte AI | Claude Prompts | Generate AI-assisted analysis |

### 5.4 Monte AI Research Assistant

1. Navigate to **Monte AI** tab
2. Select analysis type:
   - **Full Analysis** - Comprehensive with schema reference
   - **Quick Analysis** - Data-only follow-up
   - **Indicator Analysis** - Focused on indicator effectiveness
   - **Options Analysis** - Options-specific insights
3. Click **"Generate Prompt"**
4. Copy prompt to Claude for interpretation

---

## 6. Training & Calibration

**When:** Weekly/monthly calibration sessions

### 6.1 Initial Setup (One-Time)

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\10_training

# Install dependencies
pip install -r requirements.txt

# Initialize database schema
python run_schema.py
```

### 6.2 Launch Training App

```bash
streamlit run app.py
```

**Access:** Browser at `http://localhost:8501`

### 6.3 Configure Session

1. **Date Range:** Default last 30 days
2. **Ticker:** Filter or "All Tickers"
3. **Model:** EPCH1-4 or "All Models"
4. **Unreviewed only:** Checkbox for fresh trades

### 6.4 Training Loop

1. Click **"Load Trades"** - fetches from Supabase
2. Trades are shuffled to prevent temporal memory leakage

**For Each Trade:**

**Pre-Trade View (Evaluate Mode):**
- Chart shows bars at entry moment (RIGHT EDGE)
- See: zones, entry price, historical context
- Do NOT see: exit price, outcome, MFE/MAE
- Make assessment: "Strong Setup" / "Weak Setup" / "No Trade"

**Post-Trade View (Reveal Mode):**
- Chart shows FULL trade from entry through exit
- MFE/MAE markers visible
- Exit time and P&L displayed
- Add notes and observations
- Toggle between views to study

### 6.5 Calibration Targets

| Assessment | Target Accuracy |
|------------|-----------------|
| Strong Setup | >60% should be winners |
| Weak Setup | >60% should be losers |
| No Trade | >60% should be losers/breakeven |

---

## 7. Indicator Edge Testing

**When:** Weekly validation, after adding new tickers, before system changes

### 7.1 Run Edge Tests

```bash
cd C:\XIIITradingSystems\Epoch\03_indicators\python

# Full analysis for each indicator
python -m volume_delta.volume_delta_edge
python -m volume_roc.volume_roc_edge
python -m candle_range.candle_range_edge
python -m cvd_slope.cvd_slope_edge
python -m sma_edge.sma_edge
python -m structure_edge.structure_edge

# With filters
python -m volume_delta.volume_delta_edge --models EPCH1,EPCH3 --direction LONG
```

### 7.2 Output Reports

Reports saved to: `03_indicators/python/[indicator]/results/`

**Report Contents:**
- Data overview (trade counts, date range)
- Statistical tests (chi-square, Spearman p-values)
- Segment analysis (ALL, LONG, SHORT, EPCH1-4)
- Actionable filter recommendations
- Confidence levels (HIGH/MEDIUM/LOW)

### 7.3 Validated Indicators Summary

| Indicator | Best Segment | Edge | Status |
|-----------|--------------|------|--------|
| H1 Structure Direction | EPCH4 SHORT | 54pp | VALIDATED |
| Candle Range Magnitude | ALL | 28-31pp | VALIDATED |
| Vol Delta Magnitude | LONG | 20pp | VALIDATED |
| CVD Slope | SHORT | 27pp | VALIDATED |
| SMA Spread Magnitude | SHORT | 25pp | VALIDATED |
| VWAP Side | - | Paradoxical | ON HOLD |
| SMA Momentum | - | No edge (p=0.10) | REJECTED |

### 7.4 Key Skip Rule

**Candle Range < 0.12% = Absorption Zone = SKIP ALL TRADES**
(Win rate drops to 31-35%)

---

## 8. DOW AI Continuous Improvement

This section provides explicit instructions for continuously updating DOW AI using indicator edge testing results and Supabase analysis.

### 8.1 DOW AI Architecture Overview

**Key Files:**
```
04_dow_ai/
├── config.py                           # Global thresholds (update here)
├── analysis/
│   ├── prompts/
│   │   ├── entry_prompt.py             # Entry analysis template
│   │   └── exit_prompt.py              # Exit analysis template
│   └── aggregator.py                   # Orchestrates all calculations
├── calculations/
│   ├── market_structure.py             # Steps 1-4
│   ├── volume_analysis.py              # Steps 5-7
│   ├── moving_averages.py              # Steps 8-9
│   └── vwap.py                         # Step 10
└── entry_qualifier/
    └── calculations/
        ├── scores.py                   # Composite scoring thresholds
        └── sma_config.py               # SMA spread threshold
```

**The 10-Step Methodology:**

| Step | Analysis | Indicator | Config Location |
|------|----------|-----------|-----------------|
| 1 | HTF Structure (H4 → H1) | BOS/ChoCH | `config.py` FRACTAL_LENGTH |
| 2 | HTF % Within Strong/Weak | Price vs levels | `market_structure.py` |
| 3 | MTF Structure (M15 → M5) | BOS/ChoCH | `config.py` FRACTAL_LENGTH |
| 4 | MTF % Within Strong/Weak | Price vs levels | `market_structure.py` |
| 5 | Volume ROC | 20-bar baseline | `config.py` VOLUME_ROC_BASELINE |
| 6 | Volume Delta (M15/M5) | 5-bar rolling | `config.py` VOLUME_DELTA_BARS |
| 7 | CVD Direction | Trend detection | `config.py` CVD_WINDOW |
| 8 | SMA9/SMA21 Alignment | Cross position | `sma_config.py` |
| 9 | SMA Spread Trend | WIDENING/NARROWING | `sma_config.py` WIDE_SPREAD_THRESHOLD |
| 10 | VWAP Location | ABOVE/BELOW | `vwap.py` |

---

### 8.2 The Indicator-to-Prompt Update Cycle

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    DOW AI CONTINUOUS IMPROVEMENT CYCLE                      │
└────────────────────────────────────────────────────────────────────────────┘

STEP 1: COLLECT DATA (Daily)
┌──────────────────────┐
│  Secondary Analysis  │───► Supabase: m1_indicator_bars, stop_analysis,
│  (13 Processors)     │              indicator_refinement
└──────────────────────┘

STEP 2: TEST EDGES (Weekly)
┌──────────────────────┐
│  03_indicators/      │───► Markdown Reports: edge test results
│  python/             │     - p-values, effect sizes
└──────────────────────┘     - segment breakdowns (EPCH1-4)
                             - confidence levels

STEP 3: DERIVE UPDATES (Weekly)
┌──────────────────────┐
│  Manual Review of    │───► Identified updates:
│  Edge Test Reports   │     - New thresholds
└──────────────────────┘     - New skip rules
                             - Prompt language changes

STEP 4: UPDATE DOW AI (Weekly/Monthly)
┌──────────────────────┐
│  04_dow_ai/          │
│  config.py           │◄─── Update thresholds
│  prompts/*.py        │◄─── Update interpretation text
│  entry_qualifier/    │◄─── Update scoring weights
└──────────────────────┘

STEP 5: VALIDATE (Next Week)
┌──────────────────────┐
│  Monitor Performance │───► Compare before/after metrics
└──────────────────────┘
```

---

### 8.3 Running Indicator Edge Tests

**Location:** `C:\XIIITradingSystems\Epoch\03_indicators\python`

**Run all indicator tests:**
```bash
cd C:\XIIITradingSystems\Epoch\03_indicators\python

# Core indicators
python -m candle_range.candle_range_edge
python -m volume_delta.volume_delta_edge
python -m volume_roc.volume_roc_edge
python -m cvd_slope.cvd_slope_edge
python -m sma_edge.sma_edge
python -m structure_edge.structure_edge
python -m vwap_simple.vwap_simple_edge

# With filters (useful for model-specific analysis)
python -m candle_range.candle_range_edge --models EPCH01,EPCH03 --direction LONG
python -m structure_edge.structure_edge --models EPCH02,EPCH04 --direction SHORT
```

**Output Location:** `03_indicators/python/[indicator]/results/[indicator]_edge_YYYYMMDD_HHMMSS.md`

---

### 8.4 Interpreting Edge Test Results

**Statistical Output Format:**

```markdown
| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Range Threshold (0.15%) | ALL | YES | HIGH | 20.0pp | 0.0000 |
| Volume Delta Sign | LONG | YES | HIGH | 15.3pp | 0.0012 |
| CVD Slope Direction | SHORT | YES | MEDIUM | 27.4pp | 0.0234 |
```

**Key Metrics:**
- **p-value < 0.05** = Statistically significant (required)
- **Effect Size > 3.0pp** = Practically significant (required)
- **Confidence: HIGH** = >= 100 trades per group (trustworthy)
- **Confidence: MEDIUM** = 30-99 trades per group (use cautiously)
- **Confidence: LOW** = < 30 trades per group (ignore)

**What Each Column Means:**
- **Edge?** - YES = Update DOW AI; NO = No action needed
- **Effect** - Win rate improvement in percentage points (pp)
- **Segment** - Which model/direction combination shows the edge

---

### 8.5 Deriving Updated Prompts from Edge Results

**Template for documenting updates:**

```
================================================================================
INDICATOR EDGE UPDATE LOG - [DATE]
================================================================================

INDICATOR: [Name]
EDGE TEST FILE: [path to markdown report]
DATE RANGE TESTED: [YYYY-MM-DD to YYYY-MM-DD]
TOTAL TRADES: [N]

FINDING:
  Test: [Test name]
  Segment: [ALL/LONG/SHORT/EPCH1-4]
  Edge: [YES/NO]
  Effect: [X.X pp]
  p-value: [0.XXXX]
  Confidence: [HIGH/MEDIUM/LOW]

GROUP STATISTICS:
  Group A: [N] trades, [X.X%] win rate
  Group B: [N] trades, [X.X%] win rate

RECOMMENDATION FROM REPORT:
  "[Exact recommendation text from edge report]"

DOW AI UPDATE:
  1. File: [config.py / entry_prompt.py / etc.]
  2. Current Value: [what it is now]
  3. New Value: [what to change it to]
  4. Rationale: [why this change improves outcomes]
================================================================================
```

---

### 8.6 Specific Update Procedures

#### 8.6.1 Updating Thresholds (config.py)

**When to update:** Edge test shows threshold produces > 5pp effect

**File:** `04_dow_ai/config.py`

```python
# CURRENT (example)
VOLUME_ROC_BASELINE = 20        # 20-bar average for ROC baseline
VOLUME_DELTA_BARS = 5           # 5-bar rolling window for delta

# AFTER edge test showing 30% ROC threshold works better:
VOLUME_ROC_THRESHOLD = 30       # ADD: 30% threshold for "elevated volume"
```

**Validation:** Run backtest with old vs new thresholds, compare win rates.

#### 8.6.2 Updating Entry Qualifier Scores (scores.py)

**File:** `04_dow_ai/entry_qualifier/calculations/scores.py`

**Current Scoring (EPCH Indicators v1.0):**
```python
# LONG Score (0-7 points):
# - Candle Range >= 0.15%: +2 points
# - H1 NEUTRAL structure: +2 points
# - Volume ROC >= 30%: +1 point
# - High magnitude volume delta (>100k): +1 point
# - Wide SMA spread (>= 0.15%): +1 point
```

**Update Process:**
1. Run structure_edge test → Find H1 direction has 30pp effect
2. Increase H1 structure weight from +2 to +3
3. Run candle_range_edge test → 0.18% threshold has 5pp better effect than 0.15%
4. Update threshold to 0.18%

#### 8.6.3 Updating Prompt Interpretation Text (entry_prompt.py)

**File:** `04_dow_ai/analysis/prompts/entry_prompt.py`

**When to update:** Edge test reveals new interpretation for indicator value

**Example - Adding absorption zone skip rule to prompt:**

```python
# BEFORE (generic volume section)
ENTRY_PROMPT_TEMPLATE = """
...
7. **Volume Analysis Section**
   - M1 Delta (5-bar): {delta_5bar}
   - Volume ROC: {volume_roc}%
...
"""

# AFTER (with edge-derived skip rule)
ENTRY_PROMPT_TEMPLATE = """
...
7. **Volume Analysis Section**
   - M1 Delta (5-bar): {delta_5bar}
   - Volume ROC: {volume_roc}%
   - Candle Range: {candle_range}%

   **SKIP RULE (Edge-Validated):** If Candle Range < 0.12%, this is an
   ABSORPTION ZONE with 33% win rate vs 51% baseline. Skip this trade.
...
"""
```

#### 8.6.4 Updating Market Structure Weights

**Based on structure_edge test results:**

```python
# In 04_dow_ai/calculations/market_structure.py or config.py

# CONFLUENCE WEIGHTS (from edge testing)
STRUCTURE_WEIGHTS = {
    'h1': 1.5,   # Strongest predictor - 30-54pp effects
    'm15': 1.0,  # Second strongest - 24-31pp effects
    'm5': 0.5,   # Entry timeframe - 19-25pp effects
    'h4': 0.0,   # Excluded - insufficient data
}
```

---

### 8.7 Supabase-Integrated Analysis Queries

**Use these queries to pull analysis data for DOW AI updates:**

```python
# In Python - using SupabaseClient from Module 12
from data.supabase_client import SupabaseClient

client = SupabaseClient()

# Get indicator performance by model
indicator_data = client.fetch_indicator_refinement(
    date_from='2026-01-01',
    date_to='2026-01-21',
    models=['EPCH01', 'EPCH02', 'EPCH03', 'EPCH04']
)

# Get stop analysis for win rate by stop type
stop_data = client.fetch_stop_analysis(
    date_from='2026-01-01',
    date_to='2026-01-21',
    stop_types=['zone_buffer', 'atr_1x', 'structure']
)

# Get entry indicators for health score correlation
entry_data = client.fetch_entry_indicators(
    date_from='2026-01-01',
    date_to='2026-01-21'
)

# Join with trades to get win rates
merged = entry_data.merge(
    client.fetch_trades(date_from='2026-01-01', date_to='2026-01-21'),
    on='trade_id'
)
```

---

### 8.8 Weekly Update Checklist

**Every Friday/Saturday:**

- [ ] Run all 7 indicator edge tests
- [ ] Review reports for edges with HIGH confidence
- [ ] Document any new edges using template (8.5)
- [ ] For edges with effect > 10pp:
  - [ ] Identify DOW AI file to update
  - [ ] Draft specific code change
  - [ ] Review with backtest comparison
  - [ ] Commit change with edge test reference
- [ ] Update skip rules in Entry Qualifier if needed
- [ ] Update prompt interpretation text if needed

---

### 8.9 Monthly Update Checklist

**End of each month:**

- [ ] Run full system analysis (30 days) in Module 12
- [ ] Export Monte AI prompt for comprehensive review
- [ ] Compare model performance trends (EPCH1-4)
- [ ] Review cumulative edge test findings
- [ ] Major prompt updates (if structural changes needed):
  - [ ] Update 10-step methodology weights
  - [ ] Revise confidence scoring logic
  - [ ] Add/remove indicators from analysis
- [ ] Version bump DOW AI prompt files
- [ ] Document all changes in changelog

---

### 8.10 Daily DOW AI Usage

**During live trading:**

```bash
cd C:\XIIITradingSystems\Epoch\04_dow_ai

# Entry analysis (reads zones from Supabase)
python main.py entry TICKER DIRECTION ZONE

# Exit analysis
python main.py exit TICKER ACTION ZONE

# Examples
python main.py entry NVDA long primary
python main.py entry TSLA short secondary
python main.py exit MSFT sell primary
python main.py exit AMZN cover secondary
```

---

### 8.11 EPCH Model Reference

| Model | Zone | Pattern | Direction Logic |
|-------|------|---------|-----------------|
| EPCH01 | PRIMARY | CONTINUATION | WITH zone direction |
| EPCH02 | PRIMARY | REVERSAL | AGAINST zone direction |
| EPCH03 | SECONDARY | CONTINUATION | WITH zone direction |
| EPCH04 | SECONDARY | REVERSAL | AGAINST zone direction |

---

### 8.12 Validated Skip Rules (From Edge Testing)

**Absorption Zone Rule:**
- **Condition:** Candle Range < 0.12%
- **Action:** SKIP ALL TRADES
- **Evidence:** 33% win rate vs 51% baseline (18pp disadvantage)
- **Confidence:** HIGH (>1000 trades tested)

**Structure Alignment Rule:**
- **Condition:** H1 structure AGAINST trade direction on EPCH4
- **Action:** SKIP or reduce position size
- **Evidence:** 54pp disadvantage when misaligned
- **Confidence:** HIGH

**Volume Delta Rule:**
- **Condition:** Vol Delta magnitude < 50k on LONG trades
- **Action:** Reduce confidence level
- **Evidence:** 20pp disadvantage on low-magnitude delta
- **Confidence:** HIGH

---

## 9. Quick Reference Commands

### Pre-Market Analysis
```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool
streamlit run app.py
# Then: Export to Supabase (critical!)
```

### Live Trading
```bash
# Entry Qualifier
cd C:\XIIITradingSystems\Epoch\04_dow_ai\entry_qualifier
python main.py

# DOW AI Analysis
cd C:\XIIITradingSystems\Epoch\04_dow_ai
python main.py entry NVDA long primary
```

### End-of-Day Processing
```bash
# Step 1: Backtest
cd C:\XIIITradingSystems\Epoch\05_analysis_tool\backtest
python backtest_runner.py

# Step 2: Secondary Analysis (CRITICAL - populates all tables)
cd processor/secondary_analysis
python run_all.py
```

### Daily Review
```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\12_system_analysis
streamlit run app.py --server.port 8502
# Filter to single date for daily review
```

### Training
```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\10_training
streamlit run app.py
```

### Indicator Testing
```bash
cd C:\XIIITradingSystems\Epoch\03_indicators\python
python -m volume_delta.volume_delta_edge
python -m candle_range.candle_range_edge
```

---

## 10. Troubleshooting

### Common Issues

**Analysis Tool won't start:**
- Check Polygon API key in `.env`
- Verify virtual environment activated
- Check Streamlit installed: `pip install streamlit`

**Backtest fails with "No zones found":**
- Ensure morning analysis was exported to Supabase
- Check `setups` table has data for the date
- Verify Supabase connection in credentials.py

**Secondary analysis shows 0 trades:**
- Run primary backtest first
- Check `trades` table has data for the date
- Verify date format (YYYY-MM-DD)

**System Analysis dashboard empty:**
- Check Supabase credentials in config.py
- Verify `trades` table has data in date range
- Check internet connection

**Training app shows no trades:**
- Run secondary analysis first (populates `mfe_mae_potential`)
- Run `python run_schema.py` if first time
- Check date range filter settings

**DOW AI shows "No zone found":**
- Ensure morning analysis exported to Supabase
- Verify ticker has a setup for the specified zone type
- Check DATA_SOURCE = 'supabase' in config.py

### Database Connection Test

```python
# Quick test of Supabase connection
cd C:\XIIITradingSystems\Epoch\02_zone_system\12_system_analysis
python -c "from data.supabase_client import get_client; c = get_client(); print(c.get_trade_count())"
```

---

## Workflow Checklists

### Daily (Pre-Market) - 7:00-8:30 AM ET
- [ ] Launch Analysis Tool (`streamlit run app.py`)
- [ ] Enter tickers and anchor dates
- [ ] Run analysis pipeline
- [ ] **Export to Supabase** (critical!)
- [ ] Generate PDF report (optional)

### Daily (Trading) - 9:30 AM - 4:00 PM ET
- [ ] Launch Entry Qualifier for monitoring
- [ ] Run DOW AI entry analysis for setups
- [ ] Execute trades based on analysis
- [ ] Run DOW AI exit analysis when exiting

### Daily (Post-Market) - 4:00-8:00 PM ET
- [ ] Run primary backtest (`python backtest_runner.py`)
- [ ] **Run secondary analysis** (`python run_all.py`) - critical!
- [ ] Review results in System Analysis dashboard
- [ ] Use Monte AI for Claude-friendly summary (optional)

### Weekly (Friday/Saturday)
- [ ] Run indicator edge tests
- [ ] Review weekly performance in System Analysis
- [ ] Use Monte AI for comprehensive analysis
- [ ] Update indicator parameters if needed

### Monthly (End of Month)
- [ ] Full system analysis (30-day range)
- [ ] Training calibration session (100+ trades)
- [ ] Review and update DOW AI prompts
- [ ] Zone performance metrics review

---

## Supabase Tables Reference

### Core Tables (Written by Analysis Tool & Backtest)

| Table | Source | Key Fields |
|-------|--------|------------|
| `daily_sessions` | Analysis Tool | date, export_source |
| `zones` | Analysis Tool | zone_id, ticker, zone_high, zone_low, rank |
| `setups` | Analysis Tool | ticker_id, setup_type, direction, target_price |
| `trades` | Backtest Runner | trade_id, model, pnl_r, is_winner |

### Enrichment Tables (Written by Secondary Analysis)

| Table | Processor Step | Key Fields |
|-------|----------------|------------|
| `m1_bars` | 1 | ticker, bar_date, bar_time, OHLCV |
| `h1_bars` | 2 | ticker, bar_date, bar_time, OHLCV |
| `mfe_mae_potential` | 3 | mfe_r_potential, mae_r_potential, is_winner |
| `entry_indicators` | 4 | health_score, vwap_aligned, structure_aligned |
| `m5_indicator_bars` | 5 | vwap, sma9, sma21, vol_roc, vol_delta |
| `m5_trade_bars` | 7 | health_score, health_label, all indicators |
| `optimal_trade` | 8 | event_type, price_at_event, health_score |
| `stop_analysis` | 12 | stop_type, outcome, r_achieved |
| `indicator_refinement` | 13 | continuation_score, rejection_score |

---

## Appendix A: Update Tracking Log Template

Use this template to document DOW AI updates based on edge testing results. Save logs to `04_dow_ai/update_logs/` for audit trail.

### Template: Edge-Derived Update Log

```markdown
================================================================================
DOW AI UPDATE LOG
================================================================================
Date: [YYYY-MM-DD]
Updated By: [Name]
Version: [From X.X to Y.Y]

--------------------------------------------------------------------------------
EDGE TEST SOURCE
--------------------------------------------------------------------------------
Indicator: [e.g., Candle Range]
Test File: 03_indicators/python/[indicator]/results/[indicator]_edge_[timestamp].md
Date Range Tested: [YYYY-MM-DD] to [YYYY-MM-DD]
Total Trades Analyzed: [N]
Baseline Win Rate: [X.X%]

--------------------------------------------------------------------------------
FINDING SUMMARY
--------------------------------------------------------------------------------
Test Name: [e.g., Range Threshold (0.15%)]
Segment: [ALL / LONG / SHORT / EPCH1 / EPCH2 / EPCH3 / EPCH4]
Edge Detected: [YES / NO]
Effect Size: [X.X pp]
P-Value: [0.XXXX]
Confidence Level: [HIGH / MEDIUM / LOW]

Group Statistics:
| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| [A]   | [N]    | [W]  | [X.X%]   | [+/-X.Xpp]  |
| [B]   | [N]    | [W]  | [X.X%]   | [+/-X.Xpp]  |

--------------------------------------------------------------------------------
RECOMMENDATION (from edge report)
--------------------------------------------------------------------------------
"[Paste exact recommendation text from the edge test report]"

--------------------------------------------------------------------------------
DOW AI CHANGES MADE
--------------------------------------------------------------------------------
File 1: [path/to/file.py]
  Line: [N]
  Before: [old code/value]
  After: [new code/value]

File 2: [path/to/file.py]
  Line: [N]
  Before: [old code/value]
  After: [new code/value]

--------------------------------------------------------------------------------
RATIONALE
--------------------------------------------------------------------------------
[Explain why this change improves trading outcomes based on the edge evidence]

--------------------------------------------------------------------------------
VALIDATION PLAN
--------------------------------------------------------------------------------
- [ ] Run backtest comparison (before vs after)
- [ ] Monitor next week's live performance
- [ ] Review in monthly analysis

Expected Improvement: [X.X pp win rate increase on [segment]]

================================================================================
```

### Example: Completed Update Log

```markdown
================================================================================
DOW AI UPDATE LOG
================================================================================
Date: 2026-01-21
Updated By: System
Version: From 1.0 to 1.1

--------------------------------------------------------------------------------
EDGE TEST SOURCE
--------------------------------------------------------------------------------
Indicator: Candle Range
Test File: 03_indicators/python/candle_range/results/candle_range_edge_20260117_114407.md
Date Range Tested: 2025-12-15 to 2026-01-16
Total Trades Analyzed: 2,788
Baseline Win Rate: 44.4%

--------------------------------------------------------------------------------
FINDING SUMMARY
--------------------------------------------------------------------------------
Test Name: Absorption Zone (<0.12%)
Segment: ALL
Edge Detected: YES
Effect Size: 18.0 pp
P-Value: 0.0000
Confidence Level: HIGH

Group Statistics:
| Group      | Trades | Wins | Win Rate | vs Baseline |
|------------|--------|------|----------|-------------|
| ABSORPTION | 1,066  | 355  | 33.3%    | -11.1pp     |
| NORMAL     | 1,722  | 883  | 51.3%    | +6.9pp      |

--------------------------------------------------------------------------------
RECOMMENDATION (from edge report)
--------------------------------------------------------------------------------
"SKIP FILTER VALIDATED - Absorption zone (33.3% WR) underperforms normal
(51.3% WR). Effect: 18.0pp. Implement skip rule for candle range < 0.12%."

--------------------------------------------------------------------------------
DOW AI CHANGES MADE
--------------------------------------------------------------------------------
File 1: 04_dow_ai/entry_qualifier/calculations/scores.py
  Line: 45
  Before: # No absorption check
  After: if candle_range < 0.12: return "SKIP - ABSORPTION ZONE"

File 2: 04_dow_ai/analysis/prompts/entry_prompt.py
  Line: 127
  Before: - Candle Range: {candle_range}%
  After: - Candle Range: {candle_range}%
         **SKIP RULE:** If < 0.12%, SKIP (33% WR vs 51% baseline)

--------------------------------------------------------------------------------
RATIONALE
--------------------------------------------------------------------------------
Absorption zones (candle range < 0.12%) show price compression indicating
institutional accumulation/distribution. These conditions produce 18pp lower
win rates because directional moves are absorbed by large orders. Skipping
these setups should improve overall system win rate by 6-8pp.

--------------------------------------------------------------------------------
VALIDATION PLAN
--------------------------------------------------------------------------------
- [x] Run backtest comparison (before vs after)
- [ ] Monitor next week's live performance
- [ ] Review in monthly analysis

Expected Improvement: +6.0 pp win rate increase on ALL trades

================================================================================
```

---

*Document generated by Claude Code - EPOCH Trading System v2.0 (Supabase-First)*
