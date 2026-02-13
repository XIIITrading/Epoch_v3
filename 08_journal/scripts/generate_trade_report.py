"""
Generate Notion trade journal pages from Supabase data.

This script builds page data (properties + content) for trades and outputs
structured JSON that Claude Code uses to create/update Notion pages via MCP.

Workflow:
    1. Check status:     python scripts/generate_trade_report.py
    2. Push new trades:  python scripts/generate_trade_report.py --push
    3. (Claude creates Notion pages via MCP)
    4. Mark synced:      python scripts/generate_trade_report.py --mark-synced TRADE_ID PAGE_ID
    5. Resync updated:   python scripts/generate_trade_report.py --resync

Legacy usage (still works):
    python scripts/generate_trade_report.py SPY_012826_JRNL_1417
    python scripts/generate_trade_report.py --date 2026-01-28
    python scripts/generate_trade_report.py --date-from 2026-01-28 --date-to 2026-01-29
    python scripts/generate_trade_report.py --date 2026-01-28 --dry-run
    python scripts/generate_trade_report.py --date 2026-01-28 --output-json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import date, datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion.data_fetcher import NotionDataFetcher
from notion.page_builder import NotionPageBuilder
from notion.config import NOTION_DATA_SOURCE_ID, BATCH_SIZE


def parse_date(s: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {s}. Use YYYY-MM-DD.")


def show_status(fetcher: NotionDataFetcher):
    """Show sync status summary (default when no args provided)."""
    stats = fetcher.fetch_sync_stats()
    print()
    print("EPOCH Trade Journal - Notion Sync Status")
    print("=" * 45)
    print(f"  Total trades in database:   {stats['total']:>4}")
    print(f"  Already pushed to Notion:   {stats['synced']:>4}")
    print(f"  Awaiting initial push:      {stats['unsynced']:>4}")
    print(f"  Stale (data changed):       {stats['stale']:>4}")
    print()
    if stats['unsynced'] > 0:
        print(f"  Run with --push to push {stats['unsynced']} new trade(s)")
    if stats['stale'] > 0:
        print(f"  Run with --resync to update {stats['stale']} stale trade(s)")
    if stats['unsynced'] == 0 and stats['stale'] == 0:
        print("  All trades are synced!")
    print()


def handle_push(fetcher: NotionDataFetcher, dry_run: bool = False):
    """Generate pages for all unsynced trades up to today."""
    trades = fetcher.fetch_unsynced_trades(up_to_date=date.today())

    if not trades:
        print("All trades are already synced to Notion!")
        return

    print(f"Found {len(trades)} unsynced trade(s)")

    if dry_run:
        print("\n=== DRY RUN (--push) ===")
        for i, t in enumerate(trades, 1):
            tid = t.get('trade_id', '?')
            sym = t.get('symbol', '?')
            d = t.get('direction', '?')
            outcome = t.get('outcome', '?')
            reviewed = "Reviewed" if t.get('stop_price') else "Unreviewed"
            print(f"  [{i}/{len(trades)}] {tid} | {sym} | {d} | {outcome} | {reviewed}")
        print(f"\nWould create {len(trades)} Notion page(s)")
        return

    # Build pages
    builder = NotionPageBuilder(fetcher)
    pages_data = _build_pages(builder, trades)

    if not pages_data:
        print("No pages built successfully.")
        return

    # Output structured JSON for MCP consumption
    output = {
        "action": "create",
        "data_source_id": NOTION_DATA_SOURCE_ID,
        "total_pages": len(pages_data),
        "pages": pages_data,
    }
    print(json.dumps(output, indent=2, default=str))

    # Print reminder
    print(f"\n--- After creating pages, run --mark-synced or --mark-synced-batch to record page IDs ---", file=sys.stderr)


def handle_resync(fetcher: NotionDataFetcher, dry_run: bool = False):
    """Regenerate pages for trades whose data changed since last sync."""
    trades = fetcher.fetch_stale_synced_trades()

    if not trades:
        print("No stale trades found. Everything is up to date!")
        return

    print(f"Found {len(trades)} stale trade(s) needing resync")

    if dry_run:
        print("\n=== DRY RUN (--resync) ===")
        for i, t in enumerate(trades, 1):
            tid = t.get('trade_id', '?')
            sym = t.get('symbol', '?')
            page_id = t.get('notion_page_id', '?')
            synced = t.get('notion_synced_at', '?')
            updated = t.get('updated_at', '?')
            print(f"  [{i}/{len(trades)}] {tid} | {sym} | page={page_id} | synced={synced} | updated={updated}")
        print(f"\nWould update {len(trades)} Notion page(s)")
        return

    # Build updated pages
    builder = NotionPageBuilder(fetcher)
    pages_data = _build_pages(builder, trades, include_page_id=True)

    if not pages_data:
        print("No pages built successfully.")
        return

    output = {
        "action": "update",
        "total_pages": len(pages_data),
        "pages": pages_data,
    }
    print(json.dumps(output, indent=2, default=str))


def handle_mark_synced(trade_id: str, page_id: str):
    """Record a Notion page_id for a single trade."""
    from data.journal_db import JournalDB

    # Build URL from page_id
    page_url = f"https://notion.so/{page_id.replace('-', '')}"

    with JournalDB() as db:
        success = db.mark_notion_synced(trade_id, page_id, page_url)

    if success:
        print(f"OK: {trade_id} -> {page_id}")
        print(f"    URL: {page_url}")
    else:
        print(f"FAILED: Could not mark {trade_id} as synced")
        sys.exit(1)


def handle_mark_synced_batch(json_string: str):
    """Record Notion page_ids for multiple trades at once."""
    from data.journal_db import JournalDB

    try:
        mappings = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(mappings, dict):
        print("Expected JSON object: {\"trade_id\": \"page_id\", ...}")
        sys.exit(1)

    success_count = 0
    with JournalDB() as db:
        for trade_id, page_id in mappings.items():
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            if db.mark_notion_synced(trade_id, page_id, page_url):
                print(f"  OK: {trade_id} -> {page_id}")
                success_count += 1
            else:
                print(f"  FAILED: {trade_id}")

    print(f"\nMarked {success_count}/{len(mappings)} trade(s) as synced")


def handle_legacy(args, fetcher: NotionDataFetcher):
    """Handle legacy CLI modes (trade_id, --date, --date-from/--date-to)."""
    trades = []
    if args.trade_id:
        trade = fetcher.fetch_trade(args.trade_id)
        if trade:
            trades = [trade]
        else:
            print(f"Trade not found: {args.trade_id}")
            sys.exit(1)
    elif args.date:
        trades = fetcher.fetch_trades_by_date(args.date)
        if not trades:
            print(f"No trades found for {args.date}")
            sys.exit(0)
    elif args.date_from:
        trades = fetcher.fetch_trades_by_range(args.date_from, args.date_to)
        if not trades:
            print(f"No trades found for {args.date_from} to {args.date_to}")
            sys.exit(0)

    print(f"Found {len(trades)} trade(s)")

    if args.dry_run:
        print("\n=== DRY RUN ===")
        for i, t in enumerate(trades, 1):
            tid = t.get('trade_id', '?')
            sym = t.get('symbol', '?')
            d = t.get('direction', '?')
            outcome = t.get('outcome', '?')
            reviewed = "Reviewed" if t.get('stop_price') else "Unreviewed"
            synced = "Synced" if t.get('notion_page_id') else "Not synced"
            print(f"  [{i}/{len(trades)}] {tid} | {sym} | {d} | {outcome} | {reviewed} | {synced}")
        print(f"\nWould create {len(trades)} Notion page(s)")
        return

    # Build pages
    builder = NotionPageBuilder(fetcher)
    pages_data = _build_pages(builder, trades)

    if args.output_json:
        output = {
            "action": "create",
            "data_source_id": NOTION_DATA_SOURCE_ID,
            "pages": pages_data,
        }
        print("\n=== JSON OUTPUT ===")
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n=== READY TO CREATE {len(pages_data)} PAGES ===")
        print(f"Target database: collection://{NOTION_DATA_SOURCE_ID}")
        print()
        for pd_item in pages_data:
            tid = pd_item['trade_id']
            props = pd_item['properties']
            ticker = props.get('Ticker', '?')
            direction = props.get('Direction', '?')
            outcome = props.get('Outcome', '?')
            pnl = props.get('P&L (R)', 'N/A')
            health = props.get('Health at Entry', 'N/A')
            print(f"  {tid} | {ticker} {direction} | {outcome} | {pnl}R | Health: {health}")

        if pages_data:
            print(f"\n=== PREVIEW: {pages_data[0]['trade_id']} ===")
            print(f"Properties: {json.dumps(pages_data[0]['properties'], indent=2, default=str)}")
            print(f"\nContent ({len(pages_data[0]['content'])} chars):")
            print(pages_data[0]['content'][:2000])
            if len(pages_data[0]['content']) > 2000:
                print(f"\n... ({len(pages_data[0]['content']) - 2000} more chars)")


def _build_pages(builder: NotionPageBuilder, trades: list, include_page_id: bool = False) -> list:
    """Build page data for a list of trades."""
    pages_data = []
    for i, trade in enumerate(trades, 1):
        trade_id = trade.get('trade_id', 'UNKNOWN')
        print(f"  [{i}/{len(trades)}] Building page for {trade_id}...", file=sys.stderr)

        try:
            properties, content = builder.build_page(trade)
            page_data = {
                "trade_id": trade_id,
                "properties": properties,
                "content": content,
            }
            if include_page_id and trade.get('notion_page_id'):
                page_data["notion_page_id"] = trade['notion_page_id']
            pages_data.append(page_data)
            print(f"    Built: {trade_id} ({len(content)} chars)", file=sys.stderr)
        except Exception as e:
            print(f"    ERROR building {trade_id}: {e}", file=sys.stderr)
            continue

    return pages_data


def main():
    parser = argparse.ArgumentParser(
        description="Generate and sync Notion trade journal pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sync workflow:
  python scripts/generate_trade_report.py                       # Check status
  python scripts/generate_trade_report.py --push                # Push unsynced trades
  python scripts/generate_trade_report.py --mark-synced TID PID # Record page ID
  python scripts/generate_trade_report.py --resync              # Update stale trades

Legacy usage:
  python scripts/generate_trade_report.py SPY_012826_JRNL_1417
  python scripts/generate_trade_report.py --date 2026-01-28
  python scripts/generate_trade_report.py --date-from 2026-01-28 --date-to 2026-01-29
        """
    )

    # Sync commands
    parser.add_argument(
        '--push', action='store_true',
        help="Generate page data for all unsynced trades up to today"
    )
    parser.add_argument(
        '--resync', action='store_true',
        help="Regenerate page data for trades whose review data changed after sync"
    )
    parser.add_argument(
        '--mark-synced', nargs=2, metavar=('TRADE_ID', 'PAGE_ID'),
        help="Record Notion page_id for a trade after successful page creation"
    )
    parser.add_argument(
        '--mark-synced-batch', type=str, metavar='JSON_STRING',
        help='JSON string of {"trade_id": "page_id", ...} mappings to record'
    )

    # Legacy commands
    parser.add_argument(
        'trade_id', nargs='?', default=None,
        help="Single trade ID to generate (e.g., SPY_012826_JRNL_1417)"
    )
    parser.add_argument(
        '--date', type=parse_date, default=None,
        help="Generate for all trades on this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--date-from', type=parse_date, default=None,
        help="Start date for range (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--date-to', type=parse_date, default=None,
        help="End date for range (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Show what would be created/updated without generating output"
    )
    parser.add_argument(
        '--output-json', action='store_true',
        help="Output structured JSON for each page (for MCP consumption)"
    )

    args = parser.parse_args()

    # Handle --mark-synced (no DB read needed)
    if args.mark_synced:
        handle_mark_synced(args.mark_synced[0], args.mark_synced[1])
        return

    # Handle --mark-synced-batch (no DB read needed)
    if args.mark_synced_batch:
        handle_mark_synced_batch(args.mark_synced_batch)
        return

    if args.date_from and not args.date_to:
        args.date_to = args.date_from

    # All remaining modes need a fetcher connection
    print("Connecting to Supabase...", file=sys.stderr)
    with NotionDataFetcher() as fetcher:

        # --push mode
        if args.push:
            handle_push(fetcher, dry_run=args.dry_run)
            return

        # --resync mode
        if args.resync:
            handle_resync(fetcher, dry_run=args.dry_run)
            return

        # Legacy modes (trade_id, --date, --date-from)
        if args.trade_id or args.date or args.date_from:
            handle_legacy(args, fetcher)
            return

        # No args at all: show status
        show_status(fetcher)


if __name__ == "__main__":
    main()
