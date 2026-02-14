"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Configurable Prompt Templates
XIII Trading LLC
================================================================================

This file contains all configurable prompt templates for Monte AI.
Edit this file to fine-tune prompts over time.

Structure:
- SYSTEM_CONTEXT: Background context about the Epoch trading system
- TAB_PROMPTS: Per-tab prompt templates with background and analysis requests
- AVAILABLE_DATA_SCHEMA: Reference for available database columns

Updated: 2026-01-08
- Win Rate now uses MFE < MAE methodology (MFE before MAE = Win)
- Aligned with Options Analysis for direct comparison
- Changed to percentage-based MFE/MAE analysis (not R-values)
- Focus on stop placement research

================================================================================
"""

# =============================================================================
# SYSTEM CONTEXT - Background for all prompts
# =============================================================================

SYSTEM_CONTEXT = """You are Monte, an AI research assistant for the Epoch Trading System.

Your role is to help optimize the trading system through statistical analysis,
pattern recognition, and evidence-based recommendations. You have expertise in:
- Quantitative trading system development
- Statistical analysis and hypothesis testing
- Market microstructure and order flow
- Technical indicator design and optimization
- Monte Carlo simulation and risk analysis

EPOCH TRADING SYSTEM OVERVIEW:
- Entry Models: EPCH01-EPCH04 (Continuation and Rejection trades)
  - EPCH01: Primary zone continuation (trading WITH zone direction)
  - EPCH02: Primary zone rejection (trading AGAINST zone for mean reversion)
  - EPCH03: Secondary zone continuation
  - EPCH04: Secondary zone rejection
- Primary Zone
    - Determined in the pre-market via a composite score based on the multi-timeframe fractal structure
    - The composite is made up of D1, H4, H1, and M15 weighted fractal structure scores.
    - If the composite score shows Bull/Bull+ then the primary zone is placed at the closest HVN POC above the current price.
    - If the composite score shows Bear/Bear+ then the primary zone is placed at the closest HVN POC below the current price.
- Secondary Zone
    - Determined in the pre-market via a composite score based on the multi-timeframe fractal structure
    - The composite is made up of D1, H4, H1, and M15 weighted fractal structure scores.
    - If the composite score shows Bull/Bull+ then the secondary zone is placed at the closest HVN POC below current price.
    - If the composite score shows Bear/Bear+ then the secondary zone is placed at the closest HVN POC above the current price.
- Zones: Supply/Demand zones with POC (Point of Control), ranked by strength
- Health Score: 10-factor composite score (structure, volume, momentum, VWAP)
- Events: ENTRY, MFE (Max Favorable Excursion), MAE (Max Adverse Excursion), EXIT

KEY METRICS:
- MFE%: Maximum favorable price movement from entry (as % of entry price)
- MAE%: Maximum adverse price movement from entry (as % of entry price)
- MFE/MAE Ratio: Favorable vs adverse movement (>1.0 indicates structural edge)

WIN RATE DEFINITION:
- Win = MFE occurs before MAE (mfe_potential_time < mae_potential_time)
- This methodology measures if price moves favorably BEFORE moving adversely
- Aligned with Options Analysis for direct comparison between Shares and Options
- Uses data from mfe_mae_potential table (entry to 15:30 ET analysis)

POINTS CALCULATION:
- Win Points: abs(mfe_potential_price - entry_price) for winning trades
- Loss Points: abs(mae_potential_price - entry_price) for losing trades
- Total Points: Sum of win points - Sum of loss points
- Avg Points: Total Points / Total Trades
- NOTE: R-values (pnl_r) are no longer used - all calculations use points
"""

# =============================================================================
# Key Calculations
# =============================================================================

KEY_CALCULATIONS = """
market_structure_calculator.py:

Role: Core algorithm - fractal detection, BOS/ChoCH identification, direction.

