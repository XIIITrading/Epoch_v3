"""
Chart Builder for Epoch Analysis Tool.

Creates visualization charts using matplotlib with:
- H1 candlestick chart with zone overlays
- POC lines from HVN calculation
- Volume profile sidebar
- Market structure and setup info tables

Ported from 02_zone_system/08_visualization/charts/chart_builder.py
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Streamlit

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import io
import logging

# Increase PIL's pixel limit to avoid DecompressionBombWarning
# This is safe because we control the image generation
from PIL import Image
Image.MAX_IMAGE_PIXELS = 200_000_000  # 200 million pixels (up from 89 million)

from config.visualization_config import (
    COLORS, RANK_COLORS, TIER_COLORS, ZONE_FILL_ALPHA,
    FIGURE_WIDTH, FIGURE_HEIGHT, DPI,
    PREVIEW_FIGURE_WIDTH, PREVIEW_FIGURE_HEIGHT, PREVIEW_DPI,
    TABLE_HEIGHT_RATIOS, VBP_COLOR,
    POC_LINE_STYLE, POC_LINE_COLOR, POC_LINE_ALPHA,
    YAXIS_PADDING_PCT, CANDLE_BAR_COUNT
)
from core.data_models import (
    MarketStructure, BarData, HVNResult, FilteredZone,
    Setup, Direction, Tier, Rank
)

logger = logging.getLogger(__name__)


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
# CHART BUILDER CLASS
# =============================================================================

class AnalysisChartBuilder:
    """Build visualization charts for analysis results."""

    def __init__(self):
        """Initialize chart builder."""
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
        notes: str = "",
        preview_mode: bool = False
    ) -> plt.Figure:
        """
        Build complete visualization figure.

        Args:
            ticker: Ticker symbol
            anchor_date: Epoch anchor date
            market_structure: Market structure data
            bar_data: Bar data with levels
            hvn_result: HVN POC calculation result
            filtered_zones: List of filtered zones
            primary_setup: Primary setup (or None)
            secondary_setup: Secondary setup (or None)
            candle_data: DataFrame with H1 OHLC data (optional)
            volume_profile: Dict of price -> volume (optional)
            notes: User notes text
            preview_mode: If True, use smaller dimensions for web preview

        Returns:
            matplotlib Figure object
        """
        # Select dimensions based on mode
        if preview_mode:
            fig_width = PREVIEW_FIGURE_WIDTH
            fig_height = PREVIEW_FIGURE_HEIGHT
            fig_dpi = PREVIEW_DPI
        else:
            fig_width = FIGURE_WIDTH
            fig_height = FIGURE_HEIGHT
            fig_dpi = DPI

        # Create figure
        self.fig = plt.figure(
            figsize=(fig_width, fig_height),
            facecolor=COLORS['dark_bg'],
            dpi=fig_dpi
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
        self._build_market_structure(self.fig.add_subplot(left_gs[0]), market_structure)
        self._build_ticker_structure(self.fig.add_subplot(left_gs[1]), market_structure, bar_data)
        self._build_zone_results(self.fig.add_subplot(left_gs[2]), filtered_zones, ticker)
        self._build_setup_analysis(
            self.fig.add_subplot(left_gs[3]),
            primary_setup, secondary_setup, ticker
        )
        self._build_notes(self.fig.add_subplot(left_gs[4]), notes, hvn_result)

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
        composite = market_structure.composite.value if market_structure else "N/A"

        self.fig.suptitle(
            f'{ticker} | Analysis Report | {date_str} | Composite: {composite}',
            color=COLORS['text_primary'], fontsize=16, fontweight='bold', y=0.97
        )

        # Subtitle with epoch info
        price = bar_data.price if bar_data else 0
        atr = bar_data.d1_atr if bar_data else 0
        anchor_str = anchor_date.strftime('%Y-%m-%d') if anchor_date else "N/A"

        self.fig.text(
            0.5, 0.935,
            f'Current: ${price:.2f} | D1 ATR: ${atr:.2f} | Anchor Date: {anchor_str}',
            color=COLORS['text_muted'], fontsize=11, ha='center'
        )

        return self.fig

    def _build_market_structure(self, ax: plt.Axes, market_structure: MarketStructure):
        """Build Market Structure table (index tickers display)."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Title
        ax.text(0.5, 0.90, 'MARKET STRUCTURE', color=COLORS['text_muted'],
                fontsize=10, ha='center', fontweight='bold')

        # Headers
        headers = ['Ticker', 'D1', 'H4', 'H1', 'M15', 'Comp']
        x_positions = [0.08, 0.22, 0.36, 0.50, 0.64, 0.82]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.70, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')

        # Data row for current ticker
        if market_structure:
            y = 0.45
            values = [
                market_structure.ticker,
                market_structure.d1.direction.value if market_structure.d1 else "-",
                market_structure.h4.direction.value if market_structure.h4 else "-",
                market_structure.h1.direction.value if market_structure.h1 else "-",
                market_structure.m15.direction.value if market_structure.m15 else "-",
                market_structure.composite.value if market_structure.composite else "-"
            ]

            for col_idx, val in enumerate(values):
                color = get_direction_color(val) if col_idx > 0 else COLORS['text_primary']
                ax.text(x_positions[col_idx], y, str(val), color=color,
                       fontsize=10, ha='center', va='center')

    def _build_ticker_structure(self, ax: plt.Axes, market_structure: MarketStructure, bar_data: BarData):
        """Build Ticker Structure table with strong/weak levels."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Column positions
        x_positions = [0.22, 0.36, 0.50, 0.64, 0.82]
        tf_labels = ['D1', 'H4', 'H1', 'M15', 'Comp']

        # Headers
        ax.text(0.05, 0.75, 'Direction:', color=COLORS['text_muted'], fontsize=9, ha='left')
        for i, tf in enumerate(tf_labels):
            ax.text(x_positions[i], 0.82, tf, color=COLORS['text_muted'], fontsize=8, ha='center')

        # Direction values
        if market_structure:
            directions = [
                market_structure.d1.direction.value,
                market_structure.h4.direction.value,
                market_structure.h1.direction.value,
                market_structure.m15.direction.value,
                market_structure.composite.value
            ]
            for i, dir_val in enumerate(directions):
                color = get_direction_color(dir_val)
                ax.text(x_positions[i], 0.65, str(dir_val) if dir_val else "-",
                       color=color, fontsize=10, ha='center', fontweight='bold')

        # Strong levels
        ax.text(0.05, 0.45, 'Strong:', color=COLORS['text_muted'], fontsize=9, ha='left')
        if bar_data:
            strongs = [bar_data.d1_strong, bar_data.h4_strong, bar_data.h1_strong, bar_data.m15_strong]
            for i, val in enumerate(strongs):
                ax.text(x_positions[i], 0.45, format_price(val),
                       color=COLORS['bull'], fontsize=9, ha='center')

        # Weak levels
        ax.text(0.05, 0.25, 'Weak:', color=COLORS['text_muted'], fontsize=9, ha='left')
        if bar_data:
            weaks = [bar_data.d1_weak, bar_data.h4_weak, bar_data.h1_weak, bar_data.m15_weak]
            for i, val in enumerate(weaks):
                ax.text(x_positions[i], 0.25, format_price(val),
                       color=COLORS['bear'], fontsize=9, ha='center')

    def _build_zone_results(self, ax: plt.Axes, zones: List[FilteredZone], ticker: str):
        """Build Zone Results table with Tier column."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Headers
        headers = ['Zone ID', 'POC', 'High', 'Low', 'Rank', 'Tier', 'Score']
        x_positions = [0.10, 0.24, 0.36, 0.48, 0.60, 0.74, 0.88]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.88, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')

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
                   fontsize=9, ha='center')
            ax.text(x_positions[1], y, format_price(zone.hvn_poc),
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            ax.text(x_positions[2], y, format_price(zone.zone_high),
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            ax.text(x_positions[3], y, format_price(zone.zone_low),
                   color=COLORS['text_primary'], fontsize=9, ha='center')

            # Rank with color
            rank_str = zone.rank.value if isinstance(zone.rank, Rank) else str(zone.rank)
            rank_color = RANK_COLORS.get(rank_str, COLORS['text_muted'])
            ax.text(x_positions[4], y, rank_str, color=rank_color,
                   fontsize=10, ha='center', fontweight='bold')

            # Tier with color
            tier_str = zone.tier.value if isinstance(zone.tier, Tier) else str(zone.tier)
            tier_color = get_tier_color(zone.tier)
            ax.text(x_positions[5], y, tier_str or '-', color=tier_color,
                   fontsize=10, ha='center', fontweight='bold')

            # Score
            ax.text(x_positions[6], y, f'{zone.score:.1f}',
                   color=COLORS['text_primary'], fontsize=9, ha='center')

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
        ticker: str
    ):
        """Build Setup Analysis table with tier display."""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Primary Setup
        ax.text(0.05, 0.90, 'PRIMARY:', color=COLORS['primary_blue'],
                fontsize=10, fontweight='bold', ha='left')

        if primary_setup and primary_setup.hvn_poc > 0:
            tier_color = get_tier_color(primary_setup.tier)
            zone_id_short = primary_setup.zone_id.replace(f'{ticker}_', '')

            primary_text = f"{primary_setup.direction.value} | Zone: {zone_id_short} | POC: {format_price(primary_setup.hvn_poc)}"
            ax.text(0.05, 0.78, primary_text, color=COLORS['text_primary'], fontsize=9, ha='left')

            # Show tier with color
            tier_str = primary_setup.tier.value if isinstance(primary_setup.tier, Tier) else str(primary_setup.tier)
            ax.text(0.95, 0.78, tier_str, color=tier_color, fontsize=10, ha='right', fontweight='bold')

            # Range and target
            range_text = f"Range: {format_price(primary_setup.zone_low)} - {format_price(primary_setup.zone_high)}"
            if primary_setup.target:
                rr_str = f"{primary_setup.risk_reward:.1f}R" if primary_setup.risk_reward else ""
                range_text += f" | Target: {format_price(primary_setup.target)} | {rr_str}"
            ax.text(0.05, 0.66, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')
        else:
            ax.text(0.05, 0.78, 'No primary setup', color=COLORS['text_dim'],
                   fontsize=9, ha='left', style='italic')

        # Secondary Setup
        ax.text(0.05, 0.48, 'SECONDARY:', color=COLORS['secondary_red'],
                fontsize=10, fontweight='bold', ha='left')

        if secondary_setup and secondary_setup.hvn_poc > 0:
            tier_color = get_tier_color(secondary_setup.tier)
            zone_id_short = secondary_setup.zone_id.replace(f'{ticker}_', '')

            secondary_text = f"{secondary_setup.direction.value} | Zone: {zone_id_short} | POC: {format_price(secondary_setup.hvn_poc)}"
            ax.text(0.05, 0.36, secondary_text, color=COLORS['text_primary'], fontsize=9, ha='left')

            # Show tier with color
            tier_str = secondary_setup.tier.value if isinstance(secondary_setup.tier, Tier) else str(secondary_setup.tier)
            ax.text(0.95, 0.36, tier_str, color=tier_color, fontsize=10, ha='right', fontweight='bold')

            # Range and target
            range_text = f"Range: {format_price(secondary_setup.zone_low)} - {format_price(secondary_setup.zone_high)}"
            if secondary_setup.target:
                rr_str = f"{secondary_setup.risk_reward:.1f}R" if secondary_setup.risk_reward else ""
                range_text += f" | Target: {format_price(secondary_setup.target)} | {rr_str}"
            ax.text(0.05, 0.24, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')
        else:
            ax.text(0.05, 0.36, 'No secondary setup', color=COLORS['text_dim'],
                   fontsize=9, ha='left', style='italic')

    def _build_notes(self, ax: plt.Axes, notes: str, hvn_result: HVNResult):
        """Build Notes section with epoch info."""
        ax.set_facecolor(COLORS['notes_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(COLORS['border'])

        ax.text(0.02, 0.88, 'NOTES:', color=COLORS['text_muted'],
                fontsize=10, fontweight='bold', ha='left')

        if notes:
            ax.text(0.02, 0.55, notes, color=COLORS['text_dim'],
                   fontsize=9, ha='left', va='center', style='italic', wrap=True)

        # Show epoch info
        if hvn_result:
            epoch_info = f"Epoch: {hvn_result.start_date} to {hvn_result.end_date} | Bars: {hvn_result.bars_analyzed}"
            ax.text(0.98, 0.12, epoch_info, color=COLORS['text_dim'],
                   fontsize=7, ha='right', style='italic')

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
        """Build H1 candlestick chart with zones and POC lines. Returns y-limits."""
        ax.set_facecolor(COLORS['dark_bg'])

        # If no candle data, show placeholder
        if candle_data is None or candle_data.empty:
            ax.text(0.5, 0.5, 'No chart data available', color=COLORS['text_muted'],
                   fontsize=14, ha='center', va='center')

            # Use HVN range if available, else bar data range
            if hvn_result and hvn_result.price_range_low and hvn_result.price_range_high:
                y_min = hvn_result.price_range_low
                y_max = hvn_result.price_range_high
            elif bar_data:
                y_min = bar_data.price * 0.95
                y_max = bar_data.price * 1.05
            else:
                return (0, 100)

            # Draw zone overlays even without candles
            self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, 0, 100)
            ax.set_xlim(0, 100)
            ax.set_ylim(y_min, y_max)
            return (y_min, y_max)

        n_bars = len(candle_data)

        # Plot candlesticks
        for i, (idx, bar) in enumerate(candle_data.iterrows()):
            color = COLORS['candle_green'] if bar['close'] >= bar['open'] else COLORS['candle_red']

            # Wick
            ax.plot([i, i], [bar['low'], bar['high']], color=color, linewidth=0.8)

            # Body
            body_bottom = min(bar['open'], bar['close'])
            body_height = abs(bar['close'] - bar['open'])
            if body_height < 0.01:
                body_height = 0.01
            rect = mpatches.Rectangle(
                (i - 0.3, body_bottom), 0.6, body_height,
                facecolor=color, edgecolor=color
            )
            ax.add_patch(rect)

        # Draw zone overlays
        self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, n_bars, -3)

        # Y-axis limits
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

        # Chart formatting
        ax.set_xlim(-2, n_bars + 15)
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel('Price ($)', color=COLORS['text_primary'], fontsize=11)
        ax.tick_params(colors=COLORS['text_primary'], labelsize=9)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(COLORS['border_light'])

        # X-axis time labels
        if hasattr(candle_data.index, 'strftime'):
            tick_interval = max(1, n_bars // 8)
            tick_positions = list(range(0, n_bars, tick_interval))
            tick_labels = [candle_data.index[i].strftime('%m/%d %H:%M')
                          for i in tick_positions if i < n_bars]
            ax.set_xticks(tick_positions[:len(tick_labels)])
            ax.set_xticklabels(tick_labels, color=COLORS['text_primary'],
                              fontsize=8, rotation=45, ha='right')
        ax.set_xlabel('Time (ET)', color=COLORS['text_primary'], fontsize=10)

        return (y_min, y_max)

    def _draw_zone_overlays(
        self, ax: plt.Axes,
        primary_setup: Optional[Setup],
        secondary_setup: Optional[Setup],
        epoch_pocs: List[float],
        n_bars: int,
        label_offset: float
    ):
        """Draw zone overlays, POC lines, and target lines."""
        # Primary Zone (Blue)
        if primary_setup and primary_setup.zone_high > 0 and primary_setup.zone_low > 0:
            ax.axhspan(
                primary_setup.zone_low, primary_setup.zone_high,
                alpha=ZONE_FILL_ALPHA, color=COLORS['primary_blue'], zorder=1
            )
            poc = primary_setup.hvn_poc
            ax.axhline(poc, color=COLORS['primary_blue'], linewidth=1.5, alpha=0.8)

            # Target line
            if primary_setup.target and primary_setup.target > 0:
                ax.axhline(primary_setup.target, color=COLORS['primary_blue'],
                          linestyle='-', linewidth=2, alpha=0.9)

        # Secondary Zone (Red)
        if secondary_setup and secondary_setup.zone_high > 0 and secondary_setup.zone_low > 0:
            ax.axhspan(
                secondary_setup.zone_low, secondary_setup.zone_high,
                alpha=ZONE_FILL_ALPHA, color=COLORS['secondary_red'], zorder=1
            )
            poc = secondary_setup.hvn_poc
            ax.axhline(poc, color=COLORS['secondary_red'], linewidth=1.5, alpha=0.8)

            # Target line
            if secondary_setup.target and secondary_setup.target > 0:
                ax.axhline(secondary_setup.target, color=COLORS['secondary_red'],
                          linestyle='-', linewidth=2, alpha=0.9)

        # POC lines from HVN calculation
        for i, poc_price in enumerate(epoch_pocs):
            if poc_price > 0:
                ax.axhline(poc_price, color=POC_LINE_COLOR, linestyle=POC_LINE_STYLE,
                          linewidth=1.0, alpha=POC_LINE_ALPHA, zorder=2)

    def _build_volume_profile(
        self, ax: plt.Axes,
        volume_profile: Optional[Dict[float, float]],
        y_limits: Tuple[float, float]
    ):
        """Build Volume Profile sidebar."""
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

        # Bar height at $0.01 fidelity
        bar_height = 0.01

        ax.barh(sorted_prices, volumes, height=bar_height,
               color=VBP_COLOR, alpha=0.8, edgecolor='none')

        ax.set_xlabel('Volume', color=COLORS['text_primary'], fontsize=9)
        ax.tick_params(colors=COLORS['text_primary'], labelleft=False, labelsize=8)

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

    def save(self, filepath: str):
        """Save current figure to file."""
        if self.fig is None:
            return

        self.fig.savefig(
            filepath, dpi=DPI, facecolor=COLORS['dark_bg'],
            edgecolor='none', bbox_inches='tight'
        )

    def close(self):
        """Close the figure to free memory."""
        if self.fig:
            plt.close(self.fig)
            self.fig = None


def build_analysis_chart(result: Dict[str, Any], preview_mode: bool = True) -> Optional[plt.Figure]:
    """
    Convenience function to build chart from pipeline result dict.

    Args:
        result: Result dictionary from PipelineRunner
        preview_mode: If True (default), use smaller dimensions for web preview.
                     Set to False for full-resolution PDF export.

    Returns:
        matplotlib Figure or None if failed
    """
    if not result.get("success"):
        return None

    builder = AnalysisChartBuilder()

    try:
        fig = builder.build(
            ticker=result["ticker"],
            anchor_date=result.get("hvn_result").start_date if result.get("hvn_result") else None,
            market_structure=result.get("market_structure"),
            bar_data=result.get("bar_data"),
            hvn_result=result.get("hvn_result"),
            filtered_zones=result.get("filtered_zones", []),
            primary_setup=result.get("primary_setup"),
            secondary_setup=result.get("secondary_setup"),
            candle_data=None,  # Will be fetched separately if needed
            volume_profile=None,  # Will be fetched separately if needed
            preview_mode=preview_mode
        )
        return fig
    except Exception as e:
        logger.error(f"Failed to build chart for {result.get('ticker')}: {e}")
        return None
