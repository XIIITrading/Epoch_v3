"""
================================================================================
EPOCH TRADING SYSTEM - INDICATOR ANALYSIS
CALC-008: Rejection Dynamics Analysis
XIII Trading LLC
================================================================================

Analyzes whether rejection trades (EPCH02/04) require different
indicators than continuation trades (EPCH01/03).

Sub-analyses:
  8A: Time-to-MFE by model type
  8B: Health Score inversion test
  8C: Individual factor inversion
  8D: Exhaustion indicator discovery

WIN CONDITION (Stop-Based):
    Win = MFE reached (>=1R) before stop hit
    Loss = Stop hit before reaching 1R

    The is_winner flag must be pre-computed from stop_analysis table
    and merged into the data before calling these functions.
    Default stop type: Zone + 5% Buffer

Version: 1.1.0
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
from decimal import Decimal
import streamlit as st


def _convert_decimals(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Decimal columns to float for Arrow serialization."""
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(1)
            if len(sample) > 0 and isinstance(sample.iloc[0], Decimal):
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    return df

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import INDICATOR_ANALYSIS_CONFIG, MODEL_TYPES, get_model_type
from .factor_importance import FACTORS, wilson_ci


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TimeToMFEResult:
    """Results for 8A: Time-to-MFE analysis."""
    model_type: str
    total_trades: int
    median_minutes: float
    mean_minutes: float
    pct_within_5min: float
    pct_within_15min: float
    pct_within_30min: float
    distribution: pd.DataFrame  # [minutes_bucket, count, pct]


@dataclass
class InversionTestResult:
    """Results for 8B: Health Score inversion test."""
    model_type: str
    correlation: float
    correlation_pvalue: float
    strong_win_rate: float
    strong_trades: int
    critical_win_rate: float
    critical_trades: int
    is_inverted: bool  # True if CRITICAL > STRONG
    inversion_magnitude: float  # critical_rate - strong_rate


@dataclass
class FactorInversionResult:
    """Results for 8C: Individual factor inversion."""
    factor_key: str
    factor_name: str
    continuation_lift: float
    continuation_healthy_wr: float
    continuation_unhealthy_wr: float
    rejection_lift: float
    rejection_healthy_wr: float
    rejection_unhealthy_wr: float
    is_inverted: bool  # True if signs differ
    inversion_strength: str  # 'STRONG', 'MODERATE', 'WEAK', 'NONE'


@dataclass
class ExhaustionIndicator:
    """Results for 8D: Exhaustion indicator discovery."""
    indicator: str
    quintile: int  # 1-5 (1=lowest, 5=highest)
    quintile_label: str
    trades: int
    win_rate: float
    lift_vs_median: float
    is_extreme_better: bool


@dataclass
class RejectionDynamicsResult:
    """Container for all CALC-008 analysis results."""
    # 8A: Time-to-MFE
    continuation_time: TimeToMFEResult
    rejection_time: TimeToMFEResult
    time_comparison: pd.DataFrame

    # 8B: Health Score Inversion
    continuation_inversion: InversionTestResult
    rejection_inversion: InversionTestResult
    health_score_by_model: pd.DataFrame

    # 8C: Factor Inversion
    factor_inversions: List[FactorInversionResult]
    inverted_factors: List[str]
    non_inverted_factors: List[str]

    # 8D: Exhaustion Indicators
    exhaustion_analysis: pd.DataFrame
    candidate_exhaustion_indicators: List[ExhaustionIndicator]

    # Summary
    rejection_requires_different_scoring: bool
    recommended_inverted_factors: List[str]


# =============================================================================
# 8A: TIME-TO-MFE ANALYSIS
# =============================================================================

