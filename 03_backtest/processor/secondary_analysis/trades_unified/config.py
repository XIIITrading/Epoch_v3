"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trades Unified (trades_m5_r_win) - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the unified canonical outcomes table.
Merges trades metadata with r_win_loss ATR-based outcomes and provides
zone_buffer fallback for trades missing r_win_loss records.

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
# ZONE BUFFER FALLBACK PARAMETERS
# =============================================================================
ZONE_BUFFER_PCT = 0.05         # 5% buffer beyond zone boundary (matches stop_analysis)

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLES = {
    'trades': 'trades',
    'r_win_loss': 'r_win_loss',
    'm1_bars': 'm1_bars',
}
TARGET_TABLE = "trades_m5_r_win"

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
