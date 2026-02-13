"""
Market Structure Calculator - Timeframe Direction and Strong/Weak Levels

Ported from:
- 02_zone_system/01_market_structure/market_structure_calculator.py
- 02_zone_system/02_ticker_structure/ticker_structure_calculator.py

Key features:
- Fractal detection for structure breaks
- Direction determination per timeframe (D1, H4, H1, M15)
- Strong/Weak level identification
- Composite direction calculation with weighted scoring
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from data import get_polygon_client
from core import MarketStructure, TimeframeStructure, Direction

logger = logging.getLogger(__name__)


# Timeframe weights for composite direction
TIMEFRAME_WEIGHTS = {
    'd1': 1.5,
    'h4': 1.5,
    'h1': 1.0,
    'm15': 0.5
}

# Minimum bars needed per timeframe (matches Excel config.TIMEFRAMES[*]['bars_needed'])
MIN_BARS = {
    'd1': 150,
    'h4': 200,
    'h1': 250,
    'm15': 300
}

# Data lookback days (matches Excel config.DATA_LOOKBACK_DAYS)
DATA_LOOKBACK_DAYS = {
    'd1': 250,
    'h4': 100,
    'h1': 50,
    'm15': 15
}


class MarketStructureCalculator:
    """
    Calculate market structure for multiple timeframes.

    Uses fractal detection to identify structure breaks (BOS/ChoCH)
    and determine directional bias with strong/weak levels.

    Matches Excel system: 02_zone_system/01_market_structure/market_structure_calculator.py
    """

    # Match Excel config: FRACTAL_LENGTH = 5
    FRACTAL_LENGTH = 5

    def __init__(self, fractal_length: int = None):
        """
        Initialize calculator.

        Args:
            fractal_length: Total fractal window size (Excel default: 5)
                           Number of bars on each side = fractal_length // 2
        """
        self.client = get_polygon_client()
        # Match Excel: self.length = fractal_length or config.FRACTAL_LENGTH
        #              self.p = int(self.length / 2)
        self.length = fractal_length or self.FRACTAL_LENGTH
        self.p = int(self.length / 2)  # This gives p=2 for length=5

    def calculate(
        self,
        ticker: str,
        analysis_date: date = None,
        end_timestamp: datetime = None
    ) -> MarketStructure:
        """
        Calculate market structure for all timeframes.

        Args:
            ticker: Stock symbol
            analysis_date: Reference date (defaults to today)
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            MarketStructure with D1, H4, H1, M15 analysis
        """
        ticker = ticker.upper()
        analysis_date = analysis_date or date.today()

        logger.info(f"Calculating market structure for {ticker}")

        # Get current price - use end_timestamp if provided for price cutoff
        if end_timestamp:
            # For pre/post market mode, get price from the last bar before cutoff
            price = self._get_price_at_timestamp(ticker, end_timestamp)
        else:
            price = self.client.get_current_price(ticker) or 0.0

        # Calculate each timeframe with end_timestamp
        d1_result = self._calculate_timeframe(ticker, analysis_date, 'd1', end_timestamp)
        h4_result = self._calculate_timeframe(ticker, analysis_date, 'h4', end_timestamp)
        h1_result = self._calculate_timeframe(ticker, analysis_date, 'h1', end_timestamp)
        m15_result = self._calculate_timeframe(ticker, analysis_date, 'm15', end_timestamp)

        # Build structure object
        structure = MarketStructure(
            ticker=ticker,
            datetime=datetime.now(),
            price=price,
            d1=d1_result,
            h4=h4_result,
            h1=h1_result,
            m15=m15_result
        )

        # Calculate composite direction
        structure.composite = self._calculate_composite(structure)

        logger.info(f"  {ticker} Composite: {structure.composite.value}")

        return structure

    def _get_price_at_timestamp(self, ticker: str, end_timestamp: datetime) -> float:
        """
        Get the closing price at a specific timestamp.

        Args:
            ticker: Stock symbol
            end_timestamp: Cutoff timestamp

        Returns:
            Close price of the last bar before the timestamp
        """
        # Fetch the last hour of data up to end_timestamp
        start_date = end_timestamp.date() - timedelta(days=1)
        df = self.client.fetch_hourly_bars(
            ticker, start_date, end_timestamp=end_timestamp
        )
        if df.empty:
            logger.warning(f"No price data for {ticker} at {end_timestamp}")
            return 0.0
        return float(df.iloc[-1]['close'])

    def _calculate_timeframe(
        self,
        ticker: str,
        analysis_date: date,
        timeframe: str,
        end_timestamp: datetime = None
    ) -> TimeframeStructure:
        """
        Calculate structure for a single timeframe.

        Args:
            ticker: Stock symbol
            analysis_date: Reference date
            timeframe: 'd1', 'h4', 'h1', or 'm15'
            end_timestamp: Optional precise end timestamp for pre/post market mode

        Returns:
            TimeframeStructure with direction and strong/weak levels
        """
        # Fetch appropriate data with end_timestamp
        df = self._fetch_timeframe_data(ticker, analysis_date, timeframe, end_timestamp)

        if df.empty or len(df) < MIN_BARS.get(timeframe, 20):
            logger.warning(f"Insufficient {timeframe} data for {ticker}")
            return TimeframeStructure(direction=Direction.NEUTRAL)

        # Detect fractals and calculate structure
        df = self._detect_fractals(df)
        df = self._calculate_structure(df)

        # Get current direction and levels
        direction, strong, weak = self._extract_current_state(df)

        return TimeframeStructure(
            direction=direction,
            strong=strong,
            weak=weak
        )

    def _fetch_timeframe_data(
        self,
        ticker: str,
        analysis_date: date,
        timeframe: str,
        end_timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch OHLC data for the specified timeframe.

        Uses lookback periods matching Excel config.DATA_LOOKBACK_DAYS:
        - D1: 250 days
        - H4: 100 days
        - H1: 50 days
        - M15: 15 days

        Args:
            ticker: Stock symbol
            analysis_date: Reference date
            timeframe: 'd1', 'h4', 'h1', or 'm15'
            end_timestamp: Optional precise end timestamp for pre/post market mode
        """
        lookback = DATA_LOOKBACK_DAYS.get(timeframe, 50)
        start = analysis_date - timedelta(days=lookback)

        if timeframe == 'd1':
            # Daily bars don't use end_timestamp (full days only)
            return self.client.fetch_daily_bars(ticker, start, analysis_date)

        elif timeframe == 'h4':
            # Fetch 4H bars directly from Polygon (matches Excel system)
            # Excel uses: multiplier=4, timespan=hour
            return self.client.fetch_4h_bars(ticker, start, analysis_date, end_timestamp=end_timestamp)

        elif timeframe == 'h1':
            return self.client.fetch_hourly_bars(ticker, start, analysis_date, end_timestamp=end_timestamp)

        elif timeframe == 'm15':
            return self.client.fetch_minute_bars(ticker, start, analysis_date, multiplier=15, end_timestamp=end_timestamp)

        return pd.DataFrame()

    def _detect_fractals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect fractal highs and lows.

        Matches Excel system logic exactly:
        - Bearish fractal (local high): all bars within p on each side have lower highs
        - Bullish fractal (local low): all bars within p on each side have higher lows

        Excel uses: for j in range(1, p+1): df['high'].iloc[i-j] < df['high'].iloc[i]
        """
        p = self.p  # Number of bars on each side (Excel: int(FRACTAL_LENGTH / 2) = 2)
        n = len(df)

        bullish_fractal = np.zeros(n, dtype=bool)
        bearish_fractal = np.zeros(n, dtype=bool)

        if n < self.length:
            df = df.copy()
            df['bearish_fractal'] = bearish_fractal
            df['bullish_fractal'] = bullish_fractal
            return df

        for i in range(p, n - p):
            # Bearish fractal (local high) - matches Excel exactly
            # Excel: before_lower = all(df['high'].iloc[i-j] < df['high'].iloc[i] for j in range(1, p+1))
            #        after_lower = all(df['high'].iloc[i+j] < df['high'].iloc[i] for j in range(1, p+1))
            before_lower = all(df['high'].iloc[i - j] < df['high'].iloc[i] for j in range(1, p + 1))
            after_lower = all(df['high'].iloc[i + j] < df['high'].iloc[i] for j in range(1, p + 1))

            if before_lower and after_lower:
                bearish_fractal[i] = True

            # Bullish fractal (local low) - matches Excel exactly
            # Excel: before_higher = all(df['low'].iloc[i-j] > df['low'].iloc[i] for j in range(1, p+1))
            #        after_higher = all(df['low'].iloc[i+j] > df['low'].iloc[i] for j in range(1, p+1))
            before_higher = all(df['low'].iloc[i - j] > df['low'].iloc[i] for j in range(1, p + 1))
            after_higher = all(df['low'].iloc[i + j] > df['low'].iloc[i] for j in range(1, p + 1))

            if before_higher and after_higher:
                bullish_fractal[i] = True

        df = df.copy()
        df['bearish_fractal'] = bearish_fractal
        df['bullish_fractal'] = bullish_fractal

        return df

    def _calculate_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate market structure based on fractal breaks.

        Matches Excel system logic exactly (market_structure_calculator.py lines 66-150):
        - Tracks upper_crossed/lower_crossed flags to prevent re-triggering
        - Structure turns BULL when close > upper_value (and not already crossed)
        - Structure turns BEAR when close < lower_value (and not already crossed)
        - New fractal resets the crossed flag for that level
        """
        df = df.copy()

        # Initialize columns matching Excel
        df['upper_fractal_value'] = np.nan
        df['lower_fractal_value'] = np.nan
        df['upper_crossed'] = False
        df['lower_crossed'] = False
        df['structure'] = 0
        df['structure_label'] = ''
        df['bull_continuation_high'] = np.nan
        df['bear_continuation_low'] = np.nan

        # State variables matching Excel
        upper_value = None
        upper_crossed = False
        lower_value = None
        lower_crossed = False
        current_structure = 0
        bull_continuation_high = None
        bear_continuation_low = None

        for i in range(len(df)):
            close = df['close'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]

            # Update fractal levels - new fractal resets crossed flag (matches Excel)
            if df['bearish_fractal'].iloc[i]:
                upper_value = df['high'].iloc[i]
                upper_crossed = False

            if df['bullish_fractal'].iloc[i]:
                lower_value = df['low'].iloc[i]
                lower_crossed = False

            # Store current fractal values
            df.loc[df.index[i], 'upper_fractal_value'] = upper_value
            df.loc[df.index[i], 'lower_fractal_value'] = lower_value

            # Check for bullish structure break (matches Excel lines 114-123)
            if upper_value is not None and not upper_crossed:
                if close > upper_value:
                    if current_structure == -1:
                        df.loc[df.index[i], 'structure_label'] = 'ChoCH'
                    else:
                        df.loc[df.index[i], 'structure_label'] = 'BOS'
                    current_structure = 1
                    upper_crossed = True
                    # Initialize continuation high when structure turns bullish
                    bull_continuation_high = high

            # Check for bearish structure break (matches Excel lines 125-134)
            if lower_value is not None and not lower_crossed:
                if close < lower_value:
                    if current_structure == 1:
                        df.loc[df.index[i], 'structure_label'] = 'ChoCH'
                    else:
                        df.loc[df.index[i], 'structure_label'] = 'BOS'
                    current_structure = -1
                    lower_crossed = True
                    # Initialize continuation low when structure turns bearish
                    bear_continuation_low = low

            # Update continuation levels while in structure (matches Excel lines 137-142)
            if current_structure == 1:  # Bull structure
                if bull_continuation_high is None or high > bull_continuation_high:
                    bull_continuation_high = high
            elif current_structure == -1:  # Bear structure
                if bear_continuation_low is None or low < bear_continuation_low:
                    bear_continuation_low = low

            # Store state (matches Excel lines 144-148)
            df.loc[df.index[i], 'structure'] = current_structure
            df.loc[df.index[i], 'upper_crossed'] = upper_crossed
            df.loc[df.index[i], 'lower_crossed'] = lower_crossed
            df.loc[df.index[i], 'bull_continuation_high'] = bull_continuation_high
            df.loc[df.index[i], 'bear_continuation_low'] = bear_continuation_low

        return df

    def _extract_current_state(
        self,
        df: pd.DataFrame
    ) -> Tuple[Direction, Optional[float], Optional[float]]:
        """
        Extract current direction and strong/weak levels from calculated DataFrame.

        Matches Excel system logic (market_structure_calculator.py lines 199-208):
        - Bull: strong = lower_fractal_value, weak = bull_continuation_high
        - Bear: strong = upper_fractal_value, weak = bear_continuation_low
        """
        if df.empty:
            return Direction.NEUTRAL, None, None

        current_structure = int(df['structure'].iloc[-1])

        # Determine direction
        if current_structure == 1:
            direction = Direction.BULL
        elif current_structure == -1:
            direction = Direction.BEAR
        else:
            direction = Direction.NEUTRAL

        # Determine strong/weak levels (matches Excel lines 199-208)
        strong_level = None
        weak_level = None

        if current_structure == 1:  # Bull
            # Strong (invalidation) = lower fractal (support that if broken = ChoCH)
            strong_level = df['lower_fractal_value'].iloc[-1]
            # Weak (continuation) = highest high since structure turned bullish
            weak_level = df['bull_continuation_high'].iloc[-1]
        elif current_structure == -1:  # Bear
            # Strong (invalidation) = upper fractal (resistance that if broken = ChoCH)
            strong_level = df['upper_fractal_value'].iloc[-1]
            # Weak (continuation) = lowest low since structure turned bearish
            weak_level = df['bear_continuation_low'].iloc[-1]

        # Convert NaN/None to None and ensure Python float type
        if strong_level is not None and pd.notna(strong_level):
            strong_level = float(strong_level)
        else:
            strong_level = None

        if weak_level is not None and pd.notna(weak_level):
            weak_level = float(weak_level)
        else:
            weak_level = None

        return direction, strong_level, weak_level

    def _calculate_composite(self, structure: MarketStructure) -> Direction:
        """
        Calculate composite direction using weighted scoring.

        Weights: D1=1.5, H4=1.5, H1=1.0, M15=0.5
        Bull+: score >= 3.5
        Bear+: score <= -3.5
        """
        score = 0.0

        for tf_name, weight in TIMEFRAME_WEIGHTS.items():
            tf_struct = getattr(structure, tf_name)
            if tf_struct.direction in [Direction.BULL, Direction.BULL_PLUS]:
                score += weight
            elif tf_struct.direction in [Direction.BEAR, Direction.BEAR_PLUS]:
                score -= weight

        if score >= 3.5:
            return Direction.BULL_PLUS
        elif score > 0:
            return Direction.BULL
        elif score <= -3.5:
            return Direction.BEAR_PLUS
        elif score < 0:
            return Direction.BEAR
        else:
            # Tie-breaker: use M15
            if structure.m15.direction == Direction.BULL:
                return Direction.BULL
            elif structure.m15.direction == Direction.BEAR:
                return Direction.BEAR
            return Direction.NEUTRAL


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def calculate_market_structure(
    ticker: str,
    analysis_date: date = None,
    end_timestamp: datetime = None
) -> MarketStructure:
    """
    Calculate market structure for a ticker.

    Args:
        ticker: Stock symbol
        analysis_date: Reference date (defaults to today)
        end_timestamp: Optional precise end timestamp for pre/post market mode

    Returns:
        MarketStructure with D1, H4, H1, M15 analysis and composite
    """
    calc = MarketStructureCalculator()
    return calc.calculate(ticker, analysis_date, end_timestamp)
