"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Bar Data Reader
================================================================================
Organization: XIII Trading LLC
Purpose: Read HVN POCs and current price from bar_data worksheet for
         target selection
================================================================================
"""

from typing import Dict, List, Optional, Tuple
import xlwings as xw

from epoch_config import (
    WORKSHEET_BAR_DATA,
    TICKER_STRUCTURE_START_ROW,
    TICKER_ID_COLUMN,
    PRICE_COLUMN,
    TIME_HVN_START_ROW,
    HVN_POC_COLUMNS,
    VERBOSE
)


class BarDataReader:
    """
    Reads HVN POCs and price data from bar_data worksheet.
    
    Used for:
    - Getting current price for bull/bear POC identification
    - Getting all 10 HVN POCs for target selection
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_BAR_DATA]
        
        # Cache for ticker data
        self._ticker_cache: Dict[str, Dict] = {}
        
    def get_ticker_data(self, ticker_index: int) -> Dict:
        """
        Get ticker_id, current price, and all 10 HVN POCs for a ticker slot.
        
        Args:
            ticker_index: Ticker slot number (1-10)
            
        Returns:
            Dictionary with keys: 'ticker_id', 'price', 'hvn_pocs' (list of 10)
        """
        if ticker_index < 1 or ticker_index > 10:
            raise ValueError(f"ticker_index must be 1-10, got {ticker_index}")
        
        # Calculate row numbers
        ticker_row = TICKER_STRUCTURE_START_ROW + (ticker_index - 1)  # 4-13
        hvn_row = TIME_HVN_START_ROW + (ticker_index - 1)             # 59-68
        
        # Read ticker_id and price
        ticker_id = self._read_cell(f"{TICKER_ID_COLUMN}{ticker_row}")
        price = self._read_cell_numeric(f"{PRICE_COLUMN}{ticker_row}")
        
        # Read all 10 HVN POCs
        hvn_pocs = []
        for poc_name, col in HVN_POC_COLUMNS.items():
            poc_value = self._read_cell_numeric(f"{col}{hvn_row}")
            hvn_pocs.append(poc_value)
        
        return {
            'ticker_id': ticker_id,
            'price': price,
            'hvn_pocs': hvn_pocs
        }
    
    def get_all_tickers_data(self) -> Dict[str, Dict]:
        """
        Get price and HVN POCs for all 10 ticker slots.
        
        Returns:
            Dictionary keyed by ticker_id:
            {
                'AMZN_112825': {
                    'price': 205.50,
                    'hvn_pocs': [232.75, 230.50, ..., 220.00]
                },
                ...
            }
        """
        if VERBOSE:
            print(f"  Reading HVN POCs from '{WORKSHEET_BAR_DATA}'...")
        
        result = {}
        
        for i in range(1, 11):
            data = self.get_ticker_data(i)
            ticker_id = data.get('ticker_id')
            
            # Skip empty slots
            if ticker_id and str(ticker_id).strip() and ticker_id != 'None':
                # Filter out None values from HVN POCs
                valid_pocs = [p for p in data['hvn_pocs'] if p is not None]
                
                result[str(ticker_id)] = {
                    'price': data['price'],
                    'hvn_pocs': data['hvn_pocs'],  # Keep all 10 (some may be None)
                    'valid_pocs': valid_pocs        # Only non-None POCs
                }
                
                if VERBOSE:
                    print(f"    Slot {i}: {ticker_id} - "
                          f"Price: ${data['price']:.2f}, "
                          f"Valid POCs: {len(valid_pocs)}")
        
        if VERBOSE:
            print(f"  Loaded HVN POC data for {len(result)} tickers")
        
        self._ticker_cache = result
        return result
    
    def get_hvn_pocs_by_ticker_id(self, ticker_id: str) -> Optional[List[float]]:
        """
        Get list of 10 HVN POCs for a specific ticker_id.
        
        Args:
            ticker_id: Ticker ID to look up
            
        Returns:
            List of 10 POC values (some may be None), or None if not found
        """
        if self._ticker_cache:
            data = self._ticker_cache.get(ticker_id)
            if data:
                return data['hvn_pocs']
        
        # Search through all slots if cache is empty
        for i in range(1, 11):
            data = self.get_ticker_data(i)
            if data.get('ticker_id') == ticker_id:
                return data['hvn_pocs']
        
        return None
    
    def get_price_by_ticker_id(self, ticker_id: str) -> Optional[float]:
        """
        Get current price for a specific ticker_id.
        
        Args:
            ticker_id: Ticker ID to look up
            
        Returns:
            Current price, or None if not found
        """
        if self._ticker_cache:
            data = self._ticker_cache.get(ticker_id)
            if data:
                return data['price']
        
        # Search through all slots if cache is empty
        for i in range(1, 11):
            data = self.get_ticker_data(i)
            if data.get('ticker_id') == ticker_id:
                return data['price']
        
        return None
    
    def get_ticker_index_by_id(self, ticker_id: str) -> Optional[int]:
        """
        Get slot index (1-10) for a ticker_id.
        
        Args:
            ticker_id: Ticker ID to look up
            
        Returns:
            Slot index (1-10), or None if not found
        """
        for i in range(1, 11):
            row = TICKER_STRUCTURE_START_ROW + (i - 1)
            slot_ticker_id = self._read_cell(f"{TICKER_ID_COLUMN}{row}")
            if slot_ticker_id == ticker_id:
                return i
        return None
    
    def _read_cell(self, cell_address: str) -> Optional[str]:
        """Read a cell value as string."""
        value = self.sheet.range(cell_address).value
        if value is None:
            return None
        return str(value).strip()
    
    def _read_cell_numeric(self, cell_address: str) -> Optional[float]:
        """Read a cell value as float."""
        value = self.sheet.range(cell_address).value
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    from epoch_config import EXCEL_FILEPATH
    
    print("=" * 70)
    print("BAR DATA READER (HVN POCs) - STANDALONE TEST")
    print("=" * 70)
    
    try:
        print("\nConnecting to Excel workbook...")
        wb = xw.Book(EXCEL_FILEPATH)
        
        reader = BarDataReader(wb)
        data = reader.get_all_tickers_data()
        
        print(f"\nLoaded data for {len(data)} tickers:")
        for ticker_id, values in data.items():
            valid_pocs = [p for p in values['hvn_pocs'] if p is not None]
            print(f"\n  {ticker_id}:")
            print(f"    Price: ${values['price']:.2f}")
            print(f"    HVN POCs: {len(valid_pocs)} valid")
            for i, poc in enumerate(values['hvn_pocs'][:5], 1):
                if poc:
                    print(f"      hvn_poc{i}: ${poc:.2f}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
