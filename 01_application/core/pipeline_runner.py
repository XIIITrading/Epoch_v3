"""
Pipeline Runner - Orchestrates the full analysis pipeline.
Epoch Trading System v2.0 - XIII Trading LLC

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
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from config import INDEX_TICKERS

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Orchestrates the full analysis pipeline for PyQt6 application.

    Handles:
    - Index tickers (SPY, QQQ, DIA) with default anchor
    - Custom tickers with individual anchor dates
    - Progress updates via callback
    - End timestamp filtering for Pre-Market/Post-Market modes
    """

    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize the pipeline runner.

        Args:
            progress_callback: Function(percent, message) to report progress
        """
        self.progress_callback = progress_callback

    def _report_progress(self, percent: int, message: str):
        """Report progress via callback."""
        if self.progress_callback:
            self.progress_callback(percent, message)
        print(f"[{percent}%] {message}")

    def run(
        self,
        ticker_inputs: List[Dict],
        analysis_date: date,
        end_timestamp: Optional[datetime] = None
    ) -> Dict[str, List[Dict]]:
        """
        Run the full analysis pipeline.

        Args:
            ticker_inputs: List of dicts with 'ticker' and 'anchor_date'
            analysis_date: The date for analysis
            end_timestamp: Optional cutoff timestamp for data (Pre-Market/Post-Market modes)

        Returns:
            Dict with 'index' and 'custom' keys, each containing list of results
        """
        results = {
            "index": [],
            "custom": []
        }

        start_time = time.time()

        print("\n" + "=" * 60)
        print("EPOCH ANALYSIS PIPELINE - STARTING")
        print(f"Analysis Date: {analysis_date}")
        if end_timestamp:
            # Format timestamp in Eastern Time for display
            eastern = ZoneInfo("America/New_York")
            et_display = end_timestamp.astimezone(eastern)
            print(f"Data Cutoff: {et_display.strftime('%Y-%m-%d %H:%M')} ET")
        print("=" * 60)

        # Get default anchor for index tickers
        default_anchor = self._get_prior_month_anchor(analysis_date)

        # 1. Process index tickers first (SPY, QQQ, DIA with prior month anchor)
        self._report_progress(5, "Processing index tickers...")
        print("\n--- Processing Index Tickers (SPY, QQQ, DIA) ---")

        index_results = self._process_index_tickers(
            default_anchor,
            analysis_date,
            end_timestamp
        )
        results["index"] = index_results
        print(f"Index tickers complete: {len([r for r in index_results if r.get('success')])} successful")

        # 2. Process custom tickers
        valid_inputs = [
            t for t in ticker_inputs
            if t.get("ticker") and t.get("anchor_date")
        ]

        total_custom = len(valid_inputs)
        if total_custom == 0:
            self._report_progress(100, "No custom tickers to process")
            return results

        print(f"\n--- Processing {total_custom} Custom Ticker(s) ---")

        for i, ticker_input in enumerate(valid_inputs):
            ticker = ticker_input["ticker"]
            anchor_date = ticker_input["anchor_date"]

            # Convert string date if needed
            if isinstance(anchor_date, str):
                anchor_date = datetime.strptime(anchor_date, '%Y-%m-%d').date()

            print(f"\n[{i+1}/{total_custom}] Processing {ticker} (anchor: {anchor_date})")

            # Update progress (10% to 95%)
            progress = 10 + int(85 * (i / total_custom))
            self._report_progress(progress, f"Processing {ticker}...")

            try:
                result = self._process_single_ticker(
                    ticker=ticker,
                    anchor_date=anchor_date,
                    analysis_date=analysis_date,
                    end_timestamp=end_timestamp
                )
                results["custom"].append(result)
                print(f"    [OK] {ticker}: {result.get('zones_count', 0)} zones, {result.get('direction', 'N/A')}")

            except Exception as e:
                error_msg = f"{ticker}: {str(e)}"
                logger.error(error_msg)
                results["custom"].append({
                    "ticker": ticker,
                    "success": False,
                    "error": str(e)
                })
                print(f"    [FAIL] {ticker}: {str(e)}")

        # Complete
        elapsed = time.time() - start_time
        successful = sum(1 for r in results["custom"] if r.get("success"))
        self._report_progress(100, f"Completed in {elapsed:.1f}s")

        print(f"\n--- Pipeline Complete ---")
        print(f"Custom tickers: {successful}/{total_custom} successful")
        print(f"Total time: {elapsed:.1f}s")

        return results

    def _get_prior_month_anchor(self, ref_date: date) -> date:
        """Get first day of prior month as anchor date."""
        first_of_month = ref_date.replace(day=1)
        prior_month = first_of_month - timedelta(days=1)
        return prior_month.replace(day=1)

    def _process_index_tickers(
        self,
        anchor_date: date,
        analysis_date: date,
        end_timestamp: Optional[datetime]
    ) -> List[Dict]:
        """
        Process index tickers (SPY, QQQ, DIA) with prior month anchor.

        Returns:
            List of index ticker result dicts
        """
        results = []

        for ticker in INDEX_TICKERS:
            print(f"  Processing index: {ticker}...")
            try:
                result = self._process_single_ticker(
                    ticker=ticker,
                    anchor_date=anchor_date,
                    analysis_date=analysis_date,
                    end_timestamp=end_timestamp
                )
                result["is_index"] = True
                results.append(result)

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
        end_timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Process a single ticker through the full pipeline.

        Args:
            ticker: Ticker symbol
            anchor_date: Start date for HVN calculation
            analysis_date: Analysis date
            end_timestamp: Optional cutoff timestamp for data

        Returns:
            Result dictionary with all analysis data
        """
        # Import calculators here to avoid circular imports
        from calculators.bar_data import calculate_bar_data
        from calculators.hvn_identifier import calculate_hvn
        from calculators.zone_calculator import calculate_zones
        from calculators.zone_filter import filter_zones
        from calculators.market_structure import calculate_market_structure
        from calculators.setup_analyzer import analyze_setups
        from calculators.options_calculator import calculate_options_levels

        if end_timestamp:
            # Format timestamp in Eastern Time for display
            eastern = ZoneInfo("America/New_York")
            et_display = end_timestamp.astimezone(eastern)
            print(f"    Data cutoff: {et_display.strftime('%Y-%m-%d %H:%M')} ET")

        # Stage 1: Market Structure
        print(f"    Stage 1/6: Market structure...")
        market_structure = calculate_market_structure(
            ticker=ticker,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp
        )

        # Stage 2: Bar Data
        print(f"    Stage 2/6: Bar data...")
        bar_data = calculate_bar_data(
            ticker=ticker,
            analysis_date=analysis_date,
            end_timestamp=end_timestamp
        )

        if not bar_data:
            raise ValueError(f"Failed to calculate bar data for {ticker}")

        # Populate market structure strong/weak levels into bar_data
        if market_structure.d1 and market_structure.d1.strong is not None:
            bar_data.d1_strong = market_structure.d1.strong
        if market_structure.d1 and market_structure.d1.weak is not None:
            bar_data.d1_weak = market_structure.d1.weak
        if market_structure.h4 and market_structure.h4.strong is not None:
            bar_data.h4_strong = market_structure.h4.strong
        if market_structure.h4 and market_structure.h4.weak is not None:
            bar_data.h4_weak = market_structure.h4.weak
        if market_structure.h1 and market_structure.h1.strong is not None:
            bar_data.h1_strong = market_structure.h1.strong
        if market_structure.h1 and market_structure.h1.weak is not None:
            bar_data.h1_weak = market_structure.h1.weak
        if market_structure.m15 and market_structure.m15.strong is not None:
            bar_data.m15_strong = market_structure.m15.strong
        if market_structure.m15 and market_structure.m15.weak is not None:
            bar_data.m15_weak = market_structure.m15.weak

        # Calculate options levels and add to bar_data
        print(f"    Stage 2b/6: Options levels...")
        try:
            options_levels = calculate_options_levels(
                ticker=ticker,
                analysis_date=analysis_date,
                last_price=bar_data.price,
                num_levels=10,
                end_timestamp=end_timestamp
            )
            bar_data.options_levels = options_levels
            print(f"              Found {len(options_levels)} options levels")
        except Exception as e:
            logger.warning(f"Options calculation failed for {ticker}: {e}")
            print(f"              Options calculation failed: {e}")

        # Stage 3: HVN POCs
        print(f"    Stage 3/6: HVN POCs (anchor: {anchor_date})...")
        hvn_result = calculate_hvn(
            ticker=ticker,
            anchor_date=anchor_date,
            analysis_date=analysis_date,
            atr_value=bar_data.d1_atr,
            end_timestamp=end_timestamp
        )

        if not hvn_result or not hvn_result.pocs:
            raise ValueError(f"Failed to calculate HVN POCs for {ticker}")

        print(f"             {len(hvn_result.pocs)} POCs from {hvn_result.bars_analyzed} bars")

        # Stage 4: Zone Calculation
        print(f"    Stage 4/6: Zone calculation...")
        raw_zones = calculate_zones(
            bar_data=bar_data,
            hvn_result=hvn_result,
            direction=market_structure.composite,
            market_structure=market_structure
        )

        # Stage 5: Zone Filter
        print(f"    Stage 5/6: Zone filtering...")
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
        primary_setup, secondary_setup = analyze_setups(
            filtered_zones=filtered_zones,
            hvn_result=hvn_result,
            bar_data=bar_data,
            direction=direction
        )

        # Convert Pydantic models to dicts for UI compatibility
        return {
            "ticker": ticker,
            "success": True,
            "price": bar_data.price,
            "anchor_date": anchor_date.isoformat(),
            "analysis_date": analysis_date.isoformat(),
            "direction": direction.value if hasattr(direction, 'value') else str(direction),
            "zones_count": len(filtered_zones),
            "bull_poc": f"${bull_poc:.2f}" if bull_poc else "N/A",
            "bear_poc": f"${bear_poc:.2f}" if bear_poc else "N/A",
            "market_structure": market_structure.model_dump() if hasattr(market_structure, 'model_dump') else market_structure,
            "bar_data": bar_data.model_dump() if hasattr(bar_data, 'model_dump') else bar_data,
            "hvn_result": hvn_result.model_dump() if hasattr(hvn_result, 'model_dump') else hvn_result,
            "raw_zones": [z.model_dump() for z in raw_zones] if raw_zones else [],
            "filtered_zones": [z.model_dump() for z in filtered_zones] if filtered_zones else [],
            "primary_setup": primary_setup.model_dump() if primary_setup and hasattr(primary_setup, 'model_dump') else primary_setup,
            "secondary_setup": secondary_setup.model_dump() if secondary_setup and hasattr(secondary_setup, 'model_dump') else secondary_setup,
        }
