"""
Epoch Ticker Structure Configuration
Epoch Trading System v1 - XIII Trading LLC

Configuration for dynamic ticker list processing (up to 10 tickers).
Reads tickers from Excel C36:C45, calculates market structure, writes results.
"""

from typing import Dict
from datetime import datetime

# ============================================================================
# POLYGON API CONFIGURATION
# ============================================================================

POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"
POLYGON_BASE_URL = "https://api.polygon.io"

# ============================================================================
# TIMEFRAME CONFIGURATION
# ============================================================================

TIMEFRAMES = {
    'D1': {
        'polygon_timespan': 'day',
        'polygon_multiplier': 1,
        'label': 'Daily',
        'bars_needed': 150,
        'weight': 1.5
    },
    'H4': {
        'polygon_timespan': 'hour',
        'polygon_multiplier': 4,
        'label': '4-Hour',
        'bars_needed': 200,
        'weight': 1.5
    },
    'H1': {
        'polygon_timespan': 'hour',
        'polygon_multiplier': 1,
        'label': '1-Hour',
        'bars_needed': 250,
        'weight': 1.0
    },
    'M15': {
        'polygon_timespan': 'minute',
        'polygon_multiplier': 15,
        'label': '15-Minute',
        'bars_needed': 300,
        'weight': 0.5
    },
    'M1': {
        'polygon_timespan': 'minute',
        'polygon_multiplier': 1,
        'label': '1-Minute',
        'bars_needed': 10,
        'weight': 0.0  # Not used for structure analysis, only for scan price
    }
}

# ============================================================================
# MARKET STRUCTURE CALCULATION SETTINGS
# ============================================================================

FRACTAL_LENGTH = 5

# ============================================================================
# EXCEL CONFIGURATION
# ============================================================================

EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
WORKSHEET_NAME = 'market_overview'

# ============================================================================
# TICKER INPUT CONFIGURATION
# ============================================================================

# Ticker input cells (read from C36:C45)
TICKER_INPUT_ROWS = list(range(36, 46))  # Rows 36-45 (10 tickers max)

# Row mapping: t1 = row 36, t2 = row 37, ... t10 = row 45
TICKER_ROWS = {
    1: 36,
    2: 37,
    3: 38,
    4: 39,
    5: 40,
    6: 41,
    7: 42,
    8: 43,
    9: 44,
    10: 45
}

# ============================================================================
# COLUMN MAPPINGS (same for all rows 36-45)
# ============================================================================

COLUMNS = {
    'ticker_id': 'B',      # AMD_112525 format
    'ticker': 'C',         # Ticker symbol (input/output)
    'date': 'D',           # Date run
    'price': 'E',          # Scan price (M1 close)
    'D1_dir': 'F',         # D1 Direction
    'D1_strong': 'G',      # D1 Strong level
    'D1_weak': 'H',        # D1 Weak level
    'H4_dir': 'I',         # H4 Direction
    'H4_strong': 'J',      # H4 Strong level
    'H4_weak': 'K',        # H4 Weak level
    'H1_dir': 'L',         # H1 Direction
    'H1_strong': 'M',      # H1 Strong level
    'H1_weak': 'N',        # H1 Weak level
    'M15_dir': 'O',        # M15 Direction
    'M15_strong': 'P',     # M15 Strong level
    'M15_weak': 'Q',       # M15 Weak level
    'composite': 'R'       # Composite direction
}

# ============================================================================
# OUTPUT FORMAT
# ============================================================================

MARKET_STRUCTURE_VALUES = {
    'BULL': 'Bull',
    'BEAR': 'Bear',
    'NEUTRAL': 'Neutral',
    'ERROR': 'ERROR'
}

# Display labels for internal use
STRUCTURE_LABELS = {
    1: 'BULL',
    -1: 'BEAR',
    0: 'NEUTRAL',
    None: 'ERROR'
}

