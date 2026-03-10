"""
================================================================================
EPOCH TRADING SYSTEM - Structure Screener Test
CLI test harness for the D1 structure screener with historical sim date.
XIII Trading LLC
================================================================================

Usage:
    python 15_testing/01_application_test/test_structure_screener.py

Interactive prompts will ask for sim date and filter preferences.
Current price is the 09:00 ET 1-minute bar close.
RVOL compares sim-date 04:00-09:00 volume to trailing 12-day average.

Run from the Epoch_v3 root directory.
================================================================================
"""

import sys
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List
from zoneinfo import ZoneInfo

# ── Path setup ────────────────────────────────────────────────────────────────
EPOCH_V3 = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(EPOCH_V3))
sys.path.insert(0, str(EPOCH_V3 / "01_application"))

from shared.indicators.structure import get_market_structure
from shared.indicators.config import CONFIG
from data.polygon_client import PolygonClient
from scanner import TickerManager, TickerList

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


# =============================================================================
# TERMINAL COLORS
# =============================================================================

BULL_COLOR = "\033[92m"    # green
BEAR_COLOR = "\033[91m"    # red
AMBER_COLOR = "\033[93m"   # yellow/amber
BLUE_COLOR = "\033[94m"    # blue
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

STATE_COLORS = {
    "Bull": BULL_COLOR,
    "Bull (Low)": BULL_COLOR,
    "Bear": BEAR_COLOR,
    "Bear (High)": BEAR_COLOR,
    "Out - Strong": AMBER_COLOR,
    "Out - Weak": BLUE_COLOR,
    "Neutral": DIM,
}


# =============================================================================
# SCORING WEIGHTS (tunable)
# =============================================================================

W_STRUCTURE = 30   # Structure state quality
W_ALIGNMENT = 20   # D1 body alignment with direction
W_GAP = 20         # Overnight gap alignment
W_RVOL = 25        # Relative volume
W_ZONE = 10        # Price position within zone


# =============================================================================
# STATE CLASSIFICATION (mirrors structure_screener.py)
# =============================================================================

def classify_ticker(direction: int, strong: float, weak: float,
                    current_price: float) -> str:
    """
    Classify a ticker's position relative to its D1 structure.

    Returns one of: "Bull", "Bear", "Out - Strong", "Out - Weak", "Neutral",
                    "Bull (Low)", "Bear (High)"
    """
    if direction == 0 or strong is None:
        return "Neutral"

    if direction == 1:  # BULL
        if weak is not None:
            if current_price > weak:
                return "Out - Weak"
            if current_price < strong:
                return "Out - Strong"
            rng = weak - strong
            if rng > 0:
                pct = (current_price - strong) / rng
                if pct >= 0.20:
                    return "Bull"
                else:
                    return "Bull (Low)"
            return "Bull"
        else:
            if current_price < strong:
                return "Out - Strong"
            return "Bull"

    elif direction == -1:  # BEAR
        if weak is not None:
            if current_price < weak:
                return "Out - Weak"
            if current_price > strong:
                return "Out - Strong"
            rng = strong - weak
            if rng > 0:
                pct = (strong - current_price) / rng
                if pct >= 0.20:
                    return "Bear"
                else:
                    return "Bear (High)"
            return "Bear"
        else:
            if current_price > strong:
                return "Out - Strong"
            return "Bear"

    return "Neutral"


# =============================================================================
# ATR
# =============================================================================

def quick_atr(df, period: int = 14) -> float:
    """Lightweight EMA-based ATR from a daily DataFrame."""
    if len(df) < 2:
        return 0.0
    df2 = df.copy()
    df2["h_l"] = df2["high"] - df2["low"]
    df2["h_pc"] = (df2["high"] - df2["close"].shift(1)).abs()
    df2["l_pc"] = (df2["low"] - df2["close"].shift(1)).abs()
    df2["tr"] = df2[["h_l", "h_pc", "l_pc"]].max(axis=1)
    return float(df2["tr"].ewm(span=period, adjust=False).mean().iloc[-1])


# =============================================================================
# MINUTE DATA: 09:00 PRICE + RVOL
# =============================================================================

