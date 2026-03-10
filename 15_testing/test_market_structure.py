"""
================================================================================
EPOCH TRADING SYSTEM - Market Structure v3 Test
Interactive terminal test for the v3 anchor + walk-forward algorithm.
XIII Trading LLC
================================================================================

Usage:
    python 15_testing/test_market_structure.py
    python 15_testing/test_market_structure.py SPY
    python 15_testing/test_market_structure.py SPY --lookback 500

Fetches D1 bars via Polygon and runs the canonical v3 structure calculation.
Displays: direction, strong level, weak level (or "pending").
================================================================================
"""

import sys
import argparse
from datetime import date, timedelta

from shared.data.polygon import PolygonClient
from shared.indicators.structure import get_market_structure
from shared.indicators.config import CONFIG


# =============================================================================
# DISPLAY
# =============================================================================

BULL_COLOR = "\033[92m"  # green
BEAR_COLOR = "\033[91m"  # red
NEUTRAL_COLOR = "\033[93m"  # yellow
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def display_result(ticker: str, result, bar_count: int):
    """Print structure result to terminal."""
    dir_color = {1: BULL_COLOR, -1: BEAR_COLOR}.get(result.direction, NEUTRAL_COLOR)
    dir_label = result.label

    print()
    print(f"  {BOLD}{'=' * 50}{RESET}")
    print(f"  {BOLD}  Market Structure v3 — {ticker.upper()} D1{RESET}")
    print(f"  {BOLD}{'=' * 50}{RESET}")
    print()
    print(f"  {DIM}Bars analyzed:{RESET}  {bar_count}")
    print(f"  {DIM}Fractal len:{RESET}    {CONFIG.structure.fractal_length} bars each side")
    print(f"  {DIM}Retrace %:{RESET}      {CONFIG.structure.retrace_pct:.0%}")
    print()
    print(f"  {BOLD}Direction:{RESET}      {dir_color}{BOLD}{dir_label}{RESET}")
    print()

    if result.direction == 1:  # BULL
        strong_label = "Strong (Support)"
        weak_label = "Weak (Resistance)"
    elif result.direction == -1:  # BEAR
        strong_label = "Strong (Resistance)"
        weak_label = "Weak (Support)"
    else:
        strong_label = "Strong"
        weak_label = "Weak"

    if result.strong_level is not None:
        print(f"  {strong_label}:  {dir_color}${result.strong_level:.2f}{RESET}")
    else:
        print(f"  {strong_label}:  {DIM}—{RESET}")

    if result.weak_level is not None:
        print(f"  {weak_label}:    {dir_color}${result.weak_level:.2f}{RESET}")
    else:
        print(f"  {weak_label}:    {DIM}pending{RESET}")

    print()
    print(f"  {BOLD}{'=' * 50}{RESET}")
    print()


# =============================================================================
# MAIN
# =============================================================================

def run(ticker: str, lookback_days: int = 365):
    """Fetch D1 bars and calculate market structure."""
    client = PolygonClient()

    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)

    print(f"\n  Fetching D1 bars for {ticker.upper()} ({start_date} to {end_date})...")

    df = client.get_daily_bars(ticker, start_date, end_date)

    if df.empty:
        print(f"\n  No data returned for {ticker.upper()}. Check the ticker.\n")
        return

    print(f"  Received {len(df)} bars.")

    result = get_market_structure(df)
    display_result(ticker, result, len(df))


def main():
    parser = argparse.ArgumentParser(
        description="Test Market Structure v3 on D1 timeframe",
    )
    parser.add_argument(
        "ticker", nargs="?", default=None,
        help="Stock ticker (prompted if not provided)",
    )
    parser.add_argument(
        "--lookback", type=int, default=365,
        help="Lookback in calendar days (default: 365)",
    )
    args = parser.parse_args()

    ticker = args.ticker
    if not ticker:
        ticker = input("\n  Enter ticker: ").strip()
        if not ticker:
            print("  No ticker provided. Exiting.")
            return

    run(ticker, args.lookback)


if __name__ == "__main__":
    main()