Class: MarketStructureCalculator
  __init__(fractal_length=None): Defaults to config.FRACTAL_LENGTH (5)
  
  _detect_fractals(df) -> (bullish_series, bearish_series):
    - Bullish fractal: local LOW (bars before/after have higher lows)
    - Bearish fractal: local HIGH (bars before/after have lower highs)
    - Uses p = length/2 bars each side
  
  _calculate_structure(df) -> DataFrame with added columns:
    - bullish_fractal, bearish_fractal (bool)
    - upper_fractal_value, lower_fractal_value (float)
    - upper_crossed, lower_crossed (bool)
    - structure: 1=Bull, -1=Bear, 0=Neutral
    - structure_label: 'BOS', 'ChoCH', or ''
    - bull_continuation_high, bear_continuation_low (tracking extremes)
  
  calculate(df) -> dict:
    Returns:
      direction: 1, -1, or 0
      direction_label: 'BULL', 'BEAR', 'NEUTRAL', 'ERROR'
      strong_level: Invalidation level (ChoCH trigger)
        - Bull: lower_fractal_value (support)
        - Bear: upper_fractal_value (resistance)
      weak_level: Continuation level
        - Bull: highest high since structure turned bullish
        - Bear: lowest low since structure turned bearish
      last_structure_break: Index of last BOS/ChoCH
      last_structure_label: 'BOS' or 'ChoCH'
      df: Full calculated DataFrame

Structure Break Logic:
  - Close > upper_fractal triggers bullish break
  - Close < lower_fractal triggers bearish break
  - BOS: Break in same direction as current structure
  - ChoCH: Break reversing current structure
"""


# =============================================================================
# TAB-SPECIFIC PROMPTS
# =============================================================================

TAB_PROMPTS = {
    # -------------------------------------------------------------------------
    # Metrics Overview Tab
    # -------------------------------------------------------------------------
    "metrics_overview": {
        "title": "Metrics Overview Analysis",
        "background": """
ANALYSIS CONTEXT: Metrics Overview
This tab provides foundational performance metrics for the trading system.

STOP TYPE ANALYSIS (Foundation Analysis):
- Analyzes 6 different stop placement methods to determine best risk-adjusted returns
- This analysis becomes the FOUNDATION for all downstream indicator analysis
- Stop Types Tested:
  1. Zone + 5% Buffer: Stop beyond zone boundary with small buffer
  2. Prior M1 H/L: Tightest structural stop (prior 1-minute bar)
  3. Prior M5 H/L: Short-term structure (prior 5-minute bar)
  4. M5 ATR (Close): Volatility-normalized, close-based trigger
  5. M15 ATR (Close): Wider volatility stop, close-based trigger
  6. M5 Fractal H/L: Market structure swing high/low
- Key Metrics: Win Rate %, Expectancy, Avg R (All)
- Win = Trade reaches 1R profit before stop is hit

CALC-001: Win Rate by Model
- Shows win/loss breakdown by entry model (EPCH01-04)
- WIN DEFINITION: MFE occurs before MAE (mfe_potential_time < mae_potential_time)
- This measures if favorable price movement happens BEFORE adverse movement
- Aligned with Options Analysis for direct comparison between Shares and Options
- Uses mfe_mae_potential table data (entry to 15:30 ET analysis)

CALC-002: MFE/MAE Distribution Analysis (Percentage-Based)
- MFE (Max Favorable Excursion): Maximum favorable price movement from ENTRY to 15:30 ET
- MAE (Max Adverse Excursion): Maximum adverse price movement from ENTRY to 15:30 ET
- All values expressed as PERCENTAGE of entry price (not R-multiples)
- This analysis informs stop placement research - stops are NOT yet statistically validated

KEY INSIGHT:
The MFE/MAE analysis measures raw market behavior from entry to end-of-day.
It answers: "How much does price typically move in my favor vs against me?"
This data should be used to DETERMINE where stops should be placed, not to
evaluate existing stops.

MFE/MAE METRICS:
- Median MFE%: Typical max favorable movement (e.g., 0.70% means price typically
  moves 0.70% in your favor at some point between entry and 15:30)
- Median MAE%: Typical max adverse movement (e.g., 0.55% means price typically
  moves 0.55% against you at some point between entry and 15:30)
- MFE/MAE Ratio: Favorable vs adverse movement. Ratio > 1.0 means favorable
  movement exceeds adverse movement - a structural edge indicator
- MAE Percentiles: P25, P50, P75 help identify optimal stop placement levels
""",
        "analysis_request": """
ANALYSIS REQUEST:

Please analyze this trading system data and provide:

