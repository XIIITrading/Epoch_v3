================================================================================
EPOCH TRADING SYSTEM - MODULE 02: ZONE SYSTEM
SUB-MODULE 12: INDICATOR ANALYSIS
XIII Trading LLC | Documentation v1.0
================================================================================

PURPOSE
-------
The purpose of this module is to provide statistical analysis via a Streamlit
front-end interface that will help identify and improve:

1. Pre-Market Ticker Selection Via the Market Screener
   - Craft: https://s.craft.me/MWnRy5E42qx8OK
   - Path: C:\XIIITradingSystems\Epoch\01_market_scanner

2. Model Use, Efficacy, and Modification via a Monte Carlo Simulation
   - Craft:
   - Path: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest

3. Entry and Exit Improvements via Validated Grading System
   - Craft:
   - Path: C:\XIIITradingSystems\Epoch\03_indicators

4. DOW AI Trading Assistant Improvement via Above Findings
   - Craft:
   - Path: C:\XIIITradingSystems\Epoch\04_dow_ai

DIRECTORY
---------
Path: C:\XIIITradingSystems\Epoch\02_zone_system\12_indicator_analysis

================================================================================
FILE INVENTORY
================================================================================

FILE: app.py
------------
Role: PRIMARY ENTRY POINT - Main Streamlit application for indicator analysis.

Run Command: streamlit run app.py --server.port 8502

Key Features:
  - Sidebar filtering (date, models, direction, tickers, outcome)
  - Two main tabs: "Metrics Overview" and "Archived Analysis"
  - Data caching for performance (TTL=300s for trades, 600s for metadata)
  - Integration with Supabase PostgreSQL backend

Main Functions:
  load_trades() -> List[Dict]:
    - Fetches trades from database with applied filters
    - Cached for 300 seconds

  load_optimal_trades() -> List[Dict]:
    - Fetches optimal_trade data (indicator snapshots at key events)
    - Cached for 300 seconds

  load_mfe_mae_potential() -> List[Dict]:
    - Fetches MFE/MAE potential data for trade management analysis
    - Cached for 300 seconds

  load_trade_bars() -> List[Dict]:
    - Fetches trade_bars data (bar-by-bar indicator values)
    - Cached for 300 seconds

  get_metadata() -> Dict:
    - Returns available tickers, models, and date range
    - Cached for 600 seconds

  main():
    - Main application logic and rendering

Request this file for: Application startup issues, caching configuration,
tab structure changes, data loading modifications.

--------------------------------------------------------------------------------

FILE: config.py
---------------
Role: Central configuration hub - database settings, model definitions, and
calculation parameters.

Database Settings:
  DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "[encrypted]",
    "sslmode": "require"
  }

Entry Models:
  EPCH1: Continuation model, primary zone
  EPCH2: Rejection model, primary zone
  EPCH3: Continuation model, secondary zone
  EPCH4: Rejection model, secondary zone

SMA Configuration:
  fast_period: 9
  slow_period: 21
  momentum_lookback: 10
  widening_threshold: 1.1
  narrowing_threshold: 0.9

Volume ROC Configuration:
  baseline_period: 20
  above_avg_threshold: +20%
  below_avg_threshold: -20%

Volume Delta Configuration:
  rolling_period: 5

CVD Configuration:
  window: 15 bars
  rising_threshold: +0.1
  falling_threshold: -0.1

Structure Configuration:
  fractal_length: 5

Health Score Configuration:
  max_score: 10 points
  Labels: STRONG (8-10), MODERATE (6-7), WEAK (4-5), CRITICAL (0-3)

Request this file for: Database connection issues, parameter tuning,
model definitions, threshold adjustments.

--------------------------------------------------------------------------------

FILE: credentials.py
--------------------
Role: API credentials for Supabase and Polygon.

Contains:
  - SUPABASE_URL, SUPABASE_KEY
  - POLYGON_API_KEY

Request this file for: Authentication issues, credential rotation.

--------------------------------------------------------------------------------

FILE: data/supabase_client.py
-----------------------------
Role: PostgreSQL database access layer via Supabase.

