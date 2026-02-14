"""
================================================================================
EPOCH TRADING SYSTEM - INDICATOR ANALYSIS
CALC-007: Indicator Progression Analysis
XIII Trading LLC
================================================================================

Analyzes how indicators change from ENTRY to MFE/MAE using m5_trade_bars data.
Identifies early warning signals for failing trades.

Core Question: "What indicator changes signal that a trade is working vs failing?"

Purpose:
    1. Exit Signal Development - Identify when to exit early
    2. Winner/Loser Differentiation - What separates winning trades?
    3. Early Warning Signals - Detect failing trades before stop hit
    4. DOW AI Exit Recommendations - Provide exit guidance

Data Source: m5_trade_bars table (populated by secondary_analysis module)

WIN CONDITION (Stop-Based):
    Win = MFE reached (>=1R) before stop hit
    Loss = Stop hit before reaching 1R

    The is_winner flag must be pre-computed from stop_analysis table
    and merged into the data before calling these functions.
    Default stop type: Zone + 5% Buffer

Version: 2.1.0
Updated: 2026-01-11
- Removed temporal mfe_time < mae_time logic
- Now uses stop-based is_winner exclusively
================================================================================
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import streamlit as st

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import INDICATOR_ANALYSIS_CONFIG


# =============================================================================
# CONSTANTS
# =============================================================================

# Indicators to track progression
PROGRESSION_INDICATORS = [
    'health_score',
    'structure_score',
    'volume_score',
    'price_score',
    'cvd_slope',
    'vol_delta',
    'vol_roc',
    'sma_spread',
    'sma_momentum_ratio'
]

# Health score factor columns
HEALTH_FACTORS = [
    'sma_alignment_healthy',
    'sma_momentum_healthy',
    'vwap_healthy',
    'vol_roc_healthy',
    'vol_delta_healthy',
    'cvd_slope_healthy',
    'h4_structure_healthy',
    'h1_structure_healthy',
    'm15_structure_healthy',
    'm5_structure_healthy'
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EventSnapshot:
    """Indicator snapshot at a specific event."""
    event_type: str
    avg_health_score: float
    std_health_score: float
    avg_structure_score: float
    avg_volume_score: float
    avg_price_score: float
    avg_cvd_slope: float
    avg_vol_delta: float
    avg_sma_spread: float
    trade_count: int
    avg_bars_from_entry: float


@dataclass
class ProgressionPath:
    """Indicator progression path for a trade group (winners/losers)."""
    outcome: str  # 'WIN' or 'LOSS'
    entry_snapshot: EventSnapshot
    peak_snapshot: EventSnapshot  # MFE for winners, MAE for losers

    # Deltas
    health_delta_to_peak: float
    structure_delta_to_peak: float
    volume_delta_to_peak: float
    price_delta_to_peak: float
    cvd_delta_to_peak: float
    vol_delta_to_peak: float

    # Timing
    avg_bars_to_peak: float
    trade_count: int


@dataclass
class EarlyWarningSignal:
    """Early warning signal definition."""
    indicator: str
    threshold: float
    direction: str  # 'drop' or 'rise'
    bars_window: int
    hit_rate_losers: float  # % of losers that show this signal
    hit_rate_winners: float  # % of winners that show this signal (false positives)
    lift: float  # hit_rate_losers - hit_rate_winners
    predictive_power: float  # Lift / hit_rate_losers


@dataclass
class FactorDegradationAnalysis:
    """Analysis of how individual factors degrade before MAE."""
    factor_name: str
    healthy_at_entry_pct: float
    healthy_at_mae_pct: float
    degradation_rate: float  # entry - mae
    flip_rate: float  # % that went from healthy to unhealthy
    early_flip_rate: float  # % that flipped within first 5 bars


@dataclass
class IndicatorProgressionResult:
    """Container for all progression analysis results."""
    total_trades: int
    winner_count: int
    loser_count: int
    overall_win_rate: float

    # Progression paths
    winner_path: Optional[ProgressionPath]
    loser_path: Optional[ProgressionPath]

    # By-event summary
    event_summary: pd.DataFrame  # [event_type, outcome, health_score, etc.]

    # Delta distributions
    winner_deltas: pd.DataFrame  # [indicator, entry_val, peak_val, delta, pct_change]
    loser_deltas: pd.DataFrame

    # Early warning signals
    early_warnings: List[EarlyWarningSignal]

    # Best early warning
    best_warning: Optional[EarlyWarningSignal]

    # Factor degradation analysis
    factor_degradation: List[FactorDegradationAnalysis]

    # Bar-by-bar progression (for charting)
    bar_progression: pd.DataFrame  # [bars_from_entry, outcome, avg_health, etc.]


# =============================================================================
# SNAPSHOT FUNCTIONS
# =============================================================================

def calculate_event_snapshot(
    df: pd.DataFrame,
    event_type: str
) -> Optional[EventSnapshot]:
    """
    Calculate indicator averages at a specific event type.

    Parameters:
        df: DataFrame filtered to specific outcome group
        event_type: 'ENTRY', 'MFE', 'MAE', or 'MFE_MAE'

    Returns:
        EventSnapshot with average values
    """
    # Handle MFE_MAE as both MFE and MAE
    if event_type in ['MFE', 'MAE']:
        event_df = df[df['event_type'].isin([event_type, 'MFE_MAE'])]
    else:
        event_df = df[df['event_type'] == event_type]

    if len(event_df) == 0:
        return None

    def safe_mean(col):
        if col not in event_df.columns:
            return 0.0
        vals = pd.to_numeric(event_df[col], errors='coerce')
        return vals.mean() if len(vals) > 0 else 0.0

    def safe_std(col):
        if col not in event_df.columns:
            return 0.0
        vals = pd.to_numeric(event_df[col], errors='coerce')
        return vals.std() if len(vals) > 0 else 0.0

    return EventSnapshot(
        event_type=event_type,
        avg_health_score=safe_mean('health_score'),
        std_health_score=safe_std('health_score'),
        avg_structure_score=safe_mean('structure_score'),
        avg_volume_score=safe_mean('volume_score'),
        avg_price_score=safe_mean('price_score'),
        avg_cvd_slope=safe_mean('cvd_slope'),
        avg_vol_delta=safe_mean('vol_delta'),
        avg_sma_spread=safe_mean('sma_spread'),
        trade_count=len(event_df['trade_id'].unique()),
        avg_bars_from_entry=safe_mean('bars_from_entry')
    )


def calculate_progression_path(
    df: pd.DataFrame,
    outcome: str,
    is_winner: bool
) -> Optional[ProgressionPath]:
    """
    Calculate progression path for winners or losers.

    Parameters:
        df: DataFrame with m5_trade_bars data
        outcome: 'WIN' or 'LOSS'
        is_winner: True for winners, False for losers

    Returns:
        ProgressionPath for the group
    """
    # Filter to outcome group
    group_df = df[df['is_winner'] == is_winner]

    if len(group_df) == 0:
        return None

    # Get snapshots
    entry_snapshot = calculate_event_snapshot(group_df, 'ENTRY')

    # Peak event differs by outcome
    if is_winner:
        peak_snapshot = calculate_event_snapshot(group_df, 'MFE')
    else:
        peak_snapshot = calculate_event_snapshot(group_df, 'MAE')

    if not entry_snapshot or not peak_snapshot:
        return None

    # Calculate deltas
    health_delta = peak_snapshot.avg_health_score - entry_snapshot.avg_health_score
    structure_delta = peak_snapshot.avg_structure_score - entry_snapshot.avg_structure_score
    volume_delta = peak_snapshot.avg_volume_score - entry_snapshot.avg_volume_score
    price_delta = peak_snapshot.avg_price_score - entry_snapshot.avg_price_score
    cvd_delta = peak_snapshot.avg_cvd_slope - entry_snapshot.avg_cvd_slope
    vol_delta = peak_snapshot.avg_vol_delta - entry_snapshot.avg_vol_delta

    return ProgressionPath(
        outcome=outcome,
        entry_snapshot=entry_snapshot,
        peak_snapshot=peak_snapshot,
        health_delta_to_peak=health_delta,
        structure_delta_to_peak=structure_delta,
        volume_delta_to_peak=volume_delta,
        price_delta_to_peak=price_delta,
        cvd_delta_to_peak=cvd_delta,
        vol_delta_to_peak=vol_delta,
        avg_bars_to_peak=peak_snapshot.avg_bars_from_entry,
        trade_count=len(group_df['trade_id'].unique())
    )


# =============================================================================
# BAR-BY-BAR ANALYSIS
# =============================================================================

def calculate_bar_by_bar_progression(
    df: pd.DataFrame,
    max_bars: int = 30
) -> pd.DataFrame:
    """
    Calculate average indicator values by bars_from_entry and outcome.

    Parameters:
        df: DataFrame with m5_trade_bars data
        max_bars: Maximum bars from entry to analyze

    Returns:
        DataFrame with [bars_from_entry, outcome, avg_health, avg_structure, ...]
    """
    # Filter to reasonable bar range
    df_filtered = df[df['bars_from_entry'] <= max_bars].copy()

    results = []

    for bars in range(0, max_bars + 1):
        for is_winner in [True, False]:
            subset = df_filtered[
                (df_filtered['bars_from_entry'] == bars) &
                (df_filtered['is_winner'] == is_winner)
            ]

            if len(subset) < 5:  # Minimum sample
                continue

            outcome = 'WIN' if is_winner else 'LOSS'

            row = {
                'bars_from_entry': bars,
                'outcome': outcome,
                'trade_count': len(subset['trade_id'].unique()),
                'avg_health_score': pd.to_numeric(subset['health_score'], errors='coerce').mean(),
                'std_health_score': pd.to_numeric(subset['health_score'], errors='coerce').std(),
                'avg_structure_score': pd.to_numeric(subset['structure_score'], errors='coerce').mean(),
                'avg_volume_score': pd.to_numeric(subset['volume_score'], errors='coerce').mean(),
                'avg_price_score': pd.to_numeric(subset['price_score'], errors='coerce').mean()
            }
            results.append(row)

    return pd.DataFrame(results)


# =============================================================================
# EARLY WARNING SIGNALS
# =============================================================================

def calculate_early_warning_signals(
    df: pd.DataFrame,
    indicators: List[str] = None,
    bars_windows: List[int] = [3, 5, 10, 15]
) -> List[EarlyWarningSignal]:
    """
    Identify early warning signals that predict losing trades.

    Parameters:
        df: DataFrame with m5_trade_bars data
        indicators: List of indicators to analyze
        bars_windows: Number of bars from entry to check

    Returns:
        List of EarlyWarningSignal objects sorted by lift
    """
    if indicators is None:
        indicators = ['health_score', 'cvd_slope', 'structure_score', 'volume_score']

    warnings = []

    for indicator in indicators:
        if indicator not in df.columns:
            continue

        for bars_window in bars_windows:
            # Get entry values
            entry_df = df[df['event_type'] == 'ENTRY']
            entry_vals = entry_df.groupby('trade_id')[indicator].first()
            entry_vals = pd.to_numeric(entry_vals, errors='coerce')

            # Get values at N bars from entry
            window_df = df[df['bars_from_entry'] == bars_window]
            window_vals = window_df.groupby('trade_id')[indicator].first()
            window_vals = pd.to_numeric(window_vals, errors='coerce')

            # Calculate change
            common_trades = entry_vals.index.intersection(window_vals.index)
            if len(common_trades) < 30:
                continue

            changes = window_vals[common_trades] - entry_vals[common_trades]

            # Get outcomes
            outcomes = df[df['trade_id'].isin(common_trades)].groupby('trade_id')['is_winner'].first()

            # Test different thresholds based on indicator type
            if indicator == 'health_score':
                thresholds = [-3, -2, -1.5, -1]
            elif indicator in ['structure_score', 'volume_score', 'price_score']:
                thresholds = [-2, -1.5, -1]
            else:
                thresholds = [-0.5, -0.3, -0.1]

            for threshold in thresholds:
                # Calculate hit rates
                losers = outcomes[outcomes == False].index
                winners = outcomes[outcomes == True].index

                if len(losers) == 0 or len(winners) == 0:
                    continue

                loser_changes = changes[changes.index.isin(losers)]
                winner_changes = changes[changes.index.isin(winners)]

                loser_hits = (loser_changes <= threshold).sum() / len(losers) * 100 if len(losers) > 0 else 0
                winner_hits = (winner_changes <= threshold).sum() / len(winners) * 100 if len(winners) > 0 else 0

                lift = loser_hits - winner_hits
                predictive = lift / loser_hits if loser_hits > 0 else 0

                if lift > 5:  # Only add if meaningful lift
                    warnings.append(EarlyWarningSignal(
                        indicator=indicator,
                        threshold=threshold,
                        direction='drop',
                        bars_window=bars_window,
                        hit_rate_losers=loser_hits,
                        hit_rate_winners=winner_hits,
                        lift=lift,
                        predictive_power=predictive
                    ))

    # Sort by lift
    warnings.sort(key=lambda x: x.lift, reverse=True)

    return warnings


# =============================================================================
# FACTOR DEGRADATION ANALYSIS
# =============================================================================

def analyze_factor_degradation(
    df: pd.DataFrame
) -> List[FactorDegradationAnalysis]:
    """
    Analyze how individual health factors degrade from entry to MAE for losers.

    Parameters:
        df: DataFrame with m5_trade_bars data

    Returns:
        List of FactorDegradationAnalysis for each factor
    """
    # Filter to losers only
    loser_df = df[df['is_winner'] == False]

    results = []

    for factor in HEALTH_FACTORS:
        if factor not in loser_df.columns:
            continue

        # Get entry state
        entry_df = loser_df[loser_df['event_type'] == 'ENTRY']
        entry_healthy = entry_df.groupby('trade_id')[factor].first()

        # Get MAE state (include MFE_MAE)
        mae_df = loser_df[loser_df['event_type'].isin(['MAE', 'MFE_MAE'])]
        mae_healthy = mae_df.groupby('trade_id')[factor].first()

        # Get state at bar 5 (early check)
        bar5_df = loser_df[loser_df['bars_from_entry'] == 5]
        bar5_healthy = bar5_df.groupby('trade_id')[factor].first()

        common = entry_healthy.index.intersection(mae_healthy.index)
        if len(common) == 0:
            continue

        healthy_at_entry = entry_healthy[common].mean() * 100
        healthy_at_mae = mae_healthy[common].mean() * 100

        # Calculate flip rate (was healthy at entry, unhealthy at MAE)
        flipped = ((entry_healthy[common] == True) & (mae_healthy[common] == False)).sum()
        flip_rate = flipped / len(common) * 100

        # Calculate early flip rate
        common_bar5 = entry_healthy.index.intersection(bar5_healthy.index)
        early_flip_rate = 0
        if len(common_bar5) > 0:
            early_flipped = (
                (entry_healthy[common_bar5] == True) &
                (bar5_healthy[common_bar5] == False)
            ).sum()
            early_flip_rate = early_flipped / len(common_bar5) * 100

        # Clean factor name for display
        factor_name = factor.replace('_healthy', '').replace('_', ' ').title()

        results.append(FactorDegradationAnalysis(
            factor_name=factor_name,
            healthy_at_entry_pct=healthy_at_entry,
            healthy_at_mae_pct=healthy_at_mae,
            degradation_rate=healthy_at_entry - healthy_at_mae,
            flip_rate=flip_rate,
            early_flip_rate=early_flip_rate
        ))

    # Sort by degradation rate
    results.sort(key=lambda x: x.degradation_rate, reverse=True)

    return results


# =============================================================================
# SUMMARY FUNCTIONS
# =============================================================================

def create_event_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary table of indicator values by event and outcome.
    """
    results = []

    for event in ['ENTRY', 'MFE', 'MAE', 'MFE_MAE']:
        for is_winner in [True, False]:
            outcome = 'WIN' if is_winner else 'LOSS'

            if event in ['MFE', 'MAE']:
                subset = df[(df['event_type'].isin([event, 'MFE_MAE'])) & (df['is_winner'] == is_winner)]
            else:
                subset = df[(df['event_type'] == event) & (df['is_winner'] == is_winner)]

            if len(subset) == 0:
                continue

            row = {
                'event': event,
                'outcome': outcome,
                'trades': len(subset['trade_id'].unique()),
                'avg_bars': pd.to_numeric(subset['bars_from_entry'], errors='coerce').mean()
            }

            for indicator in PROGRESSION_INDICATORS:
                if indicator in subset.columns:
                    vals = pd.to_numeric(subset[indicator], errors='coerce')
                    row[f'{indicator}_avg'] = vals.mean()
                    row[f'{indicator}_std'] = vals.std()

            results.append(row)

    return pd.DataFrame(results)


