"""
Bucket C — Morning Runner
Screener Pipeline Build (Seed 004) — XIII Trading LLC

Runs manually before the session (~07:30 ET). Computes pre-market data
using bars from 16:00 ET prior day to 07:30 ET current day:
  - Pre-Market High (PMH)
  - Pre-Market Low (PML)
  - Pre-Market Volume Profile (PMPOC / PMVAH / PMVAL)
  - Current price at trigger time

Also queries nightly data from Supabase to confirm it's present.

Pre-market window: 16:00 ET prior day -> 07:30 ET current day.

Usage:
    Called by bucket_runner.py --bucket morning
"""
import logging
import sys
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


def run_morning(
    ticker_inputs: List[Dict],
    analysis_date: date,
) -> Dict:
    """
    Run morning pre-market calculations for all universe tickers.

    Fetches M1 bars for the pre-market window (16:00 ET prior day to
    07:30 ET current day), computes PMH/PML/PMPOC/PMVAH/PMVAL, and
    writes pm_* columns to bar_data in Supabase.

    Requires Bucket B (nightly) to have run first — bar_data rows must
    exist for the analysis date.

    Args:
        ticker_inputs: List of dicts with 'ticker' and 'anchor_date'
        analysis_date: Today's date

    Returns:
        Dict with success/fail counts and errors
    """
    from data import get_polygon_client
    from shared.indicators.core.volume_profile import (
        _build_profile_core,
        _find_poc_index,
        _calculate_poc_price,
        _calculate_value_area,
    )

    start_time = time.time()
    print("\n" + "=" * 60)
    print("BUCKET C — MORNING RUNNER")
    print(f"Date: {analysis_date}")
    print(f"Tickers: {len(ticker_inputs)}")
    print("=" * 60)

    client = get_polygon_client()
    errors = []
    success_count = 0
    pm_results = {}

    # Define pre-market window in ET
    prior_day = analysis_date - timedelta(days=1)
    # Handle weekends: if today is Monday, prior day for PM is Friday
    while prior_day.weekday() >= 5:  # Saturday=5, Sunday=6
        prior_day = prior_day - timedelta(days=1)

    pm_start_et = datetime(prior_day.year, prior_day.month, prior_day.day,
                           16, 0, tzinfo=ET)
    pm_end_et = datetime(analysis_date.year, analysis_date.month, analysis_date.day,
                         7, 30, tzinfo=ET)

    # Convert to UTC for Polygon API
    pm_start_utc = pm_start_et.astimezone(ZoneInfo("UTC"))
    pm_end_utc = pm_end_et.astimezone(ZoneInfo("UTC"))

    print(f"  PM window: {pm_start_et.strftime('%Y-%m-%d %H:%M')} ET -> "
          f"{pm_end_et.strftime('%Y-%m-%d %H:%M')} ET")

    for ticker_input in ticker_inputs:
        ticker = ticker_input["ticker"]
        print(f"\n  Processing {ticker}...")

        try:
            # Fetch M1 bars for the pre-market window
            # Use the start/end dates for the Polygon API
            df = client.fetch_minute_bars_chunked(
                ticker=ticker,
                start_date=prior_day,
                end_date=analysis_date,
                multiplier=1,
            )

            if df is None or df.empty:
                error_msg = f"{ticker}: no pre-market bars available"
                logger.warning(error_msg)
                print(f"    SKIP — {error_msg}")
                errors.append(error_msg)
                continue

            # Filter to pre-market window
            # The DataFrame should have a timestamp column
            if 'timestamp' in df.columns:
                df['ts'] = pd.to_datetime(df['timestamp'])
                if df['ts'].dt.tz is None:
                    df['ts'] = df['ts'].dt.tz_localize('UTC')
                pm_df = df[
                    (df['ts'] >= pm_start_utc) &
                    (df['ts'] <= pm_end_utc)
                ].copy()
            elif 't' in df.columns:
                # Polygon raw format uses 't' for timestamp (ms)
                df['ts'] = pd.to_datetime(df['t'], unit='ms', utc=True)
                pm_df = df[
                    (df['ts'] >= pm_start_utc) &
                    (df['ts'] <= pm_end_utc)
                ].copy()
            else:
                error_msg = f"{ticker}: no timestamp column in bars DataFrame"
                logger.error(error_msg)
                print(f"    FAIL — {error_msg}")
                errors.append(error_msg)
                continue

            if pm_df.empty or len(pm_df) < 5:
                error_msg = f"{ticker}: only {len(pm_df)} pre-market bars (need >= 5)"
                logger.warning(error_msg)
                print(f"    SKIP — {error_msg}")
                errors.append(error_msg)
                continue

            # Map column names (handle both 'high'/'h' formats)
            h_col = 'high' if 'high' in pm_df.columns else 'h'
            l_col = 'low' if 'low' in pm_df.columns else 'l'
            o_col = 'open' if 'open' in pm_df.columns else 'o'
            c_col = 'close' if 'close' in pm_df.columns else 'c'
            v_col = 'volume' if 'volume' in pm_df.columns else 'v'

            # Calculate PMH and PML
            pm_high = float(pm_df[h_col].max())
            pm_low = float(pm_df[l_col].min())
            pm_price = float(pm_df[c_col].iloc[-1])  # Latest close

            # Calculate pre-market volume profile (POC/VAH/VAL)
            opens = pm_df[o_col].values.astype(np.float64)
            highs = pm_df[h_col].values.astype(np.float64)
            lows = pm_df[l_col].values.astype(np.float64)
            closes = pm_df[c_col].values.astype(np.float64)
            volumes = pm_df[v_col].values.astype(np.float64)

            resolution = 200  # Same resolution as the standard VP
            va_pct = 70  # 70% value area

            zone_tops, buy_prof, sell_prof, s_high, s_low, gap = _build_profile_core(
                opens, highs, lows, closes, volumes, resolution
            )

            pm_poc = None
            pm_vah = None
            pm_val = None

            if gap > 0:
                poc_idx = _find_poc_index(buy_prof, sell_prof)
                pm_poc = _calculate_poc_price(zone_tops, poc_idx, gap)
                pm_val, pm_vah = _calculate_value_area(
                    buy_prof, sell_prof, zone_tops, gap, poc_idx, va_pct
                )

            pm_results[ticker] = {
                "pm_high": pm_high,
                "pm_low": pm_low,
                "pm_poc": pm_poc,
                "pm_vah": pm_vah,
                "pm_val": pm_val,
                "pm_price": pm_price,
            }

            print(f"    PMH={pm_high:.2f} PML={pm_low:.2f} "
                  f"POC={pm_poc:.2f if pm_poc else 'N/A'} "
                  f"Price={pm_price:.2f} "
                  f"({len(pm_df)} bars)")

            success_count += 1

        except Exception as e:
            error_msg = f"{ticker}: {str(e)}"
            logger.error(error_msg)
            print(f"    FAIL — {error_msg}")
            errors.append(error_msg)

    # Write pm_* columns to Supabase bar_data table
    print("\n--- Exporting PM Data to Supabase ---")
    _export_pm_data(pm_results, analysis_date)

    elapsed = time.time() - start_time
    fail_count = len(ticker_inputs) - success_count

    print(f"\n--- Morning Complete ---")
    print(f"  Success: {success_count} | Failed: {fail_count}")
    print(f"  Time: {elapsed:.1f}s")

    return {
        "bucket": "morning",
        "date": analysis_date.isoformat(),
        "success": success_count,
        "failed": fail_count,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
    }