def fetch_minute_data(ticker: str, polygon: PolygonClient,
                      sim_date: date) -> dict:
    """
    Fetch minute bars to get:
      - Last bar close at or before 09:00 ET (current_price)
      - RVOL%: sim-date 04:00-09:00 volume vs trailing 12-day average

    Returns dict with keys: price_0900, rvol_pct, today_vol, avg_vol
    """
    result = {"price_0900": None, "rvol_pct": None}

    try:
        # Fetch minute bars covering sim_date + 12 trailing trading days
        # (~20 calendar days back covers weekends/holidays)
        rvol_start = sim_date - timedelta(days=25)
        min_df = polygon.fetch_minute_bars(ticker, rvol_start, sim_date)

        if min_df.empty:
            return result

        # Convert UTC timestamps to ET
        min_df["et_time"] = min_df["timestamp"].dt.tz_convert(ET)
        min_df["bar_date"] = min_df["et_time"].dt.date
        min_df["bar_hour"] = min_df["et_time"].dt.hour
        min_df["bar_minute"] = min_df["et_time"].dt.minute

        # ── Price at ~09:00 on sim_date ──
        # Use last bar at or before 09:00 (premarket gaps may skip exact minute)
        sim_bars = min_df[min_df["bar_date"] == sim_date].copy()
        if not sim_bars.empty:
            pre_0901 = sim_bars[
                (sim_bars["bar_hour"] < 9) |
                ((sim_bars["bar_hour"] == 9) & (sim_bars["bar_minute"] == 0))
            ]
            if not pre_0901.empty:
                result["price_0900"] = float(pre_0901["close"].iloc[-1])

        # ── RVOL: 04:00-09:00 volume ──
        premarket = min_df[
            (min_df["bar_hour"] >= 4) & (min_df["bar_hour"] < 9)
        ]
        if premarket.empty:
            return result

        daily_pm_vol = premarket.groupby("bar_date")["volume"].sum()

        today_vol = daily_pm_vol.get(sim_date, 0)

        # Trailing 12 trading days (exclude sim_date)
        prior_vols = daily_pm_vol.drop(sim_date, errors="ignore")
        prior_vols = prior_vols.sort_index().tail(12)

        if len(prior_vols) > 0 and prior_vols.mean() > 0:
            avg_vol = prior_vols.mean()
            result["rvol_pct"] = round((today_vol / avg_vol) * 100, 0)
        else:
            result["rvol_pct"] = 0

    except Exception as exc:
        logger.debug(f"Minute data skip {ticker}: {exc}")

    return result


# =============================================================================
# SINGLE TICKER PROCESSING
# =============================================================================

def process_ticker(ticker: str, polygon: PolygonClient,
                   d1_start: date, d1_end: date, sim_date: date,
                   min_price: float, min_atr: float) -> Optional[dict]:
    """Process one ticker: D1 structure + 09:00 price + RVOL."""
    try:
        # ── Phase 1: D1 structure ──
        df = polygon.fetch_daily_bars(ticker, d1_start, d1_end)
        if df.empty or len(df) < 20:
            return None

        d1_close = float(df["close"].iloc[-1])

        # Price/ATR filters use D1 close (fast screening)
        if d1_close < min_price:
            return None

        atr = quick_atr(df)
        if atr < min_atr:
            return None

        # Prior day body check (uses last two D1 bars)
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

        last_bar_date = df["date"].iloc[-1]

        # Run v3 market structure
        structure = get_market_structure(df)

        # ── Phase 2: 09:00 price + RVOL ──
        minute_data = fetch_minute_data(ticker, polygon, sim_date)

        # Use 09:00 bar close if available, otherwise D1 close
        current_price = minute_data["price_0900"] or d1_close
        price_source = "09:00" if minute_data["price_0900"] else "D1"

        # Overnight gap: 09:00 price vs D1 close
        if price_source == "09:00" and d1_close > 0:
            gap_pct = round((current_price - d1_close) / d1_close * 100, 2)
        else:
            gap_pct = 0.0

        # Classify using current_price (09:00 bar when available)
        state = classify_ticker(
            structure.direction,
            structure.strong_level,
            structure.weak_level,
            current_price,
        )

        return {
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
            "last_bar_date": last_bar_date,
            "rvol_pct": minute_data["rvol_pct"],
        }
    except Exception as exc:
        logger.debug(f"Skip {ticker}: {exc}")
        return None


