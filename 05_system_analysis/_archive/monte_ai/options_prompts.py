"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Options Analysis Prompt Templates
XIII Trading LLC
================================================================================

Configurable prompt templates specifically for the Options Analysis tab.
Mirrors the structure of prompts.py but tailored for options trading analysis.

Structure:
- OPTIONS_CONTEXT: Background about options trading in Epoch
- OPTIONS_TAB_PROMPTS: Per-section prompt templates
- OPTIONS_DATA_SCHEMA: Reference for options-specific columns

================================================================================
"""

# =============================================================================
# OPTIONS SYSTEM CONTEXT
# =============================================================================

OPTIONS_CONTEXT = """You are Monte, an AI research assistant for the Epoch Trading System.

Your role is to help analyze OPTIONS trading performance and optimize options strategy.
You have expertise in:
- Options pricing and Greeks
- Leverage analysis and capital efficiency
- Options MFE/MAE behavior analysis
- Strike selection and contract analysis
- Comparing options to underlying performance

EPOCH OPTIONS TRADING OVERVIEW:
- Options are used as the trading vehicle (instead of shares)
- We always BUY options (never sell/write)
- Contract selection: First ITM or ATM based on underlying direction
- CALL options for LONG underlying direction
- PUT options for SHORT underlying direction
- All analysis uses entry-to-15:30 ET window

KEY METRICS FOR OPTIONS:
- MFE%: Maximum favorable movement as % of option entry price
- MAE%: Maximum adverse movement as % of option entry price
- Exit%: Final P/L at 15:30 ET as % of entry price
- Leverage: Options movement relative to underlying movement
  - MFE Leverage = Options MFE% / Underlying MFE%
  - MAE Leverage = Options MAE% / Underlying MAE%

IMPORTANT DIFFERENCES FROM UNDERLYING (SHARES):
- Options move in PERCENTAGES much larger than underlying
- A 0.5% underlying move might result in 10-20% options move
- Options have time decay (theta) working against us intraday
- Options have leverage - both favorable and adverse moves are amplified

COMPARISON TO UNDERLYING (SHARES) ANALYSIS:
- Options win rate uses exit_pct > 0 (option price higher at 15:30 than entry)
- Shares win rate uses MFE time < MAE time (favorable movement before adverse)
- Both methodologies analyze entry to 15:30 ET window
- Options trade count may be lower due to liquidity/data gaps
- Leverage metrics are OPTIONS-ONLY (not applicable to shares)
- For direct comparison, compare Options Exit% to Shares MFE/MAE behavior
"""

# =============================================================================
# OPTIONS DATA SCHEMA
# =============================================================================

OPTIONS_DATA_SCHEMA = """
OPTIONS DATABASE TABLE: op_mfe_mae_potential

Core Fields:
- trade_id: Links to trades table
- date: Trade date
- ticker: Underlying stock symbol
- direction: LONG or SHORT (underlying direction)
- model: Entry model (EPCH01-04)

Options Contract Info:
- options_ticker: Full options ticker (e.g., O:AAPL250117C00175000)
- strike: Strike price
- expiration: Expiration date
- contract_type: CALL or PUT

Options Price Movement:
- option_entry_price: Entry price of options contract
- mfe_points: Max favorable movement in points (dollars)
- mfe_pct: Max favorable movement as % of entry
- mfe_price: Price at MFE
- mfe_time: Time when MFE occurred
- mae_points: Max adverse movement in points (dollars)
- mae_pct: Max adverse movement as % of entry
- mae_price: Price at MAE
- mae_time: Time when MAE occurred
- exit_points: Exit movement in points (dollars)
- exit_pct: Exit P/L as % of entry
- exit_price: Price at 15:30 ET
- exit_time: Exit timestamp (15:30 ET)

Underlying Comparison:
- underlying_mfe_pct: Underlying MFE% from mfe_mae_potential table
- underlying_mae_pct: Underlying MAE% from mfe_mae_potential table
- underlying_exit_pct: Underlying exit% from mfe_mae_potential table

