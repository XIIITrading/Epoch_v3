"""
One-time setup: Add properties to the existing Trade Journal Notion database.

This script is idempotent — safe to re-run. It will update the existing
database properties rather than creating duplicates.

The Trade Journal database must already exist in Notion. This script adds
the required properties (Date, Ticker, Model, Direction, Outcome, etc.)
and the 14 predefined tag options.

Usage:
    python scripts/setup_notion_db.py           # Apply properties
    python scripts/setup_notion_db.py --dry-run  # Show what would be done
    python scripts/setup_notion_db.py --status   # Show current schema

Requires: Notion MCP server connected (run from Claude Code)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from notion.config import NOTION_DATA_SOURCE_ID, TAGS


# The full property schema to apply
PROPERTY_SCHEMA = {
    # Rename "Name" to "Trade ID" (title property)
    "Name": {"name": "Trade ID"},

    # Date property
    "Date": {"date": {}},

    # Select properties
    "Ticker": {
        "select": {
            "options": [
                {"name": t, "color": "gray"}
                for t in ["AMD", "META", "MSFT", "SPY", "QQQ",
                          "AAPL", "NVDA", "TSLA", "AMZN", "GOOG"]
            ]
        }
    },
    "Model": {
        "select": {
            "options": [
                {"name": "EPCH1", "color": "blue"},
                {"name": "EPCH2", "color": "purple"},
                {"name": "EPCH3", "color": "green"},
                {"name": "EPCH4", "color": "orange"},
            ]
        }
    },
    "Direction": {
        "select": {
            "options": [
                {"name": "LONG", "color": "green"},
                {"name": "SHORT", "color": "red"},
            ]
        }
    },
    "Outcome": {
        "select": {
            "options": [
                {"name": "WIN", "color": "green"},
                {"name": "LOSS", "color": "red"},
            ]
        }
    },

    # Number properties
    "P&L (R)": {"number": {"format": "number"}},
    "Health at Entry": {"number": {"format": "number"}},

    # Multi-select (tags)
    "Tags": {
        "multi_select": {
            "options": TAGS
        }
    },

    # Checkbox
    "Reviewed": {"checkbox": {}},
}


def main():
    parser = argparse.ArgumentParser(
        description="Setup Notion Trade Journal database properties"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Show what would be created without applying"
    )
    parser.add_argument(
        '--status', action='store_true',
        help="Show current database schema and exit"
    )
    args = parser.parse_args()

    print(f"Trade Journal Database")
    print(f"Data Source ID: {NOTION_DATA_SOURCE_ID}")
    print()

    if args.status:
        print("To check current schema, run: notion-fetch on the database URL")
        print("https://www.notion.so/2fef98ca811d8013b83ac85f36ba5cc2")
        return

    if args.dry_run:
        print("=== DRY RUN — Properties to apply ===")
        print(json.dumps(PROPERTY_SCHEMA, indent=2))
        print()
        print(f"Total: {len(PROPERTY_SCHEMA)} properties")
        print("  - 1 title rename (Name → Trade ID)")
        print("  - 1 date (Date)")
        print("  - 4 selects (Ticker, Model, Direction, Outcome)")
        print("  - 2 numbers (P&L (R), Health at Entry)")
        print(f"  - 1 multi_select (Tags with {len(TAGS)} options)")
        print("  - 1 checkbox (Reviewed)")
        return

    print("Apply these properties using Notion MCP:")
    print()
    print("Step 1: notion-update-data-source")
    print(f"  data_source_id: {NOTION_DATA_SOURCE_ID}")
    print(f"  properties: (see JSON below)")
    print()
    print(json.dumps(PROPERTY_SCHEMA, indent=2))
    print()
    print("Step 2: Verify with notion-fetch on the database URL")


if __name__ == "__main__":
    main()