def create_delta_summary(df: pd.DataFrame, is_winner: bool) -> pd.DataFrame:
    """
    Create summary of indicator changes from entry to peak.
    """
    outcome_df = df[df['is_winner'] == is_winner]
    peak_event = 'MFE' if is_winner else 'MAE'

    entry_df = outcome_df[outcome_df['event_type'] == 'ENTRY']
    peak_df = outcome_df[outcome_df['event_type'].isin([peak_event, 'MFE_MAE'])]

    results = []

    for indicator in PROGRESSION_INDICATORS:
        if indicator not in entry_df.columns:
            continue

        entry_vals = entry_df.groupby('trade_id')[indicator].first()
        peak_vals = peak_df.groupby('trade_id')[indicator].first()

        common = entry_vals.index.intersection(peak_vals.index)
        if len(common) == 0:
            continue

        # Convert to numeric
        entry_numeric = pd.to_numeric(entry_vals[common], errors='coerce')
        peak_numeric = pd.to_numeric(peak_vals[common], errors='coerce')

        entry_avg = entry_numeric.mean()
        peak_avg = peak_numeric.mean()
        delta = peak_avg - entry_avg
        pct_change = (delta / entry_avg * 100) if entry_avg != 0 else 0

        results.append({
            'indicator': indicator,
            'entry_avg': entry_avg,
            'peak_avg': peak_avg,
            'delta': delta,
            'pct_change': pct_change
        })

    return pd.DataFrame(results)


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_indicator_progression(df: pd.DataFrame) -> IndicatorProgressionResult:
    """
    Main analysis function for CALC-007.

    Parameters:
        df: DataFrame with m5_trade_bars data joined with outcomes

    Returns:
        IndicatorProgressionResult with all analysis outputs
    """
    # Filter out trades without stop analysis data (is_winner = None)
    df = df[df['is_winner'].notna()].copy()

    # Basic counts
    trades = df['trade_id'].unique()
    total_trades = len(trades)

    winner_trades = df[df['is_winner'] == True]['trade_id'].unique()
    loser_trades = df[df['is_winner'] == False]['trade_id'].unique()

    winner_count = len(winner_trades)
    loser_count = len(loser_trades)
    overall_win_rate = (winner_count / total_trades * 100) if total_trades > 0 else 0

    # Calculate progression paths
    winner_path = calculate_progression_path(df, 'WIN', True)
    loser_path = calculate_progression_path(df, 'LOSS', False)

    # Event summary
    event_summary = create_event_summary(df)

    # Delta summaries
    winner_deltas = create_delta_summary(df, True)
    loser_deltas = create_delta_summary(df, False)

    # Bar-by-bar progression
    bar_progression = calculate_bar_by_bar_progression(df)

    # Early warning signals
    early_warnings = calculate_early_warning_signals(df)
    best_warning = early_warnings[0] if early_warnings else None

    # Factor degradation analysis
    factor_degradation = analyze_factor_degradation(df)

    return IndicatorProgressionResult(
        total_trades=total_trades,
        winner_count=winner_count,
        loser_count=loser_count,
        overall_win_rate=overall_win_rate,
        winner_path=winner_path,
        loser_path=loser_path,
        event_summary=event_summary,
        winner_deltas=winner_deltas,
        loser_deltas=loser_deltas,
        early_warnings=early_warnings,
        best_warning=best_warning,
        factor_degradation=factor_degradation,
        bar_progression=bar_progression
    )


