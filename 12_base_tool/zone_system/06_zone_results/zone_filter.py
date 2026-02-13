"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Zone Filter
================================================================================
Organization: XIII Trading LLC
Purpose: Filter zones by proximity, add tier classification, eliminate overlaps
================================================================================

VERSION 1.1 CHANGES:
- No longer filters out L1 zones - ALL ranks (L1-L5) are included
- Added tier classification (T1/T2/T3) based on confluence rank
- Selection is proximity-based (closest to price wins)
- Tier indicates quality, not selection priority
================================================================================
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional

from epoch_config import (
    ATR_GROUP_1_THRESHOLD,
    ATR_GROUP_2_THRESHOLD,
    MAX_ZONES_PER_TICKER,
    VALID_RANKS,
    TIER_MAPPING,
    TIER_DESCRIPTIONS,
    VERBOSE
)


class ZoneFilter:
    """
    Filters and processes zones from raw_zones to produce actionable zone list.
    
    Processing Pipeline (V1.1):
    1. Add tier classification (T1/T2/T3) based on rank
    2. Filter by rank (now includes ALL L1-L5)
    3. Calculate ATR distance from current price
    4. Assign proximity groups (Group 1/2 or excluded)
    5. Sort by proximity group, then score, then distance
    6. Eliminate overlapping zones (highest score wins)
    """
    
    def __init__(self):
        """Initialize the filter with configuration values."""
        self.atr_group_1_threshold = ATR_GROUP_1_THRESHOLD
        self.atr_group_2_threshold = ATR_GROUP_2_THRESHOLD
        self.max_zones_per_ticker = MAX_ZONES_PER_TICKER
        self.valid_ranks = VALID_RANKS
        self.tier_mapping = TIER_MAPPING
        
    def add_tier_classification(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add tier classification column based on rank.
        
        Tier mapping:
        - L1, L2 → T1 (Lower confluence quality)
        - L3 → T2 (Medium confluence quality)
        - L4, L5 → T3 (High confluence quality)
        
        Args:
            zones_df: DataFrame with 'rank' column
            
        Returns:
            DataFrame with added 'tier' column
        """
        if zones_df.empty:
            zones_df['tier'] = []
            return zones_df
        
        zones_df = zones_df.copy()
        zones_df['tier'] = zones_df['rank'].map(self.tier_mapping)
        
        # Handle any unmapped ranks
        zones_df['tier'] = zones_df['tier'].fillna('T1')
        
        if VERBOSE:
            tier_counts = zones_df['tier'].value_counts()
            print(f"  Tier classification: {tier_counts.to_dict()}")
        
        return zones_df
        
    def filter_by_rank(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter zones to include valid ranks.
        
        V1.1 CHANGE: Now includes ALL ranks (L1-L5).
        This method is kept for pipeline consistency but no longer removes zones.
        
        Args:
            zones_df: DataFrame with all zones
            
        Returns:
            DataFrame with valid ranks (now all zones)
        """
        if zones_df.empty:
            return zones_df
        
        initial_count = len(zones_df)
        filtered_df = zones_df[zones_df['rank'].isin(self.valid_ranks)].copy()
        removed_count = initial_count - len(filtered_df)
        
        if VERBOSE:
            print(f"  Rank filter: {initial_count} → {len(filtered_df)} "
                  f"(all L1-L5 ranks included)")
            if removed_count > 0:
                print(f"    Note: {removed_count} zones had invalid/missing ranks")
        
        return filtered_df
    
    def add_proximity_data(self, zones_df: pd.DataFrame, 
                           price_atr_data: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Add ATR distance and proximity group columns to zones DataFrame.
        
        Args:
            zones_df: DataFrame with zones
            price_atr_data: Dict mapping ticker_id to {'price': float, 'd1_atr': float}
            
        Returns:
            DataFrame with added columns: atr_distance, proximity_group
        """
        if zones_df.empty:
            zones_df['atr_distance'] = []
            zones_df['proximity_group'] = []
            return zones_df
        
        # Calculate ATR distance and proximity group for each zone
        atr_distances = []
        proximity_groups = []
        
        for _, row in zones_df.iterrows():
            ticker_id = row['ticker_id']
            
            # Get price/ATR for this ticker
            ticker_data = price_atr_data.get(ticker_id)
            
            if ticker_data is None:
                if VERBOSE:
                    print(f"    WARNING: No price/ATR data for {ticker_id}")
                atr_distances.append(None)
                proximity_groups.append(None)
                continue
            
            price = ticker_data['price']
            d1_atr = ticker_data['d1_atr']
            
            # Calculate zone midpoint
            zone_high = row['zone_high']
            zone_low = row['zone_low']
            zone_midpoint = (zone_high + zone_low) / 2
            
            # Calculate ATR distance
            distance = abs(zone_midpoint - price)
            atr_distance = distance / d1_atr if d1_atr > 0 else float('inf')
            atr_distances.append(round(atr_distance, 3))
            
            # Assign proximity group
            if atr_distance <= self.atr_group_1_threshold:
                proximity_groups.append(1)
            elif atr_distance <= self.atr_group_2_threshold:
                proximity_groups.append(2)
            else:
                proximity_groups.append(None)  # Excluded
        
        zones_df['atr_distance'] = atr_distances
        zones_df['proximity_group'] = proximity_groups
        
        return zones_df
    
    def filter_by_proximity(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove zones that are beyond 2 ATR from current price.
        
        Args:
            zones_df: DataFrame with proximity_group column
            
        Returns:
            DataFrame with only Group 1 and Group 2 zones
        """
        if zones_df.empty:
            return zones_df
        
        initial_count = len(zones_df)
        
        # Keep only zones with proximity_group 1 or 2
        filtered_df = zones_df[zones_df['proximity_group'].notna()].copy()
        excluded_count = initial_count - len(filtered_df)
        
        if VERBOSE:
            print(f"  Proximity filter: {initial_count} → {len(filtered_df)} "
                  f"(excluded {excluded_count} zones beyond 2 ATR)")
        
        return filtered_df
    
    def sort_zones(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort zones by: ticker_id, proximity_group (asc), score (desc), atr_distance (asc).
        
        This ensures closest zones to price are prioritized, with higher scores
        breaking ties.
        
        Args:
            zones_df: DataFrame with zones
            
        Returns:
            Sorted DataFrame
        """
        if zones_df.empty:
            return zones_df
        
        sorted_df = zones_df.sort_values(
            by=['ticker_id', 'proximity_group', 'score', 'atr_distance'],
            ascending=[True, True, False, True]
        ).copy()
        
        return sorted_df
    
    def eliminate_overlaps(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        """
        Eliminate overlapping zones within each ticker. Highest score wins.
        
        Two zones overlap if: zone1_low < zone2_high AND zone1_high > zone2_low
        
        Args:
            zones_df: Sorted DataFrame with zones
            
        Returns:
            DataFrame with overlapping zones removed
        """
        if zones_df.empty:
            return zones_df
        
        final_zones = []
        total_eliminated = 0
        
        # Process each ticker separately
        for ticker_id in zones_df['ticker_id'].unique():
            ticker_zones = zones_df[zones_df['ticker_id'] == ticker_id]
            selected = []
            eliminated_count = 0
            
            for _, zone in ticker_zones.iterrows():
                # Check if this zone overlaps with any already selected zone
                has_overlap = False
                
                for selected_zone in selected:
                    if self._zones_overlap(zone, selected_zone):
                        has_overlap = True
                        eliminated_count += 1
                        break
                
                # Add zone if no overlap and haven't hit max limit
                if not has_overlap and len(selected) < self.max_zones_per_ticker:
                    selected.append(zone)
            
            final_zones.extend(selected)
            total_eliminated += eliminated_count
            
            if VERBOSE and eliminated_count > 0:
                print(f"    {ticker_id}: eliminated {eliminated_count} overlapping zones")
        
        result_df = pd.DataFrame(final_zones)
        
        if VERBOSE:
            print(f"  Overlap elimination: {len(zones_df)} → {len(result_df)} "
                  f"(eliminated {total_eliminated} overlapping zones)")
        
        return result_df
    
    def _zones_overlap(self, zone1: pd.Series, zone2: pd.Series) -> bool:
        """
        Check if two zones overlap.
        
        Args:
            zone1: First zone (pandas Series with zone_high, zone_low)
            zone2: Second zone (pandas Series with zone_high, zone_low)
            
        Returns:
            True if zones overlap, False otherwise
        """
        # Two ranges overlap if: start1 < end2 AND end1 > start2
        return (zone1['zone_low'] < zone2['zone_high'] and 
                zone1['zone_high'] > zone2['zone_low'])
    
    def process_all(self, zones_df: pd.DataFrame,
                    price_atr_data: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Execute complete filtering pipeline.
        
        Pipeline (V1.1):
        1. Add tier classification (T1/T2/T3)
        2. Filter by rank (now keeps ALL L1-L5)
        3. Add ATR distance and proximity group
        4. Filter by proximity (within 2 ATR only)
        5. Sort by ticker, proximity group, score
        6. Eliminate overlapping zones
        
        Args:
            zones_df: Raw zones DataFrame from Module 05
            price_atr_data: Dict mapping ticker_id to price/ATR data
            
        Returns:
            Filtered, sorted DataFrame with tier classification and no overlapping zones
        """
        if VERBOSE:
            print(f"\n  Starting filter pipeline with {len(zones_df)} zones...")
        
        # Step 1: Add tier classification
        df = self.add_tier_classification(zones_df)
        
        # Step 2: Filter by rank (now includes all L1-L5)
        df = self.filter_by_rank(df)
        
        if df.empty:
            if VERBOSE:
                print("  WARNING: No zones remain after rank filter")
            return df
        
        # Step 3: Add proximity data
        df = self.add_proximity_data(df, price_atr_data)
        
        # Step 4: Filter by proximity
        df = self.filter_by_proximity(df)
        
        if df.empty:
            if VERBOSE:
                print("  WARNING: No zones remain after proximity filter")
            return df
        
        # Step 5: Sort
        df = self.sort_zones(df)
        
        # Step 6: Eliminate overlaps
        df = self.eliminate_overlaps(df)
        
        if VERBOSE:
            print(f"\n  Filter pipeline complete: {len(df)} zones in final output")
            self._print_summary(df)
        
        return df
    
    def _print_summary(self, df: pd.DataFrame) -> None:
        """Print summary statistics for filtered zones."""
        if df.empty:
            return
        
        print(f"\n  Summary by Tier (Quality Classification):")
        for tier in ['T3', 'T2', 'T1']:
            count = len(df[df['tier'] == tier])
            if count > 0:
                desc = TIER_DESCRIPTIONS.get(tier, '')
                print(f"    {tier} ({desc}): {count} zones")
        
        print(f"\n  Summary by Rank:")
        for rank in ['L5', 'L4', 'L3', 'L2', 'L1']:
            count = len(df[df['rank'] == rank])
            if count > 0:
                print(f"    {rank}: {count} zones")
        
        print(f"\n  Summary by Proximity Group:")
        for group in [1, 2]:
            count = len(df[df['proximity_group'] == group])
            if count > 0:
                label = "≤1 ATR" if group == 1 else "1-2 ATR"
                print(f"    Group {group} ({label}): {count} zones")
        
        print(f"\n  Zones per Ticker:")
        for ticker_id in df['ticker_id'].unique():
            ticker_df = df[df['ticker_id'] == ticker_id]
            count = len(ticker_df)
            tier_dist = ticker_df['tier'].value_counts().to_dict()
            tier_str = ', '.join([f"{t}:{c}" for t, c in sorted(tier_dist.items())])
            print(f"    {ticker_id}: {count} zones ({tier_str})")


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    import numpy as np
    
    print("=" * 70)
    print("ZONE FILTER V1.1 - STANDALONE TEST")
    print("=" * 70)
    
    # Create sample test data with ALL ranks (L1-L5)
    print("\nCreating sample test data with all ranks (L1-L5)...")
    
    test_zones = pd.DataFrame({
        'ticker_id': ['TEST_123'] * 10,
        'ticker': ['TEST'] * 10,
        'date': ['12-01-24'] * 10,
        'price': [100.0] * 10,
        'direction': ['Bull'] * 10,
        'zone_id': [f'hvn_poc{i}' for i in range(1, 11)],
        'hvn_poc': [100.0, 101.0, 102.0, 95.0, 90.0, 
                    85.0, 80.0, 75.0, 70.0, 65.0],
        'zone_high': [100.5, 101.5, 102.5, 95.5, 90.5,
                      85.5, 80.5, 75.5, 70.5, 65.5],
        'zone_low': [99.5, 100.5, 101.5, 94.5, 89.5,
                     84.5, 79.5, 74.5, 69.5, 64.5],
        'overlaps': [5, 4, 3, 3, 2, 2, 1, 1, 0, 0],
        'score': [12.5, 10.0, 8.0, 7.5, 5.0, 4.0, 3.5, 3.0, 2.0, 0.5],
        'rank': ['L5', 'L4', 'L3', 'L3', 'L2', 'L2', 'L2', 'L2', 'L1', 'L1'],
        'confluences': ['m1_01,w1_01'] * 10
    })
    
    test_price_atr = {
        'TEST_123': {'price': 100.0, 'd1_atr': 5.0}
    }
    
    print(f"Test data: {len(test_zones)} zones")
    print(f"Price: ${test_price_atr['TEST_123']['price']:.2f}")
    print(f"D1 ATR: ${test_price_atr['TEST_123']['d1_atr']:.2f}")
    print(f"Ranks in test data: {test_zones['rank'].value_counts().to_dict()}")
    
    # Run filter pipeline
    print("\n" + "-" * 70)
    print("Running filter pipeline...")
    print("-" * 70)
    
    zone_filter = ZoneFilter()
    result = zone_filter.process_all(test_zones, test_price_atr)
    
    print("\n" + "-" * 70)
    print("Final Result:")
    print("-" * 70)
    print(result[['zone_id', 'hvn_poc', 'score', 'rank', 'tier',
                  'atr_distance', 'proximity_group']].to_string())