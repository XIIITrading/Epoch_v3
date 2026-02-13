"""
Epoch Trading System - HVN POC Lines Helper
Adds horizontal POC lines to any Plotly chart at 70% transparency.
"""

import plotly.graph_objects as go
from typing import List, Optional

# POC line styling
POC_COLOR = '#FFFFFF'   # White
POC_OPACITY = 0.3       # 70% transparent (1.0 - 0.7 = 0.3)
POC_WIDTH = 1.0
POC_DASH = 'dot'


def add_poc_lines(
    fig: go.Figure,
    pocs: Optional[List[float]] = None,
):
    """
    Add HVN POC horizontal lines to a chart.

    Args:
        fig: Plotly Figure
        pocs: List of POC prices from hvn_pocs table
    """
    if not pocs:
        return

    for price in pocs:
        if price and price > 0:
            fig.add_hline(
                y=price,
                line_color=POC_COLOR,
                line_width=POC_WIDTH,
                line_dash=POC_DASH,
                opacity=POC_OPACITY,
            )
