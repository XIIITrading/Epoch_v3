# hvn_runner.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier\
# Purpose: Orchestrate HVN POC calculation for all tickers

"""
HVN Runner - Orchestration Script for Epoch HVN Identifier

UPDATED: Now reads start_date from market_overview S36:S45 instead of bar_data E59:E68

Workflow:
1. Connect to Excel workbook (must be open)
2. Read ticker list from market_overview -> ticker_structure (C36:C45)
3. Read epoch start_dates from market_overview -> ticker_structure (S36:S45)
4. For each ticker with a valid start_date:
   a. Read ATR from bar_data on_options_metrics section (column T)
   b. Call EpochHVNIdentifier.analyze()
   c. Write 10 POCs to bar_data time_hvn section (columns F-O)
   d. Write analysis date to bar_data time_hvn section (column D)
   e. Copy start_date to bar_data time_hvn section (column E) for reference
5. Print summary

Input Sources:
- Ticker: market_overview C36:C45
- Start Date: market_overview S36:S45
- ATR: bar_data T73:T82 (on_options_metrics section)

Output Destination:
- bar_data time_hvn section (rows 59-68)
  - Date: Column D (most recent data date)
  - Start Date: Column E (copied from market_overview for reference)
  - HVN POCs 1-10: Columns F-O
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import (
        EXCEL_FILEPATH,
        BAR_DATA_WORKSHEET,
        MARKET_OVERVIEW_WORKSHEET,
        VERBOSE
    )
except ImportError:
    EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
    BAR_DATA_WORKSHEET = 'bar_data'
    MARKET_OVERVIEW_WORKSHEET = 'market_overview'
    VERBOSE = True


# =============================================================================
# CELL MAP LOADER
# =============================================================================

def load_cell_map() -> Dict:
    """Load cell mapping from JSON file"""
    cell_map_path = Path(__file__).parent / 'hvn_cell_map.json'
    
    if not cell_map_path.exists():
        raise FileNotFoundError(f"Cell map not found: {cell_map_path}")
    
    with open(cell_map_path, 'r') as f:
        return json.load(f)


# =============================================================================
# EXCEL INTERFACE
# =============================================================================

class ExcelInterface:
    """Handle all Excel read/write operations via xlwings"""
    
    def __init__(self, filepath: str):
        """
        Initialize Excel interface.
        
        Args:
            filepath: Path to Excel workbook
        """
        import xlwings as xw
        
        self.filepath = filepath
        
        # Connect to open workbook
        try:
            self.wb = xw.Book(filepath)
            self.bar_data_ws = self.wb.sheets[BAR_DATA_WORKSHEET]
            self.market_overview_ws = self.wb.sheets[MARKET_OVERVIEW_WORKSHEET]
            logger.info(f"Connected to {filepath}")
            logger.info(f"  - bar_data worksheet: OK")
            logger.info(f"  - market_overview worksheet: OK")
        except Exception as e:
            raise ConnectionError(f"Could not connect to Excel: {e}\n"
                                  f"Make sure {filepath} is open in Excel.")
    
    def read_cell(self, worksheet, cell: str) -> any:
        """Read value from a cell in specified worksheet"""
        return worksheet.range(cell).value
    
    def write_cell(self, worksheet, cell: str, value: any):
        """Write value to a cell in specified worksheet"""
        worksheet.range(cell).value = value
    
    def read_ticker_inputs(self, cell_map: Dict) -> List[Dict]:
        """
        Read tickers and start_dates from market_overview worksheet.
        
        NEW: Reads from market_overview S36:S45 for start_dates
        
        Returns list of dicts with:
        - index: Ticker position (1-10)
        - ticker: Stock symbol (from market_overview C36:C45)
        - start_date: User-entered epoch start date (from market_overview S36:S45)
        - atr_cell: Cell reference for ATR value (bar_data T73:T82)
        - output_section: Cell mapping for output (bar_data time_hvn)
        """
        mo_inputs = cell_map['market_overview_inputs']
        time_hvn_map = cell_map['time_hvn']
        atr_map = cell_map['on_options_metrics']
        
        ticker_inputs = []
        
        for i in range(1, 11):
            key = f't{i}'
            
            if key not in mo_inputs:
                continue
            
            mo_section = mo_inputs[key]
            
            # Read ticker from market_overview
            ticker = self.read_cell(self.market_overview_ws, mo_section['ticker'])
            
            # Skip if ticker is empty
            if not ticker or str(ticker).strip() == '':
                continue
            
            ticker = str(ticker).upper().strip()
            
            # Read start_date from market_overview (NEW SOURCE: S36:S45)
            start_date = self.read_cell(self.market_overview_ws, mo_section['start_date'])
            
            # Check if start_date is valid
            if start_date is None or str(start_date).strip() == '':
                logger.warning(f"Ticker {ticker} (t{i}) has no start_date in {mo_section['start_date']} - SKIPPING")
                continue
            
            # Convert date to string format if it's a datetime
            if isinstance(start_date, datetime):
                start_date_str = start_date.strftime('%Y-%m-%d')
            else:
                # Try to parse as string
                try:
                    parsed = datetime.strptime(str(start_date), '%Y-%m-%d')
                    start_date_str = parsed.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        # Try mm/dd/yyyy format
                        parsed = datetime.strptime(str(start_date), '%m/%d/%Y')
                        start_date_str = parsed.strftime('%Y-%m-%d')
                    except ValueError:
                        try:
                            # Try mm-dd-yy format
                            parsed = datetime.strptime(str(start_date), '%m-%d-%y')
                            start_date_str = parsed.strftime('%Y-%m-%d')
                        except ValueError:
                            logger.warning(f"Ticker {ticker} has invalid start_date format: {start_date} - SKIPPING")
                            continue
            
            # Get ATR cell reference from bar_data on_options_metrics
            atr_cell = atr_map[key]['d1_atr'] if key in atr_map else None
            
            # Get output section from bar_data time_hvn
            output_section = time_hvn_map[key] if key in time_hvn_map else None
            
            ticker_inputs.append({
                'index': i,
                'ticker': ticker,
                'start_date': start_date_str,
                'start_date_source': mo_section['start_date'],  # For logging
                'atr_cell': atr_cell,
                'output_section': output_section
            })
            
            logger.info(f"Found ticker: {ticker} with start_date: {start_date_str} (from {mo_section['start_date']})")
        
        return ticker_inputs
    
    def read_atr(self, cell: str) -> Optional[float]:
        """Read ATR value from bar_data worksheet"""
        if cell is None:
            return None
        
        value = self.read_cell(self.bar_data_ws, cell)
        
        if value is None or value == '' or value == 0:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def write_results(self, section: Dict, ticker: str, result: Dict, start_date: str, end_date: str):
        """
        Write HVN POC results to bar_data worksheet.
        
        Args:
            section: Cell mapping for this ticker row (bar_data time_hvn)
            ticker: Stock symbol (e.g., "SPY")
            result: Dictionary with hvn_poc1 through hvn_poc10
            start_date: Epoch start date (to copy to bar_data for reference)
            end_date: Most recent data date
        """
        # Format ticker_id as TICKER_MMDDYY (e.g., SPY_121225)
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            date_suffix = end_date_obj.strftime('%m%d%y')
        except ValueError:
            date_suffix = datetime.now().strftime('%m%d%y')
        ticker_id = f"{ticker}_{date_suffix}"
        
        # Write ticker_id (column B)
        self.write_cell(self.bar_data_ws, section['ticker_id'], ticker_id)
        
        # Write ticker (column C)
        self.write_cell(self.bar_data_ws, section['ticker'], ticker)
        
        # Write date (column D - end of epoch)
        self.write_cell(self.bar_data_ws, section['date'], end_date)
        
        # Write start_date to bar_data for reference display (column E)
        self.write_cell(self.bar_data_ws, section['start_date'], start_date)
        
        # Write POCs (columns F-O)
        for i in range(1, 11):
            poc_key = f'hvn_poc{i}'
            cell = section.get(poc_key)
            
            if cell:
                value = result.get(poc_key, 0.0)
                self.write_cell(self.bar_data_ws, cell, value if value > 0 else '')
        
        logger.info(f"Wrote results for {ticker_id} to bar_data time_hvn section")


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run():
    """Main execution workflow"""
    
    print("\n" + "=" * 70)
    print("EPOCH HVN IDENTIFIER")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Start date source: market_overview S36:S45")
    print(f"Output destination: bar_data time_hvn (rows 59-68)")
    print("=" * 70)
    
    start_time = datetime.now()
    
    # Load cell map
    try:
        cell_map = load_cell_map()
        logger.info("Loaded cell map")
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # Connect to Excel
    try:
        excel = ExcelInterface(EXCEL_FILEPATH)
    except ConnectionError as e:
        logger.error(str(e))
        return
    
    # Read ticker inputs from market_overview
    ticker_inputs = excel.read_ticker_inputs(cell_map)
    
    if not ticker_inputs:
        logger.warning("No valid tickers found with start_dates")
        print("\nNo tickers to process. Make sure:")
        print("  1. Tickers are entered in market_overview column C (rows 36-45)")
        print("  2. Start dates are entered in market_overview column S (rows 36-45)")
        return
    
    print(f"\nFound {len(ticker_inputs)} ticker(s) to process")
    
    # Import the identifier from calculations folder
    from calculations.epoch_hvn_identifier import EpochHVNIdentifier
    
    # Initialize identifier
    try:
        identifier = EpochHVNIdentifier()
    except ValueError as e:
        logger.error(f"Could not initialize identifier: {e}")
        return
    
    # Process each ticker
    results_summary = []
    
    for ticker_input in ticker_inputs:
        ticker = ticker_input['ticker']
        start_date = ticker_input['start_date']
        output_section = ticker_input['output_section']
        
        print(f"\n{'-'*50}")
        print(f"Processing: {ticker}")
        print(f"Epoch: {start_date} to today")
        print(f"Start date from: market_overview {ticker_input['start_date_source']}")
        
        # Read ATR from bar_data
        atr_value = excel.read_atr(ticker_input['atr_cell'])
        if atr_value:
            print(f"ATR from bar_data: ${atr_value:.2f}")
        else:
            print("ATR: Will calculate from data")
        
        try:
            # Run analysis
            result = identifier.analyze(
                ticker=ticker,
                start_date=start_date,
                end_date=None,  # Current date
                atr_value=atr_value
            )
            
            # Convert to dict for Excel writing
            result_dict = result.to_dict()
            
            # Write results to bar_data
            excel.write_results(output_section, ticker, result_dict, start_date, result.end_date)
            
            # Track summary
            results_summary.append({
                'ticker': ticker,
                'status': 'SUCCESS',
                'pocs_found': len(result.pocs),
                'bars': result.bars_analyzed
            })
            
            print(f"✓ Success: {len(result.pocs)} POCs found")
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            results_summary.append({
                'ticker': ticker,
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"✗ Failed: {e}")
    
    # Print summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    success_count = sum(1 for r in results_summary if r['status'] == 'SUCCESS')
    fail_count = sum(1 for r in results_summary if r['status'] == 'FAILED')
    
    print(f"Processed: {len(results_summary)} tickers")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Runtime: {elapsed:.1f} seconds")
    
    print("\nDetails:")
    for r in results_summary:
        if r['status'] == 'SUCCESS':
            print(f"  ✓ {r['ticker']}: {r['pocs_found']} POCs ({r['bars']:,} bars)")
        else:
            print(f"  ✗ {r['ticker']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("HVN IDENTIFIER COMPLETE")
    print("=" * 70)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run()