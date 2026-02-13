"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Analysis Writer
================================================================================
Organization: XIII Trading LLC
Purpose: Write primary and secondary setups to Analysis worksheet
================================================================================

VERSION 1.1 CHANGES:
- Added Tier column to output
- Primary section: B31:L40 (11 columns including tier)
- Secondary section: N31:X40 (11 columns including tier)
- Headers updated to include "Tier"
================================================================================
"""

import pandas as pd
from typing import List
import xlwings as xw

from epoch_config import (
    WORKSHEET_ANALYSIS,
    ANALYSIS_PRIMARY_HEADER_ROW,
    ANALYSIS_PRIMARY_START_ROW,
    ANALYSIS_PRIMARY_END_ROW,
    ANALYSIS_SECONDARY_START_ROW,
    ANALYSIS_SECONDARY_END_ROW,
    TIER_DESCRIPTIONS,
    VERBOSE
)


class AnalysisWriter:
    """
    Writes primary and secondary setups to the Analysis worksheet.
    
    Layout (V1.1 - includes Tier):
    - Primary section: B31:L40 (10 rows max)
    - Secondary section: N31:X40 (10 rows max)
    
    Headers at row 30.
    """
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize with Excel workbook connection.
        
        Args:
            workbook: xlwings Book object connected to epoch_v1.xlsm
        """
        self.workbook = workbook
        self.sheet = workbook.sheets[WORKSHEET_ANALYSIS]
        
    def write_setups(self, df_primary: pd.DataFrame, 
                     df_secondary: pd.DataFrame) -> tuple:
        """
        Write both primary and secondary setups to Analysis worksheet.
        
        Args:
            df_primary: DataFrame with primary setups
            df_secondary: DataFrame with secondary setups
            
        Returns:
            Tuple of (primary_count, secondary_count)
        """
        print("\n" + "=" * 70)
        print("WRITING TO ANALYSIS SHEET (V1.1 - WITH TIER)")
        print("=" * 70)
        
        # Clear existing data
        self._clear_sections()
        
        # Write headers
        self._write_headers()
        
        # Write primary section
        primary_count = self._write_primary(df_primary)
        
        # Write secondary section
        secondary_count = self._write_secondary(df_secondary)
        
        # Print tier summary
        self._print_tier_summary(df_primary, df_secondary)
        
        print(f"\n✓ Analysis sheet updated")
        
        return primary_count, secondary_count
    
    def _write_headers(self) -> None:
        """Write headers for both sections (V1.1 - includes Tier)."""
        # V1.1: Added Tier column after Zone Low
        headers = ['Ticker', 'Direction', 'Ticker ID', 'Zone ID', 'HVN POC',
                   'Zone High', 'Zone Low', 'Tier', 'Target ID', 'Target', 'R:R']
        
        # Primary headers at B30
        self.sheet.range('B30').value = headers
        
        # Secondary headers at N30
        self.sheet.range('N30').value = headers
    
    def _write_primary(self, df_primary: pd.DataFrame) -> int:
        """
        Write primary setups to B31:L40.
        
        V1.1: Now includes Tier column (column I).
        
        Args:
            df_primary: DataFrame with primary setups
            
        Returns:
            Number of setups written
        """
        print("\n  Writing Primary section (B31:L40)...")
        
        if df_primary.empty:
            print("    No primary setups to write")
            return 0
        
        # Limit to 10 rows
        df_out = df_primary.head(10)
        
        # Prepare data
        output_data = self._prepare_output_data(df_out)
        
        # Write to Excel
        if output_data:
            self.sheet.range('B31').value = output_data
            print(f"    ✓ Wrote {len(output_data)} primary setups")
            
            # Show tier breakdown
            if 'tier' in df_out.columns:
                tier_counts = df_out['tier'].value_counts().to_dict()
                tier_str = ', '.join([f"{t}:{c}" for t, c in sorted(tier_counts.items())])
                print(f"      Tiers: {tier_str}")
        
        return len(output_data) if output_data else 0
    
    def _write_secondary(self, df_secondary: pd.DataFrame) -> int:
        """
        Write secondary setups to N31:X40.
        
        V1.1: Now includes Tier column (column U).
        
        Args:
            df_secondary: DataFrame with secondary setups
            
        Returns:
            Number of setups written
        """
        print("\n  Writing Secondary section (N31:X40)...")
        
        if df_secondary.empty:
            print("    No secondary setups to write")
            return 0
        
        # Limit to 10 rows
        df_out = df_secondary.head(10)
        
        # Prepare data
        output_data = self._prepare_output_data(df_out)
        
        # Write to Excel
        if output_data:
            self.sheet.range('N31').value = output_data
            print(f"    ✓ Wrote {len(output_data)} secondary setups")
            
            # Show tier breakdown
            if 'tier' in df_out.columns:
                tier_counts = df_out['tier'].value_counts().to_dict()
                tier_str = ', '.join([f"{t}:{c}" for t, c in sorted(tier_counts.items())])
                print(f"      Tiers: {tier_str}")
        
        return len(output_data) if output_data else 0
    
    def _prepare_output_data(self, df: pd.DataFrame) -> List[List]:
        """
        Prepare DataFrame for Excel output.
        
        V1.1 Column order: Ticker, Direction, Ticker ID, Zone ID, HVN POC,
                           Zone High, Zone Low, Tier, Target ID, Target, R:R
        """
        output_rows = []
        
        # V1.1: Added tier to column order
        column_order = ['ticker', 'direction', 'ticker_id', 'zone_id',
                        'hvn_poc', 'zone_high', 'zone_low', 'tier',
                        'target_id', 'target', 'r_r']
        
        for _, row in df.iterrows():
            output_row = []
            
            for col in column_order:
                value = row.get(col, '')
                
                # Format based on column type
                if col in ['hvn_poc', 'zone_high', 'zone_low', 'target']:
                    # Price columns - round to 2 decimal places
                    if pd.notna(value) and value != '':
                        try:
                            output_row.append(round(float(value), 2))
                        except (ValueError, TypeError):
                            output_row.append('')
                    else:
                        output_row.append('')
                        
                elif col == 'r_r':
                    # R:R ratio - round to 2 decimal places
                    if pd.notna(value) and value != '':
                        try:
                            output_row.append(round(float(value), 2))
                        except (ValueError, TypeError):
                            output_row.append('')
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
    
    def _clear_sections(self) -> None:
        """Clear both primary and secondary sections (V1.1 - expanded ranges)."""
        print("\n  Clearing ranges...")
        
        try:
            # V1.1: Clear primary section (B31:L40) - expanded for tier column
            self.sheet.range('B31:L40').clear_contents()
            
            # V1.1: Clear secondary section (N31:X40) - expanded for tier column
            self.sheet.range('N31:X40').clear_contents()
            
            if VERBOSE:
                print("    Cleared B31:L40 and N31:X40")
                
        except Exception as e:
            if VERBOSE:
                print(f"    Note: Could not clear sections ({e})")
    
    def _print_tier_summary(self, df_primary: pd.DataFrame, df_secondary: pd.DataFrame) -> None:
        """Print combined tier summary for both sections."""
        print("\n  Tier Quality Summary:")
        
        all_tiers = {'T1': 0, 'T2': 0, 'T3': 0}
        
        if not df_primary.empty and 'tier' in df_primary.columns:
            for tier in df_primary['tier']:
                if tier in all_tiers:
                    all_tiers[tier] += 1
        
        if not df_secondary.empty and 'tier' in df_secondary.columns:
            for tier in df_secondary['tier']:
                if tier in all_tiers:
                    all_tiers[tier] += 1
        
        total = sum(all_tiers.values())
        if total > 0:
            for tier in ['T3', 'T2', 'T1']:
                count = all_tiers[tier]
                if count > 0:
                    desc = TIER_DESCRIPTIONS.get(tier, '')
                    pct = (count / total) * 100
                    print(f"    {tier} ({desc}): {count} setups ({pct:.1f}%)")


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ANALYSIS WRITER V1.1 - STANDALONE TEST")
    print("=" * 70)
    print("\nThis module requires integration with Excel.")
    print("Run setup_runner.py for full test.")