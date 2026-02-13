"""
Epoch Trading System - TradingView Dark Plotly Template
Registers a custom Plotly template matching the TradingView dark theme.
"""

import plotly.graph_objects as go
import plotly.io as pio


def register_tv_dark_template():
    """Register the TradingView Dark template and set as default."""
    tv_dark = go.layout.Template(
        layout=go.Layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#D1D4DC', family='Arial'),
            xaxis=dict(
                gridcolor='#2A2E39',
                showgrid=False,
                linecolor='#1A1E29',
                linewidth=0,
                zerolinecolor='#2A2E39',
                tickfont=dict(color='#787B86'),
            ),
            yaxis=dict(
                gridcolor='#2A2E39',
                linecolor='#1A1E29',
                linewidth=0,
                zerolinecolor='#2A2E39',
                tickfont=dict(color='#787B86'),
                side='right',
            ),
            colorway=['#2962FF', '#089981', '#F23645', '#FF9800'],
        )
    )
    pio.templates['tradingview_dark'] = tv_dark
    pio.templates.default = 'tradingview_dark'


# Auto-register on import
register_tv_dark_template()
