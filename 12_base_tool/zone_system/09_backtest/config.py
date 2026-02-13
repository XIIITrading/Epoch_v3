"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v2.0
Configuration Settings
XIII Trading LLC
================================================================================
"""
from datetime import time
from pathlib import Path

# =============================================================================
# FILE PATHS
# =============================================================================
BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
WORKBOOK_NAME = "epoch_v1.xlsm"
WORKBOOK_PATH = BASE_DIR / WORKBOOK_NAME

# =============================================================================
# WORKSHEET NAMES
# =============================================================================
WORKSHEETS = {
    'market_overview': 'market_overview',
    'bar_data': 'bar_data',
    'zone_results': 'zone_results',
    'analysis': 'Analysis',
    'backtest': 'backtest'
}

# =============================================================================
# POLYGON API
# =============================================================================
POLYGON_API_KEY = None  # Will be loaded from credentials.py
API_DELAY = 0.25  # Seconds between API calls
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
ENTRY_START_TIME = time(9, 30)   # Market open
ENTRY_END_TIME = time(15, 30)    # Stop new entries
FORCE_EXIT_TIME = time(15, 50)   # Close all positions

# =============================================================================
# BACKTEST PARAMETERS
# =============================================================================
BAR_TIMEFRAME_MINUTES = 5  # M5 bars for entry/exit

# Entry Models
ENTRY_MODELS = {
    'EPCH1': 1,  # Primary zone continuation
    'EPCH2': 2,  # Primary zone rejection
    'EPCH3': 3,  # Secondary zone continuation
    'EPCH4': 4   # Secondary zone rejection
}

# Stop buffer percentage (applied to zone distance for stop calculation)
# LONG:  stop = zone_low - (zone_distance * STOP_BUFFER_PCT)
# SHORT: stop = zone_high + (zone_distance * STOP_BUFFER_PCT)
STOP_BUFFER_PCT = 0.05  # 5% buffer on stops

# Minimum risk filter - skip trades with risk below this
MIN_RISK_DOLLARS = 0.10  # Minimum $0.10 risk per share

# Zone touch buffer - price within this distance counts as "touching" zone
# This captures trades where price comes very close but doesn't technically touch
ZONE_TOUCH_BUFFER = 0.25  # $0.25 buffer for zone interaction

# =============================================================================
# EXIT PARAMETERS
# =============================================================================
TARGET_R_MULTIPLE = 3.0  # 3R target

USE_CHOCH_EXIT = True  # Enable M5 CHoCH structure exit
FRACTAL_LENGTH = 5     # Bars for CHoCH detection

# Stop loss assumption for backtesting
# True = stops always fill at stop price (-1R)
# False = stops fill at actual bar price (can be worse than -1R)
ASSUME_STOP_FILL_AT_PRICE = True

# =============================================================================
# ANALYSIS WORKSHEET - Primary/Secondary Setup Details
# Based on cell map: PRIMARY B31:L40, SECONDARY N31:X40
# =============================================================================
ANALYSIS_PRIMARY_START_ROW = 31
ANALYSIS_PRIMARY_END_ROW = 40

# PRIMARY SECTION (B31:L40) - With-trend setups
ANALYSIS_PRIMARY_COLUMNS = {
    'ticker': 'B',
    'direction': 'C',
    'ticker_id': 'D',
    'zone_id': 'E',
    'hvn_poc': 'F',
    'zone_high': 'G',
    'zone_low': 'H',
    'tier': 'I',
    'target_id': 'J',
    'target': 'K',
    'rr': 'L'
}

ANALYSIS_SECONDARY_START_ROW = 31
ANALYSIS_SECONDARY_END_ROW = 40

# SECONDARY SECTION (N31:X40) - Counter-trend setups
ANALYSIS_SECONDARY_COLUMNS = {
    'ticker': 'N',
    'direction': 'O',
    'ticker_id': 'P',
    'zone_id': 'Q',
    'hvn_poc': 'R',
    'zone_high': 'S',
    'zone_low': 'T',
    'tier': 'U',
    'target_id': 'V',
    'target': 'W',
    'rr': 'X'
}

# =============================================================================
# ZONE RESULTS INPUT (Columns A-N from Module 06)
# =============================================================================
ZONE_RESULTS_START_ROW = 2
ZONE_RESULTS_COLUMNS = {
    'ticker_id': 'A',
    'ticker': 'B',
    'date': 'C',
    'price': 'D',
    'direction': 'E',
    'zone_id': 'F',
    'hvn_poc': 'G',
    'zone_high': 'H',
    'zone_low': 'I',
    'overlaps': 'J',
    'score': 'K',
    'rank': 'L',
    'confluences': 'M'
}

# Setup columns from Module 07 (O-T)
ZONE_RESULTS_SETUP_COLUMNS = {
    'epch_bull': 'O',
    'epch_bear': 'P',
    'epch_bull_price': 'Q',
    'epch_bear_price': 'R',
    'epch_bull_target': 'S',
    'epch_bear_target': 'T'
}

# =============================================================================
# MARKET OVERVIEW - Direction (kept for reference)
# =============================================================================
MO_TICKER_START_ROW = 36
MO_TICKER_END_ROW = 45
MO_TICKER_ID_COLUMN = 'B'
MO_COMPOSITE_COLUMN = 'R'

# =============================================================================
# BAR DATA - Price and ATR
# =============================================================================
BD_TICKER_START_ROW = 4
BD_TICKER_END_ROW = 13
BD_TICKER_ID_COLUMN = 'B'
BD_PRICE_COLUMN = 'E'

# ATR section (rows 73-82)
BD_ATR_START_ROW = 73
BD_ATR_END_ROW = 82
BD_ATR_TICKER_ID_COLUMN = 'B'
BD_M5_ATR_COLUMN = 'Q'
BD_D1_ATR_COLUMN = 'T'

# =============================================================================
# BACKTEST OUTPUT
# =============================================================================
BACKTEST_TRADE_LOG_START_ROW = 2

# Trade log columns - trade_id in column A, all others shifted right by 1
# Format: {ticker}_{MMDDYY}_{model}_{HHMM} (e.g., LLY_120925_EPCH2_1450)
BACKTEST_TRADE_LOG_COLUMNS = {
    'trade_id': 'A',      # NEW: Format ticker_MMDDYY_model_HHMM
    'date': 'B',          # Was A
    'ticker': 'C',        # Was B
    'model': 'D',         # Was C
    'zone_type': 'E',     # Was D
    'direction': 'F',     # Was E
    'zone_high': 'G',     # Was F
    'zone_low': 'H',      # Was G
    'entry_price': 'I',   # Was H
    'entry_time': 'J',    # Was I
    'stop_price': 'K',    # Was J
    'target_3r': 'L',     # Was K
    'target_calc': 'M',   # Was L
    'target_used': 'N',   # Was M
    'exit_price': 'O',    # Was N
    'exit_time': 'P',     # Was O
    'exit_reason': 'Q',   # Was P
    'pnl_dollars': 'R',   # Was Q
    'pnl_r': 'S',         # Was R
    'risk': 'T',          # Was S
    'win': 'U'            # Was T
}

# Summary section (shifted right by 1)
BACKTEST_SUMMARY_START_ROW = 2
BACKTEST_SUMMARY_START_COL = 'W'  # Was V

# =============================================================================
# VALID RANKS FOR TRADING
# =============================================================================
VALID_RANKS = ['L2', 'L3', 'L4', 'L5']

# =============================================================================
# DIRECTION MAPPINGS
# =============================================================================
BULLISH_DIRECTIONS = ['Bull', 'Bull+']
BEARISH_DIRECTIONS = ['Bear', 'Bear+']

# =============================================================================
# DISPLAY/LOGGING
# =============================================================================
VERBOSE = True