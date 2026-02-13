# epoch_hvn_identifier.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier\calculations\
# Purpose: Calculate HVN POCs for user-defined epoch periods

"""
Epoch HVN Identifier - Core Calculation Engine

Key differences from Meridian:
1. Single user-defined epoch (start_date to current) instead of 9 fixed timeframes
2. $0.01 price granularity instead of 100 fixed levels
3. 10 non-overlapping POCs instead of 54
4. Volume-only ranking (highest volume = poc1) instead of proximity-based
5. Overlap prevention using ATR/2 threshold
6. Includes all market hours (pre/post/RTH)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from math import floor, ceil
import logging
import time
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class POCResult:
    """Container for a single POC result"""
    price: float
    volume: float
    rank: int  # 1 = highest volume
    
    def __repr__(self):
        return f"POC(rank={self.rank}, price=${self.price:.2f}, vol={self.volume:,.0f})"


@dataclass
class EpochAnalysisResult:
    """Container for complete epoch analysis results"""
    ticker: str
    start_date: str
    end_date: str
    pocs: List[POCResult]
    total_volume: float
    price_range: Tuple[float, float]
    bars_analyzed: int
    atr_used: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Excel writing"""
        result = {
            'ticker': self.ticker,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_volume': self.total_volume,
            'bars_analyzed': self.bars_analyzed,
            'atr_used': self.atr_used,
        }
        # Add POCs
        for i, poc in enumerate(self.pocs, 1):
            result[f'hvn_poc{i}'] = poc.price
        # Fill remaining with 0 if less than 10
        for i in range(len(self.pocs) + 1, 11):
            result[f'hvn_poc{i}'] = 0.0
        return result


# =============================================================================
# POLYGON DATA FETCHER
# =============================================================================

