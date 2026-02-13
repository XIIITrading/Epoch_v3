"""
Pipeline Runner - Orchestrates the full analysis pipeline.

Runs the complete analysis flow:
1. Fetch data (uses cache for Polygon API calls)
2. Calculate bar data (OHLC, ATR, Camarilla)
3. Calculate HVN POCs
4. Calculate confluence zones
5. Filter zones and identify setups

Handles both custom tickers and index tickers (SPY, QQQ, DIA).
"""
import logging
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from config.settings import INDEX_TICKERS
from core.state_manager import (
    update_pipeline_progress,
    set_state,
    add_error,
    get_prior_month_anchor,
    get_anchor_date,
    get_market_end_timestamp,
    get_market_time_mode,
    ANCHOR_PRESETS,
)
from core.data_models import (
    TickerInput,
    BarData,
    HVNResult,
    RawZone,
    FilteredZone,
    Direction,
)

# Import the standalone functions (not classes)
from calculators.bar_data import calculate_bar_data
from calculators.hvn_identifier import calculate_hvn
from calculators.zone_calculator import calculate_zones
from calculators.zone_filter import filter_zones
from calculators.market_structure import calculate_market_structure
from calculators.setup_analyzer import analyze_setups
from calculators.options_calculator import calculate_options_levels

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Orchestrates the full analysis pipeline.

    Handles:
    - Index tickers (SPY, QQQ, DIA) with prior month anchor
    - Custom tickers with individual anchor dates
    - Progress updates via Streamlit session state
    """

    def __init__(self):
        """Initialize the pipeline runner."""
        pass  # All calculators are standalone functions

    def _log(self, message: str, level: str = "INFO") -> None:
        """Print a log message to terminal for Claude Code visibility."""
        print(f"[{level}] {message}")

    def run(self, ticker_inputs: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Run the full analysis pipeline.

        Args:
            ticker_inputs: List of dicts with 'ticker', 'anchor_date', 'analysis_date'

        Returns:
            Dict with 'index' and 'custom' keys, each containing list of results
        """
        results = {
            "index": [],
            "custom": []
        }

        start_time = time.time()

        print("\n" + "="*60)
        print("EPOCH ANALYSIS PIPELINE - STARTING")
        print("="*60)

        # 1. Process index tickers first (SPY, QQQ, DIA with prior month anchor)
        print("\n--- Processing Index Tickers (SPY, QQQ, DIA) ---")
        update_pipeline_progress("fetch_data", 0.05, "Processing index tickers...")
        index_results = self._process_index_tickers()
        results["index"] = index_results
        print(f"Index tickers complete: {len([r for r in index_results if r.get('success')])} successful")

        # 2. Process custom tickers
        valid_inputs = [
            t for t in ticker_inputs
            if t.get("ticker") and t.get("anchor_date")
        ]

        total_custom = len(valid_inputs)
        if total_custom == 0:
            update_pipeline_progress("complete", 1.0, "No custom tickers to process")
            return results

        print(f"\n--- Processing {total_custom} Custom Ticker(s) ---")

        for i, ticker_input in enumerate(valid_inputs):
            ticker = ticker_input["ticker"]
            anchor_date = ticker_input["anchor_date"]
            analysis_date = ticker_input.get("analysis_date") or date.today()

            print(f"\n[{i+1}/{total_custom}] Processing {ticker} (anchor: {anchor_date})")

            # Update progress
            progress = 0.1 + (0.85 * (i / total_custom))
            set_state("current_ticker", ticker)

            try:
                result = self._process_single_ticker(
                    ticker=ticker,
                    anchor_date=anchor_date,
                    analysis_date=analysis_date,
                    progress_base=progress,
                    progress_range=0.85 / total_custom
                )
                results["custom"].append(result)
                print(f"    [OK] {ticker}: {result.get('zones_count', 0)} zones, {result.get('direction', 'N/A')}")

            except Exception as e:
                error_msg = f"{ticker}: {str(e)}"
                logger.error(error_msg)
                add_error(error_msg)
                results["custom"].append({
                    "ticker": ticker,
                    "success": False,
                    "error": str(e)
                })
                print(f"    [FAIL] {ticker}: {str(e)}")

        # Complete
        elapsed = time.time() - start_time
        successful = sum(1 for r in results["custom"] if r.get("success"))
        update_pipeline_progress("complete", 1.0, f"Completed in {elapsed:.1f}s")
        set_state("current_ticker", None)

        print(f"\n--- Pipeline Complete ---")
        print(f"Custom tickers: {successful}/{total_custom} successful")
        print(f"Total time: {elapsed:.1f}s")

        return results

    def _process_index_tickers(self, full_analysis: bool = True) -> List[Dict]:
        """
        Process index tickers (SPY, QQQ, DIA) with prior month anchor.

        Args:
            full_analysis: If True, run full zone analysis. If False, only market structure.

        Returns:
            List of index ticker result dicts
        """
        results = []
        anchor_date = get_prior_month_anchor()
        analysis_date = date.today()

        # Get end timestamp based on market time mode (same as custom tickers)
        end_timestamp = get_market_end_timestamp(analysis_date)
        market_mode = get_market_time_mode()

        for ticker in INDEX_TICKERS:
            print(f"  Processing index: {ticker}...")
            if end_timestamp:
                print(f"    Market time mode: {market_mode} (cutoff: {end_timestamp.strftime('%H:%M ET')})")
            try:
                set_state("current_ticker", ticker)

                if full_analysis:
                    # Run full analysis pipeline (same as custom tickers)
                    result = self._process_single_ticker(
                        ticker=ticker,
                        anchor_date=anchor_date,
                        analysis_date=analysis_date,
                        progress_base=0.0,
                        progress_range=0.05
                    )
                    result["is_index"] = True
                    results.append(result)
                else:
                    # Just market structure and bar data (lightweight)
                    # Pass end_timestamp to respect market time mode
                    market_structure = calculate_market_structure(
                        ticker=ticker,
                        analysis_date=analysis_date,
                        end_timestamp=end_timestamp  # Pass market time mode cutoff
                    )

                    bar_data = calculate_bar_data(
                        ticker=ticker,
                        analysis_date=analysis_date,
                        end_timestamp=end_timestamp  # Pass market time mode cutoff
                    )

                    results.append({
                        "ticker": ticker,
                        "success": True,
                        "direction": market_structure.composite.value,
                        "price": market_structure.price,
                        "anchor_date": anchor_date.isoformat(),
                        "market_structure": market_structure,
                        "bar_data": bar_data,
                        "is_index": True,
                        "market_mode": market_mode,
                    })

            except Exception as e:
                logger.error(f"Index ticker {ticker} error: {e}")
                print(f"    [FAIL] {ticker}: {str(e)}")
                results.append({
                    "ticker": ticker,
                    "success": False,
                    "error": str(e),
                    "direction": "ERROR",
                    "is_index": True,
                })

        return results

    def _process_single_ticker(
        self,
        ticker: str,
        anchor_date: date,
        analysis_date: date,
        progress_base: float,
        progress_range: float
    ) -> Dict:
        """
        Process a single custom ticker through the full pipeline.

        Args:
            ticker: Ticker symbol
            anchor_date: Start date for HVN calculation
            analysis_date: Analysis date (usually today)
            progress_base: Base progress value (0.0-1.0)
            progress_range: Progress range for this ticker

        Returns:
            Result dictionary with all analysis data
        """
        # Get end timestamp based on market time mode (Pre-Market / Post-Market / Live)
        end_timestamp = get_market_end_timestamp(analysis_date)
        market_mode = get_market_time_mode()
        if end_timestamp:
            print(f"    Market time mode: {market_mode} (cutoff: {end_timestamp.strftime('%H:%M ET')})")
        else:
            print(f"    Market time mode: {market_mode}")

        # Stage 1: Market Structure
        print(f"    Stage 1/6: Market structure...")
        update_pipeline_progress(
            "fetch_data",
            progress_base + (progress_range * 0.1),
            f"Calculating market structure for {ticker}..."
        )

        market_structure = calculate_market_structure(
            ticker=ticker,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp  # Pass market time mode cutoff
        )

        # Stage 2: Bar Data
        print(f"    Stage 2/6: Bar data...")
        update_pipeline_progress(
            "bar_data",
            progress_base + (progress_range * 0.25),
            f"Calculating bar data for {ticker}..."
        )

        bar_data = calculate_bar_data(
            ticker=ticker,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp  # Pass market time mode cutoff
        )

        if not bar_data:
            raise ValueError(f"Failed to calculate bar data for {ticker}")

        # Populate market structure strong/weak levels into bar_data
        # This is required for zone confluence scoring
        if market_structure.d1.strong is not None:
            bar_data.d1_strong = market_structure.d1.strong
        if market_structure.d1.weak is not None:
            bar_data.d1_weak = market_structure.d1.weak
        if market_structure.h4.strong is not None:
            bar_data.h4_strong = market_structure.h4.strong
        if market_structure.h4.weak is not None:
            bar_data.h4_weak = market_structure.h4.weak
        if market_structure.h1.strong is not None:
            bar_data.h1_strong = market_structure.h1.strong
        if market_structure.h1.weak is not None:
            bar_data.h1_weak = market_structure.h1.weak
        if market_structure.m15.strong is not None:
            bar_data.m15_strong = market_structure.m15.strong
        if market_structure.m15.weak is not None:
            bar_data.m15_weak = market_structure.m15.weak

        # Calculate options levels and add to bar_data
        print(f"    Stage 2b/6: Options levels...")
        try:
            options_levels = calculate_options_levels(
                ticker=ticker,
                analysis_date=analysis_date,
                last_price=bar_data.price,
                num_levels=10,
                end_timestamp=end_timestamp  # Pass market time mode cutoff
            )
            bar_data.options_levels = options_levels
            print(f"              Found {len(options_levels)} options levels")
        except Exception as e:
            logger.warning(f"Options calculation failed for {ticker}: {e}")
            print(f"              Options calculation failed: {e}")

        # Stage 3: HVN POCs
        print(f"    Stage 3/6: HVN POCs (anchor: {anchor_date})...")
        update_pipeline_progress(
            "hvn_calc",
            progress_base + (progress_range * 0.5),
            f"Calculating HVN POCs for {ticker}..."
        )

        hvn_result = calculate_hvn(
            ticker=ticker,
            anchor_date=anchor_date,
            analysis_date=analysis_date,
            atr_value=bar_data.d1_atr,  # Use D1 ATR for overlap threshold (matches original)
            end_timestamp=end_timestamp  # Pass market time mode cutoff
        )

        if not hvn_result or not hvn_result.pocs:
            raise ValueError(f"Failed to calculate HVN POCs for {ticker}")

        print(f"             {len(hvn_result.pocs)} POCs from {hvn_result.bars_analyzed} bars")

        # Stage 4: Zone Calculation
        print(f"    Stage 4/6: Zone calculation...")
        update_pipeline_progress(
            "zone_calc",
            progress_base + (progress_range * 0.7),
            f"Calculating zones for {ticker}..."
        )

        raw_zones = calculate_zones(
            bar_data=bar_data,
            hvn_result=hvn_result,
            direction=market_structure.composite,
            market_structure=market_structure
        )

        # Stage 5: Zone Filter
        print(f"    Stage 5/6: Zone filtering...")
        update_pipeline_progress(
            "zone_filter",
            progress_base + (progress_range * 0.9),
            f"Filtering zones for {ticker}..."
        )

        # Use market structure composite for direction
        direction = market_structure.composite
        filtered_zones = filter_zones(
            raw_zones=raw_zones,
            bar_data=bar_data,
            direction=direction
        )

        # Find bull and bear POCs
        bull_poc = next(
            (z.hvn_poc for z in filtered_zones if z.is_bull_poc),
            None
        )
        bear_poc = next(
            (z.hvn_poc for z in filtered_zones if z.is_bear_poc),
            None
        )

        # Stage 6: Setup Analysis
        print(f"    Stage 6/6: Setup analysis...")
        update_pipeline_progress(
            "setup_analysis",
            progress_base + (progress_range * 0.95),
            f"Analyzing setups for {ticker}..."
        )

        primary_setup, secondary_setup = analyze_setups(
            filtered_zones=filtered_zones,
            hvn_result=hvn_result,
            bar_data=bar_data,
            direction=direction
        )

        return {
            "ticker": ticker,
            "success": True,
            "price": bar_data.price,
            "anchor_date": anchor_date.isoformat(),
            "analysis_date": analysis_date.isoformat(),
            "direction": direction.value,
            "zones_count": len(filtered_zones),
            "bull_poc": f"${bull_poc:.2f}" if bull_poc else "N/A",
            "bear_poc": f"${bear_poc:.2f}" if bear_poc else "N/A",
            "market_mode": market_mode,
            "market_structure": market_structure,
            "bar_data": bar_data,
            "hvn_result": hvn_result,
            "raw_zones": raw_zones,
            "filtered_zones": filtered_zones,
            "primary_setup": primary_setup,
            "secondary_setup": secondary_setup,
        }

    def _determine_direction(self, bar_data: BarData) -> Direction:
        """
        Determine market direction from bar data.

        Simple implementation: compare current price to prior day close.

        Args:
            bar_data: BarData object

        Returns:
            Direction enum value
        """
        if not bar_data:
            return Direction.NEUTRAL

        price = bar_data.price
        prior_close = bar_data.d1_prior.close if bar_data.d1_prior else None

        if prior_close is None:
            return Direction.NEUTRAL

        change_pct = ((price - prior_close) / prior_close) * 100

        if change_pct > 1.0:
            return Direction.BULL_PLUS
        elif change_pct > 0:
            return Direction.BULL
        elif change_pct < -1.0:
            return Direction.BEAR_PLUS
        elif change_pct < 0:
            return Direction.BEAR
        else:
            return Direction.NEUTRAL

    def run_batch(
        self,
        tickers: List[str],
        anchor_presets: List[str],
        analysis_date: date = None
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Run analysis for multiple anchor dates (batch mode).

        Args:
            tickers: List of ticker symbols
            anchor_presets: List of anchor preset names ('Prior Day', 'Prior Week', etc.)
            analysis_date: Analysis date (defaults to today)

        Returns:
            Dict keyed by anchor preset name, each containing:
            - 'index': List of index ticker results
            - 'custom': List of custom ticker results
        """
        analysis_date = analysis_date or date.today()
        batch_results = {}

        start_time = time.time()
        total_presets = len(anchor_presets)

        print("\n" + "="*60)
        print("EPOCH BATCH ANALYSIS - STARTING")
        print(f"Presets: {', '.join(anchor_presets)}")
        print(f"Tickers: {', '.join(tickers)}")
        print("="*60)

        for preset_idx, preset in enumerate(anchor_presets):
            # Calculate anchor date for this preset
            try:
                anchor_date = get_anchor_date(preset)
            except ValueError as e:
                logger.error(f"Invalid preset {preset}: {e}")
                print(f"[ERROR] Invalid preset {preset}: {e}")
                continue

            print(f"\n--- [{preset_idx+1}/{total_presets}] {preset} (anchor: {anchor_date}) ---")
            logger.info(f"Running batch for {preset}: anchor={anchor_date}")

            # Progress tracking for this preset
            preset_progress_base = preset_idx / total_presets
            preset_progress_range = 1.0 / total_presets

            update_pipeline_progress(
                "batch",
                preset_progress_base,
                f"Processing {preset} ({preset_idx + 1}/{total_presets})..."
            )

            # Build ticker inputs for this preset
            ticker_inputs = [
                {
                    "ticker": ticker,
                    "anchor_date": anchor_date,
                    "analysis_date": analysis_date
                }
                for ticker in tickers
            ]

            # Run analysis for this preset
            preset_results = {
                "index": [],
                "custom": [],
                "anchor_date": anchor_date.isoformat(),
                "preset": preset
            }

            # Process index tickers (always with prior month for context)
            index_results = self._process_index_tickers()
            preset_results["index"] = index_results

            # Process custom tickers with this anchor
            total_tickers = len(tickers)
            for i, ticker in enumerate(tickers):
                ticker_progress = preset_progress_base + (
                    preset_progress_range * (i / max(total_tickers, 1))
                )
                set_state("current_ticker", ticker)

                try:
                    result = self._process_single_ticker(
                        ticker=ticker,
                        anchor_date=anchor_date,
                        analysis_date=analysis_date,
                        progress_base=ticker_progress,
                        progress_range=preset_progress_range / max(total_tickers, 1)
                    )
                    preset_results["custom"].append(result)

                except Exception as e:
                    error_msg = f"{ticker} ({preset}): {str(e)}"
                    logger.error(error_msg)
                    add_error(error_msg)
                    print(f"    [FAIL] {ticker}: {str(e)}")
                    preset_results["custom"].append({
                        "ticker": ticker,
                        "success": False,
                        "error": str(e),
                        "anchor_date": anchor_date.isoformat(),
                        "preset": preset
                    })

            successful = sum(1 for r in preset_results["custom"] if r.get("success"))
            print(f"  {preset} complete: {successful}/{len(tickers)} successful")
            batch_results[preset] = preset_results

        # Complete
        elapsed = time.time() - start_time
        update_pipeline_progress(
            "complete",
            1.0,
            f"Batch complete: {len(anchor_presets)} anchors in {elapsed:.1f}s"
        )
        set_state("current_ticker", None)

        print(f"\n--- Batch Analysis Complete ---")
        print(f"Presets processed: {len(batch_results)}")
        print(f"Total time: {elapsed:.1f}s")

        return batch_results


def compare_zones_across_anchors(
    batch_results: Dict[str, Dict[str, List[Dict]]],
    ticker: str
) -> Dict[str, Any]:
    """
    Compare zones for a ticker across different anchor dates.

    Args:
        batch_results: Results from run_batch()
        ticker: Ticker to compare

    Returns:
        Comparison data with common zones, unique zones, etc.
    """
    comparison = {
        "ticker": ticker,
        "anchors": {},
        "common_pocs": [],
        "unique_zones": {}
    }

    # Collect zones from each anchor
    all_pocs = {}  # POC price -> list of anchors where it appears

    for preset, preset_results in batch_results.items():
        custom_results = preset_results.get("custom", [])
        ticker_result = next(
            (r for r in custom_results if r.get("ticker") == ticker),
            None
        )

        if not ticker_result or not ticker_result.get("success"):
            continue

        filtered_zones = ticker_result.get("filtered_zones", [])
        hvn_result = ticker_result.get("hvn_result")

        comparison["anchors"][preset] = {
            "anchor_date": ticker_result.get("anchor_date"),
            "zones_count": len(filtered_zones),
            "bull_poc": ticker_result.get("bull_poc"),
            "bear_poc": ticker_result.get("bear_poc"),
            "zones": filtered_zones
        }

        # Track POCs across anchors
        if hvn_result:
            for i, poc in enumerate(hvn_result.pocs):
                poc_key = round(poc.price, 2)  # Round for comparison
                if poc_key not in all_pocs:
                    all_pocs[poc_key] = []
                all_pocs[poc_key].append(preset)

    # Find POCs that appear in multiple anchors
    for poc_price, anchors in all_pocs.items():
        if len(anchors) > 1:
            comparison["common_pocs"].append({
                "price": poc_price,
                "anchors": anchors,
                "count": len(anchors)
            })

    # Sort common POCs by how many anchors they appear in
    comparison["common_pocs"].sort(key=lambda x: x["count"], reverse=True)

    return comparison
