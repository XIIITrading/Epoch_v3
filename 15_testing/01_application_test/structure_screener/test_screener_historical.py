"""
================================================================================
EPOCH TRADING SYSTEM - Historical Structure Screener Test
Simulates running the structure screener as of 08:00 ET on a given date.
XIII Trading LLC
================================================================================

Usage:
    python test_screener_historical.py
    python test_screener_historical.py 2026-03-13
    python test_screener_historical.py 2026-03-13 SP500

Description:
    Runs the full structure screener scan with all data cut off at 08:00 ET
    on the specified date, exactly as if the scan had been run live that
    morning. Uses the same scoring engine, classification, and PDV alignment
    logic as the production screener.

    Outputs (in terminal):
        1. Top 10 Bull shortlist  (PDV = Aligned Inside required)
        2. Top 10 Bear shortlist  (PDV = Aligned Inside required)
        3. All tickers with PDV = Aligned (Inside)
        4. All tickers with PDV = Aligned (Outside)

Calculation Logic:
    1. Fetches 365 days of daily bars up to (but not including) the analysis
       date. The analysis date's bar is excluded because at 08:00 ET the
       regular session has not started yet.

    2. For each ticker:
       a. Hard filters: min price ($10), min ATR ($2), min 20 bars
       b. D1 market structure (v3) from daily bars
       c. Prior D1 body alignment (open-close of second-to-last bar)
       d. Price at 08:00 ET from 5-min premarket bars
       e. RVOL: 04:00-08:00 volume vs trailing 12-day average
       f. Gap%: 08:00 price vs prior D1 close
       g. State classification (7 states)
       h. Composite score: S + A + G + R + Z (max ~105)
       i. PDV alignment (Prior Day Value calculation)

    3. Shortlist filter: score > 0 AND PDV = Aligned (Inside)

    4. Sorted by composite score descending.

Ticker Lists:
    SP500     — S&P 500 (default)
    NASDAQ100 — NASDAQ 100
    DOW30     — DOW 30
    RUSSELL   — Russell 2000
    ALL       — All US Equities
================================================================================
"""

import sys
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
EPOCH_V2 = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(EPOCH_V2))
sys.path.insert(0, str(EPOCH_V2 / "01_application"))

from data.polygon_client import PolygonClient
from shared.indicators.structure import get_market_structure
from shared.calculations.pdv import calculate_pdv, Alignment
from scanner import TickerManager, TickerList

# Import scoring functions from the production screener
from ui.tabs.structure_screener import (
    classify_ticker,
    score_ticker,
)

logger = logging.getLogger(__name__)
ET = ZoneInfo("America/New_York")

# =============================================================================
# TERMINAL COLORS
# =============================================================================

BULL_COLOR = "\033[92m"    # green
BEAR_COLOR = "\033[91m"    # red
CYAN = "\033[96m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

TICKER_LISTS = {
    "SP500": TickerList.SP500,
    "NASDAQ100": TickerList.NASDAQ100,
    "DOW30": TickerList.DOW30,
    "RUSSELL": TickerList.RUSSELL2000,
    "ALL": TickerList.ALL_US_EQUITIES,
}

# =============================================================================
# CORE SCAN LOGIC
# =============================================================================

def quick_atr(df, period: int = 14) -> float:
    """Lightweight ATR from a daily DataFrame (EMA-based, matches screener)."""
    if len(df) < 2:
        return 0.0
    df2 = df.copy()
    df2["h_l"] = df2["high"] - df2["low"]
    df2["h_pc"] = (df2["high"] - df2["close"].shift(1)).abs()
    df2["l_pc"] = (df2["low"] - df2["close"].shift(1)).abs()
    df2["tr"] = df2[["h_l", "h_pc", "l_pc"]].max(axis=1)
    return float(df2["tr"].ewm(span=period, adjust=False).mean().iloc[-1])


