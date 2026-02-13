"""
Test script to verify zones are being read correctly from Excel.

Run with: python test_zones.py
Requires: epoch_v1.xlsm to be open in Excel
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.excel_reader import ExcelReader
from config import EXCEL_PATH


def main():
    print("=" * 60)
    print("Zones Reader Test")
    print("=" * 60)
    print(f"\nReading from: {EXCEL_PATH}")
    print("Make sure the workbook is open in Excel.\n")

    reader = ExcelReader(EXCEL_PATH)

    try:
        reader.open()
        print("Connected to Excel workbook.\n")

        # Read zone_results (filtered zones)
        print("Reading zone_results worksheet...")
        filtered = reader.read_zone_results()
        print(f"  Found {len(filtered)} filtered zones.\n")

        if filtered:
            print("  Sample filtered zones (first 3):")
            for i, zone in enumerate(filtered[:3]):
                print(f"\n  Zone {i+1}:")
                print(f"    ticker: {zone.get('ticker')}")
                print(f"    zone_id: {zone.get('zone_id')}")
                print(f"    direction: {zone.get('direction')}")
                print(f"    rank: {zone.get('rank')} (type: {type(zone.get('rank')).__name__})")
                print(f"    tier: {zone.get('tier')}")
                print(f"    score: {zone.get('score')}")
                print(f"    is_filtered: {zone.get('is_filtered')}")
                print(f"    is_epch_bull: {zone.get('is_epch_bull')}")
                print(f"    is_epch_bear: {zone.get('is_epch_bear')}")
                print(f"    epch_bull_price: {zone.get('epch_bull_price')}")
                print(f"    epch_bear_price: {zone.get('epch_bear_price')}")
                print(f"    epch_bull_target: {zone.get('epch_bull_target')}")
                print(f"    epch_bear_target: {zone.get('epch_bear_target')}")

        # Read raw_zones
        print("\n" + "-" * 60)
        print("Reading raw_zones worksheet...")
        raw = reader.read_raw_zones()
        print(f"  Found {len(raw)} raw zones.\n")

        if raw:
            print("  Sample raw zones (first 3):")
            for i, zone in enumerate(raw[:3]):
                print(f"\n  Zone {i+1}:")
                print(f"    ticker: {zone.get('ticker')}")
                print(f"    zone_id: {zone.get('zone_id')}")
                print(f"    direction: {zone.get('direction')}")
                print(f"    rank: {zone.get('rank')} (type: {type(zone.get('rank')).__name__})")
                print(f"    score: {zone.get('score')}")
                print(f"    is_filtered: {zone.get('is_filtered')}")

        print("\n" + "=" * 60)
        print("Test Complete")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        reader.close()


if __name__ == "__main__":
    main()
