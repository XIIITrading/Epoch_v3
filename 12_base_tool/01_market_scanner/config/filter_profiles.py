"""
Pre-defined filter profiles for different scanning strategies.
"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class FilterProfile:
    """Container for a set of filter criteria."""
    name: str
    description: str
    min_price: float
    max_price: float
    min_avg_volume: float
    min_premarket_volume: float
    min_premarket_volume_ratio: float
    min_dollar_volume: float
    min_atr: float
    min_atr_percent: float

class FilterProfiles:
    """Pre-defined filter profiles."""
    
    STRICT = FilterProfile(
        name="strict",
        description="Strict criteria for high-quality setups",
        min_price=20.0,
        max_price=300.0,
        min_avg_volume=2_000_000,
        min_premarket_volume=500_000,
        min_premarket_volume_ratio=0.05,
        min_dollar_volume=50_000_000,
        min_atr=2.0,
        min_atr_percent=1.5
    )
    
    RELAXED = FilterProfile(
        name="relaxed",
        description="Relaxed criteria for broader market view",
        min_price=5.0,
        max_price=500.0,
        min_avg_volume=500_000,
        min_premarket_volume=300_000,
        min_premarket_volume_ratio=0.0015,
        min_dollar_volume=1_000_000,
        min_atr=0.5,
        min_atr_percent=0.5
    )
    
    MOMENTUM = FilterProfile(
        name="momentum",
        description="Focus on high momentum stocks",
        min_price=10.0,
        max_price=400.0,
        min_avg_volume=1_000_000,
        min_premarket_volume=400_000,
        min_premarket_volume_ratio=0.10,
        min_dollar_volume=10_000_000,
        min_atr=3.0,
        min_atr_percent=2.0
    )
    
    PENNY_STOCKS = FilterProfile(
        name="penny_stocks",
        description="Low-priced stocks with volume",
        min_price=1.0,
        max_price=10.0,
        min_avg_volume=5_000_000,
        min_premarket_volume=1_000_000,
        min_premarket_volume_ratio=0.05,
        min_dollar_volume=5_000_000,
        min_atr=0.10,
        min_atr_percent=3.0
    )
    
    # Gap scanning profiles
    GAP_UP = FilterProfile(
        name="gap_up",
        description="Stocks gapping up 3% or more",
        min_price=1.0,
        max_price=1000.0,
        min_avg_volume=500_000,
        min_premarket_volume=10_000,
        min_premarket_volume_ratio=0.001,
        min_dollar_volume=500_000,
        min_atr=0.10,
        min_atr_percent=0.5
    )
    
    GAP_DOWN = FilterProfile(
        name="gap_down",
        description="Stocks gapping down 3% or more",
        min_price=1.0,
        max_price=1000.0,
        min_avg_volume=500_000,
        min_premarket_volume=10_000,
        min_premarket_volume_ratio=0.001,
        min_dollar_volume=500_000,
        min_atr=0.10,
        min_atr_percent=0.5
    )
    
    LARGE_GAP = FilterProfile(
        name="large_gap",
        description="Stocks with large gaps (5%+)",
        min_price=2.0,
        max_price=500.0,
        min_avg_volume=1_000_000,
        min_premarket_volume=50_000,
        min_premarket_volume_ratio=0.01,
        min_dollar_volume=2_000_000,
        min_atr=0.20,
        min_atr_percent=1.0
    )

def get_filter_profile(name: str) -> FilterProfile:
    """Get filter profile by name."""
    profiles = {
        'strict': FilterProfiles.STRICT,
        'relaxed': FilterProfiles.RELAXED,
        'momentum': FilterProfiles.MOMENTUM,
        'penny_stocks': FilterProfiles.PENNY_STOCKS,
        'gap_up': FilterProfiles.GAP_UP,
        'gap_down': FilterProfiles.GAP_DOWN,
        'large_gap': FilterProfiles.LARGE_GAP
    }
    
    if name not in profiles:
        raise ValueError(f"Unknown profile: {name}. Available: {list(profiles.keys())}")
    
    return profiles[name]