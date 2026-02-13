"""
Camarilla Pivot Calculator v1.5
Meridian Trading System v2 - XIII Trading LLC

VERSION: 1.5
DATE: 2025-11-14
CHANGES: Using EXACT Polygon API format from working example (adjusted="true", sort="asc")

CHANGELOG:
v1.5 - Use exact Polygon API format: adjusted="true" (string), sort="asc", limit=120
v1.4 - Tried proper from < to ordering (still failed)
v1.3 - Tried to fetch PRIOR COMPLETE periods (date backwards - failed)
v1.2 - Attempted fix for weekly/monthly date ranges (failed)
v1.1 - Fixed date format conversion (partial success - daily only)
v1.0 - Initial implementation (partial success - daily only)
"""

__version__ = "1.5"
__date__ = "2025-11-14"

from polygon import RESTClient
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

# Import API key from credentials
try:
    from credentials import POLYGON_API_KEY
    client = RESTClient(POLYGON_API_KEY)
except ImportError:
    print("Warning: credentials.py not found. Using fallback API key.")
    client = RESTClient("f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CamarillaCalculator:
    """
    Calculate Camarilla pivot levels for multiple timeframes.
    
    Camarilla Pivot Formula:
    - Range = High - Low
    - S6 = Close - (Range × 1.000)
    - S4 = Close - (Range × 0.618)
    - S3 = Close - (Range × 0.500)
    - R3 = Close + (Range × 0.500)
    - R4 = Close + (Range × 0.618)
    - R6 = Close + (Range × 1.000)
    
    Version: 1.5
    """
    
    def __init__(self):
        """Initialize the Camarilla Calculator."""
        self.client = client
        self.version = __version__
        self.timeframes = {
            'daily': 'd1',
            'weekly': 'w1',
            'monthly': 'm1'
        }
    
    def convert_date_format(self, date_str: str) -> str:
        """
        Convert date from mm-dd-yy to YYYY-MM-DD format.
        
        Args:
            date_str: Date in mm-dd-yy format (e.g., "11-14-25")
        
        Returns:
            Date in YYYY-MM-DD format (e.g., "2025-11-14")
        """
        try:
            # Parse mm-dd-yy format
            date_obj = datetime.strptime(date_str, "%m-%d-%y")
            # Return YYYY-MM-DD format
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # If already in YYYY-MM-DD format, return as-is
            return date_str
    
    def get_prior_period_ohlc(self, ticker: str, date_str: str, timeframe: str = 'daily') -> Optional[Dict]:
        """
        Get Prior Period OHLC for Camarilla calculations.
        
        Args:
            ticker: Stock ticker symbol
            date_str: Reference date in YYYY-MM-DD format
            timeframe: 'daily', 'weekly', or 'monthly'
        
        Returns:
            dict with 'high', 'low', 'close' keys or None if data unavailable
        """
        year, month, day = map(int, date_str.split('-'))
        reference_date = datetime(year, month, day)
        
        try:
            if timeframe == 'daily':
                # Get prior trading day - try up to 5 days back to handle holidays
                for days_back in range(1, 6):
                    prior_day = reference_date - timedelta(days=days_back)
                    
                    # Skip weekends
                    if prior_day.weekday() >= 5:  # Saturday or Sunday
                        continue
                    
                    prior_str = prior_day.strftime("%Y-%m-%d")
                    
                    # Fetch daily bar - EXACT format from working example
                    aggs = []
                    for a in self.client.list_aggs(
                        ticker,
                        1,
                        "day",
                        prior_str,
                        prior_str,
                        adjusted="true",
                        sort="asc",
                        limit=120,
                    ):
                        aggs.append(a)
                    
                    if aggs:
                        bar = aggs[0]
                        logger.info(f"Daily data found for {ticker} on {prior_str}")
                        return {
                            'high': bar.high,
                            'low': bar.low,
                            'close': bar.close,
                            'open': bar.open,
                            'date': prior_str
                        }
                
                # If no data found after trying 5 days, return None
                logger.warning(f"No daily data found for {ticker} in the last 5 trading days from {reference_date}")
                return None
            
            elif timeframe == 'weekly':
                # Get weekly bars - EXACT format from working example
                # Use 30 days lookback to get recent weeks
                from_date = (reference_date - timedelta(days=30)).strftime("%Y-%m-%d")
                to_date = reference_date.strftime("%Y-%m-%d")
                
                logger.info(f"Weekly fetch: {from_date} to {to_date}")
                
                # Fetch weekly bars using EXACT working format
                aggs = []
                for a in self.client.list_aggs(
                    ticker,
                    1,
                    "week",
                    from_date,
                    to_date,
                    adjusted="true",
                    sort="asc",
                    limit=120,
                ):
                    aggs.append(a)
                
                # Get the most recent complete week (last bar in asc order)
                # If we have multiple weeks, take the second-to-last (prior complete week)
                if len(aggs) >= 2:
                    bar = aggs[-2]  # Second to last = prior complete week
                    return {
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'open': bar.open,
                        'timestamp': bar.timestamp
                    }
                elif len(aggs) == 1:
                    bar = aggs[0]
                    return {
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'open': bar.open,
                        'timestamp': bar.timestamp
                    }
            
            elif timeframe == 'monthly':
                # Get monthly bars - EXACT format from working example
                # Use 120 days lookback to get recent months
                from_date = (reference_date - timedelta(days=120)).strftime("%Y-%m-%d")
                to_date = reference_date.strftime("%Y-%m-%d")
                
                logger.info(f"Monthly fetch: {from_date} to {to_date}")
                
                # Fetch monthly bars using EXACT working format
                aggs = []
                for a in self.client.list_aggs(
                    ticker,
                    1,
                    "month",
                    from_date,
                    to_date,
                    adjusted="true",
                    sort="asc",
                    limit=120,
                ):
                    aggs.append(a)
                
                # Get the most recent complete month (last bar in asc order)
                # If we have multiple months, take the second-to-last (prior complete month)
                if len(aggs) >= 2:
                    bar = aggs[-2]  # Second to last = prior complete month
                    return {
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'open': bar.open,
                        'timestamp': bar.timestamp
                    }
                elif len(aggs) == 1:
                    bar = aggs[0]
                    return {
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'open': bar.open,
                        'timestamp': bar.timestamp
                    }
        
        except Exception as e:
            logger.warning(f"Error fetching {timeframe} data for {ticker}: {e}")
            return None
        
        return None
    
    def calculate_camarilla_levels(self, high: float, low: float, close: float) -> Dict:
        """
        Calculate Camarilla pivot levels.
        
        Args:
            high: Prior period high
            low: Prior period low
            close: Prior period close
        
        Returns:
            dict with Camarilla levels (S6, S4, S3, R3, R4, R6)
        """
        price_range = high - low
        
        return {
            's6': close - (price_range * 1.000),
            's4': close - (price_range * 0.618),
            's3': close - (price_range * 0.500),
            'r3': close + (price_range * 0.500),
            'r4': close + (price_range * 0.618),
            'r6': close + (price_range * 1.000)
        }
    
    def calculate_metrics(self, ticker: str, date_str: str) -> Dict:
        """
        Calculate Camarilla levels for all three timeframes.
        
        Args:
            ticker: Stock ticker symbol
            date_str: Reference date in mm-dd-yy format
        
        Returns:
            Dictionary with flattened structure:
            {
                'd1_s6': value, 'd1_s4': value, 'd1_s3': value,
                'd1_r3': value, 'd1_r4': value, 'd1_r6': value,
                'w1_s6': value, 'w1_s4': value, ... (same pattern),
                'm1_s6': value, 'm1_s4': value, ... (same pattern)
            }
        """
        # Convert date format
        date_formatted = self.convert_date_format(date_str)
        
        results = {}
        
        # Process each timeframe
        for timeframe_name, timeframe_prefix in self.timeframes.items():
            # Get prior period OHLC
            ohlc_data = self.get_prior_period_ohlc(ticker, date_formatted, timeframe_name)
            
            if ohlc_data:
                # Calculate Camarilla levels
                levels = self.calculate_camarilla_levels(
                    ohlc_data['high'],
                    ohlc_data['low'],
                    ohlc_data['close']
                )
                
                # Flatten into results with timeframe prefix
                for level_name, level_value in levels.items():
                    field_name = f"{timeframe_prefix}_{level_name}"
                    results[field_name] = round(level_value, 2)
            else:
                # If data unavailable, set levels to None
                for level_name in ['s6', 's4', 's3', 'r3', 'r4', 'r6']:
                    field_name = f"{timeframe_prefix}_{level_name}"
                    results[field_name] = None
        
        return results


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    
    print(f"Camarilla Calculator v{__version__}")
    print(f"Date: {__date__}")
    print()
    
    if len(sys.argv) != 3:
        print("Usage: python camarilla_calculator.py <TICKER> <DATE>")
        print("Example: python camarilla_calculator.py AAPL 11-14-25")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    date_str = sys.argv[2]
    
    calc = CamarillaCalculator()
    results = calc.calculate_metrics(ticker, date_str)
    
    print("\n" + "=" * 60)
    print(f"CAMARILLA LEVELS - {ticker}")
    print("=" * 60)
    print(f"Date: {date_str}")
    print("\n" + "-" * 60)
    
    # Group by timeframe for display
    timeframes = {
        'DAILY (D1)': 'd1',
        'WEEKLY (W1)': 'w1',
        'MONTHLY (M1)': 'm1'
    }
    
    for tf_label, tf_prefix in timeframes.items():
        print(f"\n{tf_label}:")
        print("-" * 40)
        
        levels = ['s6', 's4', 's3', 'r3', 'r4', 'r6']
        for level in levels:
            field_name = f"{tf_prefix}_{level}"
            value = results.get(field_name)
            if value is not None:
                print(f"  {level.upper()}: ${value:.2f}")
            else:
                print(f"  {level.upper()}: N/A")
    
    print("\n" + "=" * 60)