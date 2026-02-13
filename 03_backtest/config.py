"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v4.0
Configuration Settings - Entry Detection Only
XIII Trading LLC
================================================================================
"""
from datetime import time
from pathlib import Path

# =============================================================================
# DATABASE CONFIGURATION
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
# POLYGON API
# =============================================================================
POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"
API_DELAY = 0.25  # Seconds between API calls
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
ENTRY_START_TIME = time(9, 30)   # Market open
ENTRY_END_TIME = time(15, 30)    # Stop new entries

# =============================================================================
# ENTRY MODELS
# =============================================================================
ENTRY_MODELS = {
    'EPCH1': 1,  # Primary zone continuation
    'EPCH2': 2,  # Primary zone rejection
    'EPCH3': 3,  # Secondary zone continuation
    'EPCH4': 4   # Secondary zone rejection
}

# =============================================================================
# DISPLAY/LOGGING
# =============================================================================
VERBOSE = False  # Set to True for detailed logging during backtest
