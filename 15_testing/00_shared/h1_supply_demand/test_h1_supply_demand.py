"""
================================================================================
EPOCH TRADING SYSTEM - H1 Supply & Demand Zone Test
Interactive terminal test for H1 pivot-based supply/demand zones.
XIII Trading LLC
================================================================================

Usage:
    python 15_testing/00_shared/h1_supply_demand/test_h1_supply_demand.py
    python 15_testing/00_shared/h1_supply_demand/test_h1_supply_demand.py MU 2026-03-17

Description:
    Prompts for ticker and date, then:
    a) Fetches ~60 trading days of H1 bars ending at 08:00 ET on analysis date
    b) Calculates D1 ATR (14-period, same as PDV)
    c) Gets price at 08:00 ET
    d) Runs H1 S/D zone detection with 3-ATR filter from 08:00 price
    e) Displays zones in two tables: ABOVE price and BELOW price

Expected Output:
    ===========================================================
      H1 Supply & Demand Zones - MU (2026-03-17)
    ===========================================================

      Price @ 08:00:    $447.04
      D1 ATR:           $12.35
      Filter Band:      $410.00 - $484.09  (3 x ATR)
      H1 Bars:          420
      Pivots Found:     6 supply, 5 demand

    -----------------------------------------------------------
      ZONES ABOVE PRICE  (Supply / Flipped Demand)
    -----------------------------------------------------------
      ID   | Type     | High     | Low      | Touches | Flips
      S1   | Supply   | $458.30  | $455.20  | 4       | 0
      D1   | Demand   | $452.10  | $449.80  | 2       | 1
    -----------------------------------------------------------

    -----------------------------------------------------------
      ZONES BELOW PRICE  (Demand / Flipped Supply)
    -----------------------------------------------------------
      ID   | Type     | High     | Low      | Touches | Flips
      D2   | Demand   | $445.50  | $443.20  | 3       | 0
      D3   | Demand   | $438.00  | $435.60  | 1       | 0
    -----------------------------------------------------------

    ===========================================================
================================================================================
"""

import sys
import argparse
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
EPOCH_V2 = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(EPOCH_V2))
sys.path.insert(0, str(EPOCH_V2 / "01_application"))

import numpy as np
import pandas as pd

from shared.calculations.h1_supply_demand import (
    calculate_h1_zones,
    H1SupplyDemandResult,
    Zone,
    ZoneType,
)
from shared.calculations.h1_supply_demand.calculator import MAX_FLIPS, MAX_TOUCHES

ET_TIMEZONE = ZoneInfo("America/New_York")
H1_LOOKBACK_DAYS = 90   # calendar days (~60 trading days of H1 bars)
ATR_FILTER_MULT = 3.0    # keep zones within 3 x D1 ATR of price


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
# DATA FETCHING (mirrors PDV pattern)
# =============================================================================

def _get_polygon_client():
    """Get the 01_application Polygon client."""
    from data import get_polygon_client
    return get_polygon_client()


def _get_price_at_0800(client, ticker: str, analysis_date: date) -> float | None:
    """Get close price of last bar before 08:00 ET (same as PDV)."""
    end_ts = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day,
        8, 0, 0, tzinfo=ET_TIMEZONE,
    )
    start_date = analysis_date - timedelta(days=1)

    df = client.fetch_minute_bars(ticker, start_date, multiplier=5, end_timestamp=end_ts)
    if df is None or df.empty:
        df = client.fetch_hourly_bars(ticker, start_date, end_timestamp=end_ts)
    if df is None or df.empty:
        return None

    return round(float(df.iloc[-1]["close"]), 2)


def _calculate_d1_atr(client, ticker: str, analysis_date: date, period: int = 14) -> float | None:
    """Calculate D1 ATR (14-period SMA of true range) - same as PDV."""
    lookback_days = period * 2 + 10
    start_date = analysis_date - timedelta(days=lookback_days)

    df = client.fetch_daily_bars(ticker, start_date, analysis_date)
    if df is None or df.empty or len(df) < period + 1:
        return None

    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values

    tr = np.zeros(len(df))
    tr[0] = highs[0] - lows[0]
    for i in range(1, len(df)):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    return round(float(np.mean(tr[-period:])), 4)


