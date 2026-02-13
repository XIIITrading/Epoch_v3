"""
Pre-Market Report Tab
Epoch Trading System v2.0 - XIII Trading LLC

Full pre-market visualization with candlestick charts and volume profile.
Matches the PDF report layout from V1.
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import io
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QScrollArea, QSizePolicy,
    QDialog, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImageReader, QImage

# Disable Qt's image allocation limit to handle full-resolution charts
QImageReader.setAllocationLimit(0)  # 0 = no limit

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from visualization_config import (
    VIZ_COLORS, RANK_COLORS, TIER_COLORS, ZONE_FILL_ALPHA,
    VBP_COLOR, POC_LINE_STYLE, POC_LINE_COLOR, POC_LINE_ALPHA,
    YAXIS_PADDING_PCT, CANDLE_BAR_COUNT, VBP_TIMEFRAME,
    FIGURE_WIDTH, FIGURE_HEIGHT, DPI, TABLE_HEIGHT_RATIOS,
    PREVIEW_FIGURE_WIDTH, PREVIEW_FIGURE_HEIGHT, PREVIEW_DPI,
    FONT_TITLE, FONT_SUBTITLE, FONT_HEADER, FONT_TABLE, FONT_TABLE_BOLD,
    FONT_LABEL, FONT_AXIS, FONT_AXIS_LABEL, FONT_POC_LABEL
)

# Increase PIL's pixel limit to avoid DecompressionBombWarning
# This is safe because we control the image generation
from PIL import Image
Image.MAX_IMAGE_PIXELS = 200_000_000  # 200 million pixels (up from 89 million)

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_direction_color(direction) -> str:
    """Get color for bull/bear direction."""
    if direction is None:
        return VIZ_COLORS['neutral']

    direction_str = str(direction).upper()
    if 'BULL' in direction_str:
        return VIZ_COLORS['bull']
    elif 'BEAR' in direction_str:
        return VIZ_COLORS['bear']
    return VIZ_COLORS['neutral']


def extract_direction(tf_data) -> str:
    """Extract direction string from timeframe data (handles nested dicts from model_dump)."""
    if tf_data is None:
        return '-'
    if isinstance(tf_data, dict):
        # Nested structure from model_dump: {'direction': 'Bull', 'strong': ..., 'weak': ...}
        dir_val = tf_data.get('direction', '-')
        if isinstance(dir_val, dict):
            # Double nested? Should not happen but handle it
            dir_val = str(dir_val.get('value', dir_val.get('direction', '-')))
        else:
            dir_val = str(dir_val) if dir_val else '-'
    else:
        dir_val = str(tf_data) if tf_data else '-'

    # Clean up direction string - remove "Direction." prefix if present
    dir_val = dir_val.replace('Direction.', '').replace('direction.', '')

    # Convert to display format: BULL -> Bull, BEAR_PLUS -> Bear+, etc.
    dir_val = dir_val.replace('_PLUS', '+').replace('_plus', '+')
    if dir_val.upper() in ['BULL', 'BEAR', 'NEUTRAL']:
        dir_val = dir_val.capitalize()
    elif dir_val.upper() == 'BULL+':
        dir_val = 'Bull+'
    elif dir_val.upper() == 'BEAR+':
        dir_val = 'Bear+'

    return dir_val


def clean_rank(rank_val) -> str:
    """Clean up rank string - remove 'Rank.' prefix."""
    if rank_val is None:
        return '-'
    rank_str = str(rank_val)
    # Remove "Rank." prefix if present
    rank_str = rank_str.replace('Rank.', '').replace('rank.', '')
    return rank_str


def clean_tier(tier_val) -> str:
    """Clean up tier string - remove 'Tier.' prefix."""
    if tier_val is None:
        return '-'
    tier_str = str(tier_val)
    # Remove "Tier." prefix if present
    tier_str = tier_str.replace('Tier.', '').replace('tier.', '')
    return tier_str


def get_tier_color(tier) -> str:
    """Get color for tier classification."""
    if tier is None:
        return VIZ_COLORS['text_muted']

    tier_str = clean_tier(str(tier)).upper()
    return TIER_COLORS.get(tier_str, VIZ_COLORS['text_muted'])


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None or price == 0 or pd.isna(price):
        return "-"
    return f"${price:.2f}"


# =============================================================================
# CHART BUILDER
# =============================================================================

class PreMarketChartBuilder:
    """Build pre-market PDF report visualization."""

    def __init__(self):
        self.fig = None
        self._current_dpi = PREVIEW_DPI  # Default to preview mode

    def build(
        self,
        ticker: str,
        anchor_date: date,
        result: Dict[str, Any],
        index_structures: List[Dict] = None,
        candle_data: pd.DataFrame = None,
        volume_profile: Dict[float, float] = None,
        notes: str = "",
        preview_mode: bool = False
    ) -> plt.Figure:
        """Build complete pre-market report visualization.

        Args:
            preview_mode: If False (default), use full dimensions for high-quality output.
                         Set to True for smaller preview dimensions.
        """
        # Extract data from result
        market_structure = result.get("market_structure", {})
        bar_data = result.get("bar_data", {})
        hvn_result = result.get("hvn_result", {})
        filtered_zones = result.get("filtered_zones", [])
        primary_setup = result.get("primary_setup", {})
        secondary_setup = result.get("secondary_setup", {})

        # Select dimensions based on mode
        if preview_mode:
            fig_width = PREVIEW_FIGURE_WIDTH
            fig_height = PREVIEW_FIGURE_HEIGHT
            fig_dpi = PREVIEW_DPI
        else:
            fig_width = FIGURE_WIDTH
            fig_height = FIGURE_HEIGHT
            fig_dpi = DPI

        # Store DPI for to_bytes method
        self._current_dpi = fig_dpi

        # Create figure with dark background
        self.fig = plt.figure(
            figsize=(fig_width, fig_height),
            facecolor=VIZ_COLORS['dark_bg'],
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

        # Get epoch POC prices (from HVNResult.pocs list)
        epoch_pocs = []
        if isinstance(hvn_result, dict):
            # HVNResult uses 'pocs' key (List[POCResult]) not 'hvn_pocs'
            pocs = hvn_result.get("pocs", [])
            epoch_pocs = [p.get("price", 0) if isinstance(p, dict) else 0 for p in pocs[:10]]

        # Build chart first to get y-limits, then VP
        y_limits = self._build_price_chart(
            ax_chart, candle_data, primary_setup, secondary_setup,
            epoch_pocs, bar_data, hvn_result
        )
        self._build_volume_profile(ax_vp, volume_profile, y_limits)

        # Title
        date_str = datetime.now().strftime('%Y-%m-%d')
        composite = "N/A"
        if isinstance(market_structure, dict):
            composite_raw = market_structure.get("composite", "N/A")
            composite = extract_direction(composite_raw)

        self.fig.suptitle(
            f'{ticker} | Pre-Market Report | {date_str} | Composite: {composite}',
            color=VIZ_COLORS['text_primary'], fontsize=FONT_TITLE, fontweight='bold', y=0.97
        )

        # Subtitle with epoch info
        price = bar_data.get("price", 0) if isinstance(bar_data, dict) else 0
        atr = bar_data.get("d1_atr", 0) if isinstance(bar_data, dict) else 0
        anchor_str = anchor_date.strftime('%Y-%m-%d') if anchor_date else "N/A"
        d1_atr_str = f"D1ATR : {atr:.2f}" if atr else "D1ATR : N/A"

        self.fig.text(
            0.5, 0.935,
            f'Current: {price:.2f}|{d1_atr_str} | Anchor Date: {anchor_str}',
            color=VIZ_COLORS['text_muted'], fontsize=FONT_SUBTITLE, ha='center'
        )

        return self.fig

    def _build_market_structure(self, ax: plt.Axes, index_structures: List[Dict]):
        """Build Market Structure table for index ETFs."""
        ax.set_facecolor(VIZ_COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        headers = ['Index', 'D1', 'H4', 'H1', 'M15', 'Comp']
        x_positions = [0.08, 0.22, 0.36, 0.50, 0.64, 0.82]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.75, header, color=VIZ_COLORS['text_muted'],
                   fontsize=FONT_HEADER, ha='center', fontweight='bold')

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
                    extract_direction(ms.get('composite', '-'))
                ]
            else:
                values = [default_indices[row_idx], '-', '-', '-', '-', '-']

            for col_idx, val in enumerate(values):
                color = get_direction_color(val) if col_idx > 0 else VIZ_COLORS['text_primary']
                ax.text(x_positions[col_idx], y, str(val), color=color,
                       fontsize=FONT_TABLE_BOLD, ha='center', va='center')

            if row_idx < 2:
                ax.axhline(y - 0.10, color=VIZ_COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)

    def _build_ticker_structure(self, ax: plt.Axes, market_structure: Dict, bar_data: Dict):
        """Build Ticker Structure table with direction and strong/weak levels."""
        ax.set_facecolor(VIZ_COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        x_positions = [0.22, 0.36, 0.50, 0.64, 0.82]
        tf_labels = ['D1', 'H4', 'H1', 'M15', 'Comp']

        ax.text(0.05, 0.72, 'Direction:', color=VIZ_COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        for i, tf in enumerate(tf_labels):
            ax.text(x_positions[i], 0.78, tf, color=VIZ_COLORS['text_muted'], fontsize=FONT_LABEL, ha='center')

        if market_structure:
            # Extract directions from nested structure (model_dump creates {'d1': {'direction': 'Bull', ...}})
            directions = [
                extract_direction(market_structure.get('d1')),
                extract_direction(market_structure.get('h4')),
                extract_direction(market_structure.get('h1')),
                extract_direction(market_structure.get('m15')),
                extract_direction(market_structure.get('composite'))
            ]
            for i, dir_val in enumerate(directions):
                color = get_direction_color(dir_val)
                ax.text(x_positions[i], 0.65, str(dir_val) if dir_val else "-",
                       color=color, fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

        ax.text(0.05, 0.45, 'Strong:', color=VIZ_COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        if bar_data:
            strongs = [bar_data.get('d1_strong'), bar_data.get('h4_strong'),
                      bar_data.get('h1_strong'), bar_data.get('m15_strong')]
            for i, val in enumerate(strongs):
                ax.text(x_positions[i], 0.45, format_price(val),
                       color=VIZ_COLORS['bull'], fontsize=FONT_TABLE, ha='center')

        ax.text(0.05, 0.25, 'Weak:', color=VIZ_COLORS['text_muted'], fontsize=FONT_HEADER, ha='left')
        if bar_data:
            weaks = [bar_data.get('d1_weak'), bar_data.get('h4_weak'),
                    bar_data.get('h1_weak'), bar_data.get('m15_weak')]
            for i, val in enumerate(weaks):
                ax.text(x_positions[i], 0.25, format_price(val),
                       color=VIZ_COLORS['bear'], fontsize=FONT_TABLE, ha='center')

    def _build_zone_results(self, ax: plt.Axes, zones: List[Dict], ticker: str):
        """Build Zone Results table."""
        ax.set_facecolor(VIZ_COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        headers = ['Zone ID', 'POC', 'High', 'Low', 'Rank', 'Tier', 'Score']
        x_positions = [0.10, 0.24, 0.36, 0.48, 0.60, 0.74, 0.88]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.88, header, color=VIZ_COLORS['text_muted'],
                   fontsize=FONT_HEADER, ha='center', fontweight='bold')

        ax.axhline(0.84, color=VIZ_COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)

        max_rows = min(6, len(zones) if zones else 0)
        row_height = 0.12

        for row_idx in range(max_rows):
            zone = zones[row_idx]
            y = 0.76 - (row_idx * row_height)

            zone_id = zone.get('zone_id', '')
            zone_id_short = zone_id.replace(f'{ticker}_', '')

            ax.text(x_positions[0], y, zone_id_short, color=VIZ_COLORS['text_primary'],
                   fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[1], y, format_price(zone.get('hvn_poc')),
                   color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[2], y, format_price(zone.get('zone_high')),
                   color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')
            ax.text(x_positions[3], y, format_price(zone.get('zone_low')),
                   color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')

            rank_str = clean_rank(zone.get('rank', ''))
            rank_color = RANK_COLORS.get(rank_str, VIZ_COLORS['text_muted'])
            ax.text(x_positions[4], y, rank_str, color=rank_color,
                   fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

            tier_str = clean_tier(zone.get('tier', ''))
            tier_color = get_tier_color(tier_str)
            ax.text(x_positions[5], y, tier_str or '-', color=tier_color,
                   fontsize=FONT_TABLE_BOLD, ha='center', fontweight='bold')

            ax.text(x_positions[6], y, f'{zone.get("score", 0):.1f}',
                   color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='center')

            if row_idx < max_rows - 1:
                ax.axhline(y - row_height/2 + 0.02, color=VIZ_COLORS['border'],
                          linewidth=0.5, xmin=0.02, xmax=0.98)

        if not zones:
            ax.text(0.5, 0.5, 'No zones found', color=VIZ_COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', style='italic')

    def _build_setup_analysis(self, ax: plt.Axes, primary_setup: Dict, secondary_setup: Dict,
                              ticker: str, filtered_zones: List[Dict]):
        """Build Setup Analysis table with confluences."""
        ax.set_facecolor(VIZ_COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        ax.text(0.05, 0.92, 'PRIMARY:', color=VIZ_COLORS['primary_blue'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if primary_setup and primary_setup.get('hvn_poc', 0) > 0:
            tier_color = get_tier_color(primary_setup.get('tier'))
            zone_id = primary_setup.get('zone_id', '')
            zone_id_short = zone_id.replace(f'{ticker}_', '')
            direction = extract_direction(primary_setup.get('direction', ''))

            primary_text = f"{direction} | Zone: {zone_id_short} | POC: {format_price(primary_setup.get('hvn_poc'))}"
            ax.text(0.05, 0.82, primary_text, color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='left')

            tier_str = clean_tier(primary_setup.get('tier', ''))
            ax.text(0.95, 0.82, tier_str, color=tier_color, fontsize=FONT_TABLE_BOLD, ha='right', fontweight='bold')

            range_text = f"Range: {format_price(primary_setup.get('zone_low'))} - {format_price(primary_setup.get('zone_high'))}"
            target = primary_setup.get('target', 0)
            if target and target > 0:
                rr = primary_setup.get('risk_reward', 0)
                rr_str = f"{rr:.2f}" if rr else ""
                range_text += f" | Target: {format_price(target)} | {rr_str}"
            ax.text(0.05, 0.73, range_text, color=VIZ_COLORS['text_muted'], fontsize=FONT_TABLE, ha='left')

            # Confluences line
            confluences = primary_setup.get('confluences', [])
            if confluences:
                if isinstance(confluences, list):
                    conf_str = ', '.join(str(c) for c in confluences)
                else:
                    conf_str = str(confluences)
                ax.text(0.05, 0.64, f"Confluences: {conf_str}", color=VIZ_COLORS['text_dim'],
                       fontsize=FONT_LABEL, ha='left')
        else:
            ax.text(0.05, 0.82, 'No primary setup', color=VIZ_COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', style='italic')

        ax.text(0.05, 0.50, 'SECONDARY:', color=VIZ_COLORS['secondary_red'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if secondary_setup and secondary_setup.get('hvn_poc', 0) > 0:
            tier_color = get_tier_color(secondary_setup.get('tier'))
            zone_id = secondary_setup.get('zone_id', '')
            zone_id_short = zone_id.replace(f'{ticker}_', '')
            direction = extract_direction(secondary_setup.get('direction', ''))

            secondary_text = f"{direction} | Zone: {zone_id_short} | POC: {format_price(secondary_setup.get('hvn_poc'))}"
            ax.text(0.05, 0.40, secondary_text, color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE, ha='left')

            tier_str = clean_tier(secondary_setup.get('tier', ''))
            ax.text(0.95, 0.40, tier_str, color=tier_color, fontsize=FONT_TABLE_BOLD, ha='right', fontweight='bold')

            range_text = f"Range: {format_price(secondary_setup.get('zone_low'))} - {format_price(secondary_setup.get('zone_high'))}"
            target = secondary_setup.get('target', 0)
            if target and target > 0:
                rr = secondary_setup.get('risk_reward', 0)
                rr_str = f"{rr:.2f}" if rr else ""
                range_text += f" | Target: {format_price(target)} | {rr_str}"
            ax.text(0.05, 0.31, range_text, color=VIZ_COLORS['text_muted'], fontsize=FONT_TABLE, ha='left')

            # Confluences line
            confluences = secondary_setup.get('confluences', [])
            if confluences:
                if isinstance(confluences, list):
                    conf_str = ', '.join(str(c) for c in confluences)
                else:
                    conf_str = str(confluences)
                ax.text(0.05, 0.22, f"Confluences: {conf_str}", color=VIZ_COLORS['text_dim'],
                       fontsize=FONT_LABEL, ha='left')
        else:
            ax.text(0.05, 0.40, 'No secondary setup', color=VIZ_COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', style='italic')

    def _build_notes(self, ax: plt.Axes, notes: str, hvn_result: Dict,
                     primary_setup: Dict, secondary_setup: Dict):
        """Build Notes section with PineScript string."""
        ax.set_facecolor(VIZ_COLORS['notes_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(VIZ_COLORS['border'])

        ax.text(0.02, 0.88, 'NOTES:', color=VIZ_COLORS['text_muted'],
                fontsize=FONT_TABLE_BOLD, fontweight='bold', ha='left')

        if notes:
            ax.text(0.02, 0.55, notes, color=VIZ_COLORS['text_dim'],
                   fontsize=FONT_TABLE, ha='left', va='center', style='italic', wrap=True)

        pinescript_string = self._build_pinescript_string(primary_setup, secondary_setup, hvn_result)
        if pinescript_string:
            display_str = pinescript_string
            if len(display_str) > 80:
                display_str = display_str[:77] + "..."
            ax.text(0.98, 0.12, f'PineScript: {display_str}', color=VIZ_COLORS['text_dim'],
                   fontsize=6, ha='right', style='italic')

    def _build_pinescript_string(self, primary_setup: Dict, secondary_setup: Dict,
                                  hvn_result: Dict) -> str:
        """Build 16-value PineScript string."""
        pri_high = primary_setup.get('zone_high', 0) if primary_setup else 0
        pri_low = primary_setup.get('zone_low', 0) if primary_setup else 0
        pri_target = primary_setup.get('target', 0) if primary_setup else 0

        sec_high = secondary_setup.get('zone_high', 0) if secondary_setup else 0
        sec_low = secondary_setup.get('zone_low', 0) if secondary_setup else 0
        sec_target = secondary_setup.get('target', 0) if secondary_setup else 0

        values = [pri_high, pri_low, pri_target, sec_high, sec_low, sec_target]

        if hvn_result:
            # HVNResult uses 'pocs' key (List[POCResult]) not 'hvn_pocs'
            pocs = hvn_result.get('pocs', [])
            for i in range(10):
                if i < len(pocs):
                    poc_item = pocs[i]
                    values.append(poc_item.get('price', 0) if isinstance(poc_item, dict) else 0)
                else:
                    values.append(0.0)
        else:
            values.extend([0.0] * 10)

        return ",".join(f"{v:.2f}" if v != 0 else "0" for v in values)

    def _build_price_chart(self, ax: plt.Axes, candle_data: pd.DataFrame,
                           primary_setup: Dict, secondary_setup: Dict,
                           epoch_pocs: List[float], bar_data: Dict,
                           hvn_result: Dict) -> Tuple[float, float]:
        """Build H1 candlestick chart with zones and POC lines."""
        ax.set_facecolor(VIZ_COLORS['dark_bg'])

        if candle_data is None or candle_data.empty:
            ax.text(0.5, 0.5, 'No chart data available', color=VIZ_COLORS['text_muted'],
                   fontsize=14, ha='center', va='center')

            if hvn_result:
                y_min = hvn_result.get('price_range_low', 0)
                y_max = hvn_result.get('price_range_high', 0)
                if y_min and y_max:
                    self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, 100, -3, y_min, y_max)
                    ax.set_xlim(0, 100)
                    ax.set_ylim(y_min, y_max)
                    return (y_min, y_max)

            return (0, 100)

        n_bars = len(candle_data)
        body_half_width = 0.3

        for i, (idx, bar) in enumerate(candle_data.iterrows()):
            color = VIZ_COLORS['candle_green'] if bar['close'] >= bar['open'] else VIZ_COLORS['candle_red']

            ax.plot([i, i], [bar['low'], bar['high']], color=color, linewidth=0.8)

            body_bottom = min(bar['open'], bar['close'])
            body_height = abs(bar['close'] - bar['open'])
            if body_height < 0.01:
                body_height = 0.01
            rect = mpatches.Rectangle(
                (i - body_half_width, body_bottom), 0.6, body_height,
                facecolor=color, edgecolor=color
            )
            ax.add_patch(rect)

        if hvn_result:
            y_min = hvn_result.get('price_range_low', candle_data['low'].min())
            y_max = hvn_result.get('price_range_high', candle_data['high'].max())
        else:
            y_min = candle_data['low'].min()
            y_max = candle_data['high'].max()

        if primary_setup and primary_setup.get('target', 0) > 0:
            y_max = max(y_max, primary_setup['target'])
            y_min = min(y_min, primary_setup['target'])
        if secondary_setup and secondary_setup.get('target', 0) > 0:
            y_max = max(y_max, secondary_setup['target'])
            y_min = min(y_min, secondary_setup['target'])

        padding = (y_max - y_min) * YAXIS_PADDING_PCT
        y_min -= padding
        y_max += padding

        self._draw_zone_overlays(ax, primary_setup, secondary_setup, epoch_pocs, n_bars, -3, y_min, y_max)

        ax.set_xlim(-2, n_bars + 15)
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel('Price ($)', color=VIZ_COLORS['text_primary'], fontsize=FONT_AXIS_LABEL)
        ax.tick_params(colors=VIZ_COLORS['text_primary'], labelsize=FONT_AXIS)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(VIZ_COLORS['border_light'])

        ax.set_xlabel('Time (ET)', color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE_BOLD)

        return (y_min, y_max)

    def _draw_zone_overlays(self, ax: plt.Axes, primary_setup: Dict, secondary_setup: Dict,
                            epoch_pocs: List[float], n_bars: int, label_offset: float,
                            y_min: float, y_max: float):
        """Draw zone overlays, POC lines, and target lines."""
        # Primary Zone (Blue)
        if primary_setup and primary_setup.get('zone_high', 0) > 0 and primary_setup.get('zone_low', 0) > 0:
            ax.axhspan(
                primary_setup['zone_low'], primary_setup['zone_high'],
                alpha=ZONE_FILL_ALPHA, color=VIZ_COLORS['primary_blue'], zorder=1
            )
            poc = primary_setup.get('hvn_poc', 0)
            if poc > 0:
                ax.axhline(poc, color=VIZ_COLORS['primary_blue'], linewidth=1.5, alpha=0.8)
                ax.text(label_offset, poc, f'${poc:.2f}',
                       color=VIZ_COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                       fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=VIZ_COLORS['dark_bg'], edgecolor=VIZ_COLORS['primary_blue'], alpha=0.8))

            target = primary_setup.get('target', 0)
            if target and target > 0:
                ax.axhline(target, color=VIZ_COLORS['primary_blue'], linestyle='-', linewidth=2, alpha=0.9)
                ax.text(label_offset, target, f'${target:.2f}',
                       color=VIZ_COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                       fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=VIZ_COLORS['dark_bg'], edgecolor=VIZ_COLORS['primary_blue'], alpha=0.8))

        # Secondary Zone (Red)
        if secondary_setup and secondary_setup.get('zone_high', 0) > 0 and secondary_setup.get('zone_low', 0) > 0:
            ax.axhspan(
                secondary_setup['zone_low'], secondary_setup['zone_high'],
                alpha=ZONE_FILL_ALPHA, color=VIZ_COLORS['secondary_red'], zorder=1
            )
            poc = secondary_setup.get('hvn_poc', 0)
            if poc > 0:
                ax.axhline(poc, color=VIZ_COLORS['secondary_red'], linewidth=1.5, alpha=0.8)
                ax.text(label_offset, poc, f'${poc:.2f}',
                       color=VIZ_COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                       bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=VIZ_COLORS['dark_bg'], edgecolor=VIZ_COLORS['secondary_red'], alpha=0.8))

            target = secondary_setup.get('target', 0)
            if target and target > 0:
                ax.axhline(target, color=VIZ_COLORS['secondary_red'], linestyle='-', linewidth=2, alpha=0.9)
                ax.text(label_offset, target, f'${target:.2f}',
                       color=VIZ_COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                       fontweight='bold', bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=VIZ_COLORS['dark_bg'], edgecolor=VIZ_COLORS['secondary_red'], alpha=0.8))

        # Build set of prices to skip
        skip_prices = set()
        price_tolerance = 0.01

        if primary_setup:
            if primary_setup.get('hvn_poc', 0) > 0:
                skip_prices.add(round(primary_setup['hvn_poc'], 2))
            if primary_setup.get('target', 0) > 0:
                skip_prices.add(round(primary_setup['target'], 2))

        if secondary_setup:
            if secondary_setup.get('hvn_poc', 0) > 0:
                skip_prices.add(round(secondary_setup['hvn_poc'], 2))
            if secondary_setup.get('target', 0) > 0:
                skip_prices.add(round(secondary_setup['target'], 2))

        # POC lines from HVN calculation
        for i, poc_price in enumerate(epoch_pocs):
            if poc_price > 0 and y_min <= poc_price <= y_max:
                poc_rounded = round(poc_price, 2)
                should_skip = any(
                    abs(poc_rounded - skip_price) < price_tolerance
                    for skip_price in skip_prices
                )

                if should_skip:
                    continue

                rank = i + 1
                ax.axhline(poc_price, color=POC_LINE_COLOR, linestyle=POC_LINE_STYLE,
                          linewidth=1.0, alpha=POC_LINE_ALPHA, zorder=2)

                ax.text(label_offset, poc_price, f'POC{rank}: ${poc_price:.2f}',
                       color=POC_LINE_COLOR, fontsize=FONT_POC_LABEL, va='center', ha='right',
                       alpha=0.8, bbox=dict(boxstyle='round,pad=0.15',
                       facecolor=VIZ_COLORS['dark_bg'], edgecolor=POC_LINE_COLOR,
                       alpha=0.5, linewidth=0.5))

    def _build_volume_profile(self, ax: plt.Axes, volume_profile: Dict[float, float],
                              y_limits: Tuple[float, float]):
        """Build Volume Profile sidebar."""
        ax.set_facecolor(VIZ_COLORS['dark_bg'])

        if not volume_profile:
            ax.text(0.5, 0.5, 'No VP', color=VIZ_COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return

        y_min, y_max = y_limits
        filtered_vp = {p: v for p, v in volume_profile.items() if y_min <= p <= y_max}

        if not filtered_vp:
            ax.text(0.5, 0.5, 'No VP in range', color=VIZ_COLORS['text_muted'],
                   fontsize=10, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return

        sorted_prices = sorted(filtered_vp.keys())
        volumes = [filtered_vp[p] for p in sorted_prices]
        bar_height = 0.01

        ax.barh(sorted_prices, volumes, height=bar_height,
               color=VBP_COLOR, alpha=0.8, edgecolor='none')

        ax.set_xlabel('Volume', color=VIZ_COLORS['text_primary'], fontsize=FONT_TABLE)
        ax.tick_params(colors=VIZ_COLORS['text_primary'], labelleft=False, labelsize=FONT_LABEL)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(VIZ_COLORS['border_light'])

        ax.set_ylim(y_limits)

    def to_bytes(self) -> bytes:
        """Convert current figure to PNG bytes."""
        if self.fig is None:
            return b''

        buf = io.BytesIO()
        self.fig.savefig(
            buf, format='png', dpi=self._current_dpi, facecolor=VIZ_COLORS['dark_bg'],
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
# EXPORT DIALOG
# =============================================================================

class ExportDialog(QDialog):
    """Export dialog for pre-market reports - modeled after trade_reel export."""

    # Export format definitions (width, height)
    EXPORT_FORMATS = {
        'discord': {'label': 'Discord', 'size': (1920, 1080), 'color': '#5865F2'},
    }

    def __init__(self, tickers: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Reports")
        self.setMinimumWidth(420)
        self.selected_format = 'discord'
        self.selected_tickers = []
        self.export_directory = str(Path(__file__).parent.parent.parent / "exports" / "discord")

        self._ticker_checkboxes = {}
        self._setup_ui(tickers)

    def _setup_ui(self, tickers: List[str]):
        """Build the export dialog UI."""
        from PyQt6.QtWidgets import QCheckBox, QGroupBox, QGridLayout, QDialogButtonBox

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Format Selection ---
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)

        for fmt_key, fmt_info in self.EXPORT_FORMATS.items():
            w, h = fmt_info['size']
            btn = QPushButton(f"  {fmt_info['label']}  ({w} x {h})")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {fmt_info['color']};
                    color: white;
                    border-radius: 4px;
                    padding: 10px 16px;
                    font-weight: bold;
                    font-size: 12px;
                    border: 2px solid {fmt_info['color']};
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {fmt_info['color']}cc;
                }}
            """)
            btn.setCheckable(True)
            btn.setChecked(fmt_key == 'discord')
            btn.clicked.connect(lambda checked, k=fmt_key: self._on_format_selected(k))
            format_layout.addWidget(btn)
            # Store reference for toggling
            if not hasattr(self, '_format_buttons'):
                self._format_buttons = {}
            self._format_buttons[fmt_key] = btn

        layout.addWidget(format_group)

        # --- Ticker Selection ---
        ticker_group = QGroupBox(f"Tickers ({len(tickers)})")
        ticker_layout = QVBoxLayout(ticker_group)

        # Select All / Deselect All
        select_row = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._toggle_all_tickers(True))
        select_row.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self._toggle_all_tickers(False))
        select_row.addWidget(deselect_all_btn)
        select_row.addStretch()
        ticker_layout.addLayout(select_row)

        # Ticker checkboxes in a grid
        grid = QGridLayout()
        for i, ticker in enumerate(sorted(tickers)):
            cb = QCheckBox(ticker)
            cb.setChecked(True)
            cb.setStyleSheet("QCheckBox { font-size: 12px; padding: 4px; }")
            self._ticker_checkboxes[ticker] = cb
            grid.addWidget(cb, i // 3, i % 3)
        ticker_layout.addLayout(grid)

        layout.addWidget(ticker_group)

        # --- Export Directory ---
        dir_group = QGroupBox("Export Directory")
        dir_layout = QHBoxLayout(dir_group)

        self._dir_label = QLabel(self.export_directory)
        self._dir_label.setStyleSheet("font-size: 11px; padding: 4px;")
        self._dir_label.setWordWrap(True)
        dir_layout.addWidget(self._dir_label, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        dir_layout.addWidget(browse_btn)

        layout.addWidget(dir_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_format_selected(self, format_key: str):
        """Handle format button toggle."""
        self.selected_format = format_key
        # Update export directory to match format
        self.export_directory = str(Path(__file__).parent.parent.parent / "exports" / format_key)
        self._dir_label.setText(self.export_directory)
        # Ensure only the selected button is checked
        for k, btn in self._format_buttons.items():
            btn.setChecked(k == format_key)

    def _toggle_all_tickers(self, checked: bool):
        """Toggle all ticker checkboxes."""
        for cb in self._ticker_checkboxes.values():
            cb.setChecked(checked)

    def _on_browse(self):
        """Open directory picker."""
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory", self.export_directory)
        if directory:
            self.export_directory = directory
            self._dir_label.setText(directory)

    def _on_accept(self):
        """Collect selections and accept dialog."""
        self.selected_tickers = [
            ticker for ticker, cb in self._ticker_checkboxes.items() if cb.isChecked()
        ]
        self.accept()


# =============================================================================
# REPORT WORKER
# =============================================================================

class ReportWorker(QThread):
    """Worker thread for generating reports."""
    progress = pyqtSignal(str)
    report_ready = pyqtSignal(str, bytes)  # ticker, image_bytes
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, results: Dict[str, Any], end_timestamp: Optional[datetime] = None):
        super().__init__()
        self.results = results
        self.end_timestamp = end_timestamp

    def _fetch_candle_data(self, ticker: str, anchor_date: date, n_bars: int = 120) -> pd.DataFrame:
        """Fetch H1 candles for candlestick chart display."""
        try:
            from data.polygon_client import PolygonClient
            client = PolygonClient()

            # Calculate start date for fetching (need extra days for market hours)
            # Use analysis_date as reference point instead of today() for historical analysis
            analysis_date = self.results.get("analysis_date", date.today())
            days_needed = max(30, (n_bars * 60) // (6.5 * 60) + 10)
            start_date = analysis_date - timedelta(days=days_needed)

            self.progress.emit(f"Fetching H1 candles for {ticker}...")

            # Fetch 60-minute bars with end_timestamp cutoff
            df = client.fetch_minute_bars(
                ticker=ticker,
                start_date=start_date,
                multiplier=60,
                end_timestamp=self.end_timestamp
            )

            if df.empty:
                return pd.DataFrame()

            # Take the last n_bars
            df = df.tail(n_bars).copy()

            # Convert to format expected by chart builder
            df.set_index('timestamp', inplace=True)
            return df

        except Exception as e:
            logger.warning(f"Failed to fetch candles for {ticker}: {e}")
            return pd.DataFrame()

    def _build_volume_profile(self, ticker: str, anchor_date: date) -> Dict[float, float]:
        """Build volume profile from anchor date to now at $0.01 granularity."""
        try:
            from data.polygon_client import PolygonClient
            from math import floor, ceil
            client = PolygonClient()

            self.progress.emit(f"Building volume profile for {ticker}...")

            # Fetch 15-minute bars for VbP (more granular than H1)
            df = client.fetch_minute_bars_chunked(
                ticker=ticker,
                start_date=anchor_date,
                multiplier=15,
                chunk_days=30,
                end_timestamp=self.end_timestamp
            )

            if df.empty:
                return {}

            volume_profile = {}
            granularity = 0.01

            for _, bar in df.iterrows():
                bar_low = bar['low']
                bar_high = bar['high']
                bar_volume = bar['volume']

                if bar_volume <= 0 or bar_high <= bar_low:
                    continue
                if pd.isna(bar_low) or pd.isna(bar_high) or pd.isna(bar_volume):
                    continue

                low_level = floor(bar_low / granularity) * granularity
                high_level = ceil(bar_high / granularity) * granularity
                num_levels = int(round((high_level - low_level) / granularity)) + 1

                if num_levels <= 0:
                    continue

                volume_per_level = bar_volume / num_levels
                current = low_level
                for _ in range(num_levels):
                    price_key = round(current, 2)
                    volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                    current += granularity

            return volume_profile

        except Exception as e:
            logger.warning(f"Failed to build volume profile for {ticker}: {e}")
            return {}

    def run(self):
        """Generate reports for all tickers."""
        try:
            index_results = self.results.get("index", [])
            custom_results = self.results.get("custom", [])

            successful_index = [r for r in index_results if r.get("success")]
            successful_custom = [r for r in custom_results if r.get("success")]

            all_results = successful_index + successful_custom

            if not all_results:
                self.error.emit("No successful results to visualize")
                return

            # Build index structures for Market Structure table
            index_structures = []
            for idx_result in successful_index:
                ms = idx_result.get("market_structure", {})
                if ms:
                    # Extract directions from nested structure (model_dump creates nested dicts)
                    index_structures.append({
                        'ticker': ms.get('ticker', ''),
                        'd1_dir': extract_direction(ms.get('d1')),
                        'h4_dir': extract_direction(ms.get('h4')),
                        'h1_dir': extract_direction(ms.get('h1')),
                        'm15_dir': extract_direction(ms.get('m15')),
                        'composite': extract_direction(ms.get('composite'))
                    })

            for result in all_results:
                ticker = result.get("ticker", "Unknown")
                self.progress.emit(f"Generating report for {ticker}...")

                try:
                    hvn_result = result.get("hvn_result", {})
                    anchor_date = hvn_result.get("start_date") if hvn_result else date.today()
                    if isinstance(anchor_date, str):
                        anchor_date = datetime.strptime(anchor_date, '%Y-%m-%d').date()

                    # Fetch H1 candle data for candlestick chart
                    candle_data = self._fetch_candle_data(ticker, anchor_date)

                    # Build volume profile from anchor date
                    volume_profile = self._build_volume_profile(ticker, anchor_date)

                    builder = PreMarketChartBuilder()
                    builder.build(
                        ticker=ticker,
                        anchor_date=anchor_date,
                        result=result,
                        index_structures=index_structures,
                        candle_data=candle_data,
                        volume_profile=volume_profile,
                        notes=""
                    )

                    img_bytes = builder.to_bytes()
                    builder.close()

                    self.report_ready.emit(ticker, img_bytes)

                except Exception as e:
                    logger.exception(f"Error generating report for {ticker}")
                    self.progress.emit(f"Error generating {ticker}: {str(e)}")

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# PRE-MARKET REPORT TAB
# =============================================================================

class PreMarketReportTab(BaseTab):
    """
    Pre-Market Report Tab

    Features:
    - Full pre-market visualization for each ticker
    - Candlestick charts with volume profile
    - Zone overlays and POC lines
    - PDF-style layout
    """

    def __init__(self, analysis_results):
        self._worker = None
        self._report_widgets = []
        self._report_images = {}  # ticker -> image_bytes for export
        super().__init__(analysis_results)

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("PRE-MARKET REPORT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Control section
        control_section = self._create_control_section()
        layout.addWidget(control_section)

        # Status section
        status_section = self._create_status_section()
        layout.addWidget(status_section)

        # Reports container (scrollable content will be added here)
        self.reports_container = QVBoxLayout()
        self.reports_container.setSpacing(20)
        layout.addLayout(self.reports_container)

        # Placeholder
        self.placeholder = QLabel("Run analysis and click GENERATE REPORTS to view pre-market visualizations.")
        self.placeholder.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 40px;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reports_container.addWidget(self.placeholder)

        layout.addStretch()

    def _create_control_section(self) -> QFrame:
        """Create the control buttons section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Generate button
        self.generate_button = QPushButton("GENERATE REPORTS")
        self.generate_button.setObjectName("runButton")
        self.generate_button.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_button)

        # Clear button
        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_button)

        # Export button
        self.export_button = QPushButton("EXPORT")
        self.export_button.setObjectName("exportButton")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)

        layout.addStretch()

        # Report count
        self.report_count = QLabel("0 reports")
        self.report_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.report_count)

        return frame

    def _create_status_section(self) -> QFrame:
        """Create the status display section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['status_ready']}; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.progress_label)

        return frame

    def _on_generate_clicked(self):
        """Handle generate button click."""
        results = self.get_results()

        if not results.get("run_complete"):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "No Data",
                "Please run analysis first before generating reports."
            )
            return

        self._clear_reports()

        self.generate_button.setEnabled(False)
        self.status_label.setText("Generating...")
        self.status_label.setStyleSheet(f"color: {COLORS['status_running']}; font-weight: bold;")

        # Get end_timestamp from results (used for Pre-Market mode)
        end_timestamp = results.get("end_timestamp")

        self._worker = ReportWorker(results, end_timestamp=end_timestamp)
        self._worker.progress.connect(self._on_progress)
        self._worker.report_ready.connect(self._on_report_ready)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self._clear_reports()

    def _clear_reports(self):
        """Clear all generated reports."""
        for widget in self._report_widgets:
            widget.deleteLater()
        self._report_widgets.clear()
        self._report_images.clear()

        self.placeholder.show()
        self.report_count.setText("0 reports")
        self.export_button.setEnabled(False)

    def _on_progress(self, message: str):
        """Handle progress update."""
        self.progress_label.setText(message)

    def _on_report_ready(self, ticker: str, image_bytes: bytes):
        """Handle a report being ready."""
        self.placeholder.hide()

        # Store image bytes for export
        if image_bytes:
            self._report_images[ticker] = image_bytes

        # Create report frame
        report_frame = QFrame()
        report_frame.setObjectName("sectionFrame")
        report_frame.setStyleSheet(f"""
            QFrame#sectionFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        report_layout = QVBoxLayout(report_frame)
        report_layout.setContentsMargins(16, 16, 16, 16)
        report_layout.setSpacing(8)

        # Ticker header
        ticker_label = QLabel(ticker)
        ticker_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        ticker_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        report_layout.addWidget(ticker_label)

        # Image - display at full 1920 width for 4K screens
        if image_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)

            image_label = QLabel()
            # Use full 1920 width - the chart is designed for 1920x1080
            image_label.setPixmap(pixmap.scaledToWidth(1920, Qt.TransformationMode.SmoothTransformation))
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setMinimumWidth(1920)
            report_layout.addWidget(image_label)
        else:
            error_label = QLabel("Failed to generate chart")
            error_label.setStyleSheet(f"color: {COLORS['status_error']};")
            report_layout.addWidget(error_label)

        self.reports_container.addWidget(report_frame)
        self._report_widgets.append(report_frame)

        self.report_count.setText(f"{len(self._report_widgets)} reports")

    def _on_finished(self):
        """Handle report generation completion."""
        self._worker = None
        self.generate_button.setEnabled(True)
        self.export_button.setEnabled(len(self._report_images) > 0)
        self.status_label.setText("Complete")
        self.status_label.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")
        self.progress_label.setText("")

    def _on_error(self, error_msg: str):
        """Handle report generation error."""
        self._worker = None
        self.generate_button.setEnabled(True)
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"color: {COLORS['status_error']}; font-weight: bold;")
        self.progress_label.setText(error_msg)

    def _on_export_clicked(self):
        """Handle export button click - show export dialog."""
        if not self._report_images:
            QMessageBox.warning(self, "No Reports", "No reports available to export. Generate reports first.")
            return

        dialog = ExportDialog(list(self._report_images.keys()), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_format = dialog.selected_format
            selected_tickers = dialog.selected_tickers
            export_dir = dialog.export_directory

            if not selected_tickers:
                QMessageBox.warning(self, "No Selection", "Please select at least one ticker to export.")
                return

            exported = 0
            for ticker in selected_tickers:
                image_bytes = self._report_images.get(ticker)
                if not image_bytes:
                    continue

                try:
                    if export_format == 'discord':
                        self._export_discord(ticker, image_bytes, export_dir)
                        exported += 1
                except Exception as e:
                    logger.exception(f"Failed to export {ticker}")
                    self.progress_label.setText(f"Export error for {ticker}: {str(e)}")

            self.progress_label.setText(f"Exported {exported} report(s) to {export_dir}")

    def _export_discord(self, ticker: str, image_bytes: bytes, export_dir: str):
        """Export report as Discord-optimized 1920x1080 PNG."""
        # Load the source image from bytes
        source = QImage()
        source.loadFromData(image_bytes)

        # Create a 1920x1080 canvas with charcoal background
        canvas = QImage(1920, 1080, QImage.Format.Format_ARGB32)
        canvas.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Fill canvas with charcoal background
        painter.fillRect(0, 0, 1920, 1080, QColor('#1C1C1C'))

        # Scale source image to fit within 1920x1080, preserving aspect ratio
        scaled = source.scaled(1920, 1080, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)

        # Center on canvas
        x_offset = (1920 - scaled.width()) // 2
        y_offset = (1080 - scaled.height()) // 2
        painter.drawImage(x_offset, y_offset, scaled)
        painter.end()

        # Save as PNG
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{ticker}_{date_str}_premarket_discord.png"
        filepath = export_path / filename
        canvas.save(str(filepath), "PNG")

        logger.info(f"Exported Discord report: {filepath}")

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if results.get("run_complete"):
            index_count = len([r for r in results.get("index", []) if r.get("success")])
            custom_count = len([r for r in results.get("custom", []) if r.get("success")])
            self.progress_label.setText(f"Ready: {index_count} index + {custom_count} custom tickers")
