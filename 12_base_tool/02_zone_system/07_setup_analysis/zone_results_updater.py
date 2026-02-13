"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Zone Results Updater
================================================================================
Organization: XIII Trading LLC
Purpose: Update zone_results worksheet columns O-T with setup analysis data
================================================================================

VERSION 1.1 CHANGES:
- Setup columns shifted from N-S to O-T to accommodate tier column at N
- Tier column (N) is written by Module 06, not modified here
================================================================================
"""

import pandas as pd
from typing import List
import xlwings as xw

from epoch_config import (
    WORKSHEET_ZONE_RESULTS,
    ZONE_RESULTS_SETUP_COLUMNS,
    ZONE_RESULTS_DATA_START_ROW,
    VERBOSE
)


class ZoneResultsUpdater:
    """
    Updates zone_results worksheet with setup analysis columns.
    
    V1.1: Columns O-T (shifted from N-S):
    - O: EPCH_Bull (X if this is the bull POC for ticker)
    - P: EPCH_Bear (X if this is the bear POC for ticker)
    - Q: EPCH_Bull Price (bull zone hvn_poc value)
    - R: EPCH_Bear Price (bear zone hvn_poc value)
    - S: EPCH_Bull Target (bull target price)
    - T: EPCH_Bear Target (bear target price)
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_ZONE_RESULTS]
        
    def update_setup_columns(self, df_zones: pd.DataFrame) -> int:
        """
        Update columns O-T with setup analysis data.
        
        V1.1: Columns shifted to O-T to accommodate tier at column N.
        
        Args:
            df_zones: DataFrame with zone data including setup columns
                      (epch_bull, epch_bear, epch_bull_price, etc.)
                      
        Returns:
            Number of rows updated
        """
        if VERBOSE:
            print(f"\n  Updating setup columns (O-T) in '{WORKSHEET_ZONE_RESULTS}'...")
        
        if df_zones.empty:
            if VERBOSE:
                print("  No zones to update")
            return 0
        
        # Clear existing data in columns O-T
        self._clear_setup_columns()
        
        # Prepare data for writing
        output_data = self._prepare_output_data(df_zones)
        
        # V1.1: Write data starting at row 2, column O (shifted from N)
        if output_data:
            start_cell = f"O{ZONE_RESULTS_DATA_START_ROW}"
            self.sheet.range(start_cell).value = output_data
            
            if VERBOSE:
                print(f"  Successfully updated {len(output_data)} rows")
        
        return len(output_data) if output_data else 0
    
    def _prepare_output_data(self, df_zones: pd.DataFrame) -> List[List]:
        """
        Prepare setup column data for Excel output.
        
        V1.1: Output columns (O-T):
        O: epch_bull
        P: epch_bear
        Q: epch_bull_price
        R: epch_bear_price
        S: epch_bull_target
        T: epch_bear_target
        
        Args:
            df_zones: DataFrame with setup analysis data
            
        Returns:
            List of lists (rows) for Excel output
        """
        output_rows = []
        
        column_order = [
            'epch_bull', 'epch_bear', 
            'epch_bull_price', 'epch_bear_price',
            'epch_bull_target', 'epch_bear_target'
        ]
        
        for _, row in df_zones.iterrows():
            output_row = []
            
            for col in column_order:
                value = row.get(col, '')
                
                # Format based on column type
                if col in ['epch_bull', 'epch_bear']:
                    # String columns (X or empty)
                    output_row.append(str(value) if pd.notna(value) and value != '' else '')
                    
                elif col in ['epch_bull_price', 'epch_bear_price', 
                             'epch_bull_target', 'epch_bear_target']:
                    # Numeric columns
                    if pd.notna(value) and value != '':
                        try:
                            output_row.append(round(float(value), 2))
                        except (ValueError, TypeError):
                            output_row.append('')
                    else:
                        output_row.append('')
                else:
                    output_row.append('')
            
            output_rows.append(output_row)
        
        return output_rows
    
    def _clear_setup_columns(self) -> None:
        """Clear columns O-T data, preserving headers and other columns."""
        try:
            last_row = self._find_last_data_row()
            
            if last_row >= ZONE_RESULTS_DATA_START_ROW:
                # V1.1: Clear columns O-T (shifted from N-S)
                clear_range = f"O{ZONE_RESULTS_DATA_START_ROW}:T{last_row}"
                self.sheet.range(clear_range).value = None
                
                if VERBOSE:
                    print(f"  Cleared setup columns (O{ZONE_RESULTS_DATA_START_ROW}:T{last_row})")
                    
        except Exception as e:
            if VERBOSE:
                print(f"  Note: Could not clear setup columns ({e})")
    
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


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ZONE RESULTS UPDATER V1.1 - STANDALONE TEST")
    print("=" * 70)
    print("\nThis module requires integration with Excel.")
    print("Run setup_runner.py for full test.")