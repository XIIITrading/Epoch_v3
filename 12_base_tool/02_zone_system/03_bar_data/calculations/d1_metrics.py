"""
D1 Metrics Calculator
Calculates current and prior day OHLC metrics for a given ticker and date
"""

import os
import sys
from datetime import datetime, timedelta, time
from typing import Dict, Optional, Tuple, List
from polygon import RESTClient
from polygon.rest.models import Agg
import calendar

# Initialize client once at module level
client = RESTClient("f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_")


class D1MetricsCalculator:
    def __init__(self):
        """Initialize the calculator with Polygon client"""
        self.client = client

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string in mm-dd-yy format"""
        try:
            return datetime.strptime(date_str, "%m-%d-%y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use mm-dd-yy format")

    def get_prior_trading_day(self, date: datetime, ticker: str) -> Optional[datetime]:
        """Find the previous trading day before the given date"""
        # Check up to 10 days back to find a trading day
        for i in range(1, 10):
            check_date = date - timedelta(days=i)

            # Try to fetch data for this date to see if it was a trading day
            try:
                aggs = list(self.client.get_aggs(
                    ticker=ticker,
                    multiplier=1,
                    timespan="day",
                    from_=check_date.strftime("%Y-%m-%d"),
                    to=check_date.strftime("%Y-%m-%d"),
                    adjusted=True,
                    limit=1
                ))

                if aggs:
                    return check_date
            except:
                continue

        return None

    def fetch_intraday_data(self, ticker: str, date: datetime) -> List[Agg]:
        """Fetch minute aggregate data from Polygon for a specific day"""
        try:
            # Use date format only (YYYY-MM-DD) for the API
            date_str = date.strftime("%Y-%m-%d")

            # Get minute aggregates for the day
            aggs = list(self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="minute",
                from_=date_str,
                to=date_str,
                adjusted=True,
                sort="asc",
                limit=1000  # Enough for all minute bars in a day
            ))

            return aggs

        except Exception as e:
            raise Exception(f"Error fetching data from Polygon: {e}")

    def calculate_daily_metrics(self, minute_bars: List[Agg]) -> Dict[str, float]:
        """Calculate daily OHLC from minute bars"""
        if not minute_bars:
            return {
                "open": None,
                "high": None,
                "low": None,
                "close": None
            }

        return {
            "open": minute_bars[0].open,  # First minute's open
            "high": max(bar.high for bar in minute_bars),  # Highest high of the day
            "low": min(bar.low for bar in minute_bars),  # Lowest low of the day
            "close": minute_bars[-1].close  # Last minute's close
        }

    def format_day_period(self, date: datetime) -> str:
        """Format day period for display"""
        return date.strftime("%m/%d/%Y (%A)")

    def calculate_metrics(self, ticker: str, date_str: str) -> Dict:
        """Calculate D1 metrics for current and prior day"""
        # Parse the input date
        target_date = self.parse_date(date_str)

        # Get prior trading day
        prior_date = self.get_prior_trading_day(target_date, ticker)

        # Fetch minute data for both days
        current_minute_bars = self.fetch_intraday_data(ticker, target_date)
        prior_minute_bars = self.fetch_intraday_data(ticker, prior_date) if prior_date else []

        # Calculate daily metrics from minute bars
        current_day_metrics = self.calculate_daily_metrics(current_minute_bars)
        prior_day_metrics = self.calculate_daily_metrics(prior_minute_bars) if prior_date else {
            "open": None, "high": None, "low": None, "close": None
        }

        metrics = {
            "ticker": ticker.upper(),
            "date": date_str,
            "current_day": {
                "period": self.format_day_period(target_date),
                "date": target_date.strftime("%Y-%m-%d"),
                "d1_01_open": current_day_metrics["open"],
                "d1_02_high": current_day_metrics["high"],
                "d1_03_low": current_day_metrics["low"],
                "d1_04_close": current_day_metrics["close"],
                "minute_bars": len(current_minute_bars)
            },
            "prior_day": {
                "period": self.format_day_period(prior_date) if prior_date else "N/A",
                "date": prior_date.strftime("%Y-%m-%d") if prior_date else None,
                "d1_po_open": prior_day_metrics["open"],
                "d1_ph_high": prior_day_metrics["high"],
                "d1_pl_low": prior_day_metrics["low"],
                "d1_pc_close": prior_day_metrics["close"],
                "minute_bars": len(prior_minute_bars)
            }
        }

        return metrics

    def display_metrics(self, metrics: Dict) -> None:
        """Display metrics in a formatted output"""
        print("\n" + "=" * 60)
        print(f"D1 METRICS for {metrics['ticker']} - Date: {metrics['date']}")
        print("=" * 60)

        print(
            f"\nCURRENT DAY ({metrics['current_day']['period']}) - {metrics['current_day']['minute_bars']} minute bars:")
        print(f"  d1_01 (Open):  ${metrics['current_day']['d1_01_open']:.2f}" if metrics['current_day'][
            'd1_01_open'] else "  d1_01 (Open):  N/A")
        print(f"  d1_02 (High):  ${metrics['current_day']['d1_02_high']:.2f}" if metrics['current_day'][
            'd1_02_high'] else "  d1_02 (High):  N/A")
        print(f"  d1_03 (Low):   ${metrics['current_day']['d1_03_low']:.2f}" if metrics['current_day'][
            'd1_03_low'] else "  d1_03 (Low):   N/A")
        print(f"  d1_04 (Close): ${metrics['current_day']['d1_04_close']:.2f}" if metrics['current_day'][
            'd1_04_close'] else "  d1_04 (Close): N/A")

        print(
            f"\nPRIOR DAY ({metrics['prior_day']['period']}) - {metrics['prior_day']['minute_bars']} minute bars:")
        print(f"  d1_po (Open):  ${metrics['prior_day']['d1_po_open']:.2f}" if metrics['prior_day'][
            'd1_po_open'] else "  d1_po (Open):  N/A")
        print(f"  d1_ph (High):  ${metrics['prior_day']['d1_ph_high']:.2f}" if metrics['prior_day'][
            'd1_ph_high'] else "  d1_ph (High):  N/A")
        print(f"  d1_pl (Low):   ${metrics['prior_day']['d1_pl_low']:.2f}" if metrics['prior_day'][
            'd1_pl_low'] else "  d1_pl (Low):   N/A")
        print(f"  d1_pc (Close): ${metrics['prior_day']['d1_pc_close']:.2f}" if metrics['prior_day'][
            'd1_pc_close'] else "  d1_pc (Close): N/A")
        print("=" * 60 + "\n")


def main():
    """Main execution function"""
    print("\n*** D1 Metrics Calculator ***")
    print("Calculate daily OHLC metrics for any ticker\n")

    try:
        # Get user input
        ticker = input("Enter ticker symbol (e.g., AVGO): ").strip().upper()
        date_str = input("Enter date (mm-dd-yy format, e.g., 09-09-25): ").strip()

        # Validate inputs
        if not ticker:
            raise ValueError("Ticker symbol cannot be empty")
        if not date_str:
            raise ValueError("Date cannot be empty")

        # Initialize calculator and get metrics
        calculator = D1MetricsCalculator()
        metrics = calculator.calculate_metrics(ticker, date_str)

        # Display results
        calculator.display_metrics(metrics)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()