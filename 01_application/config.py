"""
Application Configuration
Epoch Trading System v2.0 - XIII Trading LLC

Central configuration for the main trading application.
"""
from pathlib import Path
from datetime import date, timedelta
import os

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
MODULE_DIR = Path(__file__).parent
EPOCH_DIR = MODULE_DIR.parent
DATA_DIR = MODULE_DIR / "data" / "cache"

# Create cache directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# API CONFIGURATION
# =============================================================================
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_")

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require"
}

# =============================================================================
# DEFAULT FILTER THRESHOLDS
# =============================================================================
DEFAULT_MIN_ATR = 2.0
DEFAULT_MIN_PRICE = 10.0
DEFAULT_MIN_GAP_PERCENT = 2.0

# =============================================================================
# ZONE CALCULATION SETTINGS
# =============================================================================
ZONE_ATR_DIVISOR = 2.0  # Zone = POC +/- (M15_ATR / 2)
MAX_ZONES_PER_TICKER = 10
PROXIMITY_ATR_MULTIPLIER = 2.0  # Zones within 2 ATR of price

# =============================================================================
# RISK SIZING SETTINGS
# =============================================================================
RISK_PER_TRADE = 20.0  # Dollar amount of risk per trade for ATR-based sizing

# =============================================================================
# ANCHOR DATE PRESETS
# =============================================================================
ANCHOR_PRESETS = {
    "custom": "Custom Date",
    "prior_day": "Previous Trading Day Close",
    "prior_week": "Previous Week Close (Friday)",
    "prior_month": "Previous Month Close",
    "ytd": "Year to Date (Jan 1)",
}

# =============================================================================
# INDEX TICKERS (always analyzed for market structure)
# =============================================================================
INDEX_TICKERS = ["SPY", "QQQ", "DIA"]

# =============================================================================
# UI CONFIGURATION
# =============================================================================
MAX_TICKERS = 10
DEFAULT_TICKER_LIST = "sp500"

# =============================================================================
# CACHE TTL (seconds)
# =============================================================================
CACHE_TTL_INTRADAY = 3600   # 1 hour
CACHE_TTL_DAILY = 86400     # 24 hours

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
VERBOSE = True
LOG_LEVEL = "INFO"
