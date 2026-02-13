"""
Test script for the data layer components.
Run from: C:/XIIITradingSystems/Epoch/05_analysis_tool
Command: python test_data_layer.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all imports work correctly."""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)

    from data import (
        PolygonClient, get_polygon_client,
        CacheManager, cache, get_cache_key,
        TickerManager, ticker_manager, parse_tickers
    )
    print("  [OK] All data module imports successful")

    from config import settings, weights
    print("  [OK] Config imports successful")
    print(f"       POLYGON_API_KEY set: {bool(settings.POLYGON_API_KEY)}")

    from core import TickerInput, BarData, Direction, Rank
    print("  [OK] Core model imports successful")

    print()
    return True


def test_cache_manager():
    """Test cache manager functionality."""
    print("=" * 60)
    print("Testing cache manager...")
    print("=" * 60)

    from data import cache
    import pandas as pd

    # Test DataFrame caching
    test_key = "test_df_cache"
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    cache.set_dataframe(test_key, df)
    loaded = cache.get_dataframe(test_key)

    assert loaded is not None, "DataFrame cache retrieval failed"
    assert len(loaded) == 3, "Wrong DataFrame length"
    print("  [OK] DataFrame caching works")

    # Test object caching
    test_key = "test_obj_cache"
    obj = {"key": "value", "num": 42, "list": [1, 2, 3]}
    cache.set_object(test_key, obj)
    loaded = cache.get_object(test_key)

    assert loaded == obj, "Object cache retrieval failed"
    print("  [OK] Object caching works")

    # Test JSON caching
    test_key = "test_json_cache"
    data = {"ticker": "SPY", "price": 595.25}
    cache.set_json(test_key, data)
    loaded = cache.get_json(test_key)

    assert loaded == data, "JSON cache retrieval failed"
    print("  [OK] JSON caching works")

    # Test cache key generation
    from data import get_cache_key
    key1 = get_cache_key("SPY", "2024-01-01", "daily")
    key2 = get_cache_key("SPY", "2024-01-01", "daily")
    key3 = get_cache_key("AAPL", "2024-01-01", "daily")

    assert key1 == key2, "Same inputs should produce same key"
    assert key1 != key3, "Different inputs should produce different keys"
    print("  [OK] Cache key generation works")

    # Get cache stats
    stats = cache.get_cache_stats()
    print(f"  [OK] Cache stats: {stats['file_count']} files, {stats['total_size_mb']} MB")

    print()
    return True


def test_ticker_manager():
    """Test ticker manager functionality."""
    print("=" * 60)
    print("Testing ticker manager...")
    print("=" * 60)

    from data import ticker_manager, parse_tickers

    # Test ticker list access
    sp500 = ticker_manager.get_sp500()
    nasdaq100 = ticker_manager.get_nasdaq100()
    print(f"  [OK] S&P 500 tickers: {len(sp500)} symbols")
    print(f"  [OK] NASDAQ 100 tickers: {len(nasdaq100)} symbols")

    # Test parsing
    tickers = parse_tickers("AAPL, MSFT, GOOGL")
    assert tickers == ["AAPL", "MSFT", "GOOGL"], "Comma parsing failed"
    print("  [OK] Comma-separated parsing works")

    tickers = parse_tickers("AAPL MSFT GOOGL")
    assert tickers == ["AAPL", "MSFT", "GOOGL"], "Space parsing failed"
    print("  [OK] Space-separated parsing works")

    tickers = parse_tickers("AAPL\nMSFT\nGOOGL")
    assert tickers == ["AAPL", "MSFT", "GOOGL"], "Newline parsing failed"
    print("  [OK] Newline-separated parsing works")

    # Test validation
    valid = ticker_manager.validate_tickers(["AAPL", "invalid!!!", "MSFT", ""])
    assert valid == ["AAPL", "MSFT"], "Validation failed"
    print("  [OK] Ticker validation works")

    # Test index detection
    assert ticker_manager.is_index_ticker("SPY") == True
    assert ticker_manager.is_index_ticker("AAPL") == False
    print("  [OK] Index ticker detection works")

    print()
    return True


def test_polygon_client():
    """Test Polygon API client functionality."""
    print("=" * 60)
    print("Testing Polygon client...")
    print("=" * 60)

    from data import PolygonClient

    client = PolygonClient()
    print("  [OK] Client initialized")

    # Test daily bars
    start = date.today() - timedelta(days=30)
    df = client.fetch_daily_bars("SPY", start)
    assert not df.empty, "No daily data returned"
    print(f"  [OK] Daily bars: {len(df)} rows")
    print(f"       Latest close: ${df.iloc[-1]['close']:.2f}")

    # Test minute bars (smaller range to be faster)
    start = date.today() - timedelta(days=3)
    df = client.fetch_minute_bars("SPY", start, multiplier=5)
    assert not df.empty, "No 5-minute data returned"
    print(f"  [OK] 5-minute bars: {len(df)} rows")

    # Test previous close
    prev_close = client.get_previous_close("SPY")
    assert prev_close is not None, "No previous close returned"
    print(f"  [OK] Previous close: ${prev_close:.2f}")

    # Test weekly bars
    start = date.today() - timedelta(days=90)
    df = client.fetch_weekly_bars("SPY", start)
    assert not df.empty, "No weekly data returned"
    print(f"  [OK] Weekly bars: {len(df)} rows")

    # Test monthly bars
    start = date.today() - timedelta(days=365)
    df = client.fetch_monthly_bars("SPY", start)
    assert not df.empty, "No monthly data returned"
    print(f"  [OK] Monthly bars: {len(df)} rows")

    print()
    return True


def test_polygon_with_caching():
    """Test Polygon client with caching."""
    print("=" * 60)
    print("Testing Polygon + Cache integration...")
    print("=" * 60)

    from data import PolygonClient, cache, get_cache_key
    from datetime import date, timedelta
    import time

    client = PolygonClient()
    ticker = "SPY"
    start = date.today() - timedelta(days=30)
    end = date.today()

    # Generate cache key
    cache_key = get_cache_key(ticker, str(start), str(end), "daily")

    # First fetch (should hit API)
    start_time = time.time()
    df1 = client.fetch_daily_bars(ticker, start, end)
    api_time = time.time() - start_time

    # Cache the result
    cache.set_dataframe(cache_key, df1)
    print(f"  [OK] API fetch took {api_time:.2f}s, cached {len(df1)} rows")

    # Second fetch (should hit cache)
    start_time = time.time()
    df2 = cache.get_dataframe(cache_key)
    cache_time = time.time() - start_time

    assert df2 is not None, "Cache miss on second fetch"
    assert len(df1) == len(df2), "Cache data mismatch"
    print(f"  [OK] Cache fetch took {cache_time:.4f}s (vs {api_time:.2f}s from API)")
    print(f"       Speedup: {api_time/cache_time:.0f}x faster")

    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EPOCH ANALYSIS TOOL - DATA LAYER TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests in order
    results.append(("Imports", test_imports()))
    results.append(("Cache Manager", test_cache_manager()))
    results.append(("Ticker Manager", test_ticker_manager()))
    results.append(("Polygon Client", test_polygon_client()))
    results.append(("Polygon + Cache", test_polygon_with_caching()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