1. **STOP TYPE ANALYSIS (Priority)**
   - Which stop type shows the best expectancy?
   - Which stop type has the highest win rate?
   - Are there trade-offs between tighter stops (higher win rate, lower R) vs wider stops?
   - Which stop type should be used as the baseline for indicator analysis?
   - Do certain stop types work better for specific model types or directions?

2. **MFE/MAE PATTERN ANALYSIS**
   - Which model-direction combinations show the best MFE/MAE ratio?
   - Are there structural differences between models in how price moves?
   - Do certain models show consistently lower adverse excursion (MAE)?
   - Which combinations have favorable movement exceeding adverse movement?

3. **STOP PLACEMENT RESEARCH**
   - Based on MAE distribution, what stop levels would capture most trades?
   - At what MAE% percentile should stops be placed to balance protection vs noise?
   - Example: "If MAE P75 = 0.80%, a stop at 0.85% would only be hit by ~25% of trades"
   - Are there model-specific stop levels that make sense?
   - How do the 6 stop types compare to MAE percentile-based stops?

4. **DIRECTION ANALYSIS**
   - Is there a systematic difference between LONG and SHORT trades?
   - Do certain directions show better MFE/MAE characteristics?
   - Should certain model-direction combinations be avoided?

5. **STATISTICAL SIGNIFICANCE**
   - Which model-direction combinations have sufficient sample size?
   - Are the observed differences statistically meaningful?
   - What confidence can we have in these patterns?

6. **ACTIONABLE RECOMMENDATIONS**
   - Which stop type should be used going forward?
   - Which model-direction combinations should be prioritized?
   - What stop levels are suggested by the MAE distribution?
   - What target levels are suggested by the MFE distribution?
   - Priority ranking by: (1) statistical confidence, (2) edge magnitude, (3) sample size

7. **DATA QUALITY NOTES**
   - Win Rate uses MFE < MAE methodology (reliable, aligned with Options Analysis)
   - Win = MFE time < MAE time (favorable movement before adverse movement)
   - Analysis uses mfe_mae_potential table exclusively (entry to 15:30 ET)
   - Stop analysis uses estimated outcomes from MFE/MAE data
   - This provides clean, comparable metrics between Shares and Options analysis
""",
    },

    # -------------------------------------------------------------------------
    # Future tabs will be added here as the system expands
    # -------------------------------------------------------------------------
    # "continuation": { ... },
    # "rejection": { ... },
    # "indicators": { ... },
    # "health": { ... },
}


# =============================================================================
# AVAILABLE DATA SCHEMA - Reference for Claude
# =============================================================================

AVAILABLE_DATA_SCHEMA = """
AVAILABLE DATABASE TABLES AND COLUMNS:

TABLE: mfe_mae_potential (PRIMARY DATA SOURCE FOR ALL ANALYSIS)
- trade_id: Unique identifier
- date: Trade date
- ticker: Stock symbol
- direction: LONG or SHORT
- model: Entry model (EPCH1, EPCH2, EPCH3, EPCH4)
- entry_time: Trade entry time (ET)
- entry_price: Entry price
- mfe_potential_price: Price at maximum favorable excursion (entry to 15:30)
- mfe_potential_time: Time when MFE occurred (USED FOR WIN CALCULATION)
- mae_potential_price: Price at maximum adverse excursion (entry to 15:30)
- mae_potential_time: Time when MAE occurred (USED FOR WIN CALCULATION)
- bars_analyzed: Number of 1-minute bars analyzed

WIN CALCULATION (CALC-001):
- Win = mfe_potential_time < mae_potential_time (MFE occurs before MAE)
- This measures if favorable price movement happens BEFORE adverse movement
- Same methodology as Options Analysis for direct comparison

POINTS CALCULATION:
- Win Points: abs(mfe_potential_price - entry_price) for winning trades
- Loss Points: abs(mae_potential_price - entry_price) for losing trades
- Total Points: Sum of win points - Sum of loss points
- Avg Points: Total Points / Total Trades
- NOTE: R-values are no longer used - all calculations use points

CALCULATED METRICS (in Streamlit):
- mfe_pct: (mfe_price - entry) / entry * 100 for LONG, inverted for SHORT
- mae_pct: (entry - mae_price) / entry * 100 for LONG, inverted for SHORT
- mfe_mae_ratio: mfe_pct / mae_pct

