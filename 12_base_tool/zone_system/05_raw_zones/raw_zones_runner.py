# raw_zones_runner.py - Epoch Raw Zones Main Runner
# Orchestrates the complete raw zones calculation workflow
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
EPOCH RAW ZONES WORKFLOW:
1. Connect to Excel workbook (epoch_v1.xlsm)
2. Initialize readers (bar_data, market_overview)
3. Initialize aggregator
4. For each ticker slot (1-10):
   a. Check if ticker exists (validate inputs)
   b. Read all bar_data metrics
   c. Read direction + market structure from market_overview
   d. Create EpochCalculator and calculate zones
   e. Add results to aggregator
5. Get all results from aggregator
6. Write to raw_zones worksheet
7. Print summary statistics

PREREQUISITES:
- Module 03 (Bar Data) must have completed successfully
- Module 04 (HVN Identifier) must have completed successfully
- epoch_v1.xlsm must be open in Excel
"""

import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main workflow for Epoch Raw Zones calculation"""
    
    print("\n" + "=" * 70)
    print("EPOCH TRADING SYSTEM - MODULE 05: RAW ZONES")
    print("Organization: XIII Trading LLC")
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Import modules
    try:
        import xlwings as xw
        import epoch_config as config
        from bar_data_reader import EpochBarDataReader
        from market_overview_reader import EpochMarketOverviewReader
        from epoch_calc_engine import EpochCalculator
        from results_aggregator import EpochResultsAggregator
        from raw_zones_writer import EpochRawZonesWriter
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("Make sure all module files are in the same directory.")
        return 1
    
    # Step 1: Connect to Excel
    print("\n[Step 1] Connecting to Excel...")
    try:
        # Try to connect to existing workbook
        wb = xw.Book(config.EXCEL_FILEPATH)
        print(f"  ✓ Connected to: {config.EXCEL_FILEPATH}")
    except Exception as e:
        print(f"  ❌ Failed to connect to Excel: {e}")
        print(f"  Make sure {config.EXCEL_FILEPATH} is open in Excel.")
        return 1
    
    # Create a simple connection wrapper
    class ExcelConnection:
        def __init__(self, workbook):
            self.wb = workbook
        def get_sheet(self, name):
            return self.wb.sheets[name]
    
    conn = ExcelConnection(wb)
    
    # Step 2: Initialize readers
    print("\n[Step 2] Initializing data readers...")
    try:
        bar_data_reader = EpochBarDataReader(conn)
        market_overview_reader = EpochMarketOverviewReader(conn)
        print("  ✓ Bar Data Reader initialized")
        print("  ✓ Market Overview Reader initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize readers: {e}")
        return 1
    
    # Step 3: Initialize aggregator
    print("\n[Step 3] Initializing results aggregator...")
    aggregator = EpochResultsAggregator()
    print("  ✓ Results Aggregator initialized")
    
    # Step 4: Process each ticker slot (1-10)
    print("\n[Step 4] Processing tickers...")
    print("-" * 60)
    
    tickers_processed = 0
    tickers_skipped = 0
    
    for ticker_index in range(1, 11):
        print(f"\n--- Ticker Slot {ticker_index} ---")
        
        try:
            # Read bar_data for this ticker
            inputs = bar_data_reader.read_ticker_data(ticker_index)
            
            # Validate inputs
            if not bar_data_reader.validate_inputs(inputs):
                print(f"  ⚠ Skipping ticker slot {ticker_index} - validation failed")
                tickers_skipped += 1
                continue
            
            # Get ticker info
            ticker_id = inputs.get('ticker_id', f'T{ticker_index}')
            ticker = inputs.get('ticker', 'UNKNOWN')
            date = inputs.get('date', '')
            price = inputs.get('price', 0)
            
            # Convert date if needed
            if hasattr(date, 'strftime'):
                date = date.strftime('%m-%d-%y')
            else:
                date = str(date)
            
            # Read market overview for direction and market structure
            market_data = market_overview_reader.get_ticker_data(ticker_index)
            direction = market_data.get('direction', 'N/A')
            
            # Create calculator and calculate zones
            calculator = EpochCalculator(inputs, market_data, config)
            zones_df = calculator.calculate_all()
            
            # Add results to aggregator
            if not zones_df.empty:
                aggregator.add_ticker_results(
                    ticker_id=ticker_id,
                    ticker=ticker,
                    date=date,
                    price=price,
                    direction=direction,
                    zones_df=zones_df
                )
                tickers_processed += 1
                hvn_count = bar_data_reader.get_hvn_poc_count(inputs)
                print(f"  ✓ Processed {ticker} ({hvn_count} HVN POCs → {len(zones_df)} zones)")
            else:
                print(f"  ⚠ No zones generated for {ticker}")
                tickers_skipped += 1
                
        except Exception as e:
            print(f"  ❌ Error processing ticker slot {ticker_index}: {e}")
            logger.exception(f"Error processing ticker {ticker_index}")
            tickers_skipped += 1
            continue
    
    print("\n" + "-" * 60)
    print(f"Tickers processed: {tickers_processed}")
    print(f"Tickers skipped: {tickers_skipped}")
    
    # Step 5: Get all results
    print("\n[Step 5] Aggregating results...")
    all_zones = aggregator.get_all_results()
    
    if all_zones.empty:
        print("  ⚠ No zones to write - check that Modules 03 and 04 have run.")
        return 1
    
    # Step 6: Write to raw_zones worksheet
    print("\n[Step 6] Writing to raw_zones worksheet...")
    try:
        writer = EpochRawZonesWriter(conn)
        writer.write_all_zones(all_zones)
    except Exception as e:
        print(f"  ❌ Failed to write zones: {e}")
        logger.exception("Write error")
        return 1
    
    # Step 7: Print summary statistics
    print("\n[Step 7] Summary Statistics")
    print("=" * 60)
    stats = aggregator.get_summary_stats()
    print(f"  Tickers Processed: {stats['total_tickers']}")
    print(f"  Total Zones: {stats['total_zones']}")
    print(f"  Average Score: {stats['avg_score']}")
    print(f"  Max Score: {stats['max_score']}")
    print(f"  Min Score: {stats['min_score']}")
    print(f"\n  Rank Distribution:")
    print(f"    L5 (Best):  {stats['l5_count']}")
    print(f"    L4:         {stats['l4_count']}")
    print(f"    L3:         {stats['l3_count']}")
    print(f"    L2:         {stats['l2_count']}")
    print(f"    L1 (Worst): {stats['l1_count']}")
    
    print("\n" + "=" * 70)
    print("✓ EPOCH RAW ZONES MODULE COMPLETE")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