def analyze_time_to_mfe(
    df: pd.DataFrame,
    model_type: str
) -> TimeToMFEResult:
    """
    Analyze time-to-MFE distribution for a model type.

    Parameters:
        df: DataFrame with mfe_mae_potential data
        model_type: 'continuation' or 'rejection'

    Returns:
        TimeToMFEResult with distribution analysis
    """
    # Filter to model type
    if model_type == 'continuation':
        type_df = df[df['model'].isin(MODEL_TYPES['continuation'])]
    else:
        type_df = df[df['model'].isin(MODEL_TYPES['rejection'])]

    # Filter to trades with valid MFE time
    valid_df = type_df[type_df['mfe_potential_time'].notna()].copy()

    if len(valid_df) == 0:
        return TimeToMFEResult(
            model_type=model_type,
            total_trades=0,
            median_minutes=0,
            mean_minutes=0,
            pct_within_5min=0,
            pct_within_15min=0,
            pct_within_30min=0,
            distribution=pd.DataFrame()
        )

    # Calculate minutes to MFE
    def time_diff_minutes(row):
        try:
            entry = row['entry_time']
            mfe = row['mfe_potential_time']

            # Handle time objects
            if hasattr(entry, 'hour'):
                entry_mins = entry.hour * 60 + entry.minute + entry.second / 60
            elif hasattr(entry, 'total_seconds'):
                # timedelta from psycopg2
                entry_mins = entry.total_seconds() / 60
            else:
                return None

            if hasattr(mfe, 'hour'):
                mfe_mins = mfe.hour * 60 + mfe.minute + mfe.second / 60
            elif hasattr(mfe, 'total_seconds'):
                mfe_mins = mfe.total_seconds() / 60
            else:
                return None

            return max(0, mfe_mins - entry_mins)
        except:
            return None

    valid_df['minutes_to_mfe'] = valid_df.apply(time_diff_minutes, axis=1)
    valid_df = valid_df[valid_df['minutes_to_mfe'].notna()]

    if len(valid_df) == 0:
        return TimeToMFEResult(
            model_type=model_type,
            total_trades=0,
            median_minutes=0,
            mean_minutes=0,
            pct_within_5min=0,
            pct_within_15min=0,
            pct_within_30min=0,
            distribution=pd.DataFrame()
        )

    total = len(valid_df)

    # Calculate metrics
    median_mins = valid_df['minutes_to_mfe'].median()
    mean_mins = valid_df['minutes_to_mfe'].mean()
    pct_5 = (valid_df['minutes_to_mfe'] <= 5).sum() / total * 100
    pct_15 = (valid_df['minutes_to_mfe'] <= 15).sum() / total * 100
    pct_30 = (valid_df['minutes_to_mfe'] <= 30).sum() / total * 100

    # Create distribution buckets
    buckets = [0, 5, 10, 15, 20, 30, 45, 60, 120, 999]
    labels = ['0-5', '5-10', '10-15', '15-20', '20-30', '30-45', '45-60', '60-120', '120+']
    valid_df['time_bucket'] = pd.cut(valid_df['minutes_to_mfe'], bins=buckets, labels=labels)

    dist = valid_df.groupby('time_bucket', observed=True).size().reset_index(name='count')
    dist['pct'] = dist['count'] / total * 100

    return TimeToMFEResult(
        model_type=model_type,
        total_trades=total,
        median_minutes=round(median_mins, 1),
        mean_minutes=round(mean_mins, 1),
        pct_within_5min=round(pct_5, 1),
        pct_within_15min=round(pct_15, 1),
        pct_within_30min=round(pct_30, 1),
        distribution=dist
    )


# =============================================================================
# 8B: HEALTH SCORE INVERSION TEST
# =============================================================================

def test_health_score_inversion(
    df: pd.DataFrame,
    model_type: str
) -> InversionTestResult:
    """
    Test if Health Score is inverted for a model type.

    Parameters:
        df: DataFrame with entry_indicators and outcomes
        model_type: 'continuation' or 'rejection'

    Returns:
        InversionTestResult with inversion analysis
    """
    # Filter to model type
    if model_type == 'continuation':
        type_df = df[df['model'].isin(MODEL_TYPES['continuation'])]
    else:
        type_df = df[df['model'].isin(MODEL_TYPES['rejection'])]

    # Filter out trades without stop analysis data (is_winner = None)
    valid_df = type_df[type_df['health_score'].notna() & type_df['is_winner'].notna()].copy()

    if len(valid_df) == 0:
        return InversionTestResult(
            model_type=model_type,
            correlation=0,
            correlation_pvalue=1,
            strong_win_rate=0,
            strong_trades=0,
            critical_win_rate=0,
            critical_trades=0,
            is_inverted=False,
            inversion_magnitude=0
        )

    # Calculate correlation
    try:
        corr, pvalue = stats.pearsonr(
            valid_df['health_score'].astype(float),
            valid_df['is_winner'].astype(int)
        )
    except:
        corr, pvalue = 0, 1

    # Calculate bucket win rates
    buckets = INDICATOR_ANALYSIS_CONFIG['health_buckets']

    strong_df = valid_df[
        (valid_df['health_score'] >= buckets['STRONG'][0]) &
        (valid_df['health_score'] <= buckets['STRONG'][1])
    ]
    critical_df = valid_df[
        (valid_df['health_score'] >= buckets['CRITICAL'][0]) &
        (valid_df['health_score'] <= buckets['CRITICAL'][1])
    ]

    strong_trades = len(strong_df)
    critical_trades = len(critical_df)

    strong_wr = (strong_df['is_winner'].sum() / strong_trades * 100) if strong_trades > 0 else 0
    critical_wr = (critical_df['is_winner'].sum() / critical_trades * 100) if critical_trades > 0 else 0

    is_inverted = critical_wr > strong_wr
    inversion_mag = critical_wr - strong_wr

    return InversionTestResult(
        model_type=model_type,
        correlation=round(corr, 3),
        correlation_pvalue=round(pvalue, 4),
        strong_win_rate=round(strong_wr, 1),
        strong_trades=strong_trades,
        critical_win_rate=round(critical_wr, 1),
        critical_trades=critical_trades,
        is_inverted=is_inverted,
        inversion_magnitude=round(inversion_mag, 1)
    )


