"""
Abstract base class for market filters.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import pandas as pd

class BaseFilter(ABC):
    """Abstract base class for all market filters."""
    
    @abstractmethod
    def apply_filters(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Apply filter criteria to market data."""
        pass
    
    @abstractmethod
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate market data before processing."""
        pass
    
    @abstractmethod
    def get_filter_summary(self, market_data: pd.DataFrame, 
                          filtered_data: pd.DataFrame) -> Dict:
        """Generate summary statistics for filtering process."""
        pass