"""
================================================================================
EPOCH TRADING SYSTEM - EPCH Indicators Edge Analysis
UI Components for Streamlit
================================================================================

Streamlit rendering functions for EPCH indicators edge analysis:
- Stop type selector
- Executive summary table
- Key findings display
- Detailed results by indicator
- Win rate charts
- Recommendations
- Monte AI prompt generation

Version: 1.0.0
================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from datetime import date

from .base_tester import (
    EdgeTestResult,
    fetch_epch_indicator_data,
    run_all_tests
)
from .prompt_generator import generate_epch_indicators_prompt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import CHART_CONFIG


# =============================================================================
# STOP TYPE CONFIGURATION
# =============================================================================

STOP_TYPE_OPTIONS = {
    'm5_atr': 'M5 ATR (1.1x) (Default)',
    'zone_buffer': 'Zone + 5% Buffer',
    'prior_m1': 'Prior M1 H/L',
    'prior_m5': 'Prior M5 H/L',
    'm15_atr': 'M15 ATR (1.1x)',
    'fractal': 'M5 Fractal H/L'
}

DEFAULT_STOP_TYPE = 'm5_atr'


# =============================================================================
# CHART THEME
# =============================================================================

def get_chart_layout(title: str = "", height: int = None) -> dict:
    """Get standard chart layout settings."""
    return {
        'title': title,
        'template': 'plotly_dark',
        'paper_bgcolor': CHART_CONFIG.get('paper_color', '#1a1a2e'),
        'plot_bgcolor': CHART_CONFIG.get('background_color', '#1a1a2e'),
        'font': {'color': CHART_CONFIG.get('text_color', '#e0e0e0')},
        'height': height or CHART_CONFIG.get('default_height', 400),
        'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60}
    }


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(ttl=300)
def load_epch_data(
    _date_from: date,
    _date_to: date,
    stop_type: str
) -> pd.DataFrame:
    """Load EPCH indicator data with caching."""
    return fetch_epch_indicator_data(
        date_from=_date_from,
        date_to=_date_to,
        stop_type=stop_type
    )


# =============================================================================
# UI COMPONENT: STOP TYPE SELECTOR
# =============================================================================

def render_stop_type_selector() -> str:
    """Render stop type selector and return selected value."""
    col1, col2 = st.columns([1, 2])

    with col1:
        selected = st.selectbox(
            "Win Condition (Stop Type)",
            options=list(STOP_TYPE_OPTIONS.keys()),
            format_func=lambda x: STOP_TYPE_OPTIONS.get(x, x),
            index=0,
            key="epch_stop_type"
        )

    with col2:
        st.info(
            "**Win Condition:** Trade is a WIN if MFE >= 1R reached before stop hit. "
            "Stop type determines the R calculation."
        )

    return selected


# =============================================================================
# UI COMPONENT: DATA SUMMARY
# =============================================================================

def render_data_summary(df: pd.DataFrame, stop_type: str):
    """Render data summary metrics."""
    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    total_trades = len(df)
    wins = df['is_winner'].sum()
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    # Date range
    min_date = df['date'].min()
    max_date = df['date'].max()

    # Model distribution
    model_counts = df['model'].value_counts().to_dict()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", f"{total_trades:,}")

    with col2:
        st.metric("Baseline Win Rate", f"{win_rate:.1f}%")

    with col3:
        st.metric("Date Range", f"{min_date} to {max_date}")

    with col4:
        st.metric("Stop Type", STOP_TYPE_OPTIONS.get(stop_type, stop_type))

    # Model breakdown
    st.markdown("**Trades by Model:**")
    model_df = pd.DataFrame([
        {'Model': k, 'Trades': v}
        for k, v in sorted(model_counts.items())
    ])
    st.dataframe(model_df, use_container_width=True, hide_index=True)


# =============================================================================
# UI COMPONENT: INDICATOR STATISTICS
# =============================================================================

def render_indicator_statistics(df: pd.DataFrame):
    """Render indicator statistics in expandable section."""
    with st.expander("Indicator Statistics", expanded=False):
        if df.empty:
            st.info("No data available.")
            return

        stats = []

        # Candle Range
        if 'candle_range_pct' in df.columns:
            cr = df['candle_range_pct'].dropna()
            if len(cr) > 0:
                stats.append({
                    'Indicator': 'Candle Range (%)',
                    'Mean': f"{cr.mean():.4f}",
                    'Median': f"{cr.median():.4f}",
                    'Std Dev': f"{cr.std():.4f}",
                    'Min': f"{cr.min():.4f}",
                    'Max': f"{cr.max():.4f}"
                })

        # Volume Delta
        if 'vol_delta' in df.columns:
            vd = df['vol_delta'].dropna()
            if len(vd) > 0:
                stats.append({
                    'Indicator': 'Volume Delta',
                    'Mean': f"{vd.mean():.2f}",
                    'Median': f"{vd.median():.2f}",
                    'Std Dev': f"{vd.std():.2f}",
                    'Min': f"{vd.min():.2f}",
                    'Max': f"{vd.max():.2f}"
                })

        # Volume ROC
        if 'vol_roc' in df.columns:
            vr = df['vol_roc'].dropna()
            if len(vr) > 0:
                stats.append({
                    'Indicator': 'Volume ROC (%)',
                    'Mean': f"{vr.mean():.2f}",
                    'Median': f"{vr.median():.2f}",
                    'Std Dev': f"{vr.std():.2f}",
                    'Min': f"{vr.min():.2f}",
                    'Max': f"{vr.max():.2f}"
                })

        # SMA Spread
        if 'sma_spread' in df.columns:
            ss = df['sma_spread'].dropna()
            if len(ss) > 0:
                stats.append({
                    'Indicator': 'SMA Spread',
                    'Mean': f"{ss.mean():.4f}",
                    'Median': f"{ss.median():.4f}",
                    'Std Dev': f"{ss.std():.4f}",
                    'Min': f"{ss.min():.4f}",
                    'Max': f"{ss.max():.4f}"
                })

        # H1 Structure distribution
        if 'h1_structure' in df.columns:
            h1_dist = df['h1_structure'].value_counts(normalize=True) * 100
            h1_str = ", ".join([f"{k}: {v:.1f}%" for k, v in h1_dist.items()])
            stats.append({
                'Indicator': 'H1 Structure',
                'Mean': h1_str,
                'Median': '-',
                'Std Dev': '-',
                'Min': '-',
                'Max': '-'
            })

        # LONG Score
        if 'long_score' in df.columns:
            ls = df['long_score'].dropna()
            if len(ls) > 0:
                stats.append({
                    'Indicator': 'LONG Score',
                    'Mean': f"{ls.mean():.2f}",
                    'Median': f"{ls.median():.1f}",
                    'Std Dev': f"{ls.std():.2f}",
                    'Min': f"{ls.min():.0f}",
                    'Max': f"{ls.max():.0f}"
                })

        # SHORT Score
        if 'short_score' in df.columns:
            ss = df['short_score'].dropna()
            if len(ss) > 0:
                stats.append({
                    'Indicator': 'SHORT Score',
                    'Mean': f"{ss.mean():.2f}",
                    'Median': f"{ss.median():.1f}",
                    'Std Dev': f"{ss.std():.2f}",
                    'Min': f"{ss.min():.0f}",
                    'Max': f"{ss.max():.0f}"
                })

        if stats:
            stats_df = pd.DataFrame(stats)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("No indicator statistics available.")


# =============================================================================
# UI COMPONENT: EXECUTIVE SUMMARY
# =============================================================================

def render_executive_summary(results: List[EdgeTestResult]):
    """Render executive summary table of all test results."""
    st.subheader("Executive Summary")

    if not results:
        st.info("No test results available.")
        return

    # Group by segment category
    segment_categories = [
        ("Overall", ["ALL"]),
        ("By Direction", ["LONG", "SHORT"]),
        ("By Trade Type", ["CONTINUATION (Combined)", "REJECTION (Combined)"]),
        ("By Model - Continuation", ["EPCH1 (Primary Cont.)", "EPCH3 (Secondary Cont.)"]),
        ("By Model - Rejection", ["EPCH2 (Primary Rej.)", "EPCH4 (Secondary Rej.)"]),
    ]

    for category_name, segment_names in segment_categories:
        category_results = [r for r in results if r.segment in segment_names]
        if not category_results:
            continue

        with st.expander(f"{category_name}", expanded=(category_name == "Overall")):
            rows = []
            for r in category_results:
                edge_icon = "YES" if r.has_edge else "NO"
                rows.append({
                    'Indicator': r.indicator,
                    'Test': r.test_name,
                    'Segment': r.segment,
                    'Edge?': edge_icon,
                    'Confidence': r.confidence,
                    'Effect (pp)': f"{r.effect_size:.1f}",
                    'p-value': f"{r.p_value:.4f}"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# UI COMPONENT: KEY FINDINGS
# =============================================================================

def render_key_findings(results: List[EdgeTestResult]):
    """Render key findings (edges detected)."""
    st.subheader("Key Findings (Edges Detected)")

    edges = [r for r in results if r.has_edge]

    if not edges:
        st.info("No statistically significant edges detected with the current data.")
        return

    # Sort by effect size
    edges_sorted = sorted(edges, key=lambda x: x.effect_size, reverse=True)

    for r in edges_sorted:
        st.markdown(
            f"- **{r.segment}** - {r.indicator} ({r.test_name}): "
            f"{r.effect_size:.1f}pp advantage (p={r.p_value:.4f})"
        )


# =============================================================================
# UI COMPONENT: DETAILED RESULTS BY INDICATOR
# =============================================================================

def render_detailed_results(results: List[EdgeTestResult], df: pd.DataFrame):
    """Render detailed results organized by indicator."""
    st.subheader("Detailed Results by Indicator")

    indicators = list(set(r.indicator for r in results))
    indicators.sort()

    for indicator in indicators:
        indicator_results = [r for r in results if r.indicator == indicator]

        with st.expander(f"{indicator}", expanded=False):
            # Summary table for this indicator
            rows = []
            for r in indicator_results:
                edge_icon = "YES" if r.has_edge else "NO"
                rows.append({
                    'Test': r.test_name,
                    'Segment': r.segment,
                    'Edge?': edge_icon,
                    'Conf': r.confidence,
                    'Effect': f"{r.effect_size:.1f}pp",
                    'p-value': f"{r.p_value:.4f}"
                })

            summary_df = pd.DataFrame(rows)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # Win rate chart for "ALL" segment
            all_results = [r for r in indicator_results if r.segment == "ALL"]
            if all_results:
                st.markdown("**Win Rate by Group (ALL Trades):**")
                for r in all_results[:2]:  # Show first 2 tests
                    if r.groups:
                        render_win_rate_chart(r.groups, r.test_name, r.baseline_win_rate)


# =============================================================================
# UI COMPONENT: WIN RATE CHART
# =============================================================================

def render_win_rate_chart(
    groups: Dict[str, Dict],
    title: str,
    baseline: float
):
    """Render win rate bar chart for a single test."""
    if not groups:
        return

    # Prepare data
    data = []
    for group_name, stats in groups.items():
        data.append({
            'Group': group_name,
            'Win Rate': stats['win_rate'],
            'Trades': stats['trades']
        })

    if not data:
        return

    chart_df = pd.DataFrame(data)

    # Create bar chart
    fig = px.bar(
        chart_df,
        x='Group',
        y='Win Rate',
        text='Trades',
        color='Win Rate',
        color_continuous_scale=['#ef5350', '#ffeb3b', '#26a69a']
    )

    # Add baseline line
    fig.add_hline(
        y=baseline,
        line_dash="dash",
        line_color="#ffffff",
        annotation_text=f"Baseline: {baseline:.1f}%",
        annotation_position="right"
    )

    fig.update_layout(**get_chart_layout(title, height=300))
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# UI COMPONENT: RECOMMENDATIONS
# =============================================================================

def render_recommendations(results: List[EdgeTestResult]):
    """Render recommendations based on test results."""
    st.subheader("Recommendations")

    edges = [r for r in results if r.has_edge]
    no_edge = [r for r in results if not r.has_edge and r.confidence != "LOW"]
    low_conf = [r for r in results if r.confidence == "LOW"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Implement (Edges Found)**")
        if edges:
            for r in edges[:10]:  # Limit to top 10
                st.markdown(f"- {r.indicator}: {r.test_name} ({r.segment})")
        else:
            st.info("No edges to implement.")

    with col2:
        st.markdown("**No Action Needed**")
        if no_edge:
            unique_tests = set((r.indicator, r.test_name) for r in no_edge)
            for ind, test in list(unique_tests)[:10]:
                st.markdown(f"- {ind}: {test}")
        else:
            st.info("All tests show edge or need more data.")

    with col3:
        st.markdown("**Needs More Data**")
        if low_conf:
            unique_tests = set((r.indicator, r.test_name) for r in low_conf)
            for ind, test in list(unique_tests)[:10]:
                st.markdown(f"- {ind}: {test}")
        else:
            st.info("Sufficient data for all tests.")


# =============================================================================
# UI COMPONENT: EFFECT SIZE COMPARISON
# =============================================================================

def render_effect_size_comparison(results: List[EdgeTestResult]):
    """Render effect size comparison chart for edges."""
    edges = [r for r in results if r.has_edge and r.segment == "ALL"]

    if not edges:
        return

    st.subheader("Effect Size Comparison (Edges Only)")

    # Sort by effect size
    edges_sorted = sorted(edges, key=lambda x: x.effect_size, reverse=True)[:15]

    data = []
    for r in edges_sorted:
        data.append({
            'Test': f"{r.indicator}: {r.test_name}",
            'Effect Size (pp)': r.effect_size,
            'p-value': r.p_value
        })

    chart_df = pd.DataFrame(data)

    fig = px.bar(
        chart_df,
        x='Effect Size (pp)',
        y='Test',
        orientation='h',
        color='Effect Size (pp)',
        color_continuous_scale=['#ffeb3b', '#26a69a']
    )

    fig.update_layout(**get_chart_layout("Edge Effect Sizes (pp)", height=400))

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# UI COMPONENT: MONTE AI SECTION
# =============================================================================

def render_monte_ai_section(results: List[EdgeTestResult], df: pd.DataFrame, stop_type: str):
    """Render Monte AI analysis section with generated prompt."""
    st.subheader("Monte AI Analysis")

    # Generate prompt
    prompt = generate_epch_indicators_prompt(results, df, stop_type)

    # Store in session state
    st.session_state['epch_indicators_result'] = {
        'prompt': prompt,
        'results': [r.to_dict() for r in results],
        'total_trades': len(df),
        'baseline_win_rate': (df['is_winner'].sum() / len(df) * 100) if len(df) > 0 else 0
    }

    with st.expander("Generated Prompt for Claude Analysis", expanded=False):
        st.text_area(
            "Copy this prompt to Claude for detailed analysis:",
            value=prompt,
            height=400,
            key="monte_ai_prompt"
        )

    st.info(
        "The above prompt contains all edge test results and can be used with Claude "
        "to get detailed insights about which indicators are most predictive for your trades."
    )


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_epch_indicators_section(
    date_from: date,
    date_to: date
) -> Optional[Dict[str, Any]]:
    """
    Main render function for EPCH Indicators tab.

    Args:
        date_from: Start date for analysis
        date_to: End date for analysis

    Returns:
        Dict with analysis results for Monte AI integration
    """
    st.header("EPCH Indicators Edge Analysis")
    st.markdown(
        "*Aggregate analysis of EPCH v1.0 indicators to identify which conditions "
        "correlate with higher win rates.*"
    )

    st.divider()

    # Stop type selector
    stop_type = render_stop_type_selector()

    st.divider()

    # Load data
    with st.spinner("Loading indicator data..."):
        df = load_epch_data(date_from, date_to, stop_type)

    if df.empty:
        st.warning(
            "No data found. Please ensure:\n"
            "1. The `m1_indicator_bars` table is populated\n"
            "2. The `stop_analysis` table has data for the selected stop type\n"
            "3. The date range contains trades"
        )
        return None

    # Data summary
    render_data_summary(df, stop_type)

    st.divider()

    # Indicator statistics
    render_indicator_statistics(df)

    st.divider()

    # Run all tests
    with st.spinner("Running edge analysis tests..."):
        results = run_all_tests(df)

    if not results:
        st.warning("No test results generated. Check data completeness.")
        return None

    # Executive summary
    render_executive_summary(results)

    st.divider()

    # Key findings
    render_key_findings(results)

    st.divider()

    # Effect size comparison
    render_effect_size_comparison(results)

    st.divider()

    # Detailed results
    render_detailed_results(results, df)

    st.divider()

    # Recommendations
    render_recommendations(results)

    st.divider()

    # Monte AI section
    render_monte_ai_section(results, df, stop_type)

    return st.session_state.get('epch_indicators_result')
