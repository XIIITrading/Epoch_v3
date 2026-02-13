"""
M1 Metrics Calculator
Calculates current and prior month OHLC metrics for a given ticker and date
Automatically uses prior closed month if current month is incomplete
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


class M1MetricsCalculator:
    def __init__(self):
        """Initialize the calculator with Polygon client"""
        self.client = client

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string in mm-dd-yy format"""
        try:
            return datetime.strptime(date_str, "%m-%d-%y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use mm-dd-yy format")

    def get_month_range(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get the first and last day of the month for a given date"""
        first_day = date.replace(day=1)
        last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
        return first_day, last_day

    def get_prior_month_range(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get the first and last day of the prior month"""
        first_day_current = date.replace(day=1)
        last_day_prior = first_day_current - timedelta(days=1)
        first_day_prior = last_day_prior.replace(day=1)
        return first_day_prior, last_day_prior

    def fetch_daily_data(self, ticker: str, start_date: datetime, end_date: datetime) -> List[Agg]:
        """Fetch daily aggregate data from Polygon"""
        try:
            # Get daily aggregates for the month
            aggs = list(self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=start_date.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d"),
                adjusted=True,
                sort="asc",
                limit=50  # Enough for any month
            ))

            return aggs

        except Exception as e:
            raise Exception(f"Error fetching data from Polygon: {e}")

    def calculate_monthly_metrics(self, daily_bars: List[Agg]) -> Dict[str, float]:
        """Calculate monthly OHLC from daily bars"""
        if not daily_bars:
            return {
                "open": None,
                "high": None,
                "low": None,
                "close": None
            }

        return {
            "open": daily_bars[0].open,  # First day's open
            "high": max(bar.high for bar in daily_bars),  # Highest high of the month
            "low": min(bar.low for bar in daily_bars),  # Lowest low of the month
            "close": daily_bars[-1].close  # Last day's close
        }

    def calculate_metrics(self, ticker: str, date_str: str) -> Dict:
        """
        Calculate M1 metrics for current and prior month.
        Automatically uses prior closed month if current month is incomplete.
        """
        # Parse the input date
        target_date = self.parse_date(date_str)

        # Get current month range
        curr_start, curr_end = self.get_month_range(target_date)
        
        # Fetch current month data
        current_daily_bars = self.fetch_daily_data(ticker, curr_start, curr_end)
        
        # Check if current month is incomplete (less than 5 trading days)
        # This ensures we have at least a full week of data
        use_prior_for_current = len(current_daily_bars) < 5
        
        if use_prior_for_current:
            # Use prior month as "current" since this month isn't complete enough
            prior_start, prior_end = self.get_prior_month_range(target_date)
            current_daily_bars = self.fetch_daily_data(ticker, prior_start, prior_end)
            curr_start, curr_end = prior_start, prior_end
            
            # Get the month before that for "prior"
            prior_prior_end = prior_start - timedelta(days=1)
            prior_prior_start = prior_prior_end.replace(day=1)
            prior_daily_bars = self.fetch_daily_data(ticker, prior_prior_start, prior_prior_end)
            prior_start, prior_end = prior_prior_start, prior_prior_end
        else:
            # Month has enough data, use normal prior month
            prior_start, prior_end = self.get_prior_month_range(target_date)
            prior_daily_bars = self.fetch_daily_data(ticker, prior_start, prior_end)

        # Calculate monthly metrics from daily bars
        current_month_metrics = self.calculate_monthly_metrics(current_daily_bars)
        prior_month_metrics = self.calculate_monthly_metrics(prior_daily_bars)

        metrics = {
            "ticker": ticker.upper(),
            "date": date_str,
            "current_month": {
                "period": f"{curr_start.strftime('%B %Y')}",
                "m1_01_open": current_month_metrics["open"],
                "m1_02_high": current_month_metrics["high"],
                "m1_03_low": current_month_metrics["low"],
                "m1_04_close": current_month_metrics["close"],
                "trading_days": len(current_daily_bars)
            },
            "prior_month": {
                "period": f"{prior_start.strftime('%B %Y')}",
                "m1_po_open": prior_month_metrics["open"],
                "m1_ph_high": prior_month_metrics["high"],
                "m1_pl_low": prior_month_metrics["low"],
                "m1_pc_close": prior_month_metrics["close"],
                "trading_days": len(prior_daily_bars)
            }
        }

        return metrics

    def display_metrics(self, metrics: Dict) -> None:
        """Display metrics in a formatted output"""
        print("\n" + "=" * 60)
        print(f"M1 METRICS for {metrics['ticker']} - Date: {metrics['date']}")
        print("=" * 60)

        print(
            f"\nCURRENT MONTH ({metrics['current_month']['period']}) - {metrics['current_month']['trading_days']} trading days:")
        print(f"  m1_01 (Open):  ${metrics['current_month']['m1_01_open']:.2f}" if metrics['current_month'][
            'm1_01_open'] else "  m1_01 (Open):  N/A")
        print(f"  m1_02 (High):  ${metrics['current_month']['m1_02_high']:.2f}" if metrics['current_month'][
            'm1_02_high'] else "  m1_02 (High):  N/A")
        print(f"  m1_03 (Low):   ${metrics['current_month']['m1_03_low']:.2f}" if metrics['current_month'][
            'm1_03_low'] else "  m1_03 (Low):   N/A")
        print(f"  m1_04 (Close): ${metrics['current_month']['m1_04_close']:.2f}" if metrics['current_month'][
            'm1_04_close'] else "  m1_04 (Close): N/A")

        print(
            f"\nPRIOR MONTH ({metrics['prior_month']['period']}) - {metrics['prior_month']['trading_days']} trading days:")
        print(f"  m1_po (Open):  ${metrics['prior_month']['m1_po_open']:.2f}" if metrics['prior_month'][
            'm1_po_open'] else "  m1_po (Open):  N/A")
        print(f"  m1_ph (High):  ${metrics['prior_month']['m1_ph_high']:.2f}" if metrics['prior_month'][
            'm1_ph_high'] else "  m1_ph (High):  N/A")
        print(f"  m1_pl (Low):   ${metrics['prior_month']['m1_pl_low']:.2f}" if metrics['prior_month'][
            'm1_pl_low'] else "  m1_pl (Low):   N/A")
        print(f"  m1_pc (Close): ${metrics['prior_month']['m1_pc_close']:.2f}" if metrics['prior_month'][
            'm1_pc_close'] else "  m1_pc (Close): N/A")
        print("=" * 60 + "\n")


def main():
    """Main execution function"""
    print("\n*** M1 Metrics Calculator ***")
    print("Calculate monthly OHLC metrics for any ticker\n")

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
        calculator = M1MetricsCalculator()
        metrics = calculator.calculate_metrics(ticker, date_str)

        # Display results
        calculator.display_metrics(metrics)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()