# polygon_fetcher.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\data_readers\
# Purpose: Fetch M15 bar data and calculate volume profile for charts

"""
Polygon Data Fetcher for Module 08 Visualization

Features:
- Fetches last N M15 bars for chart display
- Calculates volume profile at $0.01 granularity
- Identifies top 10 HVN zones for highlighting
- Returns data ready for matplotlib charting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from math import floor, ceil
import logging
import time
import requests
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.visualization_config import (
    POLYGON_API_KEY, API_DELAY, API_RETRIES, API_RETRY_DELAY,
    DEFAULT_BAR_COUNT, DEFAULT_BAR_TIMEFRAME, DISPLAY_TIMEZONE
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class HVNZone:
    """A High Volume Node zone"""
    poc_price: float  # Point of Control (highest volume price)
    zone_high: float  # POC + ATR/2
    zone_low: float   # POC - ATR/2
    volume: float     # Volume at POC
    rank: int         # 1 = highest volume


@dataclass
class ChartData:
    """Container for chart-ready data"""
    ticker: str
    bars: pd.DataFrame  # OHLCV with datetime index
    volume_profile: Dict[float, float]  # price -> volume
    hvn_zones: List[HVNZone]  # Top 10 HVN zones for highlighting
    fetch_time: datetime
    bar_count: int
    m5_atr: float = 0.0  # M5 ATR for zone width calculation
    
    @property
    def price_range(self) -> Tuple[float, float]:
        """Get price range from bars"""
        if self.bars.empty:
            return (0, 0)
        return (self.bars['low'].min(), self.bars['high'].max())
    
    @property
    def current_price(self) -> float:
        """Get current price (last close)"""
        if self.bars.empty:
            return 0
        return self.bars['close'].iloc[-1]
    
    def is_in_hvn_zone(self, price: float) -> bool:
        """Check if a price is within any HVN zone"""
        for zone in self.hvn_zones:
            if zone.zone_low <= price <= zone.zone_high:
                return True
        return False


# =============================================================================
# POLYGON FETCHER
# =============================================================================

class PolygonBarFetcher:
    """Fetch bar data from Polygon API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize fetcher with API key.
        
        Args:
            api_key: Polygon API key. Uses config default if not provided.
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"
        
        if not self.api_key:
            logger.warning("No Polygon API key configured")
    
    def fetch_last_n_bars(self, ticker: str, n_bars: int = DEFAULT_BAR_COUNT,
                          timeframe_minutes: int = DEFAULT_BAR_TIMEFRAME,
                          m5_atr: float = None) -> ChartData:
        """
        Fetch the last N bars for a ticker.
        
        Args:
            ticker: Stock symbol (e.g., "TSLA")
            n_bars: Number of bars to fetch (default 120)
            timeframe_minutes: Bar timeframe in minutes (default 15)
            m5_atr: M5 ATR for HVN zone width (if None, estimates from data)
            
        Returns:
            ChartData with bars, volume profile, and HVN zones
        """
        ticker = ticker.upper().strip()
        fetch_time = datetime.now()
        
        # Calculate date range (fetch extra days to ensure we get enough bars)
        end_date = fetch_time.strftime('%Y-%m-%d')
        # For 120 M15 bars, need ~5 days of data
        days_needed = max(7, (n_bars * timeframe_minutes) // (6.5 * 60) + 2)
        start_date = (fetch_time - timedelta(days=days_needed)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching last {n_bars} M{timeframe_minutes} bars for {ticker}")
        
        try:
            bars = self._fetch_bars(ticker, start_date, end_date, timeframe_minutes)
            
            if bars.empty:
                logger.warning(f"No data returned for {ticker}")
                return ChartData(
                    ticker=ticker,
                    bars=pd.DataFrame(),
                    volume_profile={},
                    hvn_zones=[],
                    fetch_time=fetch_time,
                    bar_count=0
                )
            
            # Take last N bars
            bars = bars.tail(n_bars).copy()
            
            # Build volume profile from the fetched bars
            volume_profile = self._build_volume_profile(bars)
            
            # Estimate M5 ATR if not provided
            if m5_atr is None or m5_atr <= 0:
                # Rough estimate: M5 ATR ≈ D1 ATR / 20
                avg_range = (bars['high'] - bars['low']).mean()
                m5_atr = avg_range / 3  # Approximate M5 ATR from M15 range
                logger.warning(f"M5 ATR not provided or zero, estimated from bars: ${m5_atr:.2f} (avg_range=${avg_range:.2f})")
            else:
                logger.info(f"Using provided M5 ATR: ${m5_atr:.2f}")
            
            # Identify top 10 HVN zones
            hvn_zones = self._identify_hvn_zones(volume_profile, m5_atr)
            
            logger.info(f"Fetched {len(bars)} bars, {len(volume_profile)} volume levels, {len(hvn_zones)} HVN zones")
            
            return ChartData(
                ticker=ticker,
                bars=bars,
                volume_profile=volume_profile,
                hvn_zones=hvn_zones,
                fetch_time=fetch_time,
                bar_count=len(bars),
                m5_atr=m5_atr
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return ChartData(
                ticker=ticker,
                bars=pd.DataFrame(),
                volume_profile={},
                hvn_zones=[],
                fetch_time=fetch_time,
                bar_count=0
            )
    
    def _fetch_bars(self, ticker: str, start_date: str, end_date: str,
                    timeframe_minutes: int) -> pd.DataFrame:
        """
        Fetch bars from Polygon API.
        
        Args:
            ticker: Stock symbol
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            timeframe_minutes: Bar size in minutes
            
        Returns:
            DataFrame with OHLCV data
        """
        endpoint = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{timeframe_minutes}/minute/{start_date}/{end_date}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        for attempt in range(API_RETRIES):
            try:
                response = requests.get(endpoint, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') != 'OK':
                    logger.warning(f"API status: {data.get('status')}")
                    return pd.DataFrame()
                
                results = data.get('results', [])
                
                if not results:
                    logger.warning(f"No results for {ticker}")
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Rename columns
                column_mapping = {
                    't': 'timestamp',
                    'o': 'open',
                    'h': 'high',
                    'l': 'low',
                    'c': 'close',
                    'v': 'volume'
                }
                df = df.rename(columns=column_mapping)
                
                # Convert timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                df['timestamp'] = df['timestamp'].dt.tz_convert(DISPLAY_TIMEZONE)
                df.set_index('timestamp', inplace=True)
                
                # Keep only OHLCV
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                return df
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < API_RETRIES - 1:
                    time.sleep(API_RETRY_DELAY)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        return pd.DataFrame()
    
    def _build_volume_profile(self, bars: pd.DataFrame, 
                               granularity: float = 0.01) -> Dict[float, float]:
        """
        Build volume profile at specified price granularity.
        
        Distributes each bar's volume proportionally across all price levels
        touched by that bar.
        
        Args:
            bars: OHLCV DataFrame
            granularity: Price level granularity (default $0.01)
            
        Returns:
            Dict mapping price level to accumulated volume
        """
        volume_profile = {}
        
        for _, bar in bars.iterrows():
            bar_low = bar['low']
            bar_high = bar['high']
            bar_volume = bar['volume']
            
            # Skip invalid bars
            if bar_volume <= 0 or bar_high <= bar_low:
                continue
            if pd.isna(bar_low) or pd.isna(bar_high) or pd.isna(bar_volume):
                continue
            
            # Round to granularity boundaries
            low_level = floor(bar_low / granularity) * granularity
            high_level = ceil(bar_high / granularity) * granularity
            
            # Count number of levels
            num_levels = int(round((high_level - low_level) / granularity)) + 1
            
            if num_levels <= 0:
                continue
            
            # Distribute volume evenly
            volume_per_level = bar_volume / num_levels
            
            # Add volume to each level
            current = low_level
            for _ in range(num_levels):
                price_key = round(current, 2)
                volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                current += granularity
        
        return volume_profile
    
    def _identify_hvn_zones(self, volume_profile: Dict[float, float], 
                            atr: float, num_zones: int = 10) -> List[HVNZone]:
        """
        Identify top N non-overlapping HVN zones.
        
        Uses ATR/2 as the zone half-width (matching Module 04 logic).
        
        Args:
            volume_profile: Dict of price -> volume
            atr: ATR value for zone width calculation
            num_zones: Number of HVN zones to identify (default 10)
            
        Returns:
            List of HVNZone objects, sorted by volume (highest first)
        """
        if not volume_profile:
            return []
        
        half_zone = atr / 2
        
        # DEBUG: Log ATR and zone width calculations
        logger.info(f"=" * 60)
        logger.info(f"HVN ZONE IDENTIFICATION DEBUG")
        logger.info(f"=" * 60)
        logger.info(f"Input ATR: ${atr:.4f}")
        logger.info(f"Half Zone (ATR/2): ${half_zone:.4f}")
        logger.info(f"Total Zone Width: ${atr:.4f}")
        logger.info(f"Volume profile levels: {len(volume_profile)}")
        
        # Sort all price levels by volume descending
        sorted_levels = sorted(
            volume_profile.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        selected_zones = []
        
        for price, volume in sorted_levels:
            # Check if this price overlaps with any already-selected zone
            has_overlap = False
            
            for existing_zone in selected_zones:
                if abs(price - existing_zone.poc_price) < atr:  # Full ATR separation
                    has_overlap = True
                    break
            
            # Add if no overlap
            if not has_overlap:
                rank = len(selected_zones) + 1
                zone = HVNZone(
                    poc_price=round(price, 2),
                    zone_high=round(price + half_zone, 2),
                    zone_low=round(price - half_zone, 2),
                    volume=volume,
                    rank=rank
                )
                selected_zones.append(zone)
                
                # DEBUG: Log each selected zone
                logger.info(f"  HVN #{rank}: POC=${zone.poc_price:.2f}, "
                           f"Low=${zone.zone_low:.2f}, High=${zone.zone_high:.2f}, "
                           f"Width=${zone.zone_high - zone.zone_low:.2f}")
            
            # Stop when we have enough zones
            if len(selected_zones) >= num_zones:
                break
        
        logger.info(f"Total HVN zones selected: {len(selected_zones)}")
        logger.info(f"=" * 60)
        
        return selected_zones
    
    def fetch_all_tickers(self, tickers: List[str], 
                          n_bars: int = DEFAULT_BAR_COUNT,
                          timeframe_minutes: int = DEFAULT_BAR_TIMEFRAME,
                          m5_atrs: Dict[str, float] = None) -> Dict[str, ChartData]:
        """
        Fetch data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            n_bars: Number of bars per ticker
            timeframe_minutes: Bar timeframe in minutes
            m5_atrs: Dict of ticker -> M5 ATR values
            
        Returns:
            Dict mapping ticker to ChartData
        """
        result = {}
        m5_atrs = m5_atrs or {}
        
        for i, ticker in enumerate(tickers):
            logger.info(f"Fetching {ticker} ({i+1}/{len(tickers)})")
            result[ticker] = self.fetch_last_n_bars(
                ticker, n_bars, timeframe_minutes,
                m5_atr=m5_atrs.get(ticker)
            )
            
            # Rate limiting
            if i < len(tickers) - 1:
                time.sleep(API_DELAY)
        
        return result


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the Polygon fetcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch M15 bars')
    parser.add_argument('ticker', type=str, help='Stock ticker')
    parser.add_argument('--bars', type=int, default=120, help='Number of bars')
    parser.add_argument('--tf', type=int, default=15, help='Timeframe in minutes')
    
    args = parser.parse_args()
    
    fetcher = PolygonBarFetcher()
    data = fetcher.fetch_last_n_bars(args.ticker, args.bars, args.tf)
    
    print(f"\n{'='*60}")
    print(f"Ticker: {data.ticker}")
    print(f"Bars fetched: {data.bar_count}")
    print(f"Fetch time: {data.fetch_time}")
    print(f"Price range: ${data.price_range[0]:.2f} - ${data.price_range[1]:.2f}")
    print(f"Current price: ${data.current_price:.2f}")
    print(f"Volume profile levels: {len(data.volume_profile)}")
    print(f"M5 ATR: ${data.m5_atr:.2f}")
    print(f"\nTop 10 HVN Zones:")
    for zone in data.hvn_zones:
        print(f"  #{zone.rank}: ${zone.poc_price:.2f} (${zone.zone_low:.2f} - ${zone.zone_high:.2f})")
    print(f"{'='*60}")
    
    if not data.bars.empty:
        print("\nFirst 5 bars:")
        print(data.bars.head())
        print("\nLast 5 bars:")
        print(data.bars.tail())


if __name__ == "__main__":
    main()
