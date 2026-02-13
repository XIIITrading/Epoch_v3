# epoch_calc_engine.py - Epoch Confluence Calculator
# Simplified single-category version of Meridian calc_engine.py
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
KEY DIFFERENCES FROM MERIDIAN:
1. Single category instead of SHORT/MID/LONG
2. 10 HVN POCs (hvn_poc1-10) instead of 54 POCs across 9 timeframes
3. Base score from volume rank (EPOCH_POC_BASE_WEIGHTS) instead of timeframe weights
4. No ATR-based proximity grouping (all zones processed equally)

ZONE CREATION:
- zone_high = hvn_poc + (m15_atr / 2)
- zone_low = hvn_poc - (m15_atr / 2)

CONFLUENCE SCORING:
- Check overlap with all technical levels
- Track max weight per bucket type (no stacking beyond max)
- total_score = base_score + sum(bucket_scores)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EpochCalculator:
    """
    Epoch confluence calculator - processes 10 volume-ranked HVN POCs
    and calculates confluence scores against all technical levels.
    """

    def __init__(self, inputs: Dict, market_structure: Dict, config):
        """
        Initialize calculator
        
        Args:
            inputs: Dict from EpochBarDataReader.read_ticker_data()
                   Contains: ticker, date, price, OHLC, HVN POCs, ATR, Camarilla, options
            market_structure: Dict from EpochMarketOverviewReader.get_ticker_data()
                   Contains: direction, d1_s/w, h4_s/w, h1_s/w, m15_s/w
            config: epoch_config module with weights and thresholds
        """
        self.inputs = inputs
        self.market_structure = market_structure
        self.config = config
        
        # Confluence zones (all technical levels as zones)
        self.zones_data = {}
        
        # Results
        self.zone_results = []

    def calculate_all(self) -> pd.DataFrame:
        """
        Main calculation pipeline
        
        Steps:
        1. Build zones_data dict from all confluence levels
        2. For each HVN POC (1-10):
           a. Create zone (POC +/- m15_atr/2)
           b. Calculate confluence score
           c. Add base score from volume rank
           d. Assign rank (L1-L5)
        3. Return DataFrame with all zones
        
        Returns:
            DataFrame with columns:
            Zone_ID, HVN_POC, Zone_High, Zone_Low, Overlaps, Score, Rank, Confluences
        """
        ticker = self.inputs.get('ticker', 'UNKNOWN')
        print(f"\n{'='*60}")
        print(f"EPOCH CALCULATOR: Processing {ticker}")
        print(f"{'='*60}")
        
        # Step 1: Build all confluence zones
        self._build_zones_data()
        print(f"  Step 1: Built {len(self.zones_data)} confluence zones")
        
        # Step 2: Process each HVN POC
        print(f"  Step 2: Processing HVN POCs...")
        self._process_hvn_pocs()
        
        # Step 3: Create results DataFrame
        if self.zone_results:
            df = pd.DataFrame(self.zone_results)
            
            # Sort by score descending
            df = df.sort_values('Score', ascending=False).reset_index(drop=True)
            
            # Print summary
            rank_counts = df['Rank'].value_counts()
            print(f"\n  Results Summary for {ticker}:")
            print(f"    Total zones: {len(df)}")
            for rank in ['L5', 'L4', 'L3', 'L2', 'L1']:
                count = rank_counts.get(rank, 0)
                if count > 0:
                    print(f"    {rank}: {count}")
            
            return df
        else:
            print(f"  ⚠ No zones calculated for {ticker}")
            return pd.DataFrame()

    def _build_zones_data(self):
        """Build zones around all technical levels for confluence checking"""
        
        # Get ATR values
        atr_values = {
            'm5': self.inputs.get('m5_atr', 0) or 0,
            'm15': self.inputs.get('m15_atr', 0) or 0,
            'h1': self.inputs.get('h1_atr', 0) or 0,
            'd1': self.inputs.get('d1_atr', 0) or 0
        }
        
        # Ensure we have valid ATR values
        if atr_values['m15'] <= 0:
            atr_values['m15'] = atr_values.get('h1', 0) or atr_values.get('d1', 0) / 4 or 1.0
        if atr_values['m5'] <= 0:
            atr_values['m5'] = atr_values['m15'] / 2
        
        # Process Monthly OHLC
        self._add_ohlc_zones('m1', atr_values)
        
        # Process Weekly OHLC
        self._add_ohlc_zones('w1', atr_values)
        
        # Process Daily OHLC
        self._add_ohlc_zones('d1', atr_values)
        
        # Process Prior Period levels
        self._add_prior_period_zones(atr_values)
        
        # Process Overnight levels
        self._add_overnight_zones(atr_values)
        
        # Process Options levels
        self._add_options_zones(atr_values)
        
        # Process Camarilla levels
        self._add_camarilla_zones(atr_values)
        
        # Process Market Structure levels
        self._add_market_structure_zones(atr_values)

    def _add_ohlc_zones(self, prefix: str, atr_values: Dict):
        """Add OHLC zones for a timeframe (m1, w1, d1)"""
        for i in range(1, 5):
            key = f'{prefix}_0{i}'
            if key in self.inputs and self.inputs[key]:
                midpoint = self.inputs[key]
                zone_config = self.config.ZONE_WEIGHTS.get(key, {})
                zone_atr = zone_config.get('zone_atr', 'm15')
                atr_half = atr_values.get(zone_atr, atr_values['m15']) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', f'{prefix}_level')
                }

    def _add_prior_period_zones(self, atr_values: Dict):
        """Add prior period OHLC zones"""
        prior_keys = [
            # Prior Day
            ('d1_po', 'prior_daily'), ('d1_ph', 'prior_daily'),
            ('d1_pl', 'prior_daily'), ('d1_pc', 'prior_daily'),
            # Prior Week
            ('w1_po', 'prior_weekly'), ('w1_ph', 'prior_weekly'),
            ('w1_pl', 'prior_weekly'), ('w1_pc', 'prior_weekly'),
            # Prior Month
            ('m1_po', 'prior_monthly'), ('m1_ph', 'prior_monthly'),
            ('m1_pl', 'prior_monthly'), ('m1_pc', 'prior_monthly'),
        ]
        
        for key, con_type in prior_keys:
            if key in self.inputs and self.inputs[key]:
                midpoint = self.inputs[key]
                zone_config = self.config.ZONE_WEIGHTS.get(key, {})
                zone_atr = zone_config.get('zone_atr', 'm15')
                atr_half = atr_values.get(zone_atr, atr_values['m15']) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', con_type)
                }

    def _add_overnight_zones(self, atr_values: Dict):
        """Add overnight high/low zones"""
        for key in ['d1_onh', 'd1_onl']:
            if key in self.inputs and self.inputs[key]:
                midpoint = self.inputs[key]
                zone_config = self.config.ZONE_WEIGHTS.get(key, {})
                atr_half = atr_values.get('m15', 1.0) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', 'prior_daily')
                }

    def _add_options_zones(self, atr_values: Dict):
        """Add options strike level zones"""
        for i in range(1, 11):
            key = f'op_{i:02d}'
            if key in self.inputs and self.inputs[key]:
                midpoint = self.inputs[key]
                zone_config = self.config.ZONE_WEIGHTS.get(key, {})
                # Options use tighter m5 ATR
                atr_half = atr_values.get('m5', atr_values['m15'] / 2) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.5),
                    'con_type': 'options_level'
                }

    def _add_camarilla_zones(self, atr_values: Dict):
        """Add Camarilla pivot zones (use pre-calculated values from bar_data)"""
        cam_keys = [
            # Daily
            'd1_s6', 'd1_s4', 'd1_s3', 'd1_r3', 'd1_r4', 'd1_r6',
            # Weekly
            'w1_s6', 'w1_s4', 'w1_s3', 'w1_r3', 'w1_r4', 'w1_r6',
            # Monthly
            'm1_s6', 'm1_s4', 'm1_s3', 'm1_r3', 'm1_r4', 'm1_r6'
        ]
        
        for key in cam_keys:
            if key in self.inputs and self.inputs[key]:
                midpoint = self.inputs[key]
                zone_config = self.config.CAM_WEIGHTS.get(key, {})
                # Camarilla uses tight m5 ATR
                atr_half = atr_values.get('m5', atr_values['m15'] / 2) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', 'daily_cam')
                }

    def _add_market_structure_zones(self, atr_values: Dict):
        """Add market structure levels from market_overview"""
        ms_keys = ['d1_s', 'd1_w', 'h4_s', 'h4_w', 'h1_s', 'h1_w', 'm15_s', 'm15_w']
        
        for key in ms_keys:
            # Market structure comes from market_structure dict, not inputs
            if key in self.market_structure and self.market_structure[key]:
                midpoint = self.market_structure[key]
                zone_config = self.config.ZONE_WEIGHTS.get(key, {})
                # Market structure uses tight m5 ATR
                atr_half = atr_values.get('m5', atr_values['m15'] / 2) / 2
                
                self.zones_data[key] = {
                    'midpoint': midpoint,
                    'high': midpoint + atr_half,
                    'low': midpoint - atr_half,
                    'weight': zone_config.get('weight', 1.0),
                    'con_type': zone_config.get('con_type', 'market_structure_daily')
                }

    def _process_hvn_pocs(self):
        """Process each HVN POC and calculate confluence"""
        
        m15_atr = self.inputs.get('m15_atr', 0) or 1.0
        
        # Process hvn_poc1 through hvn_poc10
        for i in range(1, 11):
            poc_key = f'hvn_poc{i}'
            poc_value = self.inputs.get(poc_key)
            
            if poc_value is None or poc_value == 0:
                continue
            
            # Create zone around POC
            zone_high = poc_value + (m15_atr / 2)
            zone_low = poc_value - (m15_atr / 2)
            
            # Calculate confluence
            result = self._calculate_zone_confluence(poc_key, poc_value, zone_high, zone_low)
            self.zone_results.append(result)
            
            print(f"    {poc_key}: POC={poc_value:.2f}, Score={result['Score']:.1f}, Rank={result['Rank']}")

    def _calculate_zone_confluence(self, poc_id: str, poc_price: float, 
                                    zone_high: float, zone_low: float) -> Dict:
        """
        Calculate confluence for one HVN POC zone
        
        Args:
            poc_id: ID like 'hvn_poc1'
            poc_price: The POC price level
            zone_high: Upper zone boundary
            zone_low: Lower zone boundary
            
        Returns:
            Dict with zone data and scores
        """
        # Initialize bucket tracking
        bucket_scores = {bucket: 0 for bucket in self.config.BUCKET_WEIGHTS.keys()}
        overlapping_zones = []
        overlapping_names = []
        
        # Check overlap with all confluence zones
        for zone_id, zone_data in self.zones_data.items():
            zone_h = zone_data['high']
            zone_l = zone_data['low']
            
            # Check for ANY overlap
            if zone_low < zone_h and zone_high > zone_l:
                weight = zone_data['weight']
                con_type = zone_data['con_type']
                
                overlapping_zones.append(zone_id)
                overlapping_names.append(self._format_zone_name(zone_id))
                
                # Track MAX weight per bucket (no stacking)
                if con_type in bucket_scores:
                    bucket_scores[con_type] = max(bucket_scores[con_type], weight)
        
        # Calculate scores
        bucket_total = sum(bucket_scores.values())
        base_score = self.config.EPOCH_POC_BASE_WEIGHTS.get(poc_id, 0)
        total_score = bucket_total + base_score
        
        # Assign rank
        rank = self._assign_rank(total_score)
        
        # Create confluences summary
        if overlapping_names:
            names_to_show = overlapping_names[:6]
            if len(overlapping_names) > 6:
                names_to_show.append(f'+{len(overlapping_names) - 6} more')
            confluences = ', '.join(names_to_show)
        else:
            confluences = 'None'
        
        return {
            'Zone_ID': poc_id,
            'HVN_POC': f"{poc_price:.2f}",
            'Zone_High': f"{zone_high:.2f}",
            'Zone_Low': f"{zone_low:.2f}",
            'Overlaps': len(overlapping_zones),
            'Score': round(total_score, 2),
            'Rank': rank,
            'Confluences': confluences
        }

    def _assign_rank(self, score: float) -> str:
        """Assign L1-L5 rank based on score"""
        thresholds = self.config.RANKING_SCORE_THRESHOLDS
        
        if score >= thresholds['L5']:
            return 'L5'
        elif score >= thresholds['L4']:
            return 'L4'
        elif score >= thresholds['L3']:
            return 'L3'
        elif score >= thresholds['L2']:
            return 'L2'
        else:
            return 'L1'

    def _format_zone_name(self, zone_id: str) -> str:
        """Convert zone IDs to readable names"""
        return self.config.ZONE_NAME_MAP.get(zone_id, zone_id)
