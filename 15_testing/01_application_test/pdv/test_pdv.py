"""
================================================================================
EPOCH TRADING SYSTEM - Prior Day Value (PDV) Test
Interactive terminal test for Prior Day Value alignment calculation.
XIII Trading LLC
================================================================================

Usage:
    python 15_testing/01_application_test/pdv/test_pdv.py
    python 15_testing/01_application_test/pdv/test_pdv.py AAPL 2026-03-14

Description:
    Prompts for ticker and date, then calculates and displays:
    a) PDV POC Price    — Prior day's Point of Control (highest volume price)
    b) PD VAH Price     — Prior day's Value Area High (upper 70% volume bound)
    c) PD VAL Price     — Prior day's Value Area Low (lower 70% volume bound)
    d) Price at 08:00   — Current price at 08:00 ET on the analysis date
    e) D1 ATR           — 14-period daily Average True Range
    f) D1 ATR High      — PD POC + D1 ATR (upper ATR envelope from POC)
    g) D1 ATR Low       — PD POC - D1 ATR (lower ATR envelope from POC)
    h) Structure Dir.   — Composite market structure direction at 08:00 ET
    i) Alignment        — Whether price is Aligned or Not Aligned with structure
                          and whether that position is Optimal or Extended

Calculation Logic:
    1. Prior Day Volume Profile is calculated from 5-min bars during 04:00-20:00
       ET on the prior trading day using the Leviathan methodology (shared lib).
       - POC  = price level with the highest volume
       - VAH  = upper bound of the 70% volume concentration around POC
       - VAL  = lower bound of the 70% volume concentration around POC

    2. Price at 08:00 ET is the close of the last available bar (5-min or H1)
       before 08:00 ET on the analysis date. This captures pre-market pricing.

    3. D1 ATR is a 14-period Simple Moving Average of daily True Range.

    4. Market Structure Direction uses fractal detection across D1, H4, H1, M15
       timeframes with weighted composite scoring (D1: 1.5, H4: 1.5, H1: 1.0,
       M15: 0.5). Data is cut off at 08:00 ET via end_timestamp.

    5. Alignment Logic:
       - Price ABOVE VAH + Bull structure        = Aligned
       - Price BELOW VAL + Bear structure        = Aligned
       - Price INSIDE VA + Bull + price >= POC   = Aligned (Optimal)
       - Price INSIDE VA + Bear + price <= POC   = Aligned (Optimal)
       - Price INSIDE VA + Bull + price <  POC   = Not Aligned (Optimal)
       - Price INSIDE VA + Bear + price >  POC   = Not Aligned (Optimal)
       - All other outside combinations          = Not Aligned

       Outside VA — Inside vs Outside ATR bands:
       - Inside:   Distance from VA boundary <= ½ D1 ATR (within ATR bands)
       - Outside:  Distance from VA boundary >  ½ D1 ATR (beyond ATR bands)
       Inside VA is always 'Inside' (within ATR bands by definition)

Expected Output:
    ==================================================
      Prior Day Value Analysis — AAPL (2026-03-14)
    ==================================================

      Prior Day:        2026-03-13

      PD POC:           $171.25
      PD VAH:           $172.80
      PD VAL:           $169.50

      Price @ 08:00:    $173.15
      D1 ATR:           $3.42
      D1 ATR High:      $176.57
      D1 ATR Low:       $169.73

      Direction:        Bull
      Alignment:        Aligned (Optimal)

    ==================================================
================================================================================
"""

import sys
import argparse
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — add project root and 01_application to sys.path
# ---------------------------------------------------------------------------
EPOCH_V2 = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(EPOCH_V2))
sys.path.insert(0, str(EPOCH_V2 / "01_application"))

from shared.calculations.pdv import calculate_pdv, PDVResult, Alignment


# =============================================================================
# TERMINAL COLORS
# =============================================================================

BULL_COLOR = "\033[92m"    # green
BEAR_COLOR = "\033[91m"    # red
NEUTRAL_COLOR = "\033[93m" # yellow
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


# =============================================================================
# DISPLAY
# =============================================================================

