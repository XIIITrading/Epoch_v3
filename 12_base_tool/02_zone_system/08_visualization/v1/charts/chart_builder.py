# chart_builder.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\charts\
# Purpose: Build complete visualization chart with tables and price chart

"""
Chart Builder for Module 08 Visualization

Creates a single-page visualization with:
- Left panel: Market Structure, Ticker Structure, Zone Results, Setup Analysis, Notes
- Right panel: M15 candlestick chart with zones + Volume Profile sidebar

Color scheme matches PineScript indicators.
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
    TABLE_HEIGHT_RATIOS, VP_BASE_COLOR, VP_HVN_COLOR
)
from data_readers.excel_reader import VisualizationData, MarketStructure, TickerStructure, ZoneResult, SetupData
from data_readers.polygon_fetcher import ChartData


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


def format_price(price: float) -> str:
    """Format price for display"""
    if price == 0 or pd.isna(price):
        return "-"
    return f"${price:.2f}"


# =============================================================================
# CHART BUILDER CLASS
# =============================================================================

class VisualizationChartBuilder:
    """Build complete visualization charts"""
    
    def __init__(self):
        """Initialize chart builder"""
        self.fig = None
        self.axes = {}
    
    def build(self, viz_data: VisualizationData, chart_data: ChartData,
              session_type: str = 'premarket', notes: str = "") -> plt.Figure:
        """
        Build complete visualization figure.
        
        Args:
            viz_data: Data from Excel (zones, setup, structure)
            chart_data: Data from Polygon (M15 bars, volume profile)
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
        self._build_notes(self.fig.add_subplot(left_gs[4]), notes, viz_data.setup.setup_string)
        
        # Build chart and volume profile with shared y-axis
        ax_chart = self.fig.add_subplot(right_gs[0])
        ax_vp = self.fig.add_subplot(right_gs[1], sharey=ax_chart)
        
        # Build chart first to get y-limits, then VP
        y_limits = self._build_price_chart(ax_chart, chart_data, viz_data.setup)
        self._build_volume_profile(ax_vp, chart_data, y_limits)
        
        # Title
        session_label = "Pre-Market Report" if session_type == 'premarket' else "Post-Market Report"
        date_str = datetime.now().strftime('%Y-%m-%d')
        composite = viz_data.ticker_structure.composite or "N/A"
        
        self.fig.suptitle(
            f'{viz_data.ticker} | {session_label} | {date_str} | Composite: {composite}',
            color=COLORS['text_primary'], fontsize=16, fontweight='bold', y=0.97
        )
        
        # Subtitle
        price = viz_data.ticker_structure.price
        atr = viz_data.ticker_structure.d1_atr
        self.fig.text(0.5, 0.935, 
                     f'Current Price: ${price:.2f} | D1 ATR: ${atr:.2f}',
                     color=COLORS['text_muted'], fontsize=11, ha='center')
        
        return self.fig
    
    def _build_market_structure(self, ax: plt.Axes, data: List[MarketStructure]):
        """Build Market Structure table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title - positioned higher
        ax.text(0.5, 0.95, 'MARKET STRUCTURE', color=COLORS['text_primary'],
                fontsize=11, fontweight='bold', ha='center', va='top')
        
        # Headers - with more space below title
        headers = ['Index', 'D1', 'H4', 'H1', 'M15', 'Comp']
        x_positions = [0.08, 0.22, 0.36, 0.50, 0.64, 0.82]
        
        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.75, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')
        
        # Data rows - adjusted positions
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
            
            # Row separator
            if row_idx < 2:
                ax.axhline(y - 0.10, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)
    
    def _build_ticker_structure(self, ax: plt.Axes, data: TickerStructure):
        """Build Ticker Structure table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title - positioned higher
        ax.text(0.5, 0.95, f'TICKER STRUCTURE: {data.ticker}', color=COLORS['text_primary'],
                fontsize=11, fontweight='bold', ha='center', va='top')
        
        # Column positions
        x_positions = [0.22, 0.36, 0.50, 0.64, 0.82]
        tf_labels = ['D1', 'H4', 'H1', 'M15', 'Comp']
        
        # Headers - with more space below title
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
        """Build Zone Results table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title - positioned higher
        ax.text(0.5, 0.97, 'ZONE RESULTS (L2-L5)', color=COLORS['text_primary'],
                fontsize=11, fontweight='bold', ha='center', va='top')
        
        # Headers - with more space below title
        headers = ['Zone ID', 'POC', 'High', 'Low', 'Rank', 'Score']
        x_positions = [0.12, 0.28, 0.42, 0.56, 0.72, 0.88]
        
        for i, header in enumerate(headers):
            ax.text(x_positions[i], 0.88, header, color=COLORS['text_muted'],
                   fontsize=9, ha='center', fontweight='bold')
        
        # Header separator line
        ax.axhline(0.84, color=COLORS['border'], linewidth=0.5, xmin=0.02, xmax=0.98)
        
        # Data rows (max 6 zones)
        max_rows = min(6, len(zones))
        row_height = 0.12
        
        for row_idx in range(max_rows):
            zone = zones[row_idx]
            y = 0.76 - (row_idx * row_height)
            
            # Zone ID (shortened)
            zone_id_short = zone.zone_id.replace(f'{zone.ticker}_', '')
            ax.text(x_positions[0], y, zone_id_short, color=COLORS['text_primary'],
                   fontsize=9, ha='center')
            
            # POC, High, Low
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
            
            # Score
            ax.text(x_positions[5], y, f'{zone.score:.1f}', 
                   color=COLORS['text_primary'], fontsize=9, ha='center')
            
            # Row separator
            if row_idx < max_rows - 1:
                ax.axhline(y - row_height/2 + 0.02, color=COLORS['border'], 
                          linewidth=0.5, xmin=0.02, xmax=0.98)
        
        if len(zones) == 0:
            ax.text(0.5, 0.5, 'No zones found', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', style='italic')
    
    def _build_setup_analysis(self, ax: plt.Axes, setup: SetupData):
        """Build Setup Analysis table"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title - positioned higher
        ax.text(0.5, 0.97, 'SETUP ANALYSIS', color=COLORS['text_primary'],
                fontsize=11, fontweight='bold', ha='center', va='top')
        
        # Primary Setup
        ax.text(0.05, 0.78, 'PRIMARY:', color=COLORS['primary_blue'],
                fontsize=10, fontweight='bold', ha='left')
        
        if setup.primary_high > 0:
            primary_text = f"{setup.primary_direction} | Zone: {setup.primary_zone_id.replace(setup.ticker + '_', '')} | POC: {format_price((setup.primary_high + setup.primary_low) / 2)}"
            ax.text(0.05, 0.65, primary_text, color=COLORS['text_primary'], fontsize=9, ha='left')
            
            range_text = f"Range: {format_price(setup.primary_low)} - {format_price(setup.primary_high)} | Target: {format_price(setup.primary_target)} | {setup.primary_rr}"
            ax.text(0.05, 0.54, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')
        else:
            ax.text(0.05, 0.65, 'No primary setup', color=COLORS['text_dim'], fontsize=9, ha='left', style='italic')
        
        # Secondary Setup
        ax.text(0.05, 0.38, 'SECONDARY:', color=COLORS['secondary_red'],
                fontsize=10, fontweight='bold', ha='left')
        
        if setup.secondary_high > 0:
            secondary_text = f"{setup.secondary_direction} | Zone: {setup.secondary_zone_id.replace(setup.ticker + '_', '')} | POC: {format_price((setup.secondary_high + setup.secondary_low) / 2)}"
            ax.text(0.05, 0.25, secondary_text, color=COLORS['text_primary'], fontsize=9, ha='left')
            
            range_text = f"Range: {format_price(setup.secondary_low)} - {format_price(setup.secondary_high)} | Target: {format_price(setup.secondary_target)} | {setup.secondary_rr}"
            ax.text(0.05, 0.14, range_text, color=COLORS['text_muted'], fontsize=9, ha='left')
        else:
            ax.text(0.05, 0.25, 'No secondary setup', color=COLORS['text_dim'], fontsize=9, ha='left', style='italic')
    
    def _build_notes(self, ax: plt.Axes, notes: str, setup_string: str):
        """Build Notes section"""
        ax.set_facecolor(COLORS['notes_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(COLORS['border'])
        
        # Title
        ax.text(0.02, 0.88, 'NOTES:', color=COLORS['text_muted'],
                fontsize=10, fontweight='bold', ha='left')
        
        # Notes text
        if notes:
            ax.text(0.02, 0.55, notes, color=COLORS['text_dim'],
                   fontsize=9, ha='left', va='center', style='italic',
                   wrap=True)
        
        # Setup string at bottom
        if setup_string:
            ax.text(0.98, 0.12, f'String: {setup_string}', color=COLORS['text_dim'],
                   fontsize=8, ha='right', style='italic')
    
    def _build_price_chart(self, ax: plt.Axes, chart_data: ChartData, setup: SetupData) -> Tuple[float, float]:
        """Build M15 candlestick chart with zones. Returns y-limits for VP."""
        ax.set_facecolor(COLORS['dark_bg'])
        
        bars = chart_data.bars
        
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
            rect = mpatches.Rectangle((i - 0.2, body_bottom), 0.4, body_height,
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
        
        # Calculate y-axis limits from bar data (highest high, lowest low)
        y_min = bars['low'].min()
        y_max = bars['high'].max()
        
        # Extend to include targets if outside bar range
        if setup.primary_target > 0:
            y_max = max(y_max, setup.primary_target)
            y_min = min(y_min, setup.primary_target)
        if setup.secondary_target > 0:
            y_max = max(y_max, setup.secondary_target)
            y_min = min(y_min, setup.secondary_target)
        if setup.primary_high > 0:
            y_max = max(y_max, setup.primary_high)
            y_min = min(y_min, setup.primary_low)
        if setup.secondary_high > 0:
            y_max = max(y_max, setup.secondary_high)
            y_min = min(y_min, setup.secondary_low)
        
        # Add padding
        padding = (y_max - y_min) * 0.03
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
        
        # === LEFT SIDE PRICE LABELS ===
        # Add price labels on left side for key levels
        label_offset = -3  # Position to the left of the y-axis
        
        if setup.primary_target > 0:
            ax.text(label_offset, setup.primary_target, f'{setup.primary_target:.2f}',
                   color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))
        
        if setup.primary_high > 0:
            primary_mid = (setup.primary_high + setup.primary_low) / 2
            ax.text(label_offset, primary_mid, f'{primary_mid:.2f}',
                   color=COLORS['primary_blue'], fontsize=8, va='center', ha='right',
                   bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['primary_blue'], alpha=0.8))
        
        if setup.secondary_target > 0:
            ax.text(label_offset, setup.secondary_target, f'{setup.secondary_target:.2f}',
                   color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))
        
        if setup.secondary_high > 0:
            secondary_mid = (setup.secondary_high + setup.secondary_low) / 2
            ax.text(label_offset, secondary_mid, f'{secondary_mid:.2f}',
                   color=COLORS['secondary_red'], fontsize=8, va='center', ha='right',
                   bbox=dict(boxstyle='round,pad=0.2', 
                   facecolor=COLORS['dark_bg'], edgecolor=COLORS['secondary_red'], alpha=0.8))
        
        return (y_min, y_max)
    
    def _build_volume_profile(self, ax: plt.Axes, chart_data: ChartData, 
                              y_limits: Tuple[float, float]):
        """Build Volume Profile sidebar with HVN highlighting at $0.01 fidelity"""
        ax.set_facecolor(COLORS['dark_bg'])
        
        volume_profile = chart_data.volume_profile
        hvn_zones = chart_data.hvn_zones
        
        # DEBUG: Log HVN zones being used
        print("=" * 60)
        print("VOLUME PROFILE RENDERING DEBUG")
        print("=" * 60)
        print(f"M5 ATR used: ${chart_data.m5_atr:.4f}")
        print(f"Number of HVN zones: {len(hvn_zones)}")
        for zone in hvn_zones:
            print(f"  Zone #{zone.rank}: POC=${zone.poc_price:.2f}, "
                  f"Range=${zone.zone_low:.2f}-${zone.zone_high:.2f}, "
                  f"Width=${zone.zone_high - zone.zone_low:.2f}")
        
        if not volume_profile:
            ax.text(0.5, 0.5, 'No VP', color=COLORS['text_muted'],
                   fontsize=11, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return
        
        # Filter volume profile to y_limits range
        y_min, y_max = y_limits
        filtered_vp = {p: v for p, v in volume_profile.items() if y_min <= p <= y_max}
        
        print(f"Y-axis range: ${y_min:.2f} - ${y_max:.2f}")
        print(f"Total VP levels: {len(volume_profile)}")
        print(f"Filtered VP levels: {len(filtered_vp)}")
        
        if not filtered_vp:
            ax.text(0.5, 0.5, 'No VP in range', color=COLORS['text_muted'],
                   fontsize=10, ha='center', va='center', rotation=90)
            ax.tick_params(labelleft=False)
            return
        
        # Sort by price - NO AGGREGATION, keep $0.01 fidelity
        sorted_prices = sorted(filtered_vp.keys())
        volumes = [filtered_vp[p] for p in sorted_prices]
        
        # Determine colors - base color for all, highlight for HVN zones
        colors = []
        hvn_price_count = 0
        for price in sorted_prices:
            is_hvn = chart_data.is_in_hvn_zone(price)
            if is_hvn:
                hvn_price_count += 1
            colors.append(VP_HVN_COLOR if is_hvn else VP_BASE_COLOR)
        
        print(f"Prices marked as HVN: {hvn_price_count} out of {len(sorted_prices)}")
        print(f"HVN percentage: {100*hvn_price_count/len(sorted_prices):.1f}%")
        
        # Calculate expected HVN coverage
        expected_hvn_levels = int(chart_data.m5_atr / 0.01) * len(hvn_zones)
        print(f"Expected HVN levels (10 zones × {chart_data.m5_atr/0.01:.0f} levels): ~{expected_hvn_levels}")
        print("=" * 60)
        
        # Use $0.01 as bar height for true fidelity
        bar_height = 0.01
        
        ax.barh(sorted_prices, volumes, height=bar_height,
               color=colors, alpha=0.8, edgecolor='none')
        
        ax.set_xlabel('Volume', color=COLORS['text_primary'], fontsize=9)
        ax.tick_params(colors=COLORS['text_primary'], labelleft=False, labelsize=8)
        
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(COLORS['border_light'])
        
        # Set y-limits to match chart
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