# =============================================================================
# 8C: FACTOR INVERSION ANALYSIS
# =============================================================================

def analyze_factor_inversion(
    df: pd.DataFrame,
    factor_key: str
) -> Optional[FactorInversionResult]:
    """
    Analyze if a single factor is inverted between model types.

    Parameters:
        df: DataFrame with entry_indicators and outcomes
        factor_key: Column name for the factor (e.g., 'cvd_slope_healthy')

    Returns:
        FactorInversionResult or None
    """
    if factor_key not in df.columns:
        return None

    factor_info = FACTORS.get(factor_key)
    if not factor_info:
        return None

    # Filter out trades without stop analysis data (is_winner = None)
    valid_df = df[df[factor_key].notna() & df['is_winner'].notna()].copy()

    def calc_lift_and_rates(subset):
        healthy = subset[subset[factor_key] == True]
        unhealthy = subset[subset[factor_key] == False]

        if len(healthy) < 10 or len(unhealthy) < 10:
            return 0, 0, 0

        h_wr = healthy['is_winner'].sum() / len(healthy) * 100
        u_wr = unhealthy['is_winner'].sum() / len(unhealthy) * 100

        return h_wr - u_wr, h_wr, u_wr

    # Calculate lift for each model type
    cont_df = valid_df[valid_df['model'].isin(MODEL_TYPES['continuation'])]
    rej_df = valid_df[valid_df['model'].isin(MODEL_TYPES['rejection'])]

    # Calculate lift for each model type (allow smaller samples)
    cont_lift, cont_h_wr, cont_u_wr = calc_lift_and_rates(cont_df) if len(cont_df) > 0 else (0, 0, 0)
    rej_lift, rej_h_wr, rej_u_wr = calc_lift_and_rates(rej_df) if len(rej_df) > 0 else (0, 0, 0)

    # Determine if inverted
    is_inverted = (cont_lift > 0 and rej_lift < 0) or (cont_lift < 0 and rej_lift > 0)

    # Classify inversion strength
    if is_inverted:
        diff = abs(cont_lift - rej_lift)
        if diff > 15:
            strength = 'STRONG'
        elif diff > 8:
            strength = 'MODERATE'
        elif diff > 3:
            strength = 'WEAK'
        else:
            strength = 'NONE'
            is_inverted = False
    else:
        strength = 'NONE'

    return FactorInversionResult(
        factor_key=factor_key,
        factor_name=factor_info['name'],
        continuation_lift=round(cont_lift, 1),
        continuation_healthy_wr=round(cont_h_wr, 1),
        continuation_unhealthy_wr=round(cont_u_wr, 1),
        rejection_lift=round(rej_lift, 1),
        rejection_healthy_wr=round(rej_h_wr, 1),
        rejection_unhealthy_wr=round(rej_u_wr, 1),
        is_inverted=is_inverted,
        inversion_strength=strength
    )


# =============================================================================
# 8D: EXHAUSTION INDICATOR DISCOVERY
# =============================================================================

