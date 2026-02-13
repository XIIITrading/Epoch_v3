"""
Epoch Trading System - Training Module Configuration
Flash card review system for deliberate practice.

Version: 1.0.0
"""

import os
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
MODULE_DIR = Path(__file__).parent
BASE_DIR = MODULE_DIR.parent.parent  # C:\XIIITradingSystems\Epoch

# Schema directory
SCHEMA_DIR = MODULE_DIR / "schema"

# =============================================================================
# Supabase Configuration (reuse from 11_database_export)
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

# Connection dict for psycopg2.connect()
DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# =============================================================================
# Polygon API (reuse from 08_visualization)
# =============================================================================
try:
    # Try to import from 08_visualization credentials
    import sys
    sys.path.insert(0, str(MODULE_DIR.parent / "08_visualization"))
    from credentials import POLYGON_API_KEY
except ImportError:
    # Fallback to environment variable
    POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')

API_DELAY = 0.25  # Seconds between API calls
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# Chart Configuration
# =============================================================================
CHART_CONFIG = {
    # Candle settings
    'candle_count': 160,
    'timeframes': ['5m', '15m', '1h'],
    'row_heights': [0.40, 0.35, 0.25],  # M5 largest, H1 smallest

    # Colors (match 08_visualization theme)
    'background_color': '#1a1a2e',
    'paper_color': '#1a1a2e',
    'grid_color': '#2a2a4e',
    'text_color': '#e0e0e0',
    'text_muted': '#888888',

    # Candle colors
    'candle_up_color': '#26a69a',
    'candle_down_color': '#ef5350',

    # Marker colors
    'entry_color': '#00C853',      # Green
    'exit_color': '#FF1744',       # Red
    'mfe_color': '#2196F3',        # Blue
    'mae_color': '#FF9800',        # Orange

    # R-level colors (v2.1.0)
    'stop_color': '#FF1744',       # Red - Stop level
    'r1_color': '#4CAF50',         # Light green - 1R target
    'r2_color': '#8BC34A',         # Lighter green - 2R target
    'r3_color': '#CDDC39',         # Lime - 3R target
    'eod_color': '#9C27B0',        # Purple - EOD exit (15:30)

    # Zone colors
    'primary_zone_color': '#90bff9',
    'secondary_zone_color': '#faa1a4',
    'zone_opacity': 0.15,

    # Toggle to show/hide additional zones (non-primary/secondary)
    'show_other_zones': False,

    # Chart dimensions
    'chart_height': 900,
    'chart_width': None,  # Use container width
}

# =============================================================================
# Zone Rank Colors
# =============================================================================
RANK_COLORS = {
    'L5': '#00C853',  # Green - best
    'L4': '#2196F3',  # Blue
    'L3': '#FFC107',  # Yellow/Amber
    'L2': '#9E9E9E',  # Gray
    'L1': '#616161',  # Dark gray
}

TIER_COLORS = {
    'T3': '#00C853',  # Green - High Quality
    'T2': '#FFC107',  # Yellow - Medium Quality
    'T1': '#9E9E9E',  # Gray - Lower Quality
}

# =============================================================================
# Indicator Refinement Colors (v2.0.0)
# =============================================================================
INDICATOR_REFINEMENT_COLORS = {
    # Trade type colors
    'continuation': '#4CAF50',  # Green for with-trend
    'rejection': '#FF9800',     # Orange for counter-trend

    # Score label colors
    'strong': '#00C853',        # Green - STRONG
    'good': '#8BC34A',          # Light green - GOOD
    'weak': '#FF9800',          # Orange - WEAK
    'avoid': '#FF1744',         # Red - AVOID

    # Boolean indicator colors
    'aligned': '#00C853',       # Green - aligned/positive
    'divergent': '#FF1744',     # Red - not aligned/negative
    'neutral': '#888888',       # Gray - unknown/neutral
}

# Score thresholds for labels
CONTINUATION_SCORE_THRESHOLDS = {
    'STRONG': (8, 10),
    'GOOD': (6, 7),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

REJECTION_SCORE_THRESHOLDS = {
    'STRONG': (9, 11),
    'GOOD': (6, 8),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

# How many upcoming trades to prefetch
PREFETCH_COUNT = 3

# =============================================================================
# Time Settings
# =============================================================================
DISPLAY_TIMEZONE = 'America/New_York'

# Market hours for fetching
MARKET_OPEN_HOUR = 8   # 08:00 ET (pre-market)
MARKET_CLOSE_HOUR = 20  # 20:00 ET (after-hours)

