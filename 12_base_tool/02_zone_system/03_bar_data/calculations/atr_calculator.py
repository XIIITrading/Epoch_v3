from polygon import RESTClient
from datetime import datetime, timedelta, timezone

# Initialize client once at module level
client = RESTClient("f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_")


def calculate_daily_atr(ticker, date_str):
    """Calculate D1 ATR: 24 daily bars from prior trading day"""
    # Parse the input date
    year, month, day = map(int, date_str.split('-'))
    reference_date = datetime(year, month, day)

    # Calculate prior trading day
    prior_day = reference_date - timedelta(days=1)

    # Adjust for weekends
    if prior_day.weekday() == 6:  # Sunday -> Friday
        prior_day -= timedelta(days=2)
    elif prior_day.weekday() == 5:  # Saturday -> Friday
        prior_day -= timedelta(days=1)

    # Fetch 24 daily bars
    bars = []
    start_date = (prior_day - timedelta(days=40)).strftime("%Y-%m-%d")
    end_date = prior_day.strftime("%Y-%m-%d")

    for bar in client.list_aggs(
            ticker, 1, "day",
            start_date, end_date,
            adjusted=True, sort="desc", limit=24
    ):
        bars.append(bar)

    if not bars:
        return 0

    # Calculate average range
    ranges = [bar.high - bar.low for bar in bars]
    return sum(ranges) / len(ranges)


def calculate_h1_atr(ticker, date_str, utc_hour=11):
    """Calculate H1 ATR for 24 bars before specified UTC time"""
    # Parse date and create UTC anchor
    year, month, day = map(int, date_str.split('-'))
    anchor = datetime(year, month, day, utc_hour, 0, 0, tzinfo=timezone.utc)
    anchor_ms = int(anchor.timestamp() * 1000)

    # Fetch bars
    bars = []
    start = (anchor - timedelta(days=4)).strftime("%Y-%m-%d")

    for bar in client.list_aggs(
            ticker, 1, "hour", start, date_str,
            adjusted=True, sort="desc", limit=100
    ):
        if bar.timestamp <= anchor_ms:
            bars.append(bar)
            if len(bars) == 24:
                break

    # Calculate ATR
    ranges = [bar.high - bar.low for bar in bars]
    return sum(ranges) / len(ranges) if ranges else 0


def calculate_m15_atr(ticker, date_str):
    """Calculate M15 ATR for prior trading day's market hours"""
    # Parse date and get prior trading day
    year, month, day = map(int, date_str.split('-'))
    reference_date = datetime(year, month, day)
    
    # Try up to 5 days back to find a valid trading day with data
    for days_back in range(1, 6):
        prior_day = reference_date - timedelta(days=days_back)

        # Skip weekends
        if prior_day.weekday() >= 5:  # Saturday or Sunday
            continue

        prior_day_str = prior_day.strftime("%Y-%m-%d")

        # Get 15-minute bars
        bars = []
        for bar in client.list_aggs(
                ticker, 15, "minute",
                prior_day_str, prior_day_str,
                adjusted=True, sort="asc", limit=50000
        ):
            bars.append(bar)

        # Calculate average range for market hours only
        # Market hours: 13:30 to 20:00 UTC (9:30 AM to 4:00 PM EDT)
        ranges = []
        for bar in bars:
            # Convert to UTC datetime
            bar_time_utc = datetime.fromtimestamp(bar.timestamp / 1000, tz=timezone.utc)
            hour = bar_time_utc.hour
            minute = bar_time_utc.minute

            # Filter for 13:30 to 20:00 UTC
            time_in_minutes = hour * 60 + minute
            market_open = 13 * 60 + 30  # 13:30 UTC
            market_close = 20 * 60  # 20:00 UTC

            if market_open <= time_in_minutes <= market_close:
                ranges.append(bar.high - bar.low)

        # If we found valid market hours data, return the ATR
        if ranges:
            return sum(ranges) / len(ranges)
    
    # No valid data found after trying 5 days
    return 0


def calculate_m5_atr(ticker, date_str):
    """Calculate M5 ATR for prior trading day's market hours"""
    # Parse date and get prior trading day
    year, month, day = map(int, date_str.split('-'))
    reference_date = datetime(year, month, day)
    
    # Try up to 5 days back to find a valid trading day with data
    for days_back in range(1, 6):
        prior_day = reference_date - timedelta(days=days_back)

        # Skip weekends
        if prior_day.weekday() >= 5:  # Saturday or Sunday
            continue

        prior_day_str = prior_day.strftime("%Y-%m-%d")

        # Get 5-minute bars
        bars = []
        for bar in client.list_aggs(
                ticker, 5, "minute",
                prior_day_str, prior_day_str,
                adjusted=True, sort="asc", limit=50000
        ):
            bars.append(bar)

        # Calculate average range for market hours only
        # Market hours: 13:30 to 20:00 UTC (9:30 AM to 4:00 PM EDT)
        ranges = []
        for bar in bars:
            # Convert to UTC datetime
            bar_time_utc = datetime.fromtimestamp(bar.timestamp / 1000, tz=timezone.utc)
            hour = bar_time_utc.hour
            minute = bar_time_utc.minute

            # Filter for 13:30 to 20:00 UTC
            time_in_minutes = hour * 60 + minute
            market_open = 13 * 60 + 30  # 13:30 UTC
            market_close = 20 * 60  # 20:00 UTC

            if market_open <= time_in_minutes <= market_close:
                ranges.append(bar.high - bar.low)

        # If we found valid market hours data, return the ATR
        if ranges:
            return sum(ranges) / len(ranges)
    
    # No valid data found after trying 5 days
    return 0


def main():
    """Main function to handle user input and coordinate calculations"""
    print("\n" + "=" * 50)
    print("Multi-Timeframe ATR Calculator")
    print("=" * 50)

    # Get user input
    ticker = input("Enter ticker symbol: ").upper().strip()
    date_str = input("Enter date (YYYY-MM-DD): ").strip()

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD")
        return

    print(f"\nCalculating ATR values for {ticker} as of {date_str}...")
    print("-" * 50)

    try:
        # Calculate all ATR values
        m5_atr = calculate_m5_atr(ticker, date_str)
        m15_atr = calculate_m15_atr(ticker, date_str)
        h1_atr = calculate_h1_atr(ticker, date_str)
        d1_atr = calculate_daily_atr(ticker, date_str)

        # Display results
        print(f"m5_atr:  ${m5_atr:.4f}")
        print(f"m15_atr: ${m15_atr:.4f}")
        print(f"h1_atr:  ${h1_atr:.4f}")
        print(f"d1_atr:  ${d1_atr:.4f}")
        print("-" * 50)

    except Exception as e:
        print(f"Error calculating ATR: {e}")


if __name__ == "__main__":
    main()