Meta:
- bars_analyzed: Number of 1-minute options bars analyzed
"""

# =============================================================================
# OPTIONS TAB PROMPTS
# =============================================================================

OPTIONS_TAB_PROMPTS = {
    # -------------------------------------------------------------------------
    # Main Options Analysis Tab
    # -------------------------------------------------------------------------
    "options_overview": {
        "title": "Options Analysis Overview",
        "background": """
ANALYSIS CONTEXT: Options Performance Analysis

This tab analyzes OPTIONS trading performance across all models and directions.
Data comes from the op_mfe_mae_potential table which tracks options price movement
from entry to 15:30 ET.

CALC-O01: Options Win Rate by Model
- Win = Exit% > 0 (option closed higher than entry at 15:30)
- Loss = Exit% <= 0 (option closed flat or lower at 15:30)
- Breakdown by model (EPCH01-04) and contract type (CALL/PUT)

CALC-O02: Options MFE/MAE Distribution
- MFE%: How high did the option price go from entry?
- MAE%: How low did the option price go from entry?
- Options MFE/MAE percentages are MUCH larger than underlying
- Typical options MFE: 20-50% (vs underlying 0.5-1.5%)
- Typical options MAE: 10-30% (vs underlying 0.3-0.8%)

CALC-O03: Options Timing Analysis
- When does MFE occur relative to MAE?
- P(MFE First): Probability favorable movement happens before adverse
- Time to MFE/MAE: How quickly do these events occur?

CALC-O04: Options vs Underlying Comparison
- MFE Leverage: Options MFE% / Underlying MFE%
- MAE Leverage: Options MAE% / Underlying MAE%
- Helps understand effective leverage being achieved
- Target: MFE leverage > MAE leverage (asymmetric leverage)
""",
        "analysis_request": """
ANALYSIS REQUEST:

Please analyze the options trading data and provide:

1. **OPTIONS WIN RATE ANALYSIS**
   - Which model-contract combinations show best win rates?
   - Is there a systematic difference between CALL and PUT performance?
   - Do certain models work better for options than underlying?
   - What is the overall options win rate vs underlying win rate?

2. **OPTIONS MFE/MAE ANALYSIS**
   - What are typical MFE percentages for options trades?
   - What are typical MAE percentages (intraday drawdowns)?
   - How does the MFE/MAE ratio compare across models?
   - Are there model-contract combinations with superior MFE/MAE?

3. **LEVERAGE ANALYSIS**
   - What is the effective leverage being achieved?
   - Is MFE leverage > MAE leverage? (desirable for asymmetric risk)
   - Are we capturing expected leverage from options?
   - Which model-contract combinations show best leverage efficiency?

4. **TIMING ANALYSIS**
   - What is P(MFE First) for options vs underlying?
   - How quickly does MFE occur in options trades?
   - Is there time decay impact visible in the MAE patterns?

5. **RECOMMENDATIONS**
   - Which model-contract combinations should be prioritized?
   - What position sizing implications does the leverage data suggest?
   - Are there contract types (CALL vs PUT) that perform better?
   - What stop strategies might work given options MAE distribution?

6. **COMPARISON TO SHARES (UNDERLYING) ANALYSIS**
   - How does options win rate compare to shares win rate for same models?
   - Note: Shares uses MFE < MAE for wins; Options uses Exit% > 0 for wins
   - Are models that perform well on shares also performing well on options?
   - What leverage is being achieved (Options MFE% / Underlying MFE%)?

7. **DATA QUALITY NOTES**
   - Note any models or contracts with insufficient sample size
   - Flag any unusual patterns that might indicate data issues
   - Consider which findings have statistical significance
   - Options trade count may be lower than shares due to liquidity gaps
""",
    },

    # -------------------------------------------------------------------------
    # Options MFE/MAE Detail Section
    # -------------------------------------------------------------------------
    "options_mfe_mae": {
        "title": "Options MFE/MAE Distribution Analysis",
        "background": """
FOCUSED ANALYSIS: Options MFE/MAE Distributions

This section provides detailed analysis of options price movement patterns.
Understanding MFE/MAE in options is critical because:
- Options have non-linear payoff structures
- Leverage amplifies both favorable and adverse movements
- Time decay affects options value throughout the day

KEY METRICS:
- Median MFE%: Typical maximum gain opportunity
- Median MAE%: Typical maximum drawdown experienced
- MFE/MAE Ratio: Edge indicator (>1.0 favorable)
- Distribution percentiles inform stop placement

