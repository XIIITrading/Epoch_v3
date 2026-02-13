from dataclasses import dataclass
from typing import Optional

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