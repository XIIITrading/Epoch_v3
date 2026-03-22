"""
Bucket B — Nightly Runner
Screener Pipeline Build (Seed 004) — XIII Trading LLC

Runs after 20:00 ET. Computes all daily data for the full universe:
  - D1 OHLC, ATR (all TFs), D1 Camarilla
  - Options OI levels
  - PDV volume profile (POC/VAH/VAL)
  - HVN POCs (epoch-anchored, top 10)
  - Market structure (D1/H4/H1/M15 + composite)
  - Zone confluence scoring + filtering
  - Setup generation (primary + secondary)

This is a thin CLI wrapper around the existing PipelineRunner.run() +
export_to_supabase(). No new calculators — just headless execution.

Usage:
    Called by bucket_runner.py --bucket nightly
    Or directly: python -m core.bucket_b_nightly
"""
import logging
import sys
import time
from datetime import date, datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _cli_progress(percent: int, message: str):
    """Progress callback for headless CLI execution."""
    print(f"  [{percent:3d}%] {message}")


def _precompute_options_parallel(
    tickers: List[str],
    analysis_date: date,
    end_timestamp: Optional[datetime] = None,
    max_workers: int = 4,
) -> Dict[str, list]:
    """
    Pre-compute options OI levels for all tickers in parallel.

    Uses ThreadPoolExecutor since this is network-bound (API calls).
    Each ticker takes ~60s sequentially; with 4 workers, 50 tickers
    take ~13 minutes instead of ~50 minutes.

    Returns:
        Dict keyed by ticker -> list of strike prices
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from calculators.options_calculator import calculate_options_levels

    print(f"\n--- Pre-computing Options OI ({len(tickers)} tickers, {max_workers} workers) ---")
    options_start = time.time()
    results = {}

    def _fetch_one(ticker: str) -> tuple:
        try:
            levels = calculate_options_levels(
                ticker=ticker,
                analysis_date=analysis_date,
                num_levels=10,
                end_timestamp=end_timestamp,
            )
            return ticker, levels, None
        except Exception as e:
            return ticker, [], str(e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_one, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, levels, error = future.result()
            results[ticker] = levels
            if error:
                print(f"  {ticker}: options FAILED — {error}")
            else:
                print(f"  {ticker}: {len(levels)} options levels")

    elapsed = time.time() - options_start
    print(f"  Options pre-computation complete: {elapsed:.1f}s "
          f"({len(results)} tickers)")

    return results


def run_nightly(
    ticker_inputs: List[Dict],
    analysis_date: date,
    end_timestamp: Optional[datetime] = None,
    parallel_options: bool = True,
    options_workers: int = 4,
) -> Dict:
    """
    Run the full nightly pipeline for all universe tickers.

    Wraps existing PipelineRunner.run() -> export_to_supabase().
    All 5 Supabase tables are written: bar_data, hvn_pocs,
    market_structure, zones, setups.

    Options OI levels are pre-computed in parallel (4 workers by default)
    to reduce total runtime from ~50 min to ~13 min for 50 tickers.

    Args:
        ticker_inputs: List of dicts with 'ticker' and 'anchor_date'
        analysis_date: The trading date to process
        end_timestamp: Optional data cutoff (defaults to None = full day)
        parallel_options: Whether to pre-compute options in parallel (default True)
        options_workers: Number of parallel threads for options (default 4)

    Returns:
        Dict with success/fail counts and errors
    """
    from core.pipeline_runner import PipelineRunner
    from data.supabase_exporter import export_to_supabase
    from config import INDEX_TICKERS

    start_time = time.time()
    print("\n" + "=" * 60)
    print("BUCKET B — NIGHTLY RUNNER")
    print(f"Date: {analysis_date}")
    print(f"Tickers: {len(ticker_inputs)}")
    print("=" * 60)

    # Phase 0: Resolve epoch anchors for tickers that need auto-detection
    # Uses find_max_volume_anchor() — the "High Volume Day in 6 Months" preset
    from calculators.anchor_resolver import find_max_volume_anchor
    from datetime import timedelta

    resolved_inputs = []
    print("\n--- Resolving Epoch Anchors ---")
    for ticker_input in ticker_inputs:
        ticker = ticker_input["ticker"]
        anchor_date = ticker_input.get("anchor_date")

        if not anchor_date or ticker_input.get("needs_auto_anchor", False):
            try:
                anchor_date, metadata = find_max_volume_anchor(ticker, analysis_date)
                exceeds = metadata.get("exceeds_threshold", False)
                print(f"  {ticker}: auto-anchor -> {anchor_date} "
                      f"(exceeds 20%: {exceeds})")
            except Exception as e:
                logger.warning(f"{ticker}: anchor resolution failed: {e}")
                print(f"  {ticker}: anchor FAILED — using prior month fallback")
                first = analysis_date.replace(day=1)
                anchor_date = (first - timedelta(days=1)).replace(day=1)
        else:
            print(f"  {ticker}: anchor = {anchor_date} (provided)")

        resolved_inputs.append({
            "ticker": ticker,
            "anchor_date": anchor_date,
        })

    ticker_inputs = resolved_inputs

    # Phase 1: Pre-compute options in parallel
    precomputed_options = None
    if parallel_options:
        all_tickers = INDEX_TICKERS + [t["ticker"] for t in ticker_inputs]
        # Deduplicate while preserving order
        seen = set()
        unique_tickers = []
        for t in all_tickers:
            if t not in seen:
                seen.add(t)
                unique_tickers.append(t)
        precomputed_options = _precompute_options_parallel(
            unique_tickers, analysis_date, end_timestamp, options_workers
        )

    # Phase 2: Run the existing pipeline headless (with pre-computed options)
    runner = PipelineRunner(progress_callback=_cli_progress)
    results = runner.run(
        ticker_inputs=ticker_inputs,
        analysis_date=analysis_date,
        end_timestamp=end_timestamp,
        precomputed_options=precomputed_options,
    )

    # Count results
    all_results = results.get("index", []) + results.get("custom", [])
    success_count = sum(1 for r in all_results if r.get("success"))
    fail_count = sum(1 for r in all_results if not r.get("success"))
    errors = [
        f"{r.get('ticker', '?')}: {r.get('error', 'unknown')}"
        for r in all_results
        if not r.get("success")
    ]

    # Export to Supabase
    print("\n--- Exporting to Supabase ---")
    try:
        stats = export_to_supabase(results)
        print(f"  Exported: {stats.total_records} records "
              f"({stats.tickers_processed} tickers)")
        if stats.errors:
            for err in stats.errors:
                print(f"  EXPORT ERROR: {err}")
                errors.append(f"export: {err}")
    except Exception as e:
        error_msg = f"Supabase export failed: {str(e)}"
        logger.error(error_msg)
        print(f"  EXPORT FAILED: {error_msg}")
        errors.append(error_msg)

    elapsed = time.time() - start_time

    print(f"\n--- Nightly Complete ---")
    print(f"  Success: {success_count} | Failed: {fail_count}")
    print(f"  Time: {elapsed:.1f}s")

    return {
        "bucket": "nightly",
        "date": analysis_date.isoformat(),
        "success": success_count,
        "failed": fail_count,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
    }


if __name__ == "__main__":
    # Direct execution for testing
    from core.bucket_runner import load_universe_tickers
    today = date.today()
    tickers = load_universe_tickers(today)
    result = run_nightly(tickers, today)
    sys.exit(0 if result["failed"] == 0 else 1)
