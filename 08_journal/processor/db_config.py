"""
================================================================================
EPOCH TRADING SYSTEM - JOURNAL PROCESSOR
Shared Database Configuration
XIII Trading LLC
================================================================================

Self-contained database and API configuration for all journal processors.
Used by all 8 secondary processor modules.

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

API_DELAY = 0.0
API_RETRIES = 3
API_RETRY_DELAY = 1.0

# =============================================================================
# M1 BAR TIME RANGE (Eastern Time)
# =============================================================================
PRIOR_DAY_START = time(16, 0)
TRADE_DAY_END = time(16, 0)

# =============================================================================
# TABLE CONFIGURATION (journal-specific)
# =============================================================================
# Source table (journal trades)
SOURCE_TABLE = "journal_trades"

# Target tables (j_ prefix)
J_M1_BARS_TABLE = "j_m1_bars"
J_M1_INDICATOR_BARS_TABLE = "j_m1_indicator_bars"
J_M1_ATR_STOP_TABLE = "j_m1_atr_stop"
J_M5_ATR_STOP_TABLE = "j_m5_atr_stop"
J_TRADES_M5_R_WIN_TABLE = "j_trades_m5_r_win"
J_M1_TRADE_INDICATOR_TABLE = "j_m1_trade_indicator"
J_M1_RAMP_UP_INDICATOR_TABLE = "j_m1_ramp_up_indicator"
J_M1_POST_TRADE_INDICATOR_TABLE = "j_m1_post_trade_indicator"

# =============================================================================
# COLUMN NAME MAPPING (journal_trades -> backtest trades_2)
# =============================================================================
# journal_trades uses 'symbol' + 'trade_date'
# backtest trades_2 uses 'ticker' + 'date'
JOURNAL_SYMBOL_COL = "symbol"
JOURNAL_DATE_COL = "trade_date"

# =============================================================================
# INDICATOR PARAMETERS (match backtest exactly)
# =============================================================================
SMA_FAST_PERIOD = 9
SMA_SLOW_PERIOD = 21
SMA_MOMENTUM_LOOKBACK = 5
SMA_WIDENING_THRESHOLD = 1.2
VOLUME_ROC_BASELINE_PERIOD = 20
VOLUME_DELTA_ROLLING_PERIOD = 5
CVD_WINDOW = 14
ATR_PERIOD = 14

# Health score thresholds
HEALTH_VOL_ROC_THRESHOLD = 50.0
HEALTH_CVD_SLOPE_THRESHOLD = 0.001
HEALTH_SMA_SPREAD_THRESHOLD = 0.001

# =============================================================================
# ATR STOP CONFIGURATION
# =============================================================================
EOD_CUTOFF = time(15, 30)
R_LEVELS = [1, 2, 3, 4, 5]

# =============================================================================
# INDICATOR / RAMP-UP / POST-TRADE CONFIGURATION
# =============================================================================
RAMP_UP_BARS = 25
POST_TRADE_BARS = 25

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 500

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
CALCULATION_VERSION = "1.0.0"
