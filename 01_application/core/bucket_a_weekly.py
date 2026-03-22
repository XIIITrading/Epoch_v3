"""
Bucket A — Weekly Runner
Screener Pipeline Build (Seed 004) — XIII Trading LLC

Runs Saturday/Sunday (manual trigger). Computes data that only changes
at weekly/monthly boundaries:
  - W1/M1 OHLC (current + prior)
  - Weekly/Monthly Camarilla pivots
  - W1/M1 Market Structure (fractal direction + strong/weak levels)
  - Epoch anchor auto-detection (max volume day in 6 months)

Also runs the full Bucket B (nightly) pipeline since the week's daily
data needs refreshing after the Friday close.

Usage:
    Called by bucket_runner.py --bucket weekly
"""
import logging
import sys
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


def run_weekly(
    ticker_inputs: List[Dict],
    analysis_date: date,
) -> Dict:
    """
    Run weekly calculations for all universe tickers.

    Computes W1/M1 structure (new), then delegates to the nightly runner
    for the full Bucket B pipeline (which writes bar_data with W1/M1
    OHLC and Camarilla already included).

    Args:
        ticker_inputs: List of dicts with 'ticker' and 'anchor_date'
        analysis_date: The analysis date (typically Saturday = Friday's data)

    Returns:
        Dict with success/fail counts and errors
    """
    from calculators.anchor_resolver import find_max_volume_anchor
    from core.bucket_b_nightly import run_nightly

    start_time = time.time()
    print("\n" + "=" * 60)
    print("BUCKET A — WEEKLY RUNNER")
    print(f"Date: {analysis_date}")
    print(f"Tickers: {len(ticker_inputs)}")
    print("=" * 60)

    errors = []
    resolved_inputs = []

    # Phase 1: Resolve epoch anchors for any tickers that need auto-detection
    print("\n--- Phase 1: Resolving Epoch Anchors ---")
    for ticker_input in ticker_inputs:
        ticker = ticker_input["ticker"]
        anchor_date = ticker_input.get("anchor_date")

        if not anchor_date or ticker_input.get("needs_auto_anchor", False):
            try:
                anchor_date, metadata = find_max_volume_anchor(ticker, analysis_date)
                exceeds = metadata.get("exceeds_threshold", False)
                print(f"  {ticker}: auto-anchor -> {anchor_date} "
                      f"(exceeds 20%: {exceeds})")

                # Update screener_universe with resolved anchor
                _update_universe_anchor(ticker, anchor_date)

            except Exception as e:
                error_msg = f"{ticker}: anchor resolution failed: {e}"
                logger.error(error_msg)
                print(f"  {ticker}: FAILED — {e}")
                errors.append(error_msg)
                # Use prior month as fallback
                first = analysis_date.replace(day=1)
                anchor_date = (first - __import__('datetime').timedelta(days=1)).replace(day=1)
                print(f"  {ticker}: fallback anchor -> {anchor_date}")
        else:
            print(f"  {ticker}: anchor = {anchor_date} (provided)")

        resolved_inputs.append({
            "ticker": ticker,
            "anchor_date": anchor_date,
        })

    # Phase 2: Calculate W1/M1 market structure (NEW)
    print("\n--- Phase 2: W1/M1 Market Structure ---")
    w1m1_results = _calculate_weekly_monthly_structure(resolved_inputs, analysis_date)
    for ticker, result in w1m1_results.items():
        if result.get("error"):
            errors.append(f"{ticker}: w1/m1 structure: {result['error']}")

    # Phase 3: Run full nightly pipeline (includes W1/M1 OHLC, Camarilla,
    # and all daily calculations)
    print("\n--- Phase 3: Running Full Nightly Pipeline ---")
    nightly_result = run_nightly(resolved_inputs, analysis_date)

    # Merge errors
    errors.extend(nightly_result.get("errors", []))

    # Phase 4: Write W1/M1 structure to market_structure table
    print("\n--- Phase 4: Exporting W1/M1 Structure ---")
    _export_w1m1_structure(w1m1_results, analysis_date)

    elapsed = time.time() - start_time
    success_count = nightly_result.get("success", 0)
    fail_count = nightly_result.get("failed", 0)

    print(f"\n--- Weekly Complete ---")
    print(f"  Success: {success_count} | Failed: {fail_count}")
    print(f"  W1/M1 structure: {len([r for r in w1m1_results.values() if not r.get('error')])} tickers")
    print(f"  Time: {elapsed:.1f}s")

    return {
        "bucket": "weekly",
        "date": analysis_date.isoformat(),
        "success": success_count,
        "failed": fail_count,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
    }


