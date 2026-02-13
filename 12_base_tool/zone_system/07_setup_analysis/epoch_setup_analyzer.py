"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Epoch Setup Analyzer
================================================================================
Organization: XIII Trading LLC
Purpose: Analyze zones to identify bull/bear POCs, calculate targets,
         and determine primary/secondary setups
================================================================================

VERSION 1.1 CHANGES:
- Removed rank filter - ALL ranks (L1-L5) now included in selection
- Selection is proximity-based (closest to price)
- Added tier to output DataFrames
- Tier indicates quality, not selection priority

ADAPTED FROM MERIDIAN:
- POC Source: Epoch uses 10 HVN POCs (volume-ranked) instead of 24 timeframe POCs
- Target Priority: Volume rank (hvn_poc1 = highest) instead of timeframe cascade
- Column Names: epch_* instead of mdn1_*
================================================================================
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

from epoch_config import (
    MIN_RR_THRESHOLD,
    DEFAULT_RR_CALC,
    VALID_RANKS,
    TIER_MAPPING,
    TIER_DESCRIPTIONS,
    VERBOSE
)


class EpochSetupAnalyzer:
    """
    Analyzes filtered zones to identify trading setups.
    
    Pipeline (V1.1 - Proximity-Based):
    1. Identify bull/bear POC anchors (closest above/below price - ALL ranks)
    2. Apply pivot logic (if only one exists, use for both)
    3. Calculate targets using 3R/4R logic with HVN POC cascade
    4. Assign primary/secondary based on market direction
    5. Calculate risk:reward ratios
    6. Include tier in output for quality indication
    """
    
    def __init__(self):
        """Initialize with configuration values."""
        self.min_rr_threshold = MIN_RR_THRESHOLD
        self.default_rr_calc = DEFAULT_RR_CALC
        self.valid_ranks = VALID_RANKS  # V1.1: Now includes ALL L1-L5
        self.tier_mapping = TIER_MAPPING
        
    def analyze_all_zones(self, df_zones: pd.DataFrame, 
                          ticker_data: Dict[str, Dict],
                          direction_data: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Complete setup analysis pipeline for all zones.
        
        V1.1 CHANGE: Now uses ALL ranks (L1-L5) for selection.
        Selection is proximity-based, tier indicates quality.
        
        Args:
            df_zones: DataFrame with all zones (L1-L5 included)
            ticker_data: Dict mapping ticker_id to {'price': float, 'hvn_pocs': list}
            direction_data: Dict mapping ticker_id to direction string
            
        Returns:
            Tuple of (df_zones_updated, df_primary, df_secondary)
        """
        print("\n" + "=" * 70)
        print("SETUP ANALYSIS - PROXIMITY-BASED SELECTION (V1.1)")
        print("All ranks (L1-L5) included, tier indicates quality")
        print("=" * 70)
        
        # Step 1: Calculate bull/bear POCs (now includes ALL ranks)
        df_zones = self._calculate_bull_bear_pocs(df_zones)
        
        # Step 2: Apply pivot logic
        df_zones = self._apply_pivot_logic(df_zones)
        
        # Step 3: Calculate targets using HVN POC cascade
        df_zones = self._calculate_targets(df_zones, ticker_data)
        
        # Step 4: Identify primary/secondary setups
        df_primary, df_secondary = self._identify_primary_secondary(df_zones, direction_data)
        
        # Step 5: Calculate risk:reward
        df_primary = self._calculate_risk_reward(df_primary)
        df_secondary = self._calculate_risk_reward(df_secondary)
        
        # Step 6: Format output (now includes tier)
        df_primary_out = self._format_output(df_primary)
        df_secondary_out = self._format_output(df_secondary)
        
        print(f"\n✓ Setup analysis complete")
        print(f"  Primary setups: {len(df_primary_out)}")
        print(f"  Secondary setups: {len(df_secondary_out)}")
        
        # Print tier summary
        self._print_tier_summary(df_primary_out, df_secondary_out)
        
        return df_zones, df_primary_out, df_secondary_out
    
    def _calculate_bull_bear_pocs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate bullish and bearish POC anchor points.
        
        V1.1 CHANGE: No longer filters by rank - ALL L1-L5 zones included.
        Selection is purely proximity-based.
        
        Bull POC: Minimum hvn_poc ABOVE current price (closest above)
        Bear POC: Maximum hvn_poc BELOW current price (closest below)
        """
        print("\n  Step 1: Calculating bull/bear POCs (proximity-based, all ranks)...")
        
        df = df.copy()
        
        # Ensure numeric types
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['hvn_poc'] = pd.to_numeric(df['hvn_poc'], errors='coerce')
        
        # V1.1: Calculate bullish POCs (minimum above price) - ALL RANKS
        mask_bull = df['hvn_poc'] > df['price']
        bull_pocs = df[mask_bull].groupby('ticker_id')['hvn_poc'].min().to_dict()
        
        # V1.1: Calculate bearish POCs (maximum below price) - ALL RANKS
        mask_bear = df['hvn_poc'] < df['price']
        bear_pocs = df[mask_bear].groupby('ticker_id')['hvn_poc'].max().to_dict()
        
        # Add POC prices to all rows in each ticker group
        df['epch_bull_price'] = df['ticker_id'].map(bull_pocs)
        df['epch_bear_price'] = df['ticker_id'].map(bear_pocs)
        
        # Mark the specific zones with 'X'
        df['epch_bull'] = df.apply(
            lambda row: 'X' if (
                row['ticker_id'] in bull_pocs and
                row['hvn_poc'] == bull_pocs[row['ticker_id']]
            ) else '',
            axis=1
        )
        
        df['epch_bear'] = df.apply(
            lambda row: 'X' if (
                row['ticker_id'] in bear_pocs and
                row['hvn_poc'] == bear_pocs[row['ticker_id']]
            ) else '',
            axis=1
        )
        
        # Log details including tier
        bulls_found = len(bull_pocs)
        bears_found = len(bear_pocs)
        print(f"    Found {bulls_found} bullish POCs and {bears_found} bearish POCs")
        
        # Show tier distribution of selected POCs
        bull_zones = df[df['epch_bull'] == 'X']
        bear_zones = df[df['epch_bear'] == 'X']
        
        if not bull_zones.empty and 'tier' in bull_zones.columns:
            bull_tiers = bull_zones['tier'].value_counts().to_dict()
            print(f"    Bull POC tiers: {bull_tiers}")
        
        if not bear_zones.empty and 'tier' in bear_zones.columns:
            bear_tiers = bear_zones['tier'].value_counts().to_dict()
            print(f"    Bear POC tiers: {bear_tiers}")
        
        return df
    
    def _apply_pivot_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        If only one POC exists (bull or bear), use it as pivot for both.
        """
        print("\n  Step 2: Applying pivot logic...")
        
        df = df.copy()
        pivots_applied = 0
        
        for ticker_id in df['ticker_id'].unique():
            mask = df['ticker_id'] == ticker_id
            
            bull_poc = df.loc[mask, 'epch_bull_price'].iloc[0]
            bear_poc = df.loc[mask, 'epch_bear_price'].iloc[0]
            
            if pd.notna(bull_poc) and pd.isna(bear_poc):
                # Use bull as bear pivot
                df.loc[mask, 'epch_bear_price'] = bull_poc
                pivot_mask = (df['ticker_id'] == ticker_id) & (df['hvn_poc'] == bull_poc) & (df['epch_bull'] == 'X')
                df.loc[pivot_mask, 'epch_bear'] = 'X'
                pivots_applied += 1
                
            elif pd.isna(bull_poc) and pd.notna(bear_poc):
                # Use bear as bull pivot
                df.loc[mask, 'epch_bull_price'] = bear_poc
                pivot_mask = (df['ticker_id'] == ticker_id) & (df['hvn_poc'] == bear_poc) & (df['epch_bear'] == 'X')
                df.loc[pivot_mask, 'epch_bull'] = 'X'
                pivots_applied += 1
        
        if pivots_applied > 0:
            print(f"    Applied pivot logic to {pivots_applied} tickers")
        else:
            print(f"    No pivot logic needed (all tickers have both bull and bear POCs)")
        
        return df
    
    def _calculate_targets(self, df_zones: pd.DataFrame, 
                           ticker_data: Dict[str, Dict]) -> pd.DataFrame:
        """
        Calculate targets using HVN POC cascade with 3R/4R distance logic.
        
        For Epoch, priority is by volume rank: hvn_poc1 (highest volume) → hvn_poc10
        
        Bull: Find POC above zone that is >= 3R from zone_high, prefer higher volume
        Bear: Find POC below zone that is <= 3R from zone_low, prefer higher volume
        
        If no POC meets 3R threshold, use calculated 4R level.
        """
        print("\n  Step 3: Calculating targets with 3R/4R HVN POC logic...")
        
        df_zones = df_zones.copy()
        
        # Ensure numeric types
        df_zones['zone_high'] = pd.to_numeric(df_zones['zone_high'], errors='coerce')
        df_zones['zone_low'] = pd.to_numeric(df_zones['zone_low'], errors='coerce')
        
        # Get zones marked for bull and bear setups
        bull_zones = df_zones[df_zones['epch_bull'] == 'X'][
            ['ticker_id', 'hvn_poc', 'zone_high', 'zone_low']
        ].drop_duplicates('ticker_id')
        
        bear_zones = df_zones[df_zones['epch_bear'] == 'X'][
            ['ticker_id', 'hvn_poc', 'zone_high', 'zone_low']
        ].drop_duplicates('ticker_id')
        
        targets = []
        
        # Process bull targets
        for _, row in bull_zones.iterrows():
            ticker_id = row['ticker_id']
            hvn_poc = row['hvn_poc']
            zone_high = row['zone_high']
            zone_low = row['zone_low']
            zone_risk = zone_high - zone_low
            
            if ticker_id not in ticker_data or zone_risk <= 0:
                continue
            
            # Get HVN POCs for this ticker
            hvn_pocs = ticker_data[ticker_id].get('hvn_pocs', [])
            valid_pocs = [p for p in hvn_pocs if p is not None]
            
            # Calculate 3R and 4R thresholds
            target_3r = zone_high + (zone_risk * self.min_rr_threshold)
            target_4r = zone_high + (zone_risk * self.default_rr_calc)
            
            # Find POCs above hvn_poc that meet 3R threshold
            # Priority: lower index = higher volume
            bull_target = None
            bull_target_id = None
            
            for i, poc in enumerate(hvn_pocs):
                if poc is None:
                    continue
                # POC must be above the zone's hvn_poc and >= 3R from zone_high
                if poc > hvn_poc and poc >= target_3r:
                    if bull_target is None or i < int(bull_target_id.replace('hvn_poc', '')) - 1:
                        bull_target = poc
                        bull_target_id = f"hvn_poc{i + 1}"
            
            # If no POC meets 3R, use calculated 4R
            if bull_target is None:
                bull_target = target_4r
                bull_target_id = "4R_calc"
            
            # Find or update this ticker in targets
            existing = next((t for t in targets if t['ticker_id'] == ticker_id), None)
            if existing:
                existing['epch_bull_target'] = bull_target
                existing['epch_bull_target_id'] = bull_target_id
            else:
                targets.append({
                    'ticker_id': ticker_id,
                    'epch_bull_target': bull_target,
                    'epch_bull_target_id': bull_target_id,
                    'epch_bear_target': None,
                    'epch_bear_target_id': None
                })
        
        # Process bear targets
        for _, row in bear_zones.iterrows():
            ticker_id = row['ticker_id']
            hvn_poc = row['hvn_poc']
            zone_high = row['zone_high']
            zone_low = row['zone_low']
            zone_risk = zone_high - zone_low
            
            if ticker_id not in ticker_data or zone_risk <= 0:
                continue
            
            # Get HVN POCs for this ticker
            hvn_pocs = ticker_data[ticker_id].get('hvn_pocs', [])
            
            # Calculate 3R and 4R thresholds
            target_3r = zone_low - (zone_risk * self.min_rr_threshold)
            target_4r = zone_low - (zone_risk * self.default_rr_calc)
            
            # Find POCs below hvn_poc that meet 3R threshold
            bear_target = None
            bear_target_id = None
            
            for i, poc in enumerate(hvn_pocs):
                if poc is None:
                    continue
                # POC must be below the zone's hvn_poc and <= 3R from zone_low
                if poc < hvn_poc and poc <= target_3r:
                    if bear_target is None or i < int(bear_target_id.replace('hvn_poc', '')) - 1:
                        bear_target = poc
                        bear_target_id = f"hvn_poc{i + 1}"
            
            # If no POC meets 3R, use calculated 4R
            if bear_target is None:
                bear_target = target_4r
                bear_target_id = "4R_calc"
            
            # Find or update this ticker in targets
            existing = next((t for t in targets if t['ticker_id'] == ticker_id), None)
            if existing:
                existing['epch_bear_target'] = bear_target
                existing['epch_bear_target_id'] = bear_target_id
            else:
                targets.append({
                    'ticker_id': ticker_id,
                    'epch_bull_target': None,
                    'epch_bull_target_id': None,
                    'epch_bear_target': bear_target,
                    'epch_bear_target_id': bear_target_id
                })
        
        # Merge targets back with df_zones
        if targets:
            df_targets = pd.DataFrame(targets)
            merge_cols = ['ticker_id', 'epch_bull_target', 'epch_bear_target',
                          'epch_bull_target_id', 'epch_bear_target_id']
            df_zones = df_zones.merge(df_targets[merge_cols], on='ticker_id', how='left')
        else:
            df_zones['epch_bull_target'] = None
            df_zones['epch_bear_target'] = None
            df_zones['epch_bull_target_id'] = None
            df_zones['epch_bear_target_id'] = None
        
        bulls_found = sum(1 for t in targets if t.get('epch_bull_target') is not None)
        bears_found = sum(1 for t in targets if t.get('epch_bear_target') is not None)
        print(f"    Found {bulls_found} bull targets and {bears_found} bear targets")
        
        return df_zones
    
    def _identify_primary_secondary(self, df: pd.DataFrame,
                                     direction_data: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Identify primary and secondary zones based on direction.
        
        Bull/Bull+: primary=bull (with trend), secondary=bear (counter-trend)
        Bear/Bear+: primary=bear (with trend), secondary=bull (counter-trend)
        
        V1.1: Tier is now included in the output.
        """
        print("\n  Step 4: Identifying primary and secondary setups...")
        
        bull_zones = df[df['epch_bull'] == 'X'].copy()
        bear_zones = df[df['epch_bear'] == 'X'].copy()
        
        primary_zones = []
        secondary_zones = []
        
        for ticker_id in df['ticker_id'].unique():
            direction = direction_data.get(ticker_id, 'N/A')
            
            bull_zone = bull_zones[bull_zones['ticker_id'] == ticker_id]
            bear_zone = bear_zones[bear_zones['ticker_id'] == ticker_id]
            
            if direction in ['Bull', 'Bull+']:
                # Primary: Bull (with trend)
                if not bull_zone.empty:
                    primary = bull_zone.iloc[0].copy()
                    primary['target'] = primary.get('epch_bull_target')
                    primary['target_id'] = primary.get('epch_bull_target_id', '')
                    primary_zones.append(primary)
                
                # Secondary: Bear (counter-trend)
                if not bear_zone.empty:
                    secondary = bear_zone.iloc[0].copy()
                    secondary['direction'] = 'Bear'  # Opposite
                    secondary['target'] = secondary.get('epch_bear_target')
                    secondary['target_id'] = secondary.get('epch_bear_target_id', '')
                    secondary_zones.append(secondary)
                elif not bull_zone.empty:
                    # Use bull zone as secondary with opposite direction
                    secondary = bull_zone.iloc[0].copy()
                    secondary['direction'] = 'Bear'
                    secondary['target'] = secondary.get('epch_bear_target')
                    secondary['target_id'] = secondary.get('epch_bear_target_id', '')
                    secondary_zones.append(secondary)
            
            elif direction in ['Bear', 'Bear+']:
                # Primary: Bear (with trend)
                if not bear_zone.empty:
                    primary = bear_zone.iloc[0].copy()
                    primary['target'] = primary.get('epch_bear_target')
                    primary['target_id'] = primary.get('epch_bear_target_id', '')
                    primary_zones.append(primary)
                
                # Secondary: Bull (counter-trend)
                if not bull_zone.empty:
                    secondary = bull_zone.iloc[0].copy()
                    secondary['direction'] = 'Bull'  # Opposite
                    secondary['target'] = secondary.get('epch_bull_target')
                    secondary['target_id'] = secondary.get('epch_bull_target_id', '')
                    secondary_zones.append(secondary)
                elif not bear_zone.empty:
                    # Use bear zone as secondary with opposite direction
                    secondary = bear_zone.iloc[0].copy()
                    secondary['direction'] = 'Bull'
                    secondary['target'] = secondary.get('epch_bull_target')
                    secondary['target_id'] = secondary.get('epch_bull_target_id', '')
                    secondary_zones.append(secondary)
            
            else:
                # Unknown direction - skip
                if VERBOSE:
                    print(f"    WARNING: Unknown direction '{direction}' for {ticker_id}")
        
        df_primary = pd.DataFrame(primary_zones) if primary_zones else pd.DataFrame()
        df_secondary = pd.DataFrame(secondary_zones) if secondary_zones else pd.DataFrame()
        
        print(f"    Identified {len(df_primary)} primary and {len(df_secondary)} secondary setups")
        
        return df_primary, df_secondary
    
    def _calculate_risk_reward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate risk:reward ratio.
        
        Bull zone (target > hvn_poc):
          Reward = target - hvn_poc
          Risk = hvn_poc - zone_low
        
        Bear zone (target < hvn_poc):
          Reward = hvn_poc - target
          Risk = zone_high - hvn_poc
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        def calc_rr(row):
            target = row.get('target')
            hvn_poc = row.get('hvn_poc')
            zone_high = row.get('zone_high')
            zone_low = row.get('zone_low')
            
            if pd.isna(target) or pd.isna(hvn_poc):
                return None
            
            if target > hvn_poc:
                # Bull zone
                reward = target - hvn_poc
                risk = hvn_poc - zone_low
            else:
                # Bear zone
                reward = hvn_poc - target
                risk = zone_high - hvn_poc
            
            return round(reward / risk, 2) if risk > 0 else None
        
        df['r_r'] = df.apply(calc_rr, axis=1)
        
        return df
    
    def _format_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format output DataFrame with required columns for Analysis sheet.
        
        V1.1: Now includes tier column.
        """
        # V1.1: Added tier to output columns
        output_cols = ['ticker', 'direction', 'ticker_id', 'zone_id',
                       'hvn_poc', 'zone_high', 'zone_low', 'tier',
                       'target_id', 'target', 'r_r']
        
        if df.empty:
            return pd.DataFrame(columns=output_cols)
        
        # Ensure all columns exist
        for col in output_cols:
            if col not in df.columns:
                df[col] = ''
        
        df_out = df[output_cols].copy()
        df_out = df_out.sort_values('ticker_id').reset_index(drop=True)
        
        return df_out
    
    def _print_tier_summary(self, df_primary: pd.DataFrame, df_secondary: pd.DataFrame) -> None:
        """Print tier distribution summary for primary and secondary setups."""
        print("\n  Tier Distribution in Setups:")
        
        if not df_primary.empty and 'tier' in df_primary.columns:
            primary_tiers = df_primary['tier'].value_counts().to_dict()
            tier_str = ', '.join([f"{t}:{c}" for t, c in sorted(primary_tiers.items())])
            print(f"    Primary: {tier_str}")
        
        if not df_secondary.empty and 'tier' in df_secondary.columns:
            secondary_tiers = df_secondary['tier'].value_counts().to_dict()
            tier_str = ', '.join([f"{t}:{c}" for t, c in sorted(secondary_tiers.items())])
            print(f"    Secondary: {tier_str}")


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EPOCH SETUP ANALYZER V1.1 - STANDALONE TEST")
    print("=" * 70)
    print("\nThis module requires integration with Excel.")
    print("Run setup_runner.py for full test.")