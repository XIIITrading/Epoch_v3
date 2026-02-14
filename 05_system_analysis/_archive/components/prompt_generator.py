"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Claude Analysis Prompt Generator
XIII Trading LLC
================================================================================

Generates copyable analysis prompts for Claude based on current filter state
and data. Enables seamless workflow between the Streamlit tool and Claude
for deeper analysis.

================================================================================
"""

import streamlit as st
from datetime import date
from typing import Dict, Any, List, Optional
import pandas as pd


def _format_date(d: Optional[date]) -> str:
    """Format date for display."""
    if d is None:
        return "All"
    return d.strftime("%Y-%m-%d")


def _format_filters(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str
) -> str:
    """Format current filter state as markdown."""
    lines = [
        f"- Date Range: {_format_date(date_from)} to {_format_date(date_to)}",
        f"- Models: {', '.join(models) if models else 'All'}",
        f"- Direction: {', '.join(directions) if directions else 'All'}",
        f"- Tickers: {', '.join(tickers) if tickers else 'All'}",
        f"- Outcome Filter: {outcome}"
    ]
    return "\n".join(lines)


def _format_summary_stats(stats: Dict[str, Any]) -> str:
    """Format summary statistics as markdown."""
    total = stats.get("total", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    avg_r = stats.get("avg_r", 0)
    total_r = stats.get("total_r", 0)

    return f"""- Total Trades: {total:,}
- Wins: {wins:,} | Losses: {losses:,}
- Win Rate: {win_rate:.1f}%
- Average R: {avg_r:+.2f}R
- Total R: {total_r:+.2f}R"""


def _format_indicator_comparison(comparison: Dict[str, Dict[str, float]]) -> str:
    """Format indicator comparison table as markdown."""
    if not comparison or "winners" not in comparison or "losers" not in comparison:
        return "No indicator comparison data available."

    winners = comparison["winners"]
    losers = comparison["losers"]

    lines = ["| Indicator | Winners | Losers | Delta |", "|-----------|---------|--------|-------|"]

    indicator_names = {
        "health_score": "Health Score",
        "vwap": "VWAP",
        "sma9": "SMA9",
        "sma21": "SMA21",
        "sma_spread": "SMA Spread",
        "sma_momentum": "SMA Momentum",
        "vol_roc": "Volume ROC",
        "vol_delta": "Volume Delta",
        "cvd_slope": "CVD Slope"
    }

    for key, display_name in indicator_names.items():
        if key in winners and key in losers:
            win_val = winners[key]
            loss_val = losers[key]
            delta = win_val - loss_val
            lines.append(f"| {display_name} | {win_val:.3f} | {loss_val:.3f} | {delta:+.3f} |")

    return "\n".join(lines)


def _format_model_stats(model_stats: List[Dict[str, Any]]) -> str:
    """Format model statistics as markdown table."""
    if not model_stats:
        return "No model statistics available."

    lines = ["| Model | Type | Total | Win Rate | Avg R |", "|-------|------|-------|----------|-------|"]

    for m in model_stats:
        model = m.get("model", "?")
        trade_type = m.get("trade_type", "?")
        total = m.get("total", 0)
        win_rate = m.get("win_rate", 0)
        avg_r = m.get("avg_r", 0)
        lines.append(f"| {model} | {trade_type} | {total} | {win_rate:.1f}% | {avg_r:+.2f}R |")

    return "\n".join(lines)


def generate_overview_prompt(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str,
    overall_stats: Dict[str, Any],
    model_stats: List[Dict[str, Any]],
    comparison: Dict[str, Dict[str, Any]]
) -> str:
    """Generate analysis prompt for Overview tab."""

    cont_stats = comparison.get("continuation", {})
    rej_stats = comparison.get("rejection", {})

    prompt = f"""## Epoch Indicator Analysis - Overview

**Filters Applied:**
{_format_filters(date_from, date_to, models, directions, tickers, outcome)}

**Overall Performance:**
{_format_summary_stats(overall_stats)}

**Performance by Model:**
{_format_model_stats(model_stats)}

**Continuation vs Rejection:**
| Metric | Continuation | Rejection |
|--------|--------------|-----------|
| Total | {cont_stats.get('total', 0)} | {rej_stats.get('total', 0)} |
| Win Rate | {cont_stats.get('win_rate', 0):.1f}% | {rej_stats.get('win_rate', 0):.1f}% |
| Avg R | {cont_stats.get('avg_r', 0):+.2f}R | {rej_stats.get('avg_r', 0):+.2f}R |

---