# Date format for ticker_id (MMDDYY)
TICKER_ID_DATE_FORMAT = '%m%d%y'

# Date format for Column D (full datetime)
DATE_FORMAT = '%m-%d-%y'

# Price format (2 decimals)
PRICE_FORMAT = '{:.2f}'

# NULL value for missing strong/weak levels
NULL_VALUE = 'NULL'

# ============================================================================
# DATA FETCH SETTINGS
# ============================================================================

DATA_LOOKBACK_DAYS = {
    'D1': 250,
    'H4': 100,
    'H1': 50,
    'M15': 15,
    'M1': 2  # 2 days for most recent minute bar including pre-market
}

API_RATE_LIMIT_DELAY = 0.25
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

VERBOSE = True

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_cell_reference(row: int, column: str) -> str:
    """
    Get Excel cell reference for a row and column.
    
    Args:
        row: Row number (36-45)
        column: Column letter ('B', 'C', 'D', etc.)
    
    Returns:
        Cell reference (e.g., 'B36', 'F40')
    """
    return f"{column}{row}"


def validate_ticker(ticker: str) -> bool:
    """
    Validate ticker symbol format.
    
    Args:
        ticker: Ticker symbol string
    
    Returns:
        True if valid, False otherwise
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Remove whitespace
    ticker = ticker.strip().upper()
    
    # Basic validation: 1-5 letters, alphabetic
    if len(ticker) < 1 or len(ticker) > 5:
        return False
    
    if not ticker.isalpha():
        return False
    
    return True


def format_ticker_id(ticker: str) -> str:
    """
    Format ticker ID with current date.
    
    Args:
        ticker: Ticker symbol
    
    Returns:
        Formatted ticker ID (e.g., 'AMD_112525')
    """
    date_str = datetime.now().strftime(TICKER_ID_DATE_FORMAT)
    return f"{ticker}_{date_str}"


def format_price(price: float) -> str:
    """
    Format price with 2 decimal places.
    
    Args:
        price: Price value or None
    
    Returns:
        Formatted string or NULL
    """
    if price is None:
        return NULL_VALUE
    return PRICE_FORMAT.format(price)


def get_current_date() -> str:
    """
    Get current date formatted for Excel.
    
    Returns:
        Date string in format mm-dd-yy
    """
    return datetime.now().strftime(DATE_FORMAT)


def calculate_weighted_direction(timeframe_results: Dict[str, Dict]) -> str:
    """
    Calculate weighted composite direction.
    
    Weights:
    - D1: 1.5
    - H4: 1.5
    - H1: 1.0
    - M15: 0.5
    
    Args:
        timeframe_results: Dictionary mapping timeframe to results
    
    Returns:
        "Bull+", "Bull", "Bear+", or "Bear"
    """
    bull_score = 0.0
    bear_score = 0.0
    
    for timeframe, result in timeframe_results.items():
        if timeframe == 'D1':
            weight = 1.5
        elif timeframe == 'H4':
            weight = 1.5
        elif timeframe == 'H1':
            weight = 1.0
        elif timeframe == 'M15':
            weight = 0.5
        else:
            continue
        
        direction_label = result.get('direction_label', 'ERROR')
        
        if direction_label == 'BULL':
            bull_score += weight
        elif direction_label == 'BEAR':
            bear_score += weight
    
    # Decision logic
    if bull_score >= 3.5:
        return "Bull+"
    elif bull_score > bear_score:
        return "Bull"
    elif bear_score >= 3.5:
        return "Bear+"
    elif bear_score > bull_score:
        return "Bear"
    else:
        # Tie - use M15 as tiebreaker
        if 'M15' in timeframe_results:
            m15_label = timeframe_results['M15'].get('direction_label', 'ERROR')
            if m15_label == 'BULL':
                return "Bull"
            elif m15_label == 'BEAR':
                return "Bear"
        return "Bear"  # Conservative default