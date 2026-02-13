"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Main Runner Script
================================================================================
Organization: XIII Trading LLC
Module Path: C:\XIIITradingSystems\Epoch\02_zone_system\06_zone_results
Version: 1.0
================================================================================

DESCRIPTION:
------------
This module reads all zones from raw_zones worksheet, filters to L2-L5 only,
applies ATR-based proximity grouping, eliminates overlapping zones, and writes
the filtered results to zone_results worksheet.

PREREQUISITES:
--------------
- Module 05 (Raw Zones) must have completed successfully
- epoch_v1.xlsm must be open in Excel

EXECUTION:
----------
cd C:\XIIITradingSystems\Epoch
.\venv\Scripts\Activate.ps1
python .\02_zone_system\06_zone_results\zone_results_runner.py

================================================================================
"""

import sys
from datetime import datetime
from pathlib import Path

import xlwings as xw

# Add module path for imports
MODULE_PATH = Path(__file__).parent
sys.path.insert(0, str(MODULE_PATH))

from epoch_config import EXCEL_FILEPATH, VERBOSE
from raw_zones_reader import RawZonesReader
from bar_data_reader import BarDataReader
from zone_filter import ZoneFilter
from zone_results_writer import ZoneResultsWriter


def run():
    """
    Main workflow for Zone Results module.
    
    Pipeline:
    1. Connect to Excel workbook
    2. Read all zones from raw_zones worksheet
    3. Read price/ATR data from bar_data for all tickers
    4. Filter by rank (L2+ only)
    5. Add proximity grouping (ATR distance)
    6. Eliminate overlapping zones
    7. Write filtered zones to zone_results worksheet
    8. Print summary
    """
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    start_time = datetime.now()
    
    try:
        # ======================================================================
        # STEP 1: Connect to Excel
        # ======================================================================
        print("\n[STEP 1] Connecting to Excel workbook...")
        
        try:
            wb = xw.Book(EXCEL_FILEPATH)
            print(f"  Connected to: {EXCEL_FILEPATH}")
        except Exception as e:
            print(f"  ERROR: Could not connect to Excel workbook")
            print(f"  Make sure epoch_v1.xlsm is open in Excel")
            print(f"  Error: {e}")
            return False
        
        # ======================================================================
        # STEP 2: Read all zones from raw_zones
        # ======================================================================
        print("\n[STEP 2] Reading zones from raw_zones worksheet...")
        
        raw_zones_reader = RawZonesReader(wb)
        raw_zones_df = raw_zones_reader.read_all_zones()
        
        if raw_zones_df.empty:
            print("  ERROR: No zones found in raw_zones worksheet")
            print("  Make sure Module 05 (Raw Zones) has run successfully")
            return False
        
        print(f"  Loaded {len(raw_zones_df)} zones from raw_zones")
        
        # Show rank distribution
        rank_counts = raw_zones_reader.get_zone_count_by_rank()
        print(f"  Rank distribution: {rank_counts}")
        
        # ======================================================================
        # STEP 3: Read price/ATR data from bar_data
        # ======================================================================
        print("\n[STEP 3] Reading price/ATR data from bar_data worksheet...")
        
        bar_data_reader = BarDataReader(wb)
        price_atr_data = bar_data_reader.get_all_tickers_price_atr()
        
        if not price_atr_data:
            print("  ERROR: No price/ATR data found in bar_data worksheet")
            print("  Make sure Module 03 (Bar Data) has run successfully")
            return False
        
        # ======================================================================
        # STEP 4-6: Filter, Group, and Eliminate Overlaps
        # ======================================================================
        print("\n[STEP 4-6] Filtering zones...")
        
        zone_filter = ZoneFilter()
        filtered_zones_df = zone_filter.process_all(raw_zones_df, price_atr_data)
        
        if filtered_zones_df.empty:
            print("\n  WARNING: No zones remain after filtering")
            print("  This may indicate all zones are L1 or beyond 2 ATR from price")
        
        # ======================================================================
        # STEP 7: Write to zone_results worksheet
        # ======================================================================
        print("\n[STEP 7] Writing to zone_results worksheet...")
        
        writer = ZoneResultsWriter(wb)
        zones_written = writer.write_zones(filtered_zones_df)
        
        # ======================================================================
        # STEP 8: Summary
        # ======================================================================
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("MODULE 06 COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"  Input zones (raw_zones):      {len(raw_zones_df)}")
        print(f"  Output zones (zone_results):  {zones_written}")
        print(f"  Zones filtered out:           {len(raw_zones_df) - zones_written}")
        print(f"  Runtime:                      {elapsed:.1f} seconds")
        print("=" * 70)
        
        # Detailed breakdown
        if not filtered_zones_df.empty:
            print("\nDETAILED BREAKDOWN:")
            print("-" * 40)
            
            # By rank
            print("\nBy Rank:")
            for rank in ['L5', 'L4', 'L3', 'L2']:
                count = len(filtered_zones_df[filtered_zones_df['rank'] == rank])
                if count > 0:
                    pct = (count / zones_written) * 100
                    print(f"  {rank}: {count} ({pct:.1f}%)")
            
            # By proximity group
            print("\nBy Proximity Group:")
            for group in [1, 2]:
                count = len(filtered_zones_df[filtered_zones_df['proximity_group'] == group])
                if count > 0:
                    label = "≤1 ATR (immediate)" if group == 1 else "1-2 ATR (near-term)"
                    pct = (count / zones_written) * 100
                    print(f"  Group {group} ({label}): {count} ({pct:.1f}%)")
            
            # By ticker
            print("\nBy Ticker:")
            for ticker_id in filtered_zones_df['ticker_id'].unique():
                ticker_zones = filtered_zones_df[filtered_zones_df['ticker_id'] == ticker_id]
                count = len(ticker_zones)
                avg_score = ticker_zones['score'].mean()
                print(f"  {ticker_id}: {count} zones (avg score: {avg_score:.2f})")
            
            # Top zones
            print("\nTop 5 Zones by Score:")
            top_5 = filtered_zones_df.nlargest(5, 'score')
            for _, zone in top_5.iterrows():
                print(f"  {zone['ticker']:<6} {zone['zone_id']:<10} @ ${zone['hvn_poc']:.2f} "
                      f"- Score: {zone['score']:.2f} ({zone['rank']}) "
                      f"- ATR Dist: {zone['atr_distance']:.2f}")
        
        print("\n" + "=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Entry point for command line execution."""
    success = run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
