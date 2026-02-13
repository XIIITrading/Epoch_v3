"""
Abstract base class for market scanners.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

class BaseScanner(ABC):
    """Abstract base class for all market scanners."""
    
    @abstractmethod
    def run_scan(self, 
                scan_time: Optional[datetime] = None,
                progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """Run the market scan."""
        pass
    
    @abstractmethod
    def get_summary_stats(self, scan_results: pd.DataFrame) -> Dict:
        """Generate summary statistics for scan results."""
        pass
    
    @abstractmethod
    def export_results(self, scan_results: pd.DataFrame, output_path: str):
        """Export scan results to file."""
        pass