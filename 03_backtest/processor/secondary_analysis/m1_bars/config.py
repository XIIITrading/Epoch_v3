"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M1 Bars Storage - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the M1 Bars storage module.
Stores 1-minute bar data from Polygon API to Supabase for analysis.

Time Range: Prior day 16:00 ET through trade day 16:00 ET
- Captures after-hours, overnight, pre-market, and full regular session
- Provides complete data for all downstream secondary processors

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
# M1 BAR TIME RANGE (Eastern Time)
# =============================================================================
# We store prior day 16:00 -> trade day 16:00 to capture:
#   Prior day after-hours (16:00 - 20:00)
#   Overnight / pre-market (04:00 - 09:30)
#   Regular trading hours (09:30 - 16:00)
PRIOR_DAY_START = time(16, 0)   # Start fetching from prior day 16:00 ET
TRADE_DAY_END = time(16, 0)     # Stop fetching at trade day 16:00 ET

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "trades_2"        # Get unique ticker-date pairs from trades_2
TARGET_TABLE = "m1_bars_2"       # Store 1-minute bars here (v2 extended session)

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 500  # Insert bars in batches of 500

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
