"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Data Collector
XIII Trading LLC
================================================================================

Collects and formats data from each tab for inclusion in prompts.
Each tab has a dedicated collector function that gathers relevant data
and formats it for Claude analysis.

Updated: 2026-01-02
- Changed to percentage-based MFE/MAE formatting
- Removed unreliable winner/loser metrics
- Added Direction column to model breakdown

================================================================================
"""

from typing import Dict, Any, List, Optional
from datetime import date
import pandas as pd


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

def _format_table(headers: List[str], rows: List[List[Any]], alignment: str = "left") -> str:
    """
    Format data as a simple ASCII table.

    Args:
        headers: List of column headers
        rows: List of rows (each row is a list of values)
        alignment: "left", "right", or "center"

    Returns:
        Formatted table string
    """
    if not rows:
        return "No data available."

    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(val)))

    # Format header
    header_line = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)

    # Format rows
    formatted_rows = []
    for row in rows:
        formatted_row = " | ".join(
            str(val).ljust(col_widths[i]) if i < len(col_widths) else str(val)
            for i, val in enumerate(row)
        )
        formatted_rows.append(formatted_row)

    return f"{header_line}\n{separator}\n" + "\n".join(formatted_rows)


def _format_key_value(data: Dict[str, Any], title: str = "") -> str:
    """
    Format a dictionary as key-value pairs.

    Args:
        data: Dictionary of key-value pairs
        title: Optional title for the section

    Returns:
        Formatted string
    """
    lines = []
    if title:
        lines.append(f"{title}:")
        lines.append("-" * len(title))

    for key, value in data.items():
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.2f}")
        else:
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def _format_filters(filters: Dict[str, Any]) -> str:
    """Format current filter state."""
    lines = ["CURRENT FILTERS:"]

    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    if date_from or date_to:
        from_str = date_from.strftime("%Y-%m-%d") if date_from else "Start"
        to_str = date_to.strftime("%Y-%m-%d") if date_to else "End"
        lines.append(f"  Date Range: {from_str} to {to_str}")

    models = filters.get("models")
    lines.append(f"  Models: {', '.join(models) if models else 'All'}")

    directions = filters.get("directions")
    lines.append(f"  Direction: {', '.join(directions) if directions else 'All'}")

    tickers = filters.get("tickers")
    lines.append(f"  Tickers: {', '.join(tickers) if tickers else 'All'}")

    outcome = filters.get("outcome", "All")
    lines.append(f"  Outcome Filter: {outcome}")

    return "\n".join(lines)


def _format_stop_analysis(stop_analysis: Dict[str, Any], use_default: bool = True) -> str:
    """
    Format stop type analysis results for prompt.

    IMPORTANT: Monte AI prompt always uses the DEFAULT stop type (Zone + 5% Buffer)
    for consistency and reproducibility, regardless of UI selection.

    Args:
        stop_analysis: Dict from render_stop_analysis_section_simple()
            Contains: summary (DataFrame), results (Dict), best_stop (Dict), total_trades (int)
        use_default: If True (default), always format using zone_buffer data.
            This ensures consistent analysis across sessions.

    Returns:
        Formatted string for prompt
    """
    if not stop_analysis:
        return "STOP TYPE ANALYSIS: Not available"

    summary_df = stop_analysis.get('summary')
    results = stop_analysis.get('results', {})
    best_stop = stop_analysis.get('best_stop', {})
    total_trades = stop_analysis.get('total_trades', 0)

    # Default stop type configuration
    DEFAULT_STOP_TYPE = 'zone_buffer'
    DEFAULT_STOP_NAME = 'Zone + 5% Buffer'

    # Calculate metrics for default stop type
    default_outcomes = results.get(DEFAULT_STOP_TYPE, [])

    if default_outcomes:
        wins = len([o for o in default_outcomes if o.get('outcome') == 'WIN'])
        losses = len([o for o in default_outcomes if o.get('outcome') == 'LOSS'])
        total = len(default_outcomes)
        win_rate = (wins / total * 100) if total > 0 else 0
        loss_rate = (losses / total) if total > 0 else 0

        # Calculate avg R on winners for expectancy formula
        winner_r_values = [o.get('r_achieved', 1.0) for o in default_outcomes if o.get('outcome') == 'WIN']
        avg_r_winners = sum(winner_r_values) / len(winner_r_values) if winner_r_values else 0

        # Expectancy formula: E = (win% * avg_win_r) - (loss% * 1R)
        # This matches results_aggregator.py
        expectancy = ((win_rate / 100) * avg_r_winners) - (loss_rate * 1.0)
    else:
        wins, losses, total, win_rate, expectancy = 0, 0, 0, 0, 0

    lines = [
        "STOP TYPE ANALYSIS (Foundation Analysis):",
        "-" * 100,
        f"  Analysis Stop Type: {DEFAULT_STOP_NAME} (Default)",
        f"  NOTE: Prompt always uses default stop type for consistency",
        "",
        f"  Total Trades Analyzed: {total_trades:,}",
        "",
        f"  Default Stop Type Performance ({DEFAULT_STOP_NAME}):",
        f"    Wins: {wins:,}",
        f"    Losses: {losses:,}",
        f"    Win Rate: {win_rate:.1f}%",
        f"    Expectancy: {expectancy:+.3f}R",
        "",
        "  Stop Type Comparison (all 6 types - FULL DATA):",
        "  " + "-" * 96,
    ]

    if summary_df is not None and not summary_df.empty:
        # Format header with ALL columns
        lines.append(f"  {'Stop Type':<20} {'n':>6} {'Avg Stop%':>10} {'Stop Hit%':>10} {'Win Rate%':>10} {'Avg R(Win)':>11} {'Avg R(All)':>11} {'Net R(MFE)':>12} {'Expectancy':>11}")
        lines.append("  " + "-" * 96)

        for _, row in summary_df.iterrows():
            stop_type = row.get('Stop Type', 'N/A')
            n = row.get('n', 0)
            avg_stop = row.get('Avg Stop %', 0)
            stop_hit = row.get('Stop Hit %', 0)
            wr = row.get('Win Rate %', 0)
            avg_r_win = row.get('Avg R (Win)', 0)
            avg_r_all = row.get('Avg R (All)', 0)
            net_r_mfe = row.get('Net R (MFE)', 0)
            exp = row.get('Expectancy', 0)

            # Mark default with asterisk
            stop_type_key = row.get('stop_type_key', '')
            marker = " *" if stop_type_key == DEFAULT_STOP_TYPE else ""

            lines.append(f"  {stop_type:<20} {n:>6} {avg_stop:>9.2f}% {stop_hit:>9.1f}% {wr:>9.1f}% {avg_r_win:>+10.2f}R {avg_r_all:>+10.2f}R {net_r_mfe:>+11.2f}R {exp:>+10.3f}{marker}")

        lines.append("")
        lines.append("  * = Default stop type used for downstream analysis")
    else:
        lines.append("  No stop analysis data available.")

    lines.append("")
    lines.append("  COLUMN DEFINITIONS:")
    lines.append("    n: Number of trades analyzed for this stop type")
    lines.append("    Avg Stop %: Average stop distance as percentage of entry price")
    lines.append("    Stop Hit %: Percentage of trades where stop was triggered (loss rate)")
    lines.append("    Win Rate %: Percentage of trades reaching 1R profit before stop hit")
    lines.append("    Avg R (Win): Average R-multiple achieved on winning trades only")
    lines.append("    Avg R (All): Average R-multiple across ALL trades (wins + losses)")
    lines.append("    Net R (MFE): Total R summed across all trades (theoretical max using MFE as exit)")
    lines.append("    Expectancy: Expected R per trade = (Win% * Avg R Win) - (Loss% * 1R)")
    lines.append("")
    lines.append("  CALCULATION METHODOLOGY:")
    lines.append("  -------------------------")
    lines.append("  1. Win Condition: Trade reaches 1R profit before stop is hit")
    lines.append("     - 1R = stop_distance (entry to stop price)")
    lines.append("     - Win if MFE >= 1R before stop triggered")
    lines.append("")
    lines.append("  2. r_achieved Calculation:")
    lines.append("     - If stop hit: r_achieved = -1.0R (full loss)")
    lines.append("     - If not hit: r_achieved = mfe_distance / stop_distance")
    lines.append("     - This measures how far price moved favorably in R-multiples")
    lines.append("")
    lines.append("  3. Avg R (Win) = mean(r_achieved) for trades where outcome = WIN")
    lines.append("")
    lines.append("  4. Avg R (All) = mean(r_achieved) for ALL trades")
    lines.append("")
    lines.append("  5. Net R (MFE) Calculation:")
    lines.append("     - Sum of all r_achieved values")
    lines.append("     - For NULL r_achieved values, impute based on win/loss ratio:")
    lines.append("       * null_wins = null_count * (win_rate / 100)")
    lines.append("       * null_losses = null_count * (stop_hit_pct / 100)")
    lines.append("       * imputed_r = (null_wins * avg_r_winners) + (null_losses * -1.0)")
    lines.append("     - Net R = non_null_sum + imputed_r")
    lines.append("     - NOTE: Uses MFE as exit point (theoretical maximum, not realistic)")
    lines.append("")
    lines.append("  6. Expectancy = (win_rate * avg_r_winners) - (loss_rate * 1.0)")
    lines.append("     - Represents expected R-value per trade")
    lines.append("")
    lines.append("  STOP TYPE DEFINITIONS:")
    lines.append("    Zone + 5% Buffer: Stop beyond zone boundary with 5% buffer (DEFAULT)")
    lines.append("    Prior M1 H/L: Tightest stop - prior M1 bar high/low")
    lines.append("    Prior M5 H/L: Short-term structure - prior M5 bar high/low")
    lines.append("    M5 ATR (Close): Volatility-based, triggers on M5 close")
    lines.append("    M15 ATR (Close): Wider volatility, triggers on M15 close")
    lines.append("    M5 Fractal H/L: Market structure swing high/low")
    lines.append("")
    lines.append("  INTERPRETATION GUIDANCE:")
    lines.append("    - Higher Win Rate % = stop rarely hit before reaching 1R")
    lines.append("    - Tighter stops (lower Avg Stop %) = higher Stop Hit % but larger R on wins")
    lines.append("    - Positive Expectancy = profitable stop type over many trades")
    lines.append("    - Net R (MFE) shows theoretical maximum if exiting at MFE (not realistic)")
    lines.append("    - Compare Avg R (All) across stop types for realistic per-trade expectation")

    return "\n".join(lines)


def _normalize_model(model: str) -> str:
    """Normalize model names (EPCH1 -> EPCH01, etc.)"""
    if not model:
        return 'UNKNOWN'
    model = str(model).upper().strip()
    # Handle various formats: EPCH1, EPCH01, epch1, etc.
    if model in ['EPCH1', 'EPCH01']:
        return 'EPCH01'
    elif model in ['EPCH2', 'EPCH02']:
        return 'EPCH02'
    elif model in ['EPCH3', 'EPCH03']:
        return 'EPCH03'
    elif model in ['EPCH4', 'EPCH04']:
        return 'EPCH04'
    return model


def _format_model_stats_with_stop(stop_analysis: Dict[str, Any]) -> str:
    """
    Format CALC-001 model statistics for Monte AI prompt.
    Always uses default stop type (zone_buffer) for consistency.

    Args:
        stop_analysis: Dict from render_stop_analysis_section_simple()
            Contains: results (Dict by stop type)

    Returns:
        Formatted string for prompt
    """
    if not stop_analysis:
        return "WIN RATE BY MODEL (Stop-Based): Not available (run CALC-009 first)\n"

    results = stop_analysis.get('results', {})
    default_outcomes = results.get('zone_buffer', [])

    if not default_outcomes:
        return "WIN RATE BY MODEL (Stop-Based): No data for default stop type\n"

    # Calculate by model
    import pandas as pd
    df = pd.DataFrame(default_outcomes)

    # Normalize model names
    if 'model' in df.columns:
        df['model'] = df['model'].apply(_normalize_model)

    lines = [
        "WIN RATE BY MODEL (Using: Zone + 5% Buffer):",
        "-" * 60,
        f"{'Model':<8} {'Wins':>6} {'Losses':>7} {'Total':>6} {'Win%':>7} {'Expectancy':>11}",
        "-" * 60,
    ]

    MODELS = ['EPCH01', 'EPCH02', 'EPCH03', 'EPCH04']

    for model in MODELS:
        model_df = df[df['model'] == model] if 'model' in df.columns else pd.DataFrame()

        if model_df.empty:
            lines.append(f"{model:<8} {'0':>6} {'0':>7} {'0':>6} {'N/A':>7} {'N/A':>11}")
            continue

        total = len(model_df)
        wins = len(model_df[model_df['outcome'] == 'WIN'])
        losses = len(model_df[model_df['outcome'] == 'LOSS'])
        win_rate = (wins / total * 100) if total > 0 else 0
        loss_rate = losses / total if total > 0 else 0

        # Calculate avg R on winners for expectancy formula
        winners_df = model_df[model_df['outcome'] == 'WIN']
        avg_r_winners = winners_df['r_achieved'].mean() if len(winners_df) > 0 else 0
        if pd.isna(avg_r_winners):
            avg_r_winners = 1.0  # Default to 1R for wins if no r_achieved data

        # Expectancy formula: E = (win% * avg_win_r) - (loss% * 1R)
        # This matches results_aggregator.py
        expectancy = ((win_rate / 100) * avg_r_winners) - (loss_rate * 1.0)

        lines.append(
            f"{model:<8} {wins:>6} {losses:>7} {total:>6} {win_rate:>6.1f}% {expectancy:>+10.3f}"
        )

    lines.append("-" * 60)
    lines.append("")
    lines.append("Note: Win = 1R reached before stop | Loss = Stop hit before 1R")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# TAB-SPECIFIC DATA COLLECTORS
# =============================================================================

def collect_metrics_overview_data(
    model_stats: pd.DataFrame,
    overall_stats: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    available_calculations: Optional[List[str]] = None,
    mfe_mae_stats: Optional[Dict[str, Any]] = None,
    mfe_mae_by_model: Optional[pd.DataFrame] = None,
    sequence_stats: Optional[Dict[str, Any]] = None,
    simulated_stats: Optional[Dict[str, Any]] = None,
    stop_analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Collect and format data for the Metrics Overview tab.

    Args:
        model_stats: DataFrame from calculate_win_rate_by_model
        overall_stats: Dict with total trades, wins, losses, win_rate, etc.
        filters: Current filter state
        available_calculations: List of calculations currently implemented
        mfe_mae_stats: Dict with MFE/MAE summary statistics (percentage-based)
        mfe_mae_by_model: DataFrame with MFE/MAE stats by model and direction
        sequence_stats: Dict with MFE/MAE sequence statistics (CALC-003)
        simulated_stats: Dict with simulated outcome statistics (CALC-004)
        stop_analysis: Dict with stop type analysis results (Stop Analysis)

    Returns:
        Formatted data string for prompt insertion
    """
    sections = []

    # Filters section
    if filters:
        sections.append(_format_filters(filters))
        sections.append("")

    # Stop Type Analysis (Foundation - always available)
    sections.append(_format_stop_analysis(stop_analysis, use_default=True))
    sections.append("")

    # Add stop-based model statistics (using default stop type)
    sections.append(_format_model_stats_with_stop(stop_analysis))
    sections.append("")

    # MFE/MAE Trade Behavior Analysis (CALC-002) - Raw Market Behavior
    # This shows what's POSSIBLE in the market, independent of stop placement
    if mfe_mae_stats:
        sections.append("MFE/MAE RAW MARKET BEHAVIOR (Entry to 15:30 ET):")
        sections.append("  Note: Shows price movement potential, not trading outcomes")
        sections.append("-" * 30)
        sections.append("  Summary Statistics (Percentage of Entry Price):")
        sections.append(f"    Median MFE: {mfe_mae_stats.get('median_mfe_pct', 0):.3f}% (typical max favorable move)")
        sections.append(f"    Median MAE: {mfe_mae_stats.get('median_mae_pct', 0):.3f}% (typical max adverse move)")
        sections.append(f"    Mean MFE: {mfe_mae_stats.get('mean_mfe_pct', 0):.3f}%")
        sections.append(f"    Mean MAE: {mfe_mae_stats.get('mean_mae_pct', 0):.3f}%")
        sections.append(f"    MFE Range (Q25-Q75): {mfe_mae_stats.get('mfe_pct_q25', 0):.3f}% - {mfe_mae_stats.get('mfe_pct_q75', 0):.3f}%")
        sections.append(f"    MAE Range (Q25-Q75): {mfe_mae_stats.get('mae_pct_q25', 0):.3f}% - {mfe_mae_stats.get('mae_pct_q75', 0):.3f}%")
        sections.append("")
        sections.append("  Key Ratios:")
        sections.append(f"    Median MFE/MAE Ratio: {mfe_mae_stats.get('median_mfe_mae_ratio', 0):.2f} (>1.0 = favorable exceeds adverse)")
        sections.append("")
        sections.append("  Distribution Analysis:")
        sections.append(f"    % Trades with MFE > 0.5%: {mfe_mae_stats.get('pct_mfe_above_0_5', 0):.1f}%")
        sections.append(f"    % Trades with MFE > 1.0%: {mfe_mae_stats.get('pct_mfe_above_1_0', 0):.1f}%")
        sections.append(f"    % Trades with MAE < 0.5%: {mfe_mae_stats.get('pct_mae_below_0_5', 0):.1f}%")
        sections.append("")
        sections.append("  Trade Count:")
        sections.append(f"    Total Trades Analyzed: {mfe_mae_stats.get('total_trades', 0):,}")
        sections.append("")

    # MFE/MAE by Model AND Direction
    if mfe_mae_by_model is not None and not mfe_mae_by_model.empty:
        sections.append("MFE/MAE BY MODEL AND DIRECTION:")
        sections.append("-" * 30)
        
        # Check if Direction column exists
        has_direction = 'Direction' in mfe_mae_by_model.columns
        
        if has_direction:
            headers = ["Model", "Direction", "Trades", "Med MFE%", "Med MAE%", "MAE P75%", "MFE/MAE"]
            rows = []
            for _, row in mfe_mae_by_model.iterrows():
                rows.append([
                    row.get("Model", "?"),
                    row.get("Direction", "?"),
                    row.get("Trades", 0),
                    f"{row.get('Med MFE%', 0):.3f}%",
                    f"{row.get('Med MAE%', 0):.3f}%",
                    f"{row.get('MAE P75%', 0):.3f}%",
                    f"{row.get('MFE/MAE Ratio', 0):.2f}"
                ])
        else:
            # Fallback for old format without Direction
            headers = ["Model", "Trades", "Med MFE%", "Med MAE%", "MFE/MAE"]
            rows = []
            for _, row in mfe_mae_by_model.iterrows():
                # Handle both old and new column names
                med_mfe = row.get('Med MFE%', row.get('Med MFE', 0))
                med_mae = row.get('Med MAE%', row.get('Med MAE', 0))
                mfe_mae_ratio = row.get('MFE/MAE Ratio', row.get('MFE/MAE', 0))
                
                rows.append([
                    row.get("Model", "?"),
                    row.get("Trades", 0),
                    f"{med_mfe:.3f}%",
                    f"{med_mae:.3f}%",
                    f"{mfe_mae_ratio:.2f}"
                ])
        
        sections.append(_format_table(headers, rows))
        sections.append("")

    # MFE/MAE Sequence Analysis (CALC-003) - Monte Carlo Baseline
    if sequence_stats and sequence_stats.get('total_trades', 0) > 0:
        sections.append("MFE/MAE SEQUENCE ANALYSIS (Monte Carlo Baseline):")
        sections.append("-" * 30)
        sections.append("  Core Question: When MFE conditions are met, does favorable movement occur before adverse?")
        sections.append("")
        sections.append("  Summary Statistics:")
        sections.append(f"    P(MFE First): {sequence_stats.get('mfe_first_rate', 0):.1%} (probability favorable movement occurs before adverse)")
        sections.append(f"    MFE First Count: {sequence_stats.get('mfe_first_count', 0):,} trades")
        sections.append(f"    MAE First Count: {sequence_stats.get('mae_first_count', 0):,} trades")
        sections.append("")
        sections.append("  Timing Analysis:")
        sections.append(f"    Median Time to MFE: {sequence_stats.get('median_time_to_mfe', 0):.0f} minutes from entry")
        sections.append(f"    Median Time to MAE: {sequence_stats.get('median_time_to_mae', 0):.0f} minutes from entry")
        sections.append(f"    Mean Time to MFE: {sequence_stats.get('mean_time_to_mfe', 0):.0f} minutes")
        sections.append(f"    Mean Time to MAE: {sequence_stats.get('mean_time_to_mae', 0):.0f} minutes")
        sections.append(f"    Median Time Delta (MAE-MFE): {sequence_stats.get('median_time_delta', 0):+.0f} minutes")
        sections.append("")
        sections.append("  Early Movement Analysis:")
        sections.append(f"    % MFE within 30 min: {sequence_stats.get('pct_mfe_under_30min', 0):.1f}%")
        sections.append(f"    % MFE within 60 min: {sequence_stats.get('pct_mfe_under_60min', 0):.1f}%")
        sections.append(f"    % MAE within 30 min: {sequence_stats.get('pct_mae_under_30min', 0):.1f}%")
        sections.append("")
        sections.append("  Sample Size:")
        sections.append(f"    Total Trades Analyzed: {sequence_stats.get('total_trades', 0):,}")
        sections.append("")
        sections.append("  Monte Carlo Interpretation:")
        mfe_first_rate = sequence_stats.get('mfe_first_rate', 0)
        if mfe_first_rate >= 0.55:
            sections.append("    -> P(MFE First) >= 55%: Entry direction shows favorable edge")
        elif mfe_first_rate >= 0.45:
            sections.append("    -> P(MFE First) ~50%: Entry direction is neutral (random)")
        else:
            sections.append("    -> P(MFE First) < 45%: Entry direction shows adverse bias")
        sections.append("")

    # Simulated Outcome Analysis (CALC-004) - Multi-R Analysis
    if simulated_stats and simulated_stats.get('total_trades', 0) > 0:
        sections.append("SIMULATED OUTCOME ANALYSIS (CALC-004) - Multi-R Comparison:")
        sections.append("-" * 60)
        sections.append("  Core Question: Which R:R ratio produces the best expectancy?")
        sections.append("")
        sections.append("  Simulation Parameters:")
        sections.append(f"    Fixed Stop %: {simulated_stats.get('stop_pct', 0):.2f}%")
        sections.append(f"    R Ratios Tested: 1R, 2R, 3R, 4R, 5R")
        sections.append("")

        # Multi-R comparison table
        multi_r_summary = simulated_stats.get('multi_r_summary', [])
        if multi_r_summary:
            sections.append("  R:R Comparison Table:")
            sections.append("  " + "-" * 50)
            sections.append(f"  {'Target':<8} {'Win Rate':>10} {'Expectancy':>12} {'Best':>6}")
            sections.append("  " + "-" * 50)

            best_r = simulated_stats.get('best_r_ratio', 1.0)
            for r_data in multi_r_summary:
                r_ratio = r_data.get('r_ratio', 0)
                win_rate = r_data.get('win_rate', 0)
                expectancy = r_data.get('expectancy_r', 0)
                is_best = " *" if r_ratio == best_r else ""
                r_label = f"{int(r_ratio)}R" if r_ratio == int(r_ratio) else f"{r_ratio}R"
                sections.append(f"  {r_label:<8} {win_rate:>9.1f}% {expectancy:>+11.3f}R{is_best:>5}")

            sections.append("  " + "-" * 50)
            sections.append("  * = Best expectancy")
            sections.append("")

        # Best R:R details
        best_r = simulated_stats.get('best_r_ratio', 1.0)
        sections.append(f"  Best R:R Ratio: 1:{best_r:.0f}")
        sections.append(f"    Target %: {simulated_stats.get('target_pct', 0):.2f}%")
        sections.append(f"    Wins: {simulated_stats.get('wins', 0):,} (target hit before stop)")
        sections.append(f"    Losses: {simulated_stats.get('losses', 0):,} (stop hit before target)")
        sections.append(f"    EOD Exits: {simulated_stats.get('eod_exits', 0):,} (neither hit by 15:30)")
        sections.append(f"    Win Rate: {simulated_stats.get('win_rate', 0):.1f}% (excludes EOD exits)")
        sim_expectancy = simulated_stats.get('expectancy_r', 0)
        sections.append(f"    Expectancy: {sim_expectancy:+.3f}R")
        sections.append("")
        sections.append("  Sample Size:")
        sections.append(f"    Total Trades Analyzed: {simulated_stats.get('total_trades', 0):,}")
        sections.append("")
        sections.append("  Interpretation:")
        if sim_expectancy > 0.1:
            sections.append(f"    -> Best R:R (1:{best_r:.0f}) shows strong positive expectancy")
        elif sim_expectancy > 0:
            sections.append(f"    -> Best R:R (1:{best_r:.0f}) shows marginally positive expectancy")
        else:
            sections.append(f"    -> All R:R ratios show negative or zero expectancy")
        sections.append("")

    # Available calculations
    sections.append("CALCULATIONS CURRENTLY AVAILABLE IN THIS VIEW:")
    sections.append("-" * 30)
    if available_calculations:
        for calc in available_calculations:
            sections.append(f"  - {calc}")
    else:
        sections.append("  - CALC-001: Win Rate by Model (MFE before MAE methodology)")
        sections.append("  - CALC-002: MFE/MAE Distribution Analysis (percentage-based, entry to 15:30)")
    sections.append("")

    # Note about additional data
    sections.append("ADDITIONAL DATA AVAILABLE FOR DEEPER ANALYSIS:")
    sections.append("-" * 30)
    sections.append("  - optimal_trades table: Indicator snapshots at ENTRY/MFE/MAE/EXIT")
    sections.append("  - trade_bars table: Bar-by-bar OHLCV and delta data")
    sections.append("  - Filtering by: date range, model, direction, ticker")
    sections.append("")
    sections.append("(Refer to AVAILABLE DATA REFERENCE section for full schema)")

    return "\n".join(sections)