def fetch_premarket_data(
    polygon: PolygonClient,
    ticker: str,
    analysis_date: date,
) -> dict:
    """
    Fetch 5-min bars to get price at 08:00 ET and RVOL (04:00-08:00).

    Mirrors the production screener's fetch_minute_data() but uses 08:00 ET
    cutoff instead of 09:00.
    """
    result = {"price_0800": None, "rvol_pct": None}

    try:
        end_ts = datetime(
            analysis_date.year, analysis_date.month, analysis_date.day,
            8, 0, 0, tzinfo=ET,
        )

        rvol_start = analysis_date - timedelta(days=25)
        min_df = polygon.fetch_minute_bars(
            ticker, rvol_start, multiplier=5, end_timestamp=end_ts,
        )

        if min_df is None or min_df.empty:
            return result

        # Convert timestamps
        min_df["et_time"] = min_df["timestamp"].dt.tz_convert(ET)
        min_df["bar_date"] = min_df["et_time"].dt.date
        min_df["bar_hour"] = min_df["et_time"].dt.hour

        # Price at 08:00: last bar close on analysis_date before cutoff
        today_bars = min_df[min_df["bar_date"] == analysis_date]
        if not today_bars.empty:
            pre_0800 = today_bars[today_bars["bar_hour"] < 8]
            if not pre_0800.empty:
                result["price_0800"] = float(pre_0800["close"].iloc[-1])

        # RVOL: 04:00-08:00 volume
        premarket = min_df[
            (min_df["bar_hour"] >= 4) & (min_df["bar_hour"] < 8)
        ]
        if premarket.empty:
            return result

        daily_pm_vol = premarket.groupby("bar_date")["volume"].sum()
        today_vol = daily_pm_vol.get(analysis_date, 0)

        prior_vols = daily_pm_vol.drop(analysis_date, errors="ignore")
        prior_vols = prior_vols.sort_index().tail(12)

        if len(prior_vols) > 0 and prior_vols.mean() > 0:
            result["rvol_pct"] = round((today_vol / prior_vols.mean()) * 100, 0)
        else:
            result["rvol_pct"] = 0

    except Exception as exc:
        logger.debug(f"Premarket data skip {ticker}: {exc}")

    return result


def process_ticker(
    ticker: str,
    polygon: PolygonClient,
    analysis_date: date,
    start_date: date,
    min_price: float = 10.0,
    min_atr: float = 2.0,
) -> Optional[dict]:
    """
    Process a single ticker — mirrors the production screener's _process_one()
    but with data cut off at 08:00 ET on analysis_date.
    """
    try:
        # The prior trading day's close is the last bar before analysis_date
        # Fetch daily bars ending the day BEFORE analysis_date
        prior_end = analysis_date - timedelta(days=1)
        df = polygon.fetch_daily_bars(ticker, start_date, prior_end)

        if df is None or df.empty or len(df) < 20:
            return None

        d1_close = float(df["close"].iloc[-1])

        # Hard filters
        if d1_close < min_price:
            return None

        atr = quick_atr(df)
        if atr < min_atr:
            return None

        # Prior day body check
        if len(df) >= 2:
            prior_open = float(df["open"].iloc[-2])
            prior_close = float(df["close"].iloc[-2])
            body_lo = min(prior_open, prior_close)
            body_hi = max(prior_open, prior_close)
            if d1_close > body_hi:
                prior_d1_body = "Above"
            elif d1_close < body_lo:
                prior_d1_body = "Below"
            else:
                prior_d1_body = "Inside"
        else:
            prior_d1_body = "—"

        # D1 market structure
        structure = get_market_structure(df)

        # Premarket data at 08:00 ET
        pm_data = fetch_premarket_data(polygon, ticker, analysis_date)

        current_price = pm_data["price_0800"] or d1_close
        price_source = "08:00" if pm_data["price_0800"] else "D1"

        # Gap%
        if price_source == "08:00" and d1_close > 0:
            gap_pct = round((current_price - d1_close) / d1_close * 100, 2)
        else:
            gap_pct = 0.0

        # State classification
        state = classify_ticker(
            structure.direction,
            structure.strong_level,
            structure.weak_level,
            current_price,
        )

        row = {
            "ticker": ticker,
            "price": current_price,
            "d1_close": d1_close,
            "price_source": price_source,
            "gap_pct": gap_pct,
            "direction": structure.label,
            "strong": structure.strong_level,
            "weak": structure.weak_level,
            "state": state,
            "atr": round(atr, 2),
            "prior_d1_body": prior_d1_body,
            "rvol_pct": pm_data["rvol_pct"],
        }

        # Score
        score_ticker(row)

        # PDV alignment
        try:
            pdv = calculate_pdv(ticker, analysis_date, polygon_client=polygon)
            row["pdv_alignment"] = pdv.alignment.value if pdv.alignment else "—"
        except Exception:
            row["pdv_alignment"] = "—"

        return row

    except Exception as exc:
        logger.debug(f"Skip {ticker}: {exc}")
        return None


