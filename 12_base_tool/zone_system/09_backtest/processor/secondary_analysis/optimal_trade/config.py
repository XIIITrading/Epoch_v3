"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Optimal Trade Calculator - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the Optimal Trade calculation module.
Points-based calculation using mfe_mae_potential and m5_trade_bars.

Version: 2.0.0
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
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
MARKET_OPEN = time(9, 30)
EOD_CUTOFF = time(15, 30)  # Fixed exit time for all trades
MARKET_CLOSE = time(16, 0)

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
TRADES_TABLE = "trades"
MFE_MAE_TABLE = "mfe_mae_potential"
M5_TRADE_BARS_TABLE = "m5_trade_bars"
TARGET_TABLE = "optimal_trade"

# =============================================================================
# HEALTH SUMMARY THRESHOLDS
# =============================================================================
HEALTH_IMPROVING_THRESHOLD = 2   # health_delta >= 2 = IMPROVING
HEALTH_DEGRADING_THRESHOLD = -2  # health_delta <= -2 = DEGRADING
# Between -2 and 2 = STABLE

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
CALCULATION_VERSION = "2.0"
