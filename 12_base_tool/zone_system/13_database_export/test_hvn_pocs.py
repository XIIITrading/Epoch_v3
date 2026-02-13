"""
Test script to verify HVN POCs are being read correctly from Excel.

Run with: python test_hvn_pocs.py
Requires: epoch_v1.xlsm to be open in Excel
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.excel_reader import ExcelReader
from config import EXCEL_PATH


def main():
    print("=" * 60)
    print("HVN POCs Reader Test")
    print("=" * 60)
    print(f"\nReading from: {EXCEL_PATH}")
    print("Make sure the workbook is open in Excel.\n")

    reader = ExcelReader(EXCEL_PATH)

    try:
        reader.open()
        print("Connected to Excel workbook.\n")

        # Read HVN POCs
        print("Reading HVN POCs from bar_data worksheet (time_hvn section, rows 59-68)...")
        data = reader.read_hvn_pocs()

        if not data:
            print("  No HVN POC data found!")
            return

        print(f"  Found {len(data)} ticker records.\n")

        # Display each ticker's POCs
        for record in data:
            ticker = record.get("ticker", "Unknown")
            ticker_id = record.get("ticker_id", "Unknown")
            epoch_start = record.get("epoch_start_date", "N/A")

            # Collect POCs
            pocs = []
            for i in range(1, 11):
                poc_val = record.get(f"poc_{i}")
                if poc_val is not None:
                    pocs.append(f"${poc_val:.2f}")

            print(f"  {ticker_id} ({ticker}):")
            print(f"    Epoch Start: {epoch_start}")
            if pocs:
                print(f"    POCs: {', '.join(pocs)}")
            else:
                print(f"    POCs: None found")
            print()

        print("=" * 60)
        print("Test Complete")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        raise

    finally:
        reader.close()


if __name__ == "__main__":
    main()