def run_scan(
    analysis_date: date,
    ticker_list: TickerList = TickerList.SP500,
    parallel_workers: int = 10,
) -> List[dict]:
    """Run the full structure screener scan for a historical date."""

    polygon = PolygonClient()
    ticker_mgr = TickerManager()
    tickers = ticker_mgr.get_tickers(ticker_list)

    start_date = analysis_date - timedelta(days=365)
    results: List[dict] = []
    total = len(tickers)

    print(f"\n  {BOLD}Scanning {total} tickers as of 08:00 ET on {analysis_date}...{RESET}")
    print(f"  {DIM}Using {parallel_workers} parallel workers{RESET}\n")

    with ThreadPoolExecutor(max_workers=parallel_workers) as pool:
        futures = {
            pool.submit(
                process_ticker, t, polygon, analysis_date, start_date
            ): t
            for t in tickers
        }
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0 or completed == total:
                pct = int(completed / total * 100)
                print(f"  {DIM}  Progress: {completed}/{total} ({pct}%){RESET}", end="\r")

            try:
                row = future.result()
                if row is not None:
                    results.append(row)
            except Exception:
                pass

    print(f"  {DIM}  Progress: {total}/{total} (100%) — {len(results)} tickers passed filters{RESET}")

    # Sort by score descending
    state_order = {
        "Out - Strong": 0, "Out - Weak": 1,
        "Bull": 2, "Bear": 3,
        "Bull (Low)": 4, "Bear (High)": 5,
        "Neutral": 6,
    }
    results.sort(key=lambda r: (-r.get("score", 0),
                                 state_order.get(r["state"], 9),
                                 r["ticker"]))
    return results


# =============================================================================
# DISPLAY
# =============================================================================

def print_header(title: str, color: str = WHITE):
    """Print a section header."""
    sep = "=" * 90
    print(f"\n  {color}{BOLD}{sep}{RESET}")
    print(f"  {color}{BOLD}  {title}{RESET}")
    print(f"  {color}{BOLD}{sep}{RESET}")


def print_table_header():
    """Print column headers for result rows."""
    print(
        f"  {DIM}{'#':>3}  {'Ticker':<7} {'Price':>8} {'Score':>5}  "
        f"{'Dir':<5} {'State':<13} {'S':>2} {'A':>2} {'G':>2} {'R':>2} {'Z':>2}  "
        f"{'Gap%':>6} {'RVOL%':>6} {'ATR':>7}  {'PDV Alignment':<22}{RESET}"
    )
    print(f"  {DIM}{'-' * 118}{RESET}")


def print_row(rank: int, r: dict, dir_color: str):
    """Print a single result row."""
    sd = r.get("score_detail", {})
    gap_str = f"{r.get('gap_pct', 0.0):+.1f}%" if r.get("price_source") != "D1" else "—"
    rvol = r.get("rvol_pct")
    rvol_str = f"{rvol:.0f}%" if rvol is not None and rvol > 0 else "—"
    pdv = r.get("pdv_alignment", "—")

    # Color PDV alignment
    if "Aligned" in pdv and "Not" not in pdv:
        pdv_color = BULL_COLOR
    elif "Not Aligned" in pdv:
        pdv_color = BEAR_COLOR
    else:
        pdv_color = DIM

    print(
        f"  {rank:>3}  {dir_color}{BOLD}{r['ticker']:<7}{RESET} "
        f"${r['price']:>7.2f} {r.get('score', 0):>5}  "
        f"{dir_color}{r['direction']:<5}{RESET} {r['state']:<13} "
        f"{sd.get('S', 0):>2} {sd.get('A', 0):>2} {sd.get('G', 0):>2} "
        f"{sd.get('R', 0):>2} {sd.get('Z', 0):>2}  "
        f"{gap_str:>6} {rvol_str:>6} ${r['atr']:>6.2f}  "
        f"{pdv_color}{pdv:<22}{RESET}"
    )