Class: SupabaseClient
  Connection Management:
    - Singleton pattern via get_client() function
    - Auto-reconnect if connection closed
    - Error handling with rollback on failure

  Core Methods:
    fetch_trades(date_from, date_to, models, directions, tickers, limit=10000):
      - Returns: List[Dict] of trade records
      - Filters applied at database level

    fetch_optimal_trades(date_from, date_to, models, event_types, limit=50000):
      - Returns: List[Dict] of optimal_trade records
      - Contains indicator snapshots at ENTRY, MFE, MAE, EXIT events

    fetch_mfe_mae_potential(date_from, date_to, models, directions, limit=50000):
      - Returns: List[Dict] of MFE/MAE potential data
      - Used for trade management efficiency analysis

    fetch_trade_bars(trade_ids, date_from, date_to, limit=100000):
      - Returns: List[Dict] of bar-by-bar data
      - Contains all indicator values for each bar

    fetch_trade_bars_grouped(trade_ids, date_from, date_to):
      - Returns: Dict[trade_id: List] grouped by trade
      - Optimized for trade-level analysis

    get_available_tickers() -> List[str]:
      - Returns distinct ticker list from database

    get_available_models() -> List[str]:
      - Returns distinct model list from database

    get_date_range() -> Dict:
      - Returns min_date, max_date from trades table

    get_trade_count() -> int:
      - Returns total trade count in database

Request this file for: Database query issues, adding new queries,
connection problems, filter logic.

--------------------------------------------------------------------------------

FILE: components/filters.py
---------------------------
Role: Sidebar filter UI components for Streamlit.

Function: render_filters(tickers, models) -> Dict
  Returns filter selections:
    models: List[str] - Selected models (EPCH1-4)
    directions: List[str] or None - ["LONG"], ["SHORT"], or None (all)
    tickers: List[str] or None - Selected tickers or None (all)
    outcome: str - "All", "Winners", or "Losers"
    trade_type: str - "All", "Continuation", or "Rejection"

Filter Chain Logic:
  1. Model selection (all or specific)
  2. Trade type (continuation/rejection) auto-filters models
  3. Direction (long/short/all)
  4. Ticker multiselect
  5. Outcome (all/winners/losers)

Request this file for: Adding new filters, modifying filter behavior,
UI layout changes.

--------------------------------------------------------------------------------

FILE: components/summary_cards.py
---------------------------------
Role: Metric display cards for summary statistics.

Functions:
  render_summary_cards(stats: Dict):
    - Displays 5 metric cards in row
    - Total Trades, Wins, Losses, Win Rate, Avg R

  render_model_cards(model_stats: List[Dict]):
    - Displays card per model with key metrics
    - Win rate, total R, trade count

Request this file for: Adding new summary metrics, card styling.

--------------------------------------------------------------------------------

FILE: components/charts.py
--------------------------
Role: Plotly chart rendering functions with dark theme.

Theme Configuration:
  Background: #1a1a2e
  Paper: #16213e
  Text: #e0e0e0
  Win color: #26a69a (teal)
  Loss color: #ef5350 (red)

Functions:
  render_win_rate_chart(data):
    - Bar chart with 50% reference line
    - Used for model comparison

  render_indicator_distribution(df, indicator, by_outcome=True):
    - Overlaid histogram (winners vs losers)
    - Shows distribution differences

  render_health_heatmap(df):
    - Heatmap of health score vs win rate by model
    - Visual correlation analysis

  render_indicator_by_event(stats):
    - Bar chart by event type (ENTRY/MFE/MAE/EXIT)
    - Shows indicator progression

  render_comparison_chart(cont_stats, rej_stats):
    - Continuation vs Rejection side-by-side
    - Model type comparison

Request this file for: Adding new chart types, theme changes,
visualization modifications.

--------------------------------------------------------------------------------

FILE: components/prompt_generator.py
------------------------------------
Role: Claude analysis prompt generation for archived analysis sections.

Functions:
  generate_analysis_prompt(context, data_summary):
    - Creates full analysis prompt with context
    - Includes relevant data summary

  format_data_for_prompt(df, max_rows=100):
    - Formats DataFrame for prompt inclusion
    - Limits rows to prevent token overflow

Request this file for: Prompt template changes, context formatting.

--------------------------------------------------------------------------------

FILE: analysis/trade_stats.py
-----------------------------
Role: Trade-level statistics calculation.

Function: get_trade_statistics(trades: List[Dict]) -> Dict
  Returns:
    total: int - Total trade count
    wins: int - Count where is_winner=True
    losses: int - Count where is_winner=False
    win_rate: float - Win percentage (0-100)
    avg_r: float - Average pnl_r
    total_r: float - Sum of pnl_r

