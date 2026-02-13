# post_market_analysis.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\
# Purpose: Standalone script to generate post-market PDF report for all tickers

"""
Post-Market Analysis Report Generator

Automates the Streamlit workflow:
1. Connects to Excel workbook (must be open)
2. Reads all ticker data from Modules 01-07
3. Fetches H1 candles and epoch VbP from Polygon API
4. Generates visualization charts for each ticker
5. Compiles all charts into a single landscape-oriented PDF

Output: post_market_report_YYYY-MM-DD.pdf in the module directory

Usage:
    cd C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization
    python post_market_analysis.py

Requirements:
    - epoch_v1.xlsm must be OPEN in Excel
    - Modules 01-07 must have been run to populate data
    - Valid Polygon API key in credentials.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# Add module directory to path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from config.visualization_config import (
    COLORS, CANDLE_BAR_COUNT, CANDLE_TIMEFRAME, VBP_TIMEFRAME,
    WORKBOOK_PATH, DPI, FIGURE_WIDTH, FIGURE_HEIGHT
)
from data_readers.excel_reader import EpochExcelReader
from data_readers.polygon_fetcher import PolygonDataFetcher
from charts.chart_builder import VisualizationChartBuilder


# =============================================================================
# CONFIGURATION
# =============================================================================

SESSION_TYPE = 'postmarket'
OUTPUT_DIR = MODULE_DIR  # Output PDF to module directory


# =============================================================================
# MAIN REPORT GENERATOR
# =============================================================================

def generate_report():
    """
    Generate post-market PDF report for all tickers.
    
    Returns:
        Path to generated PDF file, or None if failed
    """
    print("=" * 70)
    print("EPOCH TRADING SYSTEM - POST-MARKET ANALYSIS REPORT")
    print("XIII Trading LLC")
    print("=" * 70)
    print()
    
    # Timestamp for filename
    date_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H%M')
    output_filename = f"post_market_report_{date_str}_{time_str}.pdf"
    output_path = OUTPUT_DIR / output_filename
    
    print(f"Output: {output_path}")
    print(f"Session Type: Post-Market Report")
    print()
    
    # ---------------------------------------------------------------------
    # STEP 1: Connect to Excel and read data
    # ---------------------------------------------------------------------
    print("[1/4] Connecting to Excel workbook...")
    
    reader = EpochExcelReader()
    if not reader.connect():
        print("ERROR: Failed to connect to Excel workbook.")
        print(f"       Ensure {WORKBOOK_PATH.name} is open in Excel.")
        return None
    
    print("       Reading ticker data...")
    viz_data_dict = reader.read_all_tickers()
    
    if not viz_data_dict:
        print("ERROR: No tickers found in workbook.")
        print("       Ensure Modules 01-07 have been run.")
        return None
    
    tickers = list(viz_data_dict.keys())
    print(f"       Found {len(tickers)} tickers: {', '.join(tickers)}")
    print()
    
    # ---------------------------------------------------------------------
    # STEP 2: Build epoch mapping and fetch Polygon data
    # ---------------------------------------------------------------------
    print("[2/4] Fetching market data from Polygon API...")
    
    # Build epoch mapping (ticker -> start_date)
    ticker_epochs = {}
    for ticker, vd in viz_data_dict.items():
        if vd.epoch and vd.epoch.start_date:
            ticker_epochs[ticker] = vd.epoch.start_date
        else:
            # Default to 30 days ago if no epoch set
            ticker_epochs[ticker] = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Fetch Polygon data for each ticker
    fetcher = PolygonDataFetcher()
    chart_data_dict = {}
    
    for i, ticker in enumerate(tickers, 1):
        epoch_start = ticker_epochs[ticker]
        print(f"       [{i}/{len(tickers)}] {ticker} (epoch: {epoch_start})...")
        
        chart_data_dict[ticker] = fetcher.fetch_chart_data(
            ticker=ticker,
            epoch_start_date=epoch_start,
            candle_bars=CANDLE_BAR_COUNT,
            candle_tf=CANDLE_TIMEFRAME,
            vbp_tf=VBP_TIMEFRAME
        )
    
    print()
    
    # ---------------------------------------------------------------------
    # STEP 3: Generate charts and compile PDF
    # ---------------------------------------------------------------------
    print("[3/4] Generating visualization charts...")
    
    # Create PDF with multiple pages
    with PdfPages(str(output_path)) as pdf:
        for i, ticker in enumerate(tickers, 1):
            print(f"       [{i}/{len(tickers)}] Building chart for {ticker}...")
            
            viz_data = viz_data_dict[ticker]
            chart_data = chart_data_dict[ticker]
            
            # Build chart
            builder = VisualizationChartBuilder()
            fig = builder.build(
                viz_data=viz_data,
                chart_data=chart_data,
                session_type=SESSION_TYPE,
                notes=""  # No notes in automated report
            )
            
            # Add page to PDF
            pdf.savefig(fig, dpi=DPI, facecolor=COLORS['dark_bg'],
                       edgecolor='none', bbox_inches='tight',
                       orientation='landscape')
            
            # Close figure to free memory
            builder.close()
    
    print()
    
    # ---------------------------------------------------------------------
    # STEP 4: Summary
    # ---------------------------------------------------------------------
    print("[4/4] Report generation complete!")
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Tickers processed: {len(tickers)}")
    print(f"Output file: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    
    # Print ticker summary
    print("Ticker Details:")
    print("-" * 70)
    for ticker in tickers:
        vd = viz_data_dict[ticker]
        cd = chart_data_dict[ticker]
        composite = vd.ticker_structure.composite or "N/A"
        price = vd.ticker_structure.price
        zones = len(vd.zones)
        candles = cd.candle_count
        print(f"  {ticker:6s} | Composite: {composite:8s} | "
              f"Price: ${price:8.2f} | Zones: {zones:2d} | Candles: {candles:3d}")
    
    print("-" * 70)
    print()
    print("Report ready for review!")
    print("=" * 70)
    
    return output_path


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        result = generate_report()
        if result:
            print(f"\nSuccess! Report saved to: {result}")
            sys.exit(0)
        else:
            print("\nReport generation failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)