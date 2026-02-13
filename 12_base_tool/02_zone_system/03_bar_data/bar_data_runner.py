"""
Bar Data Runner
Epoch Trading System - XIII Trading LLC

Module 1: Bar Data Fetcher
Fetches and calculates all bar data metrics using existing calculation modules.

CRITICAL EPOCH DIFFERENCE FROM MERIDIAN:
- Reads tickers from market_overview worksheet -> ticker_structure (C36:C45)
- NOT from bar_data worksheet (C4:C13) as in Meridian
- No HVN calculation - that's handled by Module 2

Populates bar_data worksheet with:
- Monthly OHLC (current + prior)
- Weekly OHLC (current + prior)
- Daily OHLC (current + prior)
- Overnight session high/low
- Top 10 options levels by open interest
- ATR values (M5, M15, H1, D1)
- Camarilla pivot levels (D1, W1, M1)
"""

import xlwings as xw
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import sys
import json
import time
from pathlib import Path

# Add calculations folder to path
sys.path.append(str(Path(__file__).parent / 'calculations'))

# Import calculation modules
from m1_metrics import M1MetricsCalculator
from w1_metrics import W1MetricsCalculator
from d1_metrics import D1MetricsCalculator
from on_calculator import ONMetricsCalculator
from options_calculator import OptionsLevelsCalculator
from atr_calculator import calculate_m5_atr, calculate_m15_atr, calculate_h1_atr, calculate_daily_atr
from camarilla_calculator import CamarillaCalculator

# Import configuration
from config import (
    EXCEL_FILEPATH, BAR_DATA_WORKSHEET, MARKET_OVERVIEW_WORKSHEET,
    MO_TICKER_START_ROW, MO_TICKER_END_ROW, TICKER_COLUMN, DATE_COLUMN,
    ALT_TICKER_START_ROW, ALT_TICKER_END_ROW, STATUS_CELL, VERBOSE, API_DELAY
)

# Cell mapping file path
BAR_DATA_MAP_PATH = Path(__file__).parent / 'bar_data_map.json'