def display_results(results: List[dict], analysis_date: date):
    """Display all output sections."""

    scoreable = [r for r in results if r.get("score", 0) > 0]
    aligned_inside_only = [
        r for r in scoreable
        if r.get("pdv_alignment") == Alignment.ALIGNED_INSIDE.value
    ]

    # ── Section 1: Top 10 Bull ──
    bulls = sorted(
        [r for r in aligned_inside_only if r["direction"] == "BULL"],
        key=lambda r: r["score"], reverse=True,
    )[:10]

    print_header(f"TOP 10 BULL — Aligned (Inside) — {analysis_date}", BULL_COLOR)
    if bulls:
        print_table_header()
        for i, r in enumerate(bulls, 1):
            print_row(i, r, BULL_COLOR)
    else:
        print(f"  {DIM}  No qualifying Bull tickers found{RESET}")

    # ── Section 2: Top 10 Bear ──
    bears = sorted(
        [r for r in aligned_inside_only if r["direction"] == "BEAR"],
        key=lambda r: r["score"], reverse=True,
    )[:10]

    print_header(f"TOP 10 BEAR — Aligned (Inside) — {analysis_date}", BEAR_COLOR)
    if bears:
        print_table_header()
        for i, r in enumerate(bears, 1):
            print_row(i, r, BEAR_COLOR)
    else:
        print(f"  {DIM}  No qualifying Bear tickers found{RESET}")

    # ── Section 3: All Aligned (Inside) ──
    all_aligned_inside = [
        r for r in results
        if r.get("pdv_alignment") == Alignment.ALIGNED_INSIDE.value
    ]
    all_aligned_inside.sort(key=lambda r: (-r.get("score", 0), r["ticker"]))

    print_header(
        f"ALL ALIGNED (INSIDE) — {len(all_aligned_inside)} tickers — {analysis_date}",
        CYAN,
    )
    if all_aligned_inside:
        print_table_header()
        for i, r in enumerate(all_aligned_inside, 1):
            dc = BULL_COLOR if r["direction"] == "BULL" else BEAR_COLOR
            print_row(i, r, dc)
    else:
        print(f"  {DIM}  No tickers with Aligned (Inside){RESET}")

    # ── Section 4: All Aligned (Outside) ──
    all_aligned_outside = [
        r for r in results
        if r.get("pdv_alignment") == Alignment.ALIGNED_OUTSIDE.value
    ]
    all_aligned_outside.sort(key=lambda r: (-r.get("score", 0), r["ticker"]))

    print_header(
        f"ALL ALIGNED (OUTSIDE) — {len(all_aligned_outside)} tickers — {analysis_date}",
        YELLOW,
    )
    if all_aligned_outside:
        print_table_header()
        for i, r in enumerate(all_aligned_outside, 1):
            dc = BULL_COLOR if r["direction"] == "BULL" else BEAR_COLOR
            print_row(i, r, dc)
    else:
        print(f"  {DIM}  No tickers with Aligned (Outside){RESET}")

    # ── Summary ──
    total = len(results)
    bull_count = sum(1 for r in results if r["direction"] == "BULL")
    bear_count = sum(1 for r in results if r["direction"] == "BEAR")
    ai_count = len(all_aligned_inside)
    ao_count = len(all_aligned_outside)
    nai = sum(1 for r in results if r.get("pdv_alignment") == Alignment.NOT_ALIGNED_INSIDE.value)
    nao = sum(1 for r in results if r.get("pdv_alignment") == Alignment.NOT_ALIGNED_OUTSIDE.value)
    na = sum(1 for r in results if r.get("pdv_alignment") == "—")

    print(f"\n  {BOLD}{'=' * 90}{RESET}")
    print(f"  {BOLD}  SUMMARY — {analysis_date}{RESET}")
    print(f"  {BOLD}{'=' * 90}{RESET}")
    print(f"    Total scanned:          {total}")
    print(f"    {BULL_COLOR}Bull:{RESET}                    {bull_count}")
    print(f"    {BEAR_COLOR}Bear:{RESET}                    {bear_count}")
    print(f"    {BULL_COLOR}Aligned (Inside):{RESET}        {ai_count}")
    print(f"    {YELLOW}Aligned (Outside):{RESET}       {ao_count}")
    print(f"    {BEAR_COLOR}Not Aligned (Inside):{RESET}   {nai}")
    print(f"    {BEAR_COLOR}Not Aligned (Outside):{RESET}  {nao}")
    print(f"    {DIM}No PDV data:{RESET}              {na}")
    print(f"  {BOLD}{'=' * 90}{RESET}\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Historical Structure Screener — simulates scan at 08:00 ET",
    )
    parser.add_argument(
        "date", nargs="?", default=None,
        help="Analysis date as YYYY-MM-DD (prompted if not provided)",
    )
    parser.add_argument(
        "ticker_list", nargs="?", default=None,
        help="Ticker list: SP500, NASDAQ100, DOW30, RUSSELL, ALL (default: SP500)",
    )
    parser.add_argument(
        "--workers", type=int, default=10,
        help="Number of parallel workers (default: 10)",
    )
    args = parser.parse_args()

    # Prompt for date
    date_str = args.date
    if not date_str:
        date_str = input("\n  Enter analysis date (YYYY-MM-DD): ").strip()
        if not date_str:
            print("  No date provided. Exiting.")
            return

    try:
        analysis_date = date.fromisoformat(date_str)
    except ValueError:
        print(f"  Invalid date format: {date_str}. Use YYYY-MM-DD.")
        return

    # Ticker list
    list_name = (args.ticker_list or "").upper()
    if not list_name:
        list_name = input(
            "  Enter ticker list [SP500/NASDAQ100/DOW30/RUSSELL/ALL] (default SP500): "
        ).strip().upper()
    if not list_name:
        list_name = "SP500"

    ticker_list = TICKER_LISTS.get(list_name)
    if ticker_list is None:
        print(f"  Unknown ticker list: {list_name}. Options: {', '.join(TICKER_LISTS.keys())}")
        return

    print(f"\n  {BOLD}Historical Structure Screener{RESET}")
    print(f"  {DIM}Date:        {analysis_date}{RESET}")
    print(f"  {DIM}Ticker List: {list_name}{RESET}")
    print(f"  {DIM}Workers:     {args.workers}{RESET}")

    results = run_scan(analysis_date, ticker_list, args.workers)
    display_results(results, analysis_date)


if __name__ == "__main__":
    main()
