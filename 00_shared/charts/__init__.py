"""
Epoch Trading System - Shared Chart Resources
==============================================

Centralized chart colors, Plotly templates, and branding for all modules.
This package is for chart RENDERING (Plotly, Matplotlib, PIL).
For PyQt widget styling, use shared.ui.styles instead.

Usage:
    from shared.charts import EPOCH_DARK, TV_DARK, RANK_COLORS, TIER_COLORS
    from shared.charts import register_templates
    from shared.charts import BRAND_COLORS, BRANDING, EXPORT_SIZES

    # Use a palette for chart rendering:
    palette = TV_DARK
    fig.add_trace(go.Candlestick(
        increasing_line_color=palette['candle_up'],
        decreasing_line_color=palette['candle_down'],
    ))

    # Plotly templates auto-register on import.
    # To switch default: register_templates(default='tradingview_dark')
"""

from .colors import (
    EPOCH_DARK,
    TV_DARK,
    TV_UI,
    RANK_COLORS,
    TIER_COLORS,
    INDICATOR_REFINEMENT_COLORS,
    COLORWAY_DEFAULT,
)

from .plotly_template import register_templates

from .branding import (
    BRAND_COLORS,
    BRANDING,
    EXPORT_SIZES,
    WATERMARK_HANDLE,
)

__all__ = [
    # Palettes
    "EPOCH_DARK",
    "TV_DARK",
    "TV_UI",
    # Semantic colors
    "RANK_COLORS",
    "TIER_COLORS",
    "INDICATOR_REFINEMENT_COLORS",
    "COLORWAY_DEFAULT",
    # Plotly
    "register_templates",
    # Branding
    "BRAND_COLORS",
    "BRANDING",
    "EXPORT_SIZES",
    "WATERMARK_HANDLE",
]