def load_bar_data_map() -> Dict:
    """Load the bar_data_map.json for cell mappings."""
    try:
        with open(BAR_DATA_MAP_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load bar_data_map.json: {e}")
        return {}


def get_cell_location(bar_data_map: Dict, field_name: str, ticker_num: int) -> Optional[str]:
    """
    Get cell location for a specific field and ticker number.
    
    Args:
        bar_data_map: Loaded bar_data_map.json
        field_name: Field name (e.g., 't1_m1_01', 't1_w1_01')
        ticker_num: Ticker number (1-10)
    
    Returns:
        Cell location (e.g., 'E17') or None
    """
    # Search through bar_data_map for matching field
    for section_name, entries in bar_data_map.items():
        for entry in entries:
            if entry.get('name') == field_name:
                return entry.get('location')
    
    return None


def connect_to_workbook():
    """Connect to Excel workbook."""
    try:
        wb = xw.Book(EXCEL_FILEPATH)
        if VERBOSE:
            print(f"✓ Connected to workbook: {EXCEL_FILEPATH}")
        return wb
    except Exception as e:
        print(f"✗ Failed to connect to workbook: {e}")
        raise


def read_ticker_date_list_from_market_overview(mo_ws) -> List[Tuple[int, str, str]]:
    """
    Read tickers and dates from market_overview -> ticker_structure section.
    Rows 36-45, columns C (ticker) and D (date).
    
    EPOCH SPECIFIC: This is the primary input source, unlike Meridian which reads from bar_data.
    
    Returns:
        List of tuples: [(ticker_num, ticker, date), ...]
        ticker_num is 1-10 corresponding to t1-t10
    """
    ticker_dates = []
    
    for row in range(MO_TICKER_START_ROW, MO_TICKER_END_ROW + 1):
        ticker_cell = f'{TICKER_COLUMN}{row}'
        date_cell = f'{DATE_COLUMN}{row}'
        
        ticker = mo_ws.range(ticker_cell).value
        date_val = mo_ws.range(date_cell).value
        
        # Skip empty cells
        if ticker is None or str(ticker).strip() == '':
            continue
        
        ticker = str(ticker).strip().upper()
        
        # Handle date formats
        if date_val is None:
            continue
        
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%m-%d-%y")
        else:
            date_str = str(date_val).strip()
        
        # Calculate ticker number (row 36 = t1, row 37 = t2, etc.)
        ticker_num = row - MO_TICKER_START_ROW + 1
        
        # Validate ticker
        if len(ticker) > 0 and len(ticker) <= 5:
            ticker_dates.append((ticker_num, ticker, date_str))
        else:
            print(f"⚠️  Invalid ticker in {ticker_cell}: {ticker}")
    
    return ticker_dates


def calculate_m1_metrics(ticker: str, date_str: str, calculator: M1MetricsCalculator) -> Dict:
    """Calculate monthly metrics."""
    try:
        metrics = calculator.calculate_metrics(ticker, date_str)
        return {
            'm1_01': metrics['current_month']['m1_01_open'],
            'm1_02': metrics['current_month']['m1_02_high'],
            'm1_03': metrics['current_month']['m1_03_low'],
            'm1_04': metrics['current_month']['m1_04_close'],
            'm1_po': metrics['prior_month']['m1_po_open'],
            'm1_ph': metrics['prior_month']['m1_ph_high'],
            'm1_pl': metrics['prior_month']['m1_pl_low'],
            'm1_pc': metrics['prior_month']['m1_pc_close']
        }
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  M1 calculation failed: {e}")
        return {}


def calculate_w1_metrics(ticker: str, date_str: str, calculator: W1MetricsCalculator) -> Dict:
    """Calculate weekly metrics."""
    try:
        metrics = calculator.calculate_metrics(ticker, date_str)
        return {
            'w1_01': metrics['current_week']['w1_01_open'],
            'w1_02': metrics['current_week']['w1_02_high'],
            'w1_03': metrics['current_week']['w1_03_low'],
            'w1_04': metrics['current_week']['w1_04_close'],
            'w1_po': metrics['prior_week']['w1_po_open'],
            'w1_ph': metrics['prior_week']['w1_ph_high'],
            'w1_pl': metrics['prior_week']['w1_pl_low'],
            'w1_pc': metrics['prior_week']['w1_pc_close']
        }
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  W1 calculation failed: {e}")
        return {}


def calculate_d1_metrics(ticker: str, date_str: str, calculator: D1MetricsCalculator) -> Dict:
    """Calculate daily metrics."""
    try:
        metrics = calculator.calculate_metrics(ticker, date_str)
        return {
            'd1_01': metrics['current_day']['d1_01_open'],
            'd1_02': metrics['current_day']['d1_02_high'],
            'd1_03': metrics['current_day']['d1_03_low'],
            'd1_04': metrics['current_day']['d1_04_close'],
            'd1_po': metrics['prior_day']['d1_po_open'],
            'd1_ph': metrics['prior_day']['d1_ph_high'],
            'd1_pl': metrics['prior_day']['d1_pl_low'],
            'd1_pc': metrics['prior_day']['d1_pc_close']
        }
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  D1 calculation failed: {e}")
        return {}


def calculate_on_metrics(ticker: str, date_str: str, calculator: ONMetricsCalculator) -> Dict:
    """Calculate overnight metrics."""
    try:
        metrics = calculator.calculate_on_metrics(ticker, date_str)
        return {
            'd1_onh': metrics['d1_onh'],
            'd1_onl': metrics['d1_onl']
        }
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  ON calculation failed: {e}")
        return {}


def calculate_options_levels(ticker: str, date_str: str, calculator: OptionsLevelsCalculator) -> Dict:
    """Calculate options levels."""
    try:
        # Convert date format from mm-dd-yy to YYYY-MM-DD
        date_obj = datetime.strptime(date_str, "%m-%d-%y")
        date_formatted = date_obj.strftime("%Y-%m-%d")
        
        levels = calculator.calculate_top_options_levels(ticker, date_formatted)
        return levels
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  Options calculation failed: {e}")
        return {}


def calculate_atr_metrics(ticker: str, date_str: str) -> Dict:
    """Calculate all ATR metrics."""
    try:
        if VERBOSE:
            print(f"      DEBUG: Received date_str='{date_str}' (type={type(date_str).__name__})")

        # Convert date format from mm-dd-yy to YYYY-MM-DD
        date_obj = datetime.strptime(date_str, "%m-%d-%y")
        date_formatted = date_obj.strftime("%Y-%m-%d")

        if VERBOSE:
            print(f"      DEBUG: Converted to date_formatted='{date_formatted}'")

        m5 = calculate_m5_atr(ticker, date_formatted)
        m15 = calculate_m15_atr(ticker, date_formatted)
        h1 = calculate_h1_atr(ticker, date_formatted)
        d1 = calculate_daily_atr(ticker, date_formatted)

        if VERBOSE:
            print(f"      ATR values: M5=${m5:.4f}, M15=${m15:.4f}, H1=${h1:.4f}, D1=${d1:.4f}")

        return {
            'm5_atr': m5,
            'm15_atr': m15,
            'h1_atr': h1,
            'd1_atr': d1
        }
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  ATR calculation failed: {e}")
            print(f"      ⚠️  Input was: ticker='{ticker}', date_str='{date_str}'")
        return {}


def calculate_camarilla_levels(ticker: str, date_str: str, calculator: CamarillaCalculator) -> Dict:
    """Calculate Camarilla pivot levels for all timeframes."""
    try:
        levels = calculator.calculate_metrics(ticker, date_str)
        if VERBOSE:
            # Debug: show what keys were returned
            d1_keys = [k for k in levels.keys() if k.startswith('d1_')]
            w1_keys = [k for k in levels.keys() if k.startswith('w1_')]
            m1_keys = [k for k in levels.keys() if k.startswith('m1_')]
            print(f"      Camarilla results: D1={len(d1_keys)} keys, W1={len(w1_keys)} keys, M1={len(m1_keys)} keys")
            if len(d1_keys) == 0:
                print(f"      ⚠️  No D1 Camarilla levels returned!")
        return levels
    except Exception as e:
        if VERBOSE:
            print(f"      ⚠️  Camarilla calculation failed: {e}")
        return {}


def write_metrics_to_excel(ws, bar_data_map: Dict, ticker_num: int, ticker: str, 
                           all_metrics: Dict):
    """
    Write all calculated metrics to Excel using bar_data_map.
    
    Args:
        ws: Excel worksheet (bar_data)
        bar_data_map: Cell mapping dictionary
        ticker_num: Ticker number (1-10, NOT row number)
        ticker: Ticker symbol
        all_metrics: Dictionary containing all calculated metrics
    """
    ticker_prefix = f"t{ticker_num}"
    
    # Write M1 metrics
    m1_fields = ['m1_01', 'm1_02', 'm1_03', 'm1_04', 'm1_po', 'm1_ph', 'm1_pl', 'm1_pc']
    for field in m1_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in all_metrics.get('m1', {}):
            value = all_metrics['m1'][field]
            if value is not None:
                ws.range(cell_loc).value = float(value)
    
    # Write W1 metrics
    w1_fields = ['w1_01', 'w1_02', 'w1_03', 'w1_04', 'w1_po', 'w1_ph', 'w1_pl', 'w1_pc']
    for field in w1_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in all_metrics.get('w1', {}):
            value = all_metrics['w1'][field]
            if value is not None:
                ws.range(cell_loc).value = float(value)
    
    # Write D1 metrics
    d1_fields = ['d1_01', 'd1_02', 'd1_03', 'd1_04', 'd1_po', 'd1_ph', 'd1_pl', 'd1_pc']
    for field in d1_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in all_metrics.get('d1', {}):
            value = all_metrics['d1'][field]
            if value is not None:
                ws.range(cell_loc).value = float(value)
    
    # Write ON metrics
    on_fields = ['d1_onh', 'd1_onl']
    for field in on_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in all_metrics.get('on', {}):
            value = all_metrics['on'][field]
            if value is not None:
                ws.range(cell_loc).value = float(value)
    
    # Write Options levels (op_01 through op_10)
    # Note: OptionsLevelsCalculator returns opt_01, opt_02, etc. but bar_data_map uses op_01, op_02
    options = all_metrics.get('options', {})
    for i in range(1, 11):
        opt_field = f"opt_{i:02d}"  # From calculator: opt_01, opt_02, etc.
        op_field = f"op_{i:02d}"    # In bar_data_map: op_01, op_02, etc.
        
        if opt_field in options:
            field_name = f"{ticker_prefix}_{op_field}"
            cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
            if cell_loc and options[opt_field] is not None:
                ws.range(cell_loc).value = float(options[opt_field])
    
    # Write ATR metrics
    atr_fields = ['m5_atr', 'm15_atr', 'h1_atr', 'd1_atr']
    atr_data = all_metrics.get('atr', {})
    for field in atr_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in atr_data:
            value = atr_data[field]
            if value is not None and value > 0:
                ws.range(cell_loc).value = float(value)
                if VERBOSE:
                    print(f"      Wrote {field}={value:.4f} to {cell_loc}")
            else:
                if VERBOSE:
                    print(f"      ⚠️  {field} value is None or 0, skipping")
        else:
            if VERBOSE:
                if not cell_loc:
                    print(f"      ⚠️  No cell location found for {field_name}")
                if field not in atr_data:
                    print(f"      ⚠️  {field} not in ATR results")
    
    # Write Camarilla levels
    camarilla = all_metrics.get('camarilla', {})
    camarilla_fields = ['d1_s6', 'd1_s4', 'd1_s3', 'd1_r3', 'd1_r4', 'd1_r6',
                        'w1_s6', 'w1_s4', 'w1_s3', 'w1_r3', 'w1_r4', 'w1_r6',
                        'm1_s6', 'm1_s4', 'm1_s3', 'm1_r3', 'm1_r4', 'm1_r6']
    for field in camarilla_fields:
        field_name = f"{ticker_prefix}_{field}"
        cell_loc = get_cell_location(bar_data_map, field_name, ticker_num)
        if cell_loc and field in camarilla:
            value = camarilla[field]
            if value is not None:
                ws.range(cell_loc).value = float(value)


def update_status(ws, status: str):
    """Update status cell."""
    ws.range(STATUS_CELL).value = status


def copy_ticker_structure_from_market_overview(mo_ws, bd_ws, ticker_dates: List[Tuple[int, str, str]]):
    """
    Copy ticker_structure data from market_overview to bar_data worksheet.
    
    Source: market_overview ticker_structure (rows 36-45, columns B-R)
    Destination: bar_data ticker_structure (rows 4-13, columns B-M)
    
    Column mapping (market_overview -> bar_data):
    - B (ticker_id) -> B (ticker_id) - will be reformatted as TICKER_DATE
    - C (ticker) -> C (ticker)
    - D (date) -> D (date)
    - E (price) -> E (price)
    - G (d1_s) -> F (d1_s)
    - H (d1_w) -> G (d1_w)
    - J (h4_s) -> H (h4_s)  [Note: market_overview has d4_s at J, but bar_data expects h4_s]
    - K (h4_w) -> I (h4_w)
    - M (h1_s) -> J (h1_s)
    - N (h1_w) -> K (h1_w)
    - P (m15_s) -> L (m15_s)
    - Q (m15_w) -> M (m15_w)
    """
    # Define the column mapping: (source_col in market_overview, dest_col in bar_data)
    column_mapping = [
        # ticker_id will be handled separately with TICKER_DATE format
        ('C', 'C'),   # ticker
        ('D', 'D'),   # date
        ('E', 'E'),   # price
        ('G', 'F'),   # d1_s
        ('H', 'G'),   # d1_w
        ('J', 'H'),   # h4_s (d4_s in MO)
        ('K', 'I'),   # h4_w
        ('M', 'J'),   # h1_s
        ('N', 'K'),   # h1_w
        ('P', 'L'),   # m15_s
        ('Q', 'M'),   # m15_w
    ]
    
    for ticker_num, ticker, date_str in ticker_dates:
        # Calculate source row (market_overview) and destination row (bar_data)
        mo_row = MO_TICKER_START_ROW + (ticker_num - 1)  # 36 + (ticker_num - 1)
        bd_row = 4 + (ticker_num - 1)  # 4 + (ticker_num - 1)
        
        # Create ticker_id in format TICKER_MMDDYY
        date_parts = date_str.replace('-', '')
        ticker_id = f"{ticker}_{date_parts}"
        
        # Write ticker_id to bar_data
        bd_ws.range(f'B{bd_row}').value = ticker_id
        
        # Copy mapped columns from market_overview to bar_data
        for src_col, dest_col in column_mapping:
            value = mo_ws.range(f'{src_col}{mo_row}').value
            if value is not None:
                bd_ws.range(f'{dest_col}{bd_row}').value = value
    
    if VERBOSE:
        print(f"✓ Copied ticker_structure from market_overview to bar_data for {len(ticker_dates)} tickers")


def copy_ticker_info_to_sections(ws, ticker_dates: List[Tuple[int, str, str]]):
    """
    Copy ticker info to the header rows of each section in bar_data worksheet.
    
    NOTE: This does NOT copy to ticker_structure (rows 4-13) - that's handled by
    copy_ticker_structure_from_market_overview() which copies the full structure.
    
    Epoch sections (from epoch_cell_map.yaml):
    - monthly_metrics: B17:D26
    - weekly_metrics: B31:D40
    - daily_metrics: B45:D54
    - time_hvn: B59:D68 (Module 2 - skip for now)
    - on_options_metrics: B73:D82
    - add_metrics: B86:D95
    """
    # Define section start rows (excluding ticker_structure which is handled separately)
    sections = {
        'monthly_metrics': 17,
        'weekly_metrics': 31,
        'daily_metrics': 45,
        'on_options_metrics': 73,
        'add_metrics': 86
    }
    
    for ticker_num, ticker, date_str in ticker_dates:
        # Create ticker_id in format TICKER_MMDDYY (e.g., NVDA_112825)
        date_parts = date_str.replace('-', '')
        ticker_id = f"{ticker}_{date_parts}"
        
        # For each ticker, write to all sections
        for section_name, base_row in sections.items():
            target_row = base_row + (ticker_num - 1)  # t1 = base_row, t2 = base_row + 1, etc.
            
            # Write ticker_id (column B), ticker (column C), date (column D)
            ws.range(f'B{target_row}').value = ticker_id
            ws.range(f'C{target_row}').value = ticker
            ws.range(f'D{target_row}').value = date_str
    
    if VERBOSE:
        print(f"✓ Copied ticker info to {len(sections)} sections for {len(ticker_dates)} tickers")


def run():
    """Main execution workflow."""
    print("=" * 60)
    print("EPOCH BAR DATA FETCHER v1.0")
    print("XIII Trading LLC - Epoch Trading System")
    print("Module 1: Bar Data")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Load bar_data_map
    print("\n📋 LOADING BAR DATA MAP")
    print("-" * 60)
    bar_data_map = load_bar_data_map()
    if not bar_data_map:
        print("✗ Could not load bar_data_map.json")
        return
    print(f"✓ Loaded {len(bar_data_map)} sections")
    
    # Connect to Excel
    print("\n📊 CONNECTING TO EXCEL")
    print("-" * 60)
    wb = connect_to_workbook()
    mo_ws = wb.sheets[MARKET_OVERVIEW_WORKSHEET]
    bd_ws = wb.sheets[BAR_DATA_WORKSHEET]
    
    # Update status
    update_status(bd_ws, "Fetching data...")
    
    # Read ticker and date list from market_overview (EPOCH SPECIFIC)
    print("\n📋 READING TICKER LIST FROM MARKET_OVERVIEW")
    print("-" * 60)
    print(f"   Reading from: {MARKET_OVERVIEW_WORKSHEET} -> ticker_structure")
    print(f"   Rows: {MO_TICKER_START_ROW} to {MO_TICKER_END_ROW}")
    
    ticker_dates = read_ticker_date_list_from_market_overview(mo_ws)
    
    if len(ticker_dates) == 0:
        print(f"⚠️  No tickers found in C{MO_TICKER_START_ROW}:C{MO_TICKER_END_ROW}")
        update_status(bd_ws, "No tickers")
        print("\n" + "=" * 60)
        print("✓ WORKFLOW COMPLETE (No tickers to process)")
        print("=" * 60)
        return
    
    print(f"Found {len(ticker_dates)} ticker(s) to process:")
    for ticker_num, ticker, date in ticker_dates:
        print(f"  - t{ticker_num}: {ticker} ({date})")
    
    # Initialize calculators
    print("\n🔧 INITIALIZING CALCULATORS")
    print("-" * 60)
    m1_calc = M1MetricsCalculator()
    w1_calc = W1MetricsCalculator()
    d1_calc = D1MetricsCalculator()
    on_calc = ONMetricsCalculator()
    opt_calc = OptionsLevelsCalculator()
    cam_calc = CamarillaCalculator()
    print("✓ All calculators initialized")
    print("   NOTE: HVN POC calculation is handled by Module 2")
    
    # Process tickers
    print("\n🔄 PROCESSING TICKERS")
    print("-" * 60)
    
    processed_count = 0
    failed_count = 0
    
    for ticker_num, ticker, date_str in ticker_dates:
        print(f"\n{ticker} (t{ticker_num}, Date: {date_str}):")
        
        try:
            all_metrics = {}
            
            # Calculate M1 metrics
            print(f"   Calculating M1 metrics...")
            all_metrics['m1'] = calculate_m1_metrics(ticker, date_str, m1_calc)
            
            # Calculate W1 metrics
            print(f"   Calculating W1 metrics...")
            all_metrics['w1'] = calculate_w1_metrics(ticker, date_str, w1_calc)
            
            # Calculate D1 metrics
            print(f"   Calculating D1 metrics...")
            all_metrics['d1'] = calculate_d1_metrics(ticker, date_str, d1_calc)
            
            # Calculate ON metrics
            print(f"   Calculating ON metrics...")
            all_metrics['on'] = calculate_on_metrics(ticker, date_str, on_calc)
            
            # Calculate Options levels
            print(f"   Calculating Options levels...")
            all_metrics['options'] = calculate_options_levels(ticker, date_str, opt_calc)
            
            # Calculate ATR metrics
            print(f"   Calculating ATR metrics...")
            all_metrics['atr'] = calculate_atr_metrics(ticker, date_str)
            
            # Calculate Camarilla levels
            print(f"   Calculating Camarilla levels...")
            all_metrics['camarilla'] = calculate_camarilla_levels(ticker, date_str, cam_calc)
            
            # Write to Excel
            print(f"   Writing to Excel...")
            write_metrics_to_excel(bd_ws, bar_data_map, ticker_num, ticker, all_metrics)
            
            print(f"   ✓ {ticker} completed")
            processed_count += 1
            
            # Add delay between tickers to avoid API rate limiting
            if API_DELAY > 0:
                time.sleep(API_DELAY)
            
        except Exception as e:
            print(f"   ⚠️  {ticker} failed: {e}")
            failed_count += 1
            continue
    
    # Copy ticker_structure from market_overview to bar_data
    print("\n📋 COPYING TICKER_STRUCTURE FROM MARKET_OVERVIEW")
    print("-" * 60)
    copy_ticker_structure_from_market_overview(mo_ws, bd_ws, ticker_dates)
    
    # Copy ticker info to other sections (monthly, weekly, daily, etc.)
    print("\n📋 COPYING TICKER INFO TO OTHER SECTIONS")
    print("-" * 60)
    copy_ticker_info_to_sections(bd_ws, ticker_dates)
    
    # Save workbook
    print("\n💾 SAVING WORKBOOK")
    print("-" * 60)
    wb.save()
    print("✓ Workbook saved")
    
    # Update final status
    if failed_count == 0:
        update_status(bd_ws, "Complete")
    else:
        update_status(bd_ws, f"Partial ({failed_count} failed)")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✓ EPOCH BAR DATA WORKFLOW COMPLETE")
    print(f"   Tickers processed: {processed_count}")
    print(f"   Tickers failed: {failed_count}")
    print(f"   Elapsed time: {elapsed:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        raise
