"""
================================================================================
EPOCH TRADING SYSTEM - Full Application Pipeline Test
Interactive terminal test for end-to-end analysis with visual output.
XIII Trading LLC
================================================================================

Usage:
    python 15_testing/01_application_test/application/test_application.py
    python 15_testing/01_application_test/application/test_application.py AAPL 2026-03-14

Description:
    Runs the complete Market Screener -> Pre-Market Report workflow for a
    single ticker outside of market hours, using Max Volume (6-Month Lookback)
    as the default anchor preset.

    Steps:
    1. Prompt user for ticker and analysis date
    2. Set data cutoff to 09:00 ET on analysis date (pre-market mode)
    3. Resolve Max Volume anchor via 6-month lookback
    4. Run the 6-stage pipeline for the ticker only:
       - Market Structure (D1/H4/H1/M15)
       - Bar Data (OHLC, ATR, Camarilla, Options)
       - HVN POC Identification (top 10 by volume)
       - Zone Confluence Calculation
       - Zone Filtering & Tier Classification
       - Setup Analysis (Primary + Secondary)
    5. Calculate H4 Supply & Demand zones (3-ATR filter from 08:00 price)
    6. Fetch H1 candle data and build volume profile
    7. Generate the pre-market report visualization (1920x1080 PNG)
       - VbP + Primary/Secondary setups + H4 S/D zones
    8. Save to exports/ and open the image

    All calculations use the production code in 00_shared/ and 01_application/.
    Nothing is recreated or duplicated.

Output:
    PNG image saved to:
    15_testing/01_application_test/application/exports/{TICKER}_{YYYYMMDD}.png
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from math import floor, ceil

import numpy as np

# ============================================================================
# PATH SETUP - make 01_application imports work
# ============================================================================

TEST_DIR = Path(__file__).parent
EXPORTS_DIR = TEST_DIR / "exports"

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # Method_v1/
APP_DIR = PROJECT_ROOT / "01_application"

# Add 01_application to sys.path (mirrors app.py setup)
# The app's own modules (config, data, calculators, etc.) live here
sys.path.insert(0, str(APP_DIR))
# Add project root so shared.* imports work
sys.path.insert(0, str(PROJECT_ROOT))

# Change working directory so relative imports within 01_application resolve
os.chdir(str(APP_DIR))

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("test_application")

# ============================================================================
# TERMINAL COLORS
# ============================================================================

class C:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


def header(text: str):
    """Print a section header."""
    width = 70
    print(f"\n{C.CYAN}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{C.RESET}")


def subheader(text: str):
    """Print a subsection header."""
    print(f"\n{C.YELLOW}--- {text} ---{C.RESET}")


def info(label: str, value: str, color: str = C.WHITE):
    """Print a labeled value."""
    print(f"  {C.GRAY}{label:<25}{C.RESET}{color}{value}{C.RESET}")


def success(msg: str):
    print(f"  {C.GREEN}[OK] {msg}{C.RESET}")


def error(msg: str):
    print(f"  {C.RED}[FAIL] {msg}{C.RESET}")


def direction_color(direction_str: str) -> str:
    """Get ANSI color for a direction string."""
    d = str(direction_str).upper()
    if "BULL" in d:
        return C.GREEN
    elif "BEAR" in d:
        return C.RED
    return C.YELLOW


# ============================================================================
# INPUT HANDLING
# ============================================================================

def get_inputs() -> tuple:
    """Get ticker and date from args or interactive prompt."""

    if len(sys.argv) >= 3:
        ticker = sys.argv[1].upper()
        date_str = sys.argv[2]
    elif len(sys.argv) == 2:
        ticker = sys.argv[1].upper()
        date_str = None
    else:
        ticker = None
        date_str = None

    if not ticker:
        ticker = input(f"\n{C.CYAN}Enter ticker symbol: {C.RESET}").strip().upper()
        if not ticker:
            print(f"{C.RED}No ticker provided. Exiting.{C.RESET}")
            sys.exit(1)

    if not date_str:
        default_date = date.today().strftime("%Y-%m-%d")
        date_str = input(
            f"{C.CYAN}Enter analysis date (YYYY-MM-DD) [{default_date}]: {C.RESET}"
        ).strip()
        if not date_str:
            date_str = default_date

    try:
        analysis_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"{C.RED}Invalid date format: {date_str}. Use YYYY-MM-DD.{C.RESET}")
        sys.exit(1)

    return ticker, analysis_date


# ============================================================================
# DATA FETCHING (candles + volume profile for chart)
# ============================================================================

def fetch_candle_data(ticker: str, analysis_date: date, end_timestamp: datetime,
                      n_bars: int = 120):
    """Fetch H1 candles for the candlestick chart - mirrors ReportWorker._fetch_candle_data."""
    from data.polygon_client import PolygonClient
    client = PolygonClient()

    days_needed = max(30, (n_bars * 60) // (6.5 * 60) + 10)
    start_date = analysis_date - timedelta(days=days_needed)

    df = client.fetch_minute_bars(
        ticker=ticker,
        start_date=start_date,
        multiplier=60,
        end_timestamp=end_timestamp
    )

    if df.empty:
        return df

    df = df.tail(n_bars).copy()
    df.set_index('timestamp', inplace=True)
    return df


def build_volume_profile(ticker: str, anchor_date: date, end_timestamp: datetime):
    """Build M15 volume profile - mirrors ReportWorker._build_volume_profile."""
    from data.polygon_client import PolygonClient
    client = PolygonClient()
    import pandas as pd

    df = client.fetch_minute_bars_chunked(
        ticker=ticker,
        start_date=anchor_date,
        multiplier=15,
        chunk_days=30,
        end_timestamp=end_timestamp
    )

    if df.empty:
        return {}

    volume_profile = {}
    granularity = 0.01

    for _, bar in df.iterrows():
        bar_low = bar['low']
        bar_high = bar['high']
        bar_volume = bar['volume']

        if bar_volume <= 0 or bar_high <= bar_low:
            continue
        if pd.isna(bar_low) or pd.isna(bar_high) or pd.isna(bar_volume):
            continue

        low_level = floor(bar_low / granularity) * granularity
        high_level = ceil(bar_high / granularity) * granularity
        num_levels = int(round((high_level - low_level) / granularity)) + 1

        if num_levels <= 0:
            continue

        volume_per_level = bar_volume / num_levels
        current = low_level
        for _ in range(num_levels):
            price_key = round(current, 2)
            volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
            current += granularity

    return volume_profile


# ============================================================================
# H4 SUPPLY & DEMAND ZONES
# ============================================================================

ET_TIMEZONE = ZoneInfo("America/New_York")
H4_LOOKBACK_DAYS = 180
ATR_FILTER_MULT = 3.0


def fetch_h4_zones(ticker: str, analysis_date: date):
    """Calculate H4 supply/demand zones for the ticker.

    Returns (H4SupplyDemandResult, price_0800, d1_atr) or (None, None, None) on failure.
    """
    from shared.calculations.h4_supply_demand import calculate_h4_zones
    from data.polygon_client import PolygonClient
    import pandas as pd

    client = PolygonClient()

    # Price at 08:00 ET
    end_ts = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day,
        8, 0, 0, tzinfo=ET_TIMEZONE,
    )
    start_date_price = analysis_date - timedelta(days=1)
    df_price = client.fetch_minute_bars(ticker, start_date_price, multiplier=5, end_timestamp=end_ts)
    if df_price is None or df_price.empty:
        df_price = client.fetch_hourly_bars(ticker, start_date_price, end_timestamp=end_ts)
    price_0800 = round(float(df_price.iloc[-1]["close"]), 2) if df_price is not None and not df_price.empty else None

    # D1 ATR (14-period)
    period = 14
    lookback_days = period * 2 + 10
    start_date_atr = analysis_date - timedelta(days=lookback_days)
    df_daily = client.fetch_daily_bars(ticker, start_date_atr, analysis_date)
    d1_atr = None
    if df_daily is not None and not df_daily.empty and len(df_daily) >= period + 1:
        highs = df_daily["high"].values
        lows = df_daily["low"].values
        closes = df_daily["close"].values
        tr = np.zeros(len(df_daily))
        tr[0] = highs[0] - lows[0]
        for i in range(1, len(df_daily)):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        d1_atr = round(float(np.mean(tr[-period:])), 4)

    # H4 bars
    start_date_h4 = analysis_date - timedelta(days=H4_LOOKBACK_DAYS)
    df_h4 = client.fetch_4h_bars(ticker, start_date_h4, end_timestamp=end_ts)
    if df_h4 is None or df_h4.empty:
        return None, price_0800, d1_atr

    # Calculate zones
    result = calculate_h4_zones(
        df_h4,
        ticker=ticker,
        d1_atr=d1_atr,
        atr_filter=ATR_FILTER_MULT,
    )
    return result, price_0800, d1_atr


# ============================================================================
# MAIN
# ============================================================================

def main():
    import matplotlib
    matplotlib.use('Agg')

    header("EPOCH TRADING SYSTEM - Full Application Pipeline Test")

    ticker, analysis_date = get_inputs()
    eastern = ZoneInfo("America/New_York")

    # Data cutoff: 08:00 ET on the analysis date (pre-market)
    # This means last complete H1 bar is 07:00–08:00 ET
    # Polygon end_timestamp filter is exclusive, so we use 09:00 ET
    # to include the 08:00-09:00 bar (matching Pre-Market mode)
    end_timestamp = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day,
        9, 0, 0, tzinfo=eastern
    )

    info("Ticker", ticker, C.BOLD + C.WHITE)
    info("Analysis Date", str(analysis_date))
    info("Data Cutoff", f"{end_timestamp.strftime('%Y-%m-%d %H:%M')} ET (Pre-Market)")

    # ------------------------------------------------------------------
    # Step 1: Resolve Max Volume Anchor
    # ------------------------------------------------------------------
    subheader("Step 1/7 - Resolving Max Volume Anchor (6-month lookback)")
    t0 = time.time()

    from calculators.anchor_resolver import find_max_volume_anchor

    anchor_date, anchor_meta = find_max_volume_anchor(
        ticker=ticker,
        analysis_date=analysis_date
    )

    info("Anchor Date", str(anchor_date), C.BOLD + C.CYAN)
    info("Max Volume", f"{anchor_meta['max_volume']:,.0f}")
    if anchor_meta.get('second_volume'):
        info("2nd Volume", f"{anchor_meta['second_volume']:,.0f}")
    info("Exceeds 20% Threshold",
         f"{'Yes' if anchor_meta.get('exceeds_threshold') else 'No'}",
         C.GREEN if anchor_meta.get('exceeds_threshold') else C.YELLOW)
    info("Bars Checked", str(anchor_meta.get('bars_checked', 0)))
    success(f"Anchor resolved in {time.time() - t0:.1f}s")

    # ------------------------------------------------------------------
    # Step 2: Run Pipeline (ticker only, no index tickers)
    # ------------------------------------------------------------------
    subheader("Step 2/7 - Running Analysis Pipeline")
    t1 = time.time()

    from core.pipeline_runner import PipelineRunner

    runner = PipelineRunner()

    try:
        result = runner._process_single_ticker(
            ticker=ticker,
            anchor_date=anchor_date,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp
        )
    except Exception as e:
        error(f"Pipeline failed: {e}")
        sys.exit(1)

    if not result.get("success"):
        error(f"Pipeline failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    pipeline_time = time.time() - t1
    success(f"Pipeline completed in {pipeline_time:.1f}s")

    # ------------------------------------------------------------------
    # Step 3: Display Pipeline Results Summary
    # ------------------------------------------------------------------
    subheader("Step 3/7 - Pipeline Results Summary")

    # Price & Direction
    direction = result.get("direction", "N/A")
    dc = direction_color(direction)
    info("Price", f"${result.get('price', 0):.2f}", C.BOLD + C.WHITE)
    info("Composite Direction", direction, dc)

    # Market Structure
    ms = result.get("market_structure", {})
    if ms:
        print(f"\n  {C.BOLD}Market Structure:{C.RESET}")
        for tf in ["d1", "h4", "h1", "m15"]:
            tf_data = ms.get(tf, {})
            if isinstance(tf_data, dict):
                d = tf_data.get("direction", "-")
                d_str = str(d).replace("Direction.", "").replace("_PLUS", "+")
                s = tf_data.get("strong")
                w = tf_data.get("weak")
                dc_tf = direction_color(d_str)
                strong_str = f"${s:.2f}" if s else "-"
                weak_str = f"${w:.2f}" if w else "-"
                print(f"    {C.GRAY}{tf.upper():<6}{C.RESET}"
                      f"{dc_tf}{d_str:<12}{C.RESET}"
                      f"  Strong: {C.WHITE}{strong_str:<10}{C.RESET}"
                      f"  Weak: {C.WHITE}{weak_str}{C.RESET}")

    # Zones
    filtered_zones = result.get("filtered_zones", [])
    info("Total Filtered Zones", str(len(filtered_zones)))
    info("Bull POC", result.get("bull_poc", "N/A"))
    info("Bear POC", result.get("bear_poc", "N/A"))

    if filtered_zones:
        print(f"\n  {C.BOLD}Zones:{C.RESET}")
        for z in filtered_zones:
            zone_id = z.get("zone_id", "?")
            tier = str(z.get("tier", "")).replace("Tier.", "")
            rank = str(z.get("rank", "")).replace("Rank.", "")
            poc = z.get("hvn_poc", 0)
            high = z.get("zone_high", 0)
            low = z.get("zone_low", 0)
            score = z.get("score", 0)
            overlaps = z.get("overlaps", 0)

            tier_color = C.GREEN if "T3" in tier else C.YELLOW if "T2" in tier else C.RED
            print(f"    {C.GRAY}{zone_id:<12}{C.RESET}"
                  f"{tier_color}{tier:<4}{C.RESET} "
                  f"{C.BLUE}{rank:<4}{C.RESET} "
                  f"POC: {C.WHITE}${poc:.2f}{C.RESET}  "
                  f"[${low:.2f} - ${high:.2f}]  "
                  f"Score: {score:.1f}  Overlaps: {overlaps}")

    # Setups
    primary = result.get("primary_setup")
    secondary = result.get("secondary_setup")

    if primary:
        print(f"\n  {C.BOLD}Primary Setup:{C.RESET}")
        p_dir = str(primary.get("direction", "")).replace("Direction.", "").replace("_PLUS", "+")
        info("Direction", p_dir, direction_color(p_dir))
        info("Zone", f"${primary.get('zone_low', 0):.2f} - ${primary.get('zone_high', 0):.2f}")
        info("Target", f"${primary.get('target', 0):.2f}" if primary.get('target') else "N/A")
        info("Risk:Reward", f"{primary.get('risk_reward', 0):.2f}" if primary.get('risk_reward') else "N/A")
        info("Tier", str(primary.get("tier", "")).replace("Tier.", ""))

    if secondary:
        print(f"\n  {C.BOLD}Secondary Setup:{C.RESET}")
        s_dir = str(secondary.get("direction", "")).replace("Direction.", "").replace("_PLUS", "+")
        info("Direction", s_dir, direction_color(s_dir))
        info("Zone", f"${secondary.get('zone_low', 0):.2f} - ${secondary.get('zone_high', 0):.2f}")
        info("Target", f"${secondary.get('target', 0):.2f}" if secondary.get('target') else "N/A")
        info("Risk:Reward", f"{secondary.get('risk_reward', 0):.2f}" if secondary.get('risk_reward') else "N/A")

    # ------------------------------------------------------------------
    # Step 4: H4 Supply & Demand Zones
    # ------------------------------------------------------------------
    subheader("Step 4/7 - Calculating H4 Supply & Demand Zones")
    t_h4 = time.time()

    h4_result, h4_price_0800, h4_d1_atr = fetch_h4_zones(ticker, analysis_date)

    if h4_result and not h4_result.error:
        success(f"H4 zones calculated in {time.time() - t_h4:.1f}s")
        info("H4 Bars", str(h4_result.bar_count))
        info("Supply Zones", str(h4_result.total_supply))
        info("Demand Zones", str(h4_result.total_demand))
        if h4_price_0800:
            info("Price @ 08:00", f"${h4_price_0800:.2f}")
        if h4_d1_atr:
            info("D1 ATR", f"${h4_d1_atr:.2f}")
            band_lo = (h4_price_0800 or 0) - h4_d1_atr * ATR_FILTER_MULT
            band_hi = (h4_price_0800 or 0) + h4_d1_atr * ATR_FILTER_MULT
            info("ATR Filter Band", f"${band_lo:.2f} - ${band_hi:.2f}")

        if h4_result.supply_zones:
            print(f"\n  {C.BOLD}H4 Supply Zones (resistance):{C.RESET}")
            for z in sorted(h4_result.supply_zones, key=lambda z: z.midpoint, reverse=True):
                print(f"    {C.RED}{z.zone_id:<4}{C.RESET}  "
                      f"${z.bottom:.2f} - ${z.top:.2f}  "
                      f"(pivot ${z.pivot_price:.2f})  "
                      f"touches: {z.recent_touches}  flips: {z.recent_flips}")

        if h4_result.demand_zones:
            print(f"\n  {C.BOLD}H4 Demand Zones (support):{C.RESET}")
            for z in sorted(h4_result.demand_zones, key=lambda z: z.midpoint, reverse=True):
                print(f"    {C.GREEN}{z.zone_id:<4}{C.RESET}  "
                      f"${z.bottom:.2f} - ${z.top:.2f}  "
                      f"(pivot ${z.pivot_price:.2f})  "
                      f"touches: {z.recent_touches}  flips: {z.recent_flips}")

        if h4_result.exhausted_zones:
            print(f"\n  {C.BOLD}H4 Exhausted Zones:{C.RESET}")
            for z in sorted(h4_result.exhausted_zones, key=lambda z: z.midpoint, reverse=True):
                ztype = "S" if z.zone_type.value == "Supply" else "D"
                print(f"    {C.GRAY}{z.zone_id:<4} ({ztype}){C.RESET}  "
                      f"${z.bottom:.2f} - ${z.top:.2f}  "
                      f"touches: {z.recent_touches}/{z.touches}  "
                      f"flips: {z.recent_flips}/{z.flips}")

        # Store H4 zones in result for chart builder
        result["h4_zones"] = h4_result
    else:
        if h4_result and h4_result.error:
            error(f"H4 zones failed: {h4_result.error}")
        else:
            error("H4 zones: No H4 data available")

    # ------------------------------------------------------------------
    # Step 5: Fetch Chart Data
    # ------------------------------------------------------------------
    subheader("Step 5/7 - Fetching Chart Data (H1 candles + M15 volume profile)")
    t2 = time.time()

    print(f"  Fetching H1 candles...")
    candle_data = fetch_candle_data(ticker, analysis_date, end_timestamp)
    print(f"  -> {len(candle_data)} H1 bars loaded")

    print(f"  Building volume profile from {anchor_date}...")
    volume_profile = build_volume_profile(ticker, anchor_date, end_timestamp)
    print(f"  -> {len(volume_profile)} price levels in volume profile")

    success(f"Chart data fetched in {time.time() - t2:.1f}s")

    # ------------------------------------------------------------------
    # Step 6: Generate Pre-Market Report Visualization
    # ------------------------------------------------------------------
    subheader("Step 6/7 - Generating Pre-Market Report Visualization")
    t3 = time.time()

    from ui.tabs.pre_market_report import PreMarketChartBuilder

    builder = PreMarketChartBuilder()
    builder.build(
        ticker=ticker,
        anchor_date=anchor_date,
        result=result,
        index_structures=[],
        candle_data=candle_data,
        volume_profile=volume_profile,
        notes=""
    )

    # Save to exports
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = analysis_date.strftime("%Y%m%d")
    output_path = EXPORTS_DIR / f"{ticker}_{date_str}.png"

    img_bytes = builder.to_bytes()
    builder.close()

    with open(output_path, "wb") as f:
        f.write(img_bytes)

    success(f"Report generated in {time.time() - t3:.1f}s")
    info("Output", str(output_path), C.BOLD + C.GREEN)
    info("File Size", f"{len(img_bytes) / 1024:.0f} KB")

    # ------------------------------------------------------------------
    # Step 7: Summary
    # ------------------------------------------------------------------
    total_time = time.time() - t0
    header("TEST COMPLETE")
    info("Ticker", ticker, C.BOLD + C.WHITE)
    info("Analysis Date", str(analysis_date))
    info("Anchor Date", str(anchor_date), C.CYAN)
    info("Direction", direction, direction_color(direction))
    info("VbP Zones", str(len(filtered_zones)))
    h4_z = result.get("h4_zones")
    if h4_z and not h4_z.error:
        info("H4 Supply Zones", str(h4_z.total_supply), C.RED)
        info("H4 Demand Zones", str(h4_z.total_demand), C.GREEN)
    info("Total Time", f"{total_time:.1f}s")
    info("Output File", str(output_path), C.GREEN)

    # Try to open the image
    print(f"\n  {C.DIM}Opening image...{C.RESET}")
    try:
        os.startfile(str(output_path))
    except Exception:
        print(f"  {C.DIM}(Could not auto-open - open the file manually){C.RESET}")

    print()


if __name__ == "__main__":
    main()