IMPORTANT NOTE:
Options MFE/MAE percentages are NOT directly comparable to underlying.
A 0.5% move in SPY might result in 15% move in ATM options.
""",
        "analysis_request": """
Please analyze the OPTIONS MFE/MAE distributions and provide:

1. What is the typical MFE range for options trades?
2. What is the typical MAE (drawdown) range?
3. At what MAE% level would you suggest stop placement?
4. Are there model-specific patterns in MFE/MAE?
5. How does CALL vs PUT MFE/MAE compare?
""",
    },

    # -------------------------------------------------------------------------
    # Options vs Underlying Section
    # -------------------------------------------------------------------------
    "options_vs_underlying": {
        "title": "Options vs Underlying Leverage Analysis",
        "background": """
FOCUSED ANALYSIS: Effective Leverage

This section compares options movement to underlying stock movement.
Understanding effective leverage helps with:
- Position sizing decisions
- Capital efficiency analysis
- Risk management calibration

LEVERAGE CALCULATIONS:
- MFE Leverage = Options MFE% / Underlying MFE%
- MAE Leverage = Options MAE% / Underlying MAE%
- Exit Leverage = |Options Exit%| / |Underlying Exit%|

IDEAL SCENARIO:
- MFE Leverage > MAE Leverage (asymmetric leverage)
- This means options amplify gains more than losses
- Achievable through strike selection and timing
""",
        "analysis_request": """
Please analyze the leverage comparison data and provide:

1. What is the typical MFE leverage achieved?
2. What is the typical MAE leverage (how much drawdown is amplified)?
3. Is leverage asymmetric (MFE leverage > MAE leverage)?
4. Which model-contract combinations show best leverage efficiency?
5. What does this suggest for position sizing?
""",
    },
}


# =============================================================================
# PROMPT ASSEMBLY HELPERS
# =============================================================================

def get_options_tab_prompt(section_name: str) -> dict:
    """
    Get the prompt configuration for a specific options section.

    Args:
        section_name: Name of the section (e.g., "options_overview")

    Returns:
        Dict with title, background, and analysis_request
    """
    return OPTIONS_TAB_PROMPTS.get(section_name, {
        "title": "Options Analysis Request",
        "background": "No specific background configured for this section.",
        "analysis_request": "Please analyze the options data provided and offer insights."
    })


def get_options_full_prompt_template(section_name: str, include_schema: bool = True) -> str:
    """
    Get the full prompt template for an options section (without data).

    Args:
        section_name: Name of the section
        include_schema: Whether to include database schema reference

    Returns:
        Complete prompt template string
    """
    section_config = get_options_tab_prompt(section_name)

    template = f"""{OPTIONS_CONTEXT}

{'=' * 80}
  {section_config['title'].upper()}
{'=' * 80}

{section_config['background']}
"""

    if include_schema:
        template += f"""
{'=' * 80}
  OPTIONS DATA REFERENCE
{'=' * 80}

{OPTIONS_DATA_SCHEMA}
"""

    template += f"""
{'=' * 80}
  ANALYSIS REQUEST
{'=' * 80}
{section_config['analysis_request']}
{'=' * 80}
  DATA FROM CURRENT VIEW
{'=' * 80}

{{data_section}}
"""

    return template


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

def format_options_mfe_mae_stats(stats: dict) -> str:
    """
    Format OPTIONS MFE/MAE statistics for Monte AI prompt.

    Args:
        stats: Dictionary from calculate_options_mfe_mae_summary()

    Returns:
        Formatted string for prompt
    """
    return f"""
