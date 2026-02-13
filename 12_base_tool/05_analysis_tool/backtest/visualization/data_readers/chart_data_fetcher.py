# chart_data_fetcher.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\data_readers\
# Purpose: Fetch OHLCV data for trade visualization charts

"""
Chart Data Fetcher

Fetches minute-level OHLCV data from Polygon API for trade visualization:
- M5 bars for trade day (09:00-16:00 ET)
- H1 bars for last 5 trading days
- M15 bars for last 3 trading days

Also reads zone and HVN POC data from Excel worksheet.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import requests
import time as time_module
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import credentials
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '04_hvn_identifier' / 'calculations'))
    from credentials import POLYGON_API_KEY
except ImportError:
    POLYGON_API_KEY = None
    logger.warning("Could not import POLYGON_API_KEY from credentials.py")


# =============================================================================
# POLYGON DATA FETCHER
# =============================================================================

class PolygonChartDataFetcher:
    """Fetch OHLCV data from Polygon API for chart visualization"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize with Polygon API key.
        
        Args:
            api_key: Polygon API key (None to use from credentials.py)
        """
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("No Polygon API key provided")
        
        self.base_url = "https://api.polygon.io"
        self.et_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC
    
    def fetch_minute_bars(self, ticker: str, start_date: str, end_date: str,
                          multiplier: int = 1, timespan: str = 'minute') -> pd.DataFrame:
        """
        Fetch OHLCV bars from Polygon.
        
        Args:
            ticker: Stock symbol
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            multiplier: Bar size multiplier (1, 5, 15, 60)
            timespan: 'minute' or 'hour'
            
        Returns:
            DataFrame with OHLCV data, index as ET datetime
        """
        endpoint = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            logger.info(f"Fetching {ticker} {multiplier}{timespan[0].upper()} from {start_date} to {end_date}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.warning(f"API returned status: {data.get('status')}")
                return pd.DataFrame()
            
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
                'v': 'volume',
                'vw': 'vwap',
                'n': 'transactions'
            }
            df = df.rename(columns=column_mapping)
            
            # Convert timestamp from milliseconds to ET datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.et_tz)
            df.set_index('timestamp', inplace=True)
            
            # Keep only OHLCV
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Fetched {len(df)} bars")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def get_m5_bars(self, ticker: str, trade_date: str) -> pd.DataFrame:
        """
        Get M5 bars for trade day (09:00-16:00 ET).
        
        Args:
            ticker: Stock symbol
            trade_date: Trade date "YYYY-MM-DD"
            
        Returns:
            DataFrame with M5 OHLCV for 09:00-16:00 ET
        """
        # Fetch 1-minute data and resample to 5-minute
        bars = self.fetch_minute_bars(ticker, trade_date, trade_date, 
                                       multiplier=5, timespan='minute')
        
        if bars.empty:
            return bars
        
        # Filter to 09:00-16:00 ET
        bars = bars.between_time('09:00', '16:00')
        
        return bars
    
    def get_h1_bars(self, ticker: str, end_date: str, trading_days: int = 5) -> pd.DataFrame:
        """
        Get H1 bars for last N trading days.
        
        Args:
            ticker: Stock symbol
            end_date: End date "YYYY-MM-DD"
            trading_days: Number of trading days to include
            
        Returns:
            DataFrame with H1 OHLCV
        """
        # Calculate start date (add buffer for weekends/holidays)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=trading_days * 2)  # 2x buffer
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # Fetch hourly bars
        bars = self.fetch_minute_bars(ticker, start_date, end_date,
                                       multiplier=1, timespan='hour')
        
        if bars.empty:
            return bars
        
        # Get unique trading days and keep last N
        bars['date'] = bars.index.date
        unique_dates = sorted(bars['date'].unique())
        
        if len(unique_dates) > trading_days:
            keep_dates = unique_dates[-trading_days:]
            bars = bars[bars['date'].isin(keep_dates)]
        
        bars = bars.drop(columns=['date'])
        
        return bars
    
    def get_m15_bars(self, ticker: str, end_date: str, trading_days: int = 3) -> pd.DataFrame:
        """
        Get M15 bars for last N trading days.
        
        Args:
            ticker: Stock symbol
            end_date: End date "YYYY-MM-DD"
            trading_days: Number of trading days to include
            
        Returns:
            DataFrame with M15 OHLCV
        """
        # Calculate start date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=trading_days * 2)
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # Fetch 15-minute bars
        bars = self.fetch_minute_bars(ticker, start_date, end_date,
                                       multiplier=15, timespan='minute')
        
        if bars.empty:
            return bars
        
        # Get unique trading days and keep last N
        bars['date'] = bars.index.date
        unique_dates = sorted(bars['date'].unique())
        
        if len(unique_dates) > trading_days:
            keep_dates = unique_dates[-trading_days:]
            bars = bars[bars['date'].isin(keep_dates)]
        
        bars = bars.drop(columns=['date'])
        
        return bars
    
    def get_all_chart_data(self, ticker: str, trade_date: str) -> Dict[str, pd.DataFrame]:
        """
        Get all chart data for a trade.
        
        Args:
            ticker: Stock symbol
            trade_date: Trade date "YYYY-MM-DD"
            
        Returns:
            Dict with 'm5', 'h1', 'm15' DataFrames
        """
        logger.info(f"Fetching all chart data for {ticker} on {trade_date}")
        
        # Rate limiting between requests
        m5_bars = self.get_m5_bars(ticker, trade_date)
        time_module.sleep(0.25)
        
        h1_bars = self.get_h1_bars(ticker, trade_date, trading_days=5)
        time_module.sleep(0.25)
        
        m15_bars = self.get_m15_bars(ticker, trade_date, trading_days=3)
        
        return {
            'm5': m5_bars,
            'h1': h1_bars,
            'm15': m15_bars
        }


# =============================================================================
# ZONE DATA READER
# =============================================================================

class ZoneDataReader:
    """Read zone and HVN POC data from Excel"""
    
    def __init__(self, workbook_path: str = None):
        """
        Initialize zone data reader.
        
        Args:
            workbook_path: Path to epoch_v1.xlsm
        """
        if workbook_path is None:
            workbook_path = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
        
        self.workbook_path = workbook_path
        self.wb = None
    
    def connect(self) -> bool:
        """Connect to Excel workbook"""
        try:
            import xlwings as xw
            self.wb = xw.Book(self.workbook_path)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Excel: {e}")
            return False
    
    def get_zones_for_trade(self, ticker: str, trade_date: str) -> Dict:
        """
        Get Primary and Secondary zone data for a trade.
        
        Args:
            ticker: Stock symbol
            trade_date: Trade date
            
        Returns:
            Dict with 'primary' and 'secondary' zone info
        """
        # This would read from the zone_processor output in Excel
        # For now, return structure that will be populated from backtest data
        
        return {
            'primary': None,
            'secondary': None
        }
    
    def get_hvn_pocs(self, ticker: str) -> List[float]:
        """
        Get HVN POC levels for a ticker from time_hvn section.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            List of up to 10 HVN POC prices
        """
        if not self.wb:
            if not self.connect():
                return []
        
        try:
            ws = self.wb.sheets['bar_data']
            
            # Search for ticker in time_hvn section (rows 59-68, column C)
            pocs = []
            
            for row in range(59, 69):
                cell_ticker = ws.range(f'C{row}').value
                
                if cell_ticker and str(cell_ticker).upper().strip() == ticker.upper():
                    # Found the ticker, read POCs from columns F-O
                    for col in 'FGHIJKLMNO':
                        poc_val = ws.range(f'{col}{row}').value
                        if poc_val and float(poc_val) > 0:
                            pocs.append(float(poc_val))
                    break
            
            logger.info(f"Found {len(pocs)} HVN POCs for {ticker}")
            return pocs
            
        except Exception as e:
            logger.error(f"Error reading HVN POCs: {e}")
            return []


# =============================================================================
# COMBINED DATA PROVIDER
# =============================================================================

class TradeChartDataProvider:
    """Provides all data needed for trade chart visualization"""
    
    def __init__(self, api_key: str = None, workbook_path: str = None):
        """
        Initialize data provider.
        
        Args:
            api_key: Polygon API key
            workbook_path: Path to epoch_v1.xlsm
        """
        self.chart_fetcher = PolygonChartDataFetcher(api_key)
        self.zone_reader = ZoneDataReader(workbook_path)
    
    def get_trade_visualization_data(self, trade) -> Dict:
        """
        Get all data needed to visualize a trade.
        
        Args:
            trade: TradeRecord object
            
        Returns:
            Dict with:
            - 'm5_bars': M5 OHLCV DataFrame
            - 'h1_bars': H1 OHLCV DataFrame  
            - 'm15_bars': M15 OHLCV DataFrame
            - 'zones': Dict with primary/secondary zone info
            - 'hvn_pocs': List of HVN POC prices
        """
        # Get chart data from Polygon
        chart_data = self.chart_fetcher.get_all_chart_data(trade.ticker, trade.date)
        
        # Build zones from trade record
        zones = {
            'primary': {
                'high': trade.zone_high,
                'low': trade.zone_low
            } if trade.zone_type == 'PRIMARY' else None,
            'secondary': {
                'high': trade.zone_high,
                'low': trade.zone_low
            } if trade.zone_type == 'SECONDARY' else None
        }
        
        # If we have zone info but it's the wrong type, put it in primary anyway
        if zones['primary'] is None and zones['secondary'] is None:
            zones['primary'] = {
                'high': trade.zone_high,
                'low': trade.zone_low
            }
        
        # Get HVN POCs from Excel
        hvn_pocs = self.zone_reader.get_hvn_pocs(trade.ticker)
        
        return {
            'm5_bars': chart_data['m5'],
            'h1_bars': chart_data['h1'],
            'm15_bars': chart_data['m15'],
            'zones': zones,
            'hvn_pocs': hvn_pocs
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the data fetcher"""
    
    # Test Polygon fetcher
    try:
        fetcher = PolygonChartDataFetcher()
        
        # Test with SPY
        ticker = "SPY"
        trade_date = "2024-12-06"  # Recent trading day
        
        print(f"\nTesting data fetch for {ticker} on {trade_date}")
        print("=" * 50)
        
        # Get M5 bars
        m5 = fetcher.get_m5_bars(ticker, trade_date)
        print(f"\nM5 bars: {len(m5)} rows")
        if not m5.empty:
            print(f"  Range: {m5.index[0]} to {m5.index[-1]}")
            print(f"  Price: ${m5['low'].min():.2f} - ${m5['high'].max():.2f}")
        
        # Get H1 bars
        h1 = fetcher.get_h1_bars(ticker, trade_date, trading_days=5)
        print(f"\nH1 bars: {len(h1)} rows")
        if not h1.empty:
            print(f"  Range: {h1.index[0]} to {h1.index[-1]}")
        
        # Get M15 bars
        m15 = fetcher.get_m15_bars(ticker, trade_date, trading_days=3)
        print(f"\nM15 bars: {len(m15)} rows")
        if not m15.empty:
            print(f"  Range: {m15.index[0]} to {m15.index[-1]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