def display_result(result: PDVResult):
    """Print PDV result to terminal with formatting."""
    sep = f"  {'=' * 54}"

    print()
    print(f"  {BOLD}{sep}{RESET}")
    print(f"  {BOLD}  Prior Day Value Analysis — {result.ticker} ({result.analysis_date}){RESET}")
    print(f"  {BOLD}{sep}{RESET}")
    print()

    if result.error:
        print(f"  {BEAR_COLOR}ERROR: {result.error}{RESET}")
        print()
        print(f"  {BOLD}{sep}{RESET}")
        print()
        return

    # Prior day date
    if result.prior_day_date:
        print(f"  {DIM}Prior Day:{RESET}        {result.prior_day_date}")
    print()

    # a) PDV POC
    _print_price("PD POC:", result.pd_poc, CYAN)

    # b) PD VAH
    _print_price("PD VAH:", result.pd_vah, CYAN)

    # c) PD VAL
    _print_price("PD VAL:", result.pd_val, CYAN)

    print()

    # d) Price at 08:00
    _print_price("Price @ 08:00:", result.price_at_0800)

    # e) D1 ATR
    if result.d1_atr is not None:
        print(f"  {DIM}D1 ATR:{RESET}           ${result.d1_atr:.2f}")
    else:
        print(f"  {DIM}D1 ATR:{RESET}           —")

    # f) D1 ATR High
    _print_price("D1 ATR High:", result.d1_atr_high)

    # g) D1 ATR Low
    _print_price("D1 ATR Low:", result.d1_atr_low)

    print()

    # h) Direction
    if result.direction:
        dir_color = {
            "Bull": BULL_COLOR,
            "Bear": BEAR_COLOR,
        }.get(result.direction, NEUTRAL_COLOR)
        print(f"  {DIM}Direction:{RESET}        {dir_color}{BOLD}{result.direction}{RESET}")
    else:
        print(f"  {DIM}Direction:{RESET}        —")

    # i) Alignment
    if result.alignment:
        if "Aligned" in result.alignment.value and "Not" not in result.alignment.value:
            align_color = BULL_COLOR
        else:
            align_color = BEAR_COLOR
        print(f"  {DIM}Alignment:{RESET}        {align_color}{BOLD}{result.alignment.value}{RESET}")
    else:
        print(f"  {DIM}Alignment:{RESET}        —")

    print()
    print(f"  {BOLD}{sep}{RESET}")
    print()


def _print_price(label: str, value, color=None):
    """Print a labeled price value."""
    padding = max(18 - len(label), 1)
    if value is not None:
        if color:
            print(f"  {DIM}{label}{RESET}{' ' * padding}{color}${value:.2f}{RESET}")
        else:
            print(f"  {DIM}{label}{RESET}{' ' * padding}${value:.2f}")
    else:
        print(f"  {DIM}{label}{RESET}{' ' * padding}—")


# =============================================================================
# MAIN
# =============================================================================

def run(ticker: str, analysis_date: date):
    """Run the PDV calculation and display results."""
    print(f"\n  Calculating Prior Day Value for {ticker.upper()} on {analysis_date}...")
    print(f"  (This fetches 5-min bars, daily bars, and multi-timeframe structure data)")
    print()

    result = calculate_pdv(ticker, analysis_date)
    display_result(result)


def main():
    parser = argparse.ArgumentParser(
        description="Test Prior Day Value (PDV) alignment calculation",
    )
    parser.add_argument(
        "ticker", nargs="?", default=None,
        help="Stock ticker (prompted if not provided)",
    )
    parser.add_argument(
        "date", nargs="?", default=None,
        help="Analysis date as YYYY-MM-DD (prompted if not provided)",
    )
    args = parser.parse_args()

    # Prompt for ticker
    ticker = args.ticker
    if not ticker:
        ticker = input("\n  Enter ticker: ").strip()
        if not ticker:
            print("  No ticker provided. Exiting.")
            return

    # Prompt for date
    analysis_date_str = args.date
    if not analysis_date_str:
        analysis_date_str = input("  Enter analysis date (YYYY-MM-DD): ").strip()
        if not analysis_date_str:
            print("  No date provided. Exiting.")
            return

    try:
        analysis_date = date.fromisoformat(analysis_date_str)
    except ValueError:
        print(f"  Invalid date format: {analysis_date_str}. Use YYYY-MM-DD.")
        return

    run(ticker, analysis_date)


if __name__ == "__main__":
    main()