**Analysis Request:**
Based on this overview of my Epoch trading system performance, please analyze:
1. Which entry model type (continuation vs rejection) shows stronger edge?
2. Are there any models significantly underperforming that need review?
3. What patterns do you see in the win rate distribution across models?
4. Any recommendations for focus areas to improve overall system performance?
"""
    return prompt


def _format_direction_stats(direction_stats: Dict[str, Dict[str, Any]]) -> str:
    """Format direction statistics as markdown table."""
    dir_lines = ["| Direction | Total | Win Rate | Avg R |", "|-----------|-------|----------|-------|"]
    if isinstance(direction_stats, dict):
        for direction, stats in direction_stats.items():
            if isinstance(stats, dict):
                dir_lines.append(f"| {direction} | {stats.get('total', 0)} | {stats.get('win_rate', 0):.1f}% | {stats.get('avg_r', 0):+.2f}R |")
    return "\n".join(dir_lines)


def _format_exit_stats(exit_stats: Dict[str, Dict[str, Any]]) -> str:
    """Format exit reason statistics as markdown table."""
    exit_lines = ["| Exit Reason | Total | Win Rate | Avg R |", "|-------------|-------|----------|-------|"]
    if isinstance(exit_stats, dict):
        for reason, stats in exit_stats.items():
            if isinstance(stats, dict):
                exit_lines.append(f"| {reason} | {stats.get('total', 0)} | {stats.get('win_rate', 0):.1f}% | {stats.get('avg_r', 0):+.2f}R |")
    return "\n".join(exit_lines)


def generate_continuation_prompt(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str,
    stats: Dict[str, Any],
    indicator_comparison: Dict[str, Dict[str, float]],
    direction_stats: Dict[str, Dict[str, Any]],
    exit_stats: Dict[str, Dict[str, Any]]
) -> str:
    """Generate analysis prompt for Continuation tab."""

    dir_table = _format_direction_stats(direction_stats)
    exit_table = _format_exit_stats(exit_stats)

    prompt = f"""## Epoch Indicator Analysis - Continuation Trades (EPCH1/EPCH3)

**Trade Type:** Continuation (through the zone - momentum continuation)

**Filters Applied:**
{_format_filters(date_from, date_to, models, directions, tickers, outcome)}

**Summary:**
{_format_summary_stats(stats)}

**By Direction:**
{dir_table}

**By Exit Reason:**
{exit_table}

**Indicator Comparison at Entry (Winners vs Losers):**
{_format_indicator_comparison(indicator_comparison)}

---

**Analysis Request:**
Analyzing my continuation trades (trades through supply/demand zones):
1. Which indicators show the strongest predictive signal separating winners from losers?
2. Are there indicator thresholds that would improve the win rate if used as filters?
3. Is there a significant difference between LONG and SHORT continuation trades?
4. What exit patterns correlate with wins vs losses?
5. Based on the indicator deltas, what entry criteria refinements would you suggest?
"""
    return prompt


def generate_rejection_prompt(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str,
    stats: Dict[str, Any],
    indicator_comparison: Dict[str, Dict[str, float]],
    direction_stats: Dict[str, Dict[str, Any]],
    exit_stats: Dict[str, Dict[str, Any]]
) -> str:
    """Generate analysis prompt for Rejection tab."""

    dir_table = _format_direction_stats(direction_stats)
    exit_table = _format_exit_stats(exit_stats)

    prompt = f"""## Epoch Indicator Analysis - Rejection Trades (EPCH2/EPCH4)

**Trade Type:** Rejection (from the zone - reversal/bounce)

**Filters Applied:**
{_format_filters(date_from, date_to, models, directions, tickers, outcome)}

**Summary:**
{_format_summary_stats(stats)}

**By Direction:**
{dir_table}

**By Exit Reason:**
{exit_table}

**Indicator Comparison at Entry (Winners vs Losers):**
{_format_indicator_comparison(indicator_comparison)}

---

**Analysis Request:**
Analyzing my rejection trades (trades from supply/demand zones):
1. Which indicators show the strongest predictive signal separating winners from losers?
2. Rejection trades require price to reverse - which indicators best confirm reversal potential?
3. Are there indicator thresholds that would improve the win rate if used as filters?
4. Compare the indicator profiles to continuation trades - what differences matter?
5. Based on the indicator deltas, what entry criteria refinements would you suggest?
"""
    return prompt


def generate_indicator_prompt(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str,
    selected_indicator: str,
    event_stats: Dict[str, Dict[str, Any]],
    trade_type_comparison: Dict[str, Dict[str, Any]]
) -> str:
    """Generate analysis prompt for Indicator Deep Dive tab."""

    # Format event stats
    event_lines = ["| Event | Count | Mean | Median | Std Dev |", "|-------|-------|------|--------|---------|"]
    for event in ["ENTRY", "MFE", "MAE", "EXIT"]:
        if event in event_stats:
            e = event_stats[event]
            event_lines.append(f"| {event} | {e.get('count', 0)} | {e.get('mean', 0):.3f} | {e.get('median', 0):.3f} | {e.get('std', 0):.3f} |")
    event_table = "\n".join(event_lines)

    # Format trade type comparison
    cont_avgs = trade_type_comparison.get("continuation", {})
    rej_avgs = trade_type_comparison.get("rejection", {})

    prompt = f"""## Epoch Indicator Analysis - {selected_indicator.upper().replace('_', ' ')} Deep Dive

