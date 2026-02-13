# bar_data_reader.py - Epoch Bar Data Reader
# Reads ticker data from bar_data worksheet using cell mappings from epoch_cell_map.yaml
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
EPOCH BAR_DATA WORKSHEET STRUCTURE:
- Rows 4-13: ticker_structure (ticker_id, ticker, date, price)
- Rows 17-26: monthly_metrics (m1_01-04, m1_po-pc)
- Rows 31-40: weekly_metrics (w1_01-04, w1_po-pc)
- Rows 45-54: daily_metrics (d1_01-04, d1_po-pc)
- Rows 59-68: time_hvn (hvn_poc1-10)
- Rows 73-82: on_options_metrics (d1_onh, d1_onl, op_01-10, ATR values)
- Rows 86-95: add_metrics (Camarilla levels d1/w1/m1 s6/s4/s3/r3/r4/r6)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EpochBarDataReader:
    """Reads ticker-specific data from Epoch bar_data worksheet"""
    
    # Row offsets from base row for each section (1-indexed ticker -> 0-indexed offset)
    TICKER_STRUCTURE_BASE = 4      # t1 at row 4, t2 at row 5, ...
    MONTHLY_METRICS_BASE = 17      # t1 at row 17, t2 at row 18, ...
    WEEKLY_METRICS_BASE = 31       # t1 at row 31, t2 at row 32, ...
    DAILY_METRICS_BASE = 45        # t1 at row 45, t2 at row 46, ...
    TIME_HVN_BASE = 59             # t1 at row 59, t2 at row 60, ...
    ON_OPTIONS_METRICS_BASE = 73   # t1 at row 73, t2 at row 74, ...
    ADD_METRICS_BASE = 86          # t1 at row 86, t2 at row 87, ...

    def __init__(self, excel_connection):
        """
        Initialize EpochBarDataReader
        
        Args:
            excel_connection: Excel connection object with get_sheet() method
        """
        self.conn = excel_connection
        self.bar_data_sheet = excel_connection.get_sheet('bar_data')
        logger.info("EpochBarDataReader initialized")

    def read_ticker_data(self, ticker_index: int) -> Dict:
        """
        Read all data for a specific ticker from bar_data worksheet
        
        Args:
            ticker_index: 1-based index (1-10) for ticker position
            
        Returns:
            dict: inputs dictionary with all bar_data metrics for this ticker
        """
        if ticker_index < 1 or ticker_index > 10:
            raise ValueError(f"ticker_index must be between 1 and 10, got {ticker_index}")
        
        print(f"\n  Reading bar_data for Ticker {ticker_index}...")
        
        inputs = {}
        
        # Read each section
        self._read_ticker_structure(inputs, ticker_index)
        self._read_monthly_metrics(inputs, ticker_index)
        self._read_weekly_metrics(inputs, ticker_index)
        self._read_daily_metrics(inputs, ticker_index)
        self._read_hvn_pocs(inputs, ticker_index)
        self._read_on_options_metrics(inputs, ticker_index)
        self._read_camarilla_levels(inputs, ticker_index)
        
        field_count = len([v for v in inputs.values() if v is not None])
        print(f"    ✓ Read {field_count} fields for Ticker {ticker_index}")
        
        return inputs

    def _read_ticker_structure(self, inputs: Dict, ticker_index: int):
        """Read ticker metadata from ticker_structure section (rows 4-13)"""
        row = self.TICKER_STRUCTURE_BASE + (ticker_index - 1)
        
        # Column mapping for ticker_structure
        # ticker_id, ticker, date are strings; price is numeric
        inputs['ticker_id'] = self._read_cell_string(f'B{row}')
        inputs['ticker'] = self._read_cell_string(f'C{row}')
        inputs['date'] = self._read_cell_string(f'D{row}')
        inputs['price'] = self._read_cell(f'E{row}')
        
        # Parse ticker from ticker_id if needed
        if inputs['ticker'] is None and inputs['ticker_id']:
            ticker_id = str(inputs['ticker_id'])
            inputs['ticker'] = ticker_id.split('.')[0] if '.' in ticker_id else ticker_id

    def _read_monthly_metrics(self, inputs: Dict, ticker_index: int):
        """Read monthly OHLC from monthly_metrics section (rows 17-26)"""
        row = self.MONTHLY_METRICS_BASE + (ticker_index - 1)
        
        # Current month OHLC (columns E-H)
        inputs['m1_01'] = self._read_cell(f'E{row}')  # Open
        inputs['m1_02'] = self._read_cell(f'F{row}')  # High
        inputs['m1_03'] = self._read_cell(f'G{row}')  # Low
        inputs['m1_04'] = self._read_cell(f'H{row}')  # Close
        
        # Prior month OHLC (columns I-L)
        inputs['m1_po'] = self._read_cell(f'I{row}')  # Prior Open
        inputs['m1_ph'] = self._read_cell(f'J{row}')  # Prior High
        inputs['m1_pl'] = self._read_cell(f'K{row}')  # Prior Low
        inputs['m1_pc'] = self._read_cell(f'L{row}')  # Prior Close

    def _read_weekly_metrics(self, inputs: Dict, ticker_index: int):
        """Read weekly OHLC from weekly_metrics section (rows 31-40)"""
        row = self.WEEKLY_METRICS_BASE + (ticker_index - 1)
        
        # Current week OHLC (columns E-H)
        inputs['w1_01'] = self._read_cell(f'E{row}')  # Open
        inputs['w1_02'] = self._read_cell(f'F{row}')  # High
        inputs['w1_03'] = self._read_cell(f'G{row}')  # Low
        inputs['w1_04'] = self._read_cell(f'H{row}')  # Close
        
        # Prior week OHLC (columns I-L)
        inputs['w1_po'] = self._read_cell(f'I{row}')  # Prior Open
        inputs['w1_ph'] = self._read_cell(f'J{row}')  # Prior High
        inputs['w1_pl'] = self._read_cell(f'K{row}')  # Prior Low
        inputs['w1_pc'] = self._read_cell(f'L{row}')  # Prior Close

    def _read_daily_metrics(self, inputs: Dict, ticker_index: int):
        """Read daily OHLC from daily_metrics section (rows 45-54)"""
        row = self.DAILY_METRICS_BASE + (ticker_index - 1)
        
        # Current day OHLC (columns E-H)
        inputs['d1_01'] = self._read_cell(f'E{row}')  # Open
        inputs['d1_02'] = self._read_cell(f'F{row}')  # High
        inputs['d1_03'] = self._read_cell(f'G{row}')  # Low
        inputs['d1_04'] = self._read_cell(f'H{row}')  # Close
        
        # Prior day OHLC (columns I-L)
        inputs['d1_po'] = self._read_cell(f'I{row}')  # Prior Open
        inputs['d1_ph'] = self._read_cell(f'J{row}')  # Prior High
        inputs['d1_pl'] = self._read_cell(f'K{row}')  # Prior Low
        inputs['d1_pc'] = self._read_cell(f'L{row}')  # Prior Close

    def _read_hvn_pocs(self, inputs: Dict, ticker_index: int):
        """Read HVN POCs from time_hvn section (rows 59-68)"""
        row = self.TIME_HVN_BASE + (ticker_index - 1)
        
        # HVN POCs in columns F-O (hvn_poc1 through hvn_poc10)
        for i in range(1, 11):
            col = chr(ord('F') + (i - 1))  # F, G, H, I, J, K, L, M, N, O
            inputs[f'hvn_poc{i}'] = self._read_cell(f'{col}{row}')

    def _read_on_options_metrics(self, inputs: Dict, ticker_index: int):
        """Read overnight, options, and ATR from on_options_metrics section (rows 73-82)"""
        row = self.ON_OPTIONS_METRICS_BASE + (ticker_index - 1)
        
        # Overnight High/Low (columns E-F)
        inputs['d1_onh'] = self._read_cell(f'E{row}')
        inputs['d1_onl'] = self._read_cell(f'F{row}')
        
        # Options levels (columns G-P: op_01 through op_10)
        for i in range(1, 11):
            col = chr(ord('G') + (i - 1))  # G, H, I, J, K, L, M, N, O, P
            inputs[f'op_{i:02d}'] = self._read_cell(f'{col}{row}')
        
        # ATR values (columns Q-T)
        inputs['m5_atr'] = self._read_cell(f'Q{row}')
        inputs['m15_atr'] = self._read_cell(f'R{row}')
        inputs['h1_atr'] = self._read_cell(f'S{row}')
        inputs['d1_atr'] = self._read_cell(f'T{row}')

    def _read_camarilla_levels(self, inputs: Dict, ticker_index: int):
        """Read Camarilla levels from add_metrics section (rows 86-95)"""
        row = self.ADD_METRICS_BASE + (ticker_index - 1)
        
        # Daily Camarilla (columns E-J)
        inputs['d1_s6'] = self._read_cell(f'E{row}')
        inputs['d1_s4'] = self._read_cell(f'F{row}')
        inputs['d1_s3'] = self._read_cell(f'G{row}')
        inputs['d1_r3'] = self._read_cell(f'H{row}')
        inputs['d1_r4'] = self._read_cell(f'I{row}')
        inputs['d1_r6'] = self._read_cell(f'J{row}')
        
        # Weekly Camarilla (columns K-P)
        inputs['w1_s6'] = self._read_cell(f'K{row}')
        inputs['w1_s4'] = self._read_cell(f'L{row}')
        inputs['w1_s3'] = self._read_cell(f'M{row}')
        inputs['w1_r3'] = self._read_cell(f'N{row}')
        inputs['w1_r4'] = self._read_cell(f'O{row}')
        inputs['w1_r6'] = self._read_cell(f'P{row}')
        
        # Monthly Camarilla (columns Q-V)
        inputs['m1_s6'] = self._read_cell(f'Q{row}')
        inputs['m1_s4'] = self._read_cell(f'R{row}')
        inputs['m1_s3'] = self._read_cell(f'S{row}')
        inputs['m1_r3'] = self._read_cell(f'T{row}')
        inputs['m1_r4'] = self._read_cell(f'U{row}')
        inputs['m1_r6'] = self._read_cell(f'V{row}')

    def _read_cell(self, cell_ref: str) -> Optional[float]:
        """
        Read a single cell value as numeric, return None if empty or error
        
        Args:
            cell_ref: Cell reference like 'A1', 'B5', etc.
            
        Returns:
            Cell value as float, or None if empty/error
        """
        try:
            value = self.bar_data_sheet.range(cell_ref).value
            if value is None or value == '' or value == 0:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    def _read_cell_string(self, cell_ref: str) -> Optional[str]:
        """
        Read a single cell value as string, return None if empty
        
        Args:
            cell_ref: Cell reference like 'A1', 'B5', etc.
            
        Returns:
            Cell value as string, or None if empty
        """
        try:
            value = self.bar_data_sheet.range(cell_ref).value
            if value is None or value == '':
                return None
            return str(value).strip()
        except Exception:
            return None

    def validate_inputs(self, inputs: Dict) -> bool:
        """
        Validate that required fields are present in inputs
        
        Args:
            inputs: inputs dictionary from read_ticker_data()
            
        Returns:
            bool: True if all required fields present, False otherwise
        """
        # Core required fields
        required_fields = ['ticker', 'date', 'price', 'm15_atr']
        
        # Check for at least one HVN POC
        has_hvn = any(inputs.get(f'hvn_poc{i}') for i in range(1, 11))
        
        missing = [f for f in required_fields if inputs.get(f) is None]
        
        if missing:
            print(f"    ⚠ Missing required fields: {missing}")
            logger.warning(f"Missing required fields: {missing}")
            return False
        
        if not has_hvn:
            print(f"    ⚠ No HVN POCs found - Module 04 must run first")
            logger.warning("No HVN POCs found")
            return False
        
        return True

    def get_hvn_poc_count(self, inputs: Dict) -> int:
        """Count how many HVN POCs are present"""
        return sum(1 for i in range(1, 11) if inputs.get(f'hvn_poc{i}') is not None)
