"""
Pre-Market Report Page - Exact replica of the PDF report visualization.

Displays the complete pre-market analysis chart matching the layout from
02_zone_system/08_visualization/pre_market_analysis.py but rendered in Streamlit.

Layout:
- Left panel: Market Structure, Ticker Structure, Zone Results, Setup Analysis, Notes
- Right panel: H1 candlestick chart with epoch VbP + POC lines
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import io
import logging
import streamlit as st

from config.visualization_config import (
    COLORS, RANK_COLORS, TIER_COLORS, ZONE_FILL_ALPHA,
    VBP_COLOR, POC_LINE_STYLE, POC_LINE_COLOR, POC_LINE_ALPHA,
    YAXIS_PADDING_PCT, CANDLE_BAR_COUNT, VBP_TIMEFRAME
)
from core.data_models import (
    MarketStructure, BarData, HVNResult, FilteredZone,
    Setup, Direction, Tier, Rank
)
from data.polygon_client import PolygonClient

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS - EXACT MATCH TO WORKING PDF GENERATOR
# =============================================================================

# Figure dimensions (matching 02_zone_system/08_visualization/charts/chart_builder.py)
FIGURE_WIDTH = 20
FIGURE_HEIGHT = 12
DPI = 600

# Table height ratios (from original)
TABLE_HEIGHT_RATIOS = [1.0, 1.2, 1.8, 1.4, 0.8]

# Font sizes (EXACT match to working chart_builder.py)
# These are fixed values - do not change or the layout will break
FONT_TITLE = 16       # Main title (suptitle)
FONT_SUBTITLE = 11    # Subtitle below title
FONT_HEADER = 9       # Table headers (bold)
FONT_TABLE = 9        # Table row data
FONT_TABLE_BOLD = 10  # Bold table values (direction, rank, tier)
FONT_LABEL = 8        # Small labels
FONT_AXIS = 9         # Axis tick labels
FONT_AXIS_LABEL = 11  # Axis title labels
FONT_POC_LABEL = 7    # POC price labels on chart

# Candlestick settings (matching original)
CANDLE_WIDTH = 0.6    # Width of candle body
CANDLE_SPACING = 1.0  # No extra spacing


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_direction_color(direction) -> str:
    """Get color for bull/bear direction."""
    if direction is None:
        return COLORS['neutral']

    if isinstance(direction, Direction):
        direction = direction.value

    direction_str = str(direction).upper()
    if 'BULL' in direction_str:
        return COLORS['bull']
    elif 'BEAR' in direction_str:
        return COLORS['bear']
    return COLORS['neutral']


def get_tier_color(tier) -> str:
    """Get color for tier classification."""
    if tier is None:
        return COLORS['text_muted']

    if isinstance(tier, Tier):
        tier = tier.value

    return TIER_COLORS.get(str(tier).upper(), COLORS['text_muted'])


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None or price == 0 or pd.isna(price):
        return "-"
    return f"${price:.2f}"


# =============================================================================
# PRE-MARKET CHART BUILDER
# =============================================================================

class PreMarketChartBuilder:
    """Build exact replica of pre-market PDF report visualization."""

    def __init__(self):
        self.fig = None
        self.axes = {}

    def build(
        self,
        ticker: str,
        anchor_date: date,
        market_structure: MarketStructure,
        bar_data: BarData,
        hvn_result: HVNResult,
        filtered_zones: List[FilteredZone],
        primary_setup: Optional[Setup],
        secondary_setup: Optional[Setup],
        candle_data: Optional[pd.DataFrame] = None,
        volume_profile: Optional[Dict[float, float]] = None,
        index_structures: Optional[List[Dict]] = None,
        notes: str = ""
    ) -> plt.Figure:
        """
        Build complete pre-market report visualization.

        Args:
            ticker: Ticker symbol
            anchor_date: Epoch anchor date
            market_structure: Market structure data for the ticker
            bar_data: Bar data with levels
            hvn_result: HVN POC calculation result
            filtered_zones: List of filtered zones
            primary_setup: Primary setup (or None)
            secondary_setup: Secondary setup (or None)
            candle_data: DataFrame with H1 OHLC data
            volume_profile: Dict of price -> volume
            index_structures: List of index ETF structures (SPY, QQQ, DIA)
            notes: User notes text

        Returns:
            matplotlib Figure object
        """
        # Create figure with dark background
        self.fig = plt.figure(
            figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
            facecolor=COLORS['dark_bg'],
            dpi=DPI
        )

        # Main layout: Left (tables) | Right (chart + VP)
        main_gs = GridSpec(
            1, 2, width_ratios=[1, 1.8], wspace=0.03,
            left=0.02, right=0.98, top=0.91, bottom=0.05
        )

        # Left panel: Stack of tables
        left_gs = main_gs[0].subgridspec(5, 1, height_ratios=TABLE_HEIGHT_RATIOS, hspace=0.15)

        # Right panel: Chart + Volume Profile
        right_gs = main_gs[1].subgridspec(1, 2, width_ratios=[4, 1], wspace=0.02)

        # Build each section
        self._build_market_structure(
            self.fig.add_subplot(left_gs[0]),
            index_structures or []
        )
        self._build_ticker_structure(
            self.fig.add_subplot(left_gs[1]),
            market_structure,
            bar_data
        )
        self._build_zone_results(
            self.fig.add_subplot(left_gs[2]),
            filtered_zones,
            ticker
        )
        self._build_setup_analysis(
            self.fig.add_subplot(left_gs[3]),
            primary_setup,
            secondary_setup,
            ticker,
            filtered_zones
        )
        self._build_notes(
            self.fig.add_subplot(left_gs[4]),
            notes,
            hvn_result,
            primary_setup,
            secondary_setup
        )

        # Build chart and volume profile with shared y-axis
        ax_chart = self.fig.add_subplot(right_gs[0])
        ax_vp = self.fig.add_subplot(right_gs[1], sharey=ax_chart)

        # Get epoch POC prices
        epoch_pocs = hvn_result.get_poc_prices() if hvn_result else []

        # Build chart first to get y-limits, then VP
        y_limits = self._build_price_chart(
            ax_chart, candle_data, primary_setup, secondary_setup,
            epoch_pocs, bar_data, hvn_result
        )
        self._build_volume_profile(ax_vp, volume_profile, y_limits)

        # Title
        date_str = datetime.now().strftime('%Y-%m-%d')
        composite = market_structure.composite.value if market_structure and market_structure.composite else "N/A"

        self.fig.suptitle(
            f'{ticker} | Pre-Market Report | {date_str} | Composite: {composite}',
            color=COLORS['text_primary'], fontsize=FONT_TITLE, fontweight='bold', y=0.97
        )

        # Subtitle with epoch info
        price = bar_data.price if bar_data else 0
        atr = bar_data.d1_atr if bar_data else 0
        anchor_str = anchor_date.strftime('%Y-%m-%d') if anchor_date else "N/A"
        d1_atr_str = f"D1ATR : {atr:.2f}" if atr else "D1ATR : N/A"

        self.fig.text(
            0.5, 0.935,
            f'Current: {price:.2f}|{d1_atr_str} | Anchor Date: {anchor_str}',
            color=COLORS['text_muted'], fontsize=FONT_SUBTITLE, ha='center'
        )

        return self.fig

    def _build_market_structure(self, ax: plt.Axes, index_structures: List[Dict]):
        """Build Market Structure table for index ETFs (SPY, QQQ, DIA)."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Headers (matching original chart_builder.py)
        headers = ['Index', 'D1', 'H4', 'H1', 'M15', 'Comp']
        x_positions = [0.08, 0.22, 0.36, 0.50, 0.64, 0.82]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.75, header, color=COLORS['text_muted'],
                   fontsize=FONT_HEADER, ha='center', fontweight='bold')

        # Data rows for SPY, QQQ, DIA
        y_positions = [0.55, 0.35, 0.15]
        default_indices = ['SPY', 'QQQ', 'DIA']

        for row_idx, y in enumerate(y_positions):
            if row_idx < len(index_structures):
                ms = index_structures[row_idx]
                values = [
                    ms.get('ticker', default_indices[row_idx]),
                    ms.get('d1_dir', '-'),
                    ms.get('h4_dir', '-'),
                    ms.get('h1_dir', '-'),
                    ms.get('m15_dir', '-'),
                    ms.get('composite', '-')
                ]
            else:
                values = [default_indices[row_idx], '-', '-', '-', '-', '-']

            for col_idx, val in enumerate(values):
                color = get_direction_color(val) if col_idx > 0 else COLORS['text_primary']
                ax.text(x_positions[col_idx], y, str(val), color=color,
                       fontsize=FONT_TABLE_BOLD, ha='center', va='center')

            if row_idx < 2:
                ax.axhline(y - 0.10, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)

    def _build_ticker_structure(self, ax: plt.Axes, market_structure: MarketStructure, bar_data: BarData):
        """Build Ticker Structure table with direction and strong/weak levels."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Column positions (matching original)
        x_positions = [0.22, 0.36, 0.50, 0.64, 0.82]
        tf_labels = ['D1', 'H4', 'H1', 'M15', 'Comp']

        # Headers
        ax.text(0.05, 0.72, 'Direction:', color=COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        for i, tf in enumerate(tf_labels):
            ax.text(x_positions[i], 0.78, tf, color=COLORS['text_muted'], fontsize=FONT_LABEL, ha='center')

        # Direction values
        if market_structure:
            directions = [
                market_structure.d1.direction.value if market_structure.d1 else "-",
                market_structure.h4.direction.value if market_structure.h4 else "-",
                market_structure.h1.direction.value if market_structure.h1 else "-",
                market_structure.m15.direction.value if market_structure.m15 else "-",
                market_structure.composite.value if market_structure.composite else "-"
            ]
            for i, dir_val in enumerate(directions):
                color = get_direction_color(dir_val)
                ax.text(x_positions[i], 0.65, str(dir_val) if dir_val else "-",
                       color=color, fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

        # Strong levels
        ax.text(0.05, 0.45, 'Strong:', color=COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        if bar_data:
            strongs = [bar_data.d1_strong, bar_data.h4_strong, bar_data.h1_strong, bar_data.m15_strong]
            for i, val in enumerate(strongs):
                ax.text(x_positions[i], 0.45, format_price(val),
                       color=COLORS['bull'], fontsize=FONT_TABLE, ha='center')

        # Weak levels
        ax.text(0.05, 0.25, 'Weak:', color=COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        if bar_data:
            weaks = [bar_data.d1_weak, bar_data.h4_weak, bar_data.h1_weak, bar_data.m15_weak]
            for i, val in enumerate(weaks):
                ax.text(x_positions[i], 0.25, format_price(val),
                       color=COLORS['bear'], fontsize=FONT_TABLE, ha='center')

    def _build_zone_results(self, ax: plt.Axes, zones: List[FilteredZone], ticker: str):
        """Build Zone Results table with Tier column (matching original)."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Headers (matching original chart_builder.py)
        headers = ['Zone ID', 'POC', 'High', 'Low', 'Rank', 'Tier', 'Score']
        x_positions = [0.10, 0.24, 0.36, 0.48, 0.60, 0.74, 0.88]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.88, header, color=COLORS['text_muted'],
                   fontsize=FONT_HEADER, ha='center', fontweight='bold')

        ax.axhline(0.84, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)

        # Data rows (max 6 zones)
        max_rows = min(6, len(zones) if zones else 0)
        row_height = 0.12

        for row_idx in range(max_rows):
            zone = zones[row_idx]
            y = 0.76 - (row_idx * row_height)

            # Shorten zone ID
            zone_id_short = zone.zone_id.replace(f'{ticker}_', '')
            ax.text(x_positions[0], y, zone_id_short, color=COLORS['text_primary'],
                   fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[1], y, format_price(zone.hvn_poc),
                   color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[2], y, format_price(zone.zone_high),
                   color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[3], y, format_price(zone.zone_low),
                   color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')

            # Rank with color (matching original: fontsize=10, fontweight='bold')
            rank_str = zone.rank.value if isinstance(zone.rank, Rank) else str(zone.rank)
            rank_color = RANK_COLORS.get(rank_str, COLORS['text_muted'])
            ax.text(x_positions[4], y, rank_str, color=rank_color,
                   fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

            # Tier with color (matching original: fontsize=10, fontweight='bold')
            tier_str = zone.tier.value if isinstance(zone.tier, Tier) else str(zone.tier)
            tier_color = get_tier_color(zone.tier)
            ax.text(x_positions[5], y, tier_str or '-', color=tier_color,
                   fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

            # Score
            ax.text(x_positions[6], y, f'{zone.score:.1f}',
                   color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')

            if row_idx < max_rows - 1:
                ax.axhline(y - row_height/2 + 0.02, color=COLORS['border'],
                          linewidth=0.5, xmin=0.02, xmax=0.98)

        if not zones or len(zones) == 0:
            ax.text(0.5, 0.5, 'No zones found', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', style='italic')

    def _build_setup_analysis(
        self, ax: plt.Axes,
        primary_setup: Optional[Setup],
        secondary_setup: Optional[Setup],
        ticker: str,
        filtered_zones: List[FilteredZone]
    ):
        """Build Setup Analysis table with tier and confluences display (matching original)."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Primary Setup (matching original: fontsize=10 for headers)
        ax.text(0.05, 0.90, 'PRIMARY:', color=COLORS['primary_blue'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if primary_setup and primary_setup.hvn_poc > 0:
            tier_color = get_tier_color(primary_setup.tier)
            zone_id_short = primary_setup.zone_id.replace(f'{ticker}_', '')

            primary_text = f"{primary_setup.direction.value} | Zone: {zone_id_short} | POC: {format_price(primary_setup.hvn_poc)}"
            ax.text(0.05, 0.80, primary_text, color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='left')

            # Show tier with color (matching original: fontsize=10)
            tier_str = primary_setup.tier.value if isinstance(primary_setup.tier, Tier) else str(primary_setup.tier)
            ax.text(0.95, 0.80, tier_str, color=tier_color, fontsize=FONT_TABLE_BOLD, ha='right', fontweight='bold')

            # Range and target (matching original: fontsize=9)
            range_text = f"Range: {format_price(primary_setup.zone_low)} - {format_price(primary_setup.zone_high)}"
            if primary_setup.target and primary_setup.target > 0:
                rr_str = f"{primary_setup.risk_reward:.2f}" if primary_setup.risk_reward else ""
                range_text += f" | Target: {format_price(primary_setup.target)} | {rr_str}"
            ax.text(0.05, 0.71, range_text, color=COLORS['text_muted'], fontsize=FONT_TABLE, ha='left')

            # Find and show confluences (matching original: fontsize=8)
            confluences = self._get_zone_confluences(primary_setup.zone_id, filtered_zones)
            if confluences:
                self._draw_wrapped_text(ax, f"Confluences: {confluences}",
                                       0.05, 0.62, COLORS['text_dim'], fontsize=FONT_LABEL, max_width=0.90)
        else:
            ax.text(0.05, 0.80, 'No primary setup', color=COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', style='italic')

        # Secondary Setup (matching original: fontsize=10 for headers)
        ax.text(0.05, 0.48, 'SECONDARY:', color=COLORS['secondary_red'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if secondary_setup and secondary_setup.hvn_poc > 0:
            tier_color = get_tier_color(secondary_setup.tier)
            zone_id_short = secondary_setup.zone_id.replace(f'{ticker}_', '')

            secondary_text = f"{secondary_setup.direction.value} | Zone: {zone_id_short} | POC: {format_price(secondary_setup.hvn_poc)}"
            ax.text(0.05, 0.38, secondary_text, color=COLORS['text_primary'], fontsize=FONT_TABLE, ha='left')

            # Show tier with color (matching original: fontsize=10)
            tier_str = secondary_setup.tier.value if isinstance(secondary_setup.tier, Tier) else str(secondary_setup.tier)
            ax.text(0.95, 0.38, tier_str, color=tier_color, fontsize=FONT_TABLE_BOLD, ha='right', fontweight='bold')

            # Range and target (matching original: fontsize=9)
            range_text = f"Range: {format_price(secondary_setup.zone_low)} - {format_price(secondary_setup.zone_high)}"
            if secondary_setup.target and secondary_setup.target > 0:
                rr_str = f"{secondary_setup.risk_reward:.2f}" if secondary_setup.risk_reward else ""
                range_text += f" | Target: {format_price(secondary_setup.target)} | {rr_str}"
            ax.text(0.05, 0.29, range_text, color=COLORS['text_muted'], fontsize=FONT_TABLE, ha='left')

            # Find and show confluences (matching original: fontsize=8)
            confluences = self._get_zone_confluences(secondary_setup.zone_id, filtered_zones)
            if confluences:
                self._draw_wrapped_text(ax, f"Confluences: {confluences}",
                                       0.05, 0.20, COLORS['text_dim'], fontsize=FONT_LABEL, max_width=0.90)
        else:
            ax.text(0.05, 0.38, 'No secondary setup', color=COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', style='italic')

    def _get_zone_confluences(self, zone_id: str, filtered_zones: List[FilteredZone]) -> str:
        """Get confluences string for a zone."""
        for zone in filtered_zones:
            if zone.zone_id == zone_id:
                return zone.confluences_str if hasattr(zone, 'confluences_str') else ", ".join(zone.confluences)
        return ""

    def _draw_wrapped_text(self, ax: plt.Axes, text: str, x: float, y: float,
                           color: str, fontsize: int = 8, max_width: float = 0.90,
                           line_height: float = 0.08):
        """Draw text with wrapping to multiple lines."""
        chars_per_line = int(60 * (max_width / 0.90) * (8 / fontsize))

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1
            if current_length + word_length <= chars_per_line:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        for i, line in enumerate(lines):
            ax.text(x, y - (i * line_height), line, color=color,
                   fontsize=fontsize, ha='left', va='top')

    def _build_notes(self, ax: plt.Axes, notes: str, hvn_result: HVNResult,
                     primary_setup: Optional[Setup], secondary_setup: Optional[Setup]):
        """Build Notes section with PineScript string (matching original)."""
        ax.set_facecolor(COLORS['notes_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(COLORS['border'])

        # Matching original: fontsize=10
        ax.text(0.02, 0.88, 'NOTES:', color=COLORS['text_muted'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if notes:
            # Matching original: fontsize=9
            ax.text(0.02, 0.55, notes, color=COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', va='center', style='italic', wrap=True)

        # Build and show PineScript string (matching original: fontsize=6)
        pinescript_string = self._build_pinescript_string(primary_setup, secondary_setup, hvn_result)
        if pinescript_string:
            display_str = pinescript_string
            if len(display_str) > 80:
                display_str = display_str[:77] + "..."
            ax.text(0.98, 0.12, f'PineScript: {display_str}', color=COLORS['text_dim'],
                   fontsize=6, ha='right', style='italic')

    def _build_pinescript_string(self, primary_setup: Optional[Setup],
                                  secondary_setup: Optional[Setup],
                                  hvn_result: HVNResult) -> str:
        """Build 16-value PineScript string."""
        # Setup values
        pri_high = primary_setup.zone_high if primary_setup else 0.0
        pri_low = primary_setup.zone_low if primary_setup else 0.0
        pri_target = primary_setup.target if primary_setup and primary_setup.target else 0.0

        sec_high = secondary_setup.zone_high if secondary_setup else 0.0
        sec_low = secondary_setup.zone_low if secondary_setup else 0.0
        sec_target = secondary_setup.target if secondary_setup and secondary_setup.target else 0.0

        values = [pri_high, pri_low, pri_target, sec_high, sec_low, sec_target]

        # Add 10 POCs
        if hvn_result:
            pocs = hvn_result.get_poc_prices()
            for i in range(10):
                values.append(pocs[i] if i < len(pocs) else 0.0)
        else:
            values.extend([0.0] * 10)

        return ",".join(f"{v:.2f}" if v != 0 else "0" for v in values)

    def _build_price_chart(
        self,
        ax: plt.Axes,
        candle_data: Optional[pd.DataFrame],
        primary_setup: Optional[Setup],
        secondary_setup: Optional[Setup],
        epoch_pocs: List[float],
        bar_data: BarData,
        hvn_result: HVNResult
    ) -> Tuple[float, float]:
        """Build H1 candlestick chart with zones and POC lines (matching original)."""
        ax.set_facecolor(COLORS['dark_bg'])

        # If no candle data, show placeholder
        if candle_data is None or candle_data.empty:
            ax.text(0.5, 0.5, 'No chart data available', color=COLORS['text_muted'],
                   fontsize=14, ha='center', va='center')

            # Use HVN range if available
            if hvn_result and hvn_result.price_range_low and hvn_result.price_range_high:
                y_min = hvn_result.price_range_low
                y_max = hvn_result.price_range_high
            elif bar_data:
                y_min = bar_data.price * 0.95
                y_max = bar_data.price * 1.05
            else:
                return (0, 100)

            self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, 100, -3, y_min, y_max)
            ax.set_xlim(0, 100)
            ax.set_ylim(y_min, y_max)
            return (y_min, y_max)

        n_bars = len(candle_data)

        # Calculate candle body half-width (matching original: 0.3 half-width = 0.6 full)
        body_half_width = 0.3

        # Plot candlesticks (matching original)
        for i, (idx, bar) in enumerate(candle_data.iterrows()):
            color = COLORS['candle_green'] if bar['close'] >= bar['open'] else COLORS['candle_red']

            # Wick (matching original: linewidth=0.8)
            ax.plot([i, i], [bar['low'], bar['high']], color=color, linewidth=0.8)

            # Body (matching original: 0.6 width)
            body_bottom = min(bar['open'], bar['close'])
            body_height = abs(bar['close'] - bar['open'])
            if body_height < 0.01:
                body_height = 0.01
            rect = mpatches.Rectangle(
                (i - body_half_width, body_bottom), 0.6, body_height,
                facecolor=color, edgecolor=color
            )
            ax.add_patch(rect)

        # Y-axis limits - use epoch range
        if hvn_result and hvn_result.price_range_low and hvn_result.price_range_high:
            y_min = hvn_result.price_range_low
            y_max = hvn_result.price_range_high
        else:
            y_min = candle_data['low'].min()
            y_max = candle_data['high'].max()

        # Extend to include targets if outside range
        if primary_setup and primary_setup.target and primary_setup.target > 0:
            y_max = max(y_max, primary_setup.target)
            y_min = min(y_min, primary_setup.target)
        if secondary_setup and secondary_setup.target and secondary_setup.target > 0:
            y_max = max(y_max, secondary_setup.target)
            y_min = min(y_min, secondary_setup.target)

        # Add padding
        padding = (y_max - y_min) * YAXIS_PADDING_PCT
        y_min -= padding
        y_max += padding

        # Draw zone overlays (matching original: label_offset=-3)
        self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, n_bars, -3, y_min, y_max)

        # Chart formatting (matching original: xlim with +15 padding)
        ax.set_xlim(-2, n_bars + 15)
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel('Price ($)', color=COLORS['text_primary'], fontsize=FONT_AXIS_LABEL)
        ax.tick_params(colors=COLORS['text_primary'], labelsize=FONT_AXIS)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(COLORS['border_light'])

        # X-axis time labels (matching original)
        if hasattr(candle_data.index, 'strftime'):
            tick_interval = max(1, n_bars // 8)
            tick_positions = list(range(0, n_bars, tick_interval))
            tick_labels = [candle_data.index[i].strftime('%m/%d %H:%M')
                          for i in tick_positions if i < n_bars]
            ax.set_xticks(tick_positions[:len(tick_labels)])
            ax.set_xticklabels(tick_labels, color=COLORS['text_primary'],
                              fontsize=FONT_LABEL, rotation=45, ha='right')
        ax.set_xlabel('Time (ET)', color=COLORS['text_primary'], fontsize=FONT_TABLE_BOLD)

        return (y_min, y_max)

    def _draw_zone_overlays(
        self, ax: plt.Axes,
        primary_setup: Optional[Setup],
        secondary_setup: Optional[Setup],
        epoch_pocs: List[float],
        n_bars: int,
        label_offset: float,
        y_min: float,
        y_max: float
    ):
        """Draw zone overlays, POC lines, and target lines (matching original)."""
        # Primary Zone (Blue)
        if primary_setup and primary_setup.zone_high > 0 and primary_setup.zone_low > 0:
            ax.axhspan(
                primary_setup.zone_low, primary_setup.zone_high,
                alpha=ZONE_FILL_ALPHA, color=COLORS['primary_blue'], zorder=1
            )
            poc = primary_setup.hvn_poc
            ax.axhline(poc, color=COLORS['primary_blue'], linewidth=1.5, alpha=0.8)

            # POC label (matching original: fontsize=8)
            ax.text(label_offset, poc, f'${poc:.2f}',
                   color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))

            # Target line
            if primary_setup.target and primary_setup.target > 0:
                ax.axhline(primary_setup.target, color=COLORS['primary_blue'],
                          linestyle='-', linewidth=2, alpha=0.9)
                # Target label (matching original)
                ax.text(label_offset, primary_setup.target, f'${primary_setup.target:.2f}',
                       color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                       fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))

        # Secondary Zone (Red)
        if secondary_setup and secondary_setup.zone_high > 0 and secondary_setup.zone_low > 0:
            ax.axhspan(
                secondary_setup.zone_low, secondary_setup.zone_high,
                alpha=ZONE_FILL_ALPHA, color=COLORS['secondary_red'], zorder=1
            )
            poc = secondary_setup.hvn_poc
            ax.axhline(poc, color=COLORS['secondary_red'], linewidth=1.5, alpha=0.8)

            # POC label (matching original: fontsize=8)
            ax.text(label_offset, poc, f'${poc:.2f}',
                   color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                   bbox=dict(boxstyle='round,pad=0.2',
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))

            # Target line
            if secondary_setup.target and secondary_setup.target > 0:
                ax.axhline(secondary_setup.target, color=COLORS['secondary_red'],
                          linestyle='-', linewidth=2, alpha=0.9)
                # Target label (matching original)
                ax.text(label_offset, secondary_setup.target, f'${secondary_setup.target:.2f}',
                       color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                       fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))

        # Build set of prices to skip (colored setup POCs and targets already drawn)
        skip_prices = set()
        price_tolerance = 0.01  # Skip if within $0.01 of a colored line

        if primary_setup:
            if primary_setup.hvn_poc and primary_setup.hvn_poc > 0:
                skip_prices.add(round(primary_setup.hvn_poc, 2))
            if primary_setup.target and primary_setup.target > 0:
                skip_prices.add(round(primary_setup.target, 2))

        if secondary_setup:
            if secondary_setup.hvn_poc and secondary_setup.hvn_poc > 0:
                skip_prices.add(round(secondary_setup.hvn_poc, 2))
            if secondary_setup.target and secondary_setup.target > 0:
                skip_prices.add(round(secondary_setup.target, 2))

        # POC lines from HVN calculation (matching original: fontsize=7)
        # Skip any POC that overlaps with setup zones or targets
        for i, poc_price in enumerate(epoch_pocs):
            if poc_price > 0 and y_min <= poc_price <= y_max:
                # Check if this POC overlaps with a colored line
                poc_rounded = round(poc_price, 2)
                should_skip = any(
                    abs(poc_rounded - skip_price) < price_tolerance
                    for skip_price in skip_prices
                )

                if should_skip:
                    continue  # Skip this grey POC line - colored line already drawn

                rank = i + 1
                ax.axhline(poc_price, color=POC_LINE_COLOR, linestyle=POC_LINE_STYLE,
                          linewidth=1.0, alpha=POC_LINE_ALPHA, zorder=2)

                # POC label on left side (matching original)
                ax.text(label_offset, poc_price, f'POC{rank}: ${poc_price:.2f}',
                       color=POC_LINE_COLOR, fontsize=FONT_POC_LABEL, va='center', ha='right',
                       alpha=0.8, bbox=dict(boxstyle='round,pad=0.15',
                       facecolor=COLORS['dark_bg'], edgecolor=POC_LINE_COLOR,
                       alpha=0.5, linewidth=0.5))

    def _build_volume_profile(
        self, ax: plt.Axes,
        volume_profile: Optional[Dict[float, float]],
        y_limits: Tuple[float, float]
    ):
        """Build Volume Profile sidebar (matching original)."""
        ax.set_facecolor(COLORS['dark_bg'])

        if not volume_profile:
            ax.text(0.5, 0.5, 'No VP', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return

        # Filter to y_limits range
        y_min, y_max = y_limits
        filtered_vp = {p: v for p, v in volume_profile.items() if y_min <= p <= y_max}

        if not filtered_vp:
            ax.text(0.5, 0.5, 'No VP in range', color=COLORS['text_muted'],
                   fontsize=10, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return

        # Sort by price
        sorted_prices = sorted(filtered_vp.keys())
        volumes = [filtered_vp[p] for p in sorted_prices]

        # Bar height at $0.01 fidelity (matching original)
        bar_height = 0.01

        ax.barh(sorted_prices, volumes, height=bar_height,
               color=VBP_COLOR, alpha=0.8, edgecolor='none')

        # Matching original: fontsize=9
        ax.set_xlabel('Volume', color=COLORS['text_primary'], fontsize=FONT_TABLE)
        ax.tick_params(colors=COLORS['text_primary'], labelleft=False, labelsize=FONT_LABEL)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(COLORS['border_light'])

        ax.set_ylim(y_limits)

    def to_bytes(self) -> bytes:
        """Convert current figure to PNG bytes."""
        if self.fig is None:
            return b''

        buf = io.BytesIO()
        self.fig.savefig(
            buf, format='png', dpi=DPI, facecolor=COLORS['dark_bg'],
            edgecolor='none', bbox_inches='tight'
        )
        buf.seek(0)
        return buf.getvalue()

    def close(self):
        """Close the figure to free memory."""
        if self.fig:
            plt.close(self.fig)
            self.fig = None


# =============================================================================
# STREAMLIT PAGE
# =============================================================================

def fetch_chart_data(
    ticker: str,
    anchor_date: date,
    end_timestamp: datetime = None
) -> Tuple[pd.DataFrame, Dict[float, float], float, float]:
    """
    Fetch H1 candle data and volume profile from Polygon.

    Args:
        ticker: Stock symbol
        anchor_date: Epoch start date
        end_timestamp: Optional precise end timestamp for pre/post market mode.
                      If provided, data is filtered to only include bars
                      before this timestamp.

    Returns:
        Tuple of (candle_data, volume_profile, epoch_low, epoch_high)
    """
    from math import floor, ceil

    try:
        client = PolygonClient()

        # Fetch H1 candles (recent bars for display)
        end_date = date.today()
        # For H1 bars, we need about 40 days of data for 120 bars
        start_date = end_date - timedelta(days=60)

        candle_data = client.fetch_hourly_bars(
            ticker=ticker,
            start_date=start_date,
            end_timestamp=end_timestamp  # Pass market time mode cutoff
        )

        # Get recent candles only
        if candle_data is not None and not candle_data.empty:
            candle_data = candle_data.tail(CANDLE_BAR_COUNT)
            # Set timestamp as index for chart display
            if 'timestamp' in candle_data.columns:
                candle_data = candle_data.set_index('timestamp')

        # Fetch M15 bars for volume profile (full epoch)
        vbp_data = client.fetch_minute_bars_chunked(
            ticker=ticker,
            start_date=anchor_date,
            multiplier=VBP_TIMEFRAME,
            chunk_days=10,
            end_timestamp=end_timestamp  # Pass market time mode cutoff
        )

        # Calculate epoch high/low and build volume profile
        epoch_low = 0.0
        epoch_high = 0.0
        volume_profile = {}

        if vbp_data is not None and not vbp_data.empty:
            epoch_low = vbp_data['low'].min()
            epoch_high = vbp_data['high'].max()

            # Build volume profile at $0.01 granularity
            for _, bar in vbp_data.iterrows():
                bar_low = bar['low']
                bar_high = bar['high']
                bar_volume = bar['volume']

                if bar_volume <= 0 or bar_high <= bar_low:
                    continue

                low_level = floor(bar_low / 0.01) * 0.01
                high_level = ceil(bar_high / 0.01) * 0.01
                num_levels = int(round((high_level - low_level) / 0.01)) + 1

                if num_levels <= 0:
                    continue

                volume_per_level = bar_volume / num_levels

                current = low_level
                for _ in range(num_levels):
                    price_key = round(current, 2)
                    volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                    current += 0.01

        return candle_data, volume_profile, epoch_low, epoch_high

    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        return pd.DataFrame(), {}, 0.0, 0.0


def render_single_report(
    result: dict,
    index_structures: List[Dict],
    report_index: int,
    total_reports: int,
    end_timestamp: datetime = None
):
    """
    Render a single ticker report.

    Args:
        result: Analysis result dict
        index_structures: List of index structures for Market Structure table
        report_index: Index of this report in the list
        total_reports: Total number of reports
        end_timestamp: Optional market time cutoff for data fetching
    """
    ticker = result.get("ticker")
    market_structure = result.get("market_structure")
    bar_data = result.get("bar_data")
    hvn_result = result.get("hvn_result")
    filtered_zones = result.get("filtered_zones", [])
    primary_setup = result.get("primary_setup")
    secondary_setup = result.get("secondary_setup")
    anchor_date = hvn_result.start_date if hvn_result else None

    # Fetch live chart data (respecting market time mode cutoff)
    candle_data = None
    volume_profile = None

    if anchor_date:
        with st.spinner(f"Fetching data for {ticker}..."):
            candle_data, volume_profile, epoch_low, epoch_high = fetch_chart_data(
                ticker, anchor_date, end_timestamp
            )
            # Update HVN result with epoch range
            if hvn_result and epoch_low > 0 and epoch_high > 0:
                hvn_result.price_range_low = epoch_low
                hvn_result.price_range_high = epoch_high

    # Build and display chart
    try:
        builder = PreMarketChartBuilder()

        fig = builder.build(
            ticker=ticker,
            anchor_date=anchor_date,
            market_structure=market_structure,
            bar_data=bar_data,
            hvn_result=hvn_result,
            filtered_zones=filtered_zones,
            primary_setup=primary_setup,
            secondary_setup=secondary_setup,
            candle_data=candle_data,
            volume_profile=volume_profile,
            index_structures=index_structures,
            notes=""
        )

        # Display as high-quality PNG image (avoids st.pyplot fuzziness)
        img_bytes = builder.to_bytes()
        st.image(img_bytes, use_container_width=True)

        # Clean up
        builder.close()

    except Exception as e:
        st.error(f"Error generating report for {ticker}: {str(e)}")
        logger.exception(f"Pre-market report generation failed for {ticker}")

    # Visual separator between reports
    if report_index < total_reports - 1:
        st.markdown("---")


def render_pre_market_report():
    """
    Render scrollable pre-market reports for all analyzed tickers.
    Shows SPY, QQQ, DIA first (prior month), then all custom tickers.
    Each report fits on an 8.5x11 landscape page.
    Fetches chart data respecting market time mode (Pre-Market/Post-Market/Live).
    """
    from core.state_manager import get_market_end_timestamp, get_market_time_mode
    from datetime import date

    st.header("Pre-Market Reports")

    # Get market time mode settings
    analysis_date = date.today()
    end_timestamp = get_market_end_timestamp(analysis_date)
    market_mode = get_market_time_mode()

    # Show market time mode in header
    if end_timestamp:
        st.caption(f"Market Time Mode: {market_mode} (cutoff: {end_timestamp.strftime('%H:%M ET')})")
    else:
        st.caption(f"Market Time Mode: {market_mode}")

    # Check if we have analysis results
    results = st.session_state.get("analysis_results", {})

    if not results:
        st.info("No analysis results available. Run analysis first to generate pre-market reports.")
        return

    # Get both index and custom results
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    # Successful results
    successful_custom = [r for r in custom_results if r.get("success")]
    successful_index = [r for r in index_results if r.get("success")]

    # Combine: index tickers first, then custom tickers
    all_reports = successful_index + successful_custom

    if not all_reports:
        st.warning("No successful analysis results to visualize.")
        return

    # Build index structures for Market Structure table (shared across all reports)
    index_structures = []
    for idx_result in successful_index:
        ms = idx_result.get("market_structure")
        if ms:
            index_structures.append({
                'ticker': ms.ticker,
                'd1_dir': ms.d1.direction.value if ms.d1 else '-',
                'h4_dir': ms.h4.direction.value if ms.h4 else '-',
                'h1_dir': ms.h1.direction.value if ms.h1 else '-',
                'm15_dir': ms.m15.direction.value if ms.m15 else '-',
                'composite': ms.composite.value if ms.composite else '-'
            })

    # Show count
    total_reports = len(all_reports)
    st.caption(f"Generating {total_reports} report(s): {len(successful_index)} index + {len(successful_custom)} custom")

    # Generate and display each ticker's report (respecting market time mode)
    for i, result in enumerate(all_reports):
        render_single_report(result, index_structures, i, total_reports, end_timestamp)


# Entry point for the page
if __name__ == "__main__":
    render_pre_market_report()
