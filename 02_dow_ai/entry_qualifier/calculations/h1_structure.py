"""
H1 Structure Calculations
Epoch Trading System v1 - XIII Trading LLC

Determines market structure state on H1 timeframe.
Structure is based on higher highs/lower lows pattern.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class MarketStructure(Enum):
    """Market structure states."""
    BULL = "BULL"      # Higher highs, higher lows
    BEAR = "BEAR"      # Lower highs, lower lows
    NEUTRAL = "NEUT"   # Mixed/consolidation


def calculate_structure(bars: List[dict], lookback: int = 5) -> MarketStructure:
    """
    Determine market structure from H1 bars.

    Uses swing high/low analysis to determine structure:
    - BULL: Recent higher high AND higher low
    - BEAR: Recent lower high AND lower low
    - NEUTRAL: Mixed signals or consolidation

    Args:
        bars: List of H1 bar dictionaries with 'high', 'low' keys
        lookback: Number of bars to analyze for swings

    Returns:
        MarketStructure enum value
    """
    if len(bars) < lookback + 2:
        return MarketStructure.NEUTRAL

    # Get recent bars for analysis
    recent = bars[-(lookback + 2):]

    # Find swing points (local highs and lows)
    highs = [bar.get('high', bar.get('h', 0)) for bar in recent]
    lows = [bar.get('low', bar.get('l', 0)) for bar in recent]

    # Compare first half highs/lows to second half
    mid = len(recent) // 2

    first_high = max(highs[:mid])
    second_high = max(highs[mid:])
    first_low = min(lows[:mid])
    second_low = min(lows[mid:])

    # Determine structure
    higher_high = second_high > first_high
    higher_low = second_low > first_low
    lower_high = second_high < first_high
    lower_low = second_low < first_low

    if higher_high and higher_low:
        return MarketStructure.BULL
    elif lower_high and lower_low:
        return MarketStructure.BEAR
    else:
        return MarketStructure.NEUTRAL


def get_h1_bar_for_timestamp(
    h1_bars: List[dict],
    m1_timestamp: int
) -> Optional[dict]:
    """
    Find the H1 bar that contains a given M1 timestamp.

    Args:
        h1_bars: List of H1 bars with 'timestamp' key (milliseconds)
        m1_timestamp: M1 bar timestamp in milliseconds

    Returns:
        The H1 bar dict, or None if not found
    """
    if not h1_bars:
        return None

    # H1 bar timestamp is the start of the hour
    # M1 timestamp falls within an H1 bar if:
    # h1_timestamp <= m1_timestamp < h1_timestamp + 3600000 (1 hour in ms)
    hour_ms = 3600000

    for h1_bar in reversed(h1_bars):
        h1_ts = h1_bar.get('timestamp', 0)
        if h1_ts <= m1_timestamp < h1_ts + hour_ms:
            return h1_bar

    # If no exact match, return the most recent H1 bar
    return h1_bars[-1] if h1_bars else None


def calculate_structure_for_bars(
    h1_bars: List[dict],
    m1_bars: List[dict],
    lookback: int = 5
) -> List[dict]:
    """
    Calculate H1 structure for each M1 bar.

    For each M1 bar, finds the corresponding H1 bar and calculates
    the structure based on H1 bars up to that point.

    Args:
        h1_bars: List of H1 bar dictionaries
        m1_bars: List of M1 bar dictionaries with 'timestamp' key
        lookback: Number of H1 bars to analyze for structure

    Returns:
        List of dicts with 'h1_structure' key for each M1 bar
    """
    results = []

    if not h1_bars:
        # No H1 data available - return NEUTRAL for all
        return [{'h1_structure': MarketStructure.NEUTRAL, 'h1_display': 'NEUT'}
                for _ in m1_bars]

    for m1_bar in m1_bars:
        m1_ts = m1_bar.get('timestamp', 0)

        # Find H1 bars up to this M1 timestamp
        relevant_h1 = [b for b in h1_bars if b.get('timestamp', 0) <= m1_ts]

        if len(relevant_h1) >= lookback + 2:
            structure = calculate_structure(relevant_h1, lookback)
        else:
            structure = MarketStructure.NEUTRAL

        results.append({
            'h1_structure': structure,
            'h1_display': structure.value
        })

    return results


class StructureCache:
    """
    Generic cache for timeframe bar data to minimize API calls.

    Caches bars for any timeframe and refreshes when a new bar closes.
    Used for M5, M15, etc. Parametrized by timeframe duration in milliseconds.

    Args:
        timeframe_ms: Duration of one bar in milliseconds
                      (e.g., 300_000 for M5, 900_000 for M15)
    """

    def __init__(self, timeframe_ms: int):
        self.timeframe_ms = timeframe_ms
        self._cache: Dict[str, Dict[str, Any]] = {}
        # ticker -> {'bars': [...], 'last_update': datetime, 'last_bar_ts': int}

    def get_bars(self, ticker: str) -> Optional[List[dict]]:
        """Get cached bars for a ticker."""
        if ticker in self._cache:
            return self._cache[ticker].get('bars')
        return None

    def set_bars(self, ticker: str, bars: List[dict]):
        """Cache bars for a ticker."""
        last_bar_ts = bars[-1].get('timestamp', 0) if bars else 0
        self._cache[ticker] = {
            'bars': bars,
            'last_update': datetime.now(),
            'last_bar_ts': last_bar_ts
        }

    def needs_refresh(self, ticker: str, current_bar_ts: int) -> bool:
        """
        Check if data needs to be refreshed.

        Returns True if:
        - No cache exists for ticker
        - A new bar has closed (current bar timestamp > cached)

        Args:
            ticker: Stock symbol
            current_bar_ts: Current bar start timestamp (milliseconds)
        """
        if ticker not in self._cache:
            return True

        cached_ts = self._cache[ticker].get('last_bar_ts', 0)
        return current_bar_ts > cached_ts

    def clear(self, ticker: str = None):
        """Clear cache for a ticker or all tickers."""
        if ticker:
            self._cache.pop(ticker, None)
        else:
            self._cache.clear()


class H1StructureCache:
    """
    Cache for H1 bar data to minimize API calls.

    H1 data is fetched on initial load and refreshed hourly.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        # ticker -> {'bars': [...], 'last_update': datetime, 'last_h1_ts': int}

    def get_bars(self, ticker: str) -> Optional[List[dict]]:
        """Get cached H1 bars for a ticker."""
        if ticker in self._cache:
            return self._cache[ticker].get('bars')
        return None

    def set_bars(self, ticker: str, bars: List[dict]):
        """Cache H1 bars for a ticker."""
        last_h1_ts = bars[-1].get('timestamp', 0) if bars else 0
        self._cache[ticker] = {
            'bars': bars,
            'last_update': datetime.now(),
            'last_h1_ts': last_h1_ts
        }

    def needs_refresh(self, ticker: str, current_h1_ts: int) -> bool:
        """
        Check if H1 data needs to be refreshed.

        Returns True if:
        - No cache exists for ticker
        - A new H1 bar has closed (current H1 timestamp > cached)

        Args:
            ticker: Stock symbol
            current_h1_ts: Current H1 bar start timestamp (milliseconds)
        """
        if ticker not in self._cache:
            return True

        cached_ts = self._cache[ticker].get('last_h1_ts', 0)
        return current_h1_ts > cached_ts

    def clear(self, ticker: str = None):
        """Clear cache for a ticker or all tickers."""
        if ticker:
            self._cache.pop(ticker, None)
        else:
            self._cache.clear()