Related Functions:
  get_stats_by_model(trades) -> List[Dict]:
    - Returns stats grouped by model

  get_stats_by_direction(trades) -> Dict:
    - Returns stats by LONG/SHORT

  get_stats_by_exit_reason(trades) -> Dict:
    - Returns stats grouped by exit reason

Request this file for: Adding new statistics, modifying calculations.

--------------------------------------------------------------------------------

FILE: analysis/indicator_stats.py
---------------------------------
Role: Indicator-level statistics and comparisons.

Indicator Columns Analyzed:
  - health_score, vwap, sma9, sma21, sma_spread
  - vol_roc, vol_delta, cvd_slope, sma_momentum
  - m5_structure, m15_structure, h1_structure, h4_structure

Functions:
  get_indicator_averages(df, indicator, by_model=False):
    - Returns avg/median/std for indicator
    - Optionally grouped by model

  get_indicator_by_event(df, indicator):
    - Returns stats by event type (ENTRY/MFE/MAE/EXIT)
    - Shows indicator progression through trade

  get_indicator_by_outcome(df, indicator):
    - Returns stats for winners vs losers
    - Key for identifying predictive indicators

  get_indicator_comparison_by_outcome(df, indicators):
    - Average values winners vs losers for multiple indicators
    - Returns Dict with "winners" and "losers" keys

  get_health_distribution(df):
    - Returns health score value counts
    - For histogram display

Request this file for: Adding indicator analysis, new comparison methods.

--------------------------------------------------------------------------------

FILE: analysis/model_comparison.py
----------------------------------
Role: Continuation vs Rejection model comparison.

Functions:
  compare_continuation_rejection(trades):
    - Compares EPCH1/3 (continuation) vs EPCH2/4 (rejection)
    - Returns stats for both model types

  get_model_type(model):
    - Returns "continuation" or "rejection" based on model

Request this file for: Model type classification, comparison logic.

================================================================================
CALCULATIONS DIRECTORY
================================================================================

SUBDIRECTORY: calculations/indicators/
--------------------------------------

FILE: sma.py
------------
Role: SMA9/SMA21 and momentum calculations.

Functions:
  calculate_sma(bars, period, up_to_index, price_key="close"):
    - Returns: Optional[float] - Simple moving average

  calculate_sma_spread(bars, up_to_index, fast_period=9, slow_period=21):
    - Returns: SMAResult dataclass
      - sma9: float
      - sma21: float
      - spread: float (sma9 - sma21)
      - alignment: "BULLISH" or "BEARISH"
      - cross_estimate: float

  calculate_sma_momentum(bars, up_to_index, lookback=10):
    - Returns: SMAMomentumResult dataclass
      - spread_now: float
      - spread_prev: float
      - momentum: "WIDENING" | "NARROWING" | "FLAT"
      - ratio: float (current / previous)

  is_sma_alignment_healthy(sma9, sma21, direction):
    - Returns: bool - True if SMA aligned with trade direction

  is_sma_momentum_healthy(momentum):
    - Returns: bool - True if spread widening

Request this file for: SMA period changes, momentum logic.

--------------------------------------------------------------------------------

FILE: vwap.py
-------------
Role: VWAP calculation and price position analysis.

Formula: VWAP = Cumulative(TP x Volume) / Cumulative(Volume)
         TP = (High + Low + Close) / 3

Functions:
  calculate_vwap(bars, up_to_index):
    - Returns: Optional[float] - Cumulative VWAP value

  calculate_vwap_metrics(bars, up_to_index, current_price):
    - Returns: VWAPResult dataclass
      - vwap: float
      - price_diff: float (price - vwap)
      - price_pct: float (percentage difference)
      - side: "ABOVE" | "BELOW" | "AT"

  is_vwap_healthy(price, vwap, direction):
    - Returns: bool - True if price position aligned with direction

Request this file for: VWAP calculation modifications.

--------------------------------------------------------------------------------

FILE: volume_roc.py
-------------------
Role: Volume Rate of Change calculation.

Formula: ROC = ((current_vol - baseline_avg) / baseline_avg) x 100
         Baseline period: 20 bars
         Classification: >+20% (Above Avg), <-20% (Below Avg)

Functions:
  calculate_volume_roc(bars, up_to_index, baseline_period=20):
    - Returns: VolumeROCResult dataclass
      - roc: float (percentage)
      - signal: str
      - current_volume: int
      - baseline_avg: float

  classify_volume_roc(roc):
    - Returns: str - "Above Avg", "Below Avg", or "Average"

  is_volume_roc_healthy(roc, threshold=20):
    - Returns: bool - True if ROC above threshold

