"""
Epoch Trading Journal - Module Configuration
"""

import os
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
MODULE_DIR = Path(__file__).parent
BASE_DIR = MODULE_DIR.parent  # C:\XIIITradingSystems\Epoch
TRADE_LOG_DIR = MODULE_DIR / "trade_log"

# =============================================================================
# Streamlit
# =============================================================================
STREAMLIT_PORT = 8502

# =============================================================================
# Polygon API
# =============================================================================
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_')
API_DELAY = 0.25        # Seconds between API calls
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# Time Settings
# =============================================================================
DISPLAY_TIMEZONE = 'America/New_York'
MARKET_OPEN_HOUR = 8    # 08:00 ET (pre-market context)
MARKET_CLOSE_HOUR = 20  # 20:00 ET (after-hours)

# =============================================================================
# Chart Configuration
# =============================================================================
CHART_CONFIG = {
    # Row heights (M1 top 60%, M15+H1 side by side 40%)
    'row_heights': [0.60, 0.40],

    # M1 chart buffer (60 pre = 60 M1 candles before entry for evaluate mode)
    'm1_pre_buffer_minutes': 60,    # Minutes before first fill
    'm1_post_buffer_minutes': 60,   # Minutes after last fill

    # Candle colors
    'candle_up_color': '#26a69a',
    'candle_down_color': '#ef5350',

    # Theme colors
    'background_color': '#1a1a2e',
    'paper_color': '#1a1a2e',
    'grid_color': '#2a2a4e',
    'text_color': '#e0e0e0',
    'text_muted': '#888888',

    # Marker colors (matching 06_training)
    'entry_color': '#00C853',       # Green — entries and adds
    'exit_color': '#FF1744',        # Red
    'eod_color': '#9C27B0',         # Purple — EOD exit

    # R-level colors
    'stop_color': '#FF1744',        # Red
    'r1_color': '#4CAF50',          # Light green
    'r2_color': '#8BC34A',          # Lighter green
    'r3_color': '#CDDC39',          # Lime

    # MFE/MAE colors (from 06_training)
    'mfe_color': '#00E676',             # Bright green — max favorable
    'mae_color': '#FF5252',             # Bright red — max adverse

    # Zone colors
    'primary_zone_color': '#90bff9',
    'secondary_zone_color': '#faa1a4',
    'zone_opacity': 0.15,

    # Chart dimensions (matches 06_training)
    'chart_height': 900,
    'chart_width': None,            # Use container width
}

# =============================================================================
# Database Configuration
# =============================================================================
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require",
}

# =============================================================================
# Flashcard / Training Configuration
# =============================================================================
PREFETCH_COUNT = 3  # Number of upcoming trades to prefetch bars for

# =============================================================================
# Ramp-Up Chart Configuration
# =============================================================================
RAMPUP_BARS = 45  # Number of M1 bars to show before entry

# =============================================================================
# M1 Indicator Calculation Parameters
# =============================================================================
SMA_FAST_PERIOD = 9
SMA_SLOW_PERIOD = 21
VOLUME_ROC_BASELINE_PERIOD = 20
VOLUME_DELTA_ROLLING_PERIOD = 5
