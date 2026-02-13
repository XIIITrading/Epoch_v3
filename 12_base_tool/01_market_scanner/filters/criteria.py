"""
Filter criteria definitions and management.
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class FilterCriteria:
    """Configurable filter criteria with defaults."""
    min_price: float = 5.0
    max_price: float = 500.0
    min_avg_volume: float = 500_000
    min_premarket_volume: float = 300_000       
    min_premarket_volume_ratio: float = 0.002
    min_dollar_volume: float = 1_000_000          
    min_atr: float = 2.0                    
    min_atr_percent: float = 0.5
    
    # Gap-specific criteria
    min_gap_percent: float = 0.0  # 0 means no gap filter
    gap_direction: str = "both"  # "up", "down", or "both"
    min_market_cap: Optional[float] = None  # For filtering all US equities
    
    def to_dict(self) -> Dict:
        """Convert criteria to dictionary for logging/display."""
        base_dict = {
            'Price Range': f'${self.min_price} - ${self.max_price}',
            'Min Avg Volume': f'{self.min_avg_volume:,.0f} shares',
            'Min PM Volume': f'{self.min_premarket_volume:,.0f} shares',
            'Min PM Volume Ratio': f'{self.min_premarket_volume_ratio:.1%}',
            'Min Dollar Volume': f'${self.min_dollar_volume:,.0f}',
            'Min ATR': f'${self.min_atr}',
            'Min ATR %': f'{self.min_atr_percent}%'
        }
        
        # Add gap criteria if applicable
        if self.min_gap_percent > 0:
            base_dict['Min Gap %'] = f'{self.min_gap_percent}%'
            base_dict['Gap Direction'] = self.gap_direction
            
        if self.min_market_cap:
            base_dict['Min Market Cap'] = f'${self.min_market_cap:,.0f}'
            
        return base_dict
    
    @classmethod
    def from_profile(cls, profile_name: str):
        """Create FilterCriteria from a pre-defined profile."""
        # Import local config
        try:
            from ..config.filter_profiles import get_filter_profile
        except ImportError:
            # Fallback for when running as script
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from config.filter_profiles import get_filter_profile
        
        profile = get_filter_profile(profile_name)
        
        # Gap-specific settings
        gap_settings = {
            'gap_up': {'min_gap_percent': 3.0, 'gap_direction': 'up'},
            'gap_down': {'min_gap_percent': 3.0, 'gap_direction': 'down'},
            'large_gap': {'min_gap_percent': 5.0, 'gap_direction': 'both'},
        }
        
        instance = cls(
            min_price=profile.min_price,
            max_price=profile.max_price,
            min_avg_volume=profile.min_avg_volume,
            min_premarket_volume=profile.min_premarket_volume,
            min_premarket_volume_ratio=profile.min_premarket_volume_ratio,
            min_dollar_volume=profile.min_dollar_volume,
            min_atr=profile.min_atr,
            min_atr_percent=profile.min_atr_percent
        )
        
        # Apply gap-specific settings if applicable
        if profile_name in gap_settings:
            instance.min_gap_percent = gap_settings[profile_name]['min_gap_percent']
            instance.gap_direction = gap_settings[profile_name]['gap_direction']
            # Set market cap filter for gap scans to avoid penny stocks
            instance.min_market_cap = 50_000_000
            
        return instance