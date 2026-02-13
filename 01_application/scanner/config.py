"""
Scanner Configuration
Epoch Trading System v2.0 - XIII Trading LLC

Centralized configuration for market scanner module.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import POLYGON_API_KEY


@dataclass
class ScannerConfig:
    """Global configuration for market scanner."""

    # Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    TICKER_DATA_DIR: Path = BASE_DIR / "data" / "ticker_lists"

    # API Configuration
    POLYGON_API_KEY: str = POLYGON_API_KEY

    # Scanner Settings
    DEFAULT_PARALLEL_WORKERS: int = 10
    DEFAULT_LOOKBACK_DAYS: int = 14
    UPDATE_FREQUENCY_DAYS: int = 90

    # Market Hours (UTC)
    PREMARKET_START_HOUR: int = 4
    PREMARKET_START_MINUTE: int = 0
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 30

    def __post_init__(self):
        """Create directories if they don't exist."""
        self.DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.TICKER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.POLYGON_API_KEY:
            raise ValueError("POLYGON_API_KEY not set")
        return True


# Global instance
scanner_config = ScannerConfig()
