"""
Pre-market filter implementation.
"""
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd

from .base_filter import BaseFilter
from .criteria import FilterCriteria
from .scoring_engine import ScoringEngine, InterestScoreWeights

logger = logging.getLogger(__name__)

class PremarketFilter(BaseFilter):
    """
    Pre-market filter for stock screening.
    Applies filtering criteria and calculates interest scores.
    """
    
    def __init__(self, 
                 criteria: Optional[FilterCriteria] = None,
                 weights: Optional[InterestScoreWeights] = None):
        """Initialize the pre-market filter."""
        self.criteria = criteria or FilterCriteria()
        
        # Use gap-optimized weights if gap filtering is enabled
        if weights is None and self.criteria.min_gap_percent > 0:
            weights = InterestScoreWeights.for_gap_scan()
            
        self.scoring_engine = ScoringEngine(weights)
        
        logger.info("PremarketFilter initialized with criteria: %s", 
                   self.criteria.to_dict())
    
    def apply_filters(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Apply all filter criteria to market data."""
        if market_data.empty:
            logger.warning("Empty market data provided")
            return pd.DataFrame()
        
        # Validate required columns
        is_valid, errors = self.validate_data(market_data)
        if not is_valid:
            raise ValueError(f"Data validation failed: {errors}")
        
        # Start with copy to avoid modifying original
        df = market_data.copy()
        initial_count = len(df)
        
        # Apply each filter
        filters = {
            'price_min': df['price'] >= self.criteria.min_price,
            'price_max': df['price'] <= self.criteria.max_price,
            'avg_volume': df['avg_daily_volume'] >= self.criteria.min_avg_volume,
            'pm_volume_min': df['premarket_volume'] >= self.criteria.min_premarket_volume,
            'pm_volume_ratio': (df['premarket_volume'] / df['avg_daily_volume']) >= self.criteria.min_premarket_volume_ratio,
            'dollar_volume': df['dollar_volume'] >= self.criteria.min_dollar_volume,
            'atr_min': df['atr'] >= self.criteria.min_atr,
            'atr_percent': df['atr_percent'] >= self.criteria.min_atr_percent
        }
        
        # Add market cap filter if specified
        if self.criteria.min_market_cap and 'market_cap' in df.columns:
            filters['market_cap'] = df['market_cap'] >= self.criteria.min_market_cap
        
        # Add gap filter if specified
        if self.criteria.min_gap_percent > 0 and 'gap_percent' in df.columns:
            if self.criteria.gap_direction == 'up':
                filters['gap_up'] = df['gap_percent'] >= self.criteria.min_gap_percent
            elif self.criteria.gap_direction == 'down':
                filters['gap_down'] = df['gap_percent'] <= -self.criteria.min_gap_percent
            else:  # both
                filters['gap_both'] = df['gap_percent'].abs() >= self.criteria.min_gap_percent
        
        # Combine all filters
        combined_filter = pd.Series(True, index=df.index)
        for filter_name, filter_mask in filters.items():
            combined_filter &= filter_mask
            passed = filter_mask.sum()
            logger.debug(f"Filter '{filter_name}': {passed}/{initial_count} passed")
        
        # Apply combined filter
        filtered_df = df[combined_filter].copy()
        
        logger.info(f"Filtering complete: {len(filtered_df)}/{initial_count} stocks passed all filters")
        
        # Calculate interest scores for filtered stocks
        if not filtered_df.empty:
            filtered_df = self.scoring_engine.calculate_scores(
                filtered_df, 
                self.criteria.min_dollar_volume
            )
        
        return filtered_df
    
    def rank_by_interest(self, filtered_df: pd.DataFrame, 
                        top_n: Optional[int] = None) -> pd.DataFrame:
        """Rank filtered stocks by interest score."""
        return self.scoring_engine.rank_by_score(filtered_df, top_n)
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate market data before processing."""
        errors = []
        
        # Check for required columns
        required_columns = ['ticker', 'price', 'avg_daily_volume', 
                        'premarket_volume', 'dollar_volume', 'atr', 'atr_percent']
        
        # Add gap-specific columns if gap filtering is enabled
        if self.criteria.min_gap_percent > 0:
            required_columns.extend(['gap_percent', 'previous_close'])
            
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
        
        # Check for data types and ranges
        if 'price' in df.columns and (df['price'] < 0).any():
            errors.append("Negative prices found")
        
        if 'avg_daily_volume' in df.columns and (df['avg_daily_volume'] < 0).any():
            errors.append("Negative volumes found")
        
        if 'atr' in df.columns and (df['atr'] < 0).any():
            errors.append("Negative ATR values found")
        
        # Check for missing values ONLY in required columns
        # Don't check optional columns like market_cap
        for col in required_columns:
            if col in df.columns and df[col].isnull().any():
                null_count = df[col].isnull().sum()
                errors.append(f"Missing values in required column '{col}': {null_count}")
        
        return len(errors) == 0, errors
    
    def get_filter_summary(self, market_data: pd.DataFrame, 
                          filtered_data: pd.DataFrame) -> Dict:
        """Generate summary statistics for the filtering process."""
        total_stocks = len(market_data)
        passed_stocks = len(filtered_data)
        
        summary = {
            'total_stocks': total_stocks,
            'passed_filters': passed_stocks,
            'pass_rate': f"{(passed_stocks / total_stocks * 100):.1f}%" if total_stocks > 0 else "0.0%",
            'filter_criteria': self.criteria.to_dict()
        }
        
        if not filtered_data.empty:
            summary.update({
                'interest_score_range': f"{filtered_data['interest_score'].min():.2f} - {filtered_data['interest_score'].max():.2f}",
                'avg_interest_score': f"{filtered_data['interest_score'].mean():.2f}",
                'top_ticker': filtered_data.iloc[0]['ticker'] if len(filtered_data) > 0 else None,
                'top_score': f"{filtered_data.iloc[0]['interest_score']:.2f}" if len(filtered_data) > 0 else None
            })
            
            # Add gap-specific summary if applicable
            if 'gap_percent' in filtered_data.columns:
                summary['avg_gap_percent'] = f"{filtered_data['gap_percent'].mean():.2f}%"
                summary['max_gap_percent'] = f"{filtered_data['gap_percent'].abs().max():.2f}%"
        
        return summary
    
    def explain_score(self, row: pd.Series) -> Dict[str, Dict[str, float]]:
        """Explain the interest score calculation for a single stock."""
        return self.scoring_engine.explain_score(row)