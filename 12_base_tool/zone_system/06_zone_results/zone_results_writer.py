"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Zone Results Writer
================================================================================
Organization: XIII Trading LLC
Purpose: Write filtered zones to zone_results worksheet
================================================================================

VERSION 1.1 CHANGES:
- Added tier column (N) to output
- Columns shifted: A-M zone data, N tier, O-T reserved for Module 07
================================================================================
"""

import pandas as pd
from typing import List, Optional
import xlwings as xw

from epoch_config import (
    WORKSHEET_ZONE_RESULTS,
    ZONE_RESULTS_COLUMNS,
    ZONE_RESULTS_DATA_START_ROW,
    VERBOSE
)


class ZoneResultsWriter:
    """
    Writes filtered zones to the zone_results worksheet.
    
    Output format (V1.1):
    - Columns A-M: Zone data (same as raw_zones)
    - Column N: Tier (T1/T2/T3 quality classification)
    - Columns O-T: Reserved for Module 07 (Setup Analysis)
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_ZONE_RESULTS]
        
    def write_zones(self, zones_df: pd.DataFrame) -> int:
        """
        Write filtered zones to zone_results worksheet.
        
        Data is written starting at row 2 (row 1 contains headers).
        Existing data is cleared before writing.
        
        Args:
            zones_df: DataFrame with filtered zones including tier column
            
        Returns:
            Number of zones written
        """
        if VERBOSE:
            print(f"\n  Writing {len(zones_df)} zones to '{WORKSHEET_ZONE_RESULTS}'...")
        
        # Clear existing data (preserve headers in row 1)
        self._clear_data_only()
        
        if zones_df.empty:
            if VERBOSE:
                print("  No zones to write")
            return 0
        
        # Prepare data for writing
        output_data = self._prepare_output_data(zones_df)
        
        # Write data starting at row 2
        if output_data:
            start_cell = f"A{ZONE_RESULTS_DATA_START_ROW}"
            
            # Convert list of rows to write
            self.sheet.range(start_cell).value = output_data
            
            if VERBOSE:
                print(f"  Successfully wrote {len(output_data)} zones")
                self._print_tier_summary(zones_df)
        
        return len(output_data) if output_data else 0
    
    def _prepare_output_data(self, zones_df: pd.DataFrame) -> List[List]:
        """
        Prepare DataFrame data for Excel output.
        
        Output columns (A-N):
        A: ticker_id
        B: ticker
        C: date
        D: price
        E: direction
        F: zone_id
        G: hvn_poc
        H: zone_high
        I: zone_low
        J: overlaps
        K: score
        L: rank
        M: confluences
        N: tier (NEW in V1.1)
        
        Note: Columns O-T are reserved for Module 07 (Setup Analysis)
        ATR distance and proximity group are used internally for filtering
        but are NOT written to the worksheet.
        
        Args:
            zones_df: Filtered zones DataFrame
            
        Returns:
            List of lists (rows) for Excel output
        """
        output_rows = []
        
        # Define column order (A-N including tier)
        column_order = [
            'ticker_id', 'ticker', 'date', 'price', 'direction',
            'zone_id', 'hvn_poc', 'zone_high', 'zone_low',
            'overlaps', 'score', 'rank', 'confluences', 'tier'
        ]
        
        for _, row in zones_df.iterrows():
            output_row = []
            
            for col in column_order:
                value = row.get(col, '')
                
                # Format specific columns
                if col in ['hvn_poc', 'zone_high', 'zone_low', 'price']:
                    # Keep as float for Excel
                    if pd.notna(value):
                        output_row.append(float(value))
                    else:
                        output_row.append('')
                        
                elif col == 'score':
                    # Round score to 2 decimal places
                    if pd.notna(value):
                        output_row.append(round(float(value), 2))
                    else:
                        output_row.append('')
                        
                elif col == 'overlaps':
                    # Keep as integer
                    if pd.notna(value):
                        output_row.append(int(value))
                    else:
                        output_row.append('')
                        
                else:
                    # String columns (including tier)
                    if pd.notna(value):
                        output_row.append(str(value))
                    else:
                        output_row.append('')
            
            output_rows.append(output_row)
        
        return output_rows
    
    def _clear_data_only(self) -> None:
        """
        Clear existing data rows in columns A-N only.
        Preserves headers (row 1) and columns O-T (Module 07 data).
        """
        try:
            # Find the last row with data
            last_row = self._find_last_data_row()
            
            if last_row >= ZONE_RESULTS_DATA_START_ROW:
                # Clear columns A-N only (preserve O-T for Module 07)
                clear_range = f"A{ZONE_RESULTS_DATA_START_ROW}:N{last_row}"
                self.sheet.range(clear_range).value = None
                
                if VERBOSE:
                    print(f"  Cleared existing data (A{ZONE_RESULTS_DATA_START_ROW}:N{last_row})")
                    
        except Exception as e:
            # If clearing fails, just overwrite (data will be replaced anyway)
            if VERBOSE:
                print(f"  Note: Could not clear existing data ({e})")
    
    def _find_last_data_row(self) -> int:
        """
        Find the last row with data in column A.
        
        Returns:
            Row number of last data row
        """
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
            
            # Safety limit
            if row > 500:
                break
        
        return last_valid_row
    
    def _print_tier_summary(self, zones_df: pd.DataFrame) -> None:
        """Print tier distribution summary."""
        if 'tier' not in zones_df.columns:
            return
        
        tier_counts = zones_df['tier'].value_counts()
        print(f"\n  Tier Distribution in Output:")
        for tier in ['T3', 'T2', 'T1']:
            count = tier_counts.get(tier, 0)
            if count > 0:
                pct = (count / len(zones_df)) * 100
                print(f"    {tier}: {count} zones ({pct:.1f}%)")
    
    def write_headers(self) -> None:
        """
        Write column headers to row 1 (columns A-N).
        
        Note: Call this only if headers don't already exist.
        Columns O-T headers should already exist for Module 07.
        """
        headers = [
            'Ticker_ID', 'Ticker', 'Date', 'Price', 'Direction',
            'Zone_ID', 'HVN_POC', 'Zone_High', 'Zone_Low',
            'Overlaps', 'Score', 'Rank', 'Confluences', 'Tier'
        ]
        
        self.sheet.range("A1").value = headers
        
        if VERBOSE:
            print(f"  Wrote headers to row 1 (A-N)")
    
    def get_zone_count(self) -> int:
        """
        Get count of zones currently in zone_results worksheet.
        
        Returns:
            Number of data rows
        """
        last_row = self._find_last_data_row()
        if last_row >= ZONE_RESULTS_DATA_START_ROW:
            return last_row - ZONE_RESULTS_DATA_START_ROW + 1
        return 0


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ZONE RESULTS WRITER V1.1 - STANDALONE TEST")
    print("=" * 70)
    
    # This test requires the actual Excel workbook
    print("\nThis test requires epoch_v1.xlsm to be open in Excel.")
    print("Run zone_results_runner.py for full integration test.")