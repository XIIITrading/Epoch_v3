"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v3.0
Backtest Runner - Main Orchestration Script (Hybrid S15/M5 Model)
XIII Trading LLC
================================================================================

HYBRID MODEL (v3.0):
    - ENTRY: S15 (15-second) bar close triggers entry detection
    - EXIT:  M5 (5-minute) bar manages exits (Stop, Target, CHoCH, EOD)

    This provides refined entry prices closer to zone boundaries while
    maintaining stable exit management on the M5 timeframe.

USAGE:
    python backtest_runner.py                     # Use date from Excel sheet
    python backtest_runner.py 2024-01-15          # Override with specific date
    python backtest_runner.py 2024-01-15 2024-01-19  # Date range
    python backtest_runner.py --clear             # Clear existing results
    python backtest_runner.py --source supabase 2024-01-15  # Load zones from Supabase

DATA SOURCES:
    --source supabase : Load zones from Supabase setups table (default, requires date)
    --source excel    : Load zones from Excel Analysis worksheet (deprecated)

REQUIREMENTS:
    - For Excel source: epoch_v1.xlsm must be open in Excel
    - For Supabase source: Setups must be exported from analysis_tool
    - Polygon API key configured in credentials.py
================================================================================
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import argparse

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import WORKBOOK_NAME, VERBOSE
from credentials import POLYGON_API_KEY
from data.zone_loader import ZoneLoader
from data.supabase_zone_loader import SupabaseZoneLoader
from data.m5_fetcher import M5Fetcher
from data.s15_fetcher import S15Fetcher
from engine.trade_simulator import TradeSimulator, CompletedTrade
from output.excel_writer import ExcelWriter


