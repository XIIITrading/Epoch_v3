"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Options Analysis - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the Options Analysis calculation module.
Analyzes options performance for completed backtest trades.

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
REQUEST_TIMEOUT = 30  # seconds

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLE = "trades"  # Get trades from here
TARGET_TABLE = "options_analysis"  # Write results here

# =============================================================================
# OPTIONS BAR TIMEFRAMES
# =============================================================================
# Entry uses 15-second bars (matching S15 equity entries)
ENTRY_BAR_MULTIPLIER = 15
ENTRY_BAR_TIMESPAN = "second"

# Exit uses 5-minute bars (matching M5 equity exits)
EXIT_BAR_MULTIPLIER = 5
EXIT_BAR_TIMESPAN = "minute"

# =============================================================================
# CONTRACT SELECTION DEFAULTS
# =============================================================================
# Expiration: Minimum days after trade exit
MIN_DAYS_TO_EXPIRY = 2

# Strike selection method: "FIRST_ITM", "ATM", "FIRST_OTM"
DEFAULT_STRIKE_METHOD = "FIRST_ITM"

# =============================================================================
# LIQUIDITY FILTERS (Optional - set to 0 to disable)
# =============================================================================
MIN_VOLUME = 0           # Minimum daily volume (0 = no filter)
MIN_OPEN_INTEREST = 0    # Minimum open interest (0 = no filter)

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
CALCULATION_VERSION = "1.0"
