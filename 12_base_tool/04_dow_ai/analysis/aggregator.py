"""
DOW AI - Analysis Aggregator
Epoch Trading System v1 - XIII Trading LLC

Orchestrates all data sources and calculations using 10-Step Methodology.
"""
from datetime import datetime
from typing import Dict, Optional, Any
import pytz
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MODELS, TIMEZONE, VERBOSE, debug_print, get_debug_filepath, DEBUG_DIR, DATA_SOURCE
)

from data.polygon_fetcher import PolygonFetcher
from data.epoch_reader import EpochReader
from data.supabase_reader import SupabaseReader

from calculations.market_structure import MarketStructureCalculator
from calculations.volume_analysis import VolumeAnalyzer
from calculations.patterns import PatternDetector
from calculations.moving_averages import MovingAverageAnalyzer
from calculations.vwap import VWAPCalculator

from analysis.claude_client import ClaudeClient
from analysis.prompts.entry_prompt import build_entry_prompt
from analysis.prompts.exit_prompt import build_exit_prompt


class AnalysisAggregator:
    """
    Aggregates all data sources and calculations for DOW 10-Step Analysis.

    Orchestrates:
    - Polygon API data fetching
    - Excel workbook data reading
    - Market structure calculation (Steps 1-4)
    - Volume analysis (Steps 5-7)
    - SMA analysis (Steps 8-9)
    - VWAP analysis (Step 10)
    - Claude API interaction
    """

    def __init__(self, verbose: bool = None, data_source: str = None):
        """
        Initialize analysis aggregator.

        Args:
            verbose: Enable verbose output
            data_source: 'excel' or 'supabase' (uses config.DATA_SOURCE if not provided)
        """
        self.verbose = verbose if verbose is not None else VERBOSE
        self.tz = pytz.timezone(TIMEZONE)
        self.data_source = data_source or DATA_SOURCE

        # Initialize components
        self.polygon = PolygonFetcher(verbose=self.verbose)

        # Initialize data reader based on source
        if self.data_source == 'supabase':
            self.epoch = SupabaseReader(verbose=self.verbose)
            if self.verbose:
                debug_print("Using Supabase as data source")
        else:
            self.epoch = EpochReader(verbose=self.verbose)
            if self.verbose:
                debug_print("Using Excel as data source")

        self.structure_calc = MarketStructureCalculator(verbose=self.verbose)
        self.volume_analyzer = VolumeAnalyzer(verbose=self.verbose)
        self.pattern_detector = PatternDetector(verbose=self.verbose)
        self.sma_analyzer = MovingAverageAnalyzer(verbose=self.verbose)
        self.vwap_calc = VWAPCalculator(verbose=self.verbose)
        self.claude = ClaudeClient(verbose=self.verbose)

        if self.verbose:
            debug_print(f"AnalysisAggregator initialized (10-Step Methodology) - Data: {self.data_source}")

    def classify_model(self, zone_type: str, zone_direction: str, trade_direction: str) -> tuple:
        """
        Determine EPCH model based on zone and trade direction.

        Args:
            zone_type: 'primary' or 'secondary'
            zone_direction: Zone's direction from Excel (e.g., 'Bull', 'Bear', 'Bull+', 'Bear+')
            trade_direction: User's intended trade direction ('long' or 'short')

        Returns:
            tuple: (model_code, model_name, trade_type)
        """
        # Normalize zone direction
        zone_is_bullish = zone_direction.lower().startswith('bull')
        trade_is_long = trade_direction.lower() == 'long'

        # Trading WITH zone direction = Continuation
        # Trading AGAINST zone direction = Reversal
        with_trend = (zone_is_bullish and trade_is_long) or (not zone_is_bullish and not trade_is_long)

        if zone_type == 'primary':
            if with_trend:
                return ('EPCH_01', 'Primary Continuation', 'continuation')
            else:
                return ('EPCH_02', 'Primary Reversal', 'reversal')
        else:  # secondary
            if with_trend:
                return ('EPCH_03', 'Secondary Continuation', 'continuation')
            else:
                return ('EPCH_04', 'Secondary Reversal', 'reversal')

    def get_price_zone_relationship(self, current_price: float, zone: dict) -> dict:
        """
        Calculate relationship between current price and zone.

        Returns:
            dict with position, distance, and description
        """
        zone_high = zone['zone_high']
        zone_low = zone['zone_low']
        zone_mid = (zone_high + zone_low) / 2

        if current_price > zone_high:
            distance = current_price - zone_high
            position = 'ABOVE'
            description = f"${distance:.2f} above zone high"
        elif current_price < zone_low:
            distance = zone_low - current_price
            position = 'BELOW'
            description = f"${distance:.2f} below zone low"
        else:
            # Inside zone
            distance = 0
            position = 'INSIDE'
            pct_through = (current_price - zone_low) / (zone_high - zone_low) * 100
            description = f"Inside zone ({pct_through:.0f}% from low)"

        return {
            'position': position,
            'distance': distance,
            'description': description,
            'zone_high': zone_high,
            'zone_low': zone_low,
            'zone_mid': zone_mid
        }

    def _format_level(self, value: Optional[float]) -> str:
        """Format a price level."""
        return f"${value:.2f}" if value else "N/A"

    def _format_last_break(self, result) -> str:
        """Format last break info."""
        if result.last_break and result.last_break_price:
            return f"{result.last_break} at ${result.last_break_price:.2f}"
        return "N/A"

    def _format_zone_data(self, zone: Optional[Dict], direction: str) -> str:
        """Format zone information."""
        if not zone:
            return "No active zone identified for this ticker/direction"

        target_str = f"${zone['target']:.2f}" if zone.get('target') else "N/A"

        return f"""Zone ID: {zone.get('zone_id', 'N/A')} | Rank: {zone.get('rank', 'N/A')}
Range: ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}
HVN POC: ${zone['hvn_poc']:.2f}
Score: {zone.get('score', 'N/A')} | Confluences: {zone.get('confluences', 'N/A')}
Target: {target_str}"""

    def _get_price_zone_relationship(
        self,
        current_price: float,
        zone: Optional[Dict]
    ) -> str:
        """Determine price relationship to zone."""
        if not zone:
            return "No zone to compare"

        zone_high = zone['zone_high']
        zone_low = zone['zone_low']
        poc = zone['hvn_poc']

        if current_price > zone_high:
            dist = current_price - zone_high
            pct = (dist / current_price) * 100
            return f"ABOVE zone by ${dist:.2f} ({pct:.1f}%)"
        elif current_price < zone_low:
            dist = zone_low - current_price
            pct = (dist / current_price) * 100
            return f"BELOW zone by ${dist:.2f} ({pct:.1f}%)"
        else:
            if current_price > poc:
                return f"INSIDE zone, above POC (${poc:.2f})"
            else:
                return f"INSIDE zone, below POC (${poc:.2f})"

    def _format_market_data(self, bar_data: Dict, structure: Dict) -> str:
        """Format raw market data summary."""
        lines = []

        for tf in ['H4', 'H1', 'M15', 'M5']:
            if tf in bar_data and tf in structure:
                df = bar_data[tf]
                s = structure[tf]
                last = df.iloc[-1]
                lines.append(f"{tf}: O={last['open']:.2f} H={last['high']:.2f} L={last['low']:.2f} C={last['close']:.2f} | {s.direction}")

        return "\n".join(lines)

    def _format_trade_plan(
        self,
        zone: Optional[Dict],
        direction: str,
        atr: float
    ) -> str:
        """Format trade plan section."""
        if not zone:
            return "  Entry: Zone needed\n  Stop: TBD\n  Target: TBD"

        if direction.lower() == 'long':
            stop = zone['zone_low'] - (atr * 0.5)
            target1 = zone.get('target', zone['zone_high'] + atr)
            target2 = target1 + (atr * 1.5) if target1 else zone['zone_high'] + (atr * 2)
        else:
            stop = zone['zone_high'] + (atr * 0.5)
            target1 = zone.get('target', zone['zone_low'] - atr)
            target2 = target1 - (atr * 1.5) if target1 else zone['zone_low'] - (atr * 2)

        return f"""  Entry: ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}
  Stop: ${stop:.2f}
  Target 1: ${target1:.2f}
  Target 2: ${target2:.2f}"""

    def _write_debug_report(
        self,
        mode: str,
        ticker: str,
        result: Dict,
        prompt: str
    ):
        """Write detailed debug report to file."""
        filepath = get_debug_filepath(mode, ticker)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"DOW AI DEBUG REPORT - {mode.upper()} ANALYSIS (10-STEP)\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Ticker: {ticker}\n")
            f.write(f"Direction: {result.get('direction', result.get('exit_action', 'N/A'))}\n")
            f.write(f"Model: {result.get('model', 'N/A')}\n")
            f.write(f"Time: {result.get('analysis_time', datetime.now())}\n")
            f.write(f"Current Price: ${result.get('current_price', 0):.2f}\n\n")

            # All 10 steps summary
            f.write("-" * 70 + "\n")
            f.write("10-STEP ANALYSIS SUMMARY\n")
            f.write("-" * 70 + "\n")

            structure = result.get('structure', {})
            for tf in ['H4', 'H1', 'M15', 'M5']:
                if tf in structure:
                    s = structure[tf]
                    f.write(f"  {tf}: {s.direction} | Strong: {s.strong_level} | Weak: {s.weak_level}\n")

            smas = result.get('smas', {})
            for tf, sma in smas.items():
                f.write(f"  {tf} SMA: 9={sma.sma9:.2f} 21={sma.sma21:.2f} | {sma.alignment} | {sma.spread_trend}\n")

            vwap_result = result.get('vwap_result')
            if vwap_result:
                f.write(f"  VWAP: ${vwap_result.vwap:.2f} | Price {vwap_result.side}\n")

            f.write("\n")

            f.write("-" * 70 + "\n")
            f.write("FULL PROMPT SENT TO CLAUDE\n")
            f.write("-" * 70 + "\n")
            f.write(prompt)
            f.write("\n\n")

            f.write("-" * 70 + "\n")
            f.write("CLAUDE RESPONSE\n")
            f.write("-" * 70 + "\n")
            f.write(result.get('claude_response', 'No response'))
            f.write("\n")

        if self.verbose:
            debug_print(f"Debug report saved: {filepath}")

        return filepath

    def run_entry_analysis(
        self,
        ticker: str,
        direction: str,
        zone_type: str,
        analysis_datetime: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run complete entry analysis.

        Args:
            ticker: Stock symbol
            direction: 'long' or 'short'
            zone_type: 'primary' or 'secondary'
            analysis_datetime: Specific time for backtest (None = live)

        Returns:
            Dict with all analysis data and Claude response
        """
        if self.verbose:
            debug_print(f"Starting entry analysis: {ticker} {direction} {zone_type}")

        # Connect to data source (Excel or Supabase)
        if not self.epoch.connect():
            if self.data_source == 'supabase':
                return {"error": "Could not connect to Supabase. Check network and credentials."}
            else:
                return {"error": "Could not connect to Excel workbook. Ensure epoch_v1.xlsm is open."}

        # Determine analysis time
        if analysis_datetime:
            analysis_time = analysis_datetime
        else:
            analysis_time = datetime.now(self.tz)

        # =========================================================================
        # STEP 1: GET ZONE DATA
        # =========================================================================
        if zone_type == 'primary':
            zone = self.epoch.get_primary_zone(ticker)
        else:
            zone = self.epoch.get_secondary_zone(ticker)

        if not zone:
            return {"error": f"No {zone_type} zone found for {ticker} in Analysis worksheet"}

        # =========================================================================
        # STEP 2: FETCH PRICE DATA
        # =========================================================================
        if self.verbose:
            debug_print("Fetching Polygon data...")

        bar_data = self.polygon.fetch_multi_timeframe(
            ticker,
            ['M1', 'M5', 'M15', 'H1', 'H4'],
            analysis_time
        )

        if not bar_data or 'M1' not in bar_data:
            return {"error": f"Could not fetch bar data for {ticker}"}

        current_price = float(bar_data['M1'].iloc[-1]['close'])

        # =========================================================================
        # STEP 3: CALCULATE MODEL
        # =========================================================================
        model_code, model_name, trade_type = self.classify_model(
            zone_type=zone_type,
            zone_direction=zone['direction'],
            trade_direction=direction
        )

        if self.verbose:
            debug_print(f"Model classified: {model_code} ({model_name})")

        # =========================================================================
        # STEP 4: PRICE-TO-ZONE RELATIONSHIP
        # =========================================================================
        price_zone_rel = self.get_price_zone_relationship(current_price, zone)

        # =========================================================================
        # STEP 5: MARKET STRUCTURE (Steps 1-4 of 10-step)
        # =========================================================================
        if self.verbose:
            debug_print("Calculating market structure...")

        structure = self.structure_calc.calculate_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf != 'M1'
        })

        # =========================================================================
        # STEP 6: VOLUME ANALYSIS (Steps 5-7 of 10-step)
        # =========================================================================
        if self.verbose:
            debug_print("Analyzing volume...")

        volume = self.volume_analyzer.analyze(bar_data['M1'])

        # Also calculate M5 and M15 delta for multi-timeframe volume
        m5_volume = self.volume_analyzer.analyze(bar_data['M5']) if 'M5' in bar_data else None
        m15_volume = self.volume_analyzer.analyze(bar_data['M15']) if 'M15' in bar_data else None

        # =========================================================================
        # STEP 7: PATTERN DETECTION
        # =========================================================================
        if self.verbose:
            debug_print("Detecting patterns...")

        patterns = self.pattern_detector.detect_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf in ['M5', 'M15', 'H1']
        })

        # =====================================================
        # SMA CALCULATIONS (Steps 8-9 of 10-Step Methodology)
        # =====================================================
        if self.verbose:
            debug_print("Calculating SMA indicators...")
        try:
            smas = self.sma_analyzer.calculate_multi_timeframe({
                'M5': bar_data.get('M5'),
                'M15': bar_data.get('M15')
            })
            if self.verbose:
                for tf, sma in smas.items():
                    if sma:
                        debug_print(f"  {tf}: SMA9=${sma.sma9:.2f}, SMA21=${sma.sma21:.2f}, {sma.alignment}")
        except Exception as e:
            if self.verbose:
                debug_print(f"SMA calculation error: {e}")
            smas = {}

        # =====================================================
        # VWAP CALCULATION (Step 10 of 10-Step Methodology)
        # =====================================================
        if self.verbose:
            debug_print("Calculating VWAP...")
        try:
            vwap_result = self.vwap_calc.analyze(bar_data.get('M1'), current_price)
            if self.verbose and vwap_result:
                debug_print(f"  VWAP=${vwap_result.vwap:.2f}, Price is {vwap_result.side} by ${abs(vwap_result.price_diff):.2f}")
        except Exception as e:
            if self.verbose:
                debug_print(f"VWAP calculation error: {e}")
            vwap_result = None

        # =========================================================================
        # STEP 8: SUPPORTING LEVELS
        # =========================================================================
        atr = self.epoch.read_atr(ticker) or 2.0
        hvn_pocs = self.epoch.read_hvn_pocs(ticker)
        camarilla = self.epoch.read_camarilla_levels(ticker)

        # Get both zones for context
        all_zones = self.epoch.get_both_zones(ticker)

        # =========================================================================
        # STEP 9: BUILD PROMPT
        # =========================================================================
        if self.verbose:
            debug_print("Building Claude prompt...")

        prompt = build_entry_prompt(
            ticker=ticker,
            direction=direction,
            zone_type=zone_type,
            zone=zone,
            price_zone_rel=price_zone_rel,
            model_code=model_code,
            model_name=model_name,
            trade_type=trade_type,
            current_price=current_price,
            analysis_time=analysis_time.strftime("%Y-%m-%d %H:%M:%S ET"),
            structure=structure,
            volume=volume,
            m5_volume=m5_volume,
            m15_volume=m15_volume,
            patterns=patterns,
            atr=atr,
            hvn_pocs=hvn_pocs,
            camarilla=camarilla,
            all_zones=all_zones,
            smas=smas,
            vwap_result=vwap_result,
        )

        # =========================================================================
        # STEP 10: CLAUDE ANALYSIS
        # =========================================================================
        if self.verbose:
            debug_print("Sending to Claude...")

        claude_response = self.claude.analyze(prompt)

        result = {
            "ticker": ticker,
            "direction": direction,
            "zone_type": zone_type,
            "zone": zone,
            "model_code": model_code,
            "model_name": model_name,
            "trade_type": trade_type,
            "current_price": current_price,
            "price_zone_rel": price_zone_rel,
            "analysis_time": analysis_time,
            "structure": structure,
            "volume": volume,
            "m5_volume": m5_volume,
            "m15_volume": m15_volume,
            "patterns": patterns,
            "atr": atr,
            "hvn_pocs": hvn_pocs,
            "camarilla": camarilla,
            "all_zones": all_zones,
            "smas": smas,
            "vwap": vwap_result,
            "claude_response": claude_response,
            "prompt": prompt
        }

        # Write debug report
        self._write_debug_report('entry', ticker, result, prompt)

        return result

    def run_exit_analysis(
        self,
        ticker: str,
        exit_action: str,
        zone_type: str,
        analysis_datetime: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run complete exit analysis.

        Args:
            ticker: Stock symbol
            exit_action: 'sell' (close long) or 'cover' (close short)
            zone_type: 'primary' or 'secondary'
            analysis_datetime: Specific time for backtest (None = live)

        Returns:
            Dict with all analysis data and Claude response
        """
        if self.verbose:
            debug_print(f"Starting exit analysis: {ticker} {exit_action} {zone_type}")

        # Connect to data source (Excel or Supabase)
        if not self.epoch.connect():
            if self.data_source == 'supabase':
                return {"error": "Could not connect to Supabase. Check network and credentials."}
            else:
                return {"error": "Could not connect to Excel workbook. Ensure epoch_v1.xlsm is open."}

        position_type = "LONG" if exit_action.lower() == "sell" else "SHORT"
        direction = "long" if position_type == "LONG" else "short"
        analysis_time = analysis_datetime if analysis_datetime else datetime.now(self.tz)

        # Fetch data
        if self.verbose:
            debug_print("Fetching Polygon data...")

        bar_data = self.polygon.fetch_multi_timeframe(
            ticker,
            ['M1', 'M5', 'M15', 'H1', 'H4'],
            analysis_time
        )

        if not bar_data or 'M1' not in bar_data:
            return {"error": f"Could not fetch bar data for {ticker}"}

        current_price = float(bar_data['M1'].iloc[-1]['close'])

        # Get zone based on zone_type parameter
        if zone_type == 'primary':
            zone = self.epoch.get_primary_zone(ticker)
        else:
            zone = self.epoch.get_secondary_zone(ticker)

        if not zone:
            return {"error": f"No {zone_type} zone found for {ticker} in Analysis worksheet"}

        target_price = zone['target'] if zone and zone.get('target') else current_price

        # Calculate all metrics (same as entry)
        structure = self.structure_calc.calculate_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf in ['M5', 'M15', 'H1', 'H4']
        })
        volume = self.volume_analyzer.analyze(bar_data['M1'])
        smas = self.sma_analyzer.calculate_multi_timeframe({
            'M5': bar_data.get('M5'),
            'M15': bar_data.get('M15')
        })
        vwap_result = self.vwap_calc.analyze(bar_data['M1'], current_price)
        hvn_pocs = self.epoch.read_hvn_pocs(ticker)

        # Collect levels
        strong_levels = []
        weak_levels = []
        for tf, s in structure.items():
            if s.strong_level:
                strong_levels.append(f"{tf}: ${s.strong_level:.2f}")
            if s.weak_level:
                weak_levels.append(f"{tf}: ${s.weak_level:.2f}")

        # Build prompt
        if self.verbose:
            debug_print("Building Claude prompt...")

        # Calculate model for prompt
        model_code_for_prompt, model_name_for_prompt, _ = self.classify_model(
            zone_type=zone_type,
            zone_direction=zone['direction'],
            trade_direction=direction
        )

        prompt = build_exit_prompt(
            ticker=ticker,
            position_type=position_type,
            exit_action=exit_action.upper(),
            model_name=f"{model_code_for_prompt} ({model_name_for_prompt})",
            current_price=current_price,
            target_price=target_price,
            target_id=zone.get('zone_id', 'Unknown') if zone else 'Unknown',
            analysis_time=analysis_time.strftime("%Y-%m-%d %H:%M:%S ET"),
            zone_context=self._format_zone_data(zone, direction),
            structure_table=self._format_market_data(bar_data, structure),
            delta_5bar=volume.delta_5bar,
            delta_signal=volume.delta_signal,
            roc_percent=volume.roc_percent,
            roc_signal=volume.roc_signal,
            cvd_trend=volume.cvd_trend,
            patterns_list="See structure data",
            hvn_pocs=", ".join([f"${p:.2f}" for p in hvn_pocs[:5]]) if hvn_pocs else "N/A",
            strong_levels=", ".join(strong_levels) if strong_levels else "N/A",
            weak_levels=", ".join(weak_levels) if weak_levels else "N/A"
        )

        # Get Claude analysis
        if self.verbose:
            debug_print("Sending to Claude...")

        claude_response = self.claude.analyze(prompt)

        # Calculate model based on zone and direction for exit
        model_code, model_name, trade_type = self.classify_model(
            zone_type=zone_type,
            zone_direction=zone['direction'],
            trade_direction=direction
        )

        result = {
            "ticker": ticker,
            "position_type": position_type,
            "exit_action": exit_action,
            "zone_type": zone_type,
            "model_code": model_code,
            "model_name": model_name,
            "current_price": current_price,
            "target_price": target_price,
            "analysis_time": analysis_time,
            "zone": zone,
            "structure": structure,
            "volume": volume,
            "smas": smas,
            "vwap_result": vwap_result,
            "claude_response": claude_response,
            "prompt": prompt
        }

        # Write debug report
        self._write_debug_report('exit', ticker, result, prompt)

        return result


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("ANALYSIS AGGREGATOR - 10-STEP METHODOLOGY TEST")
    print("=" * 60)
    print("\nNOTE: This test requires:")
    print("  1. epoch_v1.xlsm open in Excel")
    print("  2. Valid Polygon API key")
    print("  3. Valid Anthropic API key")
    print()

    aggregator = AnalysisAggregator(verbose=True)

    # Test entry analysis
    print("[TEST] Running 10-step entry analysis for SPY long EPCH_01...")
    result = aggregator.run_entry_analysis('SPY', 'long', 'EPCH_01')

    if 'error' in result:
        print(f"\nERROR: {result['error']}")
    else:
        print(f"\nCurrent Price: ${result['current_price']:.2f}")
        print(f"\nClaude Response:")
        print("-" * 60)
        print(result['claude_response'])
        print("-" * 60)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
