# trade_chart_builder.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\charts\
# Purpose: Build 4-quadrant trade visualization with M5, H1, M15 charts

"""
Trade Chart Builder for Backtest Visualization

Creates a single-page 4-quadrant visualization:
- Top Left: Trade metrics table
- Top Right: M5 candlestick chart (trade day 09:00-16:00 ET)
- Bottom Left: H1 chart (last 5 trading days)
- Bottom Right: M15 chart (last 3 trading days)

All charts include:
- Candlesticks
- VWAP (anchored to pre-market each day)
- 9 EMA
- 21 EMA
- Volume bars (bottom subplot)
- Zones (Primary/Secondary)
- HVN POC lines

M5 chart additionally shows:
- Entry/Exit markers
- Stop and Target lines
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from sibling modules (adjust path as needed)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config.backtest_config import (
        COLORS, ZONE_FILL_ALPHA, MARKERS,
        PAGE_WIDTH, PAGE_HEIGHT, PDF_DPI,
        M5_START_HOUR, M5_END_HOUR, M5_TIMEFRAME,
        H1_TRADING_DAYS, H1_TIMEFRAME,
        M15_TRADING_DAYS, M15_TIMEFRAME,
        EMA_FAST, EMA_SLOW,
        PRE_MARKET_START, DISPLAY_TIMEZONE
    )
except ImportError:
    # Fallback defaults
    COLORS = {
        'dark_bg': '#1a1a2e', 'chart_bg': '#0f0f1a', 'table_bg': '#16213e',
        'text_primary': '#e0e0e0', 'text_muted': '#888888', 'text_dim': '#666666',
        'primary_blue': '#90bff9', 'secondary_red': '#faa1a4',
        'candle_green': '#26a69a', 'candle_red': '#ef5350',
        'vwap': '#ff9800', 'ema_fast': '#2196f3', 'ema_slow': '#9c27b0',
        'volume_up': '#26a69a80', 'volume_down': '#ef535080',
        'entry_long': '#00c853', 'entry_short': '#ff5252',
        'exit_win': '#2196f3', 'exit_loss': '#ef5350',
        'stop_line': '#ff5722', 'target_line': '#4caf50',
        'poc_line': '#ffffff', 'poc_line_alpha': 0.3,
        'grid': '#2a2a4e', 'border': '#333333',
    }
    ZONE_FILL_ALPHA = 0.15
    MARKERS = {
        'entry_long': {'marker': '^', 'color': '#00c853', 'size': 120},
        'entry_short': {'marker': 'v', 'color': '#ff5252', 'size': 120},
        'exit_win': {'marker': 'o', 'color': '#2196f3', 'size': 80},
        'exit_loss': {'marker': 'o', 'color': '#ef5350', 'size': 80},
    }
    PAGE_WIDTH, PAGE_HEIGHT = 11.0, 8.5
    PDF_DPI = 150
    M5_START_HOUR, M5_END_HOUR, M5_TIMEFRAME = 9, 16, 5
    H1_TRADING_DAYS, H1_TIMEFRAME = 5, 60
    M15_TRADING_DAYS, M15_TIMEFRAME = 3, 15
    EMA_FAST, EMA_SLOW = 9, 21
    PRE_MARKET_START = 4
    DISPLAY_TIMEZONE = 'America/New_York'


# =============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# =============================================================================

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_vwap(df: pd.DataFrame, anchor_hour: int = 4) -> pd.Series:
    """
    Calculate VWAP anchored to pre-market start each day.
    
    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns
        anchor_hour: Hour to reset VWAP (default 4 = 04:00 pre-market)
        
    Returns:
        Series with VWAP values
    """
    if df.empty:
        return pd.Series()
    
    # Typical price
    df = df.copy()
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    
    # Get trading day (reset at anchor_hour)
    df['hour'] = df.index.hour
    df['trading_day'] = df.index.date
    
    # Mark session starts (where VWAP resets)
    df['new_session'] = (df['hour'] == anchor_hour) | (
        (df['hour'] < anchor_hour) & (df['hour'].shift(1) >= anchor_hour)
    )
    
    # Create session groups
    df['session'] = df['new_session'].cumsum()
    
    # Calculate cumulative sums within each session
    df['cum_tp_vol'] = df.groupby('session')['tp_volume'].cumsum()
    df['cum_vol'] = df.groupby('session')['volume'].cumsum()
    
    # VWAP
    vwap = df['cum_tp_vol'] / df['cum_vol']
    
    return vwap


def calculate_volume_colors(df: pd.DataFrame) -> List[str]:
    """Determine volume bar colors based on price direction"""
    colors = []
    for i in range(len(df)):
        if df['close'].iloc[i] >= df['open'].iloc[i]:
            colors.append(COLORS['volume_up'])
        else:
            colors.append(COLORS['volume_down'])
    return colors


# =============================================================================
# TRADE CHART BUILDER CLASS
# =============================================================================

class TradeChartBuilder:
    """Build 4-quadrant trade visualization"""
    
    def __init__(self):
        """Initialize chart builder"""
        self.fig = None
        self.axes = {}
    
    def build(self, trade, m5_bars: pd.DataFrame, h1_bars: pd.DataFrame, 
              m15_bars: pd.DataFrame, zones: Dict = None, 
              hvn_pocs: List[float] = None) -> plt.Figure:
        """
        Build complete 4-quadrant trade visualization.
        
        Args:
            trade: TradeRecord object
            m5_bars: M5 OHLCV DataFrame for trade day
            h1_bars: H1 OHLCV DataFrame (last 5 trading days)
            m15_bars: M15 OHLCV DataFrame (last 3 trading days)
            zones: Dict with 'primary' and 'secondary' zone info
            hvn_pocs: List of HVN POC prices (up to 10)
            
        Returns:
            matplotlib Figure object
        """
        # Create figure (landscape letter size)
        self.fig = plt.figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT), 
                              facecolor=COLORS['dark_bg'], dpi=PDF_DPI)
        
        # Main grid: 2x2 quadrants
        gs = GridSpec(2, 2, figure=self.fig, 
                     left=0.05, right=0.98, top=0.92, bottom=0.05,
                     wspace=0.12, hspace=0.15)
        
        # Top Left: Metrics table
        ax_metrics = self.fig.add_subplot(gs[0, 0])
        self._build_metrics_table(ax_metrics, trade)
        
        # Top Right: M5 Chart with volume subplot
        gs_m5 = gs[0, 1].subgridspec(2, 1, height_ratios=[4, 1], hspace=0.02)
        ax_m5 = self.fig.add_subplot(gs_m5[0])
        ax_m5_vol = self.fig.add_subplot(gs_m5[1], sharex=ax_m5)
        self._build_m5_chart(ax_m5, ax_m5_vol, trade, m5_bars, zones, hvn_pocs)
        
        # Bottom Left: H1 Chart with volume subplot
        gs_h1 = gs[1, 0].subgridspec(2, 1, height_ratios=[4, 1], hspace=0.02)
        ax_h1 = self.fig.add_subplot(gs_h1[0])
        ax_h1_vol = self.fig.add_subplot(gs_h1[1], sharex=ax_h1)
        self._build_multi_day_chart(ax_h1, ax_h1_vol, h1_bars, 'H1', zones, hvn_pocs)
        
        # Bottom Right: M15 Chart with volume subplot
        gs_m15 = gs[1, 1].subgridspec(2, 1, height_ratios=[4, 1], hspace=0.02)
        ax_m15 = self.fig.add_subplot(gs_m15[0])
        ax_m15_vol = self.fig.add_subplot(gs_m15[1], sharex=ax_m15)
        self._build_multi_day_chart(ax_m15, ax_m15_vol, m15_bars, 'M15', zones, hvn_pocs)
        
        # Main title
        result_color = COLORS['entry_long'] if trade.win else COLORS['exit_loss']
        result_text = 'WIN' if trade.win else 'LOSS'
        
        self.fig.suptitle(
            f'{trade.ticker} | {trade.date} | {trade.model} | {trade.direction} | '
            f'{result_text}: {trade.pnl_r:+.2f}R (${trade.pnl_dollars:+.2f})',
            color=result_color, fontsize=14, fontweight='bold', y=0.97
        )
        
        return self.fig
    
    def _build_metrics_table(self, ax: plt.Axes, trade):
        """Build trade metrics table (Top Left quadrant)"""
        ax.set_facecolor(COLORS['table_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.97, 'TRADE DETAILS', color=COLORS['text_primary'],
                fontsize=12, fontweight='bold', ha='center', va='top')
        
        # Trade Info Section
        y = 0.88
        line_height = 0.055
        
        # Column 1: Basic Info
        col1_x = 0.05
        ax.text(col1_x, y, 'ENTRY', color=COLORS['text_muted'], fontsize=9, fontweight='bold')
        y -= line_height
        
        items = [
            ('Time:', trade.entry_time),
            ('Price:', f'${trade.entry_price:.2f}'),
            ('Zone:', trade.zone_type),
            ('Zone High:', f'${trade.zone_high:.2f}'),
            ('Zone Low:', f'${trade.zone_low:.2f}'),
            ('Zone POC:', f'${trade.zone_poc:.2f}'),
        ]
        
        for label, value in items:
            ax.text(col1_x, y, label, color=COLORS['text_muted'], fontsize=8)
            ax.text(col1_x + 0.22, y, str(value), color=COLORS['text_primary'], fontsize=8)
            y -= line_height
        
        # Column 2: Risk Management
        y = 0.88
        col2_x = 0.52
        ax.text(col2_x, y, 'RISK MGMT', color=COLORS['text_muted'], fontsize=9, fontweight='bold')
        y -= line_height
        
        items = [
            ('Stop:', f'${trade.stop_price:.2f}'),
            ('Target 3R:', f'${trade.target_3r:.2f}'),
            ('Target Calc:', f'${trade.target_calc:.2f}'),
            ('Target Used:', trade.target_used),
            ('Risk:', f'${trade.risk:.2f}'),
        ]
        
        for label, value in items:
            ax.text(col2_x, y, label, color=COLORS['text_muted'], fontsize=8)
            ax.text(col2_x + 0.22, y, str(value), color=COLORS['text_primary'], fontsize=8)
            y -= line_height
        
        # Exit Section
        y -= line_height * 0.5
        ax.axhline(y + line_height * 0.3, color=COLORS['border'], linewidth=0.5, 
                   xmin=0.03, xmax=0.97)
        y -= line_height * 0.5
        
        ax.text(col1_x, y, 'EXIT', color=COLORS['text_muted'], fontsize=9, fontweight='bold')
        ax.text(col2_x, y, 'RESULT', color=COLORS['text_muted'], fontsize=9, fontweight='bold')
        y -= line_height
        
        # Exit info
        ax.text(col1_x, y, 'Time:', color=COLORS['text_muted'], fontsize=8)
        ax.text(col1_x + 0.22, y, trade.exit_time, color=COLORS['text_primary'], fontsize=8)
        
        result_color = COLORS['entry_long'] if trade.win else COLORS['exit_loss']
        ax.text(col2_x, y, 'P&L ($):', color=COLORS['text_muted'], fontsize=8)
        ax.text(col2_x + 0.22, y, f'${trade.pnl_dollars:+.2f}', color=result_color, 
                fontsize=8, fontweight='bold')
        y -= line_height
        
        ax.text(col1_x, y, 'Price:', color=COLORS['text_muted'], fontsize=8)
        ax.text(col1_x + 0.22, y, f'${trade.exit_price:.2f}', color=COLORS['text_primary'], fontsize=8)
        
        ax.text(col2_x, y, 'P&L (R):', color=COLORS['text_muted'], fontsize=8)
        ax.text(col2_x + 0.22, y, f'{trade.pnl_r:+.2f}R', color=result_color, 
                fontsize=8, fontweight='bold')
        y -= line_height
        
        ax.text(col1_x, y, 'Reason:', color=COLORS['text_muted'], fontsize=8)
        ax.text(col1_x + 0.22, y, trade.exit_reason, color=COLORS['text_primary'], fontsize=8)
        
        ax.text(col2_x, y, 'Duration:', color=COLORS['text_muted'], fontsize=8)
        ax.text(col2_x + 0.22, y, f'{trade.duration_minutes} min', 
                color=COLORS['text_primary'], fontsize=8)
        y -= line_height
        
        # Win/Loss indicator box
        y -= line_height
        box_width = 0.3
        box_height = 0.08
        box_x = 0.35
        
        result_text = 'WIN' if trade.win else 'LOSS'
        box_color = COLORS['entry_long'] if trade.win else COLORS['exit_loss']
        
        rect = mpatches.FancyBboxPatch((box_x, y), box_width, box_height,
                                        boxstyle="round,pad=0.02",
                                        facecolor=box_color, edgecolor=box_color,
                                        alpha=0.3)
        ax.add_patch(rect)
        ax.text(box_x + box_width/2, y + box_height/2, result_text,
                color=box_color, fontsize=14, fontweight='bold',
                ha='center', va='center')
    
    def _build_m5_chart(self, ax: plt.Axes, ax_vol: plt.Axes, trade,
                        bars: pd.DataFrame, zones: Dict = None, 
                        hvn_pocs: List[float] = None):
        """Build M5 candlestick chart for trade day (Top Right quadrant)"""
        ax.set_facecolor(COLORS['chart_bg'])
        ax_vol.set_facecolor(COLORS['chart_bg'])
        
        if bars.empty:
            ax.text(0.5, 0.5, 'No M5 data available', color=COLORS['text_muted'],
                   fontsize=12, ha='center', va='center', transform=ax.transAxes)
            return
        
        # Filter to trade day window (09:00-16:00)
        bars = bars.copy()
        
        n_bars = len(bars)
        
        # Calculate indicators
        bars['ema_fast'] = calculate_ema(bars['close'], EMA_FAST)
        bars['ema_slow'] = calculate_ema(bars['close'], EMA_SLOW)
        bars['vwap'] = calculate_vwap(bars, anchor_hour=PRE_MARKET_START)
        
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
        
        # Plot indicators
        x_range = range(len(bars))
        ax.plot(x_range, bars['ema_fast'].values, color=COLORS['ema_fast'], 
                linewidth=1, label=f'{EMA_FAST} EMA', alpha=0.8)
        ax.plot(x_range, bars['ema_slow'].values, color=COLORS['ema_slow'], 
                linewidth=1, label=f'{EMA_SLOW} EMA', alpha=0.8)
        ax.plot(x_range, bars['vwap'].values, color=COLORS['vwap'], 
                linewidth=1.5, label='VWAP', alpha=0.9)
        
        # Plot zones
        if zones:
            self._draw_zones(ax, zones)
        
        # Plot HVN POCs
        if hvn_pocs:
            self._draw_hvn_pocs(ax, hvn_pocs)
        
        # Plot entry/exit markers
        self._draw_trade_markers(ax, trade, bars)
        
        # Plot stop and target lines
        self._draw_stop_target_lines(ax, trade, n_bars)
        
        # Volume bars
        vol_colors = calculate_volume_colors(bars)
        ax_vol.bar(x_range, bars['volume'].values, color=vol_colors, width=0.6)
        
        # Formatting
        y_min = bars['low'].min()
        y_max = bars['high'].max()
        
        # Extend for stop/target if outside range
        y_min = min(y_min, trade.stop_price) - (y_max - y_min) * 0.02
        y_max = max(y_max, trade.target_price) + (y_max - y_min) * 0.02
        
        ax.set_ylim(y_min, y_max)
        ax.set_xlim(-1, n_bars + 1)
        
        # X-axis time labels
        self._format_time_axis(ax, ax_vol, bars)
        
        ax.set_title(f'M5 Chart | {trade.date} | 09:00-16:00 ET', 
                    color=COLORS['text_primary'], fontsize=10, pad=5)
        ax.set_ylabel('Price', color=COLORS['text_primary'], fontsize=9)
        ax_vol.set_ylabel('Vol', color=COLORS['text_primary'], fontsize=8)
        
        ax.tick_params(colors=COLORS['text_primary'], labelsize=8)
        ax_vol.tick_params(colors=COLORS['text_primary'], labelsize=7)
        
        ax.legend(loc='upper left', fontsize=7, facecolor=COLORS['chart_bg'],
                 edgecolor=COLORS['border'], labelcolor=COLORS['text_primary'])
        
        # Grid
        ax.grid(True, alpha=0.2, color=COLORS['grid'])
        ax.set_axisbelow(True)
        
        for spine in ax.spines.values():
            spine.set_color(COLORS['border'])
        for spine in ax_vol.spines.values():
            spine.set_color(COLORS['border'])
    
    def _build_multi_day_chart(self, ax: plt.Axes, ax_vol: plt.Axes,
                               bars: pd.DataFrame, timeframe: str,
                               zones: Dict = None, hvn_pocs: List[float] = None):
        """Build H1 or M15 multi-day chart (Bottom quadrants)"""
        ax.set_facecolor(COLORS['chart_bg'])
        ax_vol.set_facecolor(COLORS['chart_bg'])
        
        if bars.empty:
            ax.text(0.5, 0.5, f'No {timeframe} data available', color=COLORS['text_muted'],
                   fontsize=12, ha='center', va='center', transform=ax.transAxes)
            return
        
        bars = bars.copy()
        n_bars = len(bars)
        
        # Calculate indicators
        bars['ema_fast'] = calculate_ema(bars['close'], EMA_FAST)
        bars['ema_slow'] = calculate_ema(bars['close'], EMA_SLOW)
        bars['vwap'] = calculate_vwap(bars, anchor_hour=PRE_MARKET_START)
        
        # Plot candlesticks
        for i, (idx, bar) in enumerate(bars.iterrows()):
            color = COLORS['candle_green'] if bar['close'] >= bar['open'] else COLORS['candle_red']
            
            # Wick
            ax.plot([i, i], [bar['low'], bar['high']], color=color, linewidth=0.6)
            
            # Body
            body_bottom = min(bar['open'], bar['close'])
            body_height = abs(bar['close'] - bar['open'])
            if body_height < 0.01:
                body_height = 0.01
            
            bar_width = 0.4 if timeframe == 'M15' else 0.5
            rect = mpatches.Rectangle((i - bar_width/2, body_bottom), bar_width, body_height,
                                      facecolor=color, edgecolor=color)
            ax.add_patch(rect)
        
        # Plot indicators
        x_range = range(len(bars))
        ax.plot(x_range, bars['ema_fast'].values, color=COLORS['ema_fast'], 
                linewidth=1, label=f'{EMA_FAST} EMA', alpha=0.8)
        ax.plot(x_range, bars['ema_slow'].values, color=COLORS['ema_slow'], 
                linewidth=1, label=f'{EMA_SLOW} EMA', alpha=0.8)
        ax.plot(x_range, bars['vwap'].values, color=COLORS['vwap'], 
                linewidth=1.5, label='VWAP', alpha=0.9)
        
        # Plot zones
        if zones:
            self._draw_zones(ax, zones)
        
        # Plot HVN POCs
        if hvn_pocs:
            self._draw_hvn_pocs(ax, hvn_pocs)
        
        # Volume bars
        vol_colors = calculate_volume_colors(bars)
        ax_vol.bar(x_range, bars['volume'].values, color=vol_colors, width=0.6)
        
        # Formatting
        y_min = bars['low'].min()
        y_max = bars['high'].max()
        padding = (y_max - y_min) * 0.02
        
        ax.set_ylim(y_min - padding, y_max + padding)
        ax.set_xlim(-1, n_bars + 1)
        
        # X-axis formatting with day separators
        self._format_multiday_axis(ax, ax_vol, bars, timeframe)
        
        days = H1_TRADING_DAYS if timeframe == 'H1' else M15_TRADING_DAYS
        ax.set_title(f'{timeframe} Chart | Last {days} Trading Days', 
                    color=COLORS['text_primary'], fontsize=10, pad=5)
        ax.set_ylabel('Price', color=COLORS['text_primary'], fontsize=9)
        ax_vol.set_ylabel('Vol', color=COLORS['text_primary'], fontsize=8)
        
        ax.tick_params(colors=COLORS['text_primary'], labelsize=8)
        ax_vol.tick_params(colors=COLORS['text_primary'], labelsize=7)
        
        ax.legend(loc='upper left', fontsize=7, facecolor=COLORS['chart_bg'],
                 edgecolor=COLORS['border'], labelcolor=COLORS['text_primary'])
        
        # Grid
        ax.grid(True, alpha=0.2, color=COLORS['grid'])
        ax.set_axisbelow(True)
        
        for spine in ax.spines.values():
            spine.set_color(COLORS['border'])
        for spine in ax_vol.spines.values():
            spine.set_color(COLORS['border'])
    
    def _draw_zones(self, ax: plt.Axes, zones: Dict):
        """Draw Primary and Secondary zones"""
        # Primary zone (blue)
        if 'primary' in zones and zones['primary']:
            p = zones['primary']
            if p.get('high', 0) > 0 and p.get('low', 0) > 0:
                ax.axhspan(p['low'], p['high'], alpha=ZONE_FILL_ALPHA, 
                          color=COLORS['primary_blue'], zorder=1)
                # POC line
                poc = (p['high'] + p['low']) / 2
                ax.axhline(poc, color=COLORS['primary_blue'], linewidth=1, alpha=0.7)
        
        # Secondary zone (red)
        if 'secondary' in zones and zones['secondary']:
            s = zones['secondary']
            if s.get('high', 0) > 0 and s.get('low', 0) > 0:
                ax.axhspan(s['low'], s['high'], alpha=ZONE_FILL_ALPHA, 
                          color=COLORS['secondary_red'], zorder=1)
                # POC line
                poc = (s['high'] + s['low']) / 2
                ax.axhline(poc, color=COLORS['secondary_red'], linewidth=1, alpha=0.7)
    
    def _draw_hvn_pocs(self, ax: plt.Axes, hvn_pocs: List[float]):
        """Draw HVN POC lines (dashed white)"""
        for i, poc in enumerate(hvn_pocs):
            if poc > 0:
                ax.axhline(poc, color=COLORS['poc_line'], linestyle='--',
                          linewidth=0.8, alpha=COLORS['poc_line_alpha'], zorder=2)
    
    def _draw_trade_markers(self, ax: plt.Axes, trade, bars: pd.DataFrame):
        """Draw entry and exit markers on M5 chart"""
        if bars.empty:
            return
        
        # Find entry bar index
        entry_bar_idx = self._find_bar_index(bars, trade.entry_time)
        exit_bar_idx = self._find_bar_index(bars, trade.exit_time)
        
        # Entry marker
        if entry_bar_idx is not None:
            marker_key = 'entry_long' if trade.is_long else 'entry_short'
            marker_style = MARKERS[marker_key]
            ax.scatter([entry_bar_idx], [trade.entry_price], 
                      marker=marker_style['marker'],
                      color=marker_style['color'],
                      s=marker_style['size'],
                      zorder=10,
                      edgecolors='white',
                      linewidths=0.5)
        
        # Exit marker
        if exit_bar_idx is not None:
            marker_key = 'exit_win' if trade.win else 'exit_loss'
            marker_style = MARKERS[marker_key]
            ax.scatter([exit_bar_idx], [trade.exit_price],
                      marker=marker_style['marker'],
                      color=marker_style['color'],
                      s=marker_style['size'],
                      zorder=10,
                      edgecolors='white',
                      linewidths=0.5)
        
        # Trade path line (entry to exit)
        if entry_bar_idx is not None and exit_bar_idx is not None:
            path_color = COLORS['entry_long'] if trade.pnl_r > 0 else COLORS['exit_loss']
            ax.plot([entry_bar_idx, exit_bar_idx], 
                   [trade.entry_price, trade.exit_price],
                   color=path_color, linestyle='--', linewidth=1, alpha=0.5)
    
    def _draw_stop_target_lines(self, ax: plt.Axes, trade, n_bars: int):
        """Draw horizontal stop and target lines"""
        # Stop line (orange dashed)
        ax.axhline(trade.stop_price, color=COLORS['stop_line'],
                  linestyle='--', linewidth=1.5, alpha=0.8)
        ax.text(n_bars - 1, trade.stop_price, f' STOP ${trade.stop_price:.2f}',
               color=COLORS['stop_line'], fontsize=7, va='center')
        
        # Target line (green dashed)
        ax.axhline(trade.target_price, color=COLORS['target_line'],
                  linestyle='--', linewidth=1.5, alpha=0.8)
        ax.text(n_bars - 1, trade.target_price, f' TARGET ${trade.target_price:.2f}',
               color=COLORS['target_line'], fontsize=7, va='center')
    
    def _find_bar_index(self, bars: pd.DataFrame, time_str: str) -> Optional[int]:
        """Find bar index for a given time string"""
        if bars.empty or not time_str:
            return None
        
        try:
            # Parse time
            target_time = datetime.strptime(time_str, '%H:%M:%S').time()
            
            # Find closest bar
            for i, idx in enumerate(bars.index):
                bar_time = idx.time()
                if bar_time >= target_time:
                    return max(0, i - 1) if i > 0 else 0
            
            return len(bars) - 1  # Return last bar if time is past
            
        except Exception as e:
            logger.warning(f"Error finding bar index for time {time_str}: {e}")
            return None
    
    def _format_time_axis(self, ax: plt.Axes, ax_vol: plt.Axes, bars: pd.DataFrame):
        """Format X-axis with time labels"""
        n_bars = len(bars)
        
        # Show label every ~15 bars
        tick_interval = max(1, n_bars // 8)
        tick_positions = list(range(0, n_bars, tick_interval))
        
        tick_labels = []
        for i in tick_positions:
            if i < len(bars):
                tick_labels.append(bars.index[i].strftime('%H:%M'))
        
        ax_vol.set_xticks(tick_positions[:len(tick_labels)])
        ax_vol.set_xticklabels(tick_labels, rotation=45, ha='right')
        ax.set_xticklabels([])  # Hide labels on main chart (shared with volume)
    
    def _format_multiday_axis(self, ax: plt.Axes, ax_vol: plt.Axes, 
                              bars: pd.DataFrame, timeframe: str):
        """Format X-axis for multi-day charts with day separators"""
        if bars.empty:
            return
        
        n_bars = len(bars)
        
        # Find day boundaries
        bars_temp = bars.copy()
        bars_temp['date'] = bars_temp.index.date
        day_starts = bars_temp.groupby('date').apply(lambda x: x.index[0]).tolist()
        
        # Draw day separators
        for dt in day_starts[1:]:  # Skip first day
            idx = bars.index.get_loc(dt)
            ax.axvline(idx, color=COLORS['border'], linestyle='-', linewidth=0.5, alpha=0.5)
            ax_vol.axvline(idx, color=COLORS['border'], linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Time labels - show date at day start, time otherwise
        tick_interval = max(1, n_bars // 10)
        tick_positions = list(range(0, n_bars, tick_interval))
        
        tick_labels = []
        for i in tick_positions:
            if i < len(bars):
                bar_dt = bars.index[i]
                # Check if this is near day start
                if any(abs((bar_dt - ds).total_seconds()) < 3600 for ds in day_starts):
                    tick_labels.append(bar_dt.strftime('%m/%d'))
                else:
                    tick_labels.append(bar_dt.strftime('%H:%M'))
        
        ax_vol.set_xticks(tick_positions[:len(tick_labels)])
        ax_vol.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=7)
        ax.set_xticklabels([])
    
    def to_bytes(self) -> bytes:
        """Convert current figure to PNG bytes"""
        if self.fig is None:
            return b''
        
        buf = io.BytesIO()
        self.fig.savefig(buf, format='png', dpi=PDF_DPI, facecolor=COLORS['dark_bg'],
                        edgecolor='none', bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
    
    def save_pdf(self, filepath: str):
        """Save current figure to PDF"""
        if self.fig is None:
            return
        
        self.fig.savefig(filepath, format='pdf', dpi=PDF_DPI, 
                        facecolor=COLORS['dark_bg'],
                        edgecolor='none', bbox_inches='tight')
    
    def close(self):
        """Close the figure"""
        if self.fig:
            plt.close(self.fig)
            self.fig = None


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test with mock data"""
    import numpy as np
    
    # Create mock trade
    class MockTrade:
        trade_id = "2024-01-15_SPY_EPCH1_1"
        date = "2024-01-15"
        ticker = "SPY"
        model = "EPCH1"
        zone_type = "PRIMARY"
        direction = "LONG"
        zone_high = 475.50
        zone_low = 474.00
        zone_poc = 474.75
        entry_price = 474.50
        entry_time = "09:45:00"
        stop_price = 473.50
        target_3r = 477.50
        target_calc = 478.00
        target_used = "3R"
        target_price = 477.50
        exit_price = 476.80
        exit_time = "11:30:00"
        exit_reason = "TARGET_3R"
        pnl_dollars = 230.00
        pnl_r = 2.3
        risk = 100.00
        win = True
        is_long = True
        duration_minutes = 105
    
    trade = MockTrade()
    
    # Create mock M5 bars
    np.random.seed(42)
    dates = pd.date_range('2024-01-15 09:00', periods=84, freq='5T', tz='America/New_York')
    
    prices = 474 + np.cumsum(np.random.randn(84) * 0.2)
    
    m5_bars = pd.DataFrame({
        'open': prices,
        'high': prices + np.random.rand(84) * 0.5,
        'low': prices - np.random.rand(84) * 0.5,
        'close': prices + np.random.randn(84) * 0.3,
        'volume': np.random.randint(10000, 100000, 84)
    }, index=dates)
    
    # Build chart
    builder = TradeChartBuilder()
    fig = builder.build(
        trade=trade,
        m5_bars=m5_bars,
        h1_bars=m5_bars.resample('1H').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 
            'close': 'last', 'volume': 'sum'
        }).dropna(),
        m15_bars=m5_bars.resample('15T').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna(),
        zones={'primary': {'high': 475.50, 'low': 474.00}},
        hvn_pocs=[475.20, 474.50, 473.80]
    )
    
    # Save test
    builder.save_pdf('/tmp/test_trade_chart.pdf')
    print("Test chart saved to /tmp/test_trade_chart.pdf")
    builder.close()


if __name__ == "__main__":
    main()
