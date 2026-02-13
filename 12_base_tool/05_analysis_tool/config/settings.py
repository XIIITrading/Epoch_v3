"""
Application settings and configuration.
Epoch Analysis Tool - Streamlit Application
"""
from pathlib import Path
from datetime import date, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).parent.parent
EPOCH_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data" / "cache"
ZONE_SYSTEM_DIR = EPOCH_ROOT / "02_zone_system"
MARKET_SCANNER_DIR = EPOCH_ROOT / "01_market_scanner"

# Create cache directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# API CONFIGURATION
# =============================================================================
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")

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
