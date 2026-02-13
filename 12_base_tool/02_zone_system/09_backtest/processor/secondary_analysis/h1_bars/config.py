"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
H1 Bars Storage - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the H1 Bars storage module.
Stores 1-hour bar data from Polygon API to Supabase for H1 structure analysis.

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
POLYGON_BASE_URL = "https://api.polygon.io"

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
# H1 BARS CONFIGURATION
# =============================================================================
# Number of H1 bars to fetch before market open
# 30 bars = ~4-5 trading days of H1 data (7 bars per day during regular hours)
H1_LOOKBACK_BARS = 30

# Number of calendar days to look back to get H1_LOOKBACK_BARS
# 7 days should be plenty to get 30 H1 bars (accounts for weekends/holidays)
H1_LOOKBACK_DAYS = 7

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "trades"          # Get unique ticker-date pairs from trades
TARGET_TABLE = "h1_bars"         # Store 1-hour bars here

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 100  # Insert bars in batches (fewer H1 bars per day)

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