Request this file for: Baseline period changes, threshold adjustments.

--------------------------------------------------------------------------------

FILE: volume_delta.py
---------------------
Role: Volume delta calculation using bar position method.

Formula (Bar Position Method):
  bar_position = (close - low) / (high - low)
  delta_multiplier = (2 x bar_position) - 1
  bar_delta = volume x delta_multiplier

Functions:
  calculate_bar_delta(bar):
    - Returns: BarDeltaResult dataclass
      - bar_delta: float
      - bar_position: float (0-1)
      - delta_multiplier: float (-1 to +1)

  calculate_bar_delta_from_dict(bar_dict):
    - Returns: BarDeltaResult from dictionary input

  calculate_rolling_delta(bars, up_to_index, period=5):
    - Returns: RollingDeltaResult dataclass
      - rolling_delta: float (sum of 5 bars)
      - signal: "Bullish" | "Bearish" | "Neutral"
      - bar_count: int

  is_volume_delta_healthy(delta, direction):
    - Returns: bool - Positive for LONG, negative for SHORT

Request this file for: Rolling period changes, delta formula.

--------------------------------------------------------------------------------

FILE: cvd.py
------------
Role: Cumulative Volume Delta slope calculation.

Process:
  1. Calculate bar deltas (bar position method)
  2. Cumulative sum for CVD series
  3. Linear regression slope on last 15 bars
  4. Normalize by CVD range
  5. Classify: Rising (>+0.1), Falling (<-0.1), Flat

Functions:
  calculate_cvd_slope(bars, up_to_index, window=15):
    - Returns: CVDResult dataclass
      - slope: float (normalized, typically -2 to +2)
      - trend: str (Rising/Falling/Flat)
      - cvd_values: List[float] (last 15 values)
      - window_size: int

  classify_cvd_trend(slope):
    - Returns: str - "Rising", "Falling", or "Flat"

  is_cvd_healthy(slope, direction):
    - Returns: bool - Rising for LONG (>+0.1), falling for SHORT (<-0.1)

Request this file for: Window size changes, slope thresholds.

--------------------------------------------------------------------------------

SUBDIRECTORY: calculations/structure/
-------------------------------------
Role: Multi-timeframe structure detection using fractal/swing analysis.

Files: m5_structure.py, m15_structure.py, h1_structure.py, h4_structure.py
(All use identical logic, different timeframe context)

Method:
  - Looks for higher highs/lower lows over 5-bar window
  - Returns: "BULL", "BEAR", or "NEUTRAL"
  - Confidence levels: HIGH, MEDIUM, LOW

Function: detect_[timeframe]_structure(bars, up_to_index, fractal_length=5)
  Returns: StructureResult dataclass
    - swing_high: float (previous high)
    - swing_low: float (previous low)
    - structure: str ("BULL", "BEAR", "NEUTRAL")
    - confidence: str ("HIGH", "MEDIUM", "LOW")

Request these files for: Fractal length changes, structure detection logic.

--------------------------------------------------------------------------------

SUBDIRECTORY: calculations/health/
----------------------------------

FILE: health_score.py
---------------------
Role: 10-factor health score calculation system.

10 Factors (1 point each, max 10):
  1. H4 Structure - Aligned with direction (BULL for LONG)
  2. H1 Structure - Aligned with direction
  3. M15 Structure - Aligned with direction
  4. M5 Structure - Aligned with direction
  5. Volume ROC - Above +20% threshold
  6. Volume Delta - Positive for LONG, negative for SHORT
  7. CVD Slope - Rising for LONG (>+0.1), falling for SHORT (<-0.1)
  8. SMA Alignment - SMA9 > SMA21 for LONG, < for SHORT
  9. SMA Momentum - Spread WIDENING (ratio > 1.1)
  10. VWAP - Price above VWAP for LONG, below for SHORT

Score Labels:
  8-10: STRONG (green)
  6-7: MODERATE (yellow)
  4-5: WEAK (orange)
  0-3: CRITICAL (red)

Function: calculate_health_score(...) -> HealthScoreResult
  Returns:
    - score: int (0-10)
    - label: str (STRONG/MODERATE/WEAK/CRITICAL)
    - score_pct: float
    - Individual boolean flags for each factor
    - Alignment groups: htf_aligned, mtf_aligned, volume_aligned, indicator_aligned

Request this file for: Adding/removing factors, weight changes, threshold tuning.

