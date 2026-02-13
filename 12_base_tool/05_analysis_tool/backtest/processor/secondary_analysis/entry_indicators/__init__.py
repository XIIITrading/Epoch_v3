"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Entry Indicators Package
XIII Trading LLC
================================================================================

This package calculates indicator snapshots at trade entry time for analysis.
It supports CALC-005 through CALC-008 (Indicator Analysis) in the
12_indicator_analysis Streamlit application.

Key Concepts:
    ENTRY INDICATORS:
        Snapshot of all relevant indicators at the M1 bar immediately prior
        to trade entry. Includes structure, volume, and price factors.

    HEALTH SCORE:
        Composite score (0-10) representing alignment of all factors with
        the trade direction. Higher score = more favorable conditions.

Usage:
    # CLI Usage
    python runner.py                    # Full batch run
    python runner.py --dry-run          # Test without saving
    python runner.py --limit 50         # Process 50 trades
    python runner.py --schema           # Create database table

    # Programmatic Usage
    from entry_indicators import EntryIndicatorsCalculator, M1DataProvider

    provider = M1DataProvider()
    calculator = EntryIndicatorsCalculator(m1_provider=provider)
    result = calculator.calculate(trade_dict)

Components:
    config.py           - Configuration (database, API, parameters)
    m1_data.py          - M1 bar data access (database + API fallback)
    indicators.py       - Indicator calculations (SMA, VWAP, Volume, CVD)
    structure.py        - Market structure detection (fractals, BOS/ChoCH)
    calculator.py       - Core calculator class
    populator.py        - Batch database population
    runner.py           - CLI runner script
    schema/             - SQL schema for entry_indicators table

Version: 1.0.0
================================================================================
"""

from .config import (
    DB_CONFIG,
    POLYGON_API_KEY,
    SOURCE_TABLE,
    TARGET_TABLE,
    M1_BARS_TABLE,
    HEALTH_BUCKETS,
    STRUCTURE_LABELS
)

from .m1_data import (
    M1DataProvider,
    aggregate_to_m5
)

from .indicators import (
    SMAResult,
    SMAMomentumResult,
    VWAPResult,
    VolumeROCResult,
    VolumeDeltaResult,
    CVDResult,
    calculate_sma,
    calculate_sma_momentum,
    calculate_vwap,
    calculate_volume_roc,
    calculate_volume_delta,
    calculate_cvd_slope
)

from .structure import (
    StructureResult,
    MarketStructureCalculator,
    HTFBarFetcher,
    StructureAnalyzer
)

from .calculator import (
    EntryIndicatorsResult,
    EntryIndicatorsCalculator,
    calculate_health_score,
    get_health_label
)

from .populator import (
    EntryIndicatorsPopulator
)


__version__ = "1.0.0"
__author__ = "XIII Trading LLC"

__all__ = [
    # Config
    'DB_CONFIG',
    'POLYGON_API_KEY',
    'SOURCE_TABLE',
    'TARGET_TABLE',
    'M1_BARS_TABLE',
    'HEALTH_BUCKETS',
    'STRUCTURE_LABELS',

    # M1 Data
    'M1DataProvider',
    'aggregate_to_m5',

    # Indicators
    'SMAResult',
    'SMAMomentumResult',
    'VWAPResult',
    'VolumeROCResult',
    'VolumeDeltaResult',
    'CVDResult',
    'calculate_sma',
    'calculate_sma_momentum',
    'calculate_vwap',
    'calculate_volume_roc',
    'calculate_volume_delta',
    'calculate_cvd_slope',

    # Structure
    'StructureResult',
    'MarketStructureCalculator',
    'HTFBarFetcher',
    'StructureAnalyzer',

    # Calculator
    'EntryIndicatorsResult',
    'EntryIndicatorsCalculator',
    'calculate_health_score',
    'get_health_label',

    # Populator
    'EntryIndicatorsPopulator',
]
