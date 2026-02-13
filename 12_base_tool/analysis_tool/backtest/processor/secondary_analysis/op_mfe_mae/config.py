"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options MFE/MAE Potential Calculator - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the Options MFE/MAE Potential calculation module.
Includes Supabase database and Polygon API credentials.

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
# POLYGON API CONFIGURATION
# =============================================================================
POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"
POLYGON_BASE_URL = "https://api.polygon.io"

# Rate limiting (not needed for max tier, but included for safety)
API_DELAY = 0.0  # No delay needed for unlimited tier
API_RETRIES = 3
API_RETRY_DELAY = 1.0
REQUEST_TIMEOUT = 30

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
MARKET_OPEN = time(9, 30)      # Regular trading hours start
EOD_CUTOFF = time(15, 30)      # End of day cutoff for MFE/MAE calculation
MARKET_CLOSE = time(16, 0)     # Regular trading hours end

# =============================================================================
# BAR CONFIGURATION
# =============================================================================
# 1-minute bars for granular MFE/MAE detection (matches share-based mfe_mae/)
BAR_MULTIPLIER = 1
BAR_TIMESPAN = "minute"

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TRADES_TABLE = "trades"
SOURCE_OPTIONS_TABLE = "options_analysis"
SOURCE_MFE_MAE_TABLE = "mfe_mae_potential"  # For underlying comparison
TARGET_TABLE = "op_mfe_mae_potential"

# =============================================================================
# CALCULATION PARAMETERS
# =============================================================================
# Minimum option price filter - skip options priced below this
MIN_OPTION_PRICE = 0.01

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