# =============================================================================
# GENERIC DATA COLLECTOR (for future tabs)
# =============================================================================

def collect_tab_data(
    tab_name: str,
    **kwargs
) -> str:
    """
    Generic data collector that routes to tab-specific collectors.

    Args:
        tab_name: Name of the tab
        **kwargs: Tab-specific data arguments

    Returns:
        Formatted data string for prompt insertion
    """
    collectors = {
        "metrics_overview": collect_metrics_overview_data,
        # Future collectors will be added here:
        # "continuation": collect_continuation_data,
        # "rejection": collect_rejection_data,
        # "indicators": collect_indicators_data,
        # "health": collect_health_data,
    }

    collector = collectors.get(tab_name)

    if collector:
        return collector(**kwargs)
    else:
        # Default: just format whatever data was passed
        sections = [f"DATA FOR TAB: {tab_name}", "-" * 40]
        for key, value in kwargs.items():
            if isinstance(value, pd.DataFrame):
                sections.append(f"\n{key.upper()}:")
                sections.append(value.to_string())
            elif isinstance(value, dict):
                sections.append(f"\n{key.upper()}:")
                sections.append(_format_key_value(value))
            elif isinstance(value, list):
                sections.append(f"\n{key.upper()}: {len(value)} items")
            else:
                sections.append(f"{key}: {value}")

        return "\n".join(sections)