TABLE: trades (ENTRY DATA ONLY - for reference)
- trade_id: Unique identifier
- ticker, date, direction, model: Trade metadata
- entry_price, entry_time: Entry execution
- stop_price: Stop level (NOT statistically validated)
- zone_type, zone_high, zone_low, zone_mid, zone_rank: Zone info

TABLE: optimal_trades (indicator snapshots at events)
- trade_id: Links to trades table
- event_type: ENTRY, MFE, MAE, or EXIT
- health_score, vwap, sma9, sma21, sma_spread, sma_momentum
- vol_roc, vol_delta, cvd_slope
- m5_structure, m15_structure, h1_structure, h4_structure
"""


# =============================================================================
# PROMPT ASSEMBLY HELPERS
# =============================================================================

def get_tab_prompt(tab_name: str) -> dict:
    """
    Get the prompt configuration for a specific tab.

    Args:
        tab_name: Name of the tab (e.g., "metrics_overview")

    Returns:
        Dict with title, background, and analysis_request
    """
    return TAB_PROMPTS.get(tab_name, {
        "title": "Analysis Request",
        "background": "No specific background configured for this tab.",
        "analysis_request": "Please analyze the data provided below and offer insights."
    })


def get_full_prompt_template(tab_name: str, include_schema: bool = True) -> str:
    """
    Get the full prompt template for a tab (without data).

    Args:
        tab_name: Name of the tab
        include_schema: Whether to include database schema reference

    Returns:
        Complete prompt template string
    """
    tab_config = get_tab_prompt(tab_name)

    template = f"""{SYSTEM_CONTEXT}

{'=' * 80}
  {tab_config['title'].upper()}
{'=' * 80}

{tab_config['background']}
"""

    if include_schema:
        template += f"""
{'=' * 80}
  AVAILABLE DATA REFERENCE
{'=' * 80}

{AVAILABLE_DATA_SCHEMA}
"""

    template += f"""
{'=' * 80}
  ANALYSIS REQUEST
{'=' * 80}
{tab_config['analysis_request']}
{'=' * 80}
  DATA FROM CURRENT VIEW
{'=' * 80}

{{data_section}}
"""

    return template


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

def format_mfe_mae_stats(stats: dict) -> str:
    """
    Format MFE/MAE statistics for Monte AI prompt.
    
    Args:
        stats: Dictionary from calculate_mfe_mae_summary()
    
    Returns:
        Formatted string for prompt
    """
    return f"""
MFE/MAE TRADE BEHAVIOR ANALYSIS (Entry to 15:30 ET):
------------------------------
  Summary Statistics (Percentage of Entry Price):
    Median MFE: {stats.get('median_mfe_pct', 0):.3f}% (typical max favorable move)
    Median MAE: {stats.get('median_mae_pct', 0):.3f}% (typical max adverse move)
    Mean MFE: {stats.get('mean_mfe_pct', 0):.3f}%
    Mean MAE: {stats.get('mean_mae_pct', 0):.3f}%
    MFE Range (Q25-Q75): {stats.get('mfe_pct_q25', 0):.3f}% - {stats.get('mfe_pct_q75', 0):.3f}%
    MAE Range (Q25-Q75): {stats.get('mae_pct_q25', 0):.3f}% - {stats.get('mae_pct_q75', 0):.3f}%

  Key Ratios:
    Median MFE/MAE Ratio: {stats.get('median_mfe_mae_ratio', 0):.2f} (>1.0 = favorable exceeds adverse)

  Distribution Analysis:
    % Trades with MFE > 0.5%: {stats.get('pct_mfe_above_0_5', 0):.1f}%
    % Trades with MFE > 1.0%: {stats.get('pct_mfe_above_1_0', 0):.1f}%
    % Trades with MAE < 0.5%: {stats.get('pct_mae_below_0_5', 0):.1f}%

  Trade Count:
    Total Trades Analyzed: {stats.get('total_trades', 0):,}
