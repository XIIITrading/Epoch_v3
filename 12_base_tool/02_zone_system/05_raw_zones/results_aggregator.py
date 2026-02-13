# results_aggregator.py - Epoch Results Aggregator
# Collects zone results from multiple tickers
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
Adapted from Meridian results_aggregator.py
Key changes:
- Simplified for Epoch's 10-POC structure
- No category separation (single unified list)
"""

from typing import Dict
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class EpochResultsAggregator:
    """Collects and organizes zone results from multiple tickers"""

    def __init__(self):
        """Initialize the aggregator"""
        self.all_results = []
        self.ticker_count = 0
        
    def add_ticker_results(self, ticker_id: str, ticker: str, date: str, 
                          price: float, direction: str, zones_df: pd.DataFrame):
        """
        Add results from a single ticker to the aggregator
        
        Args:
            ticker_id: Ticker ID (e.g., 'SPY.113024')
            ticker: Ticker symbol (e.g., 'SPY')
            date: Date string (e.g., '11-30-24')
            price: Last price
            direction: Direction/composite from market_overview (e.g., 'Bull+')
            zones_df: DataFrame with zone results from EpochCalculator
        """
        if zones_df is None or zones_df.empty:
            logger.warning(f"No zones found for {ticker_id}")
            return
        
        # Add metadata columns to each zone
        for idx, zone in zones_df.iterrows():
            zone_record = {
                'ticker_id': ticker_id,
                'ticker': ticker,
                'date': date,
                'price': price,
                'direction': direction,
                'zone_id': zone['Zone_ID'],
                'hvn_poc': zone['HVN_POC'],
                'zone_high': zone['Zone_High'],
                'zone_low': zone['Zone_Low'],
                'overlaps': zone['Overlaps'],
                'score': zone['Score'],
                'rank': zone['Rank'],
                'confluences': zone['Confluences']
            }
            self.all_results.append(zone_record)
        
        self.ticker_count += 1
        logger.info(f"Added {len(zones_df)} zones from {ticker_id}")
    
    def get_all_results(self) -> pd.DataFrame:
        """
        Get ALL zones (unfiltered) grouped by ticker
        
        Returns all zones regardless of rank, sorted by ticker_id and score.
        Used for writing to raw_zones sheet.
        
        Returns:
            DataFrame: All zones grouped by ticker, sorted by score
        """
        if not self.all_results:
            logger.warning("No results to return")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(self.all_results)
        
        print(f"\nPreparing {len(df)} total zones from {self.ticker_count} tickers for raw_zones...")
        
        # Sort by ticker_id, then by score descending within each ticker
        sorted_df = df.sort_values(['ticker_id', 'score'], ascending=[True, False])
        
        # Print breakdown by ticker and rank
        print(f"\n  Zones by ticker (all ranks):")
        for ticker_id in sorted_df['ticker_id'].unique():
            ticker_zones = sorted_df[sorted_df['ticker_id'] == ticker_id]
            rank_counts = ticker_zones['rank'].value_counts()
            l5 = rank_counts.get('L5', 0)
            l4 = rank_counts.get('L4', 0)
            l3 = rank_counts.get('L3', 0)
            l2 = rank_counts.get('L2', 0)
            l1 = rank_counts.get('L1', 0)
            print(f"    {ticker_id}: {len(ticker_zones)} zones (L5:{l5}, L4:{l4}, L3:{l3}, L2:{l2}, L1:{l1})")
        
        return sorted_df
    
    def get_filtered_results(self, min_rank: str = 'L2') -> pd.DataFrame:
        """
        Get filtered zones (L2+ by default)
        
        Args:
            min_rank: Minimum rank to include ('L2', 'L3', 'L4', 'L5')
        
        Returns:
            DataFrame: Filtered zones sorted by ticker and score
        """
        if not self.all_results:
            logger.warning("No results to filter")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.all_results)
        
        # Define rank hierarchy
        rank_values = {'L5': 5, 'L4': 4, 'L3': 3, 'L2': 2, 'L1': 1}
        min_value = rank_values.get(min_rank, 2)
        
        # Filter by rank
        filtered_df = df[df['rank'].map(rank_values) >= min_value].copy()
        
        print(f"\nFiltered to {len(filtered_df)} zones with rank >= {min_rank}")
        
        return filtered_df.sort_values(['ticker_id', 'score'], ascending=[True, False])
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics about collected results
        
        Returns:
            dict: Summary statistics
        """
        if not self.all_results:
            return {
                'total_tickers': 0,
                'total_zones': 0,
                'l5_count': 0,
                'l4_count': 0,
                'l3_count': 0,
                'l2_count': 0,
                'l1_count': 0,
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0
            }
        
        df = pd.DataFrame(self.all_results)
        rank_counts = df['rank'].value_counts()
        
        return {
            'total_tickers': self.ticker_count,
            'total_zones': len(df),
            'l5_count': rank_counts.get('L5', 0),
            'l4_count': rank_counts.get('L4', 0),
            'l3_count': rank_counts.get('L3', 0),
            'l2_count': rank_counts.get('L2', 0),
            'l1_count': rank_counts.get('L1', 0),
            'avg_score': round(df['score'].mean(), 2),
            'max_score': df['score'].max(),
            'min_score': df['score'].min()
        }
    
    def clear(self):
        """Clear all accumulated results"""
        self.all_results = []
        self.ticker_count = 0
        logger.info("Results aggregator cleared")
