"""
Data validation utilities.
"""
from typing import List, Tuple, Dict
import pandas as pd

class DataValidator:
    """Utilities for validating market data."""
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate OHLCV data."""
        errors = []
        
        # Required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for nulls
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            errors.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
        
        # Check price relationships
        if 'high' in df.columns and 'low' in df.columns:
            invalid_hl = df[df['high'] < df['low']]
            if not invalid_hl.empty:
                errors.append(f"High < Low in {len(invalid_hl)} rows")
        
        # Check for negative values
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns and (df[col] < 0).any():
                errors.append(f"Negative values in {col}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_scan_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate scan data structure."""
        errors = []
        
        required_cols = [
            'ticker', 'price', 'avg_daily_volume', 
            'premarket_volume', 'dollar_volume', 'atr', 'atr_percent'
        ]
        
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Type checks
        if 'ticker' in df.columns and not df['ticker'].dtype == 'object':
            errors.append("Ticker column should be string type")
        
        # Range checks
        numeric_cols = ['price', 'avg_daily_volume', 'premarket_volume', 
                       'dollar_volume', 'atr', 'atr_percent']
        
        for col in numeric_cols:
            if col in df.columns:
                if (df[col] < 0).any():
                    errors.append(f"Negative values in {col}")
        
        return len(errors) == 0, errors