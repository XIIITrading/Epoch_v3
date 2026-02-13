"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Indicator Bars - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the M1 Indicator Bars calculation module.
Stores direction-agnostic M1 bars with full indicators for ramp-up analysis.

Version: 1.0.0
================================================================================
"""

from datetime import time
from pathlib import Path

# =============================================================================
# MODULE PATHS
# =============================================================================
MODULE_DIR = Path(__file__).parent
SCHEMA_DIR = MODULE_DIR / "schema"

# =============================================================================
# SUPABASE CONFIGURATION
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
# POLYGON API CONFIGURATION
# =============================================================================
POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"
POLYGON_BASE_URL = "https://api.polygon.io"

# Rate limiting
API_DELAY = 0.0  # No delay needed for unlimited tier
API_RETRIES = 3
API_RETRY_DELAY = 1.0

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
# Start from pre-market to have enough bars for indicator calculation at open
PREMARKET_START = time(8, 0)   # 8:00 AM ET - start of data fetch
MARKET_OPEN = time(9, 30)
EOD_CUTOFF = time(15, 30)
MARKET_CLOSE = time(16, 0)

# Prior day extended hours for SMA calculation
PRIOR_DAY_START = time(16, 0)  # 4 PM prior day

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "trades"  # Get unique ticker+dates from here
TARGET_TABLE = "m1_indicator_bars"

# =============================================================================
# INDICATOR CALCULATION PARAMETERS
# =============================================================================

# SMA Configuration (same as M5 for consistency)
SMA_FAST_PERIOD = 9
SMA_SLOW_PERIOD = 21
SMA_MOMENTUM_LOOKBACK = 10
SMA_WIDENING_THRESHOLD = 1.1  # Ratio indicating widening
SMA_NARROWING_THRESHOLD = 0.9  # Ratio indicating narrowing

# Volume ROC Configuration
VOLUME_ROC_BASELINE_PERIOD = 20

# Volume Delta Configuration
VOLUME_DELTA_ROLLING_PERIOD = 5

# CVD Configuration
CVD_WINDOW = 15

# Structure Configuration
FRACTAL_LENGTH = 5  # Bars on each side for fractal detection

# =============================================================================
# HEALTH SCORE THRESHOLDS
# =============================================================================
# Used for computing health_score (0-10)
HEALTH_VOL_ROC_THRESHOLD = 50.0       # Volume ROC above this is healthy
HEALTH_CVD_SLOPE_THRESHOLD = 0.0      # CVD slope sign alignment
HEALTH_SMA_SPREAD_THRESHOLD = 0.0     # SMA spread sign for alignment

# =============================================================================
# STRUCTURE LABELS
# =============================================================================
STRUCTURE_LABELS = {
    1: 'BULL',
    -1: 'BEAR',
    0: 'NEUTRAL',
    None: 'ERROR'
}

# =============================================================================
# HTF BAR REQUIREMENTS (for structure detection)
# =============================================================================

# How many bars we need for each timeframe to calculate structure
HTF_BARS_NEEDED = {
    'M1': 100,   # ~1.5 hours of 1-min bars
    'M5': 100,   # ~8 hours of 5-min bars
    'M15': 100,  # ~25 hours of 15-min bars
    'H1': 100,   # ~100 hours of 1-hour bars
    'H4': 50,    # ~200 hours of 4-hour bars
}

# Lookback days for fetching HTF bars from Polygon
HTF_LOOKBACK_DAYS = {
    'M1': 1,
    'M5': 3,
    'M15': 7,
    'H1': 14,
    'H4': 30,
}

# =============================================================================
# RAMP-UP CHART CONFIGURATION
# =============================================================================
RAMPUP_BARS_BEFORE_ENTRY = 15  # Number of M1 bars to show before entry

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 500  # Larger batch for M1 due to more bars

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True

# =============================================================================
# VERSION
# =============================================================================
CALCULATION_VERSION = "1.0"
