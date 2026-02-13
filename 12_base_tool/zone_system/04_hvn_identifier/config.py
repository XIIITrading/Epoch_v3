# config.py - Epoch HVN Identifier Configuration
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier\
# Purpose: Centralized configuration for the HVN Identifier module

"""
Configuration for Epoch HVN Identifier Module

Key difference from Meridian:
- Single user-defined epoch (start_date to current) instead of 9 fixed timeframes
- 10 non-overlapping POCs instead of 54 (6 per timeframe × 9)
- $0.01 price granularity instead of 100 fixed levels
- Volume-only ranking instead of proximity-based

UPDATED: Start date now read from market_overview S36:S45
"""

# =============================================================================
# EXCEL PATHS
# =============================================================================

EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
BAR_DATA_WORKSHEET = 'bar_data'
MARKET_OVERVIEW_WORKSHEET = 'market_overview'

# =============================================================================
# EPOCH START DATE SOURCE (from market_overview -> ticker_structure)
# =============================================================================

# Start date is now read from market_overview S36:S45 (same section as tickers)
# This keeps all user inputs consolidated in the market_overview ticker_structure
MO_START_DATE_COLUMN = 'S'
MO_START_DATE_START_ROW = 36  # t1 start_date at S36
MO_START_DATE_END_ROW = 45    # t10 start_date at S45

# Ticker source (also from market_overview)
MO_TICKER_COLUMN = 'C'
MO_TICKER_START_ROW = 36
MO_TICKER_END_ROW = 45

# =============================================================================
# HVN CALCULATION PARAMETERS
# =============================================================================

# Price granularity - $0.01 precision for volume profile
PRICE_GRANULARITY = 0.01

# Number of POCs to return per ticker
POC_COUNT = 10

# API request chunking (Polygon limits)
CHUNK_SIZE_DAYS = 30

# =============================================================================
# OVERLAP PREVENTION
# =============================================================================

# Overlap threshold = ATR / OVERLAP_ATR_DIVISOR
# POCs must be at least this distance apart
OVERLAP_ATR_DIVISOR = 2

# Fallback ATR if not available from Excel
DEFAULT_ATR = 2.0

# =============================================================================
# MARKET HOURS
# =============================================================================

# Include extended hours in volume profile calculation
INCLUDE_PRE_MARKET = True   # 04:00-09:30 ET (08:00-13:30 UTC)
INCLUDE_POST_MARKET = True  # 16:00-20:00 ET (20:00-00:00 UTC)

# Regular trading hours (UTC)
RTH_START_UTC = 13.5  # 13:30 UTC = 9:30 ET
RTH_END_UTC = 20.0    # 20:00 UTC = 16:00 ET

# Pre-market hours (UTC)
PRE_MARKET_START_UTC = 8.0   # 08:00 UTC = 04:00 ET
PRE_MARKET_END_UTC = 13.5    # 13:30 UTC = 09:30 ET

# Post-market hours (UTC)
POST_MARKET_START_UTC = 20.0  # 20:00 UTC = 16:00 ET
POST_MARKET_END_UTC = 24.0    # 00:00 UTC = 20:00 ET

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Verbose output for debugging
VERBOSE = True

# Round POC prices to this many decimal places
PRICE_DECIMAL_PLACES = 2

# =============================================================================
# CELL MAPPING REFERENCE
# =============================================================================

# Time HVN section rows in bar_data worksheet (OUTPUT destination)
TIME_HVN_START_ROW = 59
TIME_HVN_END_ROW = 68

# Column layout for time_hvn section (OUTPUT)
TIME_HVN_COLUMNS = {
    'ticker_id': 'B',      # e.g., "SPY.112724"
    'ticker': 'C',         # e.g., "SPY"
    'date': 'D',           # OUTPUT: Most recent data date
    'start_date': 'E',     # Now just for display (copied from market_overview)
    'hvn_poc1': 'F',       # Highest volume POC
    'hvn_poc2': 'G',
    'hvn_poc3': 'H',
    'hvn_poc4': 'I',
    'hvn_poc5': 'J',
    'hvn_poc6': 'K',
    'hvn_poc7': 'L',
    'hvn_poc8': 'M',
    'hvn_poc9': 'N',
    'hvn_poc10': 'O',      # 10th highest volume POC
}

# ATR source rows in on_options_metrics section
ATR_COLUMN = 'T'
ATR_START_ROW = 73
ATR_END_ROW = 82