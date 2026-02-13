# chart_builder.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\charts\
# Purpose: Build complete visualization chart with tables and price chart (V1.1)

"""
Chart Builder for Module 08 Visualization V1.1

V1.1 CHANGES:
- Zone Results table now shows Tier column
- Setup Analysis section shows tier (T1/T2/T3) alongside zone info
- Tier color-coding: T3 (green), T2 (yellow), T1 (gray)

Creates a single-page visualization with:
- Left panel: Market Structure, Ticker Structure, Zone Results, Setup Analysis, Notes
- Right panel: H1 candlestick chart with epoch VbP + POC lines
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import io
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.visualization_config import (
    COLORS, RANK_COLORS, ZONE_FILL_ALPHA,
    FIGURE_WIDTH, FIGURE_HEIGHT, DPI,
    TABLE_HEIGHT_RATIOS, VBP_COLOR,
    POC_LINE_STYLE, POC_LINE_COLOR, POC_LINE_ALPHA,
    YAXIS_PADDING_PCT
)
from data_readers.excel_reader import VisualizationData, MarketStructure, TickerStructure, ZoneResult, SetupData, EpochData
from data_readers.polygon_fetcher import ChartData


# =============================================================================
# V1.1 TIER COLORS
# =============================================================================

TIER_COLORS = {
    'T3': '#00C853',  # Green - High Quality (L4-L5)
    'T2': '#FFC107',  # Yellow/Amber - Medium Quality (L3)
    'T1': '#9E9E9E',  # Gray - Lower Quality (L1-L2)
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_direction_color(direction: str) -> str:
    """Get color for bull/bear direction"""
    if not direction:
        return COLORS['neutral']
    direction = str(direction).upper()
    if 'BULL' in direction:
        return COLORS['bull']
    elif 'BEAR' in direction:
        return COLORS['bear']
    return COLORS['neutral']


def get_tier_color(tier: str) -> str:
    """Get color for tier classification - V1.1"""
    if not tier:
        return COLORS['text_muted']
    return TIER_COLORS.get(tier.upper(), COLORS['text_muted'])


def format_price(price: float) -> str:
    """Format price for display"""
    if price == 0 or pd.isna(price):
        return "-"
    return f"${price:.2f}"


# =============================================================================
# CHART BUILDER CLASS - V1.1
# =============================================================================

class VisualizationChartBuilder:
    """Build complete visualization charts (V1.1 with tier support)"""
    
    def __init__(self):
        """Initialize chart builder"""
        self.fig = None
        self.axes = {}
    
    def build(self, viz_data: VisualizationData, chart_data: ChartData,
              session_type: str = 'premarket', notes: str = "") -> plt.Figure:
        """
        Build complete visualization figure.
        
        Args:
            viz_data: Data from Excel (zones, setup, structure, epoch POCs)
            chart_data: Data from Polygon (H1 candles, epoch VbP)
            session_type: 'premarket' or 'postmarket'
            notes: User-entered notes text
            
        Returns:
            matplotlib Figure object
        """
        # Create figure with high DPI
        self.fig = plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), 
                              facecolor=COLORS['dark_bg'], dpi=DPI)
        
        # Main layout: Left (tables) | Right (chart + VP)
        main_gs = GridSpec(1, 2, width_ratios=[1, 1.8], wspace=0.03,
                          left=0.02, right=0.98, top=0.91, bottom=0.05)
        
        # Left panel: Stack of tables
        left_gs = main_gs[0].subgridspec(5, 1, height_ratios=TABLE_HEIGHT_RATIOS, hspace=0.15)
        
        # Right panel: Chart + Volume Profile
        right_gs = main_gs[1].subgridspec(1, 2, width_ratios=[4, 1], wspace=0.02)
        
        # Build each section
        self._build_market_structure(self.fig.add_subplot(left_gs[0]), viz_data.market_structure)
        self._build_ticker_structure(self.fig.add_subplot(left_gs[1]), viz_data.ticker_structure)
        self._build_zone_results(self.fig.add_subplot(left_gs[2]), viz_data.zones)
        self._build_setup_analysis(self.fig.add_subplot(left_gs[3]), viz_data.setup)
        self._build_notes(self.fig.add_subplot(left_gs[4]), notes, viz_data.full_pinescript_string)
        
        # Build chart and volume profile with shared y-axis
        ax_chart = self.fig.add_subplot(right_gs[0])
        ax_vp = self.fig.add_subplot(right_gs[1], sharey=ax_chart)
        
        # Get epoch POCs from viz_data
        epoch_pocs = viz_data.epoch.hvn_pocs if viz_data.epoch else []
        
        # Build chart first to get y-limits, then VP
        y_limits = self._build_price_chart(ax_chart, chart_data, viz_data.setup, epoch_pocs)
        self._build_volume_profile(ax_vp, chart_data, y_limits)
        
        # Title
        session_label = "Pre-Market Report" if session_type == 'premarket' else "Post-Market Report"
        date_str = datetime.now().strftime('%Y-%m-%d')
        composite = viz_data.ticker_structure.composite or "N/A"
        
        self.fig.suptitle(
            f'{viz_data.ticker} | {session_label} | {date_str} | Composite: {composite}',
            color=COLORS['text_primary'], fontsize=16, fontweight='bold', y=0.97
        )
        
        # Subtitle with epoch info
        price = viz_data.ticker_structure.price
        atr = viz_data.ticker_structure.d1_atr
        epoch_start = viz_data.epoch.start_date if viz_data.epoch else "N/A"
        self.fig.text(0.5, 0.935,
                     f'Current: ${price:.2f} | D1 ATR: ${atr:.2f} | Anchor Date: {epoch_start}',
                     color=COLORS['text_muted'], fontsize=11, ha='center')
        
        return self.fig
    
    def _build_market_structure(self, ax: plt.Axes, data: List[MarketStructure]):
        """Build Market Structure table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Headers
        headers = ['Index', 'D1', 'H4', 'H1', 'M15', 'Comp']
        x_positions = [0.08, 0.22, 0.36, 0.50, 0.64, 0.82]
        
        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.75, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')
        
        # Data rows
        y_positions = [0.55, 0.35, 0.15]
        for row_idx, ms in enumerate(data):
            if row_idx >= 3:
                break
            y = y_positions[row_idx]
            
            values = [ms.ticker, ms.d1_dir, ms.h4_dir, ms.h1_dir, ms.m15_dir, ms.composite]
            for col_idx, val in enumerate(values):
                color = get_direction_color(val) if col_idx > 0 else COLORS['text_primary']
                ax.text(x_positions[col_idx], y, str(val), color=color,
                       fontsize=10, ha='center', va='center')
            
            if row_idx < 2:
                ax.axhline(y - 0.10, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)
    
    def _build_ticker_structure(self, ax: plt.Axes, data: TickerStructure):
        """Build Ticker Structure table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Column positions
        x_positions = [0.22, 0.36, 0.50, 0.64, 0.82]
        tf_labels = ['D1', 'H4', 'H1', 'M15', 'Comp']
        
        # Headers
        ax.text(0.05, 0.72, 'Direction:', color=COLORS['text_muted'], fontsize=9, ha='left')
        for i, tf in enumerate(tf_labels):
            ax.text(x_positions[i], 0.78, tf, color=COLORS['text_muted'], fontsize=8, ha='center')
        
        # Direction values
        directions = [data.d1_dir, data.h4_dir, data.h1_dir, data.m15_dir, data.composite]
        for i, dir_val in enumerate(directions):
            color = get_direction_color(dir_val)
            ax.text(x_positions[i], 0.65, str(dir_val) if dir_val else "-", 
                   color=color, fontsize=10, ha='center', fontweight='bold')
        
        # Strong levels
        ax.text(0.05, 0.45, 'Strong:', color=COLORS['text_muted'], fontsize=9, ha='left')
        strongs = [data.d1_strong, data.h4_strong, data.h1_strong, data.m15_strong]
        for i, val in enumerate(strongs):
            ax.text(x_positions[i], 0.45, format_price(val), 
                   color=COLORS['bull'], fontsize=9, ha='center')
        
        # Weak levels
        ax.text(0.05, 0.25, 'Weak:', color=COLORS['text_muted'], fontsize=9, ha='left')
        weaks = [data.d1_weak, data.h4_weak, data.h1_weak, data.m15_weak]
        for i, val in enumerate(weaks):
            ax.text(x_positions[i], 0.25, format_price(val), 
                   color=COLORS['bear'], fontsize=9, ha='center')
    
    def _build_zone_results(self, ax: plt.Axes, zones: List[ZoneResult]):
        """Build Zone Results table - V1.1 with Tier column"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # V1.1: Added Tier column, adjusted positions
        headers = ['Zone ID', 'POC', 'High', 'Low', 'Rank', 'Tier', 'Score']
        x_positions = [0.10, 0.24, 0.36, 0.48, 0.60, 0.74, 0.88]
        
        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.88, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')
        
        ax.axhline(0.84, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)
        
        # Data rows (max 6 zones)
        max_rows = min(6, len(zones))
        row_height = 0.12
        
        for row_idx in range(max_rows):
            zone = zones[row_idx]
            y = 0.76 - (row_idx * row_height)
            
            zone_id_short = zone.zone_id.replace(f'{zone.ticker}_', '')
            ax.text(x_positions[0], y, zone_id_short, color=COLORS['text_primary'],
                   fontsize=9, ha='center')
            ax.text(x_positions[1], y, format_price(zone.hvn_poc), 
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            ax.text(x_positions[2], y, format_price(zone.zone_high), 
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            ax.text(x_positions[3], y, format_price(zone.zone_low), 
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            
            # Rank with color
            rank_color = RANK_COLORS.get(zone.rank, COLORS['text_muted'])
            ax.text(x_positions[4], y, zone.rank, color=rank_color,
                   fontsize=10, ha='center', fontweight='bold')
            
            # V1.1: Tier with color
            tier_color = get_tier_color(zone.tier)
            ax.text(x_positions[5], y, zone.tier or '-', color=tier_color,
                   fontsize=10, ha='center', fontweight='bold')
            
            # Score
            ax.text(x_positions[6], y, f'{zone.score:.1f}', 
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            
            if row_idx < max_rows - 1:
                ax.axhline(y - row_height/2 + 0.02, color=COLORS['border'], 
                          linewidth=0.5, xmin=0.02, xmax=0.98)
        
        if len(zones) == 0:
            ax.text(0.5, 0.5, 'No zones found', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', style='italic')
    
    def _build_setup_analysis(self, ax: plt.Axes, setup: SetupData):
        """Build Setup Analysis table - V1.2 with tier and confluences display"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Primary Setup - adjusted y-positions for confluence line
        ax.text(0.05, 0.90, 'PRIMARY:', color=COLORS['primary_blue'],
                fontsize=10, fontweight='bold', ha='left')

        if setup.primary_high > 0:
            tier_color = get_tier_color(setup.primary_tier)

            primary_text = f"{setup.primary_direction} | Zone: {setup.primary_zone_id.replace(setup.ticker + '_', '')} | POC: {format_price((setup.primary_high + setup.primary_low) / 2)}"
            ax.text(0.05, 0.80, primary_text, color=COLORS['text_primary'], fontsize=9, ha='left')

            # V1.1: Show tier with color
            if setup.primary_tier:
                ax.text(0.95, 0.80, setup.primary_tier, color=tier_color, fontsize=10,
                       ha='right', fontweight='bold')

            range_text = f"Range: {format_price(setup.primary_low)} - {format_price(setup.primary_high)} | Target: {format_price(setup.primary_target)} | {setup.primary_rr}"
            ax.text(0.05, 0.71, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')

            # V1.2: Show confluences with wrapping
            if setup.primary_confluences:
                self._draw_wrapped_text(ax, f"Confluences: {setup.primary_confluences}",
                                       0.05, 0.62, COLORS['text_dim'], fontsize=8, max_width=0.90)
        else:
            ax.text(0.05, 0.80, 'No primary setup', color=COLORS['text_dim'], fontsize=9, ha='left', style='italic')

        # Secondary Setup - adjusted y-positions for confluence line
        ax.text(0.05, 0.48, 'SECONDARY:', color=COLORS['secondary_red'],
                fontsize=10, fontweight='bold', ha='left')

        if setup.secondary_high > 0:
            tier_color = get_tier_color(setup.secondary_tier)

            secondary_text = f"{setup.secondary_direction} | Zone: {setup.secondary_zone_id.replace(setup.ticker + '_', '')} | POC: {format_price((setup.secondary_high + setup.secondary_low) / 2)}"
            ax.text(0.05, 0.38, secondary_text, color=COLORS['text_primary'], fontsize=9, ha='left')

            # V1.1: Show tier with color
            if setup.secondary_tier:
                ax.text(0.95, 0.38, setup.secondary_tier, color=tier_color, fontsize=10,
                       ha='right', fontweight='bold')

            range_text = f"Range: {format_price(setup.secondary_low)} - {format_price(setup.secondary_high)} | Target: {format_price(setup.secondary_target)} | {setup.secondary_rr}"
            ax.text(0.05, 0.29, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')

            # V1.2: Show confluences with wrapping
            if setup.secondary_confluences:
                self._draw_wrapped_text(ax, f"Confluences: {setup.secondary_confluences}",
                                       0.05, 0.20, COLORS['text_dim'], fontsize=8, max_width=0.90)
        else:
            ax.text(0.05, 0.38, 'No secondary setup', color=COLORS['text_dim'], fontsize=9, ha='left', style='italic')

    def _draw_wrapped_text(self, ax: plt.Axes, text: str, x: float, y: float,
                           color: str, fontsize: int = 8, max_width: float = 0.90,
                           line_height: float = 0.08):
        """
        Draw text with wrapping to multiple lines.

        Args:
            ax: Axes to draw on
            text: Text to draw
            x: X position (0-1)
            y: Starting Y position (0-1)
            color: Text color
            fontsize: Font size
            max_width: Maximum width as fraction of axes (0-1)
            line_height: Height between lines as fraction of axes
        """
        # Approximate characters per line based on font size and width
        # Assuming ~60 chars fit in max_width at fontsize 8
        chars_per_line = int(60 * (max_width / 0.90) * (8 / fontsize))

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
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

        # Draw each line
        for i, line in enumerate(lines):
            ax.text(x, y - (i * line_height), line, color=color,
                   fontsize=fontsize, ha='left', va='top')
    
    def _build_notes(self, ax: plt.Axes, notes: str, pinescript_string: str):
        """Build Notes section"""
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
                   fontsize=9, ha='left', va='center', style='italic',
                   wrap=True)
        
        # Show PineScript string (truncate if too long for display)
        if pinescript_string:
            display_str = pinescript_string
            if len(display_str) > 80:
                display_str = display_str[:77] + "..."
            ax.text(0.98, 0.12, f'PineScript: {display_str}', color=COLORS['text_dim'],
                   fontsize=6, ha='right', style='italic')
    
    def _build_price_chart(self, ax: plt.Axes, chart_data: ChartData, 
                           setup: SetupData, epoch_pocs: List[float]) -> Tuple[float, float]:
        """Build H1 candlestick chart with zones and POC lines. Returns y-limits for VP."""
        ax.set_facecolor(COLORS['dark_bg'])
        
        bars = chart_data.candle_bars
        
        if bars.empty:
            ax.text(0.5, 0.5, 'No chart data available', color=COLORS['text_muted'],
                   fontsize=14, ha='center', va='center')
            return (0, 100)
        
        n_bars = len(bars)
        
        # Plot candlesticks
        for i, (idx, bar) in enumerate(bars.iterrows()):
            color = COLORS['candle_green'] if bar['close'] >= bar['open'] else COLORS['candle_red']
            
            # Wick
            ax.plot([i, i], [bar['low'], bar['high']], color=color, linewidth=0.8)
            
            # Body
            body_bottom = min(bar['open'], bar['close'])
            body_height = abs(bar['close'] - bar['open'])
            if body_height < 0.01:
                body_height = 0.01
            rect = mpatches.Rectangle((i - 0.3, body_bottom), 0.6, body_height,
                                      facecolor=color, edgecolor=color)
            ax.add_patch(rect)
        
        # Primary Zone (Blue)
        if setup.primary_high > 0 and setup.primary_low > 0:
            ax.axhspan(setup.primary_low, setup.primary_high, 
                      alpha=ZONE_FILL_ALPHA, color=COLORS['primary_blue'], zorder=1)
            poc = (setup.primary_high + setup.primary_low) / 2
            ax.axhline(poc, color=COLORS['primary_blue'], linewidth=1.5, alpha=0.8)
        
        # Secondary Zone (Red)
        if setup.secondary_high > 0 and setup.secondary_low > 0:
            ax.axhspan(setup.secondary_low, setup.secondary_high,
                      alpha=ZONE_FILL_ALPHA, color=COLORS['secondary_red'], zorder=1)
            poc = (setup.secondary_high + setup.secondary_low) / 2
            ax.axhline(poc, color=COLORS['secondary_red'], linewidth=1.5, alpha=0.8)
        
        # Primary Target Line
        if setup.primary_target > 0:
            ax.axhline(setup.primary_target, color=COLORS['primary_blue'],
                      linestyle='-', linewidth=2, alpha=0.9)
        
        # Secondary Target Line
        if setup.secondary_target > 0:
            ax.axhline(setup.secondary_target, color=COLORS['secondary_red'],
                      linestyle='-', linewidth=2, alpha=0.9)
        
        # ========== POC LINES FROM MODULE 04 ==========
        # Draw 10 dashed lines at epoch POC prices
        print("=" * 60)
        print("POC LINES DEBUG")
        print("=" * 60)
        print(f"Epoch POCs received: {len(epoch_pocs)}")
        
        for i, poc_price in enumerate(epoch_pocs):
            if poc_price > 0:
                rank = i + 1
                ax.axhline(poc_price, color=POC_LINE_COLOR, linestyle=POC_LINE_STYLE,
                          linewidth=1.0, alpha=POC_LINE_ALPHA, zorder=2)
                print(f"  POC{rank}: ${poc_price:.2f}")
        print("=" * 60)
        
        # ========== Y-AXIS LIMITS (EPOCH RANGE) ==========
        # Use epoch range for y-axis (full institutional context)
        y_min = chart_data.epoch_low
        y_max = chart_data.epoch_high
        
        # If epoch data unavailable, fall back to candle range
        if y_min == 0 and y_max == 0:
            y_min = bars['low'].min()
            y_max = bars['high'].max()
        
        # Extend to include targets if outside range
        if setup.primary_target > 0:
            y_max = max(y_max, setup.primary_target)
            y_min = min(y_min, setup.primary_target)
        if setup.secondary_target > 0:
            y_max = max(y_max, setup.secondary_target)
            y_min = min(y_min, setup.secondary_target)
        
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
        tick_interval = max(1, n_bars // 8)
        tick_positions = list(range(0, n_bars, tick_interval))
        tick_labels = [bars.index[i].strftime('%m/%d %H:%M') for i in tick_positions if i < n_bars]
        ax.set_xticks(tick_positions[:len(tick_labels)])
        ax.set_xticklabels(tick_labels, color=COLORS['text_primary'], fontsize=8, rotation=45, ha='right')
        ax.set_xlabel('Time (ET)', color=COLORS['text_primary'], fontsize=10)
        
        # ========== LEFT SIDE PRICE LABELS ==========
        label_offset = -3
        
        # POC labels on left side
        for i, poc_price in enumerate(epoch_pocs):
            if poc_price > 0 and y_min <= poc_price <= y_max:
                rank = i + 1
                ax.text(label_offset, poc_price, f'POC{rank}: ${poc_price:.2f}',
                       color=POC_LINE_COLOR, fontsize=7, va='center', ha='right',
                       alpha=0.8, bbox=dict(boxstyle='round,pad=0.15', 
                       facecolor=COLORS['dark_bg'], edgecolor=POC_LINE_COLOR, 
                       alpha=0.5, linewidth=0.5))
        
        # Primary/Secondary zone midpoint labels
        if setup.primary_high > 0:
            primary_mid = (setup.primary_high + setup.primary_low) / 2
            ax.text(label_offset, primary_mid, f'${primary_mid:.2f}',
                   color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))
        
        if setup.primary_target > 0:
            ax.text(label_offset, setup.primary_target, f'${setup.primary_target:.2f}',
                   color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))
        
        if setup.secondary_high > 0:
            secondary_mid = (setup.secondary_high + setup.secondary_low) / 2
            ax.text(label_offset, secondary_mid, f'${secondary_mid:.2f}',
                   color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                   bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))
        
        if setup.secondary_target > 0:
            ax.text(label_offset, setup.secondary_target, f'${setup.secondary_target:.2f}',
                   color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))
        
        return (y_min, y_max)
    
    def _build_volume_profile(self, ax: plt.Axes, chart_data: ChartData, 
                              y_limits: Tuple[float, float]):
        """Build Volume Profile sidebar from full epoch data (single color)"""
        ax.set_facecolor(COLORS['dark_bg'])
        
        volume_profile = chart_data.vbp_volume_profile
        
        # DEBUG
        print("=" * 60)
        print("VOLUME PROFILE RENDERING DEBUG")
        print("=" * 60)
        print(f"Epoch: {chart_data.epoch_start_date}")
        print(f"Epoch range: ${chart_data.epoch_low:.2f} - ${chart_data.epoch_high:.2f}")
        print(f"VbP bars fetched: {chart_data.vbp_bar_count}")
        print(f"Total VP levels: {len(volume_profile)}")
        
        if not volume_profile:
            ax.text(0.5, 0.5, 'No VP', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return
        
        # Filter to y_limits range
        y_min, y_max = y_limits
        filtered_vp = {p: v for p, v in volume_profile.items() if y_min <= p <= y_max}
        
        print(f"Y-axis range: ${y_min:.2f} - ${y_max:.2f}")
        print(f"Filtered VP levels: {len(filtered_vp)}")
        print("=" * 60)
        
        if not filtered_vp:
            ax.text(0.5, 0.5, 'No VP in range', color=COLORS['text_muted'],
                   fontsize=10, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return
        
        # Sort by price
        sorted_prices = sorted(filtered_vp.keys())
        volumes = [filtered_vp[p] for p in sorted_prices]
        
        # Single color for all bars
        bar_color = VBP_COLOR
        
        # Bar height at $0.01 fidelity
        bar_height = 0.01
        
        ax.barh(sorted_prices, volumes, height=bar_height,
               color=bar_color, alpha=0.8, edgecolor='none')
        
        ax.set_xlabel('Volume', color=COLORS['text_primary'], fontsize=9)
        ax.tick_params(colors=COLORS['text_primary'], labelleft=False, labelsize=8)
        
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(COLORS['border_light'])
        
        ax.set_ylim(y_limits)
    
    def to_bytes(self) -> bytes:
        """Convert current figure to PNG bytes"""
        if self.fig is None:
            return b''
        
        buf = io.BytesIO()
        self.fig.savefig(buf, format='png', dpi=DPI, facecolor=COLORS['dark_bg'],
                        edgecolor='none', bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
    
    def save(self, filepath: str):
        """Save current figure to file"""
        if self.fig is None:
            return
        
        self.fig.savefig(filepath, dpi=DPI, facecolor=COLORS['dark_bg'],
                        edgecolor='none', bbox_inches='tight')
    
    def close(self):
        """Close the figure"""
        if self.fig:
            plt.close(self.fig)
            self.fig = None
