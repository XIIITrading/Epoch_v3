"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Main Runner Script
================================================================================
Organization: XIII Trading LLC
Module Path: C:\XIIITradingSystems\Epoch\02_zone_system\07_setup_analysis
Version: 1.0
================================================================================

DESCRIPTION:
------------
This module analyzes filtered L2-L5 zones to identify trading setups.
It calculates bull/bear POC anchors, determines profit targets using
HVN POC cascade logic with 3R/4R thresholds, and generates primary/secondary
setups based on market direction.

OUTPUTS:
--------
1. zone_results worksheet: Columns N-S updated with setup data
2. Analysis worksheet: Primary setups (B31:K40), Secondary setups (M31:V40)

PREREQUISITES:
--------------
- Module 06 (Zone Results) must have completed successfully
- epoch_v1.xlsm must be open in Excel

EXECUTION:
----------
cd C:\XIIITradingSystems\Epoch
.\\venv\\Scripts\\Activate.ps1
python .\\02_zone_system\\07_setup_analysis\\setup_runner.py

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
from zone_results_reader import ZoneResultsReader
from bar_data_reader import BarDataReader
from market_overview_reader import MarketOverviewReader
from epoch_setup_analyzer import EpochSetupAnalyzer
from zone_results_updater import ZoneResultsUpdater
from analysis_writer import AnalysisWriter


def run():
    """
    Main workflow for Setup Analysis module.
    
    Pipeline:
    1. Connect to Excel workbook
    2. Read zones from zone_results worksheet
    3. Read HVN POCs from bar_data for target selection
    4. Read direction from market_overview for primary/secondary
    5. Run setup analysis (bull/bear POCs, targets, R:R)
    6. Update zone_results with setup columns N-S
    7. Write primary/secondary setups to Analysis worksheet
    8. Print summary
    """
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS")
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
        # STEP 2: Read zones from zone_results
        # ======================================================================
        print("\n[STEP 2] Reading zones from zone_results worksheet...")
        
        zone_reader = ZoneResultsReader(wb)
        df_zones = zone_reader.read_all_zones()
        
        if df_zones.empty:
            print("  ERROR: No zones found in zone_results worksheet")
            print("  Make sure Module 06 (Zone Results) has run successfully")
            return False
        
        print(f"  Loaded {len(df_zones)} zones")
        print(f"  Tickers: {zone_reader.get_unique_ticker_ids()}")
        
        # ======================================================================
        # STEP 3: Read HVN POCs from bar_data
        # ======================================================================
        print("\n[STEP 3] Reading HVN POCs from bar_data worksheet...")
        
        bar_reader = BarDataReader(wb)
        ticker_data = bar_reader.get_all_tickers_data()
        
        if not ticker_data:
            print("  ERROR: No HVN POC data found in bar_data worksheet")
            return False
        
        # ======================================================================
        # STEP 4: Read direction from market_overview
        # ======================================================================
        print("\n[STEP 4] Reading direction from market_overview worksheet...")
        
        mo_reader = MarketOverviewReader(wb)
        direction_data = mo_reader.get_all_directions()
        
        if not direction_data:
            print("  WARNING: No direction data found - using default")
        
        # ======================================================================
        # STEP 5: Run setup analysis
        # ======================================================================
        print("\n[STEP 5] Running setup analysis...")
        
        analyzer = EpochSetupAnalyzer()
        df_zones_updated, df_primary, df_secondary = analyzer.analyze_all_zones(
            df_zones, ticker_data, direction_data
        )
        
        # ======================================================================
        # STEP 6: Update zone_results with setup columns
        # ======================================================================
        print("\n[STEP 6] Updating zone_results worksheet (columns N-S)...")
        
        updater = ZoneResultsUpdater(wb)
        rows_updated = updater.update_setup_columns(df_zones_updated)
        
        # ======================================================================
        # STEP 7: Write to Analysis worksheet
        # ======================================================================
        print("\n[STEP 7] Writing to Analysis worksheet...")
        
        writer = AnalysisWriter(wb)
        primary_count, secondary_count = writer.write_setups(df_primary, df_secondary)
        
        # ======================================================================
        # STEP 8: Summary
        # ======================================================================
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("MODULE 07 COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"  Zones analyzed:          {len(df_zones)}")
        print(f"  Zone_results updated:    {rows_updated} rows (columns N-S)")
        print(f"  Primary setups:          {primary_count}")
        print(f"  Secondary setups:        {secondary_count}")
        print(f"  Runtime:                 {elapsed:.1f} seconds")
        print("=" * 70)
        
        # Detailed primary/secondary breakdown
        if not df_primary.empty:
            print("\nPRIMARY SETUPS (with trend):")
            print("-" * 60)
            for _, row in df_primary.iterrows():
                ticker = row.get('ticker', '')
                direction = row.get('direction', '')
                hvn_poc = row.get('hvn_poc', 0)
                target = row.get('target', 0)
                rr = row.get('r_r', 0)
                target_id = row.get('target_id', '')
                
                try:
                    print(f"  {ticker:<6} {direction:<6} POC: ${hvn_poc:.2f} → "
                          f"Target: ${target:.2f} ({target_id}) R:R {rr:.1f}")
                except (TypeError, ValueError):
                    print(f"  {ticker:<6} {direction:<6} (data formatting issue)")
        
        if not df_secondary.empty:
            print("\nSECONDARY SETUPS (counter-trend):")
            print("-" * 60)
            for _, row in df_secondary.iterrows():
                ticker = row.get('ticker', '')
                direction = row.get('direction', '')
                hvn_poc = row.get('hvn_poc', 0)
                target = row.get('target', 0)
                rr = row.get('r_r', 0)
                target_id = row.get('target_id', '')
                
                try:
                    print(f"  {ticker:<6} {direction:<6} POC: ${hvn_poc:.2f} → "
                          f"Target: ${target:.2f} ({target_id}) R:R {rr:.1f}")
                except (TypeError, ValueError):
                    print(f"  {ticker:<6} {direction:<6} (data formatting issue)")
        
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
