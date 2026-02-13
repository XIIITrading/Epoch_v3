# visualization_config.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\config\
# Purpose: Central configuration for Module 08 Visualization

"""
Module 08 Configuration
- Color scheme matching PineScript indicators
- Excel workbook path and worksheet names
- Polygon API settings
- Chart parameters
"""

import os
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

# Base directory (adjust if running from different location)
BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
MODULE_DIR = BASE_DIR / "02_zone_system" / "08_visualization"

# Excel workbook
WORKBOOK_NAME = "epoch_v1.xlsm"
WORKBOOK_PATH = BASE_DIR / WORKBOOK_NAME

# Worksheet names
WORKSHEETS = {
    'market_overview': 'market_overview',
    'bar_data': 'bar_data',
    'zone_results': 'zone_results',
    'analysis': 'Analysis'
}

# =============================================================================
# POLYGON API
# =============================================================================

# Try to load from credentials file
try:
    from credentials import POLYGON_API_KEY
except ImportError:
    # Fallback - set your API key here or via environment variable
    POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')

API_DELAY = 0.25  # Seconds between API calls
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# CHART PARAMETERS
# =============================================================================

# Candlestick settings
CANDLE_TIMEFRAME = 60          # H1 in minutes (1 hour)
CANDLE_BAR_COUNT = 120         # ~18 trading days at H1

# Volume Profile settings
VBP_TIMEFRAME = 15             # M15 for VbP (configurable: 15, 5, or 1)
VBP_COLOR = '#5c6bc0'          # Indigo, single color
VBP_GRANULARITY = 0.01         # $0.01 fidelity

# POC Lines (from Module 04)
POC_LINE_STYLE = '--'          # Dashed
POC_LINE_COLOR = '#ffffff'     # White
POC_LINE_ALPHA = 0.3           # 70% transparent
POC_LABEL_SIDE = 'left'

# Chart dimensions (inches) - sized for 4K display
FIGURE_WIDTH = 20
FIGURE_HEIGHT = 12
DPI = 300  # High resolution for 4K screens

# Y-axis padding (percentage of range)
YAXIS_PADDING_PCT = 0.02       # 2% padding

# =============================================================================
# COLOR SCHEME (Matching PineScript)
# =============================================================================

COLORS = {
    # Background colors
    'dark_bg': '#1a1a2e',
    'dark_bg_lighter': '#16213e',
    'table_bg': '#0f0f1a',
    'notes_bg': '#0a0a12',
    
    # Text colors
    'text_primary': '#e0e0e0',
    'text_muted': '#888888',
    'text_dim': '#666666',
    
    # Zone colors (from PineScript - 90% transparency converted to alpha=0.15)
    'primary_blue': '#90bff9',
    'primary_blue_fill': '#90bff9',  # Use with alpha=0.15
    'secondary_red': '#faa1a4',
    'secondary_red_fill': '#faa1a4',  # Use with alpha=0.15
    'pivot_purple': '#b19cd9',
    
    # Direction colors
    'bull': '#26a69a',
    'bear': '#ef5350',
    'neutral': '#888888',
    
    # Candlestick colors
    'candle_green': '#26a69a',
    'candle_red': '#ef5350',
    
    # UI elements
    'border': '#333333',
    'border_light': '#444444',
    'grid': '#2a2a4e',
}

# Zone fill alpha (matching PineScript color.new with 90 transparency)
ZONE_FILL_ALPHA = 0.15

# =============================================================================
# RANK COLORS (for Zone Results table)
# =============================================================================

RANK_COLORS = {
    'L5': '#00C853',  # Green - best
    'L4': '#2196F3',  # Blue
    'L3': '#FFC107',  # Yellow/Amber
    'L2': '#9E9E9E',  # Gray
    'L1': '#616161',  # Dark gray (shouldn't appear in filtered results)
}

# =============================================================================
# TABLE LAYOUT
# =============================================================================

# Left panel table height ratios
TABLE_HEIGHT_RATIOS = [1.0, 1.2, 1.8, 1.4, 0.8]  # Market, Ticker, Zones, Setup, Notes

# Column widths for each table
TABLE_COLUMN_WIDTHS = {
    'market_structure': [0.12, 0.15, 0.15, 0.15, 0.15, 0.15],
    'ticker_structure': [0.10, 0.15, 0.15, 0.15, 0.15, 0.15],
    'zone_results': [0.20, 0.14, 0.14, 0.14, 0.10, 0.10],
}

# =============================================================================
# TIME SETTINGS
# =============================================================================

# Timezone for display
DISPLAY_TIMEZONE = 'America/New_York'

# Market session labels
SESSION_LABELS = {
    'premarket': 'Pre-Market Report',
    'postmarket': 'Post-Market Report'
}

# =============================================================================
# INDEX TICKERS
# =============================================================================

INDEX_TICKERS = ['SPY', 'QQQ', 'DIA']

# =============================================================================
# EXCEL ROW MAPPINGS
# =============================================================================

# Ticker slot to row number mappings
TICKER_ROWS = {
    'market_overview': {
        't1': 36, 't2': 37, 't3': 38, 't4': 39, 't5': 40,
        't6': 41, 't7': 42, 't8': 43, 't9': 44, 't10': 45
    },
    'bar_data_ticker': {
        't1': 4, 't2': 5, 't3': 6, 't4': 7, 't5': 8,
        't6': 9, 't7': 10, 't8': 11, 't9': 12, 't10': 13
    },
    'bar_data_atr': {
        't1': 73, 't2': 74, 't3': 75, 't4': 76, 't5': 77,
        't6': 78, 't7': 79, 't8': 80, 't9': 81, 't10': 82
    },
    'time_hvn': {
        't1': 59, 't2': 60, 't3': 61, 't4': 62, 't5': 63,
        't6': 64, 't7': 65, 't8': 66, 't9': 67, 't10': 68
    },
    'analysis_strings': {
        't1': 44, 't2': 45, 't3': 46, 't4': 47, 't5': 48,
        't6': 49, 't7': 50, 't8': 51, 't9': 52, 't10': 53
    }
}

# time_hvn column mappings for POCs
TIME_HVN_COLUMNS = {
    'ticker': 'C',
    'start_date': 'E',
    'hvn_poc1': 'F',
    'hvn_poc2': 'G',
    'hvn_poc3': 'H',
    'hvn_poc4': 'I',
    'hvn_poc5': 'J',
    'hvn_poc6': 'K',
    'hvn_poc7': 'L',
    'hvn_poc8': 'M',
    'hvn_poc9': 'N',
    'hvn_poc10': 'O'
}

INDEX_ROWS = {
    'SPY': 29,
    'QQQ': 30,
    'DIA': 31
}