**Selected Indicator:** {selected_indicator}

**Filters Applied:**
{_format_filters(date_from, date_to, models, directions, tickers, outcome)}

**{selected_indicator.upper()} by Event Type:**
{event_table}

**Continuation vs Rejection at Entry:**
| Trade Type | {selected_indicator} Value |
|------------|---------------------------|
| Continuation | {cont_avgs.get(selected_indicator, 'N/A')} |
| Rejection | {rej_avgs.get(selected_indicator, 'N/A')} |

---

**Analysis Request:**
Deep diving into the {selected_indicator.replace('_', ' ')} indicator:
1. How does this indicator change from ENTRY to MFE (maximum favorable) to MAE (maximum adverse) to EXIT?
2. What does the event progression tell us about trade dynamics?
3. Is there a meaningful difference in this indicator between continuation and rejection trades?
4. What threshold values for this indicator would you recommend for trade filtering?
5. How should this indicator be weighted in the overall health score?
"""
    return prompt


def generate_health_prompt(
    date_from: Optional[date],
    date_to: Optional[date],
    models: List[str],
    directions: Optional[List[str]],
    tickers: Optional[List[str]],
    outcome: str,
    winner_stats: Dict[str, Any],
    loser_stats: Dict[str, Any],
    threshold_analysis: Dict[str, Any]
) -> str:
    """Generate analysis prompt for Health Score tab."""

    prompt = f"""## Epoch Indicator Analysis - Health Score Analysis

**Filters Applied:**
{_format_filters(date_from, date_to, models, directions, tickers, outcome)}

**Health Score Statistics:**
| Metric | Winners | Losers | Delta |
|--------|---------|--------|-------|
| Mean | {winner_stats.get('mean', 0):.2f} | {loser_stats.get('mean', 0):.2f} | {winner_stats.get('mean', 0) - loser_stats.get('mean', 0):+.2f} |
| Median | {winner_stats.get('median', 0):.2f} | {loser_stats.get('median', 0):.2f} | {winner_stats.get('median', 0) - loser_stats.get('median', 0):+.2f} |
| Std Dev | {winner_stats.get('std', 0):.2f} | {loser_stats.get('std', 0):.2f} | - |
| Min | {winner_stats.get('min', 0):.0f} | {loser_stats.get('min', 0):.0f} | - |
| Max | {winner_stats.get('max', 0):.0f} | {loser_stats.get('max', 0):.0f} | - |

**Threshold Analysis (Current: {threshold_analysis.get('threshold', 6)}):**
| Condition | Trades | Win Rate |
|-----------|--------|----------|
| Health >= {threshold_analysis.get('threshold', 6)} | {threshold_analysis.get('above_count', 0)} | {threshold_analysis.get('above_win_rate', 0):.1f}% |
| Health < {threshold_analysis.get('threshold', 6)} | {threshold_analysis.get('below_count', 0)} | {threshold_analysis.get('below_win_rate', 0):.1f}% |

---

**Analysis Request:**
Analyzing the 10-factor health score effectiveness:
1. Is the health score effectively separating winners from losers?
2. What is the optimal threshold for filtering trades based on health score?
3. Should the health score calculation be adjusted (factor weights, thresholds)?
4. Are there specific health score ranges that should trigger different position sizes?
5. How does the health score delta from Entry to MFE/MAE correlate with outcomes?

**Health Score Components (for reference):**
- H4/H1/M15/M5 Structure alignment (4 factors)
- Volume ROC, Volume Delta, CVD Slope (3 factors)
- SMA Alignment, SMA Momentum (2 factors)
- VWAP position (1 factor)
"""
    return prompt


def render_analysis_prompt(prompt: str, section_title: str = "Claude Analysis Prompt"):
    """Render a copyable analysis prompt section."""
    with st.expander(f"📋 {section_title}", expanded=False):
        st.markdown("*Copy this prompt and paste into Claude for deeper analysis:*")
        st.code(prompt, language="markdown")
        st.markdown("---")
        st.markdown("**Preview:**")
        st.markdown(prompt)