# =============================================================================
# SCORING ENGINE
# =============================================================================

def score_structure(state: str) -> int:
    """Score structure state quality (0-30 pts)."""
    return {
        "Bull": W_STRUCTURE, "Bear": W_STRUCTURE,
        "Bull (Low)": 15, "Bear (High)": 15,
        "Out - Weak": 5,
        "Out - Strong": 0, "Neutral": 0,
    }.get(state, 0)


def score_alignment(direction: str, prior_d1_body: str) -> int:
    """Score D1 body alignment with structure direction (0-20 pts)."""
    if prior_d1_body == "Inside":
        return 10  # Neutral — no directional signal
    if direction == "BULL":
        return W_ALIGNMENT if prior_d1_body == "Above" else 5
    elif direction == "BEAR":
        return W_ALIGNMENT if prior_d1_body == "Below" else 5
    return 0


def score_gap(direction: str, gap_pct: float, price_source: str) -> int:
    """Score overnight gap alignment (0-20 pts)."""
    if price_source == "D1":
        return 10  # No 09:00 bar — neutral

    if direction == "BULL":
        if gap_pct >= 1.0:   return 20
        if gap_pct >= 0.5:   return 15
        if gap_pct >= 0.0:   return 10
        if gap_pct >= -0.5:  return 5
        return 0
    elif direction == "BEAR":
        if gap_pct <= -1.0:  return 20
        if gap_pct <= -0.5:  return 15
        if gap_pct <= 0.0:   return 10
        if gap_pct <= 0.5:   return 5
        return 0
    return 0


def score_rvol(rvol_pct) -> int:
    """Score relative volume (0-25 pts, tier-based)."""
    if rvol_pct is None or rvol_pct <= 0:
        return 0
    if rvol_pct < 50:   return 5
    if rvol_pct < 100:  return 10
    if rvol_pct < 150:  return 15
    if rvol_pct < 200:  return 20
    return W_RVOL  # 25


def score_zone(state: str, price: float, strong, weak,
               direction: str) -> int:
    """Score price position within the zone (0-10 pts)."""
    if state in ("Out - Weak", "Out - Strong", "Neutral"):
        return 0

    if weak is None:
        return 5  # Pending weak — trend mode, neutral

    if strong is None:
        return 0

    # Calculate zone percentage
    if direction == "BULL":
        rng = weak - strong
    elif direction == "BEAR":
        rng = strong - weak
    else:
        return 0

    if rng <= 0:
        return 5

    if direction == "BULL":
        zone_pct = (price - strong) / rng
    else:
        zone_pct = (strong - price) / rng

    zone_pct = max(0.0, min(1.0, zone_pct))

    if 0.20 <= zone_pct <= 0.45:  return 10  # Sweet spot
    if 0.45 < zone_pct <= 0.70:   return 7   # Mid zone
    if 0.70 < zone_pct <= 1.00:   return 4   # Near weak
    if 0.0 <= zone_pct < 0.20:    return 3   # Uncommitted
    return 0


def score_ticker(result: dict) -> dict:
    """Calculate composite score. Adds 'score' and 'score_detail' to result."""
    s = score_structure(result["state"])
    a = score_alignment(result["direction"], result["prior_d1_body"])
    g = score_gap(result["direction"], result.get("gap_pct", 0.0),
                  result.get("price_source", "D1"))
    r = score_rvol(result.get("rvol_pct"))
    z = score_zone(result["state"], result["price"],
                   result.get("strong"), result.get("weak"),
                   result["direction"])

    result["score"] = s + a + g + r + z
    result["score_detail"] = {"S": s, "A": a, "G": g, "R": r, "Z": z}
    return result


# =============================================================================
# DISPLAY
# =============================================================================

SHORTLIST_WIDTH = 94
TABLE_WIDTH = 90


