"""
Epoch Trading System - HVN POC Lines Helper
Adds horizontal POC lines to any Plotly chart.
Zone POC lines color-coded by setup_type from setups table:
  - PRIMARY: blue
  - SECONDARY: red
"""

import plotly.graph_objects as go
from typing import List, Optional

# POC line styling
POC_COLOR = '#FFFFFF'   # White (fallback)
POC_OPACITY = 0.3       # 70% transparent (1.0 - 0.7 = 0.3)
POC_WIDTH = 1.0
POC_DASH = 'solid'

# Setup-type colors
PRIMARY_COLOR = '#2962FF'    # Blue
SECONDARY_COLOR = '#F23645'  # Red


def add_poc_lines(
    fig: go.Figure,
    pocs: Optional[List[float]] = None,
):
    """
    Add HVN POC horizontal lines to a chart (flat list, white lines).

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


def add_zone_poc_lines(
    fig: go.Figure,
    zones: Optional[List[dict]] = None,
    highlight=None,
):
    """
    Add HVN POC lines from setups table, color-coded by setup_type.
    PRIMARY = blue, SECONDARY = red.

    Args:
        fig: Plotly Figure
        zones: List of setup dicts with setup_type, hvn_poc keys
        highlight: Optional HighlightTrade (unused, kept for API compatibility)
    """
    if not zones:
        return

    for zone in zones:
        poc_price = zone.get('hvn_poc')
        if not poc_price or float(poc_price) <= 0:
            continue

        setup_type = (zone.get('setup_type') or '').upper()
        if setup_type == 'PRIMARY':
            color = PRIMARY_COLOR
        elif setup_type == 'SECONDARY':
            color = SECONDARY_COLOR
        else:
            color = POC_COLOR

        fig.add_hline(
            y=float(poc_price),
            line_color=color,
            line_width=POC_WIDTH,
            line_dash=POC_DASH,
            opacity=POC_OPACITY,
        )
