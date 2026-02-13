"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Raw Zones Reader
================================================================================
Organization: XIII Trading LLC
Purpose: Read all zones from raw_zones worksheet into DataFrame
================================================================================
"""

import pandas as pd
from typing import List, Dict, Any, Optional
import xlwings as xw

from epoch_config import (
    WORKSHEET_RAW_ZONES,
    RAW_ZONES_COLUMNS,
    RAW_ZONES_DATA_START_ROW,
    VERBOSE
)


class RawZonesReader:
    """
    Reads all zones from the raw_zones worksheet.
    
    The raw_zones worksheet is populated by Module 05 and contains all L1-L5
    ranked zones for all tickers.
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_RAW_ZONES]
        
    def read_all_zones(self) -> pd.DataFrame:
        """
        Read all zones from raw_zones worksheet into DataFrame.
        
        Returns:
            DataFrame with columns: ticker_id, ticker, date, price, direction,
            zone_id, hvn_poc, zone_high, zone_low, overlaps, score, rank, confluences
        """
        if VERBOSE:
            print(f"  Reading zones from '{WORKSHEET_RAW_ZONES}' worksheet...")
        
        # Find the last row with data
        last_row = self._find_last_data_row()
        
        if last_row < RAW_ZONES_DATA_START_ROW:
            if VERBOSE:
                print("  WARNING: No data found in raw_zones worksheet")
            return pd.DataFrame()
        
        # Build column letter list in order
        col_order = ['ticker_id', 'ticker', 'date', 'price', 'direction',
                     'zone_id', 'hvn_poc', 'zone_high', 'zone_low', 
                     'overlaps', 'score', 'rank', 'confluences']
        
        # Read data range
        data_range = f"A{RAW_ZONES_DATA_START_ROW}:M{last_row}"
        raw_data = self.sheet.range(data_range).value
        
        # Handle single row case (xlwings returns list instead of list of lists)
        if last_row == RAW_ZONES_DATA_START_ROW:
            raw_data = [raw_data]
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data, columns=col_order)
        
        # Clean up data types
        df = self._clean_data_types(df)
        
        # Filter out any empty rows
        df = df.dropna(subset=['ticker_id'])
        
        if VERBOSE:
            print(f"  Read {len(df)} zones from raw_zones worksheet")
        
        return df
    
    def _find_last_data_row(self) -> int:
        """
        Find the last row with data in column A (ticker_id).
        
        Returns:
            Row number of last data row, or 1 if no data
        """
        # Start from row 2 and search down
        col_a = self.sheet.range("A:A")
        last_cell = col_a.end('down')
        
        # If the cell is empty or row 1, check if there's any data
        if last_cell.row == 1:
            # Check if row 2 has data
            if self.sheet.range("A2").value is not None:
                return 2
            return 1
        
        # xlwings end('down') from column range goes to last used cell
        # But we need to be more careful - let's iterate to find actual last row
        row = RAW_ZONES_DATA_START_ROW
        max_empty = 0
        last_valid_row = 1
        
        while max_empty < 5:  # Stop after 5 consecutive empty rows
            cell_value = self.sheet.range(f"A{row}").value
            if cell_value is not None and str(cell_value).strip() != '':
                last_valid_row = row
                max_empty = 0
            else:
                max_empty += 1
            row += 1
            
            # Safety limit
            if row > 1000:
                break
        
        return last_valid_row
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and convert data types for the DataFrame.
        
        Args:
            df: Raw DataFrame from Excel
            
        Returns:
            DataFrame with proper data types
        """
        # Numeric columns
        numeric_cols = ['price', 'hvn_poc', 'zone_high', 'zone_low', 
                        'overlaps', 'score']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # String columns
        string_cols = ['ticker_id', 'ticker', 'date', 'direction', 
                       'zone_id', 'rank', 'confluences']
        
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('None', '')
        
        return df
    
    def get_unique_tickers(self) -> List[str]:
        """
        Get list of unique ticker_ids in raw_zones.
        
        Returns:
            List of unique ticker_id strings
        """
        df = self.read_all_zones()
        if df.empty:
            return []
        return df['ticker_id'].unique().tolist()
    
    def get_zones_by_ticker(self, ticker_id: str) -> pd.DataFrame:
        """
        Get all zones for a specific ticker.
        
        Args:
            ticker_id: Ticker ID to filter by (e.g., "AMZN_112825")
            
        Returns:
            DataFrame with zones for that ticker only
        """
        df = self.read_all_zones()
        return df[df['ticker_id'] == ticker_id]
    
    def get_zone_count_by_rank(self) -> Dict[str, int]:
        """
        Get count of zones by rank.
        
        Returns:
            Dictionary mapping rank to count (e.g., {'L1': 46, 'L2': 35, ...})
        """
        df = self.read_all_zones()
        if df.empty:
            return {}
        return df['rank'].value_counts().to_dict()


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    from epoch_config import EXCEL_FILEPATH
    
    print("=" * 70)
    print("RAW ZONES READER - STANDALONE TEST")
    print("=" * 70)
    
    try:
        # Connect to Excel
        print("\nConnecting to Excel workbook...")
        wb = xw.Book(EXCEL_FILEPATH)
        
        # Create reader
        reader = RawZonesReader(wb)
        
        # Read all zones
        print("\nReading all zones...")
        df = reader.read_all_zones()
        
        if not df.empty:
            print(f"\nTotal zones read: {len(df)}")
            print(f"\nUnique tickers: {reader.get_unique_tickers()}")
            print(f"\nZones by rank: {reader.get_zone_count_by_rank()}")
            print(f"\nSample data (first 5 rows):")
            print(df.head())
        else:
            print("No zones found in raw_zones worksheet")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