def discover_exhaustion_indicators(
    df: pd.DataFrame,
    indicator: str
) -> List[ExhaustionIndicator]:
    """
    Analyze an indicator by quintiles for rejection trades.

    Parameters:
        df: DataFrame with entry_indicators and outcomes
        indicator: Raw indicator column name (e.g., 'cvd_slope')

    Returns:
        List of ExhaustionIndicator for each quintile
    """
    # Filter to rejection models only
    rej_df = df[df['model'].isin(MODEL_TYPES['rejection'])].copy()

    if indicator not in rej_df.columns or len(rej_df) == 0:
        return []

    # Filter out trades without stop analysis data (is_winner = None)
    valid_df = rej_df[rej_df[indicator].notna() & rej_df['is_winner'].notna()].copy()

    if len(valid_df) < 5:
        return []

    # Create quintiles
    try:
        valid_df['quintile'] = pd.qcut(
            valid_df[indicator],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        )
    except:
        return []

    # Calculate win rate by quintile
    results = []
    median_wr = valid_df['is_winner'].mean() * 100

    quintile_labels = {
        1: 'Lowest (Q1)',
        2: 'Low (Q2)',
        3: 'Middle (Q3)',
        4: 'High (Q4)',
        5: 'Highest (Q5)'
    }

    for q in range(1, 6):
        q_df = valid_df[valid_df['quintile'] == q]
        if len(q_df) < 5:
            continue

        wr = q_df['is_winner'].sum() / len(q_df) * 100
        lift = wr - median_wr

        results.append(ExhaustionIndicator(
            indicator=indicator,
            quintile=q,
            quintile_label=quintile_labels[q],
            trades=len(q_df),
            win_rate=round(wr, 1),
            lift_vs_median=round(lift, 1),
            is_extreme_better=(q in [1, 5] and lift > 5)
        ))

    return results


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_rejection_dynamics(
    entry_df: pd.DataFrame,
    mfe_mae_df: pd.DataFrame
) -> RejectionDynamicsResult:
    """
    Main analysis function for CALC-008.

    Parameters:
        entry_df: DataFrame from entry_indicators with outcomes
        mfe_mae_df: DataFrame from mfe_mae_potential

    Returns:
        RejectionDynamicsResult with all analysis outputs
    """
    # 8A: Time-to-MFE
    cont_time = analyze_time_to_mfe(mfe_mae_df, 'continuation')
    rej_time = analyze_time_to_mfe(mfe_mae_df, 'rejection')

    time_comparison = pd.DataFrame([
        {
            'Model Type': 'Continuation',
            'Trades': cont_time.total_trades,
            'Median Min': cont_time.median_minutes,
            'Mean Min': cont_time.mean_minutes,
            '<=5min': f"{cont_time.pct_within_5min:.1f}%",
            '<=15min': f"{cont_time.pct_within_15min:.1f}%",
            '<=30min': f"{cont_time.pct_within_30min:.1f}%"
        },
        {
            'Model Type': 'Rejection',
            'Trades': rej_time.total_trades,
            'Median Min': rej_time.median_minutes,
            'Mean Min': rej_time.mean_minutes,
            '<=5min': f"{rej_time.pct_within_5min:.1f}%",
            '<=15min': f"{rej_time.pct_within_15min:.1f}%",
            '<=30min': f"{rej_time.pct_within_30min:.1f}%"
        }
    ])

    # 8B: Health Score Inversion
    cont_inversion = test_health_score_inversion(entry_df, 'continuation')
    rej_inversion = test_health_score_inversion(entry_df, 'rejection')

    # Create health score by model breakdown
    # Filter out trades without stop analysis data
    entry_df_valid = entry_df[entry_df['is_winner'].notna()]
    hs_data = []
    for model in entry_df_valid['model'].dropna().unique():
        model_df = entry_df_valid[entry_df_valid['model'] == model]
        for bucket_name, (low, high) in INDICATOR_ANALYSIS_CONFIG['health_buckets'].items():
            bucket_df = model_df[(model_df['health_score'] >= low) & (model_df['health_score'] <= high)]
            if len(bucket_df) > 0:
                wr = bucket_df['is_winner'].sum() / len(bucket_df) * 100
                hs_data.append({
                    'model': model,
                    'model_type': get_model_type(model),
                    'bucket': bucket_name,
                    'trades': len(bucket_df),
                    'win_rate': round(wr, 1)
                })

    health_score_by_model = pd.DataFrame(hs_data)

    # 8C: Factor Inversion
    factor_inversions = []
    for factor_key in FACTORS.keys():
        result = analyze_factor_inversion(entry_df, factor_key)
        if result:
            factor_inversions.append(result)

    inverted = [f.factor_name for f in factor_inversions if f.is_inverted]
    non_inverted = [f.factor_name for f in factor_inversions if not f.is_inverted]

    # 8D: Exhaustion Indicators
    exhaustion_results = []
    for indicator in ['cvd_slope', 'vol_delta', 'vol_roc', 'sma_spread']:
        results = discover_exhaustion_indicators(entry_df, indicator)
        exhaustion_results.extend(results)

    exhaustion_df = pd.DataFrame([{
        'Indicator': e.indicator,
        'Quintile': e.quintile_label,
        'Trades': e.trades,
        'Win Rate': f"{e.win_rate:.1f}%",
        'Lift': f"{e.lift_vs_median:+.1f}pp",
        'Extreme Better': e.is_extreme_better
    } for e in exhaustion_results]) if exhaustion_results else pd.DataFrame()

    candidate_exhaustion = [e for e in exhaustion_results if e.is_extreme_better]

    # Summary determination
    rejection_different = (
        rej_inversion.is_inverted or
        len(inverted) >= 2 or
        (rej_time.pct_within_5min - cont_time.pct_within_5min) > 10
    )

    return RejectionDynamicsResult(
        continuation_time=cont_time,
        rejection_time=rej_time,
        time_comparison=time_comparison,
        continuation_inversion=cont_inversion,
        rejection_inversion=rej_inversion,
        health_score_by_model=health_score_by_model,
        factor_inversions=factor_inversions,
        inverted_factors=inverted,
        non_inverted_factors=non_inverted,
        exhaustion_analysis=exhaustion_df,
        candidate_exhaustion_indicators=candidate_exhaustion,
        rejection_requires_different_scoring=rejection_different,
        recommended_inverted_factors=inverted
    )


