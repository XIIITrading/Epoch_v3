"""
Scanner Filters
Epoch Trading System v2.0 - XIII Trading LLC

Filter classes for two-phase scanning.
"""
from dataclasses import dataclass


@dataclass
class FilterPhase:
    """Hard filters that remove tickers from consideration."""
    min_atr: float = 2.00  # $2.00 minimum ATR
    min_price: float = 10.00  # $10 minimum price
    min_gap_percent: float = 2.0  # 2% minimum gap (absolute value)


@dataclass
class RankingWeights:
    """Weights for ranking metrics (all set to 1 initially)."""
    overnight_volume: float = 1.0
    relative_overnight_volume: float = 1.0
    relative_volume: float = 1.0
    gap_magnitude: float = 1.0
    short_interest: float = 1.0


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


def get_filter_profile(name: str) -> FilterProfile:
    """Get filter profile by name."""
    profiles = {
        'strict': FilterProfiles.STRICT,
        'relaxed': FilterProfiles.RELAXED,
        'momentum': FilterProfiles.MOMENTUM
    }

    if name not in profiles:
        raise ValueError(f"Unknown profile: {name}. Available: {list(profiles.keys())}")

    return profiles[name]
