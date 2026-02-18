"""
Epoch Trading System - Global Configuration
============================================

Central configuration for system-wide settings, paths, and constants.

Usage:
    from shared.config import EpochConfig
    config = EpochConfig()
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class EpochConfig:
    """
    Global configuration for Epoch Trading System.
    """

    # ==========================================================================
    # PATHS
    # ==========================================================================
    BASE_DIR: Path = field(default_factory=lambda: Path(r"C:\XIIITradingSystems\Epoch"))

    @property
    def EXCEL_FILEPATH(self) -> Path:
        return self.BASE_DIR / "epoch_v1.xlsm"

    @property
    def DATA_DIR(self) -> Path:
        return self.BASE_DIR / "data"

    @property
    def CACHE_DIR(self) -> Path:
        return self.BASE_DIR / "cache"

    # ==========================================================================
    # DATA SOURCE
    # ==========================================================================
    # 'supabase' or 'excel' - supabase is default for V2
    DATA_SOURCE: str = "supabase"

    # ==========================================================================
    # API SETTINGS
    # ==========================================================================
    API_RATE_LIMIT_DELAY: float = 0.1  # seconds between calls (unlimited tier)
    API_MAX_RETRIES: int = 3
    API_RETRY_DELAY: float = 1.0

    # ==========================================================================
    # POLYGON TIMEFRAME SETTINGS
    # ==========================================================================
    TIMEFRAMES: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'M1': {'multiplier': 1, 'timespan': 'minute', 'bars_needed': 50},
        'M5': {'multiplier': 5, 'timespan': 'minute', 'bars_needed': 100},
        'M15': {'multiplier': 15, 'timespan': 'minute', 'bars_needed': 100},
        'H1': {'multiplier': 1, 'timespan': 'hour', 'bars_needed': 100},
        'H4': {'multiplier': 4, 'timespan': 'hour', 'bars_needed': 50},
        'D1': {'multiplier': 1, 'timespan': 'day', 'bars_needed': 100},
        'W1': {'multiplier': 1, 'timespan': 'week', 'bars_needed': 52},
    })

    # Lookback periods for data fetching (in days)
    DATA_LOOKBACK: Dict[str, int] = field(default_factory=lambda: {
        'M1': 2,
        'M5': 5,
        'M15': 10,
        'H1': 30,
        'H4': 60,
        'D1': 365,
        'W1': 365,
    })

    # ==========================================================================
    # MARKET STRUCTURE SETTINGS
    # ==========================================================================
    FRACTAL_LENGTH: int = 5  # Bars each side for fractal detection
    STRUCTURE_LABELS: Dict[int, str] = field(default_factory=lambda: {
        1: 'B+',
        -1: 'B-',
        0: 'N'
    })

    # ==========================================================================
    # VOLUME ANALYSIS SETTINGS
    # ==========================================================================
    VOLUME_DELTA_BARS: int = 5       # Rolling window for delta
    VOLUME_ROC_BASELINE: int = 20    # Bars for average volume baseline
    CVD_WINDOW: int = 15             # Bars for CVD trend analysis

    # ==========================================================================
    # CLAUDE AI SETTINGS
    # ==========================================================================
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"  # Fast for live trading
    CLAUDE_MAX_TOKENS: int = 1500

    # ==========================================================================
    # MODEL DEFINITIONS
    # ==========================================================================
    MODELS: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        'EPCH_01': {
            'name': 'Primary Continuation',
            'zone_type': 'primary',
            'trade_type': 'continuation',
            'description': 'Continuation through primary zone in trend direction'
        },
        'EPCH_02': {
            'name': 'Primary Reversal',
            'zone_type': 'primary',
            'trade_type': 'reversal',
            'description': 'Reversal/mean reversion at primary zone'
        },
        'EPCH_03': {
            'name': 'Secondary Continuation',
            'zone_type': 'secondary',
            'trade_type': 'continuation',
            'description': 'Continuation through secondary zone with trend'
        },
        'EPCH_04': {
            'name': 'Secondary Reversal',
            'zone_type': 'secondary',
            'trade_type': 'reversal',
            'description': 'Reversal at secondary zone'
        },
    })

    # ==========================================================================
    # DEBUG SETTINGS
    # ==========================================================================
    VERBOSE: bool = True

    def debug_print(self, message: str):
        """Print debug message if verbose mode is enabled."""
        if self.VERBOSE:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")


# Default instance
config = EpochConfig()
