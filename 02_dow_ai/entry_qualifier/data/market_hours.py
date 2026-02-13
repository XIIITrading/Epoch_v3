"""
Market Hours Logic
Epoch Trading System v1 - XIII Trading LLC

Handles market open/close detection for US equity markets.
"""
from datetime import datetime, time
from typing import Tuple
import pytz


class MarketHours:
    """
    Handles market hours detection for US equity markets.

    Trading hours (Eastern Time):
    - Pre-market: 4:00 AM - 9:30 AM
    - Regular: 9:30 AM - 4:00 PM
    - After-hours: 4:00 PM - 8:00 PM
    - Closed: 8:00 PM - 4:00 AM (and weekends)
    """

    # Market hours in Eastern Time
    PREMARKET_START = time(4, 0)
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)
    AFTERHOURS_END = time(20, 0)

    # US Market holidays for 2024-2026 (add more as needed)
    HOLIDAYS = {
        # 2024
        datetime(2024, 1, 1).date(),   # New Year's Day
        datetime(2024, 1, 15).date(),  # MLK Day
        datetime(2024, 2, 19).date(),  # Presidents Day
        datetime(2024, 3, 29).date(),  # Good Friday
        datetime(2024, 5, 27).date(),  # Memorial Day
        datetime(2024, 6, 19).date(),  # Juneteenth
        datetime(2024, 7, 4).date(),   # Independence Day
        datetime(2024, 9, 2).date(),   # Labor Day
        datetime(2024, 11, 28).date(), # Thanksgiving
        datetime(2024, 12, 25).date(), # Christmas
        # 2025
        datetime(2025, 1, 1).date(),   # New Year's Day
        datetime(2025, 1, 20).date(),  # MLK Day
        datetime(2025, 2, 17).date(),  # Presidents Day
        datetime(2025, 4, 18).date(),  # Good Friday
        datetime(2025, 5, 26).date(),  # Memorial Day
        datetime(2025, 6, 19).date(),  # Juneteenth
        datetime(2025, 7, 4).date(),   # Independence Day
        datetime(2025, 9, 1).date(),   # Labor Day
        datetime(2025, 11, 27).date(), # Thanksgiving
        datetime(2025, 12, 25).date(), # Christmas
        # 2026
        datetime(2026, 1, 1).date(),   # New Year's Day
        datetime(2026, 1, 19).date(),  # MLK Day
        datetime(2026, 2, 16).date(),  # Presidents Day
        datetime(2026, 4, 3).date(),   # Good Friday
        datetime(2026, 5, 25).date(),  # Memorial Day
        datetime(2026, 6, 19).date(),  # Juneteenth
        datetime(2026, 7, 3).date(),   # Independence Day (observed)
        datetime(2026, 9, 7).date(),   # Labor Day
        datetime(2026, 11, 26).date(), # Thanksgiving
        datetime(2026, 12, 25).date(), # Christmas
    }

    def __init__(self):
        self.tz = pytz.timezone('America/New_York')

    def get_current_time(self) -> datetime:
        """Get current time in Eastern timezone."""
        return datetime.now(self.tz)

    def is_weekend(self, dt: datetime = None) -> bool:
        """Check if given datetime is a weekend."""
        if dt is None:
            dt = self.get_current_time()
        return dt.weekday() >= 5  # Saturday = 5, Sunday = 6

    def is_holiday(self, dt: datetime = None) -> bool:
        """Check if given datetime is a market holiday."""
        if dt is None:
            dt = self.get_current_time()
        return dt.date() in self.HOLIDAYS

    def is_trading_hours(self, dt: datetime = None) -> bool:
        """
        Check if market is in trading hours (including extended hours).

        Returns True for pre-market, regular, and after-hours sessions.
        """
        if dt is None:
            dt = self.get_current_time()

        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        # Check weekend
        if self.is_weekend(dt):
            return False

        # Check holiday
        if self.is_holiday(dt):
            return False

        # Check time of day
        current_time = dt.time()
        return self.PREMARKET_START <= current_time < self.AFTERHOURS_END

    def get_market_status(self, dt: datetime = None) -> Tuple[bool, str]:
        """
        Get market status and description.

        Returns:
            Tuple of (is_open, status_string)
        """
        if dt is None:
            dt = self.get_current_time()

        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        # Check weekend
        if self.is_weekend(dt):
            return False, "Market Closed (Weekend)"

        # Check holiday
        if self.is_holiday(dt):
            return False, "Market Closed (Holiday)"

        current_time = dt.time()

        # Check different sessions
        if current_time < self.PREMARKET_START:
            return False, "Market Closed"
        elif current_time < self.MARKET_OPEN:
            return True, "Pre-Market"
        elif current_time < self.MARKET_CLOSE:
            return True, "Market Open"
        elif current_time < self.AFTERHOURS_END:
            return True, "After-Hours"
        else:
            return False, "Market Closed"

    def seconds_until_next_minute(self, dt: datetime = None) -> int:
        """
        Calculate seconds until the next minute boundary.

        Used to sync refresh timer to minute boundaries (e.g., :01, :02, etc.)
        """
        if dt is None:
            dt = self.get_current_time()

        seconds_into_minute = dt.second + (dt.microsecond / 1_000_000)
        return int(60 - seconds_into_minute)

    def get_next_minute_boundary(self, dt: datetime = None) -> datetime:
        """Get the datetime of the next minute boundary."""
        if dt is None:
            dt = self.get_current_time()

        # Round up to next minute
        next_minute = dt.replace(second=0, microsecond=0)
        from datetime import timedelta
        next_minute += timedelta(minutes=1)
        return next_minute
