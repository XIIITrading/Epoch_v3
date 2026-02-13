"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Indicator Refinement - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for Continuation/Rejection scoring.
Based on Epoch Indicator Model Specification v1.0 (January 12, 2026).

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
EOD_CUTOFF = time(15, 30)
MARKET_CLOSE = time(16, 0)

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "entry_indicators"       # Read from entry_indicators (has structure/volume data)
TARGET_TABLE = "indicator_refinement"   # Write refined scores
M1_BARS_TABLE = "m1_bars"
M5_BARS_TABLE = "m5_indicator_bars"
TRADES_TABLE = "trades"

# =============================================================================
# MODEL CLASSIFICATION
# =============================================================================

# Which models are continuation vs rejection
# Note: Database uses EPCH1/2/3/4 (without leading zero)
CONTINUATION_MODELS = ['EPCH1', 'EPCH3', 'EPCH01', 'EPCH03']  # With-trend trades
REJECTION_MODELS = ['EPCH2', 'EPCH4', 'EPCH02', 'EPCH04']     # Counter-trend/exhaustion trades

# =============================================================================
# CONTINUATION INDICATOR THRESHOLDS (CONT-01 to CONT-04)
# =============================================================================

# CONT-02: SMA Momentum
SMA_SPREAD_ROC_THRESHOLD = 5.0          # ROC > 5% = expanding
SMA_SPREAD_LOOKBACK = 5                 # Bars for ROC calculation

# CONT-03: Volume Thrust
VOLUME_ROC_STRONG_THRESHOLD = 20.0      # vol_roc > 20% = strong
VOLUME_DELTA_PERIOD = 5                 # Bars for delta sum

# CONT-04: Pullback Quality
PULLBACK_BARS = 3                       # Look back 3 bars for pullback
PULLBACK_DELTA_THRESHOLD_HIGH = 0.3     # < 0.3 = high quality
PULLBACK_DELTA_THRESHOLD_MOD = 0.5      # < 0.5 = moderate quality

# =============================================================================
# REJECTION INDICATOR THRESHOLDS (REJ-01 to REJ-05)
# =============================================================================

# REJ-02: SMA Exhaustion
SMA_SPREAD_Q1_THRESHOLD = 0.15          # Lowest 20% of spreads (very tight)
SMA_SPREAD_Q2_THRESHOLD = 0.25          # Lowest 40% of spreads (tight)
SMA_SPREAD_CONTRACTING_THRESHOLD = -10.0  # ROC < -10% = contracting

# REJ-03: Delta Absorption
ABSORPTION_Q5_THRESHOLD = 2.0           # Top 20% absorption
ABSORPTION_Q4_THRESHOLD = 1.5           # Top 40% absorption
PRICE_CHANGE_MIN = 0.05                 # Minimum price change % to avoid division issues

# REJ-04: Volume Climax
VOLUME_ROC_Q5_THRESHOLD = 50.0          # Top 20% volume spike
VOLUME_ROC_Q4_THRESHOLD = 30.0          # Top 40% volume spike

# REJ-05: CVD Extreme
CVD_SLOPE_PERIOD = 15                   # Bars for CVD slope calculation
CVD_Q1_THRESHOLD = -0.5                 # Lowest 20% (strong selling)
CVD_Q2_THRESHOLD = -0.3                 # Lowest 40%

# =============================================================================
# COMPOSITE SCORE THRESHOLDS
# =============================================================================

# Continuation scores (0-10 scale)
CONTINUATION_THRESHOLDS = {
    'STRONG': (8, 10),
    'GOOD': (6, 7),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

# Rejection scores (0-11 scale)
REJECTION_THRESHOLDS = {
    'STRONG': (9, 11),
    'GOOD': (6, 8),
    'WEAK': (4, 5),
    'AVOID': (0, 3)
}

# =============================================================================
# HEALTH SCORE BUCKETS (for consistency with entry_indicators)
# =============================================================================
HEALTH_BUCKETS = {
    "CRITICAL": (0, 3),
    "WEAK": (4, 5),
    "MODERATE": (6, 7),
    "STRONG": (8, 10)
}

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
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 100

# =============================================================================
# HTF BAR REQUIREMENTS (for structure detection)
# =============================================================================
HTF_BARS_NEEDED = {
    'M5': 100,
    'M15': 100,
    'H1': 100,
    'H4': 50,
}

HTF_LOOKBACK_DAYS = {
    'M5': 3,
    'M15': 7,
    'H1': 14,
    'H4': 30,
}

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True

# =============================================================================
# VERSION
# =============================================================================
CALCULATION_VERSION = "1.0"
