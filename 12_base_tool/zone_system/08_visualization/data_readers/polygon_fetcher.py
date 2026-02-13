# polygon_fetcher.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\data_readers\
# Purpose: Fetch H1 candle data and epoch VbP from Polygon API

"""
Polygon Data Fetcher for Module 08 Visualization V2

Features:
- Fetches H1 bars for candlestick display (240 bars)
- Fetches M15 bars for full epoch VbP (configurable: M15, M5, or M1)
- Builds volume profile at $0.01 granularity
- No HVN highlighting (POC lines from Excel instead)
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
    CANDLE_BAR_COUNT, CANDLE_TIMEFRAME,
    VBP_TIMEFRAME, VBP_GRANULARITY, DISPLAY_TIMEZONE
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ChartData:
    """Container for chart-ready data"""
    ticker: str
    candle_bars: pd.DataFrame      # H1 OHLCV for candlesticks
    vbp_volume_profile: Dict[float, float]  # Full epoch VbP at $0.01
    epoch_start_date: str          # User-defined start date
    epoch_high: float              # Highest price in epoch
    epoch_low: float               # Lowest price in epoch
    fetch_time: datetime
    candle_count: int
    vbp_bar_count: int
    
    @property
    def candle_price_range(self) -> Tuple[float, float]:
        """Get price range from visible candles"""
        if self.candle_bars.empty:
            return (0, 0)
        return (self.candle_bars['low'].min(), self.candle_bars['high'].max())
    
    @property
    def current_price(self) -> float:
        """Get current price (last close)"""
        if self.candle_bars.empty:
            return 0
        return self.candle_bars['close'].iloc[-1]


# =============================================================================
# POLYGON FETCHER
# =============================================================================

class PolygonDataFetcher:
    """Fetch bar data from Polygon API for V2 visualization"""
    
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
    
    def fetch_chart_data(self, ticker: str, epoch_start_date: str,
                         candle_bars: int = CANDLE_BAR_COUNT,
                         candle_tf: int = CANDLE_TIMEFRAME,
                         vbp_tf: int = VBP_TIMEFRAME) -> ChartData:
        """
        Fetch all data needed for chart visualization.
        
        Args:
            ticker: Stock symbol (e.g., "TSLA")
            epoch_start_date: Start date for VbP "YYYY-MM-DD"
            candle_bars: Number of H1 candles (default 240)
            candle_tf: Candle timeframe in minutes (default 60)
            vbp_tf: VbP bar timeframe in minutes (default 15)
            
        Returns:
            ChartData with candles and epoch VbP
        """
        ticker = ticker.upper().strip()
        fetch_time = datetime.now()
        end_date = fetch_time.strftime('%Y-%m-%d')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"FETCHING DATA FOR {ticker}")
        logger.info(f"{'='*60}")
        logger.info(f"Epoch: {epoch_start_date} to {end_date}")
        
        # Fetch H1 candles (recent bars for display)
        logger.info(f"Fetching {candle_bars} H{candle_tf//60} candles...")
        candles = self._fetch_recent_bars(ticker, candle_bars, candle_tf)
        logger.info(f"Got {len(candles)} candles")
        
        # Fetch VbP bars for full epoch
        logger.info(f"Fetching M{vbp_tf} bars for epoch VbP...")
        vbp_bars = self._fetch_epoch_bars(ticker, epoch_start_date, end_date, vbp_tf)
        logger.info(f"Got {len(vbp_bars)} VbP bars")
        
        # Calculate epoch high/low from VbP bars
        if not vbp_bars.empty:
            epoch_high = vbp_bars['high'].max()
            epoch_low = vbp_bars['low'].min()
        else:
            epoch_high = 0
            epoch_low = 0
        
        logger.info(f"Epoch range: ${epoch_low:.2f} - ${epoch_high:.2f}")
        
        # Build volume profile at $0.01 granularity
        volume_profile = self._build_volume_profile(vbp_bars, VBP_GRANULARITY)
        logger.info(f"Built VbP with {len(volume_profile)} price levels")
        logger.info(f"{'='*60}")
        
        return ChartData(
            ticker=ticker,
            candle_bars=candles,
            vbp_volume_profile=volume_profile,
            epoch_start_date=epoch_start_date,
            epoch_high=epoch_high,
            epoch_low=epoch_low,
            fetch_time=fetch_time,
            candle_count=len(candles),
            vbp_bar_count=len(vbp_bars)
        )
    
    def _fetch_recent_bars(self, ticker: str, n_bars: int, 
                           timeframe_minutes: int) -> pd.DataFrame:
        """
        Fetch the most recent N bars for candlestick display.
        
        Args:
            ticker: Stock symbol
            n_bars: Number of bars to fetch
            timeframe_minutes: Bar size in minutes (60 for H1)
            
        Returns:
            DataFrame with OHLCV data
        """
        # Calculate date range needed
        end_date = datetime.now().strftime('%Y-%m-%d')
        # For 240 H1 bars, need ~40 calendar days
        days_needed = max(60, (n_bars * timeframe_minutes) // (6.5 * 60) + 10)
        start_date = (datetime.now() - timedelta(days=days_needed)).strftime('%Y-%m-%d')
        
        bars = self._fetch_bars(ticker, start_date, end_date, timeframe_minutes)
        
        if not bars.empty:
            bars = bars.tail(n_bars).copy()
        
        return bars
    
    def _fetch_epoch_bars(self, ticker: str, start_date: str, 
                          end_date: str, timeframe_minutes: int) -> pd.DataFrame:
        """
        Fetch bars for the full epoch period (for VbP calculation).
        Uses chunked requests for long periods.
        
        Args:
            ticker: Stock symbol
            start_date: Epoch start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            timeframe_minutes: Bar size in minutes
            
        Returns:
            DataFrame with OHLCV data for full epoch
        """
        all_data = []
        current_start = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        chunk_days = 30  # Fetch in 30-day chunks
        chunk_num = 1
        
        while current_start < end_dt:
            chunk_end = min(current_start + timedelta(days=chunk_days), end_dt)
            
            try:
                chunk_data = self._fetch_bars(
                    ticker,
                    current_start.strftime('%Y-%m-%d'),
                    chunk_end.strftime('%Y-%m-%d'),
                    timeframe_minutes
                )
                
                if not chunk_data.empty:
                    all_data.append(chunk_data)
                    logger.debug(f"Chunk {chunk_num}: {len(chunk_data)} bars")
                
                # Rate limiting
                time.sleep(API_DELAY)
                
            except Exception as e:
                logger.warning(f"Chunk {chunk_num} failed: {e}")
            
            current_start = chunk_end
            chunk_num += 1
        
        if all_data:
            combined = pd.concat(all_data)
            combined = combined[~combined.index.duplicated(keep='first')]
            combined = combined.sort_index()
            return combined
        
        return pd.DataFrame()
    
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
        
        if bars.empty:
            return volume_profile
        
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
    
    def fetch_all_tickers(self, ticker_epochs: Dict[str, str],
                          candle_bars: int = CANDLE_BAR_COUNT,
                          candle_tf: int = CANDLE_TIMEFRAME,
                          vbp_tf: int = VBP_TIMEFRAME) -> Dict[str, ChartData]:
        """
        Fetch data for multiple tickers.
        
        Args:
            ticker_epochs: Dict mapping ticker to epoch start date
            candle_bars: Number of candles per ticker
            candle_tf: Candle timeframe in minutes
            vbp_tf: VbP timeframe in minutes
            
        Returns:
            Dict mapping ticker to ChartData
        """
        result = {}
        tickers = list(ticker_epochs.keys())
        
        for i, ticker in enumerate(tickers):
            epoch_start = ticker_epochs[ticker]
            logger.info(f"Fetching {ticker} ({i+1}/{len(tickers)})")
            
            if not epoch_start:
                logger.warning(f"No epoch start date for {ticker}, using 30 days ago")
                epoch_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            result[ticker] = self.fetch_chart_data(
                ticker, epoch_start, candle_bars, candle_tf, vbp_tf
            )
            
            # Rate limiting between tickers
            if i < len(tickers) - 1:
                time.sleep(API_DELAY)
        
        return result


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the Polygon fetcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch chart data')
    parser.add_argument('ticker', type=str, help='Stock ticker')
    parser.add_argument('start_date', type=str, help='Epoch start date (YYYY-MM-DD)')
    parser.add_argument('--candles', type=int, default=240, help='Number of H1 candles')
    parser.add_argument('--vbp-tf', type=int, default=15, help='VbP timeframe in minutes')
    
    args = parser.parse_args()
    
    fetcher = PolygonDataFetcher()
    data = fetcher.fetch_chart_data(args.ticker, args.start_date, 
                                     candle_bars=args.candles, vbp_tf=args.vbp_tf)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {data.ticker}")
    print(f"{'='*60}")
    print(f"Epoch: {data.epoch_start_date}")
    print(f"Epoch range: ${data.epoch_low:.2f} - ${data.epoch_high:.2f}")
    print(f"Candles: {data.candle_count}")
    print(f"VbP bars: {data.vbp_bar_count}")
    print(f"VbP levels: {len(data.vbp_volume_profile)}")
    print(f"Current price: ${data.current_price:.2f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
