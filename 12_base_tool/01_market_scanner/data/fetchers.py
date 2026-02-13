"""
Data fetching abstraction layer.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

import sys
import os

# Add the parent directory to path so we can import the 09_data_server as a package
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import from 09_data_server package
try:
    # Import as a proper Python package
    import importlib
    data_server = importlib.import_module('09_data_server')
    DataFetcher = data_server.DataFetcher
    PolygonConfig = data_server.PolygonConfig
except ImportError as e:
    # Create a mock for development/testing
    print(f"Warning: Could not import 09_data_server module: {e}")
    
    class DataFetcher:
        def __init__(self, config=None):
            self.config = config
            
        def fetch_data(self, **kwargs):
            import pandas as pd
            return pd.DataFrame()
    
    class PolygonConfig:
        def __init__(self, config_dict=None):
            self.config = config_dict or {}

# Import local config
try:
    from ..config import config
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config

logger = logging.getLogger(__name__)

class DataFetcherInterface(ABC):
    """Abstract interface for data fetchers."""
    
    @abstractmethod
    def fetch_historical(self, 
                        symbol: str,
                        start_date: datetime,
                        end_date: datetime) -> pd.DataFrame:
        """Fetch historical daily data."""
        pass
    
    @abstractmethod
    def fetch_intraday(self,
                      symbol: str,
                      start_time: datetime,
                      end_time: datetime,
                      timeframe: str = '1min') -> pd.DataFrame:
        """Fetch intraday data."""
        pass

class PolygonDataFetcher(DataFetcherInterface):
    """Polygon.io data fetcher implementation."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize Polygon fetcher."""
        self.fetcher = DataFetcher(
            config=PolygonConfig({'cache_enabled': cache_enabled})
        )
    
    def fetch_historical(self, 
                        symbol: str,
                        start_date: datetime,
                        end_date: datetime) -> pd.DataFrame:
        """Fetch historical daily data from Polygon."""
        try:
            df = self.fetcher.fetch_data(
                symbol=symbol,
                timeframe='1d',
                start_date=start_date,
                end_date=end_date,
                use_cache=True,
                validate=True,
                fill_gaps=True
            )
            return df
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_intraday(self,
                      symbol: str,
                      start_time: datetime,
                      end_time: datetime,
                      timeframe: str = '1min') -> pd.DataFrame:
        """Fetch intraday data from Polygon."""
        try:
            df = self.fetcher.fetch_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_time,
                end_date=end_time,
                use_cache=True,
                validate=True
            )
            return df
        except Exception as e:
            logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
            return pd.DataFrame()