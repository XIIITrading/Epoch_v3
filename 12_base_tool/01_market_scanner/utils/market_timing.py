"""
Market timing utilities.
"""
from datetime import datetime, time, timezone, timedelta
from typing import Tuple
import pytz
import pandas_market_calendars as mcal

class MarketTiming:
    """Utilities for market hours and timing."""
    
    def __init__(self, exchange: str = 'NYSE'):
        """Initialize with market calendar."""
        self.calendar = mcal.get_calendar(exchange)
    
    def is_market_open(self, timestamp: datetime) -> bool:
        """Check if market is open at given time."""
        # Ensure timezone aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Get market schedule for the date
        schedule = self.calendar.schedule(
            start_date=timestamp.date(),
            end_date=timestamp.date()
        )
        
        if schedule.empty:
            return False
        
        market_open = schedule.iloc[0]['market_open']
        market_close = schedule.iloc[0]['market_close']
        
        return market_open <= timestamp <= market_close
    
    def is_premarket(self, timestamp: datetime) -> bool:
        """Check if in pre-market hours."""
        # Ensure timezone aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Pre-market: 4:00 AM - 9:30 AM ET
        et_tz = pytz.timezone('US/Eastern')
        et_time = timestamp.astimezone(et_tz)
        
        premarket_start = time(4, 0)
        market_open = time(9, 30)
        
        return premarket_start <= et_time.time() < market_open
    
    def get_next_market_open(self, from_date: datetime) -> datetime:
        """Get next market open time."""
        # Get schedule for next few days
        schedule = self.calendar.schedule(
            start_date=from_date.date(),
            end_date=from_date.date() + timedelta(days=10)
        )
        
        if not schedule.empty:
            return schedule.iloc[0]['market_open']
        
        return None