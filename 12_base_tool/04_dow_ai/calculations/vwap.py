"""
DOW AI - VWAP Calculator
Epoch Trading System v1 - XIII Trading LLC

Volume Weighted Average Price calculation for intraday analysis.
"""
import pandas as pd
from datetime import datetime, time
import pytz
from typing import Dict, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TIMEZONE, VERBOSE, debug_print

# Add shared library
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03_indicators" / "python"))
from core.vwap import calculate_vwap as _shared_calculate_vwap


@dataclass
class VWAPResult:
    """VWAP calculation result."""
    vwap: float
    price_diff: float
    price_pct: float
    side: str  # 'ABOVE', 'BELOW', 'AT'


class VWAPCalculator:
    """
    Calculates Volume Weighted Average Price.

    VWAP is calculated from the session start (9:30 AM ET by default)
    and shows the average price weighted by volume throughout the day.
    """

    def __init__(
        self,
        timezone: str = None,
        session_start_hour: int = 9,
        session_start_minute: int = 30,
        verbose: bool = None
    ):
        """
        Initialize VWAP calculator.

        Args:
            timezone: Timezone for session start (default from config)
            session_start_hour: Hour session starts (default 9)
            session_start_minute: Minute session starts (default 30)
            verbose: Enable verbose output
        """
        self.tz = pytz.timezone(timezone or TIMEZONE)
        self.session_start_hour = session_start_hour
        self.session_start_minute = session_start_minute
        self.verbose = verbose if verbose is not None else VERBOSE

    def calculate_vwap(self, df: pd.DataFrame) -> float:
        """
        Calculate VWAP from session start.

        Args:
            df: M1 DataFrame with timestamp, high, low, close, volume

        Returns:
            Current VWAP value
        """
        if df is None or df.empty:
            if self.verbose:
                debug_print("Empty DataFrame for VWAP calculation")
            return 0.0

        df = df.copy()

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Make timezone-aware if not already
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(self.tz)
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.tz)

        # Get the date of the last bar
        last_date = df['timestamp'].iloc[-1].date()

        # Create session start timestamp
        session_start = self.tz.localize(datetime(
            year=last_date.year,
            month=last_date.month,
            day=last_date.day,
            hour=self.session_start_hour,
            minute=self.session_start_minute,
            second=0
        ))

        # Filter to current session
        session_df = df[df['timestamp'] >= session_start].copy()

        if session_df.empty:
            if self.verbose:
                debug_print("No data in current session for VWAP")
            return 0.0

        # Convert DataFrame to list of dicts for shared library
        bars = session_df.to_dict('records')

        # Use shared library calculation
        vwap = _shared_calculate_vwap(bars)

        if vwap is None:
            return 0.0

        if self.verbose:
            debug_print(f"VWAP: ${vwap:.2f} (from {len(session_df)} bars)")

        return float(vwap)

    def get_price_vs_vwap(self, current_price: float, vwap: float) -> VWAPResult:
        """
        Get price relationship to VWAP.

        Args:
            current_price: Current stock price
            vwap: Calculated VWAP value

        Returns:
            VWAPResult with difference, percentage, and side
        """
        if vwap == 0:
            return VWAPResult(
                vwap=0.0,
                price_diff=0.0,
                price_pct=0.0,
                side='N/A'
            )

        diff = current_price - vwap
        pct = (diff / vwap) * 100

        if diff > 0.01:
            side = 'ABOVE'
        elif diff < -0.01:
            side = 'BELOW'
        else:
            side = 'AT'

        return VWAPResult(
            vwap=vwap,
            price_diff=diff,
            price_pct=pct,
            side=side
        )

    def analyze(self, df: pd.DataFrame, current_price: float = None) -> VWAPResult:
        """
        Complete VWAP analysis.

        Args:
            df: M1 DataFrame
            current_price: Current price (uses last close if None)

        Returns:
            VWAPResult with all metrics
        """
        vwap = self.calculate_vwap(df)

        if current_price is None and df is not None and not df.empty:
            current_price = float(df.iloc[-1]['close'])
        elif current_price is None:
            current_price = 0.0

        return self.get_price_vs_vwap(current_price, vwap)


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("VWAP CALCULATOR - STANDALONE TEST")
    print("=" * 60)

    from data.polygon_fetcher import PolygonFetcher

    fetcher = PolygonFetcher(verbose=False)
    calculator = VWAPCalculator(verbose=True)

    # Test with SPY M1 data
    print("\n[TEST 1] SPY VWAP Calculation...")
    df = fetcher.fetch_bars('SPY', 'M1', bars_needed=200)

    if df is not None:
        current_price = float(df.iloc[-1]['close'])
        result = calculator.analyze(df, current_price)

        print(f"  Current Price: ${current_price:.2f}")
        print(f"  VWAP:          ${result.vwap:.2f}")
        print(f"  Difference:    ${result.price_diff:+.2f}")
        print(f"  Percent:       {result.price_pct:+.2f}%")
        print(f"  Side:          {result.side}")
    else:
        print("  FAILED: Could not fetch data")

    # Test with TSLA
    print("\n[TEST 2] TSLA VWAP Calculation...")
    df = fetcher.fetch_bars('TSLA', 'M1', bars_needed=200)

    if df is not None:
        current_price = float(df.iloc[-1]['close'])
        result = calculator.analyze(df, current_price)

        print(f"  Current Price: ${current_price:.2f}")
        print(f"  VWAP:          ${result.vwap:.2f}")
        print(f"  Side:          {result.side} by {result.price_pct:+.2f}%")
    else:
        print("  FAILED: Could not fetch data")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
