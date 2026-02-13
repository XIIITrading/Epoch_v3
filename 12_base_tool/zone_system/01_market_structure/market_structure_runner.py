"""
Market Structure Runner - Epoch Market Structure Module
Epoch Trading System v1 - XIII Trading LLC

Main execution script for SPY/QQQ/DIA market structure analysis.
Fetches data, calculates structure, writes results to Excel.
"""

import xlwings as xw
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import epoch_market_structure_config as config
from polygon_data_fetcher import PolygonDataFetcher
from market_structure_calculator import MarketStructureCalculator


def connect_to_workbook():
    """
    Connect to Excel workbook.
    
    Returns:
        xlwings workbook object
    """
    try:
        wb = xw.Book(config.EXCEL_FILEPATH)
        if config.VERBOSE:
            print(f"✓ Connected to workbook: {config.EXCEL_FILEPATH}")
        return wb
    except Exception as e:
        print(f"✗ Failed to connect to workbook: {e}")
        raise


def fetch_ticker_data(ticker: str, fetcher: PolygonDataFetcher) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Fetch OHLC data for all timeframes.
    
    Args:
        ticker: Stock symbol (SPY, QQQ, DIA)
        fetcher: PolygonDataFetcher instance
    
    Returns:
        Dictionary: {'D1': df, 'H4': df, 'H1': df, 'M15': df}
        Returns None if any timeframe fails
    """
    data = {}
    
    for timeframe in ['D1', 'H4', 'H1', 'M15']:
        if config.VERBOSE:
            print(f"   Fetching {timeframe} data... ", end='')
        
        df = fetcher.fetch_bars_for_structure(ticker, timeframe)
        
        if df is not None:
            data[timeframe] = df
            if config.VERBOSE:
                print(f"✓ {len(df)} bars")
        else:
            if config.VERBOSE:
                print(f"✗ Failed")
            return None
    
    return data


def fetch_scan_price_data(ticker: str, fetcher: PolygonDataFetcher) -> Optional[pd.DataFrame]:
    """
    Fetch 1-minute data for most recent scan price.
    This includes pre-market and extended hours.
    
    Args:
        ticker: Stock symbol
        fetcher: PolygonDataFetcher instance
    
    Returns:
        DataFrame with M1 data or None if failed
    """
    if config.VERBOSE:
        print(f"   Fetching M1 data for scan price... ", end='')
    
    df = fetcher.fetch_bars_for_structure(ticker, 'M1')
    
    if df is not None:
        if config.VERBOSE:
            print(f"✓ {len(df)} bars (last: {df['timestamp'].iloc[-1]})")
    else:
        if config.VERBOSE:
            print(f"⚠️  Failed (will use D1 as fallback)")
    
    return df


def calculate_all_structures(ticker: str, data: Dict, calculator: MarketStructureCalculator) -> Dict[str, Dict]:
    """
    Calculate market structure for all timeframes.
    
    Args:
        ticker: Stock symbol
        data: Dictionary of DataFrames
        calculator: MarketStructureCalculator instance
    
    Returns:
        Dictionary: {
            'D1': {'direction_label': 'BULL', 'strong_level': 580.50, ...},
            'H4': {...},
            'H1': {...},
            'M15': {...}
        }
    """
    results = {}
    
    if config.VERBOSE:
        print(f"   Calculating structures...")
    
    for timeframe, df in data.items():
        result = calculator.calculate(df)
        results[timeframe] = result
        
        if config.VERBOSE:
            direction = result['direction_label']
            strong = result['strong_level']
            weak = result['weak_level']
            
            strong_str = f"{strong:.2f}" if strong is not None else "NULL"
            weak_str = f"{weak:.2f}" if weak is not None else "NULL"
            
            print(f"     {timeframe}: {direction} (Strong: {strong_str}, Weak: {weak_str})")
    
    return results


def get_scan_price(df_m1: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Get last close price from 1-minute data (most recent bar).
    This includes pre-market and extended hours data.
    
    Args:
        df_m1: DataFrame with M1 data
    
    Returns:
        Last close price (float)
    """
    if df_m1 is None or df_m1.empty:
        return None
    
    return df_m1['close'].iloc[-1]