OPTIONS MFE/MAE ANALYSIS (Entry to 15:30 ET):
---------------------------------------------
  Summary Statistics (Percentage of Options Entry Price):
    Median MFE: {stats.get('median_mfe_pct', 0):.1f}% (typical max favorable move)
    Median MAE: {stats.get('median_mae_pct', 0):.1f}% (typical max adverse move)
    Mean MFE: {stats.get('mean_mfe_pct', 0):.1f}%
    Mean MAE: {stats.get('mean_mae_pct', 0):.1f}%
    MFE Range (Q25-Q75): {stats.get('mfe_pct_q25', 0):.1f}% - {stats.get('mfe_pct_q75', 0):.1f}%
    MAE Range (Q25-Q75): {stats.get('mae_pct_q25', 0):.1f}% - {stats.get('mae_pct_q75', 0):.1f}%

  Key Ratios:
    Median MFE/MAE Ratio: {stats.get('median_mfe_mae_ratio', 0):.2f} (>1.0 = favorable exceeds adverse)
    Median Exit: {stats.get('median_exit_pct', 0):.1f}%

  Distribution Analysis:
    % Trades with MFE > 25%: {stats.get('pct_mfe_above_25', 0):.1f}%
    % Trades with MFE > 50%: {stats.get('pct_mfe_above_50', 0):.1f}%
    % Trades with MAE < 25%: {stats.get('pct_mae_below_25', 0):.1f}%

  Trade Count:
    Total Options Trades Analyzed: {stats.get('total_trades', 0):,}
"""


def format_options_leverage_stats(stats: dict) -> str:
    """
    Format OPTIONS leverage comparison statistics.

    Args:
        stats: Dictionary from calculate_leverage_comparison()

    Returns:
        Formatted string for prompt
    """
    return f"""
OPTIONS VS UNDERLYING LEVERAGE:
-------------------------------
  Leverage Ratios:
    MFE Leverage: {stats.get('median_mfe_leverage', 0):.1f}x (options MFE% / underlying MFE%)
    MAE Leverage: {stats.get('median_mae_leverage', 0):.1f}x (options MAE% / underlying MAE%)
    Exit Leverage: {stats.get('median_exit_leverage', 0):.1f}x (options exit% / underlying exit%)

  Asymmetry Analysis:
    MFE Lev > MAE Lev: {'YES' if stats.get('median_mfe_leverage', 0) > stats.get('median_mae_leverage', 0) else 'NO'}
    Ratio: {stats.get('median_mfe_leverage', 0) / stats.get('median_mae_leverage', 1):.2f}x

  Movement Comparison:
    Options MFE: {stats.get('median_options_mfe', 0):.1f}%
    Underlying MFE: {stats.get('median_underlying_mfe', 0):.2f}%
    Options MAE: {stats.get('median_options_mae', 0):.1f}%
    Underlying MAE: {stats.get('median_underlying_mae', 0):.2f}%

  Sample Size:
    Trades with Comparison Data: {stats.get('trades_with_comparison', 0):,}
    Total Options Trades: {stats.get('total_trades', 0):,}
"""


def format_options_sequence_stats(stats: dict) -> str:
    """
    Format OPTIONS sequence/timing statistics.

    Args:
        stats: Dictionary from calculate_options_sequence_summary()

    Returns:
        Formatted string for prompt
    """
    return f"""
OPTIONS TIMING ANALYSIS (MFE/MAE Sequence):
------------------------------------------
  Probability Analysis:
    P(MFE First): {stats.get('mfe_first_rate', 0):.1%} (probability favorable move occurs before adverse)
    MFE First Count: {stats.get('mfe_first_count', 0):,}
    MAE First Count: {stats.get('mae_first_count', 0):,}

  Time to Events:
    Median Time to MFE: {stats.get('median_time_to_mfe', 0):.0f} minutes
    Median Time to MAE: {stats.get('median_time_to_mae', 0):.0f} minutes
    Mean Time to MFE: {stats.get('mean_time_to_mfe', 0):.0f} minutes
    Mean Time to MAE: {stats.get('mean_time_to_mae', 0):.0f} minutes

  Distribution:
    % MFE under 30 min: {stats.get('pct_mfe_under_30min', 0):.1f}%
    % MFE under 60 min: {stats.get('pct_mfe_under_60min', 0):.1f}%
    % MAE under 30 min: {stats.get('pct_mae_under_30min', 0):.1f}%

  Sample Size:
    Total Trades Analyzed: {stats.get('total_trades', 0):,}
