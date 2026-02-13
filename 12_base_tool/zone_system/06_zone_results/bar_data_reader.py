"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Bar Data Reader
================================================================================
Organization: XIII Trading LLC
Purpose: Read current price and d1_atr from bar_data worksheet for ATR
         distance calculations
================================================================================
"""

from typing import Dict, Optional, List
import xlwings as xw

from epoch_config import (
    WORKSHEET_BAR_DATA,
    TICKER_STRUCTURE_START_ROW,
    TICKER_STRUCTURE_END_ROW,
    PRICE_COLUMN,
    ON_OPTIONS_START_ROW,
    ON_OPTIONS_END_ROW,
    D1_ATR_COLUMN,
    TICKER_ID_COLUMN,
    VERBOSE
)


class BarDataReader:
    """
    Reads price and ATR data from bar_data worksheet for proximity calculations.
    
    This reader extracts:
    - Current price from ticker_structure section (rows 4-13, column E)
    - D1 ATR from on_options_metrics section (rows 73-82, column T)
    - Ticker ID for matching zones to the correct bar_data row
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_BAR_DATA]
        
        # Cache for ticker data (avoid repeated Excel reads)
        self._ticker_cache: Dict[str, Dict] = {}
        
    def get_ticker_price_atr(self, ticker_index: int) -> Dict[str, Optional[float]]:
        """
        Get current price and d1_atr for a ticker by slot index (1-10).
        
        Args:
            ticker_index: Ticker slot number (1-10)
            
        Returns:
            Dictionary with keys: 'ticker_id', 'price', 'd1_atr'
            Values may be None if not found
        """
        if ticker_index < 1 or ticker_index > 10:
            raise ValueError(f"ticker_index must be 1-10, got {ticker_index}")
        
        # Calculate row numbers
        ticker_row = TICKER_STRUCTURE_START_ROW + (ticker_index - 1)  # 4-13
        atr_row = ON_OPTIONS_START_ROW + (ticker_index - 1)          # 73-82
        
        # Read values
        ticker_id = self._read_cell(f"{TICKER_ID_COLUMN}{ticker_row}")
        price = self._read_cell_numeric(f"{PRICE_COLUMN}{ticker_row}")
        d1_atr = self._read_cell_numeric(f"{D1_ATR_COLUMN}{atr_row}")
        
        return {
            'ticker_id': ticker_id,
            'price': price,
            'd1_atr': d1_atr
        }
    
    def get_all_tickers_price_atr(self) -> Dict[str, Dict[str, float]]:
        """
        Get price and ATR for all 10 ticker slots.
        
        Returns:
            Dictionary keyed by ticker_id:
            {
                'AMZN_112825': {'price': 205.50, 'd1_atr': 4.25},
                'NVDA_112825': {'price': 140.30, 'd1_atr': 5.10},
                ...
            }
        """
        if VERBOSE:
            print(f"  Reading price and ATR data from '{WORKSHEET_BAR_DATA}'...")
        
        result = {}
        valid_count = 0
        
        for i in range(1, 11):
            data = self.get_ticker_price_atr(i)
            ticker_id = data.get('ticker_id')
            
            # Skip empty slots
            if ticker_id and str(ticker_id).strip() and ticker_id != 'None':
                # Only include if we have both price and ATR
                if data['price'] is not None and data['d1_atr'] is not None:
                    result[str(ticker_id)] = {
                        'price': data['price'],
                        'd1_atr': data['d1_atr']
                    }
                    valid_count += 1
                    
                    if VERBOSE:
                        print(f"    Slot {i}: {ticker_id} - "
                              f"Price: ${data['price']:.2f}, "
                              f"D1 ATR: ${data['d1_atr']:.2f}")
                else:
                    if VERBOSE:
                        print(f"    Slot {i}: {ticker_id} - "
                              f"WARNING: Missing price or ATR")
        
        if VERBOSE:
            print(f"  Loaded price/ATR data for {valid_count} tickers")
        
        # Cache the result
        self._ticker_cache = result
        
        return result
    
    def get_price_atr_by_ticker_id(self, ticker_id: str) -> Optional[Dict[str, float]]:
        """
        Get price and ATR for a specific ticker_id.
        
        Args:
            ticker_id: Ticker ID to look up (e.g., "AMZN_112825")
            
        Returns:
            Dictionary with 'price' and 'd1_atr', or None if not found
        """
        # Use cache if available
        if self._ticker_cache:
            return self._ticker_cache.get(ticker_id)
        
        # Otherwise search through all slots
        for i in range(1, 11):
            data = self.get_ticker_price_atr(i)
            if data.get('ticker_id') == ticker_id:
                if data['price'] is not None and data['d1_atr'] is not None:
                    return {
                        'price': data['price'],
                        'd1_atr': data['d1_atr']
                    }
        
        return None
    
    def _read_cell(self, cell_address: str) -> Optional[str]:
        """
        Read a cell value as string.
        
        Args:
            cell_address: Excel cell address (e.g., "B4")
            
        Returns:
            Cell value as string, or None if empty
        """
        value = self.sheet.range(cell_address).value
        if value is None:
            return None
        return str(value).strip()
    
    def _read_cell_numeric(self, cell_address: str) -> Optional[float]:
        """
        Read a cell value as float.
        
        Args:
            cell_address: Excel cell address (e.g., "E4")
            
        Returns:
            Cell value as float, or None if empty/invalid
        """
        value = self.sheet.range(cell_address).value
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_active_ticker_ids(self) -> List[str]:
        """
        Get list of active ticker_ids from bar_data (non-empty slots).
        
        Returns:
            List of ticker_id strings
        """
        ticker_ids = []
        for i in range(1, 11):
            row = TICKER_STRUCTURE_START_ROW + (i - 1)
            ticker_id = self._read_cell(f"{TICKER_ID_COLUMN}{row}")
            if ticker_id and ticker_id != 'None':
                ticker_ids.append(ticker_id)
        return ticker_ids


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    from epoch_config import EXCEL_FILEPATH
    
    print("=" * 70)
    print("BAR DATA READER - STANDALONE TEST")
    print("=" * 70)
    
    try:
        # Connect to Excel
        print("\nConnecting to Excel workbook...")
        wb = xw.Book(EXCEL_FILEPATH)
        
        # Create reader
        reader = BarDataReader(wb)
        
        # Read all tickers
        print("\nReading all ticker price/ATR data...")
        data = reader.get_all_tickers_price_atr()
        
        print(f"\nLoaded data for {len(data)} tickers:")
        for ticker_id, values in data.items():
            print(f"  {ticker_id}: Price=${values['price']:.2f}, "
                  f"D1_ATR=${values['d1_atr']:.2f}")
        
        # Test lookup by ticker_id
        print("\nTesting lookup by ticker_id...")
        active_tickers = reader.get_active_ticker_ids()
        if active_tickers:
            test_ticker = active_tickers[0]
            result = reader.get_price_atr_by_ticker_id(test_ticker)
            print(f"  Lookup '{test_ticker}': {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