--------------------------------------------------------------------------------

FILE: thresholds.py
-------------------
Role: Configurable thresholds for health score factors.

Contains:
  - VOLUME_ROC_THRESHOLD: 20 (percent)
  - CVD_RISING_THRESHOLD: 0.1
  - CVD_FALLING_THRESHOLD: -0.1
  - SMA_WIDENING_THRESHOLD: 1.1
  - HEALTH_SCORE_LABELS: Dict mapping score ranges to labels

Request this file for: Threshold value adjustments.

--------------------------------------------------------------------------------

SUBDIRECTORY: calculations/derived/
-----------------------------------

FILE: mfe_mae.py
----------------
Role: MFE/MAE with R-multiple calculations.

Functions:
  calculate_mfe_r(entry_price, mfe_price, stop_price, direction):
    - Returns: float - MFE in R-multiples

  calculate_mae_r(entry_price, mae_price, stop_price, direction):
    - Returns: float - MAE in R-multiples

Request this file for: R-multiple calculation logic.

--------------------------------------------------------------------------------

FILE: trade_outcome.py
----------------------
Role: Trade outcome classification.

Functions:
  classify_outcome(pnl_r):
    - Returns: str - "WIN", "LOSS", or "BREAKEVEN"

  get_outcome_category(actual_r):
    - Returns: str - Detailed category (e.g., "Big Win", "Small Loss")

Request this file for: Outcome classification rules.

--------------------------------------------------------------------------------

SUBDIRECTORY: calculations/model/
---------------------------------

FILE: win_rate_by_model.py
--------------------------
Role: CALC-001 - System-wide performance baseline for Monte Carlo simulation.

Purpose: Provides unfiltered win rate breakdown by model for Monte Carlo inputs.

Function: calculate_win_rate_by_model(trades: List[Dict]) -> pd.DataFrame
  Input: Raw trades with 'model' and 'is_winner' columns
  Output DataFrame:
    Model | Wins | Losses | Win% | Expectancy
    EPCH1 |  42  |   18   | 70.0 |    1.23
    EPCH2 |  35  |   25   | 58.3 |    0.87
    EPCH3 |  48  |   15   | 76.2 |    1.45
    EPCH4 |  29  |   31   | 48.3 |   -0.12

Display Functions:
  render_model_summary_table(df):
    - Transposed table display for Streamlit

  render_model_win_loss_chart(df):
    - Grouped bar chart (green wins, red losses)

  render_model_breakdown(df):
    - Convenience function rendering both table and chart

IMPORTANT: Shows FULL system (unfiltered) for Monte Carlo baseline.

Request this file for: Win rate calculation, Monte Carlo integration.

--------------------------------------------------------------------------------

SUBDIRECTORY: calculations/trade_management/
--------------------------------------------

FILE: mfe_mae_stats.py
----------------------
Role: CALC-002 - MFE/MAE distribution analysis for trade management research.

Purpose: Analyze trade management efficiency using percentage-based MFE/MAE.

Data Source: mfe_mae_potential table
  - entry_price
  - mfe_potential_price (best price from entry to 15:30 ET)
  - mae_potential_price (worst price from entry to 15:30 ET)
  - direction (LONG/SHORT)
  - model (EPCH01-04)

Percentage Calculations:
  For LONG:
    MFE% = (mfe_potential_price - entry_price) / entry_price x 100
    MAE% = (entry_price - mae_potential_price) / entry_price x 100

  For SHORT:
    MFE% = (entry_price - mfe_potential_price) / entry_price x 100
    MAE% = (mae_potential_price - entry_price) / entry_price x 100

Function: calculate_mfe_mae_summary(data) -> Dict[str, Any]
  Returns:
    median_mfe_pct: float - Median favorable move
    median_mae_pct: float - Median adverse move
    mean_mfe_pct: float
    mean_mae_pct: float
    mfe_pct_q25: float - 25th percentile
    mfe_pct_q75: float - 75th percentile
    mae_pct_q25: float
    mae_pct_q75: float
    median_mfe_mae_ratio: float - Favorable/adverse ratio
    pct_mfe_above_0_5: float - % trades reaching 0.5% favorable
    pct_mfe_above_1_0: float - % trades reaching 1.0% favorable
    pct_mae_below_0_5: float - % trades with <0.5% adverse
    total_trades: int

