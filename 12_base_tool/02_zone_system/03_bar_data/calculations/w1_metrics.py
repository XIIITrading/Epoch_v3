"""
W1 Metrics Calculator
Calculates current and prior week OHLC metrics for a given ticker and date
Automatically uses prior closed week if current week is incomplete
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from polygon import RESTClient
from polygon.rest.models import Agg
import calendar

# Initialize client once at module level
client = RESTClient("f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_")


class W1MetricsCalculator:
    def __init__(self):
        """Initialize the calculator with Polygon client"""
        self.client = client

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string in mm-dd-yy format"""
        try:
            return datetime.strptime(date_str, "%m-%d-%y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use mm-dd-yy format")

    def get_week_range(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get the Monday and Sunday of the week for a given date"""
        # Get the Monday of the current week (weekday() returns 0 for Monday, 6 for Sunday)
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def get_prior_week_range(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get the Monday and Sunday of the prior week"""
        # Get Monday of current week
        days_since_monday = date.weekday()
        current_monday = date - timedelta(days=days_since_monday)

        # Prior week's Sunday is day before current Monday
        prior_sunday = current_monday - timedelta(days=1)
        prior_monday = prior_sunday - timedelta(days=6)

        return prior_monday, prior_sunday

    def fetch_daily_data(self, ticker: str, start_date: datetime, end_date: datetime) -> List[Agg]:
        """Fetch daily aggregate data from Polygon"""
        try:
            # Get daily aggregates for the week
            aggs = list(self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=start_date.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d"),
                adjusted=True,
                sort="asc",
                limit=10  # Enough for a week
            ))

            return aggs

        except Exception as e:
            raise Exception(f"Error fetching data from Polygon: {e}")

    def calculate_weekly_metrics(self, daily_bars: List[Agg]) -> Dict[str, float]:
        """Calculate weekly OHLC from daily bars"""
        if not daily_bars:
            return {
                "open": None,
                "high": None,
                "low": None,
                "close": None
            }

        return {
            "open": daily_bars[0].open,  # First day's open
            "high": max(bar.high for bar in daily_bars),  # Highest high of the week
            "low": min(bar.low for bar in daily_bars),  # Lowest low of the week
            "close": daily_bars[-1].close  # Last day's close
        }

    def format_week_period(self, start_date: datetime, end_date: datetime) -> str:
        """Format week period for display"""
        return f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d/%Y')}"

    def calculate_metrics(self, ticker: str, date_str: str) -> Dict:
        """
        Calculate W1 metrics for current and prior week.
        Automatically uses prior closed week if current week is incomplete.
        """
        # Parse the input date
        target_date = self.parse_date(date_str)

        # Get current week range
        curr_start, curr_end = self.get_week_range(target_date)
        
        # Fetch current week data
        current_daily_bars = self.fetch_daily_data(ticker, curr_start, curr_end)
        
        # Check if current week is incomplete (less than 4 trading days)
        # This handles Monday/Tuesday/Wednesday scenarios where we don't have a full week yet
        use_prior_for_current = len(current_daily_bars) < 4
        
        if use_prior_for_current:
            # Use prior week as "current" since this week isn't complete enough
            prior_start, prior_end = self.get_prior_week_range(target_date)
            current_daily_bars = self.fetch_daily_data(ticker, prior_start, prior_end)
            curr_start, curr_end = prior_start, prior_end
            
            # Get the week before that for "prior"
            prior_prior_start = prior_start - timedelta(days=7)
            prior_prior_end = prior_end - timedelta(days=7)
            prior_daily_bars = self.fetch_daily_data(ticker, prior_prior_start, prior_prior_end)
            prior_start, prior_end = prior_prior_start, prior_prior_end
        else:
            # Week has enough data, use normal prior week
            prior_start, prior_end = self.get_prior_week_range(target_date)
            prior_daily_bars = self.fetch_daily_data(ticker, prior_start, prior_end)

        # Calculate weekly metrics from daily bars
        current_week_metrics = self.calculate_weekly_metrics(current_daily_bars)
        prior_week_metrics = self.calculate_weekly_metrics(prior_daily_bars)

        metrics = {
            "ticker": ticker.upper(),
            "date": date_str,
            "current_week": {
                "period": self.format_week_period(curr_start, curr_end),
                "start_date": curr_start.strftime("%Y-%m-%d"),
                "end_date": curr_end.strftime("%Y-%m-%d"),
                "w1_01_open": current_week_metrics["open"],
                "w1_02_high": current_week_metrics["high"],
                "w1_03_low": current_week_metrics["low"],
                "w1_04_close": current_week_metrics["close"],
                "trading_days": len(current_daily_bars)
            },
            "prior_week": {
                "period": self.format_week_period(prior_start, prior_end),
                "start_date": prior_start.strftime("%Y-%m-%d"),
                "end_date": prior_end.strftime("%Y-%m-%d"),
                "w1_po_open": prior_week_metrics["open"],
                "w1_ph_high": prior_week_metrics["high"],
                "w1_pl_low": prior_week_metrics["low"],
                "w1_pc_close": prior_week_metrics["close"],
                "trading_days": len(prior_daily_bars)
            }
        }

        return metrics

    def display_metrics(self, metrics: Dict) -> None:
        """Display metrics in a formatted output"""
        print("\n" + "=" * 60)
        print(f"W1 METRICS for {metrics['ticker']} - Date: {metrics['date']}")
        print("=" * 60)

        print(
            f"\nCURRENT WEEK ({metrics['current_week']['period']}) - {metrics['current_week']['trading_days']} trading days:")
        print(f"  w1_01 (Open):  ${metrics['current_week']['w1_01_open']:.2f}" if metrics['current_week'][
            'w1_01_open'] else "  w1_01 (Open):  N/A")
        print(f"  w1_02 (High):  ${metrics['current_week']['w1_02_high']:.2f}" if metrics['current_week'][
            'w1_02_high'] else "  w1_02 (High):  N/A")
        print(f"  w1_03 (Low):   ${metrics['current_week']['w1_03_low']:.2f}" if metrics['current_week'][
            'w1_03_low'] else "  w1_03 (Low):   N/A")
        print(f"  w1_04 (Close): ${metrics['current_week']['w1_04_close']:.2f}" if metrics['current_week'][
            'w1_04_close'] else "  w1_04 (Close): N/A")

        print(
            f"\nPRIOR WEEK ({metrics['prior_week']['period']}) - {metrics['prior_week']['trading_days']} trading days:")
        print(f"  w1_po (Open):  ${metrics['prior_week']['w1_po_open']:.2f}" if metrics['prior_week'][
            'w1_po_open'] else "  w1_po (Open):  N/A")
        print(f"  w1_ph (High):  ${metrics['prior_week']['w1_ph_high']:.2f}" if metrics['prior_week'][
            'w1_ph_high'] else "  w1_ph (High):  N/A")
        print(f"  w1_pl (Low):   ${metrics['prior_week']['w1_pl_low']:.2f}" if metrics['prior_week'][
            'w1_pl_low'] else "  w1_pl (Low):   N/A")
        print(f"  w1_pc (Close): ${metrics['prior_week']['w1_pc_close']:.2f}" if metrics['prior_week'][
            'w1_pc_close'] else "  w1_pc (Close): N/A")
        print("=" * 60 + "\n")


def main():
    """Main execution function"""
    print("\n*** W1 Metrics Calculator ***")
    print("Calculate weekly OHLC metrics for any ticker\n")

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
        calculator = W1MetricsCalculator()
        metrics = calculator.calculate_metrics(ticker, date_str)

        # Display results
        calculator.display_metrics(metrics)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()