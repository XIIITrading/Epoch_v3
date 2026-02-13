"""
DOW AI Prediction Display Component
Renders AI prediction from ai_predictions table.

Single-pass prediction with confidence, reasoning, and extracted indicators.
"""

import streamlit as st
from typing import Optional, Dict, Any


def render_batch_prediction(trade_id: str, supabase_client) -> None:
    """
    Render AI prediction for a trade from ai_predictions table.

    Args:
        trade_id: Trade ID to fetch prediction for
        supabase_client: SupabaseClient instance
    """
    prediction = supabase_client.fetch_ai_prediction(trade_id)

    if not prediction:
        st.info("No AI prediction available for this trade.")
        return

    _render_prediction_content(prediction)


def _render_prediction_content(pred: Dict[str, Any]) -> None:
    """Render the AI prediction content (no wrapper - caller controls container)."""

    # Decision and confidence header
    prediction = pred.get('prediction', 'N/A')
    confidence = pred.get('confidence', 'N/A')

    # Decision color
    if prediction == 'TRADE':
        dec_color = "#4CAF50"
    elif prediction == 'NO_TRADE':
        dec_color = "#FF5252"
    else:
        dec_color = "#888"

    # Confidence color
    conf_colors = {
        'HIGH': '#4CAF50',
        'MEDIUM': '#FFD700',
        'LOW': '#FF9800'
    }
    conf_color = conf_colors.get(confidence, '#888')

    # Correctness badge
    is_correct = pred.get('prediction_correct')
    if is_correct is True:
        correct_badge = "<span style='color: #4CAF50; margin-left: 8px;'>&#10004;</span>"
    elif is_correct is False:
        correct_badge = "<span style='color: #FF5252; margin-left: 8px;'>&#10008;</span>"
    else:
        correct_badge = ""

    # Main prediction display
    st.markdown(f"""
    <div style="border: 1px solid #333; border-radius: 8px; padding: 16px; background-color: #1a1a2e; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; margin-bottom: 8px;">
            <span style="color: {dec_color};">{prediction}</span>
            {correct_badge}
        </div>
        <div style="margin-bottom: 4px;">
            Confidence: <span style="color: {conf_color}; font-weight: bold;">{confidence}</span>
        </div>
        <div style="font-size: 12px; color: #666;">
            {pred.get('direction', '')} | {pred.get('model', '')} | {pred.get('zone_type', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reasoning
    reasoning = pred.get('reasoning')
    if reasoning:
        with st.expander("Reasoning", expanded=False):
            st.markdown(f"_{reasoning}_")

    # Extracted Indicators
    st.markdown("---")
    st.markdown("**EXTRACTED INDICATORS:**")

    candle_pct = pred.get('candle_pct')
    vol_delta = pred.get('vol_delta')
    vol_roc = pred.get('vol_roc')
    sma = pred.get('sma')
    h1_struct = pred.get('h1_struct')

    candle_str = f"{candle_pct:.2f}%" if candle_pct is not None else "N/A"
    vol_roc_str = f"{vol_roc:+.0f}%" if vol_roc is not None else "N/A"

    indicators = f"""
- **Candle %:** {candle_str} ({_status_badge(pred.get('candle_status'))})
- **Vol Delta:** {_format_vol_delta(vol_delta)} ({_status_badge(pred.get('vol_delta_status'))})
- **Vol ROC:** {vol_roc_str} ({_status_badge(pred.get('vol_roc_status'))})
- **SMA:** {sma or 'N/A'}
- **H1 Structure:** {h1_struct or 'N/A'}
    """
    st.markdown(indicators)

    # Outcome tracking
    actual_outcome = pred.get('actual_outcome')
    if actual_outcome:
        st.markdown("---")
        st.markdown("**OUTCOME TRACKING:**")

        actual_pnl_r = pred.get('actual_pnl_r')
        pnl_str = f"{actual_pnl_r:+.2f}R" if actual_pnl_r is not None else "N/A"

        outcome_color = "#4CAF50" if actual_outcome in ('WIN', 'winner') else "#FF5252"

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f"**Actual:** <span style='color: {outcome_color};'>{actual_outcome.upper()}</span> ({pnl_str})",
                unsafe_allow_html=True
            )
        with col_b:
            correct_icon = "&#10004;" if is_correct else "&#10008;" if is_correct is False else "&#8212;"
            correct_color = "#4CAF50" if is_correct else "#FF5252" if is_correct is False else "#888"
            st.markdown(
                f"**Prediction:** <span style='color: {correct_color};'>{correct_icon}</span>",
                unsafe_allow_html=True
            )

    # Metadata
    st.markdown("---")
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.caption(f"Version: {pred.get('prompt_version', 'N/A')}")
    with meta_cols[1]:
        st.caption(f"Model: {pred.get('model_used', 'N/A')}")
    with meta_cols[2]:
        created_at = pred.get('created_at')
        if created_at:
            try:
                st.caption(f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}")
            except AttributeError:
                st.caption(f"Created: {created_at}")


def _status_badge(status: str) -> str:
    """Return status text with appropriate formatting."""
    status_map = {
        'FAVORABLE': 'FAVORABLE',
        'NEUTRAL': 'NEUTRAL',
        'UNFAVORABLE': 'UNFAVORABLE',
        'SKIP': 'SKIP',
        'ALIGNED': 'ALIGNED',
        'OPPOSING': 'OPPOSING',
        'ELEVATED': 'ELEVATED',
        'NORMAL': 'NORMAL',
        'LOW': 'LOW'
    }
    return status_map.get(status, status or 'N/A')


def _format_vol_delta(value) -> str:
    """Format volume delta with K/M suffix."""
    if value is None:
        return 'N/A'
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:+,.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:+,.0f}K"
    return f"{value:+,.0f}"