Function: calculate_mfe_mae_by_model(data) -> pd.DataFrame
  Output Columns:
    Model | Direction | Trades | Med MFE% | Med MAE% | MAE P75% | MFE/MAE Ratio

Display Functions:
  render_mfe_mae_summary_cards(summary):
    - 8 metric cards with key statistics

  render_mfe_histogram(df, column="mfe_pct"):
    - Distribution with 0.5%/1.0% reference lines

  render_mae_histogram(df, column="mae_pct"):
    - Distribution with 0.25%/0.5%/1.0% reference lines

  render_mfe_mae_scatter(df):
    - MFE vs MAE by model (diagonal = neutral)

  render_model_mfe_mae_table(df):
    - Breakdown by model and direction

Request this file for: Trade management analysis, stop/target research.

================================================================================
MONTE AI DIRECTORY
================================================================================

SUBDIRECTORY: monte_ai/
-----------------------
Role: Monte AI Research Assistant - Claude-powered analysis prompt generation.

FILE: ui.py
-----------
Role: Monte AI UI component for Streamlit.

Functions:
  render_metrics_overview_monte_ai(trades, mfe_mae_data, optimal_trades):
    - Top-level Monte AI UI for metrics tab
    - Generates comprehensive analysis prompts

  render_monte_ai_section(data, context):
    - Generic Monte AI section for archived analysis tabs
    - Context-aware prompt generation

Request this file for: Monte AI UI modifications, section placement.

--------------------------------------------------------------------------------

FILE: prompt_generator.py
-------------------------
Role: Prompt generation logic for Claude analysis.

Functions:
  generate_prompt(data, context, include_schema=True):
    - Creates full analysis prompt with database schema reference
    - Used for first-time/comprehensive analysis

  generate_quick_prompt(data, context):
    - Shorter follow-up prompt without schema
    - Used for iterative analysis

  get_prompt_stats(prompt):
    - Returns: Dict with chars, words, estimated tokens

Request this file for: Prompt template modifications, context formatting.

--------------------------------------------------------------------------------

FILE: prompts.py
----------------
Role: Prompt templates for different analysis types.

Contains:
  - SYSTEM_PROMPT: Base context for Claude
  - ANALYSIS_TEMPLATES: Dict of analysis-specific templates
  - SCHEMA_REFERENCE: Database schema for context

Request this file for: Adding new analysis types, template changes.

--------------------------------------------------------------------------------

FILE: data_collector.py
-----------------------
Role: Data collection and formatting for prompts.

Functions:
  collect_metrics_data(trades, mfe_mae, optimal):
    - Aggregates data from multiple sources
    - Formats for prompt inclusion

  format_dataframe_for_prompt(df, max_rows=100):
    - Limits rows to prevent token overflow
    - Formats for readability

Request this file for: Data aggregation logic, formatting changes.

================================================================================
STREAMLIT TAB STRUCTURE
================================================================================

TAB 1: METRICS OVERVIEW
-----------------------
Primary analysis dashboard with key metrics.

Sections:
  1. Summary Cards
     - Total Trades, Wins, Losses, Win Rate, Avg R
     - 5 cards in horizontal row

  2. Win Rate by Model (CALC-001)
     - FULL SYSTEM (unfiltered) for Monte Carlo baseline
     - Transposed table display
     - Grouped bar chart (wins/losses)

  3. Trade Management Efficiency (CALC-002)
     - MFE/MAE Potential analysis
     - 8 summary metric cards
     - MFE distribution histogram
     - MAE distribution histogram
     - MFE vs MAE scatter plot
     - Model breakdown table

  4. Monte AI Research Assistant
     - Claude analysis prompt generator
     - Generate, Copy, Download buttons

--------------------------------------------------------------------------------

TAB 2: ARCHIVED ANALYSIS
------------------------
Original analysis functionality organized in sub-tabs.

Sub-Tab: Overview
  - Summary cards
  - Win rate by model (filtered)
  - Continuation vs rejection comparison
  - Model cards
  - Claude analysis prompt

Sub-Tab: Continuation
  - Analysis of EPCH1/EPCH3 models
  - Summary stats
  - Direction breakdown (LONG/SHORT)
  - Exit reason breakdown
  - Indicator values at entry (winners vs losers)
  - Claude analysis prompt

Sub-Tab: Rejection
  - Analysis of EPCH2/EPCH4 models
  - Same structure as Continuation tab

Sub-Tab: Indicator Deep Dive
  - Indicator selector dropdown
  - Distribution histogram (at entry)
  - Value by event type chart
  - Continuation vs rejection comparison
  - Claude analysis prompt

