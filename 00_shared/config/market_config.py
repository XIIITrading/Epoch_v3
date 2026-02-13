"""
Epoch Trading System - Market Configuration
============================================

Market hours, holidays, and trading calendar configuration.

Usage:
    from shared.config import MarketConfig
    mc = MarketConfig()
    if mc.is_market_open():
        ...
"""

from datetime import datetime, time, date
from typing import Optional, Tuple
import pytz
from dataclasses import dataclass, field


@dataclass
class MarketConfig:
    """
    Market timing and calendar configuration.
    """

    # ==========================================================================
    # TIMEZONE
    # ==========================================================================
    TIMEZONE_STR: str = "America/New_York"

    @property
    def tz(self):
        return pytz.timezone(self.TIMEZONE_STR)

    # ==========================================================================
    # TRADING HOURS (Eastern Time)
    # ==========================================================================
    PREMARKET_START: time = field(default_factory=lambda: time(4, 0))
    PREMARKET_END: time = field(default_factory=lambda: time(9, 30))
    MARKET_OPEN: time = field(default_factory=lambda: time(9, 30))
    MARKET_CLOSE: time = field(default_factory=lambda: time(16, 0))
    AFTERHOURS_END: time = field(default_factory=lambda: time(20, 0))

    # ==========================================================================
    # KEY TIMES
    # ==========================================================================
    FIRST_HOUR_END: time = field(default_factory=lambda: time(10, 30))
    LUNCH_START: time = field(default_factory=lambda: time(12, 0))
    LUNCH_END: time = field(default_factory=lambda: time(13, 30))
    POWER_HOUR_START: time = field(default_factory=lambda: time(15, 0))

    def now_et(self) -> datetime:
        """Get current time in Eastern timezone."""
        return datetime.now(self.tz)

    def is_market_open(self, dt: Optional[datetime] = None) -> bool:
        """Check if market is currently open."""
        if dt is None:
            dt = self.now_et()

        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        # Check weekday (0=Monday, 4=Friday)
        if dt.weekday() > 4:
            return False

        # Check time
        current_time = dt.time()
        return self.MARKET_OPEN <= current_time < self.MARKET_CLOSE

    def is_premarket(self, dt: Optional[datetime] = None) -> bool:
        """Check if currently in premarket session."""
        if dt is None:
            dt = self.now_et()

        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        if dt.weekday() > 4:
            return False

        current_time = dt.time()
        return self.PREMARKET_START <= current_time < self.MARKET_OPEN

    def is_afterhours(self, dt: Optional[datetime] = None) -> bool:
        """Check if currently in after-hours session."""
        if dt is None:
            dt = self.now_et()

        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        if dt.weekday() > 4:
            return False

        current_time = dt.time()
        return self.MARKET_CLOSE <= current_time < self.AFTERHOURS_END

    def get_session(self, dt: Optional[datetime] = None) -> str:
        """
        Get current market session.

        Returns:
            'premarket', 'open', 'first_hour', 'lunch', 'power_hour', 'afterhours', 'closed'
        """
        if dt is None:
            dt = self.now_et()

        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        # Weekend
        if dt.weekday() > 4:
            return 'closed'

        current_time = dt.time()

        if current_time < self.PREMARKET_START:
            return 'closed'
        elif current_time < self.MARKET_OPEN:
            return 'premarket'
        elif current_time < self.FIRST_HOUR_END:
            return 'first_hour'
        elif current_time < self.LUNCH_START:
            return 'open'
        elif current_time < self.LUNCH_END:
            return 'lunch'
        elif current_time < self.POWER_HOUR_START:
            return 'open'
        elif current_time < self.MARKET_CLOSE:
            return 'power_hour'
        elif current_time < self.AFTERHOURS_END:
            return 'afterhours'
        else:
            return 'closed'

    def get_market_hours_today(self) -> Tuple[datetime, datetime]:
        """Get market open and close times for today."""
        today = self.now_et().date()
        market_open = self.tz.localize(datetime.combine(today, self.MARKET_OPEN))
        market_close = self.tz.localize(datetime.combine(today, self.MARKET_CLOSE))
        return market_open, market_close

    def get_trading_date(self, dt: Optional[datetime] = None) -> date:
        """
        Get the trading date for a given datetime.
        Before market open, returns previous trading day.
        """
        if dt is None:
            dt = self.now_et()

        if dt.tzinfo is None:
            dt = self.tz.localize(dt)

        current_date = dt.date()

        # If before market open, use previous day
        if dt.time() < self.MARKET_OPEN:
            current_date = current_date - timedelta(days=1)

        # Adjust for weekends
        while current_date.weekday() > 4:
            current_date = current_date - timedelta(days=1)

        return current_date


# Need this import for get_trading_date
from datetime import timedelta

# Default instance
market_config = MarketConfig()