def print_shortlist(results: List[dict], sim_date: date):
    """Print Top 10 Bull and Top 10 Bear shortlists with score breakdown."""
    scoreable = [r for r in results if r.get("score", 0) > 0]

    bulls = sorted([r for r in scoreable if r["direction"] == "BULL"],
                   key=lambda r: r["score"], reverse=True)[:10]
    bears = sorted([r for r in scoreable if r["direction"] == "BEAR"],
                   key=lambda r: r["score"], reverse=True)[:10]

    print(f"  {BOLD}{'=' * SHORTLIST_WIDTH}{RESET}")
    print(f"  {BOLD}  TOP 10 SHORTLIST — {sim_date}{RESET}")
    print(f"  {BOLD}{'=' * SHORTLIST_WIDTH}{RESET}")
    print()
    print(f"  {DIM}Score = S(tructure) + A(lignment) + G(ap) + R(VOL) + Z(one)  "
          f"max ~105{RESET}")
    print()

    for label, color, top_list in [
        ("BULL", BULL_COLOR, bulls),
        ("BEAR", BEAR_COLOR, bears),
    ]:
        print(f"  {color}{BOLD}  Top 10 {label}{RESET}")
        if not top_list:
            print(f"  {DIM}  No eligible tickers.{RESET}")
            print()
            continue

        print(f"  {'-' * SHORTLIST_WIDTH}")
        print(f"  {BOLD}  {'#':>2}  {'Ticker':<7} {'Price':>8}  "
              f"{'Score':>5}  "
              f"{'S':>2} {'A':>2} {'G':>2} {'R':>2} {'Z':>2}  "
              f"{'Gap%':>6}  {'RVOL%':>6}  {'State':<14}{RESET}")
        print(f"  {'-' * SHORTLIST_WIDTH}")

        for rank, r in enumerate(top_list, 1):
            sd = r.get("score_detail", {})
            sc = STATE_COLORS.get(r["state"], "")

            # Gap display
            if r.get("price_source") == "09:00":
                gap_str = f"{r.get('gap_pct', 0.0):+.1f}%"
            else:
                gap_str = "—"

            # RVOL display with color
            rvol = r.get("rvol_pct")
            if rvol is not None and rvol > 0:
                rvol_str = f"{rvol:.0f}%"
                if rvol >= 200:
                    rvol_disp = f"{BULL_COLOR}{rvol_str:>6}{RESET}"
                elif rvol >= 100:
                    rvol_disp = f"{rvol_str:>6}"
                else:
                    rvol_disp = f"{DIM}{rvol_str:>6}{RESET}"
            else:
                rvol_disp = f"{DIM}{'—':>6}{RESET}"

            line = (f"  {rank:>3}  {r['ticker']:<7} ${r['price']:>7.2f}  "
                    f"{r['score']:>5}  "
                    f"{sd.get('S',0):>2} {sd.get('A',0):>2} "
                    f"{sd.get('G',0):>2} {sd.get('R',0):>2} "
                    f"{sd.get('Z',0):>2}  "
                    f"{gap_str:>6}  {rvol_disp}  "
                    f"{sc}{r['state']:<14}{RESET}")
            print(line)

        print(f"  {'-' * SHORTLIST_WIDTH}")
        print()

def print_header(sim_date: date, d1_end: date, ticker_list: str,
                 hide_inside: bool):
    """Print scan header."""
    print()
    print(f"  {BOLD}{'=' * TABLE_WIDTH}{RESET}")
    print(f"  {BOLD}  Structure Screener — Sim {sim_date} @ 09:00 pre-market{RESET}")
    print(f"  {BOLD}{'=' * TABLE_WIDTH}{RESET}")
    print()
    print(f"  {DIM}D1 data through:{RESET}  {d1_end}  (prior day close)")
    print(f"  {DIM}Current price:{RESET}    Last bar close at or before 09:00 ET")
    print(f"  {DIM}RVOL window:{RESET}      04:00–09:00 ET vs trailing 12 days")
    print(f"  {DIM}Ticker list:{RESET}      {ticker_list}")
    print(f"  {DIM}Retrace %:{RESET}        {CONFIG.structure.retrace_pct:.0%}")
    print(f"  {DIM}Hide Inside D1:{RESET}   {'Yes' if hide_inside else 'No'}")
    print()


