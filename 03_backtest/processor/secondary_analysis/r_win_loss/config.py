"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
R Win/Loss Calculator - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the R Win/Loss calculation module.
Evaluates trades using M5 ATR-based stop and R-multiple targets (1R-5R)
to determine win/loss outcomes with reduced drawdown analysis.

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

# Connection string for psycopg2
DATABASE_URL = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DATABASE}"

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
MARKET_OPEN = time(9, 30)      # Regular trading hours start
EOD_CUTOFF = time(15, 30)      # End of day cutoff for trade evaluation
MARKET_CLOSE = time(16, 0)     # Regular trading hours end

# =============================================================================
# ATR PARAMETERS (matches stop_analysis m5_atr stop type)
# =============================================================================
ATR_PERIOD = 14          # 14-period ATR
ATR_MULTIPLIER = 1.1     # 1.1x ATR for stop distance (1R)

# =============================================================================
# R-LEVEL CONFIGURATION
# =============================================================================
R_LEVELS = [1, 2, 3, 4, 5]    # R-multiples to track

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLES = {
    'trades': 'trades',
    'm1_bars': 'm1_bars',
    'm5_bars': 'm5_trade_bars',
    'm5_indicator_bars': 'm5_indicator_bars',
}
TARGET_TABLE = "r_win_loss"

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