# =============================================================================
# STREAMLIT RENDERING FUNCTIONS
# =============================================================================

def render_time_to_mfe_comparison(result: RejectionDynamicsResult):
    """Render time-to-MFE comparison charts."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st.markdown("### 8A: Time-to-MFE Analysis")
    st.markdown("*Do rejection trades reach MFE faster?*")

    # Summary table
    st.dataframe(_convert_decimals(result.time_comparison.copy()), use_container_width=True, hide_index=True)

    # Key insight
    cont = result.continuation_time
    rej = result.rejection_time

    if cont.total_trades > 0 and rej.total_trades > 0:
        if rej.median_minutes < cont.median_minutes:
            diff = cont.median_minutes - rej.median_minutes
            st.success(f"Rejection trades reach MFE **{diff:.1f} minutes faster** on median")
        elif rej.median_minutes > cont.median_minutes:
            diff = rej.median_minutes - cont.median_minutes
            st.info(f"Continuation trades reach MFE **{diff:.1f} minutes faster** on median")
        else:
            st.info("Both model types reach MFE at similar times")

    # Histogram comparison
    if not cont.distribution.empty or not rej.distribution.empty:
        fig = make_subplots(rows=1, cols=2, subplot_titles=['Continuation', 'Rejection'])

        if not cont.distribution.empty:
            fig.add_trace(
                go.Bar(
                    x=cont.distribution['time_bucket'].astype(str),
                    y=cont.distribution['pct'],
                    marker_color='#7c3aed',
                    name='Continuation',
                    text=[f"{p:.1f}%" for p in cont.distribution['pct']],
                    textposition='outside'
                ),
                row=1, col=1
            )

        if not rej.distribution.empty:
            fig.add_trace(
                go.Bar(
                    x=rej.distribution['time_bucket'].astype(str),
                    y=rej.distribution['pct'],
                    marker_color='#f59e0b',
                    name='Rejection',
                    text=[f"{p:.1f}%" for p in rej.distribution['pct']],
                    textposition='outside'
                ),
                row=1, col=2
            )

        fig.update_layout(
            title="Time-to-MFE Distribution by Model Type",
            template="plotly_dark",
            paper_bgcolor="#16213e",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#e0e0e0"),
            showlegend=False,
            height=350
        )

        fig.update_xaxes(title_text="Minutes to MFE", row=1, col=1)
        fig.update_xaxes(title_text="Minutes to MFE", row=1, col=2)
        fig.update_yaxes(title_text="% of Trades", row=1, col=1)

        st.plotly_chart(fig, use_container_width=True)


def render_health_score_inversion(result: RejectionDynamicsResult):
    """Render health score inversion analysis."""
    import plotly.express as px

    st.markdown("### 8B: Health Score Inversion Test")
    st.markdown("*Is Health Score negatively correlated for rejection trades?*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Continuation Models (EPCH01/03)**")
        ci = result.continuation_inversion

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.metric("Correlation", f"{ci.correlation:+.3f}")
            st.metric("STRONG Win Rate", f"{ci.strong_win_rate:.1f}%",
                     help=f"n={ci.strong_trades}")
        with mcol2:
            st.metric("P-Value", f"{ci.correlation_pvalue:.4f}")
            st.metric("CRITICAL Win Rate", f"{ci.critical_win_rate:.1f}%",
                     help=f"n={ci.critical_trades}")

        if ci.is_inverted:
            st.error(f"INVERTED: CRITICAL beats STRONG by {ci.inversion_magnitude:+.1f}pp")
        else:
            st.success(f"Normal: STRONG beats CRITICAL by {-ci.inversion_magnitude:+.1f}pp")

    with col2:
        st.markdown("**Rejection Models (EPCH02/04)**")
        ri = result.rejection_inversion

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.metric("Correlation", f"{ri.correlation:+.3f}")
            st.metric("STRONG Win Rate", f"{ri.strong_win_rate:.1f}%",
                     help=f"n={ri.strong_trades}")
        with mcol2:
            st.metric("P-Value", f"{ri.correlation_pvalue:.4f}")
            st.metric("CRITICAL Win Rate", f"{ri.critical_win_rate:.1f}%",
                     help=f"n={ri.critical_trades}")

        if ri.is_inverted:
            st.error(f"INVERTED: CRITICAL beats STRONG by {ri.inversion_magnitude:+.1f}pp")
        else:
            st.success(f"Normal: STRONG beats CRITICAL by {-ri.inversion_magnitude:+.1f}pp")

    # Heatmap
    if not result.health_score_by_model.empty:
        st.markdown("#### Win Rate Heatmap by Model and Health Bucket")

        pivot = result.health_score_by_model.pivot(
            index='model',
            columns='bucket',
            values='win_rate'
        )

        bucket_order = ['CRITICAL', 'WEAK', 'MODERATE', 'STRONG']
        pivot = pivot.reindex(columns=[b for b in bucket_order if b in pivot.columns])

        fig = px.imshow(
            pivot,
            labels=dict(color="Win Rate %"),
            color_continuous_scale='RdYlGn',
            text_auto='.1f',
            aspect='auto'
        )

        fig.update_layout(
            title="Win Rate by Model and Health Bucket",
            template="plotly_dark",
            paper_bgcolor="#16213e",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#e0e0e0"),
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)


def render_factor_inversion_table(result: RejectionDynamicsResult):
    """Render factor inversion analysis."""
    import plotly.graph_objects as go

    st.markdown("### 8C: Factor Inversion Analysis")
    st.markdown("*Which factors have inverted meaning for rejection trades?*")

    if not result.factor_inversions:
        st.warning("Insufficient data for factor inversion analysis")
        return

    # Create summary table
    data = [{
        'Factor': fi.factor_name,
        'Cont. Healthy': f"{fi.continuation_healthy_wr:.1f}%",
        'Cont. Unhealthy': f"{fi.continuation_unhealthy_wr:.1f}%",
        'Cont. Lift': f"{fi.continuation_lift:+.1f}pp",
        'Rej. Healthy': f"{fi.rejection_healthy_wr:.1f}%",
        'Rej. Unhealthy': f"{fi.rejection_unhealthy_wr:.1f}%",
        'Rej. Lift': f"{fi.rejection_lift:+.1f}pp",
        'Inverted': 'YES' if fi.is_inverted else 'No',
        'Strength': fi.inversion_strength
    } for fi in result.factor_inversions]

    df = _convert_decimals(pd.DataFrame(data))
    st.dataframe(df, use_container_width=True, hide_index=True)

    if result.inverted_factors:
        st.warning(f"**Inverted Factors:** {', '.join(result.inverted_factors)}")
        st.info("These factors should use OPPOSITE logic for rejection trades in DOW AI scoring.")
    else:
        st.success("No factors show significant inversion between model types.")

    # Visual comparison chart
    fig = go.Figure()

    factors = [fi.factor_name for fi in result.factor_inversions]
    cont_lifts = [fi.continuation_lift for fi in result.factor_inversions]
    rej_lifts = [fi.rejection_lift for fi in result.factor_inversions]

    fig.add_trace(go.Bar(
        name='Continuation Lift',
        x=factors,
        y=cont_lifts,
        marker_color='#7c3aed',
        text=[f"{l:+.1f}" for l in cont_lifts],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='Rejection Lift',
        x=factors,
        y=rej_lifts,
        marker_color='#f59e0b',
        text=[f"{l:+.1f}" for l in rej_lifts],
        textposition='outside'
    ))

    fig.add_hline(y=0, line_color='#e0e0e0', line_width=1)

    fig.update_layout(
        title="Factor Lift: Continuation vs Rejection",
        xaxis_title="Factor",
        yaxis_title="Lift (pp)",
        barmode='group',
        template="plotly_dark",
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        height=400,
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)


def render_exhaustion_analysis(result: RejectionDynamicsResult):
    """Render exhaustion indicator discovery."""
    st.markdown("### 8D: Exhaustion Indicator Discovery")
    st.markdown("*Do extreme indicator values predict rejection success?*")

    if result.exhaustion_analysis.empty:
        st.info("Insufficient rejection trade data for exhaustion analysis")
        return

    st.dataframe(_convert_decimals(result.exhaustion_analysis.copy()), use_container_width=True, hide_index=True)

    if result.candidate_exhaustion_indicators:
        st.success("**Candidate Exhaustion Indicators Found:**")
        for e in result.candidate_exhaustion_indicators:
            st.markdown(f"- **{e.indicator}** {e.quintile_label}: {e.win_rate:.1f}% win rate ({e.lift_vs_median:+.1f}pp vs median)")
    else:
        st.info("No strong exhaustion patterns detected in rejection trades.")


def render_calc_008_section(entry_df: pd.DataFrame, mfe_mae_df: pd.DataFrame) -> Optional[RejectionDynamicsResult]:
    """
    Main render function for CALC-008 section in Streamlit.

    Parameters:
        entry_df: DataFrame from entry_indicators with outcomes
        mfe_mae_df: DataFrame from mfe_mae_potential

    Returns:
        RejectionDynamicsResult or None on error
    """
    st.subheader("CALC-008: Rejection Dynamics Analysis")
    st.markdown("*Do rejection trades require different indicators?*")

    # Show data stats
    cont_count = len(entry_df[entry_df['model'].isin(MODEL_TYPES['continuation'])])
    rej_count = len(entry_df[entry_df['model'].isin(MODEL_TYPES['rejection'])])
    st.caption(f"Analyzing {cont_count:,} continuation trades vs {rej_count:,} rejection trades")

    if cont_count < 30 or rej_count < 30:
        st.warning(f"Low sample size - results may not be statistically significant. Recommend 30+ trades per type.")

    try:
        result = analyze_rejection_dynamics(entry_df, mfe_mae_df)

        # 8A: Time-to-MFE
        render_time_to_mfe_comparison(result)

        st.divider()

        # 8B: Health Score Inversion
        render_health_score_inversion(result)

        st.divider()

        # 8C: Factor Inversion
        render_factor_inversion_table(result)

        st.divider()

        # 8D: Exhaustion Indicators
        render_exhaustion_analysis(result)

        # Summary Verdict
        st.divider()
        st.markdown("### CALC-008 Verdict")

        if result.rejection_requires_different_scoring:
            st.error("**REJECTION TRADES MAY REQUIRE DIFFERENT SCORING**")

            reasons = []
            if result.rejection_inversion.is_inverted:
                reasons.append("Health Score is inverted for rejection trades")
            if len(result.inverted_factors) >= 2:
                reasons.append(f"{len(result.inverted_factors)} factors show inversion")
            if (result.rejection_time.pct_within_5min - result.continuation_time.pct_within_5min) > 10:
                reasons.append("Rejection trades reach MFE significantly faster")

            for reason in reasons:
                st.markdown(f"- {reason}")

            if result.inverted_factors:
                st.markdown(f"**Factors to invert for rejection:** {', '.join(result.inverted_factors)}")

            st.info("Consider building a separate 'Exhaustion Score' for EPCH02/04 models.")
        else:
            st.success("**Current scoring system appears valid for both model types**")
            st.markdown("No significant inversion detected. Continue using unified Health Score.")

        return result

    except Exception as e:
        st.error(f"Error in CALC-008 analysis: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None