def print_results(results: List[dict], total_scanned: int, hide_inside: bool,
                  sim_date: date = None):
    """Print results table to terminal."""
    # Apply inside filter
    if hide_inside:
        filtered = [r for r in results if r["prior_d1_body"] != "Inside"]
    else:
        filtered = results

    # Sort by state priority then ticker
    state_order = {
        "Out - Strong": 0, "Out - Weak": 1,
        "Bull": 2, "Bear": 3,
        "Bull (Low)": 4, "Bear (High)": 5,
        "Neutral": 6,
    }
    filtered.sort(key=lambda r: (-r.get("score", 0),
                                    state_order.get(r["state"], 9),
                                    r["ticker"]))

    # Summary counts
    counts = {
        "Bull": sum(1 for r in filtered if r["state"] in ("Bull", "Bull (Low)")),
        "Bear": sum(1 for r in filtered if r["state"] in ("Bear", "Bear (High)")),
        "Out - Strong": sum(1 for r in filtered if r["state"] == "Out - Strong"),
        "Out - Weak": sum(1 for r in filtered if r["state"] == "Out - Weak"),
        "Neutral": sum(1 for r in filtered if r["state"] == "Neutral"),
    }

    # Price source stats
    p0900 = sum(1 for r in filtered if r.get("price_source") == "09:00")
    p_d1 = sum(1 for r in filtered if r.get("price_source") == "D1")

    print(f"  {BOLD}Summary:{RESET}  {len(filtered)} results"
          f"  (of {len(results)} matched / {total_scanned} scanned)")
    if hide_inside:
        hidden = len(results) - len(filtered)
        print(f"  {DIM}({hidden} hidden — inside prior day bar){RESET}")
    print(f"  {DIM}Price source: {p0900} @ 09:00 bar, {p_d1} @ D1 close fallback{RESET}")
    print()
    print(f"  {BULL_COLOR}Bull: {counts['Bull']}{RESET}  "
          f"{BEAR_COLOR}Bear: {counts['Bear']}{RESET}  "
          f"{AMBER_COLOR}Out-Strong: {counts['Out - Strong']}{RESET}  "
          f"{BLUE_COLOR}Out-Weak: {counts['Out - Weak']}{RESET}  "
          f"{DIM}Neutral: {counts['Neutral']}{RESET}")
    print()

    if not filtered:
        print(f"  {DIM}No results.{RESET}")
        print()
        return

    # ── Data boundary verification ──
    bar_dates = set(str(r["last_bar_date"]) for r in filtered if r.get("last_bar_date"))
    if bar_dates:
        max_bar = max(bar_dates)
        min_bar = min(bar_dates)

        if sim_date and max_bar >= str(sim_date):
            status = f"{BEAR_COLOR}LEAK DETECTED — data includes sim date or later{RESET}"
        else:
            status = f"{BULL_COLOR}OK — no data on or after sim date{RESET}"

        if max_bar == min_bar:
            print(f"  {BOLD}Data verification:{RESET}  Last bar = {max_bar}  |  {status}")
        else:
            print(f"  {BOLD}Data verification:{RESET}  Last bars = {min_bar} to {max_bar}"
                  f"  (varies — weekends/holidays)  |  {status}")
        print()

    # Table header
    hdr = (f"  {'Ticker':<8} {'Price':>8} {'Dir':<6} "
           f"{'Strong':>9} {'Weak':>9} {'State':<14} {'Prior D1':<10} "
           f"{'ATR':>7}  {'RVOL%':>6}  {'Gap%':>6}  {'Score':>5}")
    print(f"  {BOLD}{'-' * TABLE_WIDTH}{RESET}")
    print(f"  {BOLD}{hdr.strip()}{RESET}")
    print(f"  {BOLD}{'-' * TABLE_WIDTH}{RESET}")

    for r in filtered:
        color = STATE_COLORS.get(r["state"], "")
        strong_str = f"${r['strong']:.2f}" if r["strong"] is not None else "—"
        weak_str = f"${r['weak']:.2f}" if r["weak"] is not None else "pending"

        # RVOL coloring
        rvol = r.get("rvol_pct")
        if rvol is not None and rvol > 0:
            rvol_str = f"{rvol:.0f}%"
            if rvol >= 200:
                rvol_display = f"{BULL_COLOR}{rvol_str:>6}{RESET}"
            elif rvol >= 100:
                rvol_display = f"{rvol_str:>6}"
            else:
                rvol_display = f"{DIM}{rvol_str:>6}{RESET}"
        else:
            rvol_display = f"{DIM}{'—':>6}{RESET}"

        # Gap display
        if r.get("price_source") == "09:00":
            gap_str = f"{r.get('gap_pct', 0.0):+.1f}%"
        else:
            gap_str = f"{DIM}{'—':>6}{RESET}"

        score_str = f"{r.get('score', 0):>5}"

        line = (f"  {r['ticker']:<8} ${r['price']:>7.2f} {r['direction']:<6} "
                f"{strong_str:>9} {weak_str:>9} "
                f"{color}{r['state']:<14}{RESET} "
                f"{r['prior_d1_body']:<10} ${r['atr']:>6.2f}  "
                f"{rvol_display}  {gap_str:>6}  {score_str}")
        print(line)

    print(f"  {BOLD}{'-' * TABLE_WIDTH}{RESET}")
    print()


