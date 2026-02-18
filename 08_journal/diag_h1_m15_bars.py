"""
Diagnostic: Check what H1 and M15 bars Polygon returns for extended hours.
Tests whether pre-market (04:00-09:30) and after-hours (16:00-20:00) bars
are present in the response for a known trade date.
"""
import requests
import pandas as pd
from datetime import date, timedelta

POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"

def fetch_and_analyze(ticker: str, trade_date: date, tf_minutes: int, lookback_days: int):
    label = f"{'H1' if tf_minutes == 60 else 'M15'}"
    start = trade_date - timedelta(days=lookback_days)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range"
        f"/{tf_minutes}/minute/{start:%Y-%m-%d}/{trade_date:%Y-%m-%d}"
    )
    params = {
        'apiKey': POLYGON_API_KEY,
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 50000,
    }

    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()

    print(f"\n{'=' * 70}")
    print(f"{label} bars for {ticker} | {start} -> {trade_date} | {tf_minutes}min")
    print(f"Status: {data.get('status')} | resultsCount: {data.get('resultsCount', 0)}")
    print(f"{'=' * 70}")

    if not data.get('results'):
        print("  No results returned!")
        return

    df = pd.DataFrame(data['results'])
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms', utc=True)
    df['timestamp_et'] = df['timestamp'].dt.tz_convert('America/New_York')
    df['hour'] = df['timestamp_et'].dt.hour
    df['date'] = df['timestamp_et'].dt.date

    total = len(df)
    print(f"  Total bars: {total}")

    # Show date range
    print(f"  First bar: {df['timestamp_et'].iloc[0]}")
    print(f"  Last bar:  {df['timestamp_et'].iloc[-1]}")

    # Categorize bars by session
    premarket = df[(df['hour'] >= 4) & (df['hour'] < 9)]
    regular_am = df[(df['hour'] >= 9) & (df['hour'] < 12)]
    regular_pm = df[(df['hour'] >= 12) & (df['hour'] < 16)]
    afterhours = df[(df['hour'] >= 16) & (df['hour'] < 20)]

    print(f"\n  Session breakdown:")
    print(f"    Pre-market  (04:00-09:00): {len(premarket)} bars")
    print(f"    Regular AM  (09:00-12:00): {len(regular_am)} bars")
    print(f"    Regular PM  (12:00-16:00): {len(regular_pm)} bars")
    print(f"    After-hours (16:00-20:00): {len(afterhours)} bars")

    # Show trade-date specific bars
    td_bars = df[df['date'] == trade_date]
    print(f"\n  Trade date ({trade_date}) bars: {len(td_bars)}")
    if not td_bars.empty:
        td_premarket = td_bars[(td_bars['hour'] >= 4) & (td_bars['hour'] < 9)]
        td_regular = td_bars[(td_bars['hour'] >= 9) & (td_bars['hour'] < 16)]
        td_afterhours = td_bars[(td_bars['hour'] >= 16) & (td_bars['hour'] < 20)]
        print(f"    Pre-market:  {len(td_premarket)} bars")
        print(f"    Regular:     {len(td_regular)} bars")
        print(f"    After-hours: {len(td_afterhours)} bars")

        # Print all trade-date bars with timestamps
        print(f"\n  All trade-date {label} bars:")
        for _, row in td_bars.iterrows():
            print(f"    {row['timestamp_et']}  O={row['o']:.2f} H={row['h']:.2f} L={row['l']:.2f} C={row['c']:.2f} V={row['v']:.0f}")

    # Show prior day bars (to check after-hours from prior day)
    prior_date = trade_date - timedelta(days=1)
    # Skip weekends
    while prior_date.weekday() >= 5:
        prior_date -= timedelta(days=1)
    pd_bars = df[df['date'] == prior_date]
    if not pd_bars.empty:
        pd_afterhours = pd_bars[(pd_bars['hour'] >= 16) & (pd_bars['hour'] < 20)]
        print(f"\n  Prior trading day ({prior_date}) after-hours bars: {len(pd_afterhours)}")
        if not pd_afterhours.empty:
            for _, row in pd_afterhours.iterrows():
                print(f"    {row['timestamp_et']}  O={row['o']:.2f} H={row['h']:.2f} L={row['l']:.2f} C={row['c']:.2f} V={row['v']:.0f}")
    else:
        print(f"\n  No bars for prior trading day ({prior_date})")


if __name__ == "__main__":
    # Use a known ticker/date from journal trades
    ticker = "TSLA"
    trade_date = date(2026, 2, 17)

    # Test H1 (60min) bars
    fetch_and_analyze(ticker, trade_date, tf_minutes=60, lookback_days=50)

    # Test M15 (15min) bars
    fetch_and_analyze(ticker, trade_date, tf_minutes=15, lookback_days=18)

    # Also test M5 for comparison (we know this works)
    fetch_and_analyze(ticker, trade_date, tf_minutes=5, lookback_days=3)

    print("\n" + "=" * 70)
    print("DONE - Check session breakdowns above for missing pre-market/after-hours bars")
    print("=" * 70)
