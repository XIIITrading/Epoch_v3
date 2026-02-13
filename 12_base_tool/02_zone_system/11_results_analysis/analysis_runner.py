"""
Module 10: Main Runner
Entry point for generating daily analysis exports.

UPDATED: Now reads trading date from Excel (ticker_id) by default,
matching the behavior of Module 09 backtester.

Usage:
    python analysis_runner.py                    # Use date from Excel sheet
    python analysis_runner.py --date 2025-12-04  # Override with specific date
    python analysis_runner.py --skip-polygon     # Skip Polygon API calls
    python analysis_runner.py --report           # Show historical report
    python analysis_runner.py --copy             # Copy JSON to clipboard
"""
import argparse
from datetime import date, datetime
from pathlib import Path
import sys

# Add module directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import EXCEL_WORKBOOK, OUTPUT_DIR, DATABASE_PATH
from daily_exporter import DailyExporter
from history_manager import HistoryManager
from excel_reader import ExcelReader
from summary_exporter import DailySummaryExporter


def get_date_from_excel() -> str:
    """
    Get trading date from Excel sheet (from ticker_id format).
    
    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    try:
        reader = ExcelReader()
        trading_date = reader.get_trading_date()
        reader.close()
        return trading_date
    except Exception as e:
        print(f"  Warning: Could not read date from Excel: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="EPOCH Module 10: Analysis Export & Historical Database"
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,  # Changed: No longer defaults to today
        help="Target date (YYYY-MM-DD format, default: read from Excel)"
    )
    parser.add_argument(
        "--skip-polygon", "-s",
        action="store_true",
        help="Skip Polygon API calls (faster, no market data)"
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Show historical summary report instead of exporting"
    )
    parser.add_argument(
        "--report-days",
        type=int,
        default=30,
        help="Number of days for historical report (default: 30)"
    )
    parser.add_argument(
        "--copy", "-c",
        action="store_true",
        help="Copy daily summary to clipboard (for Claude)"
    )
    parser.add_argument(
        "--copy-json",
        action="store_true",
        help="Copy full JSON to clipboard (large, not for chat)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save to file (useful with --copy)"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Don't save to SQLite database"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EPOCH Module 10: Analysis Export")
    print("=" * 60)
    
    # Handle report mode (doesn't need a date)
    if args.report:
        print(f"\n--- Historical Report (last {args.report_days} days) ---")
        manager = HistoryManager()
        report = manager.get_summary_report(args.report_days)
        
        agg = report["aggregate"]
        print(f"\nAggregate Statistics:")
        print(f"  Days analyzed: {agg['days_analyzed']}")
        print(f"  Total trades: {agg['total_trades']}")
        print(f"  Total wins: {agg['total_wins']}")
        print(f"  Win rate: {agg['overall_win_rate']:.1%}")
        print(f"  Total R: {agg['total_r']:.2f}")
        print(f"  Avg daily R: {agg['avg_daily_r']:.2f}")
        
        if report["model_performance"]:
            print(f"\nModel Performance:")
            for m in report["model_performance"]:
                name = m.get('model_name', m['model'])
                wr = m['total_wins'] / m['total_trades'] if m['total_trades'] else 0
                print(f"  {m['model']} ({name}): {m['total_trades']} trades, {wr:.0%} WR, {m['total_r']:.2f}R")
        
        if report["daily_breakdown"]:
            print(f"\nRecent Days:")
            for d in report["daily_breakdown"][:10]:
                print(f"  {d['date']}: {d['total_trades']} trades, {d['win_rate']:.0%} WR, {d['net_pnl_r']:.2f}R")
        
        return
    
    # Determine target date
    if args.date:
        # User specified date on command line
        target_date = args.date
        print(f"\nUsing command-line date: {target_date}")
    else:
        # Read date from Excel sheet (from ticker_id format)
        print(f"\nReading date from Excel sheet...")
        target_date = get_date_from_excel()
        
        if target_date:
            print(f"  Found date from ticker_id: {target_date}")
        else:
            print("\nERROR: Could not determine trading date from Excel sheet.")
            print("Please either:")
            print("  1. Ensure Analysis worksheet has valid ticker_id values (e.g., 'AMZN_120525')")
            print("  2. Specify date on command line: python analysis_runner.py --date 2025-12-05")
            sys.exit(1)
    
    # Show configuration
    print(f"\nConfiguration:")
    print(f"  Workbook: {EXCEL_WORKBOOK}")
    print(f"  Output Dir: {OUTPUT_DIR}")
    print(f"  Database: {DATABASE_PATH}")
    print(f"  Target Date: {target_date}")
    print(f"  Polygon API: {'Skipped' if args.skip_polygon else 'Enabled'}")
    
    # Export mode
    print(f"\n--- Generating Export for {target_date} ---")
    
    try:
        exporter = DailyExporter(
            target_date=target_date,
            skip_polygon=args.skip_polygon
        )
        
        # Generate export
        export_data = exporter.export()
        
        # Show summary
        meta = export_data["meta"]
        stats = export_data["statistics"]["overall"]
        
        print(f"\nExport Summary:")
        print(f"  Date: {meta['date']}")
        print(f"  Tickers: {', '.join(meta['ticker_list'])}")
        print(f"  Trades: {stats['total_trades']}")
        print(f"  Wins: {stats['winning_trades']}")
        print(f"  Win Rate: {stats['win_rate']:.1%}")
        print(f"  Net R: {stats['net_pnl_r']:.2f}")
        print(f"  Expectancy: {stats['expectancy_r']:.3f}R")
        
        # Show tier summary (V1.1)
        tier = export_data.get("tier_summary", {})
        if tier and tier.get("total_zones", 0) > 0:
            print(f"\nTier Quality:")
            print(f"  T1 (Premium): {tier['by_tier'].get('T1', 0)} zones ({tier['t1_percentage']:.1f}%)")
            print(f"  T2 (Standard): {tier['by_tier'].get('T2', 0)} zones ({tier['t2_percentage']:.1f}%)")
            print(f"  T3 (Marginal): {tier['by_tier'].get('T3', 0)} zones ({tier['t3_percentage']:.1f}%)")
        
        # Show market context
        context = export_data["market_context"]
        print(f"\nMarket Context:")
        print(f"  SPY Direction: {context['spy_direction']}")
        if context.get("vix_level"):
            print(f"  VIX: {context['vix_level']:.2f}")
        print(f"  Composite: {context['market_structure']['composite_bull']} Bull / {context['market_structure']['composite_bear']} Bear")
        
        # Show model breakdown
        if export_data["statistics"]["by_model"]:
            print(f"\nBy Model:")
            for model, model_stats in export_data["statistics"]["by_model"].items():
                name = model_stats.get('model_name', model)
                print(f"  {model} ({name}): {model_stats['trades']} trades, {model_stats['win_rate']:.0%} WR, {model_stats['net_r']:.2f}R")
        
        # Show trades
        if export_data["trades"]:
            print(f"\nTrades:")
            for t in export_data["trades"]:
                win = "W" if t["is_win"] else "L"
                name = t.get("model_name", t["model"])
                print(f"  {t['ticker']} {t['model']} ({name}) {t['direction']}: {t['pnl_r']:+.2f}R [{win}]")
        
        # Show validation
        validation = export_data["validation_checks"]
        if validation.get("tier_warnings"):
            print(f"\nTier Warnings:")
            for w in validation["tier_warnings"][:5]:  # Show first 5
                print(f"  ⚠ {w}")
        
        if validation["anomalies"]:
            print(f"\nValidation Warnings:")
            for a in validation["anomalies"]:
                print(f"  ⚠ {a}")
        
        # Save to file
        if not args.no_save:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / f"epoch_analysis_{target_date}.json"
            
            import json
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            print(f"\n✓ Full export saved to: {output_path}")
            
            # Generate condensed summary for Claude
            print(f"\nGenerating daily summary...")
            summary_exporter = DailySummaryExporter(target_date)
            summary = summary_exporter.export()
            summary_path = summary_exporter.save(summary)
            print(f"✓ Daily summary saved to: {summary_path}")
        
        # Save to database
        if not args.no_db:
            manager = HistoryManager()
            manager.save_daily_export(export_data)
            print(f"✓ Saved to database: {DATABASE_PATH}")
        
        # Copy to clipboard (summary for Claude, not full JSON)
        if args.copy:
            try:
                import pyperclip
                # Copy condensed summary (Claude-friendly) instead of full JSON
                if not args.no_save:
                    pyperclip.copy(summary)
                    print("✓ Daily summary copied to clipboard (paste into Claude)")
                else:
                    # If no-save, generate summary on the fly
                    summary_exporter = DailySummaryExporter(target_date)
                    summary = summary_exporter.export()
                    pyperclip.copy(summary)
                    print("✓ Daily summary copied to clipboard")
            except ImportError:
                print("⚠ pyperclip not installed - run: pip install pyperclip")
        
        # Copy full JSON to clipboard (if requested)
        if args.copy_json:
            try:
                import pyperclip
                import json
                pyperclip.copy(json.dumps(export_data, indent=2))
                print("✓ Full JSON copied to clipboard (warning: large)")
            except ImportError:
                print("⚠ pyperclip not installed - run: pip install pyperclip")
        
        print("\n" + "=" * 60)
        print("Export complete!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Could not find file")
        print(f"   {e}")
        print(f"\n   Make sure the workbook exists at:")
        print(f"   {EXCEL_WORKBOOK}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()