class PolygonDataFetcher:
    """Fetch minute-level OHLCV data from Polygon API"""
    
    def __init__(self, api_key: str):
        """Initialize with Polygon API key"""
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        
    def fetch_minute_bars(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch minute-level OHLCV data from Polygon.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            
        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: timestamp (UTC)
        """
        endpoint = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/minute/{start_date}/{end_date}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                raise ValueError(f"API returned status: {data.get('status')}")
            
            results = data.get('results', [])
            
            if not results:
                logger.warning(f"No data returned for {ticker}")
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
            
            # Convert timestamp from milliseconds to datetime UTC
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df.set_index('timestamp', inplace=True)
            
            # Keep only OHLCV
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Fetched {len(df)} bars for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise
    
    def fetch_data_chunked(self, ticker: str, start_date: str, end_date: str, 
                           chunk_days: int = 30) -> pd.DataFrame:
        """
        Fetch data in chunks to handle API limits and long date ranges.
        
        Args:
            ticker: Stock symbol
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            chunk_days: Days per API request (default 30)
            
        Returns:
            Combined DataFrame with all data
        """
        all_data = []
        current_start = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        logger.info(f"Fetching {ticker} data in {chunk_days}-day chunks")
        
        chunk_num = 1
        while current_start < end_dt:
            chunk_end = min(current_start + timedelta(days=chunk_days), end_dt)
            
            try:
                chunk_data = self.fetch_minute_bars(
                    ticker,
                    current_start.strftime('%Y-%m-%d'),
                    chunk_end.strftime('%Y-%m-%d')
                )
                
                if not chunk_data.empty:
                    all_data.append(chunk_data)
                    logger.info(f"Chunk {chunk_num}: {len(chunk_data)} bars")
                
                # Rate limiting - be nice to the API
                time.sleep(0.25)
                
            except Exception as e:
                logger.warning(f"Chunk {chunk_num} failed: {e}")
            
            current_start = chunk_end
            chunk_num += 1
        
        if all_data:
            combined = pd.concat(all_data)
            combined = combined[~combined.index.duplicated(keep='first')]
            combined = combined.sort_index()
            logger.info(f"Total: {len(combined)} bars from {chunk_num - 1} chunks")
            return combined
        
        return pd.DataFrame()


# =============================================================================
# EPOCH HVN IDENTIFIER (CORE CLASS)
# =============================================================================

class EpochHVNIdentifier:
    """
    Calculate HVN POCs for user-defined epoch periods.
    
    Key features:
    - $0.01 price granularity
    - Single epoch period (start_date to current)
    - 10 non-overlapping POCs ranked by volume
    - ATR/2 overlap prevention
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the HVN Identifier.
        
        Args:
            api_key: Polygon API key. If None, attempts to load from credentials.py
        """
        if api_key is None:
            try:
                from .credentials import POLYGON_API_KEY
                api_key = POLYGON_API_KEY
            except ImportError:
                try:
                    from credentials import POLYGON_API_KEY
                    api_key = POLYGON_API_KEY
                except ImportError:
                    raise ValueError("No API key provided and credentials.py not found")
        
        self.data_fetcher = PolygonDataFetcher(api_key)
        self.price_granularity = 0.01
        self.poc_count = 10
        self.overlap_atr_divisor = 2
        self.default_atr = 2.0
    
    def analyze(self, ticker: str, start_date: str, end_date: str = None,
                atr_value: float = None) -> EpochAnalysisResult:
        """
        Main analysis method - calculates HVN POCs for the epoch period.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            start_date: Epoch start date "YYYY-MM-DD" (user input from Excel)
            end_date: Epoch end date "YYYY-MM-DD" (None = current date)
            atr_value: Daily ATR for overlap calculation (None = calculate from data)
            
        Returns:
            EpochAnalysisResult with 10 non-overlapping POCs ranked by volume
        """
        ticker = ticker.upper().strip()
        
        # Default end_date to today
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"EPOCH HVN ANALYSIS: {ticker}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"{'='*60}")
        
        # Fetch minute data for the epoch
        bars = self._fetch_minute_data(ticker, start_date, end_date)
        
        if bars.empty:
            logger.error(f"No data available for {ticker} in epoch period")
            return self._empty_result(ticker, start_date, end_date)
        
        logger.info(f"Loaded {len(bars)} minute bars")
        
        # Build volume profile at $0.01 granularity
        volume_profile = self._build_volume_profile(bars)
        
        if not volume_profile:
            logger.error(f"Could not build volume profile for {ticker}")
            return self._empty_result(ticker, start_date, end_date)
        
        logger.info(f"Built volume profile with {len(volume_profile)} price levels")
        
        # Determine ATR for overlap threshold
        if atr_value is None or atr_value <= 0:
            atr_value = self._calculate_simple_atr(bars)
            logger.info(f"Calculated ATR from data: ${atr_value:.2f}")
        else:
            logger.info(f"Using provided ATR: ${atr_value:.2f}")
        
        # Select top 10 non-overlapping POCs by volume
        pocs = self._select_pocs_no_overlap(volume_profile, atr_value)
        
        logger.info(f"Selected {len(pocs)} non-overlapping POCs")
        for poc in pocs:
            logger.info(f"  {poc}")
        
        # Calculate total volume
        total_volume = sum(volume_profile.values())
        
        # Get price range
        price_range = (min(volume_profile.keys()), max(volume_profile.keys()))
        
        return EpochAnalysisResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            pocs=pocs,
            total_volume=total_volume,
            price_range=price_range,
            bars_analyzed=len(bars),
            atr_used=atr_value
        )
    
    def _fetch_minute_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch 1-minute bars for the epoch period.
        Uses chunked requests to handle long date ranges.
        """
        return self.data_fetcher.fetch_data_chunked(ticker, start_date, end_date)
    
    def _build_volume_profile(self, bars: pd.DataFrame) -> Dict[float, float]:
        """
        Build volume profile at $0.01 granularity.
        
        For each bar, volume is distributed proportionally across all price levels
        touched by that bar (from low to high).
        
        Args:
            bars: DataFrame with OHLCV data
            
        Returns:
            Dict mapping price level (rounded to $0.01) to total volume
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
            
            # Round to $0.01 boundaries
            low_level = floor(bar_low / self.price_granularity) * self.price_granularity
            high_level = ceil(bar_high / self.price_granularity) * self.price_granularity
            
            # Count number of $0.01 levels in this bar's range
            num_levels = int(round((high_level - low_level) / self.price_granularity)) + 1
            
            if num_levels <= 0:
                continue
            
            # Distribute volume evenly across all levels
            volume_per_level = bar_volume / num_levels
            
            # Add volume to each price level
            current = low_level
            for _ in range(num_levels):
                price_key = round(current, 2)
                volume_profile[price_key] = volume_profile.get(price_key, 0) + volume_per_level
                current += self.price_granularity
        
        return volume_profile
    
    def _calculate_simple_atr(self, bars: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate a simple ATR from the minute data.
        Aggregates to daily bars first, then calculates ATR.
        
        Args:
            bars: Minute-level OHLCV DataFrame
            period: ATR lookback period (default 14 days)
            
        Returns:
            ATR value, or default if calculation fails
        """
        try:
            # Resample to daily bars
            daily = bars.resample('D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            if len(daily) < period:
                logger.warning(f"Not enough daily bars for ATR, using default")
                return self.default_atr
            
            # Calculate True Range
            daily['prev_close'] = daily['close'].shift(1)
            daily['tr1'] = daily['high'] - daily['low']
            daily['tr2'] = abs(daily['high'] - daily['prev_close'])
            daily['tr3'] = abs(daily['low'] - daily['prev_close'])
            daily['true_range'] = daily[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR as simple moving average of True Range
            atr = daily['true_range'].tail(period).mean()
            
            if pd.isna(atr) or atr <= 0:
                return self.default_atr
            
            return round(atr, 2)
            
        except Exception as e:
            logger.warning(f"ATR calculation failed: {e}, using default")
            return self.default_atr
    
    def _select_pocs_no_overlap(self, volume_profile: Dict[float, float], 
                                 atr: float) -> List[POCResult]:
        """
        Select top POCs ensuring no overlap (minimum ATR/2 distance apart).
        
        POCs are ranked purely by volume (highest volume = poc1).
        No two POCs can be within ATR/2 of each other.
        
        Args:
            volume_profile: Dict of price -> volume
            atr: Daily ATR value
            
        Returns:
            List of POCResult objects, sorted by volume (descending)
        """
        overlap_threshold = atr / self.overlap_atr_divisor
        
        logger.info(f"Overlap threshold: ${overlap_threshold:.2f} (ATR/2)")
        
        # Sort all price levels by volume descending
        sorted_levels = sorted(
            volume_profile.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        selected_pocs = []
        
        for price, volume in sorted_levels:
            # Check if this price overlaps with any already-selected POC
            has_overlap = False
            
            for existing_poc in selected_pocs:
                if abs(price - existing_poc.price) < overlap_threshold:
                    has_overlap = True
                    break
            
            # Add if no overlap
            if not has_overlap:
                rank = len(selected_pocs) + 1
                selected_pocs.append(POCResult(
                    price=round(price, 2),
                    volume=volume,
                    rank=rank
                ))
            
            # Stop when we have enough POCs
            if len(selected_pocs) >= self.poc_count:
                break
        
        return selected_pocs
    
    def _empty_result(self, ticker: str, start_date: str, end_date: str) -> EpochAnalysisResult:
        """Create an empty result when analysis fails"""
        return EpochAnalysisResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            pocs=[],
            total_volume=0,
            price_range=(0, 0),
            bars_analyzed=0,
            atr_used=self.default_atr
        )


# =============================================================================
# STANDALONE TESTING
# =============================================================================

def main():
    """Test the Epoch HVN Identifier standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Epoch HVN Identifier')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('start_date', type=str, help='Epoch start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None, help='Epoch end date (default: today)')
    parser.add_argument('--atr', type=float, default=None, help='ATR value for overlap threshold')
    
    args = parser.parse_args()
    
    try:
        identifier = EpochHVNIdentifier()
        result = identifier.analyze(
            ticker=args.ticker,
            start_date=args.start_date,
            end_date=args.end_date,
            atr_value=args.atr
        )
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {result.ticker}")
        print(f"{'='*60}")
        print(f"Epoch: {result.start_date} to {result.end_date}")
        print(f"Bars analyzed: {result.bars_analyzed:,}")
        print(f"Total volume: {result.total_volume:,.0f}")
        print(f"Price range: ${result.price_range[0]:.2f} - ${result.price_range[1]:.2f}")
        print(f"ATR used: ${result.atr_used:.2f}")
        print(f"\nTop 10 POCs (ranked by volume):")
        print(f"{'-'*40}")
        
        for poc in result.pocs:
            print(f"  POC {poc.rank}: ${poc.price:.2f} ({poc.volume:,.0f} volume)")
        
        # Show as dict for Excel writing
        print(f"\nExcel output format:")
        output = result.to_dict()
        for i in range(1, 11):
            print(f"  hvn_poc{i}: ${output[f'hvn_poc{i}']:.2f}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()