def _fetch_h1_bars(client, ticker: str, analysis_date: date) -> pd.DataFrame:
    """Fetch H1 bars ending at 08:00 ET on analysis date."""
    end_ts = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day,
        8, 0, 0, tzinfo=ET_TIMEZONE,
    )
    start_date = analysis_date - timedelta(days=H1_LOOKBACK_DAYS)

    df = client.fetch_hourly_bars(ticker, start_date, end_timestamp=end_ts)
    if df is None or df.empty:
        return pd.DataFrame()

    return df


# =============================================================================
# DISPLAY
# =============================================================================

def _zone_type_colored(zone: Zone) -> str:
    """Zone type with color."""
    if zone.zone_type == ZoneType.SUPPLY:
        return f"{BEAR_COLOR}Supply{RESET} "
    else:
        return f"{BULL_COLOR}Demand{RESET} "


def _zone_id_colored(zone: Zone) -> str:
    """Zone ID with color."""
    if zone.zone_type == ZoneType.SUPPLY:
        return f"{BEAR_COLOR}{zone.zone_id:4s}{RESET}"
    else:
        return f"{BULL_COLOR}{zone.zone_id:4s}{RESET}"


def _print_zone_table(title: str, zones: list[Zone], show_lifetime: bool = False):
    """Print a formatted zone table."""
    if show_lifetime:
        sep = f"  {'-' * 97}"
    else:
        sep = f"  {'-' * 73}"

    print(sep)
    print(f"  {BOLD}  {title}{RESET}")
    print(sep)

    if not zones:
        print(f"  {DIM}  (none){RESET}")
        print(sep)
        return

    # Header
    if show_lifetime:
        print(
            f"  {DIM}  {'ID':4s} | {'Type':8s} | {'Pivot':>9s} | "
            f"{'High':>9s} | {'Low':>9s} | "
            f"{'Recent':>6s} | {'R.Flp':>5s} | "
            f"{'Total':>5s} | {'T.Flp':>5s}{RESET}"
        )
    else:
        print(
            f"  {DIM}  {'ID':4s} | {'Type':8s} | {'Pivot':>9s} | "
            f"{'High':>9s} | {'Low':>9s} | "
            f"{'Touches':>7s} | {'Flips':>5s}{RESET}"
        )

    for z in zones:
        if show_lifetime:
            print(
                f"   {_zone_id_colored(z)} | {_zone_type_colored(z)}  | "
                f"${z.pivot_price:>8.2f} | "
                f"${z.top:>8.2f} | ${z.bottom:>8.2f} | "
                f"{z.recent_touches:>6d} | {z.recent_flips:>5d} | "
                f"{z.touches:>5d} | {z.flips:>5d}"
            )
        else:
            print(
                f"   {_zone_id_colored(z)} | {_zone_type_colored(z)}  | "
                f"${z.pivot_price:>8.2f} | "
                f"${z.top:>8.2f} | ${z.bottom:>8.2f} | "
                f"{z.recent_touches:>7d} | {z.recent_flips:>5d}"
            )

    print(sep)


