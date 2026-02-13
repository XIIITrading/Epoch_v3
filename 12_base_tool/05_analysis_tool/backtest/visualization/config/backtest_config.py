# backtest_config.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\config\
# Purpose: Configuration for Module 09 Backtest Visualization

"""
Backtest Visualization Configuration

Settings for the 4-quadrant trade visualization:
- Top Left: Trade metrics table
- Top Right: M5 candlestick chart (trade day 09:00-16:00 ET)
- Bottom Left: H1 chart (last 5 trading days)
- Bottom Right: M15 chart (last 3 trading days)
"""

from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
MODULE_DIR = BASE_DIR / "02_zone_system" / "09_backtest" / "visualization"

# Excel workbook
WORKBOOK_NAME = "epoch_v1.xlsm"
WORKBOOK_PATH = BASE_DIR / WORKBOOK_NAME

# Backtest worksheet name
BACKTEST_WORKSHEET = 'backtest'

# =============================================================================
# BACKTEST COLUMNS (A:T)
# =============================================================================

BACKTEST_COLUMNS = {
    'date': 'A',
    'ticker': 'B',
    'model': 'C',
    'zone_type': 'D',
    'direction': 'E',
    'zone_high': 'F',
    'zone_low': 'G',
    'entry_price': 'H',
    'entry_time': 'I',
    'stop_price': 'J',
    'target_3r': 'K',
    'target_calc': 'L',
    'target_used': 'M',
    'exit_price': 'N',
    'exit_time': 'O',
    'exit_reason': 'P',
    'pnl_dollars': 'Q',
    'pnl_r': 'R',
    'risk': 'S',
    'win': 'T'
}

# Column order for DataFrame
BACKTEST_COLUMN_ORDER = [
    'date', 'ticker', 'model', 'zone_type', 'direction',
    'zone_high', 'zone_low', 'entry_price', 'entry_time',
    'stop_price', 'target_3r', 'target_calc', 'target_used',
    'exit_price', 'exit_time', 'exit_reason',
    'pnl_dollars', 'pnl_r', 'risk', 'win'
]

# =============================================================================
# CHART TIME WINDOWS
# =============================================================================

# M5 Chart: Trade day window
M5_START_HOUR = 9   # 09:00 ET
M5_END_HOUR = 16    # 16:00 ET
M5_TIMEFRAME = 5    # Minutes

# H1 Chart: Last N trading days
H1_TRADING_DAYS = 5
H1_TIMEFRAME = 60   # Minutes

# M15 Chart: Last N trading days
M15_TRADING_DAYS = 3
M15_TIMEFRAME = 15  # Minutes

# =============================================================================
# MARKET HOURS (ET)
# =============================================================================

# Pre-market
PRE_MARKET_START = 4   # 04:00 ET
PRE_MARKET_END = 9.5   # 09:30 ET

# Regular Trading Hours
RTH_START = 9.5        # 09:30 ET
RTH_END = 16           # 16:00 ET

# After Hours
AFTER_HOURS_START = 16  # 16:00 ET
AFTER_HOURS_END = 20    # 20:00 ET

# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================

# EMA Periods
EMA_FAST = 9
EMA_SLOW = 21

# VWAP resets at pre-market start each day
VWAP_ANCHOR = 'pre_market'  # 'pre_market' or 'rth'

# =============================================================================
# PAGE LAYOUT (Landscape Letter)
# =============================================================================

# Page dimensions (inches)
PAGE_WIDTH = 11.0
PAGE_HEIGHT = 8.5

# Margins
MARGIN_LEFT = 0.5
MARGIN_RIGHT = 0.5
MARGIN_TOP = 0.5
MARGIN_BOTTOM = 0.5

# Content area
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT   # 10.0
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM  # 7.5

# Quadrant dimensions (approximate - adjusted for spacing)
QUADRANT_WIDTH = CONTENT_WIDTH / 2 - 0.1   # ~4.9
QUADRANT_HEIGHT = CONTENT_HEIGHT / 2 - 0.1  # ~3.65

# DPI for PDF export
PDF_DPI = 150

# =============================================================================
# COLOR SCHEME (Matching existing visualization)
# =============================================================================

COLORS = {
    # Background colors
    'dark_bg': '#1a1a2e',
    'chart_bg': '#0f0f1a',
    'table_bg': '#16213e',
    
    # Text colors
    'text_primary': '#e0e0e0',
    'text_muted': '#888888',
    'text_dim': '#666666',
    
    # Zone colors
    'primary_blue': '#90bff9',
    'secondary_red': '#faa1a4',
    
    # Candlestick colors
    'candle_green': '#26a69a',
    'candle_red': '#ef5350',
    
    # Indicator colors
    'vwap': '#ff9800',        # Orange
    'ema_fast': '#2196f3',    # Blue (9 EMA)
    'ema_slow': '#9c27b0',    # Purple (21 EMA)
    
    # Volume colors
    'volume_up': '#26a69a80',   # Green with alpha
    'volume_down': '#ef535080', # Red with alpha
    
    # Entry/Exit markers
    'entry_long': '#00c853',   # Green
    'entry_short': '#ff5252',  # Red
    'exit_win': '#2196f3',     # Blue
    'exit_loss': '#ef5350',    # Red
    
    # Lines
    'stop_line': '#ff5722',    # Orange
    'target_line': '#4caf50',  # Green
    
    # POC lines
    'poc_line': '#ffffff',     # White
    'poc_line_alpha': 0.3,
    
    # Grid
    'grid': '#2a2a4e',
    'border': '#333333',
}

# Zone fill alpha
ZONE_FILL_ALPHA = 0.15

# =============================================================================
# ENTRY/EXIT MARKER STYLES
# =============================================================================

MARKERS = {
    'entry_long': {
        'marker': '^',      # Up arrow
        'color': COLORS['entry_long'],
        'size': 120,
    },
    'entry_short': {
        'marker': 'v',      # Down arrow
        'color': COLORS['entry_short'],
        'size': 120,
    },
    'exit_win': {
        'marker': 'o',      # Circle
        'color': COLORS['exit_win'],
        'size': 80,
    },
    'exit_loss': {
        'marker': 'o',      # Circle
        'color': COLORS['exit_loss'],
        'size': 80,
    },
}

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

# Timezone
DISPLAY_TIMEZONE = 'America/New_York'

# Date formats
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# Price formatting
PRICE_DECIMALS = 2

# =============================================================================
# PDF EXPORT SETTINGS
# =============================================================================

# Single trade PDF filename template
SINGLE_PDF_TEMPLATE = "{ticker}_{date}_{model}_{direction}.pdf"

# Batch PDF filename template
BATCH_PDF_TEMPLATE = "backtest_report_{start_date}_to_{end_date}.pdf"

# Include summary page in batch export
BATCH_INCLUDE_SUMMARY = True