# =============================================================================
# STREAMLIT RENDERING FUNCTIONS
# =============================================================================

def render_progression_summary_cards(result: IndicatorProgressionResult):
    """Render summary cards for progression analysis."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Trades",
            value=f"{result.total_trades:,}"
        )

    with col2:
        st.metric(
            label="Winners",
            value=f"{result.winner_count:,}",
            delta=f"{result.overall_win_rate:.1f}%"
        )

    with col3:
        st.metric(
            label="Losers",
            value=f"{result.loser_count:,}"
        )

    with col4:
        if result.best_warning:
            st.metric(
                label="Best Warning Signal",
                value=f"{result.best_warning.indicator}",
                delta=f"+{result.best_warning.lift:.1f}pp lift"
            )
        else:
            st.metric(
                label="Best Warning Signal",
                value="N/A"
            )


def render_progression_path_chart(result: IndicatorProgressionResult):
    """Render line chart comparing winner vs loser progression paths."""
    import plotly.graph_objects as go

    fig = go.Figure()

    # Winner path
    if result.winner_path:
        wp = result.winner_path
        fig.add_trace(go.Scatter(
            x=['ENTRY', f'MFE\n({wp.avg_bars_to_peak:.0f} bars)'],
            y=[
                wp.entry_snapshot.avg_health_score,
                wp.peak_snapshot.avg_health_score
            ],
            mode='lines+markers+text',
            name=f'Winners (n={wp.trade_count})',
            line=dict(color='#26a69a', width=3),
            marker=dict(size=14),
            text=[
                f"{wp.entry_snapshot.avg_health_score:.1f}",
                f"{wp.peak_snapshot.avg_health_score:.1f}"
            ],
            textposition='top center'
        ))

    # Loser path
    if result.loser_path:
        lp = result.loser_path
        fig.add_trace(go.Scatter(
            x=['ENTRY', f'MAE\n({lp.avg_bars_to_peak:.0f} bars)'],
            y=[
                lp.entry_snapshot.avg_health_score,
                lp.peak_snapshot.avg_health_score
            ],
            mode='lines+markers+text',
            name=f'Losers (n={lp.trade_count})',
            line=dict(color='#ef5350', width=3),
            marker=dict(size=14),
            text=[
                f"{lp.entry_snapshot.avg_health_score:.1f}",
                f"{lp.peak_snapshot.avg_health_score:.1f}"
            ],
            textposition='bottom center'
        ))

    fig.update_layout(
        title="Health Score Progression: Entry to Peak",
        xaxis_title="Event",
        yaxis_title="Average Health Score (0-10)",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        yaxis=dict(range=[0, 10]),
        showlegend=True,
        legend=dict(orientation='h', y=-0.2),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_bar_by_bar_progression_chart(result: IndicatorProgressionResult):
    """Render line chart of bar-by-bar health score progression."""
    import plotly.graph_objects as go

    if result.bar_progression.empty:
        st.warning("Insufficient data for bar-by-bar analysis")
        return

    df = result.bar_progression

    fig = go.Figure()

    # Winner progression
    winners = df[df['outcome'] == 'WIN'].sort_values('bars_from_entry')
    if not winners.empty:
        fig.add_trace(go.Scatter(
            x=winners['bars_from_entry'],
            y=winners['avg_health_score'],
            mode='lines+markers',
            name='Winners',
            line=dict(color='#26a69a', width=2),
            marker=dict(size=6)
        ))

        # Add confidence band
        upper = winners['avg_health_score'] + winners['std_health_score']
        lower = winners['avg_health_score'] - winners['std_health_score']
        fig.add_trace(go.Scatter(
            x=pd.concat([winners['bars_from_entry'], winners['bars_from_entry'][::-1]]),
            y=pd.concat([upper, lower[::-1]]),
            fill='toself',
            fillcolor='rgba(38, 166, 154, 0.2)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Winner Std Dev',
            showlegend=False
        ))

    # Loser progression
    losers = df[df['outcome'] == 'LOSS'].sort_values('bars_from_entry')
    if not losers.empty:
        fig.add_trace(go.Scatter(
            x=losers['bars_from_entry'],
            y=losers['avg_health_score'],
            mode='lines+markers',
            name='Losers',
            line=dict(color='#ef5350', width=2),
            marker=dict(size=6)
        ))

        # Add confidence band
        upper = losers['avg_health_score'] + losers['std_health_score']
        lower = losers['avg_health_score'] - losers['std_health_score']
        fig.add_trace(go.Scatter(
            x=pd.concat([losers['bars_from_entry'], losers['bars_from_entry'][::-1]]),
            y=pd.concat([upper, lower[::-1]]),
            fill='toself',
            fillcolor='rgba(239, 83, 80, 0.2)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Loser Std Dev',
            showlegend=False
        ))

    fig.update_layout(
        title="Bar-by-Bar Health Score Progression",
        xaxis_title="Bars from Entry",
        yaxis_title="Average Health Score",
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        yaxis=dict(range=[0, 10]),
        showlegend=True,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_score_components_chart(result: IndicatorProgressionResult):
    """Render stacked bar chart of score components (structure, volume, price)."""
    import plotly.graph_objects as go

    if not result.winner_path or not result.loser_path:
        st.warning("Insufficient data for score component analysis")
        return

    categories = ['Winner Entry', 'Winner MFE', 'Loser Entry', 'Loser MAE']

    structure_scores = [
        result.winner_path.entry_snapshot.avg_structure_score,
        result.winner_path.peak_snapshot.avg_structure_score,
        result.loser_path.entry_snapshot.avg_structure_score,
        result.loser_path.peak_snapshot.avg_structure_score
    ]

    volume_scores = [
        result.winner_path.entry_snapshot.avg_volume_score,
        result.winner_path.peak_snapshot.avg_volume_score,
        result.loser_path.entry_snapshot.avg_volume_score,
        result.loser_path.peak_snapshot.avg_volume_score
    ]

    price_scores = [
        result.winner_path.entry_snapshot.avg_price_score,
        result.winner_path.peak_snapshot.avg_price_score,
        result.loser_path.entry_snapshot.avg_price_score,
        result.loser_path.peak_snapshot.avg_price_score
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Structure (0-4)',
        x=categories,
        y=structure_scores,
        marker_color='#7c3aed',
        text=[f"{s:.1f}" for s in structure_scores],
        textposition='inside'
    ))

    fig.add_trace(go.Bar(
        name='Volume (0-3)',
        x=categories,
        y=volume_scores,
        marker_color='#3b82f6',
        text=[f"{s:.1f}" for s in volume_scores],
        textposition='inside'
    ))

    fig.add_trace(go.Bar(
        name='Price (0-3)',
        x=categories,
        y=price_scores,
        marker_color='#10b981',
        text=[f"{s:.1f}" for s in price_scores],
        textposition='inside'
    ))

    fig.update_layout(
        title="Health Score Components by Event",
        xaxis_title="",
        yaxis_title="Score",
        barmode='stack',
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_delta_comparison_chart(result: IndicatorProgressionResult):
    """Render bar chart comparing entry-to-peak deltas for winners vs losers."""
    import plotly.graph_objects as go

    if result.winner_deltas is None or len(result.winner_deltas) == 0:
        st.warning("Insufficient data for winner delta comparison")
        return

    if result.loser_deltas is None or len(result.loser_deltas) == 0:
        st.warning("Insufficient data for loser delta comparison")
        return

    # Merge on indicator
    merged = result.winner_deltas.merge(
        result.loser_deltas,
        on='indicator',
        suffixes=('_win', '_loss')
    )

    if len(merged) == 0:
        st.warning("No common indicators for comparison")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Winners (Entry -> MFE)',
        x=merged['indicator'],
        y=merged['delta_win'],
        marker_color='#26a69a',
        text=[f"{d:+.2f}" for d in merged['delta_win']],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='Losers (Entry -> MAE)',
        x=merged['indicator'],
        y=merged['delta_loss'],
        marker_color='#ef5350',
        text=[f"{d:+.2f}" for d in merged['delta_loss']],
        textposition='outside'
    ))

    # Zero line
    fig.add_hline(y=0, line_color='#e0e0e0', line_width=1)

    fig.update_layout(
        title="Indicator Delta: Entry to Peak",
        xaxis_title="Indicator",
        yaxis_title="Change (Delta)",
        barmode='group',
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        xaxis_tickangle=-45,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_early_warning_table(result: IndicatorProgressionResult):
    """Render table of early warning signals."""
    if not result.early_warnings:
        st.info("No significant early warning signals identified")
        return

    data = [{
        'Indicator': w.indicator.replace('_', ' ').title(),
        'Threshold': f"<= {w.threshold}",
        'Window': f"{w.bars_window} bars",
        'Loser Hit%': f"{w.hit_rate_losers:.1f}%",
        'Winner Hit%': f"{w.hit_rate_winners:.1f}%",
        'Lift': f"+{w.lift:.1f}pp",
        'Predictive': f"{w.predictive_power:.2f}"
    } for w in result.early_warnings[:10]]  # Top 10

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_factor_degradation_table(result: IndicatorProgressionResult):
    """Render table of factor degradation analysis."""
    if not result.factor_degradation:
        st.info("No factor degradation data available")
        return

    data = [{
        'Factor': fd.factor_name,
        'Healthy @ Entry': f"{fd.healthy_at_entry_pct:.1f}%",
        'Healthy @ MAE': f"{fd.healthy_at_mae_pct:.1f}%",
        'Degradation': f"-{fd.degradation_rate:.1f}pp",
        'Flip Rate': f"{fd.flip_rate:.1f}%",
        'Early Flip (5 bars)': f"{fd.early_flip_rate:.1f}%"
    } for fd in result.factor_degradation]

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_event_summary_table(result: IndicatorProgressionResult):
    """Render detailed event summary table."""
    if result.event_summary is None or len(result.event_summary) == 0:
        st.info("No event summary data available")
        return

    df = result.event_summary.copy()

    # Format numeric columns
    for col in df.columns:
        if '_avg' in col or '_std' in col:
            df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_calc_007_section(df: pd.DataFrame) -> Optional[IndicatorProgressionResult]:
    """
    Main render function for CALC-007 section in Streamlit.

    Parameters:
        df: DataFrame from m5_trade_bars with outcomes joined

    Returns:
        IndicatorProgressionResult or None on error
    """
    st.subheader("CALC-007: Indicator Progression Analysis")
    st.markdown("*What changes between entry and outcome?*")

    try:
        result = analyze_indicator_progression(df)

        # Summary cards
        render_progression_summary_cards(result)

        st.divider()

        # Main visualizations in tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Progression Paths",
            "Bar-by-Bar Analysis",
            "Early Warnings",
            "Factor Degradation"
        ])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Health Score Progression")
                render_progression_path_chart(result)

            with col2:
                st.markdown("### Score Components")
                render_score_components_chart(result)

            st.markdown("### Indicator Deltas: Entry to Peak")
            render_delta_comparison_chart(result)

        with tab2:
            st.markdown("### Bar-by-Bar Health Score")
            st.markdown("*Average health score at each bar from entry*")
            render_bar_by_bar_progression_chart(result)

        with tab3:
            st.markdown("### Early Warning Signals")
            st.markdown("*Signals that predict trade failure before stop is hit*")
            render_early_warning_table(result)

            if result.best_warning:
                bw = result.best_warning
                st.success(
                    f"**Best Warning:** {bw.indicator.replace('_', ' ').title()} drop of {bw.threshold} within "
                    f"{bw.bars_window} bars catches {bw.hit_rate_losers:.0f}% of losers "
                    f"(only {bw.hit_rate_winners:.0f}% false positives)"
                )

        with tab4:
            st.markdown("### Factor Degradation Analysis")
            st.markdown("*How individual health factors change for losing trades*")
            render_factor_degradation_table(result)

        # Event summary (expandable)
        with st.expander("Detailed Event Summary", expanded=False):
            render_event_summary_table(result)

        # Key findings
        st.divider()
        st.markdown("### Key Findings")

        findings = []

        if result.winner_path and result.loser_path:
            hs_diff = result.winner_path.entry_snapshot.avg_health_score - result.loser_path.entry_snapshot.avg_health_score
            if abs(hs_diff) > 0.3:
                if hs_diff > 0:
                    findings.append(f"**Winners start with higher Health Score** (+{hs_diff:.1f} points at entry)")
                else:
                    findings.append(f"**Winners start with similar Health Score** ({hs_diff:+.1f} points at entry)")

            w_delta = result.winner_path.health_delta_to_peak
            l_delta = result.loser_path.health_delta_to_peak

            if w_delta > 0 and l_delta < 0:
                findings.append(f"**Divergent paths:** Winners improve ({w_delta:+.1f}), losers degrade ({l_delta:+.1f})")
            elif w_delta > l_delta:
                findings.append(f"**Winners improve more:** Winner delta ({w_delta:+.1f}) vs Loser delta ({l_delta:+.1f})")

            # Timing insight
            w_bars = result.winner_path.avg_bars_to_peak
            l_bars = result.loser_path.avg_bars_to_peak
            findings.append(f"**Timing:** Winners reach MFE in {w_bars:.0f} bars, losers hit MAE in {l_bars:.0f} bars")

        if result.best_warning:
            bw = result.best_warning
            findings.append(
                f"**Best Early Warning:** {bw.indicator.replace('_', ' ').title()} drop of {bw.threshold} within {bw.bars_window} bars "
                f"(catches {bw.hit_rate_losers:.0f}% of losers, {bw.hit_rate_winners:.0f}% false positive rate)"
            )

        if result.factor_degradation:
            worst = result.factor_degradation[0]
            findings.append(
                f"**Fastest Degrading Factor:** {worst.factor_name} "
                f"({worst.degradation_rate:.1f}pp drop from entry to MAE)"
            )

        if not findings:
            findings.append("Insufficient MFE/MAE event data for meaningful progression analysis")

        for finding in findings:
            st.markdown(f"- {finding}")

        # DOW AI Recommendations
        st.markdown("### DOW AI Recommendations")

        recommendations = []

        if result.best_warning:
            bw = result.best_warning
            recommendations.append(
                f"**Exit Signal:** Consider early exit if {bw.indicator.replace('_', ' ')} drops {abs(bw.threshold):.1f}+ within {bw.bars_window} bars"
            )

        if result.winner_path and result.loser_path:
            if result.winner_path.health_delta_to_peak > 0:
                recommendations.append("**Stay in Winners:** Health Score improving = trade working, let it run")
            if result.loser_path.health_delta_to_peak < -1:
                recommendations.append("**Cut Losers Early:** Rapid health degradation signals trade failure before stop")

        if not recommendations:
            recommendations.append("Need more MFE/MAE event data to generate recommendations")

        for rec in recommendations:
            st.markdown(f"- {rec}")

        return result

    except Exception as e:
        st.error(f"Error in CALC-007 analysis: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None
