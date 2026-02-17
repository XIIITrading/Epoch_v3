"""
Epoch Trading System - Volume by Price (VbP) for Plotly Charts
Builds horizontal volume profile from OHLCV bars and renders as
left-side overlay shapes within the main chart area.

Layout: VbP bars are drawn as rectangles on the chart, anchored to the
left edge, with the largest bar capped at 20% of the chart width.
Uses Plotly shapes (not traces) to avoid axis/background artifacts.
"""

import pandas as pd
import plotly.graph_objects as go
from math import floor, ceil
from typing import Dict, Optional, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_COLORS

# VbP configuration
VBP_NUM_BINS = 150          # Target number of price bins (auto-scales granularity)
VBP_COLOR = 'rgba(195,195,195,0.30)'  # Light grey at 30% opacity
VBP_MAX_WIDTH_FRAC = 0.20  # Largest bar = 20% of x-axis (paper coords)

# Volume bar colors (match candle colors with transparency)
VOL_UP_COLOR = CHART_COLORS['candle_up']      # Teal (up candles)
VOL_DOWN_COLOR = CHART_COLORS['candle_down']   # Red (down candles)
VOL_OPACITY = 0.45                              # Subtle but visible

# Volume bars render inside the candlestick area (shared y-axis domain)
VOL_BAR_MAX_HEIGHT = 0.20       # Volume bars: max 20% of chart height
CANDLE_DOMAIN_BOTTOM = 0.0      # No domain offset — volume buffer handled via y-range padding
VOL_CLEARANCE_FRAC = 0.24       # Lowest candle sits at 24% of chart height (above 20% vol bars + gap)


def build_volume_profile(bars: pd.DataFrame, num_bins: int = VBP_NUM_BINS) -> Dict[float, float]:
    """
    Build volume profile with auto-scaled price bins.

    Args:
        bars: OHLCV DataFrame
        num_bins: Target number of price bins across the full range

    Returns:
        Dict mapping price_level -> accumulated_volume
    """
    if bars is None or bars.empty:
        return {}

    price_min = float(bars['low'].min())
    price_max = float(bars['high'].max())
    price_range = price_max - price_min

    if price_range <= 0:
        return {}

    # Auto-scale granularity based on price range and target bin count
    granularity = price_range / num_bins
    granularity = _round_granularity(granularity)

    volume_profile: Dict[float, float] = {}

    for _, bar in bars.iterrows():
        bar_low = float(bar['low'])
        bar_high = float(bar['high'])
        bar_volume = float(bar['volume'])

        if bar_volume <= 0 or bar_high <= bar_low:
            continue

        low_level = floor(bar_low / granularity) * granularity
        high_level = ceil(bar_high / granularity) * granularity

        num_levels = int(round((high_level - low_level) / granularity)) + 1
        if num_levels <= 0:
            continue

        volume_per_level = bar_volume / num_levels

        current = low_level
        for _ in range(num_levels):
            price_key = round(current, 4)
            volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
            current += granularity

    return volume_profile


def _round_granularity(g: float) -> float:
    """Round raw granularity to a clean step size."""
    if g >= 5.0:
        return round(g)
    elif g >= 1.0:
        return round(g * 2) / 2
    elif g >= 0.25:
        return round(g * 4) / 4
    elif g >= 0.10:
        return round(g * 10) / 10
    elif g >= 0.05:
        return 0.05
    elif g >= 0.01:
        return round(g * 100) / 100
    else:
        return 0.01


def create_chart_with_vbp(height: int = 380) -> go.Figure:
    """
    Create a standard single-panel Plotly figure with y-axis domain
    offset to separate candlesticks from volume bars at the bottom.

    Args:
        height: Figure height in pixels

    Returns:
        Plotly Figure (single panel)
    """
    fig = go.Figure()
    fig.update_layout(
        yaxis=dict(domain=[CANDLE_DOMAIN_BOTTOM, 1.0]),
    )
    return fig


def _add_vbp_shapes(
    fig: go.Figure,
    profile: Dict[float, float],
    y_min: float,
    y_max: float,
):
    """
    Internal: render pre-filtered volume profile dict as Plotly shapes.

    Args:
        fig: Plotly Figure
        profile: Dict mapping price_level -> volume (already filtered to visible range)
        y_min: Minimum price of visible range (for bin height fallback)
        y_max: Maximum price of visible range (for bin height fallback)
    """
    if not profile:
        return

    max_vol = max(profile.values())
    if max_vol <= 0:
        return

    sorted_prices = sorted(profile.keys())

    # Calculate bin height from actual spacing
    if len(sorted_prices) >= 2:
        bin_height = sorted_prices[1] - sorted_prices[0]
    else:
        bin_height = (y_max - y_min) / VBP_NUM_BINS

    half_bin = bin_height / 2

    # Build shapes: each bar is a rectangle
    # x-coords in paper space (0=left edge, 1=right edge)
    # y-coords in data space (price)
    shapes = []
    for price, vol in profile.items():
        # Normalized width: max vol bar = VBP_MAX_WIDTH_FRAC of chart
        width_frac = (vol / max_vol) * VBP_MAX_WIDTH_FRAC

        shapes.append(dict(
            type='rect',
            xref='paper',
            yref='y',
            x0=0,
            x1=width_frac,
            y0=price - half_bin,
            y1=price + half_bin,
            fillcolor=VBP_COLOR,
            line=dict(width=0),
            layer='below',
        ))

    fig.update_layout(shapes=list(fig.layout.shapes or []) + shapes)