"""


def format_options_win_rate_by_model(model_data) -> str:
    """
    Format OPTIONS win rate by model table.

    Args:
        model_data: List of dicts or DataFrame with model statistics

    Returns:
        Formatted string for prompt
    """
    # Handle None
    if model_data is None:
        return "OPTIONS WIN RATE BY MODEL: No data available"

    # Handle DataFrame
    if hasattr(model_data, 'to_dict'):
        if len(model_data) == 0:
            return "OPTIONS WIN RATE BY MODEL: No data available"
        rows = model_data.to_dict('records')
    else:
        rows = model_data

    if not rows:
        return "OPTIONS WIN RATE BY MODEL: No data available"

    lines = [
        "OPTIONS WIN RATE BY MODEL:",
        "-" * 60,
        f"{'Model':<8} {'Wins':>6} {'Losses':>8} {'Win%':>8} {'Avg Exit%':>12}",
        "-" * 60
    ]

    for row in rows:
        lines.append(
            f"{row.get('Model', 'N/A'):<8} "
            f"{row.get('Wins', 0):>6} "
            f"{row.get('Losses', 0):>8} "
            f"{row.get('Win%', 0):>8.1f} "
            f"{row.get('Avg Exit%', 0):>12.1f}"
        )

    return "\n".join(lines)


def format_options_filters(filters: dict) -> str:
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
  Models: {', '.join(filters.get('models') or []) or 'All'}
  Direction: {', '.join(filters.get('directions') or []) or 'All'}
  Contract Types: {', '.join(filters.get('contract_types') or []) or 'All'}
"""


def format_options_stop_analysis(stop_analysis: dict) -> str:
    """
    Format OPTIONS stop analysis statistics for Monte AI prompt.

    Args:
        stop_analysis: Dictionary from render_op_stop_analysis_section()
            Contains: best_stop, summary (DataFrame), total_trades, results

    Returns:
        Formatted string for prompt
    """
    import pandas as pd

    if not stop_analysis:
        return "OPTIONS STOP ANALYSIS: No data available"

    best_stop = stop_analysis.get('best_stop', {})
    summary = stop_analysis.get('summary', pd.DataFrame())
    total_trades = stop_analysis.get('total_trades', 0)

    lines = [
        "OPTIONS STOP TYPE ANALYSIS:",
        "-" * 60,
        f"  Best Stop Type: {best_stop.get('stop_type', 'N/A')}",
        f"  Best Expectancy: {best_stop.get('expectancy', 0):+.3f}R",
        f"  Best Win Rate: {best_stop.get('win_rate', 0):.1f}%",
        f"  Trades Analyzed: {total_trades:,}",
        "",
        "  Stop Type Comparison:",
        f"  {'Stop Type':<12} {'Stop%':>6} {'n':>6} {'Win%':>8} {'Stop Hit%':>10} {'Expectancy':>12}",
        "  " + "-" * 56
    ]

    if isinstance(summary, pd.DataFrame) and not summary.empty:
        for _, row in summary.iterrows():
            stop_type = row.get('Stop Type', 'N/A')
            stop_pct = row.get('Stop %', 0)
            n = row.get('n', 0)
            win_rate = row.get('Win Rate %', 0)
            stop_hit = row.get('Stop Hit %', 0)
            expectancy = row.get('Expectancy', 0)
            lines.append(
                f"  {stop_type:<12} {stop_pct:>6.0f}% {n:>6} {win_rate:>8.1f}% {stop_hit:>10.1f}% {expectancy:>+12.3f}R"
            )

    lines.append("")
    lines.append("  Key Insights:")
    lines.append("    - Tighter stops (10-15%) have higher stop-out rates but limit losses")
    lines.append("    - Wider stops (30-50%) reduce stop-outs but increase average loss")
    lines.append("    - Target = 1R (same % as stop) for all calculations")

    return "\n".join(lines)


