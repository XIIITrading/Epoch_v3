"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the Entry Indicators calculation module.
Calculates indicator snapshots at trade entry time for analysis.

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
DOCS_DIR = MODULE_DIR / "docs"

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
# POLYGON API CONFIGURATION (for HTF bar fetching if needed)
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
MARKET_OPEN = time(9, 30)
EOD_CUTOFF = time(15, 30)
MARKET_CLOSE = time(16, 0)

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "mfe_mae_potential"  # Get trades from here (not optimal_trade)
TARGET_TABLE = "entry_indicators"
M1_BARS_TABLE = "m1_bars"  # Source for 1-minute bar data

# =============================================================================
# INDICATOR CALCULATION PARAMETERS
# =============================================================================

# SMA Configuration
SMA_FAST_PERIOD = 9
SMA_SLOW_PERIOD = 21
SMA_MOMENTUM_LOOKBACK = 10
SMA_WIDENING_THRESHOLD = 1.1  # Ratio indicating widening
SMA_NARROWING_THRESHOLD = 0.9  # Ratio indicating narrowing

# Volume ROC Configuration
VOLUME_ROC_BASELINE_PERIOD = 20
VOLUME_ROC_ABOVE_AVG_THRESHOLD = 20.0  # Above this = healthy
VOLUME_ROC_BELOW_AVG_THRESHOLD = -20.0

# Volume Delta Configuration
VOLUME_DELTA_ROLLING_PERIOD = 5

# CVD Configuration
CVD_WINDOW = 15
CVD_RISING_THRESHOLD = 0.1  # Slope above this = bullish
CVD_FALLING_THRESHOLD = -0.1  # Slope below this = bearish

# Structure Configuration
FRACTAL_LENGTH = 5  # Bars on each side for fractal detection

# =============================================================================
# HEALTH SCORE CONFIGURATION
# =============================================================================

# Health score buckets
HEALTH_BUCKETS = {
    "CRITICAL": (0, 3),
    "WEAK": (4, 5),
    "MODERATE": (6, 7),
    "STRONG": (8, 10)
}

# Structure labels
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
    'M5': 100,   # ~8 hours of 5-min bars
    'M15': 100,  # ~25 hours of 15-min bars
    'H1': 100,   # ~100 hours of 1-hour bars
    'H4': 50,    # ~200 hours of 4-hour bars
}

# Lookback days for fetching HTF bars from Polygon
HTF_LOOKBACK_DAYS = {
    'M5': 3,
    'M15': 7,
    'H1': 14,
    'H4': 30,
}

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 100

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True

# =============================================================================
# VERSION
# =============================================================================
CALCULATION_VERSION = "1.0"
