"""
ON Metrics Calculator
Calculates overnight high (d1_onh) and overnight low (d1_onl) for a given ticker and date
Time range: 20:00 UTC prior day to 12:00 UTC current day using 5-minute bars
"""

from polygon import RESTClient
from datetime import datetime, timedelta
import pytz


class ONMetricsCalculator:
    def __init__(self, api_key="f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"):
        self.client = RESTClient(api_key)

    def parse_date(self, date_str):
        """Parse date from mm-dd-yy format"""
        try:
            return datetime.strptime(date_str, "%m-%d-%y")
        except ValueError:
            raise ValueError("Date must be in mm-dd-yy format (e.g., 09-09-25)")

    def get_time_range(self, target_date):
        """
        Calculate the time range for overnight data
        20:00 UTC prior day to 12:00 UTC current day
        """
        # Prior day at 20:00 UTC
        prior_day = target_date - timedelta(days=1)
        start_time = prior_day.replace(hour=20, minute=0, second=0, microsecond=0)
        start_time = pytz.UTC.localize(start_time)

        # Current day at 12:00 UTC
        end_time = target_date.replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = pytz.UTC.localize(end_time)

        return start_time, end_time

    def calculate_on_metrics(self, ticker, date_str):
        """
        Main calculation function
        Returns d1_onh (overnight high) and d1_onl (overnight low)
        """
        # Parse the input date
        target_date = self.parse_date(date_str)

        # Get time range
        start_time, end_time = self.get_time_range(target_date)

        # Convert to milliseconds for Polygon API
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        # Fetch 5-minute bar data
        bars = []
        try:
            for agg in self.client.list_aggs(
                    ticker=ticker.upper(),
                    multiplier=5,
                    timespan="minute",
                    from_=start_ms,
                    to=end_ms,
                    adjusted=True,
                    sort="asc",
                    limit=50000
            ):
                bars.append({
                    'timestamp': agg.timestamp,
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume,
                    'vwap': agg.vwap if hasattr(agg, 'vwap') else None,
                    'transactions': agg.transactions if hasattr(agg, 'transactions') else None
                })
        except Exception as e:
            raise Exception(f"Error fetching data: {str(e)}")

        if not bars:
            raise ValueError(f"No data found for {ticker} on {date_str}")

        # Calculate overnight high and low
        d1_onh = max(bar['high'] for bar in bars)  # Highest high
        d1_onl = min(bar['low'] for bar in bars)  # Lowest low

        return {
            "ticker": ticker.upper(),
            "date": date_str,
            "d1_onh": round(d1_onh, 2),
            "d1_onl": round(d1_onl, 2),
            "bar_count": len(bars),
            "time_range": f"{start_time.strftime('%Y-%m-%d %H:%M')} UTC to {end_time.strftime('%Y-%m-%d %H:%M')} UTC"
        }


def main():
    """Main function to run from terminal"""
    print("=== ON Metrics Calculator ===")
    print("Calculate overnight high/low for a ticker\n")

    # Get user input
    ticker = input("Enter ticker symbol (e.g., AVGO): ").strip()
    date_str = input("Enter date in mm-dd-yy format (e.g., 09-09-25): ").strip()

    # Initialize calculator
    calculator = ONMetricsCalculator()

    try:
        # Calculate metrics
        print(f"\nCalculating ON metrics for {ticker} on {date_str}...")
        results = calculator.calculate_on_metrics(ticker, date_str)

        # Display results
        print("\n" + "=" * 40)
        print("RESULTS:")
        print("=" * 40)
        print(f"Ticker: {results['ticker']}")
        print(f"Date: {results['date']}")
        print(f"Time Range: {results['time_range']}")
        print(f"Bars Processed: {results['bar_count']}")
        print("-" * 40)
        print(f"d1_onh (Overnight High): ${results['d1_onh']}")
        print(f"d1_onl (Overnight Low): ${results['d1_onl']}")
        print("=" * 40)

    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    main()