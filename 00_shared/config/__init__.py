"""
Configuration module for Epoch Trading System.

Provides centralized access to:
- API credentials (Polygon, Supabase, Anthropic)
- System configuration
- Market configuration
"""

from .credentials import (
    POLYGON_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    ANTHROPIC_API_KEY,
)
from .epoch_config import EpochConfig
from .market_config import MarketConfig

__all__ = [
    "POLYGON_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "ANTHROPIC_API_KEY",
    "EpochConfig",
    "MarketConfig",
]
