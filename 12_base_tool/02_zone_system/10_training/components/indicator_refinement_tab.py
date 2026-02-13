"""
Epoch Trading System - Indicator Refinement Tab Component
Displays Continuation and Rejection scores for trade qualification.

Based on Epoch Indicator Model Specification v1.0:
    - CONTINUATION (EPCH01/03): With-trend trades, scored 0-10
    - REJECTION (EPCH02/04): Counter-trend/exhaustion, scored 0-11

Version: 1.0.0
"""

import streamlit as st
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics
from data.supabase_client import SupabaseClient


# =============================================================================
# SCORE LABEL THRESHOLDS
# =============================================================================

CONTINUATION_THRESHOLDS = {
    'STRONG': (8, 10),
    'GOOD': (6, 7),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

REJECTION_THRESHOLDS = {
    'STRONG': (9, 11),
    'GOOD': (6, 8),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

# Trade type by model
CONTINUATION_MODELS = ['EPCH1', 'EPCH3', 'EPCH01', 'EPCH03']
REJECTION_MODELS = ['EPCH2', 'EPCH4', 'EPCH02', 'EPCH04']


# =============================================================================
# COLOR HELPERS
# =============================================================================

def get_score_color(score: Optional[int], max_score: int) -> str:
    """Get color for a score based on percentage of max."""
    if score is None:
        return "#888888"
    pct = score / max_score
    if pct >= 0.8:
        return "#00C853"  # Green
    elif pct >= 0.6:
        return "#8BC34A"  # Light green
    elif pct >= 0.4:
        return "#FFC107"  # Yellow
    elif pct >= 0.2:
        return "#FF9800"  # Orange
    else:
        return "#FF1744"  # Red


def get_label_color(label: Optional[str]) -> str:
    """Get color for a label."""
    if not label:
        return "#888888"
    label = label.upper()
    if label == 'STRONG':
        return "#00C853"
    elif label == 'GOOD':
        return "#8BC34A"
    elif label == 'WEAK':
        return "#FF9800"
    elif label == 'AVOID':
        return "#FF1744"
    return "#888888"


def get_bool_color(value: Optional[bool], positive_is_good: bool = True) -> str:
    """Get color for a boolean value."""
    if value is None:
        return "#888888"
    if positive_is_good:
        return "#00C853" if value else "#FF1744"
    else:
        return "#FF1744" if value else "#00C853"


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_indicator_refinement_tab(
    trade: TradeWithMetrics,
    supabase: SupabaseClient
):
    """
    Render the Indicator Refinement tab content.

    Displays Continuation and Rejection scores with all component indicators.

    Args:
        trade: TradeWithMetrics being reviewed
        supabase: Database client for fetching refinement data
    """
    st.markdown("### Indicator Refinement Analysis")

    # Fetch refinement data
    refinement = supabase.fetch_indicator_refinement(trade.trade_id)

    if not refinement:
        st.info("No indicator refinement data available for this trade. "
                "Run the indicator_refinement populator to generate scores.")
        return

    # Determine trade type
    trade_type = refinement.get('trade_type', 'UNKNOWN')
    is_continuation = trade_type == 'CONTINUATION'

    # Header with trade type and primary score
    _render_score_header(refinement, is_continuation)

    # Continuation indicators section
    st.markdown("---")
    _render_continuation_section(refinement, is_continuation)

    # Rejection indicators section
    st.markdown("---")
    _render_rejection_section(refinement, not is_continuation)

    # Monte AI prompt section
    st.markdown("---")
    _render_monte_prompt_section(trade, refinement)


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def _render_score_header(refinement: Dict[str, Any], is_continuation: bool):
    """Render the score header with composite scores."""
    trade_type = refinement.get('trade_type', 'UNKNOWN')
    cont_score = refinement.get('continuation_score', 0)
    cont_label = refinement.get('continuation_label', 'UNKNOWN')
    rej_score = refinement.get('rejection_score', 0)
    rej_label = refinement.get('rejection_label', 'UNKNOWN')

    # Model and trade type
    model = refinement.get('model', 'N/A')
    direction = refinement.get('direction', 'N/A')

    col1, col2, col3 = st.columns(3)

    with col1:
        # Trade classification
        type_color = "#4CAF50" if is_continuation else "#FF9800"
        st.markdown(
            f"**Trade Type:** <span style='color:{type_color};font-weight:bold'>{trade_type}</span> ({model})",
            unsafe_allow_html=True
        )
        st.caption(f"Direction: {direction}")

    with col2:
        # Continuation score
        cont_color = get_score_color(cont_score, 10)
        label_color = get_label_color(cont_label)
        highlight = "border:2px solid #4CAF50;border-radius:8px;padding:8px;" if is_continuation else ""
        st.markdown(
            f"<div style='{highlight}'>"
            f"<span style='color:#888;font-size:12px;'>Continuation Score</span><br/>"
            f"<span style='color:{cont_color};font-size:28px;font-weight:bold;'>{cont_score}/10</span> "
            f"<span style='color:{label_color};font-size:14px;'>({cont_label})</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col3:
        # Rejection score
        rej_color = get_score_color(rej_score, 11)
        label_color = get_label_color(rej_label)
        highlight = "border:2px solid #FF9800;border-radius:8px;padding:8px;" if not is_continuation else ""
        st.markdown(
            f"<div style='{highlight}'>"
            f"<span style='color:#888;font-size:12px;'>Rejection Score</span><br/>"
            f"<span style='color:{rej_color};font-size:28px;font-weight:bold;'>{rej_score}/11</span> "
            f"<span style='color:{label_color};font-size:14px;'>({rej_label})</span>"
            f"</div>",
            unsafe_allow_html=True
        )


def _render_continuation_section(refinement: Dict[str, Any], is_primary: bool):
    """Render continuation indicators (CONT-01 to CONT-04)."""
    header_style = "color:#4CAF50;" if is_primary else "color:#666;"
    st.markdown(f"<h4 style='{header_style}'>Continuation Indicators (0-10 pts)</h4>", unsafe_allow_html=True)

    # Row 1: CONT-01 MTF Alignment (0-4) and CONT-02 SMA Momentum (0-2)
    col1, col2 = st.columns(2)

    with col1:
        _render_mtf_alignment(refinement)

    with col2:
        _render_sma_momentum(refinement)

    # Row 2: CONT-03 Volume Thrust (0-2) and CONT-04 Pullback Quality (0-2)
    col3, col4 = st.columns(2)

    with col3:
        _render_volume_thrust(refinement)

    with col4:
        _render_pullback_quality(refinement)


def _render_rejection_section(refinement: Dict[str, Any], is_primary: bool):
    """Render rejection indicators (REJ-01 to REJ-05)."""
    header_style = "color:#FF9800;" if is_primary else "color:#666;"
    st.markdown(f"<h4 style='{header_style}'>Rejection Indicators (0-11 pts)</h4>", unsafe_allow_html=True)

    # Row 1: REJ-01 Structure Divergence (0-2) and REJ-02 SMA Exhaustion (0-3)
    col1, col2 = st.columns(2)

    with col1:
        _render_structure_divergence(refinement)

    with col2:
        _render_sma_exhaustion(refinement)

    # Row 2: REJ-03 Delta Absorption (0-2) and REJ-04 Volume Climax (0-2)
    col3, col4 = st.columns(2)

    with col3:
        _render_delta_absorption(refinement)

    with col4:
        _render_volume_climax(refinement)

    # Row 3: REJ-05 CVD Extreme (0-2)
    col5, col6 = st.columns(2)

    with col5:
        _render_cvd_extreme(refinement)


# =============================================================================
# CONTINUATION INDICATOR RENDERERS
# =============================================================================

def _render_mtf_alignment(refinement: Dict):
    """CONT-01: Multi-Timeframe Alignment (0-4 pts)."""
    score = refinement.get('mtf_align_score', 0)
    color = get_score_color(score, 4)

    st.markdown(f"**CONT-01: MTF Alignment** <span style='color:{color}'>{score}/4</span>", unsafe_allow_html=True)

    h4 = refinement.get('mtf_h4_aligned')
    h1 = refinement.get('mtf_h1_aligned')
    m15 = refinement.get('mtf_m15_aligned')
    m5 = refinement.get('mtf_m5_aligned')

    # Display alignment icons
    def align_icon(aligned):
        if aligned is None:
            return "⬜"
        return "✅" if aligned else "❌"

    st.markdown(
        f"H4: {align_icon(h4)} | H1: {align_icon(h1)} | M15: {align_icon(m15)} | M5: {align_icon(m5)}",
        unsafe_allow_html=True
    )


def _render_sma_momentum(refinement: Dict):
    """CONT-02: SMA Momentum (0-2 pts)."""
    score = refinement.get('sma_mom_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**CONT-02: SMA Momentum** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    spread = refinement.get('sma_spread')
    spread_pct = refinement.get('sma_spread_pct')
    spread_roc = refinement.get('sma_spread_roc')
    aligned = refinement.get('sma_spread_aligned')
    expanding = refinement.get('sma_spread_expanding')

    # Format values
    spread_str = f"{spread:.4f}" if spread is not None else "-"
    spread_pct_str = f"{spread_pct:.3f}%" if spread_pct is not None else "-"
    roc_str = f"{spread_roc:+.1f}%" if spread_roc is not None else "-"

    aligned_icon = "✅" if aligned else "❌" if aligned is not None else "⬜"
    expand_icon = "✅" if expanding else "❌" if expanding is not None else "⬜"

    st.markdown(f"Spread: {spread_str} ({spread_pct_str})")
    st.markdown(f"ROC: {roc_str} | Aligned: {aligned_icon} | Expanding: {expand_icon}")


def _render_volume_thrust(refinement: Dict):
    """CONT-03: Volume Thrust (0-2 pts)."""
    score = refinement.get('vol_thrust_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**CONT-03: Volume Thrust** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    vol_roc = refinement.get('vol_roc')
    vol_delta_5 = refinement.get('vol_delta_5')
    roc_strong = refinement.get('vol_roc_strong')
    delta_aligned = refinement.get('vol_delta_aligned')

    roc_str = f"{vol_roc:+.1f}%" if vol_roc is not None else "-"
    delta_str = f"{vol_delta_5:+.0f}" if vol_delta_5 is not None else "-"
    strong_icon = "✅" if roc_strong else "❌" if roc_strong is not None else "⬜"
    aligned_icon = "✅" if delta_aligned else "❌" if delta_aligned is not None else "⬜"

    st.markdown(f"Vol ROC: {roc_str} (Strong: {strong_icon})")
    st.markdown(f"Delta 5-bar: {delta_str} (Aligned: {aligned_icon})")


def _render_pullback_quality(refinement: Dict):
    """CONT-04: Pullback Quality (0-2 pts)."""
    score = refinement.get('pullback_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**CONT-04: Pullback Quality** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    in_pullback = refinement.get('in_pullback')
    delta_ratio = refinement.get('pullback_delta_ratio')

    pullback_icon = "✅" if in_pullback else "❌" if in_pullback is not None else "⬜"
    ratio_str = f"{delta_ratio:.2f}" if delta_ratio is not None else "-"

    st.markdown(f"In Pullback: {pullback_icon} | Delta Ratio: {ratio_str}")


# =============================================================================
# REJECTION INDICATOR RENDERERS
# =============================================================================

def _render_structure_divergence(refinement: Dict):
    """REJ-01: Structure Divergence (0-2 pts)."""
    score = refinement.get('struct_div_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**REJ-01: Structure Divergence** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    htf_aligned = refinement.get('htf_aligned')
    ltf_divergent = refinement.get('ltf_divergent')

    htf_icon = "✅" if htf_aligned else "❌" if htf_aligned is not None else "⬜"
    ltf_icon = "✅" if ltf_divergent else "❌" if ltf_divergent is not None else "⬜"

    st.markdown(f"HTF Aligned: {htf_icon} | LTF Divergent: {ltf_icon}")


def _render_sma_exhaustion(refinement: Dict):
    """REJ-02: SMA Exhaustion (0-3 pts)."""
    score = refinement.get('sma_exhst_score', 0)
    color = get_score_color(score, 3)

    st.markdown(f"**REJ-02: SMA Exhaustion** <span style='color:{color}'>{score}/3</span>", unsafe_allow_html=True)

    contracting = refinement.get('sma_spread_contracting')
    very_tight = refinement.get('sma_spread_very_tight')
    tight = refinement.get('sma_spread_tight')

    cont_icon = "✅" if contracting else "❌" if contracting is not None else "⬜"
    vtight_icon = "✅" if very_tight else "❌" if very_tight is not None else "⬜"
    tight_icon = "✅" if tight else "❌" if tight is not None else "⬜"

    st.markdown(f"Contracting: {cont_icon} | Very Tight: {vtight_icon} | Tight: {tight_icon}")


def _render_delta_absorption(refinement: Dict):
    """REJ-03: Delta Absorption (0-2 pts)."""
    score = refinement.get('delta_abs_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**REJ-03: Delta Absorption** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    ratio = refinement.get('absorption_ratio')
    ratio_str = f"{ratio:.2f}" if ratio is not None else "-"

    st.markdown(f"Absorption Ratio: {ratio_str}")


def _render_volume_climax(refinement: Dict):
    """REJ-04: Volume Climax (0-2 pts)."""
    score = refinement.get('vol_climax_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**REJ-04: Volume Climax** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    roc_q5 = refinement.get('vol_roc_q5')
    declining = refinement.get('vol_declining')

    q5_icon = "✅" if roc_q5 else "❌" if roc_q5 is not None else "⬜"
    dec_icon = "✅" if declining else "❌" if declining is not None else "⬜"

    st.markdown(f"Vol ROC Q5 (>50%): {q5_icon} | Declining: {dec_icon}")


def _render_cvd_extreme(refinement: Dict):
    """REJ-05: CVD Extreme (0-2 pts)."""
    score = refinement.get('cvd_extr_score', 0)
    color = get_score_color(score, 2)

    st.markdown(f"**REJ-05: CVD Extreme** <span style='color:{color}'>{score}/2</span>", unsafe_allow_html=True)

    slope = refinement.get('cvd_slope')
    slope_norm = refinement.get('cvd_slope_normalized')
    extreme = refinement.get('cvd_extreme')

    slope_str = f"{slope:.6f}" if slope is not None else "-"
    norm_str = f"{slope_norm:.4f}" if slope_norm is not None else "-"
    extreme_icon = "✅" if extreme else "❌" if extreme is not None else "⬜"

    st.markdown(f"CVD Slope: {slope_str} (Norm: {norm_str})")
    st.markdown(f"Extreme: {extreme_icon}")


# =============================================================================
# MONTE AI PROMPT SECTION
# =============================================================================

def _render_monte_prompt_section(trade: TradeWithMetrics, refinement: Dict[str, Any]):
    """Render the Monte AI prompt generator section."""
    st.markdown("#### Monte AI Analysis")

    with st.expander("Generate Analysis Prompt", expanded=False):
        prompt = _generate_monte_prompt(trade, refinement)

        st.text_area(
            "Copy this prompt for Claude review:",
            value=prompt,
            height=300,
            key="monte_prompt"
        )

        st.caption("Copy the prompt above and paste into Claude for trade analysis.")


def _generate_monte_prompt(trade: TradeWithMetrics, refinement: Dict[str, Any]) -> str:
    """Generate a Monte AI prompt for trade analysis."""
    trade_type = refinement.get('trade_type', 'UNKNOWN')
    model = refinement.get('model', 'N/A')
    direction = refinement.get('direction', 'N/A')
    cont_score = refinement.get('continuation_score', 0)
    cont_label = refinement.get('continuation_label', 'UNKNOWN')
    rej_score = refinement.get('rejection_score', 0)
    rej_label = refinement.get('rejection_label', 'UNKNOWN')

    # Build indicator summary
    cont_details = f"""
CONTINUATION INDICATORS (Score: {cont_score}/10 - {cont_label}):
- CONT-01 MTF Alignment: {refinement.get('mtf_align_score', 'N/A')}/4
  - H4: {'Aligned' if refinement.get('mtf_h4_aligned') else 'Not Aligned'}
  - H1: {'Aligned' if refinement.get('mtf_h1_aligned') else 'Not Aligned'}
  - M15: {'Aligned' if refinement.get('mtf_m15_aligned') else 'Not Aligned'}
  - M5: {'Aligned' if refinement.get('mtf_m5_aligned') else 'Not Aligned'}
- CONT-02 SMA Momentum: {refinement.get('sma_mom_score', 'N/A')}/2
  - Spread: {refinement.get('sma_spread', 'N/A')}, ROC: {refinement.get('sma_spread_roc', 'N/A')}%
  - Aligned: {refinement.get('sma_spread_aligned', 'N/A')}, Expanding: {refinement.get('sma_spread_expanding', 'N/A')}
- CONT-03 Volume Thrust: {refinement.get('vol_thrust_score', 'N/A')}/2
  - Vol ROC: {refinement.get('vol_roc', 'N/A')}%, Delta 5-bar: {refinement.get('vol_delta_5', 'N/A')}
- CONT-04 Pullback Quality: {refinement.get('pullback_score', 'N/A')}/2
  - In Pullback: {refinement.get('in_pullback', 'N/A')}, Delta Ratio: {refinement.get('pullback_delta_ratio', 'N/A')}
"""

    rej_details = f"""
REJECTION INDICATORS (Score: {rej_score}/11 - {rej_label}):
- REJ-01 Structure Divergence: {refinement.get('struct_div_score', 'N/A')}/2
  - HTF Aligned: {refinement.get('htf_aligned', 'N/A')}, LTF Divergent: {refinement.get('ltf_divergent', 'N/A')}
- REJ-02 SMA Exhaustion: {refinement.get('sma_exhst_score', 'N/A')}/3
  - Contracting: {refinement.get('sma_spread_contracting', 'N/A')}, Very Tight: {refinement.get('sma_spread_very_tight', 'N/A')}
- REJ-03 Delta Absorption: {refinement.get('delta_abs_score', 'N/A')}/2
  - Absorption Ratio: {refinement.get('absorption_ratio', 'N/A')}
- REJ-04 Volume Climax: {refinement.get('vol_climax_score', 'N/A')}/2
  - Vol ROC Q5: {refinement.get('vol_roc_q5', 'N/A')}, Declining: {refinement.get('vol_declining', 'N/A')}
- REJ-05 CVD Extreme: {refinement.get('cvd_extr_score', 'N/A')}/2
  - CVD Slope: {refinement.get('cvd_slope', 'N/A')}, Extreme: {refinement.get('cvd_extreme', 'N/A')}
"""

    prompt = f"""EPOCH INDICATOR REFINEMENT ANALYSIS

Trade: {trade.trade_id}
Date: {trade.date}
Ticker: {trade.ticker}
Model: {model}
Direction: {direction}
Trade Type: {trade_type}
Entry Price: ${trade.entry_price:.2f if trade.entry_price else 'N/A'}

{cont_details}
{rej_details}

ANALYSIS REQUEST:
Based on the indicator refinement scores above, please analyze:

1. **Score Interpretation**: Is the {'continuation' if trade_type == 'CONTINUATION' else 'rejection'} score of {cont_score if trade_type == 'CONTINUATION' else rej_score} appropriate for this {'with-trend' if trade_type == 'CONTINUATION' else 'counter-trend/exhaustion'} trade?

2. **Key Strengths**: Which indicators contributed most positively to the score?

3. **Key Weaknesses**: Which indicators suggest caution or weakness?

4. **Trade Qualification**: Based on the label ({cont_label if trade_type == 'CONTINUATION' else rej_label}), would you have taken this trade? Why or why not?

5. **Learning Points**: What can be learned from this indicator configuration for future trades?
"""

    return prompt
