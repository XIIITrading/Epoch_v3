"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Market Overview Reader
================================================================================
Organization: XIII Trading LLC
Purpose: Read composite direction from market_overview worksheet for
         primary/secondary setup assignment
================================================================================
"""

from typing import Dict, Optional
import xlwings as xw

from epoch_config import (
    WORKSHEET_MARKET_OVERVIEW,
    MO_TICKER_STRUCTURE_START_ROW,
    MO_TICKER_ID_COLUMN,
    MO_COMPOSITE_COLUMN,
    VERBOSE
)


class MarketOverviewReader:
    """
    Reads direction data from the market_overview worksheet.
    
    The composite direction (Bull, Bull+, Bear, Bear+) determines
    which setup is primary (with trend) vs secondary (counter-trend).
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_MARKET_OVERVIEW]
        
        # Cache for direction data
        self._direction_cache: Dict[str, str] = {}
        
    def get_direction(self, ticker_index: int) -> Optional[str]:
        """
        Get composite direction for a ticker by slot index.
        
        Args:
            ticker_index: Ticker slot number (1-10)
            
        Returns:
            Direction string: 'Bull', 'Bull+', 'Bear', 'Bear+', or None
        """
        if ticker_index < 1 or ticker_index > 10:
            raise ValueError(f"ticker_index must be 1-10, got {ticker_index}")
        
        row = MO_TICKER_STRUCTURE_START_ROW + (ticker_index - 1)  # 36-45
        
        ticker_id = self._read_cell(f"{MO_TICKER_ID_COLUMN}{row}")
        direction = self._read_cell(f"{MO_COMPOSITE_COLUMN}{row}")
        
        return direction
    
    def get_all_directions(self) -> Dict[str, str]:
        """
        Get direction for all ticker slots.
        
        Returns:
            Dictionary mapping ticker_id to direction:
            {
                'AMZN_112825': 'Bull+',
                'NVDA_112825': 'Bear',
                ...
            }
        """
        if VERBOSE:
            print(f"  Reading directions from '{WORKSHEET_MARKET_OVERVIEW}'...")
        
        result = {}
        
        for i in range(1, 11):
            row = MO_TICKER_STRUCTURE_START_ROW + (i - 1)
            
            ticker_id = self._read_cell(f"{MO_TICKER_ID_COLUMN}{row}")
            direction = self._read_cell(f"{MO_COMPOSITE_COLUMN}{row}")
            
            # Skip empty slots
            if ticker_id and str(ticker_id).strip() and ticker_id != 'None':
                result[str(ticker_id)] = direction if direction else 'N/A'
                
                if VERBOSE:
                    print(f"    Slot {i}: {ticker_id} - Direction: {direction}")
        
        if VERBOSE:
            print(f"  Loaded direction data for {len(result)} tickers")
        
        self._direction_cache = result
        return result
    
    def get_direction_by_ticker_id(self, ticker_id: str) -> Optional[str]:
        """
        Get direction for a specific ticker_id.
        
        Args:
            ticker_id: Ticker ID to look up
            
        Returns:
            Direction string, or None if not found
        """
        if self._direction_cache:
            return self._direction_cache.get(ticker_id)
        
        # Search through all slots if cache is empty
        for i in range(1, 11):
            row = MO_TICKER_STRUCTURE_START_ROW + (i - 1)
            slot_ticker_id = self._read_cell(f"{MO_TICKER_ID_COLUMN}{row}")
            if slot_ticker_id == ticker_id:
                return self._read_cell(f"{MO_COMPOSITE_COLUMN}{row}")
        
        return None
    
    def _read_cell(self, cell_address: str) -> Optional[str]:
        """Read a cell value as string."""
        value = self.sheet.range(cell_address).value
        if value is None:
            return None
        return str(value).strip()


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    from epoch_config import EXCEL_FILEPATH
    
    print("=" * 70)
    print("MARKET OVERVIEW READER - STANDALONE TEST")
    print("=" * 70)
    
    try:
        print("\nConnecting to Excel workbook...")
        wb = xw.Book(EXCEL_FILEPATH)
        
        reader = MarketOverviewReader(wb)
        directions = reader.get_all_directions()
        
        print(f"\nLoaded directions for {len(directions)} tickers:")
        for ticker_id, direction in directions.items():
            print(f"  {ticker_id}: {direction}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
