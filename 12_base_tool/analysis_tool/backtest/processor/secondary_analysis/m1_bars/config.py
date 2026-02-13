"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the M1 Bars storage module.
Stores 1-minute bar data from Polygon API to Supabase for analysis.

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
# POLYGON API CONFIGURATION
# =============================================================================
POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"

# Rate limiting (not needed for max tier, but included for safety)
API_DELAY = 0.0  # No delay needed for unlimited tier
API_RETRIES = 3
API_RETRY_DELAY = 1.0

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
MARKET_OPEN = time(9, 30)      # Regular trading hours start
EOD_CUTOFF = time(15, 30)      # End of day cutoff for analysis
MARKET_CLOSE = time(16, 0)     # Regular trading hours end

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "trades"          # Get unique ticker-date pairs from trades
TARGET_TABLE = "m1_bars"         # Store 1-minute bars here

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 500  # Insert bars in batches of 500

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