def write_ticker_results(ws, ticker: str, scan_price: float, 
                         results: Dict[str, Dict], composite: str):
    """
    Write all results for one ticker to its row.
    
    Args:
        ws: xlwings worksheet
        ticker: Ticker symbol (SPY, QQQ, DIA)
        scan_price: Last close price
        results: Dict of timeframe results
        composite: Weighted direction string
    """
    row_num = config.get_ticker_row(ticker)
    
    # Ticker ID (Column B) - format: SPY_112525
    ticker_id = config.format_ticker_id(ticker)
    ws.range(f'B{row_num}').value = ticker_id
    
    # Ticker (Column C)
    ws.range(f'C{row_num}').value = ticker
    
    # Date (Column D)
    ws.range(f'D{row_num}').value = datetime.now()
    
    # Scan Price (Column E)
    if scan_price is not None:
        ws.range(f'E{row_num}').value = scan_price
    else:
        ws.range(f'E{row_num}').value = config.NULL_VALUE
    
    # D1 Results (Columns F, G, H)
    d1 = results.get('D1', {})
    ws.range(f'F{row_num}').value = config.MARKET_STRUCTURE_VALUES.get(
        d1.get('direction_label', 'ERROR'), 'ERROR')
    ws.range(f'G{row_num}').value = d1.get('strong_level')
    ws.range(f'H{row_num}').value = d1.get('weak_level')
    
    # H4 Results (Columns I, J, K)
    h4 = results.get('H4', {})
    ws.range(f'I{row_num}').value = config.MARKET_STRUCTURE_VALUES.get(
        h4.get('direction_label', 'ERROR'), 'ERROR')
    ws.range(f'J{row_num}').value = h4.get('strong_level')
    ws.range(f'K{row_num}').value = h4.get('weak_level')
    
    # H1 Results (Columns L, M, N)
    h1 = results.get('H1', {})
    ws.range(f'L{row_num}').value = config.MARKET_STRUCTURE_VALUES.get(
        h1.get('direction_label', 'ERROR'), 'ERROR')
    ws.range(f'M{row_num}').value = h1.get('strong_level')
    ws.range(f'N{row_num}').value = h1.get('weak_level')
    
    # M15 Results (Columns O, P, Q)
    m15 = results.get('M15', {})
    ws.range(f'O{row_num}').value = config.MARKET_STRUCTURE_VALUES.get(
        m15.get('direction_label', 'ERROR'), 'ERROR')
    ws.range(f'P{row_num}').value = m15.get('strong_level')
    ws.range(f'Q{row_num}').value = m15.get('weak_level')
    
    # Composite (Column R)
    ws.range(f'R{row_num}').value = composite


def run():
    """
    Main execution workflow.
    """
    print("=" * 60)
    print("EPOCH MARKET STRUCTURE MODULE v1.0")
    print("XIII Trading LLC - Epoch System")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Connect to Excel workbook
    print("\n📊 CONNECTING TO EXCEL")
    print("-" * 60)
    wb = connect_to_workbook()
    ws = wb.sheets[config.WORKSHEET_NAME]
    
    # Initialize data fetcher and calculator
    print("\n📊 INITIALIZING COMPONENTS")
    print("-" * 60)
    fetcher = PolygonDataFetcher()
    calculator = MarketStructureCalculator()
    print("✓ Data fetcher initialized")
    print("✓ Structure calculator initialized")
    
    # Process fixed tickers
    print("\n📊 PROCESSING MARKET TICKERS")
    print("-" * 60)
    print(f"Tickers to process: {', '.join(config.TICKER_ORDER)}")
    
    processed_count = 0
    skipped_count = 0
    
    for ticker in config.TICKER_ORDER:
        row_num = config.get_ticker_row(ticker)
        print(f"\n{ticker} (Row {row_num}):")
        
        try:
            # Fetch data for all timeframes
            data = fetch_ticker_data(ticker, fetcher)
            
            if data is None:
                print(f"   ⚠️  {ticker} failed: Could not fetch data")
                skipped_count += 1
                continue
            
            # Calculate structures
            results = calculate_all_structures(ticker, data, calculator)
            
            # Calculate composite direction
            composite = config.calculate_weighted_direction(results)
            if config.VERBOSE:
                print(f"   Composite: {composite}")
            
            # Get scan price from M1 data (most recent 1-minute bar)
            m1_data = fetch_scan_price_data(ticker, fetcher)
            if m1_data is not None:
                scan_price = get_scan_price(m1_data)
            else:
                # Fallback to D1 if M1 fetch fails
                scan_price = get_scan_price(data['D1'])
            
            if config.VERBOSE:
                scan_price_str = f"{scan_price:.2f}" if scan_price is not None else "NULL"
                print(f"   Scan Price: {scan_price_str}")
            
            # Write results to Excel
            write_ticker_results(ws, ticker, scan_price, results, composite)
            
            print(f"   ✓ {ticker} completed")
            processed_count += 1
            
        except Exception as e:
            print(f"   ⚠️  {ticker} failed: {e}")
            skipped_count += 1
            continue
    
    # Save workbook
    print("\n💾 SAVING WORKBOOK")
    print("-" * 60)
    wb.save()
    print("✓ Workbook saved")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✓ WORKFLOW COMPLETE")
    print(f"   Tickers processed: {processed_count}")
    print(f"   Tickers skipped: {skipped_count}")
    print(f"   Elapsed time: {elapsed:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        raise