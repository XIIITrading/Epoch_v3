"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Zone Results Reader
================================================================================
Organization: XIII Trading LLC
Purpose: Read filtered zones from zone_results worksheet
================================================================================

VERSION 1.1 CHANGES:
- Added tier column (N) to input reading
- Now reads columns A-N instead of A-M
================================================================================
"""

import pandas as pd
from typing import Dict, List, Optional
import xlwings as xw

from epoch_config import (
    WORKSHEET_ZONE_RESULTS,
    ZONE_RESULTS_INPUT_COLUMNS,
    ZONE_RESULTS_DATA_START_ROW,
    TIER_DESCRIPTIONS,
    VERBOSE
)


class ZoneResultsReader:
    """
    Reads filtered zones from the zone_results worksheet.
    
    This is the output from Module 06 that will be enhanced with
    setup analysis data. V1.1 now includes tier column.
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_ZONE_RESULTS]
        
    def read_all_zones(self) -> pd.DataFrame:
        """
        Read all zones from zone_results worksheet into DataFrame.
        
        V1.1: Now includes tier column (N).
        
        Returns:
            DataFrame with columns: ticker_id, ticker, date, price, direction,
            zone_id, hvn_poc, zone_high, zone_low, overlaps, score, rank, 
            confluences, tier
        """
        if VERBOSE:
            print(f"  Reading zones from '{WORKSHEET_ZONE_RESULTS}' worksheet...")
        
        # Find the last row with data
        last_row = self._find_last_data_row()
        
        if last_row < ZONE_RESULTS_DATA_START_ROW:
            if VERBOSE:
                print("  WARNING: No data found in zone_results worksheet")
            return pd.DataFrame()
        
        # V1.1: Column order now includes tier
        col_order = ['ticker_id', 'ticker', 'date', 'price', 'direction',
                     'zone_id', 'hvn_poc', 'zone_high', 'zone_low', 
                     'overlaps', 'score', 'rank', 'confluences', 'tier']
        
        # V1.1: Read data range (columns A-N instead of A-M)
        data_range = f"A{ZONE_RESULTS_DATA_START_ROW}:N{last_row}"
        raw_data = self.sheet.range(data_range).value
        
        # Handle single row case
        if last_row == ZONE_RESULTS_DATA_START_ROW:
            raw_data = [raw_data]
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data, columns=col_order)
        
        # Clean up data types
        df = self._clean_data_types(df)
        
        # Filter out empty rows
        df = df.dropna(subset=['ticker_id'])
        
        if VERBOSE:
            print(f"  Read {len(df)} zones from zone_results worksheet")
            self._print_tier_summary(df)
        
        return df
    
    def _find_last_data_row(self) -> int:
        """Find the last row with data in column A."""
        row = ZONE_RESULTS_DATA_START_ROW
        max_empty = 0
        last_valid_row = ZONE_RESULTS_DATA_START_ROW - 1
        
        while max_empty < 5:
            cell_value = self.sheet.range(f"A{row}").value
            if cell_value is not None and str(cell_value).strip() != '':
                last_valid_row = row
                max_empty = 0
            else:
                max_empty += 1
            row += 1
            
            if row > 500:
                break
        
        return last_valid_row
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types for the DataFrame."""
        # Numeric columns
        numeric_cols = ['price', 'hvn_poc', 'zone_high', 'zone_low', 
                        'overlaps', 'score']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # String columns (now includes tier)
        string_cols = ['ticker_id', 'ticker', 'date', 'direction', 
                       'zone_id', 'rank', 'confluences', 'tier']
        
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('None', '')
        
        return df
    
    def _print_tier_summary(self, df: pd.DataFrame) -> None:
        """Print tier distribution summary."""
        if 'tier' not in df.columns or df.empty:
            return
        
        tier_counts = df['tier'].value_counts()
        print(f"  Tier distribution: ", end="")
        tier_strs = []
        for tier in ['T3', 'T2', 'T1']:
            count = tier_counts.get(tier, 0)
            if count > 0:
                tier_strs.append(f"{tier}:{count}")
        print(', '.join(tier_strs))
    
    def get_zones_by_ticker(self) -> Dict[str, pd.DataFrame]:
        """
        Get zones grouped by ticker_id.
        
        Returns:
            Dictionary mapping ticker_id to DataFrame of zones
        """
        df = self.read_all_zones()
        if df.empty:
            return {}
        
        return {ticker_id: group for ticker_id, group in df.groupby('ticker_id')}
    
    def get_unique_ticker_ids(self) -> List[str]:
        """Get list of unique ticker_ids in zone_results."""
        df = self.read_all_zones()
        if df.empty:
            return []
        return df['ticker_id'].unique().tolist()
    
    def get_tier_counts(self) -> Dict[str, int]:
        """
        Get count of zones by tier.
        
        Returns:
            Dictionary mapping tier to count (e.g., {'T3': 10, 'T2': 15, 'T1': 20})
        """
        df = self.read_all_zones()
        if df.empty or 'tier' not in df.columns:
            return {}
        return df['tier'].value_counts().to_dict()


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    from epoch_config import EXCEL_FILEPATH
    
    print("=" * 70)
    print("ZONE RESULTS READER V1.1 - STANDALONE TEST")
    print("=" * 70)
    
    try:
        print("\nConnecting to Excel workbook...")
        wb = xw.Book(EXCEL_FILEPATH)
        
        reader = ZoneResultsReader(wb)
        df = reader.read_all_zones()
        
        if not df.empty:
            print(f"\nTotal zones: {len(df)}")
            print(f"Unique tickers: {reader.get_unique_ticker_ids()}")
            print(f"Tier counts: {reader.get_tier_counts()}")
            print(f"\nSample data (first 5 rows):")
            print(df[['ticker_id', 'zone_id', 'hvn_poc', 'rank', 'tier', 'score']].head())
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()