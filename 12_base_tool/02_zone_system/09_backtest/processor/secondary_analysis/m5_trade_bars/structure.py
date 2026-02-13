"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
M5 Trade Bars - Market Structure Detection
XIII Trading LLC
================================================================================

Multi-timeframe market structure calculation for trade bars.
Self-contained implementation matching m5_indicator_bars module.

Version: 1.0.0
================================================================================
"""

from typing import Dict, List, Optional, Tuple, NamedTuple
import numpy as np
from datetime import datetime, date, time, timedelta
import requests
import time as time_module

from config import (
    FRACTAL_LENGTH,
    STRUCTURE_LABELS,
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    API_DELAY,
    API_RETRIES,
    API_RETRY_DELAY,
    HTF_BARS_NEEDED,
    HTF_LOOKBACK_DAYS
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class StructureResult(NamedTuple):
    """Result of market structure calculation."""
    direction: int  # 1 = BULL, -1 = BEAR, 0 = NEUTRAL
    direction_label: str  # 'BULL', 'BEAR', 'NEUTRAL', 'ERROR'
    last_break_label: Optional[str]  # 'BOS' or 'ChoCH'
    strong_level: Optional[float]
    weak_level: Optional[float]


# =============================================================================
# MARKET STRUCTURE CALCULATOR
# =============================================================================

class MarketStructureCalculator:
    """Calculates market structure from OHLC data."""

    def __init__(self, fractal_length: int = None):
        self.length = fractal_length or FRACTAL_LENGTH
        self.p = int(self.length / 2)

    def _detect_fractals(self, bars: List[Dict]) -> Tuple[List[bool], List[bool]]:
        """Detect bullish and bearish fractals."""
        n = len(bars)
        p = self.p

        bullf = [False] * n
        bearf = [False] * n

        if n < self.length:
            return bullf, bearf

        for i in range(p, n - p):
            high_i = float(bars[i].get('high', 0))
            low_i = float(bars[i].get('low', 0))

            # Bearish fractal (local high)
            before_lower = all(
                float(bars[i - j].get('high', 0)) < high_i
                for j in range(1, p + 1)
            )
            after_lower = all(
                float(bars[i + j].get('high', 0)) < high_i
                for j in range(1, p + 1)
            )

            if before_lower and after_lower:
                bearf[i] = True

            # Bullish fractal (local low)
            before_higher = all(
                float(bars[i - j].get('low', 0)) > low_i
                for j in range(1, p + 1)
            )
            after_higher = all(
                float(bars[i + j].get('low', 0)) > low_i
                for j in range(1, p + 1)
            )

            if before_higher and after_higher:
                bullf[i] = True

        return bullf, bearf

    def calculate(self, bars: List[Dict]) -> StructureResult:
        """Calculate market structure from OHLC data."""
        if not bars or len(bars) < 50:
            return StructureResult(
                direction=0,
                direction_label='NEUTRAL',
                last_break_label=None,
                strong_level=None,
                weak_level=None
            )

        bullf, bearf = self._detect_fractals(bars)

        upper_value = None
        upper_crossed = False
        lower_value = None
        lower_crossed = False
        current_structure = 0
        last_break_label = None
        bull_continuation_high = None
        bear_continuation_low = None

        for i in range(len(bars)):
            close = float(bars[i].get('close', 0))
            high = float(bars[i].get('high', 0))
            low = float(bars[i].get('low', 0))

            if bearf[i]:
                upper_value = high
                upper_crossed = False

            if bullf[i]:
                lower_value = low
                lower_crossed = False

            if upper_value is not None and not upper_crossed:
                if close > upper_value:
                    if current_structure == -1:
                        last_break_label = 'ChoCH'
                    else:
                        last_break_label = 'BOS'
                    current_structure = 1
                    upper_crossed = True
                    bull_continuation_high = high

            if lower_value is not None and not lower_crossed:
                if close < lower_value:
                    if current_structure == 1:
                        last_break_label = 'ChoCH'
                    else:
                        last_break_label = 'BOS'
                    current_structure = -1
                    lower_crossed = True
                    bear_continuation_low = low

            if current_structure == 1:
                if bull_continuation_high is None or high > bull_continuation_high:
                    bull_continuation_high = high
            elif current_structure == -1:
                if bear_continuation_low is None or low < bear_continuation_low:
                    bear_continuation_low = low

        strong_level = None
        weak_level = None

        if current_structure == 1:
            strong_level = lower_value
            weak_level = bull_continuation_high
        elif current_structure == -1:
            strong_level = upper_value
            weak_level = bear_continuation_low

        return StructureResult(
            direction=current_structure,
            direction_label=STRUCTURE_LABELS.get(current_structure, 'NEUTRAL'),
            last_break_label=last_break_label,
            strong_level=strong_level,
            weak_level=weak_level
        )


# =============================================================================
# HTF BAR FETCHER
# =============================================================================

class HTFBarFetcher:
    """Fetches higher timeframe bars from Polygon API."""

    TIMEFRAME_CONFIG = {
        'M5': {'multiplier': 5, 'timespan': 'minute'},
        'M15': {'multiplier': 15, 'timespan': 'minute'},
        'H1': {'multiplier': 1, 'timespan': 'hour'},
        'H4': {'multiplier': 4, 'timespan': 'hour'},
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.last_request_time = 0
        self._cache: Dict[str, List[Dict]] = {}

    def _rate_limit(self):
        if API_DELAY > 0:
            elapsed = time_module.time() - self.last_request_time
            if elapsed < API_DELAY:
                time_module.sleep(API_DELAY - elapsed)
        self.last_request_time = time_module.time()

    def _get_cache_key(self, ticker: str, timeframe: str, trade_date: date) -> str:
        return f"{ticker}_{timeframe}_{trade_date.strftime('%Y%m%d')}"

    def fetch_bars(
        self,
        ticker: str,
        timeframe: str,
        trade_date: date,
        end_time: time = None
    ) -> List[Dict]:
        """Fetch HTF bars from Polygon API."""
        if timeframe not in self.TIMEFRAME_CONFIG:
            return []

        cache_key = self._get_cache_key(ticker, timeframe, trade_date)

        if cache_key in self._cache:
            bars = self._cache[cache_key]
            if end_time:
                bars = self._filter_bars_by_time(bars, trade_date, end_time)
            return bars

        lookback_days = HTF_LOOKBACK_DAYS.get(timeframe, 7)
        from_date = trade_date - timedelta(days=lookback_days)
        to_date = trade_date

        config = self.TIMEFRAME_CONFIG[timeframe]
        multiplier = config['multiplier']
        timespan = config['timespan']

        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"

        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    wait_time = API_RETRY_DELAY * (attempt + 1)
                    time_module.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    return []

                data = response.json()

                if data.get('status') not in ['OK', 'DELAYED']:
                    return []

                if 'results' not in data or not data['results']:
                    return []

                bars = []
                for result in data['results']:
                    ts_ms = result['t']
                    ts = datetime.utcfromtimestamp(ts_ms / 1000)

                    bar = {
                        'timestamp': ts,
                        'bar_date': ts.date(),
                        'bar_time': ts.time(),
                        'open': result['o'],
                        'high': result['h'],
                        'low': result['l'],
                        'close': result['c'],
                        'volume': int(result['v']),
                        'vwap': result.get('vw')
                    }
                    bars.append(bar)

                self._cache[cache_key] = bars

                if end_time:
                    bars = self._filter_bars_by_time(bars, trade_date, end_time)

                return bars

            except requests.exceptions.Timeout:
                time_module.sleep(API_RETRY_DELAY)
            except Exception:
                return []

        return []

    def _filter_bars_by_time(self, bars: List[Dict], trade_date: date, end_time: time) -> List[Dict]:
        """Filter bars to before end_time."""
        filtered = []
        for bar in bars:
            bar_date = bar.get('bar_date')
            if bar_date and bar_date < trade_date:
                filtered.append(bar)
            elif bar_date and bar_date == trade_date:
                bar_time = bar.get('bar_time')
                if bar_time and bar_time <= end_time:
                    filtered.append(bar)
        return filtered

    def clear_cache(self):
        self._cache.clear()


# =============================================================================
# STRUCTURE ANALYZER
# =============================================================================

class StructureAnalyzer:
    """High-level analyzer for structure detection."""

    def __init__(self, fetcher: HTFBarFetcher = None):
        self.fetcher = fetcher or HTFBarFetcher()
        self.calculator = MarketStructureCalculator()

    def get_structure(
        self,
        ticker: str,
        timeframe: str,
        trade_date: date,
        bar_time: time
    ) -> StructureResult:
        """Get market structure for a specific timeframe."""
        bars = self.fetcher.fetch_bars(ticker, timeframe, trade_date, bar_time)

        if not bars:
            return StructureResult(
                direction=0,
                direction_label='NEUTRAL',
                last_break_label=None,
                strong_level=None,
                weak_level=None
            )

        return self.calculator.calculate(bars)

    def get_all_structures(
        self,
        ticker: str,
        trade_date: date,
        bar_time: time
    ) -> Dict[str, StructureResult]:
        """Get market structure for all HTF timeframes."""
        results = {}
        for timeframe in ['M5', 'M15', 'H1', 'H4']:
            results[timeframe] = self.get_structure(ticker, timeframe, trade_date, bar_time)
        return results

    def clear_cache(self):
        self.fetcher.clear_cache()
