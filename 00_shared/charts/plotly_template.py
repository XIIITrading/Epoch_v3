"""
Epoch Trading System - Plotly Template Registration
====================================================

Registers two custom Plotly templates:
- 'epoch_dark': Standard dark theme for analytics charts
- 'tradingview_dark': TradingView-style for trade_reel charts

Import this module to auto-register both templates.
Calling register_templates() is idempotent.

Usage:
    from shared.charts import register_templates

    # Default is 'epoch_dark'
    register_templates()

    # Switch to TradingView dark
    register_templates(default='tradingview_dark')
"""

import plotly.graph_objects as go
import plotly.io as pio

from .colors import EPOCH_DARK, TV_DARK, COLORWAY_DEFAULT

_registered = False


def register_templates(default: str = 'epoch_dark'):
    """
    Register Epoch Plotly templates and set the default.

    Both templates are always registered. The `default` parameter
    controls which one is active globally.

    Args:
        default: 'epoch_dark' or 'tradingview_dark'
    """
    global _registered

    if not _registered:
        # Epoch Dark template
        epoch_tmpl = go.layout.Template(
            layout=go.Layout(
                plot_bgcolor=EPOCH_DARK['background'],
                paper_bgcolor=EPOCH_DARK['paper'],
                font=dict(color=EPOCH_DARK['text'], family='Arial'),
                xaxis=dict(
                    gridcolor=EPOCH_DARK['grid'],
                    linecolor=EPOCH_DARK['grid'],
                    zerolinecolor=EPOCH_DARK['grid'],
                    tickfont=dict(color=EPOCH_DARK['text_muted']),
                ),
                yaxis=dict(
                    gridcolor=EPOCH_DARK['grid'],
                    linecolor=EPOCH_DARK['grid'],
                    zerolinecolor=EPOCH_DARK['grid'],
                    tickfont=dict(color=EPOCH_DARK['text_muted']),
                    side='right',
                ),
                colorway=COLORWAY_DEFAULT,
            )
        )
        pio.templates['epoch_dark'] = epoch_tmpl

        # TradingView Dark template
        tv_tmpl = go.layout.Template(
            layout=go.Layout(
                plot_bgcolor=TV_DARK['background'],
                paper_bgcolor=TV_DARK['paper'],
                font=dict(color=TV_DARK['text'], family='Arial'),
                xaxis=dict(
                    gridcolor=TV_DARK['grid'],
                    showgrid=False,
                    linecolor='#1A1E29',
                    linewidth=0,
                    zerolinecolor=TV_DARK['grid'],
                    tickfont=dict(color=TV_DARK['text_muted']),
                ),
                yaxis=dict(
                    gridcolor=TV_DARK['grid'],
                    linecolor='#1A1E29',
                    linewidth=0,
                    zerolinecolor=TV_DARK['grid'],
                    tickfont=dict(color=TV_DARK['text_muted']),
                    side='right',
                ),
                colorway=COLORWAY_DEFAULT,
            )
        )
        pio.templates['tradingview_dark'] = tv_tmpl
        _registered = True

    pio.templates.default = default


# Auto-register on import
register_templates()
