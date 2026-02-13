"""
Epoch Bar Data Module Configuration
XIII Trading LLC - Epoch Trading System

Module 1: Bar Data Configuration
"""

# Excel paths
EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
BAR_DATA_WORKSHEET = 'bar_data'
MARKET_OVERVIEW_WORKSHEET = 'market_overview'

# CRITICAL DIFFERENCE FROM MERIDIAN:
# Input tickers come from market_overview -> ticker_structure section (rows 36-45)
# NOT from bar_data (rows 4-13) as in Meridian

# Input cell ranges (from market_overview -> ticker_structure)
TICKER_INPUT_SECTION = 'ticker_structure'
MO_TICKER_START_ROW = 36  # t1_ticker starts at row 36 in market_overview
MO_TICKER_END_ROW = 45    # t10_ticker ends at row 45 in market_overview
TICKER_COLUMN = 'C'
DATE_COLUMN = 'D'

# Alternative: Read from bar_data worksheet (for fallback)
ALT_TICKER_START_ROW = 4
ALT_TICKER_END_ROW = 13

# Status cell (in bar_data worksheet)
STATUS_CELL = 'A1'

# Verbose output
VERBOSE = True

# API delay between tickers (seconds) - helps avoid rate limiting
API_DELAY = 0.5