def format_options_simulated_outcomes(simulated_stats: dict) -> str:
    """
    Format OPTIONS simulated outcomes for Monte AI prompt.

    Args:
        simulated_stats: Dictionary from render_simulated_outcomes_section()
            Contains: overall_optimal, model_optimal (DataFrame), total_trades

    Returns:
        Formatted string for prompt
    """
    import pandas as pd

    if not simulated_stats:
        return "OPTIONS SIMULATED OUTCOMES: No data available"

    optimal = simulated_stats.get('overall_optimal', {})
    model_optimal = simulated_stats.get('model_optimal', pd.DataFrame())
    total_trades = simulated_stats.get('total_trades', 0)

    lines = [
        "OPTIONS SIMULATED OUTCOMES:",
        "-" * 60,
        "  Grid Search: Stop (10-50%) x Target (25-200%)",
        "",
        "  Overall Optimal Parameters:",
        f"    Optimal Stop: {optimal.get('stop_pct', 25):.0f}%",
        f"    Optimal Target: {optimal.get('target_pct', 50):.0f}%",
        f"    R:R Ratio: {optimal.get('r_ratio', 2.0):.1f}:1",
        f"    Win Rate: {optimal.get('win_rate', 0):.1f}%",
        f"    Expectancy: {optimal.get('expectancy', 0):+.3f}R",
        f"    Trades: {optimal.get('n', total_trades):,}",
        ""
    ]

    if isinstance(model_optimal, pd.DataFrame) and not model_optimal.empty:
        lines.append("  Optimal Parameters by Model:")
        lines.append(f"  {'Model':<8} {'Stop':>8} {'Target':>8} {'R:R':>8} {'Win%':>8} {'Expectancy':>12}")
        lines.append("  " + "-" * 52)

        for _, row in model_optimal.iterrows():
            model = row.get('Model', 'N/A')
            stop = row.get('Optimal Stop', 'N/A')
            target = row.get('Optimal Target', 'N/A')
            rr = row.get('R:R', 'N/A')
            win_rate = row.get('Win Rate', 0)
            expectancy = row.get('Expectancy', 0)

            # Handle formatting for numeric vs string values
            if isinstance(win_rate, str):
                win_rate_str = win_rate
            else:
                win_rate_str = f"{win_rate:.1f}%"

            if isinstance(expectancy, str):
                exp_str = expectancy
            else:
                exp_str = f"{expectancy:+.3f}R"

            lines.append(
                f"  {model:<8} {stop:>8} {target:>8} {rr:>8} {win_rate_str:>8} {exp_str:>12}"
            )

    lines.append("")
    lines.append("  Note: Grid search finds optimal stop/target to maximize expectancy")

    return "\n".join(lines)


def format_options_win_rate_with_stop(model_data, stop_name: str = "25%") -> str:
    """
    Format OPTIONS win rate by model using stop-based outcomes.

    Args:
        model_data: DataFrame with model statistics from stop-based calculation
        stop_name: Display name of stop type used

    Returns:
        Formatted string for prompt
    """
    if model_data is None:
        return f"OPTIONS WIN RATE BY MODEL (Using {stop_name} Stop): No data available"

    if hasattr(model_data, 'to_dict'):
        if len(model_data) == 0:
            return f"OPTIONS WIN RATE BY MODEL (Using {stop_name} Stop): No data available"
        rows = model_data.to_dict('records')
    else:
        rows = model_data

    if not rows:
        return f"OPTIONS WIN RATE BY MODEL (Using {stop_name} Stop): No data available"

    lines = [
        f"OPTIONS WIN RATE BY MODEL (Using {stop_name} Stop):",
        f"  Win = 1R target reached before stop hit",
        "-" * 60,
        f"{'Model':<8} {'Wins':>6} {'Losses':>8} {'Win%':>8} {'Avg R':>10} {'Total':>8}",
        "-" * 60
    ]

    total_wins = 0
    total_losses = 0
    total_trades = 0

    for row in rows:
        wins = int(row.get('Wins', 0))
        losses = int(row.get('Losses', 0))
        total = int(row.get('Total', wins + losses))
        win_pct = row.get('Win%', 0)
        avg_r = row.get('Avg R', 0)

        total_wins += wins
        total_losses += losses
        total_trades += total

        lines.append(
            f"{row.get('Model', 'N/A'):<8} "
            f"{wins:>6} "
            f"{losses:>8} "
            f"{win_pct:>8.1f}% "
            f"{avg_r:>+10.2f}R "
            f"{total:>8}"
        )

    # Add totals row
    overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
    lines.append("-" * 60)
    lines.append(
        f"{'TOTAL':<8} "
        f"{total_wins:>6} "
        f"{total_losses:>8} "
        f"{overall_wr:>8.1f}% "
        f"{'':>10} "
        f"{total_trades:>8}"
    )

    return "\n".join(lines)