def _calculate_weekly_monthly_structure(
    ticker_inputs: List[Dict],
    analysis_date: date,
) -> Dict[str, Dict]:
    """
    Calculate W1 and M1 fractal market structure for each ticker.

    Uses the shared indicator library's get_market_structure() which
    works on any timeframe — we just pass W1/M1 bar DataFrames.

    Returns:
        Dict keyed by ticker -> {w1_direction, w1_strong, w1_weak,
                                  m1_direction, m1_strong, m1_weak, error}
    """
    from data import get_polygon_client
    from shared.indicators.structure import get_market_structure

    client = get_polygon_client()
    results = {}

    for ticker_input in ticker_inputs:
        ticker = ticker_input["ticker"]
        result = {
            "w1_direction": None, "w1_strong": None, "w1_weak": None,
            "m1_direction": None, "m1_strong": None, "m1_weak": None,
            "error": None,
        }

        try:
            # Fetch weekly bars (2 years for structure calculation)
            from datetime import timedelta
            w1_start = analysis_date - timedelta(days=730)
            w1_df = client.fetch_weekly_bars(ticker, w1_start, analysis_date)

            if w1_df is not None and not w1_df.empty and len(w1_df) >= 10:
                w1_structure = get_market_structure(w1_df)
                if w1_structure:
                    result["w1_direction"] = w1_structure.direction
                    result["w1_strong"] = w1_structure.strong_level
                    result["w1_weak"] = w1_structure.weak_level
                    print(f"  {ticker} W1: dir={w1_structure.label}, "
                          f"strong={w1_structure.strong_level}, weak={w1_structure.weak_level}")
                else:
                    print(f"  {ticker} W1: insufficient swing points")
            else:
                print(f"  {ticker} W1: insufficient bars ({len(w1_df) if w1_df is not None else 0})")

            # Fetch monthly bars (5 years for structure calculation)
            m1_start = analysis_date - timedelta(days=1825)
            m1_df = client.fetch_monthly_bars(ticker, m1_start, analysis_date)

            if m1_df is not None and not m1_df.empty and len(m1_df) >= 10:
                m1_structure = get_market_structure(m1_df)
                if m1_structure:
                    result["m1_direction"] = m1_structure.direction
                    result["m1_strong"] = m1_structure.strong_level
                    result["m1_weak"] = m1_structure.weak_level
                    print(f"  {ticker} M1: dir={m1_structure.label}, "
                          f"strong={m1_structure.strong_level}, weak={m1_structure.weak_level}")
                else:
                    print(f"  {ticker} M1: insufficient swing points")
            else:
                print(f"  {ticker} M1: insufficient bars ({len(m1_df) if m1_df is not None else 0})")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"{ticker} W1/M1 structure failed: {e}")
            print(f"  {ticker}: FAILED — {e}")

        results[ticker] = result

    return results


def _export_w1m1_structure(
    w1m1_results: Dict[str, Dict],
    analysis_date: date,
):
    """
    Write W1/M1 structure columns to existing market_structure rows.

    The nightly runner already wrote D1/H4/H1/M15 structure. This
    updates the same rows with the new W1/M1 columns.
    """
    import psycopg2
    from config import DB_CONFIG

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for ticker, result in w1m1_results.items():
            if result.get("error"):
                continue

            # Get direction value (handle enum or int)
            w1_dir = result["w1_direction"]
            if hasattr(w1_dir, 'value'):
                w1_dir = w1_dir.value
            m1_dir = result["m1_direction"]
            if hasattr(m1_dir, 'value'):
                m1_dir = m1_dir.value

            cur.execute("""
                UPDATE market_structure
                SET w1_direction = %s, w1_strong = %s, w1_weak = %s,
                    m1_direction = %s, m1_strong = %s, m1_weak = %s
                WHERE date = %s AND ticker = %s
            """, (
                w1_dir, result["w1_strong"], result["w1_weak"],
                m1_dir, result["m1_strong"], result["m1_weak"],
                analysis_date, ticker,
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"  W1/M1 structure exported for {len(w1m1_results)} tickers")

    except Exception as e:
        logger.error(f"W1/M1 export failed: {e}")
        print(f"  W1/M1 export FAILED: {e}")


def _update_universe_anchor(ticker: str, anchor_date: date):
    """Update the screener_universe table with resolved epoch anchor."""
    import psycopg2
    from config import DB_CONFIG

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO screener_universe (ticker, epoch_anchor_date, added_date)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (ticker)
            DO UPDATE SET epoch_anchor_date = EXCLUDED.epoch_anchor_date,
                          updated_at = NOW()
        """, (ticker, anchor_date))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Universe anchor update failed for {ticker}: {e}")


if __name__ == "__main__":
    from core.bucket_runner import load_universe_tickers
    today = date.today()
    tickers = load_universe_tickers(today)
    result = run_weekly(tickers, today)
    sys.exit(0 if result["failed"] == 0 else 1)