Sub-Tab: Health Score
  - Health score distribution histogram
  - Health score statistics table
  - Health score heatmap by model
  - Threshold slider (0-10)
  - Win rate metrics above/below threshold
  - Claude analysis prompt

Sub-Tab: Raw Data
  - Toggle: Trades or Optimal Trade Events
  - Full DataFrame display (600px height)
  - CSV download button

================================================================================
DATA FLOW
================================================================================

                    ┌─────────────────────────────────────────┐
                    │      Supabase PostgreSQL Database       │
                    ├─────────────────────────────────────────┤
                    │ Tables:                                 │
                    │  - trades (base trade records)          │
                    │  - trade_bars (bars with indicators)    │
                    │  - optimal_trade (event snapshots)      │
                    │  - mfe_mae_potential (MFE/MAE data)     │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │   SupabaseClient (data/supabase_client) │
                    │   - Connection management               │
                    │   - Query building with filters         │
                    │   - Result parsing                      │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │          Streamlit app.py               │
                    │   - Data loading with @st.cache_data    │
                    │   - Sidebar filter rendering            │
                    │   - Filter application                  │
                    └────────────────┬────────────────────────┘
                                     │
          ┌──────────────┬───────────┼───────────┬──────────────┐
          ▼              ▼           ▼           ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Analysis  │  │Calculations│  │Components│  │Monte AI │  │  Docs   │
    │           │  │           │  │          │  │         │  │         │
    │trade_stats│  │indicators/│  │charts.py │  │ui.py    │  │*.txt    │
    │indicator_ │  │structure/ │  │filters.py│  │prompts  │  │         │
    │stats.py   │  │health/    │  │summary_  │  │prompt_  │  │         │
    │model_comp │  │derived/   │  │cards.py  │  │generator│  │         │
    │           │  │model/     │  │          │  │         │  │         │
    │           │  │trade_mgmt/│  │          │  │         │  │         │
    └───────────┘  └───────────┘  └──────────┘  └─────────┘  └─────────┘
          │              │             │             │
          └──────────────┴─────────────┴─────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────────────┐
                    │        Streamlit Rendering              │
                    │        Tabs / Cards / Charts            │
                    └─────────────────────────────────────────┘

================================================================================
DATABASE SCHEMA
================================================================================

TABLE: trades
-------------
Primary trade records from backtest system.

Columns:
  trade_id: str (primary key)
  date: date
  entry_time: timestamp
  ticker: str
  direction: str (LONG/SHORT)
  model: str (EPCH1-4)
  entry_price: float
  exit_price: float
  stop_price: float
  is_winner: bool
  pnl_r: float
  exit_reason: str
  bars_in_trade: int
  actual_r: float

--------------------------------------------------------------------------------

TABLE: trade_bars
-----------------
Bar-by-bar data with all indicator values for each trade.

Columns:
  trade_id: str (foreign key)
  date: date
  event_seq: int
  event_time: timestamp
  bars_from_entry: int
  event_type: str (ENTRY/MFE/MAE/EXIT/BAR)
  open_price, high_price, low_price, close_price: float
  volume: int
  r_at_event: float
  health_score: int
  vwap: float
  sma9, sma21: float
  sma_spread, sma_momentum: float
  vol_roc: float
  vol_delta: float
  cvd_slope: float
  m5_structure, m15_structure, h1_structure, h4_structure: str
  ticker, direction, model: str
  win: bool
  actual_r: float
  exit_reason: str

--------------------------------------------------------------------------------

TABLE: optimal_trade
--------------------
Indicator snapshots at key trade events (ENTRY, MFE, MAE, EXIT).

Columns:
  trade_id: str (foreign key)
  event_type: str (ENTRY/MFE/MAE/EXIT)
  date: date
  ticker: str
  direction: str
  model: str
  win: bool
  event_time: timestamp
  bars_from_entry: int
  price_at_event: float
  r_at_event: float
  health_score: int
  health_delta: float
  health_summary: str
  [All indicator columns same as trade_bars]
  actual_r: float
  exit_reason: str

--------------------------------------------------------------------------------

TABLE: mfe_mae_potential
------------------------
Maximum Favorable/Adverse Excursion from entry to 15:30 ET.