def add_volume_profile(
    fig: go.Figure,
    bars: pd.DataFrame,
    y_min: Optional[float] = None,
    y_max: Optional[float] = None,
):
    """
    Add volume profile as left-side overlay using Plotly shapes.
    Computes the profile from bars, then renders. Use add_volume_profile_from_dict()
    if you have a pre-computed profile to avoid redundant computation.

    Args:
        fig: Plotly Figure (single panel)
        bars: OHLCV DataFrame used to compute the profile
        y_min: Optional minimum price to filter profile
        y_max: Optional maximum price to filter profile
    """
    if bars is None or bars.empty:
        return

    vp = build_volume_profile(bars)
    if not vp:
        return

    if y_min is None:
        y_min = float(bars['low'].min())
    if y_max is None:
        y_max = float(bars['high'].max())

    # Filter to visible range
    filtered = {p: v for p, v in vp.items() if y_min <= p <= y_max}
    _add_vbp_shapes(fig, filtered, y_min, y_max)


def add_volume_profile_from_dict(
    fig: go.Figure,
    volume_profile: Dict[float, float],
    y_min: Optional[float] = None,
    y_max: Optional[float] = None,
):
    """
    Add volume profile from a pre-computed dict (avoids re-computing from bars).
    Filters the profile to the visible price range [y_min, y_max].

    Args:
        fig: Plotly Figure (single panel)
        volume_profile: Pre-computed dict mapping price_level -> volume
        y_min: Minimum visible price (required for filtering)
        y_max: Maximum visible price (required for filtering)
    """
    if not volume_profile:
        return

    if y_min is None or y_max is None:
        # No bounds given — use entire profile
        filtered = volume_profile
        all_prices = list(volume_profile.keys())
        y_min = min(all_prices) if all_prices else 0
        y_max = max(all_prices) if all_prices else 1
    else:
        # Filter to visible range
        filtered = {p: v for p, v in volume_profile.items() if y_min <= p <= y_max}

    _add_vbp_shapes(fig, filtered, y_min, y_max)


def add_volume_bars(fig: go.Figure, df: pd.DataFrame):
    """
    Add TradingView-style volume bars at the bottom of a candlestick chart.
    Bars are color-matched to candle direction (up=teal, down=red).

    Uses Plotly shapes (not go.Bar) to avoid axis scaling issues with
    rangebreaks. Each bar is a rectangle: x in data coords (datetime),
    y from paper 0 (bottom) to a height proportional to volume (max = 20%).

    Args:
        fig: Plotly Figure with candlestick already added
        df: OHLCV DataFrame (must have 'open', 'close', 'volume' columns)
    """
    if df is None or df.empty or 'volume' not in df.columns:
        return

    max_vol = df['volume'].max()
    if max_vol <= 0:
        return

    # Max volume bar height as fraction of chart
    max_height_frac = VOL_BAR_MAX_HEIGHT

    # Calculate half-bar width from median candle interval
    half_width = pd.Timedelta(minutes=0.4)  # fallback
    if len(df) >= 2:
        diffs = pd.Series(df.index).diff().dropna()
        median_interval = diffs.median()
        half_width = median_interval * 0.4  # 80% of interval, split in half

    shapes = []
    for idx, row in df.iterrows():
        vol = float(row['volume'])
        if vol <= 0:
            continue

        # Bar height proportional to volume (paper coords: 0=bottom, 1=top)
        height_frac = (vol / max_vol) * max_height_frac

        # Color based on candle direction
        color = VOL_UP_COLOR if row['close'] >= row['open'] else VOL_DOWN_COLOR

        shapes.append(dict(
            type='rect',
            xref='x',
            yref='paper',
            x0=idx - half_width,
            x1=idx + half_width,
            y0=0,
            y1=height_frac,
            fillcolor=color,
            opacity=VOL_OPACITY,
            line=dict(width=0),
            layer='below',
        ))

    fig.update_layout(shapes=list(fig.layout.shapes or []) + shapes)