# =============================================================================
# INTERACTIVE PROMPTS
# =============================================================================

TICKER_LIST_MAP = {
    "sp500": TickerList.SP500,
    "nasdaq100": TickerList.NASDAQ100,
    "dow30": TickerList.DOW30,
    "russell2000": TickerList.RUSSELL2000,
    "all": TickerList.ALL_US_EQUITIES,
}


def prompt_user() -> dict:
    """Interactive terminal prompts for scan parameters."""
    print()
    print(f"  {BOLD}{'=' * TABLE_WIDTH}{RESET}")
    print(f"  {BOLD}  Structure Screener — Configuration{RESET}")
    print(f"  {BOLD}{'=' * TABLE_WIDTH}{RESET}")
    print()

    # ── Sim date ──
    today_str = date.today().strftime("%Y-%m-%d")
    date_input = input(f"  Sim date (YYYY-MM-DD) [{today_str}]: ").strip()
    if not date_input:
        sim_date = date.today()
    else:
        try:
            parts = date_input.split("-")
            sim_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            print(f"  {BEAR_COLOR}Invalid date format. Using today.{RESET}")
            sim_date = date.today()

    # ── Hide inside prior day ──
    filter_input = input(f"  Hide Inside Prior Day Bar? (Y/n) [Y]: ").strip().lower()
    hide_inside = filter_input != "n"

    print()

    return {
        "sim_date": sim_date,
        "hide_inside": hide_inside,
    }


# =============================================================================
# MAIN
# =============================================================================

def run(sim_date: date, ticker_list_name: str = "sp500",
        min_price: float = 10.0, min_atr: float = 2.0,
        hide_inside: bool = True, workers: int = 10,
        lookback_days: int = 365):
    """Run the structure screener for a given sim date."""

    # D1 data: pull through the day before sim_date
    # (at 09:00 the current day's D1 bar hasn't formed)
    d1_end = sim_date - timedelta(days=1)
    d1_start = d1_end - timedelta(days=lookback_days)

    ticker_list_enum = TICKER_LIST_MAP.get(ticker_list_name)
    if ticker_list_enum is None:
        print(f"  Unknown ticker list: {ticker_list_name}")
        print(f"  Available: {', '.join(TICKER_LIST_MAP.keys())}")
        return

    print_header(sim_date, d1_end, ticker_list_name, hide_inside)

    # Build ticker universe
    ticker_mgr = TickerManager()
    tickers = ticker_mgr.get_tickers(ticker_list_enum)
    total = len(tickers)
    print(f"  Scanning {total} tickers with {workers} workers...")
    print(f"  {DIM}(fetching D1 bars + 09:00 minute bar + RVOL per ticker){RESET}")
    print()

    polygon = PolygonClient()
    results: List[dict] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(process_ticker, t, polygon,
                        d1_start, d1_end, sim_date,
                        min_price, min_atr): t
            for t in tickers
        }
        for future in as_completed(futures):
            completed += 1
            ticker = futures[future]
            pct = int(completed / total * 100)
            print(f"\r  [{pct:3d}%] {completed}/{total} — {ticker:<8}", end="", flush=True)
            try:
                row = future.result()
                if row is not None:
                    results.append(row)
            except Exception:
                pass

    # Clear progress line
    print(f"\r  {'':70}")
    print()

    # Score all results
    for r in results:
        score_ticker(r)

    # Print shortlist first, then full results
    print_shortlist(results, sim_date)
    print_results(results, total, hide_inside, sim_date)


def main():
    params = prompt_user()

    run(
        sim_date=params["sim_date"],
        hide_inside=params["hide_inside"],
    )


if __name__ == "__main__":
    main()
