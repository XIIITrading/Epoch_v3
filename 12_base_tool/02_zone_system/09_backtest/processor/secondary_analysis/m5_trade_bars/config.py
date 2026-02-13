"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the M5 Trade Bars calculation module.
Trade-specific M5 bars from entry to 15:30 with health scoring and MFE/MAE marking.

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
MARKET_OPEN = time(9, 30)
EOD_CUTOFF = time(15, 30)  # Trade bars end at 15:30
MARKET_CLOSE = time(16, 0)

# Prior day extended hours for SMA calculation
PRIOR_DAY_START = time(16, 0)  # 4 PM prior day

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
TRADES_TABLE = "trades"
MFE_MAE_TABLE = "mfe_mae_potential"
M5_INDICATOR_BARS_TABLE = "m5_indicator_bars"
TARGET_TABLE = "m5_trade_bars"

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

# Volume Delta Configuration
VOLUME_DELTA_ROLLING_PERIOD = 5

# CVD Configuration
CVD_WINDOW = 15
CVD_RISING_THRESHOLD = 0.1  # Slope above this = bullish
CVD_FALLING_THRESHOLD = -0.1  # Slope below this = bearish

# Structure Configuration
FRACTAL_LENGTH = 5  # Bars on each side for fractal detection

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
# HEALTH SCORE CONFIGURATION
# =============================================================================

# Health score buckets
HEALTH_BUCKETS = {
    "CRITICAL": (0, 3),
    "WEAK": (4, 5),
    "MODERATE": (6, 7),
    "STRONG": (8, 10)
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