Columns:
  trade_id: str (foreign key)
  date: date
  ticker: str
  direction: str
  model: str
  entry_time: timestamp
  entry_price: float
  mfe_potential_price: float (best price reached)
  mfe_potential_time: timestamp
  mae_potential_price: float (worst price reached)
  mae_potential_time: timestamp
  bars_analyzed: int

================================================================================
KEY CONCEPTS
================================================================================

ENTRY MODELS
------------
EPCH1: Continuation model, primary zone
  - Trades WITH the trend at primary support/resistance
EPCH2: Rejection model, primary zone
  - Trades AGAINST the trend at primary support/resistance
EPCH3: Continuation model, secondary zone
  - Trades WITH the trend at secondary support/resistance
EPCH4: Rejection model, secondary zone
  - Trades AGAINST the trend at secondary support/resistance

HEALTH SCORE SYSTEM
-------------------
10-factor scoring system (0-10 points) measuring trade setup quality:
  - Structure alignment (4 factors): H4, H1, M15, M5
  - Volume factors (3 factors): Volume ROC, Volume Delta, CVD Slope
  - Price factors (3 factors): SMA Alignment, SMA Momentum, VWAP

Labels:
  STRONG (8-10): High probability setup
  MODERATE (6-7): Acceptable setup
  WEAK (4-5): Caution advised
  CRITICAL (0-3): High risk setup

MFE/MAE ANALYSIS
----------------
MFE (Maximum Favorable Excursion): Best price reached during trade
MAE (Maximum Adverse Excursion): Worst price reached during trade

Used for:
  - Stop placement optimization (MAE distribution)
  - Target placement optimization (MFE distribution)
  - Risk/reward ratio analysis (MFE/MAE ratio)

EVENT TYPES
-----------
ENTRY: Trade entry point
MFE: Maximum favorable excursion reached
MAE: Maximum adverse excursion reached
EXIT: Trade exit point
BAR: Regular bar during trade (trade_bars only)

MONTE CARLO INTEGRATION
-----------------------
Win Rate by Model (CALC-001) provides unfiltered baseline for:
  - Monte Carlo simulation inputs
  - Model efficacy comparison
  - System-wide performance assessment

================================================================================
DEPENDENCIES
================================================================================

Python Packages:
  - streamlit (web interface)
  - pandas (data manipulation)
  - plotly (interactive charts)
  - psycopg2 (PostgreSQL driver)
  - numpy (numerical operations)

External:
  - Supabase PostgreSQL database
  - Backtest data from 02_zone_system/09_backtest
  - Polygon.io API (for live data if needed)

================================================================================
COMMON MODIFICATION SCENARIOS
================================================================================

Add new indicator to health score:
  -> calculations/health/health_score.py: Add factor to calculation
  -> calculations/health/thresholds.py: Add threshold if needed
  -> Update max_score in config.py

Add new chart type:
  -> components/charts.py: Add render function
  -> app.py: Import and call in appropriate tab

Add new filter option:
  -> components/filters.py: Add to render_filters()
  -> app.py: Apply filter to data loading

Add new analysis tab:
  -> app.py: Add tab in tab structure
  -> Create analysis functions in analysis/
  -> Add display components in components/

Modify database queries:
  -> data/supabase_client.py: Update fetch methods
  -> Ensure proper parameterization for SQL injection safety

Add new Monte AI analysis type:
  -> monte_ai/prompts.py: Add template
  -> monte_ai/prompt_generator.py: Add generation logic
  -> monte_ai/ui.py: Add UI section

Change MFE/MAE calculation:
  -> calculations/trade_management/mfe_mae_stats.py: Update formulas
  -> Ensure consistency between LONG and SHORT calculations

================================================================================
USAGE
================================================================================

Start Application:
  cd C:\XIIITradingSystems\Epoch\02_zone_system\12_indicator_analysis
  streamlit run app.py --server.port 8502

Access:
  http://localhost:8502

Default Filters:
  - All models (EPCH1-4)
  - All directions (LONG/SHORT)
  - All tickers
  - All outcomes (Winners/Losers)
  - Full date range available in database

================================================================================
INTEGRATION POINTS
================================================================================

Input From:
  - 02_zone_system/09_backtest: Trade data, trade_bars, optimal_trade
  - 02_zone_system/11_database_export: Data export to Supabase

Output To:
  - 01_market_scanner: Ticker selection improvements
  - 02_zone_system/09_backtest: Model efficacy findings
  - 03_indicators: Entry/exit improvement research
  - 04_dow_ai: AI assistant improvement via findings

================================================================================
END OF DOCUMENTATION
================================================================================