def display_result(
    result: H1SupplyDemandResult,
    analysis_date: date,
    price_0800: float | None,
    d1_atr: float | None,
):
    """Print full result to terminal."""
    sep = f"  {'=' * 59}"

    print()
    print(f"  {BOLD}{sep}{RESET}")
    print(f"  {BOLD}  H1 Supply & Demand Zones - {result.ticker} ({analysis_date}){RESET}")
    print(f"  {BOLD}{sep}{RESET}")
    print()

    if result.error:
        print(f"  {BEAR_COLOR}ERROR: {result.error}{RESET}")
        print()
        print(f"  {BOLD}{sep}{RESET}")
        print()
        return

    # Summary info
    if price_0800 is not None:
        print(f"  {DIM}Price @ 08:00:{RESET}    ${price_0800:.2f}")
    else:
        print(f"  {DIM}Price @ 08:00:{RESET}    -")

    if d1_atr is not None:
        print(f"  {DIM}D1 ATR:{RESET}           ${d1_atr:.2f}")

    if price_0800 is not None and d1_atr is not None:
        band_lo = price_0800 - d1_atr * ATR_FILTER_MULT
        band_hi = price_0800 + d1_atr * ATR_FILTER_MULT
        print(f"  {DIM}Filter Band:{RESET}      ${band_lo:.2f} - ${band_hi:.2f}  ({ATR_FILTER_MULT:.0f} x ATR)")

    print(f"  {DIM}H1 Bars:{RESET}          {result.bar_count}")
    print(
        f"  {DIM}Zones Found:{RESET}      "
        f"{result.total_supply} supply, {result.total_demand} demand"
    )
    print()

    # Split zones into above / below price
    ref_price = price_0800 if price_0800 is not None else result.last_close

    above = [z for z in result.all_zones if z.bottom >= ref_price]
    below = [z for z in result.all_zones if z.top < ref_price]
    straddle = [
        z for z in result.all_zones
        if z.bottom < ref_price and z.top >= ref_price
    ]

    # Above price: highest first
    above_sorted = sorted(above, key=lambda z: z.midpoint, reverse=True)
    # Below price: highest first (closest to price at top)
    below_sorted = sorted(below, key=lambda z: z.midpoint, reverse=True)
    # Straddle: price is inside zone
    straddle_sorted = sorted(straddle, key=lambda z: z.midpoint, reverse=True)

    _print_zone_table("ZONES ABOVE PRICE", above_sorted)
    print()

    if straddle_sorted:
        _print_zone_table("ZONES AT PRICE  (price inside zone)", straddle_sorted)
        print()

    _print_zone_table("ZONES BELOW PRICE", below_sorted)

    # Exhausted zones at the bottom — show both recent and lifetime counts
    if result.exhausted_zones:
        print()
        exhausted_sorted = sorted(
            result.exhausted_zones, key=lambda z: z.midpoint, reverse=True
        )
        _print_zone_table(
            f"EXHAUSTED ZONES  ({DIM}{MAX_FLIPS}+ recent flips or {MAX_TOUCHES}+ recent touches{RESET}{BOLD})",
            exhausted_sorted,
            show_lifetime=True,
        )

    print()
    print(f"  {BOLD}{sep}{RESET}")
    print()


# =============================================================================
# MAIN
# =============================================================================

def run(ticker: str, analysis_date: date):
    """Run the H1 S/D calculation and display results."""
    ticker = ticker.upper()

    print(f"\n  Calculating H1 Supply & Demand for {ticker} on {analysis_date}...")
    print(f"  (Fetching ~{H1_LOOKBACK_DAYS} days of H1 bars + D1 ATR)")
    print()

    client = _get_polygon_client()

    # Step 1: Price at 08:00
    print(f"  {DIM}  Fetching price @ 08:00 ET...{RESET}")
    price_0800 = _get_price_at_0800(client, ticker, analysis_date)

    # Step 2: D1 ATR
    print(f"  {DIM}  Calculating D1 ATR...{RESET}")
    d1_atr = _calculate_d1_atr(client, ticker, analysis_date)

    # Step 3: H1 bars
    print(f"  {DIM}  Fetching H1 bars...{RESET}")
    df_h1 = _fetch_h1_bars(client, ticker, analysis_date)

    if df_h1.empty:
        print(f"  {BEAR_COLOR}ERROR: No H1 data returned for {ticker}{RESET}")
        return

    print(f"  {DIM}  Running zone detection...{RESET}")

    # Step 4: Calculate zones with 3-ATR filter
    result = calculate_h1_zones(
        df_h1,
        ticker=ticker,
        d1_atr=d1_atr,
        atr_filter=ATR_FILTER_MULT,
    )

    display_result(result, analysis_date, price_0800, d1_atr)


def main():
    parser = argparse.ArgumentParser(
        description="Test H1 Supply & Demand zone calculation",
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