"""


def format_mfe_mae_by_model(model_data: list) -> str:
    """
    Format MFE/MAE by model table for Monte AI prompt.
    
    Args:
        model_data: List of dicts or DataFrame with model statistics
    
    Returns:
        Formatted string for prompt
    """
    if not model_data:
        return "MFE/MAE BY MODEL: No data available"
    
    # Handle DataFrame or list of dicts
    if hasattr(model_data, 'to_dict'):
        rows = model_data.to_dict('records')
    else:
        rows = model_data
    
    if not rows:
        return "MFE/MAE BY MODEL: No data available"
    
    lines = [
        "MFE/MAE BY MODEL AND DIRECTION:",
        "-" * 80,
        f"{'Model':<8} {'Dir':<6} {'Trades':>7} {'Med MFE%':>10} {'Med MAE%':>10} {'MAE P75%':>10} {'MFE/MAE':>8}",
        "-" * 80
    ]
    
    for row in rows:
        lines.append(
            f"{row.get('Model', 'N/A'):<8} "
            f"{row.get('Direction', 'N/A'):<6} "
            f"{row.get('Trades', 0):>7} "
            f"{row.get('Med MFE%', 0):>10.3f} "
            f"{row.get('Med MAE%', 0):>10.3f} "
            f"{row.get('MAE P75%', 0):>10.3f} "
            f"{row.get('MFE/MAE Ratio', 0):>8.2f}"
        )
    
    return "\n".join(lines)


def format_filters(filters: dict) -> str:
    """
    Format current filter settings for Monte AI prompt.

    Args:
        filters: Dictionary of current filter values

    Returns:
        Formatted string for prompt
    """
    return f"""
CURRENT FILTERS:
  Date Range: {filters.get('date_from', 'N/A')} to {filters.get('date_to', 'N/A')}
  Models: {', '.join(filters.get('models', [])) or 'All'}
  Direction: {', '.join(filters.get('directions', [])) or 'All'}
  Tickers: {', '.join(filters.get('tickers', [])) or 'All'}
"""


def format_stop_analysis(stop_analysis: dict) -> str:
    """
    Format stop type analysis results for Monte AI prompt.

    Args:
        stop_analysis: Dictionary from render_stop_analysis_section_simple()
            Contains: summary (DataFrame), results (Dict), best_stop (Dict), total_trades (int)

    Returns:
        Formatted string for prompt
    """
    if not stop_analysis:
        return "STOP TYPE ANALYSIS: Not available\n"

    summary_df = stop_analysis.get('summary')
    best_stop = stop_analysis.get('best_stop', {})
    total_trades = stop_analysis.get('total_trades', 0)

    lines = [
        "STOP TYPE ANALYSIS (Foundation Analysis):",
        "-" * 50,
        f"  Total Trades Analyzed: {total_trades:,}",
        f"  Best Stop Type: {best_stop.get('stop_type', 'N/A')}",
        f"  Best Expectancy: {best_stop.get('expectancy', 0):+.3f}R",
        "",
        "  Stop Type Comparison:",
        "  " + "-" * 46,
    ]

    if summary_df is not None and not summary_df.empty:
        # Format header
        lines.append(f"  {'Stop Type':<20} {'n':>6} {'Win%':>7} {'Exp':>8} {'Avg R':>8}")
        lines.append("  " + "-" * 46)

        for _, row in summary_df.iterrows():
            stop_type = row.get('Stop Type', 'N/A')
            n = row.get('n', 0)
            win_rate = row.get('Win Rate %', 0)
            expectancy = row.get('Expectancy', 0)
            avg_r = row.get('Avg R (All)', 0)

            lines.append(f"  {stop_type:<20} {n:>6} {win_rate:>6.1f}% {expectancy:>+7.3f} {avg_r:>+7.2f}")
    else:
        lines.append("  No stop analysis data available.")

    lines.append("")
    lines.append("  Stop Type Definitions:")
    lines.append("    Zone + 5% Buffer: Stop beyond zone boundary with 5% buffer")
    lines.append("    Prior M1 H/L: Tightest stop - prior M1 bar high/low")
    lines.append("    Prior M5 H/L: Short-term structure - prior M5 bar high/low")
    lines.append("    M5 ATR (Close): Volatility-based, triggers on M5 close")
    lines.append("    M15 ATR (Close): Wider volatility, triggers on M15 close")
    lines.append("    M5 Fractal H/L: Market structure swing high/low")
    lines.append("")
    lines.append("  Interpretation:")
    lines.append("    - Higher Win Rate % = stop rarely hit before reaching 1R")
    lines.append("    - Positive Expectancy = profitable stop type")
    lines.append("    - Avg R (All) = net R per trade after wins and losses")
    lines.append("")

    return "\n".join(lines)