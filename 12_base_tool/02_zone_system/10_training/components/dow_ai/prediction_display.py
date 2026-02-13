"""
DOW AI Prediction Display Component
Renders pre-computed batch predictions from ai_predictions table.
"""

import streamlit as st
from typing import Optional, Dict, Any


def render_batch_prediction(trade_id: str, supabase_client) -> None:
    """
    Render batch DOW AI prediction for a trade.

    Args:
        trade_id: Trade ID to fetch prediction for
        supabase_client: SupabaseClient instance
    """
    prediction = supabase_client.fetch_ai_prediction(trade_id)

    if not prediction:
        st.info("No batch prediction available. Run batch analyzer to generate.")
        return

    _render_prediction_panel(prediction)


def _render_prediction_panel(pred: Dict[str, Any]) -> None:
    """Render the prediction panel matching live DOW AI format."""

    with st.expander("DOW AI Pre-Trade Analysis", expanded=True):
        # Header: Prediction + Confidence
        prediction = pred.get('prediction', 'N/A')
        confidence = pred.get('confidence', 'N/A')

        pred_color = "#4CAF50" if prediction == 'TRADE' else "#FF5252"

        st.markdown(f"""
        <div style="font-size: 24px; font-weight: bold; margin-bottom: 16px;">
            <span style="color: {pred_color};">[{prediction}]</span>
            <span style="color: #888;">|</span>
            Confidence: <span style="color: #FFD700;">{confidence}</span>
        </div>
        """, unsafe_allow_html=True)

        # Indicators Section
        st.markdown("**INDICATORS:**")

        candle_pct = pred.get('candle_pct')
        vol_delta = pred.get('vol_delta')
        vol_roc = pred.get('vol_roc')

        # Handle None values gracefully
        candle_str = f"{candle_pct:.2f}%" if candle_pct is not None else "N/A"
        vol_roc_str = f"{vol_roc:+.0f}%" if vol_roc is not None else "N/A"

        indicators = f"""
- **Candle %:** {candle_str} ({_status_badge(pred.get('candle_status'))})
- **Vol Delta:** {_format_vol_delta(vol_delta)} ({_status_badge(pred.get('vol_delta_status'))})
- **Vol ROC:** {vol_roc_str} ({_status_badge(pred.get('vol_roc_status'))})
- **SMA:** {_direction_badge(pred.get('sma'))}
- **H1 Struct:** {_direction_badge(pred.get('h1_struct'))}
        """
        st.markdown(indicators)

        # Snapshot
        snapshot = pred.get('snapshot', '')
        if snapshot:
            st.markdown("---")
            st.markdown("**SNAPSHOT:**")
            st.markdown(f"_{snapshot}_")


def _status_badge(status: str) -> str:
    """Return colored status text."""
    colors = {
        'GOOD': 'GOOD',
        'OK': 'OK',
        'SKIP': 'SKIP',
        'FAVORABLE': 'FAVORABLE',
        'NEUTRAL': 'NEUTRAL',
        'WEAK': 'WEAK',
        'ELEVATED': 'ELEVATED',
        'NORMAL': 'NORMAL'
    }
    return colors.get(status, status or 'N/A')


def _direction_badge(direction: str) -> str:
    """Return colored direction text."""
    colors = {
        'BULL': 'BULL',
        'BEAR': 'BEAR',
        'NEUT': 'NEUT'
    }
    return colors.get(direction, direction or 'N/A')


def _format_vol_delta(value) -> str:
    """Format volume delta with K/M suffix."""
    if value is None:
        return 'N/A'
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:+,.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:+,.0f}K"
    return f"{value:+,.0f}"
