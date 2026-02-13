"""
Module 10: Polygon Data Fetcher
Fetches M5 bars, daily data, and market context from Polygon.io API.
"""
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from config import POLYGON_API_KEY, POLYGON_BASE_URL


class PolygonFetcher:
    """Fetches market data from Polygon.io API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling."""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["apiKey"] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Polygon API error: {e}")
            return None
    
    def get_m5_bars(self, ticker: str, target_date: str) -> List[Dict]:
        """
        Get 5-minute bars for a ticker on a specific date.
        
        Args:
            ticker: Stock symbol
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            List of bar dictionaries with OHLCV data
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/5/minute/{target_date}/{target_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
        }
        
        data = self._make_request(endpoint, params)
        if not data or "results" not in data:
            return []
        
        bars = []
        for bar in data["results"]:
            bars.append({
                "timestamp": bar.get("t"),
                "open": bar.get("o"),
                "high": bar.get("h"),
                "low": bar.get("l"),
                "close": bar.get("c"),
                "volume": bar.get("v"),
                "vwap": bar.get("vw"),
                "transactions": bar.get("n"),
            })
        
        return bars
    
    def get_daily_bars(self, ticker: str, target_date: str) -> Optional[Dict]:
        """
        Get daily OHLCV data for a ticker.
        
        Args:
            ticker: Stock symbol
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with OHLCV data or None
        """
        endpoint = f"/v1/open-close/{ticker}/{target_date}"
        params = {"adjusted": "true"}
        
        data = self._make_request(endpoint, params)
        if not data or data.get("status") != "OK":
            # Try aggs endpoint as fallback
            return self._get_daily_from_aggs(ticker, target_date)
        
        return {
            "open": data.get("open"),
            "high": data.get("high"),
            "low": data.get("low"),
            "close": data.get("close"),
            "volume": data.get("volume"),
            "premarket": data.get("preMarket"),
            "afterhours": data.get("afterHours"),
        }
    
    def _get_daily_from_aggs(self, ticker: str, target_date: str) -> Optional[Dict]:
        """Fallback to aggs endpoint for daily data."""
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/day/{target_date}/{target_date}"
        params = {"adjusted": "true"}
        
        data = self._make_request(endpoint, params)
        if not data or "results" not in data or not data["results"]:
            return None
        
        bar = data["results"][0]
        return {
            "open": bar.get("o"),
            "high": bar.get("h"),
            "low": bar.get("l"),
            "close": bar.get("c"),
            "volume": bar.get("v"),
            "vwap": bar.get("vw"),
        }
    
    def get_vix_level(self, target_date: str) -> Optional[Dict]:
        """
        Get VIX closing level for a date.
        
        Note: VIX requires special handling - uses I: prefix for indices
        """
        # Try the index ticker
        endpoint = f"/v2/aggs/ticker/I:VIX/range/1/day/{target_date}/{target_date}"
        params = {"adjusted": "true"}
        
        data = self._make_request(endpoint, params)
        if data and "results" in data and data["results"]:
            bar = data["results"][0]
            return {
                "open": bar.get("o"),
                "high": bar.get("h"),
                "low": bar.get("l"),
                "close": bar.get("c"),
            }
        
        # Fallback: try VIX ETF (VIXY) as proxy
        return self.get_daily_bars("VIXY", target_date)
    
    def get_previous_close(self, ticker: str) -> Optional[float]:
        """Get previous trading day's close price."""
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        params = {"adjusted": "true"}
        
        data = self._make_request(endpoint, params)
        if data and "results" in data and data["results"]:
            return data["results"][0].get("c")
        return None
    
    def get_opening_range(self, ticker: str, target_date: str, minutes: int = 30) -> Optional[Dict]:
        """
        Calculate opening range high/low from M5 bars.
        
        Args:
            ticker: Stock symbol
            target_date: Date in YYYY-MM-DD format
            minutes: Number of minutes for opening range (default 30)
            
        Returns:
            Dictionary with opening range data
        """
        bars = self.get_m5_bars(ticker, target_date)
        if not bars:
            return None
        
        # Get bars within opening range (first N minutes)
        num_bars = minutes // 5
        opening_bars = bars[:num_bars]
        
        if not opening_bars:
            return None
        
        return {
            "high": max(b["high"] for b in opening_bars),
            "low": min(b["low"] for b in opening_bars),
            "open": opening_bars[0]["open"],
            "close": opening_bars[-1]["close"],
            "volume": sum(b["volume"] for b in opening_bars),
            "bars_count": len(opening_bars),
        }


def main():
    """Test the Polygon fetcher."""
    from datetime import date
    
    print("Testing Polygon Fetcher...")
    print(f"API Key configured: {bool(POLYGON_API_KEY and POLYGON_API_KEY != 'your_polygon_api_key_here')}")
    
    fetcher = PolygonFetcher()
    today = date.today().strftime("%Y-%m-%d")
    
    # Test SPY daily
    print(f"\nSPY Daily ({today}):")
    spy = fetcher.get_daily_bars("SPY", today)
    if spy:
        print(f"  O: {spy['open']}, H: {spy['high']}, L: {spy['low']}, C: {spy['close']}")
    else:
        print("  No data (market may be closed)")
    
    # Test VIX
    print(f"\nVIX Level:")
    vix = fetcher.get_vix_level(today)
    if vix:
        print(f"  Close: {vix['close']}")
    else:
        print("  No data")
    
    # Test M5 bars
    print(f"\nAAPL M5 bars:")
    bars = fetcher.get_m5_bars("AAPL", today)
    print(f"  Bars fetched: {len(bars)}")
    if bars:
        print(f"  First bar: {bars[0]}")


if __name__ == "__main__":
    main()