def get_trading_days(start_date: str, end_date: str = None) -> List[str]:
    """
    Get list of trading days between start and end dates.
    Simple implementation - excludes weekends only.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else start
    
    days = []
    current = start
    
    while current <= end:
        # Skip weekends (0=Monday, 6=Sunday)
        if current.weekday() < 5:
            days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return days


def run_backtest_for_date(date: str, zone_loader: ZoneLoader,
                          m5_fetcher: M5Fetcher,
                          s15_fetcher: S15Fetcher) -> List[CompletedTrade]:
    """
    Run backtest for a single date.
    
    Returns: List of all completed trades
    """
    print(f"\n{'='*60}")
    print(f"BACKTESTING: {date}")
    print(f"{'='*60}")
    
    all_trades = []
    
    # Load zones for the day
    source_name = "Supabase" if isinstance(zone_loader, SupabaseZoneLoader) else "Analysis worksheet"
    print(f"\nLoading zones from {source_name}...")
    primary_zones, secondary_zones = zone_loader.load_all_zones()
    
    if not primary_zones and not secondary_zones:
        print("  No zones found - skipping date")
        return all_trades
    
    # Get unique tickers
    tickers = set()
    for z in primary_zones:
        tickers.add(z.ticker)
    for z in secondary_zones:
        tickers.add(z.ticker)
    
    print(f"  Found {len(primary_zones)} primary zones, {len(secondary_zones)} secondary zones")
    print(f"  Tickers: {', '.join(sorted(tickers))}")
    
    # Process each ticker
    for ticker in sorted(tickers):
        print(f"\n--- Processing {ticker} ---")
        
        # Get zones for this ticker
        primary = next((z for z in primary_zones if z.ticker == ticker), None)
        secondary = next((z for z in secondary_zones if z.ticker == ticker), None)
        
        # Convert to dict format
        primary_dict = zone_loader.get_zone_dict(primary) if primary else None
        secondary_dict = zone_loader.get_zone_dict(secondary) if secondary else None
        
        if primary_dict:
            print(f"  Primary Zone: ${primary_dict['zone_low']:.2f} - ${primary_dict['zone_high']:.2f}")
        if secondary_dict:
            print(f"  Secondary Zone: ${secondary_dict['zone_low']:.2f} - ${secondary_dict['zone_high']:.2f}")
        
        # =================================================================
        # HYBRID MODEL: S15 for entries, M5 for exits
        # =================================================================

        # Fetch S15 data for entry detection
        s15_bars = s15_fetcher.fetch_bars_extended(ticker, date)

        if not s15_bars:
            print(f"  No S15 data available")
            continue

        # Fetch M5 data for exit management
        m5_bars = m5_fetcher.fetch_bars_extended(ticker, date)

        if not m5_bars:
            print(f"  No M5 data available")
            continue

        print(f"  Processing {len(s15_bars)} S15 bars (entry) + {len(m5_bars)} M5 bars (exit)...")

        # Initialize simulator with hybrid mode
        simulator = TradeSimulator(ticker=ticker, trade_date=date)
        simulator.set_zones(primary_zone=primary_dict, secondary_zone=secondary_dict)

        # Build M5 bar index for exit processing
        # Maps M5 bar timestamp to (bar_idx, bar) for quick lookup
        m5_bar_map = {}
        for idx, bar in enumerate(m5_bars):
            m5_bar_map[bar.timestamp] = (idx, bar)

        # Track which M5 bar we're currently in for exit checks
        current_m5_idx = 0
        last_m5_bar = None

        # Process S15 bars for entry detection
        for s15_idx, s15_bar in enumerate(s15_bars):
            # Find the corresponding M5 bar for this S15 timestamp
            # M5 bar covers a 5-minute window, so we find which M5 bar contains this S15 bar
            s15_time = s15_bar.timestamp

            # Update to the correct M5 bar (M5 bar timestamp is the START of the 5-min window)
            while current_m5_idx < len(m5_bars) - 1:
                next_m5_bar = m5_bars[current_m5_idx + 1]
                if s15_time >= next_m5_bar.timestamp:
                    current_m5_idx += 1
                else:
                    break

            current_m5_bar = m5_bars[current_m5_idx]

            # Check exits on M5 timeframe (only when M5 bar changes)
            if last_m5_bar is None or current_m5_bar.timestamp != last_m5_bar.timestamp:
                # Process M5 bar for exits only (no entry detection on M5)
                simulator.process_bar_exits_only(
                    bar_idx=current_m5_idx,
                    bar_time=current_m5_bar.timestamp,
                    bar_open=current_m5_bar.open,
                    bar_high=current_m5_bar.high,
                    bar_low=current_m5_bar.low,
                    bar_close=current_m5_bar.close
                )
                last_m5_bar = current_m5_bar

            # Check entries on S15 timeframe
            entries = simulator.process_bar_entries_only(
                bar_idx=s15_idx,
                bar_time=s15_bar.timestamp,
                bar_open=s15_bar.open,
                bar_high=s15_bar.high,
                bar_low=s15_bar.low,
                bar_close=s15_bar.close
            )

        # Force close any remaining positions using last M5 bar
        if simulator.get_active_position_count() > 0 and m5_bars:
            last_bar = m5_bars[-1]
            last_bar_idx = len(m5_bars) - 1
            simulator.force_close_all(
                bar_idx=last_bar_idx,
                bar_time=last_bar.timestamp,
                bar_close=last_bar.close
            )
        
        # Collect trades
        ticker_trades = simulator.get_completed_trades()
        all_trades.extend(ticker_trades)
        
        print(f"  Completed {len(ticker_trades)} trades for {ticker}")
        
        # Show trade summary
        for trade in ticker_trades:
            print(f"    {trade.model_name} {trade.direction}: "
                  f"${trade.entry_price:.2f} -> ${trade.exit_price:.2f} "
                  f"({trade.exit_reason}) {trade.pnl_r:+.2f}R")
    
    return all_trades


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Epoch Backtest Runner v3.0')
    parser.add_argument('start_date', nargs='?', help='Start date (YYYY-MM-DD) - if omitted, reads from Excel')
    parser.add_argument('end_date', nargs='?', help='End date (YYYY-MM-DD)')
    parser.add_argument('--clear', action='store_true', help='Clear existing results')
    parser.add_argument('--source', choices=['excel', 'supabase'], default='supabase',
                        help='Data source for zones (default: supabase)')
    parser.add_argument('--export', action='store_true',
                        help='Export trades to Supabase after backtest completes')

    args = parser.parse_args()

    print("=" * 70)
    print("EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v3.0")
    print("Hybrid Model: S15 Entry / M5 Exit")
    print("XIII Trading LLC")
    print("=" * 70)

    # Check API key
    if POLYGON_API_KEY == "your_polygon_api_key_here":
        print("\nERROR: Please set your Polygon API key in credentials.py")
        sys.exit(1)

    # Validate Supabase source requirements
    if args.source == 'supabase' and not args.start_date:
        print("\nERROR: When using --source supabase, you must specify a date.")
        print("Usage: python backtest_runner.py --source supabase 2025-01-20")
        sys.exit(1)

    # Initialize components based on source
    wb = None
    excel_writer = None
    zone_loader = None

    if args.source == 'excel':
        # Connect to Excel
        try:
            import xlwings as xw
            wb = xw.books[WORKBOOK_NAME]
            print(f"\nConnected to: {WORKBOOK_NAME}")
        except Exception as e:
            print(f"\nERROR: Could not connect to Excel workbook: {e}")
            print(f"Make sure {WORKBOOK_NAME} is open in Excel")
            sys.exit(1)

        zone_loader = ZoneLoader(wb)
        excel_writer = ExcelWriter(wb)
        print(f"\nData Source: Excel ({WORKBOOK_NAME})")
    else:
        # Supabase source - will create loader per date
        print(f"\nData Source: Supabase")

    m5_fetcher = M5Fetcher(POLYGON_API_KEY)
    s15_fetcher = S15Fetcher(POLYGON_API_KEY)

    print("\nHybrid Model Active:")
    print("  - Entry Detection: S15 (15-second) bar close")
    print("  - Exit Management: M5 (5-minute) bar (Stop/Target/CHoCH/EOD)")

    # Clear results if requested (only for Excel mode)
    if args.clear and excel_writer:
        print("\nClearing existing results...")
        excel_writer.clear_results()
        if not args.start_date:
            sheet_date = zone_loader.get_trading_date()
            if not sheet_date:
                print("Results cleared.")
                return

    # Determine dates to process
    if args.start_date:
        # User specified date(s) on command line
        dates = get_trading_days(args.start_date, args.end_date)
        print(f"\nUsing command-line date(s): {', '.join(dates)}")
    else:
        # Read date from Excel sheet (from ticker_id format) - only for Excel source
        sheet_date = zone_loader.get_trading_date()

        if sheet_date:
            dates = [sheet_date]
            print(f"\nUsing date from Excel sheet: {sheet_date}")
        else:
            print("\nERROR: Could not determine trading date from Excel sheet.")
            print("Please either:")
            print("  1. Ensure Analysis worksheet has valid ticker_id values (e.g., 'AMZN_120525')")
            print("  2. Specify date on command line: python backtest_runner.py 2025-12-05")
            print("  3. Use Supabase source: python backtest_runner.py --source supabase 2025-12-05")
            sys.exit(1)
    
    print(f"\nProcessing dates: {', '.join(dates)}")

    # Run backtest
    all_trades = []

    for date in dates:
        # For Supabase source, create a loader for each date
        if args.source == 'supabase':
            zone_loader = SupabaseZoneLoader(date, verbose=VERBOSE)

        trades = run_backtest_for_date(date, zone_loader, m5_fetcher, s15_fetcher)
        all_trades.extend(trades)

        # Close Supabase connection after each date
        if args.source == 'supabase':
            zone_loader.close()
    
    # Write results
    print(f"\n{'='*60}")
    if excel_writer:
        print("WRITING RESULTS TO EXCEL")
    else:
        print("BACKTEST RESULTS")
    print(f"{'='*60}")

    if excel_writer:
        if args.clear or not all_trades:
            excel_writer.clear_results()

        if all_trades:
            excel_writer.write_trades(all_trades)
            stats = excel_writer.calculate_stats(all_trades)
            excel_writer.write_summary(stats)

    if all_trades:
        # Calculate stats for display (works for both modes)
        if excel_writer:
            stats = excel_writer.calculate_stats(all_trades)
        else:
            # Calculate basic stats for Supabase mode (no Excel writer)
            from dataclasses import dataclass

            @dataclass
            class BasicStats:
                total_trades: int = 0
                wins: int = 0
                losses: int = 0
                win_rate: float = 0.0
                total_pnl_r: float = 0.0
                expectancy: float = 0.0
                profit_factor: float = 0.0
                by_model: dict = None
                by_exit: dict = None

            stats = BasicStats()
            stats.total_trades = len(all_trades)
            stats.wins = sum(1 for t in all_trades if t.pnl_r > 0)
            stats.losses = stats.total_trades - stats.wins
            stats.win_rate = stats.wins / stats.total_trades if stats.total_trades > 0 else 0
            stats.total_pnl_r = sum(t.pnl_r for t in all_trades)
            stats.expectancy = stats.total_pnl_r / stats.total_trades if stats.total_trades > 0 else 0

            gross_profit = sum(t.pnl_r for t in all_trades if t.pnl_r > 0)
            gross_loss = abs(sum(t.pnl_r for t in all_trades if t.pnl_r < 0))
            stats.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

            # By model
            stats.by_model = {}
            for trade in all_trades:
                model = trade.model_name
                if model not in stats.by_model:
                    stats.by_model[model] = {'trades': 0, 'wins': 0, 'total_r': 0}
                stats.by_model[model]['trades'] += 1
                if trade.pnl_r > 0:
                    stats.by_model[model]['wins'] += 1
                stats.by_model[model]['total_r'] += trade.pnl_r
            for model in stats.by_model:
                t = stats.by_model[model]['trades']
                w = stats.by_model[model]['wins']
                stats.by_model[model]['win_rate'] = w / t if t > 0 else 0

            # By exit
            stats.by_exit = {}
            for trade in all_trades:
                exit_type = trade.exit_reason
                if exit_type not in stats.by_exit:
                    stats.by_exit[exit_type] = {'trades': 0, 'total_r': 0}
                stats.by_exit[exit_type]['trades'] += 1
                stats.by_exit[exit_type]['total_r'] += trade.pnl_r

        # Print summary
        print(f"\n{'='*60}")
        print("BACKTEST COMPLETE")
        print(f"{'='*60}")
        print(f"Total Trades: {stats.total_trades}")
        print(f"Win Rate: {stats.win_rate:.1%}")
        print(f"Total P&L: {stats.total_pnl_r:+.2f}R")
        print(f"Expectancy: {stats.expectancy:+.2f}R")
        print(f"Profit Factor: {stats.profit_factor:.2f}")

        print(f"\nBy Model:")
        for model, data in stats.by_model.items():
            print(f"  {model}: {data['trades']} trades, {data['win_rate']:.0%} WR, {data['total_r']:+.1f}R")

        print(f"\nBy Exit Type:")
        for exit_type, data in stats.by_exit.items():
            print(f"  {exit_type}: {data['trades']} trades, {data['total_r']:+.1f}R")
    else:
        print("\nNo trades generated.")

    if excel_writer:
        print(f"\nResults written to '{WORKBOOK_NAME}' -> backtest worksheet")
    else:
        print(f"\nBacktest complete. Results displayed above.")

    # Export to Supabase if requested
    if args.export and all_trades:
        print(f"\n{'='*60}")
        print("EXPORTING TO SUPABASE")
        print(f"{'='*60}")
        try:
            from data.trades_exporter import export_trades
            from datetime import datetime as dt

            # Export for each date processed
            for trade_date_str in dates:
                trade_date = dt.strptime(trade_date_str, '%Y-%m-%d').date()
                date_trades = [t for t in all_trades if t.date == trade_date_str]
                if date_trades:
                    export_stats = export_trades(date_trades, trade_date, verbose=True)
                    if export_stats.success:
                        print(f"  {trade_date}: {export_stats.trades_exported} trades exported")
                    else:
                        print(f"  {trade_date}: Export failed - {export_stats.errors}")
            print(f"\nExport complete!")
        except Exception as e:
            print(f"\nExport failed: {e}")
            print("You can manually export later using: python -m data.trades_exporter --date YYYY-MM-DD")
    elif not args.export and all_trades and args.source == 'supabase':
        print("\nTip: Add --export flag to automatically upload trades to Supabase")


if __name__ == "__main__":
    main()