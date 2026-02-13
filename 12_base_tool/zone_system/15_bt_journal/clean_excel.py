"""
Epoch Backtest Journal - Excel Cleaner
Clears data from all cells written by journal modules.

Usage:
    python clean_excel.py           # Clear all module cells
    python clean_excel.py --module 01_win_loss    # Clear specific module
    python clean_excel.py --module 02_model_ratio # Clear specific module
    python clean_excel.py --module 03_indicator_edge # Clear specific module
    python clean_excel.py --list    # List all registered cells
"""

import argparse
import xlwings as xw
from pathlib import Path


# Excel file path
EXCEL_PATH = Path(r"C:\XIIITradingSystems\Epoch\02_zone_system\12_bt_journal\bt_journal.xlsx")

# Cell registry - add new modules here as they are developed
# Format: "module_name": {"sheet": "sheet_name", "ranges": ["range1", "range2", ...]}
# Use ranges for efficiency (e.g., "I10:P12" instead of individual cells)
CELL_REGISTRY = {
    "01_win_loss": {
        "sheet": "analysis",
        "ranges": [
            "C2",       # Total Trades
            "C6:D7",    # Win/Loss counts and percents
        ],
        "description": "Win/Loss Statistics (Overall)"
    },
    "02_model_ratio": {
        "sheet": "analysis",
        "ranges": [
            "C10:F13",  # All model data (Count, Win, Loss, Rate × 4 models)
        ],
        "description": "Win/Loss Statistics by Model (EPCH1-4)"
    },
    "03_indicator_edge": {
        "sheet": "analysis",
        "ranges": [
            # Section 1: Segment Summary
            "I10:P12",      # Baseline WR, Trade Count, Type (3 rows × 8 cols)
            # Section 2: Indicator Win Rate Matrix
            "I16:P27",      # Win rates by indicator state (12 rows × 8 cols)
            # Section 3: Top 5 Indicators by Edge
            "I31:P35",      # Top indicator per segment (5 rows × 8 cols)
            # Section 4: Optimal Entry Profiles
            "H40:J44",      # CONTINUATION LONGS (5 rows × 3 cols)
            "M40:O44",      # CONTINUATION SHORTS (5 rows × 3 cols)
            "H48:J52",      # REVERSAL LONGS (5 rows × 3 cols)
            "M48:O52",      # REVERSAL SHORTS (5 rows × 3 cols)
        ],
        "description": "Indicator Edge Analysis by Model Type and Direction"
    },
    # Add future modules here:
    # "04_module_name": {
    #     "sheet": "analysis",
    #     "ranges": ["A1:B5", "D1:E5"],
    #     "description": "Module description"
    # },
}


def count_cells_in_range(range_str: str) -> int:
    """
    Count the number of cells in a range string.
    
    Args:
        range_str: Excel range like "A1" or "A1:B5"
    
    Returns:
        Number of cells in the range
    """
    if ":" not in range_str:
        return 1
    
    start, end = range_str.split(":")
    
    # Extract column letters and row numbers
    start_col = ''.join(c for c in start if c.isalpha())
    start_row = int(''.join(c for c in start if c.isdigit()))
    end_col = ''.join(c for c in end if c.isalpha())
    end_row = int(''.join(c for c in end if c.isdigit()))
    
    # Convert column letters to numbers (A=1, B=2, etc.)
    def col_to_num(col):
        num = 0
        for c in col.upper():
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num
    
    start_col_num = col_to_num(start_col)
    end_col_num = col_to_num(end_col)
    
    rows = end_row - start_row + 1
    cols = end_col_num - start_col_num + 1
    
    return rows * cols


def clear_cells(modules: list = None, verbose: bool = True) -> dict:
    """
    Clear cells for specified modules (or all modules if none specified).

    Args:
        modules: List of module names to clear. None = all modules.
        verbose: Print progress messages.

    Returns:
        Dictionary with clearing results.
    """
    if modules is None:
        modules = list(CELL_REGISTRY.keys())

    # Validate module names
    invalid = [m for m in modules if m not in CELL_REGISTRY]
    if invalid:
        raise ValueError(f"Unknown module(s): {', '.join(invalid)}")

    if verbose:
        print(f"[1/2] Connecting to Excel...")

    wb = xw.Book(str(EXCEL_PATH))

    results = {}
    total_cells = 0

    if verbose:
        print(f"[2/2] Clearing cells...")
        print()

    for module_name in modules:
        module_config = CELL_REGISTRY[module_name]
        sheet_name = module_config["sheet"]
        ranges = module_config["ranges"]

        try:
            ws = wb.sheets[sheet_name]
            
            cells_cleared = 0
            for range_str in ranges:
                ws.range(range_str).clear_contents()
                cells_cleared += count_cells_in_range(range_str)

            results[module_name] = {
                "success": True,
                "cells_cleared": cells_cleared,
                "ranges_cleared": len(ranges),
                "sheet": sheet_name
            }
            total_cells += cells_cleared

            if verbose:
                print(f"  {module_name}: Cleared {cells_cleared} cells ({len(ranges)} ranges) in '{sheet_name}'")

        except Exception as e:
            results[module_name] = {
                "success": False,
                "error": str(e)
            }
            if verbose:
                print(f"  {module_name}: ERROR - {e}")

    if verbose:
        print()
        print("=" * 50)
        print(f"Total cells cleared: {total_cells}")
        print("=" * 50)

    return results


def list_cells(verbose: bool = True):
    """
    List all registered cells by module.

    Args:
        verbose: Print formatted output.
    """
    print()
    print("=" * 70)
    print("REGISTERED CELLS BY MODULE")
    print("=" * 70)
    print()

    total_cells = 0

    for module_name, config in CELL_REGISTRY.items():
        cell_count = sum(count_cells_in_range(r) for r in config["ranges"])
        
        print(f"{module_name}/")
        print(f"    Description: {config['description']}")
        print(f"    Sheet:       {config['sheet']}")
        print(f"    Ranges ({len(config['ranges'])}): {', '.join(config['ranges'])}")
        print(f"    Total cells: {cell_count}")
        print()
        total_cells += cell_count

    print("-" * 70)
    print(f"Total modules: {len(CELL_REGISTRY)}")
    print(f"Total cells:   {total_cells}")
    print("=" * 70)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Epoch Backtest Journal - Excel Cell Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python clean_excel.py                              # Clear all modules
    python clean_excel.py --module 01_win_loss         # Clear specific module
    python clean_excel.py --module 02_model_ratio      # Clear specific module
    python clean_excel.py --module 03_indicator_edge   # Clear specific module
    python clean_excel.py --list                       # List all registered cells

Registered Modules:
""" + "\n".join(f"    {k:20} {v['description']}" for k, v in CELL_REGISTRY.items())
    )

    parser.add_argument(
        "--module", "-m",
        type=str,
        action="append",
        choices=list(CELL_REGISTRY.keys()),
        help="Module(s) to clear (can specify multiple). Default: all modules."
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all registered cells and exit"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        list_cells()
        return

    # Clear mode
    try:
        clear_cells(
            modules=args.module,
            verbose=not args.quiet
        )
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()