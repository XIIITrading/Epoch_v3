# market_overview_reader.py - Epoch Market Overview Reader
# Reads direction and market structure levels from market_overview worksheet
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
EPOCH MARKET_OVERVIEW WORKSHEET STRUCTURE (ticker_structure section):
- Rows 36-45: t1-t10 ticker structure
- Columns:
  B: ticker_id
  C: ticker
  D: date
  E: price
  F: d1_dir (D1 direction)
  G: d1_s (D1 strong level)
  H: d1_w (D1 weak level)
  I: h4_dir (H4 direction)
  J: h4_s (H4 strong level)  
  K: h4_w (H4 weak level)
  L: h1_dir (H1 direction)
  M: h1_s (H1 strong level)
  N: h1_w (H1 weak level)
  O: m15_dir (M15 direction)
  P: m15_s (M15 strong level)
  Q: m15_w (M15 weak level)
  R: composite (Bull/Bear/Bull+/Bear+ direction)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EpochMarketOverviewReader:
    """Reads direction and market structure levels from market_overview worksheet"""
    
    # ticker_structure section starts at row 36
    TICKER_STRUCTURE_BASE = 36  # t1 at row 36, t2 at row 37, ...

    def __init__(self, excel_connection):
        """
        Initialize EpochMarketOverviewReader
        
        Args:
            excel_connection: Excel connection object with get_sheet() method
        """
        self.conn = excel_connection
        self.market_overview_sheet = excel_connection.get_sheet('market_overview')
        logger.info("EpochMarketOverviewReader initialized")

    def get_ticker_data(self, ticker_index: int) -> Dict:
        """
        Get direction and market structure for ticker
        
        Args:
            ticker_index: 1-based index (1-10) for ticker position
            
        Returns:
            dict with:
            - direction: 'Bull', 'Bull+', 'Bear', 'Bear+', or 'N/A'
            - d1_s, d1_w: D1 strong/weak levels
            - h4_s, h4_w: H4 strong/weak levels
            - h1_s, h1_w: H1 strong/weak levels
            - m15_s, m15_w: M15 strong/weak levels
        """
        if ticker_index < 1 or ticker_index > 10:
            raise ValueError(f"ticker_index must be between 1 and 10, got {ticker_index}")
        
        print(f"  Reading market_overview for Ticker {ticker_index}...")
        
        row = self.TICKER_STRUCTURE_BASE + (ticker_index - 1)
        
        result = {
            # Ticker metadata
            'ticker_id': self._read_cell(f'B{row}'),
            'ticker': self._read_cell(f'C{row}'),
            
            # Composite direction (column R)
            'direction': self._read_cell(f'R{row}') or 'N/A',
            
            # D1 Market Structure (columns G, H)
            'd1_s': self._read_numeric(f'G{row}'),
            'd1_w': self._read_numeric(f'H{row}'),
            
            # H4 Market Structure (columns J, K)
            'h4_s': self._read_numeric(f'J{row}'),
            'h4_w': self._read_numeric(f'K{row}'),
            
            # H1 Market Structure (columns M, N)
            'h1_s': self._read_numeric(f'M{row}'),
            'h1_w': self._read_numeric(f'N{row}'),
            
            # M15 Market Structure (columns P, Q)
            'm15_s': self._read_numeric(f'P{row}'),
            'm15_w': self._read_numeric(f'Q{row}'),
        }
        
        # Count how many market structure levels we found
        ms_count = sum(1 for k in ['d1_s', 'd1_w', 'h4_s', 'h4_w', 'h1_s', 'h1_w', 'm15_s', 'm15_w']
                       if result.get(k) is not None)
        
        print(f"    ✓ Direction: {result['direction']}, Market Structure Levels: {ms_count}/8")
        
        return result

    def _read_cell(self, cell_ref: str) -> Optional[str]:
        """
        Read a cell value as string, return None if empty
        
        Args:
            cell_ref: Cell reference like 'A1', 'R36', etc.
            
        Returns:
            Cell value as string, or None if empty
        """
        try:
            value = self.market_overview_sheet.range(cell_ref).value
            if value is None or value == '':
                return None
            return str(value).strip()
        except Exception as e:
            logger.warning(f"Error reading cell {cell_ref}: {e}")
            return None

    def _read_numeric(self, cell_ref: str) -> Optional[float]:
        """
        Read a cell value as float, return None if empty or non-numeric
        
        Args:
            cell_ref: Cell reference like 'G36', etc.
            
        Returns:
            Cell value as float, or None if empty/non-numeric
        """
        try:
            value = self.market_overview_sheet.range(cell_ref).value
            if value is None or value == '' or value == 0:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    def validate_ticker_match(self, bar_data_ticker: str, market_overview_ticker: str) -> bool:
        """
        Validate that the ticker from bar_data matches market_overview
        
        Args:
            bar_data_ticker: Ticker from bar_data worksheet
            market_overview_ticker: Ticker from market_overview worksheet
            
        Returns:
            bool: True if tickers match (or market_overview is None)
        """
        if market_overview_ticker is None:
            return True  # Allow if market_overview hasn't been populated
        
        return str(bar_data_ticker).upper() == str(market_overview_ticker).upper()