def _export_pm_data(pm_results: Dict[str, Dict], analysis_date: date):
    """
    Write pm_* columns to existing bar_data rows in Supabase.

    The nightly runner (Bucket B) already created the bar_data rows.
    This updates the pm_* columns for tickers that have pre-market data.
    """
    import psycopg2
    from config import DB_CONFIG

    if not pm_results:
        print("  No PM data to export")
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        updated = 0
        for ticker, data in pm_results.items():
            # Build ticker_id to match bar_data PK format
            ticker_id = f"{ticker}_{analysis_date.strftime('%m%d%y')}"

            cur.execute("""
                UPDATE bar_data
                SET pm_high = %s, pm_low = %s, pm_poc = %s,
                    pm_vah = %s, pm_val = %s, pm_price = %s
                WHERE date = %s AND ticker_id = %s
            """, (
                data["pm_high"], data["pm_low"], data["pm_poc"],
                data["pm_vah"], data["pm_val"], data["pm_price"],
                analysis_date, ticker_id,
            ))

            if cur.rowcount > 0:
                updated += 1
            else:
                # Row might not exist if nightly didn't run for this ticker
                logger.warning(f"No bar_data row for {ticker} on {analysis_date} — "
                               f"pm data not written. Run nightly first.")

        conn.commit()
        cur.close()
        conn.close()
        print(f"  PM data exported for {updated}/{len(pm_results)} tickers")

    except Exception as e:
        logger.error(f"PM export failed: {e}")
        print(f"  PM export FAILED: {e}")


if __name__ == "__main__":
    from core.bucket_runner import load_universe_tickers
    today = date.today()
    tickers = load_universe_tickers(today)
    result = run_morning(tickers, today)
    sys.exit(0 if result["failed"] == 0 else 1)
