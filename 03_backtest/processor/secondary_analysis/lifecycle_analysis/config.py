"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Trade Lifecycle Analysis - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for trade lifecycle signal extraction.
Analyzes M1 indicator bars before, at, and after trade entries to produce
derivative signals (INCREASING, DECREASING, FLIP, etc.) for each indicator.

Version: 1.0.0
================================================================================
"""

from pathlib import Path

# =============================================================================
# MODULE PATHS
# =============================================================================
MODULE_DIR = Path(__file__).parent
SCHEMA_DIR = MODULE_DIR / "schema"

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
M1_BARS_TABLE = "m1_indicator_bars"
M5_TRADE_BARS_TABLE = "m5_trade_bars"
TRADES_TABLE = "trades_m5_r_win"
TARGET_TABLE = "trade_lifecycle_signals"

# =============================================================================
# LIFECYCLE WINDOWS (in M1 bars = minutes)
# =============================================================================
RAMPUP_BARS = 30        # 30 M1 bars before entry (30 minutes)
POST_ENTRY_BARS = 30    # 30 M1 bars after entry (30 minutes)

# =============================================================================
# TREND DETECTION
# =============================================================================
TREND_WINDOW = 5         # Rolling window for direction signals

# =============================================================================
# NUMERIC INDICATORS TO ANALYZE
# =============================================================================
# These are the columns from m1_indicator_bars with numeric values
# that we compute trend/level/flip signals for.
M1_NUMERIC_INDICATORS = [
    "candle_range_pct",
    "vol_delta",
    "vol_roc",
    "cvd_slope",
    "sma_spread",
    "sma_momentum_ratio",
    "health_score",
    "long_score",
    "short_score",
]

# =============================================================================
# CATEGORICAL INDICATORS TO SNAPSHOT
# =============================================================================
# These are captured at entry for context.
M1_CATEGORICAL_INDICATORS = [
    "sma_momentum_label",
    "m1_structure",
    "m5_structure",
    "m15_structure",
    "h1_structure",
    "h4_structure",
]

# =============================================================================
# LEVEL CLASSIFICATION THRESHOLDS
# =============================================================================
LEVEL_THRESHOLDS = {
    "candle_range_pct": {
        "COMPRESSED": (None, 0.08),
        "NORMAL": (0.08, 0.15),
        "EXPANDING": (0.15, 0.25),
        "EXPLOSIVE": (0.25, None),
    },
    "vol_roc": {
        "LOW": (None, 10),
        "MODERATE": (10, 50),
        "ELEVATED": (50, 100),
        "EXTREME": (100, None),
    },
    "vol_delta": {
        "STRONG_SELL": (None, -50000),
        "MILD_SELL": (-50000, 0),
        "MILD_BUY": (0, 50000),
        "STRONG_BUY": (50000, None),
    },
    "cvd_slope": {
        "STRONG_FALLING": (None, -0.2),
        "MILD_FALLING": (-0.2, 0),
        "MILD_RISING": (0, 0.2),
        "STRONG_RISING": (0.2, None),
    },
    "health_score": {
        "CRITICAL": (None, 4),
        "WEAK": (4, 6),
        "MODERATE": (6, 8),
        "STRONG": (8, None),
    },
    "long_score": {
        "MINIMAL": (None, 2),
        "LOW": (2, 5),
        "MODERATE": (5, 8),
        "HIGH": (8, None),
    },
    "short_score": {
        "MINIMAL": (None, 2),
        "LOW": (2, 5),
        "MODERATE": (5, 8),
        "HIGH": (8, None),
    },
    "sma_spread": {
        "WIDE_BEAR": (None, -0.15),
        "NARROW_BEAR": (-0.15, 0),
        "NARROW_BULL": (0, 0.15),
        "WIDE_BULL": (0.15, None),
    },
    "sma_momentum_ratio": {
        "NARROWING": (None, -1),
        "FLAT": (-1, 1),
        "WIDENING": (1, 5),
        "STRONG_WIDENING": (5, None),
    },
}

# Indicators that support sign-based flip detection
FLIP_INDICATORS = ["vol_delta", "cvd_slope", "sma_spread"]

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================
BATCH_INSERT_SIZE = 100

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True

# =============================================================================
# VERSION
# =============================================================================
CALCULATION_VERSION = "1.0"
