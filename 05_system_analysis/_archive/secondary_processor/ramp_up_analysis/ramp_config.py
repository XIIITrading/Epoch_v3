"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Configuration Settings
XIII Trading LLC
================================================================================

Configurable parameters for ramp-up indicator progression analysis.

================================================================================
"""

# =============================================================================
# STOP ANALYSIS CONFIGURATION
# =============================================================================
# Which stop type to use for outcome/mfe_distance/r_achieved
# Options: zone_buffer, prior_m1, prior_m5, m5_atr, m15_atr, fractal
STOP_TYPE = "m5_atr"

# =============================================================================
# LOOKBACK CONFIGURATION
# =============================================================================
# Number of M1 bars BEFORE entry bar to analyze
# Total bars = LOOKBACK_BARS + 1 (entry bar)
LOOKBACK_BARS = 15

# =============================================================================
# INDICATOR CONFIGURATION
# =============================================================================
# Indicators to include in analysis (from m1_indicator_bars table)
INDICATORS = [
    "candle_range_pct",
    "vol_delta",
    "vol_roc",
    "sma_spread",
    "sma_momentum_ratio",
    "m15_structure",
    "h1_structure",
    "long_score",
    "short_score",
]

# Numeric indicators (for trend/momentum calculations)
NUMERIC_INDICATORS = [
    "candle_range_pct",
    "vol_delta",
    "vol_roc",
    "sma_spread",
    "sma_momentum_ratio",
    "long_score",
    "short_score",
]

# Categorical indicators (structure labels)
CATEGORICAL_INDICATORS = [
    "m15_structure",
    "h1_structure",
]

# =============================================================================
# TREND CALCULATION CONFIGURATION
# =============================================================================
# Linear regression slope threshold (% of indicator range)
# Values below this are classified as FLAT
TREND_THRESHOLD = 0.05  # 5% of range

# =============================================================================
# MOMENTUM CALCULATION CONFIGURATION (First-half vs Second-half)
# =============================================================================
# Percentage change threshold between first and second half averages
# Values below this are classified as STABLE
MOMENTUM_THRESHOLD = 0.10  # 10% change

# How to split bars for momentum calculation
# First half: bars -15 to -8 (8 bars)
# Second half: bars -7 to -1 (7 bars)
MOMENTUM_SPLIT_BAR = -8  # Bars <= this are "first half"

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================
# Directory for CSV exports (relative to this module)
OUTPUT_DIR = "outputs"

# Date format for output filenames
DATE_FORMAT = "%Y%m%d"

# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================
# Batch size for database inserts
BATCH_SIZE = 100

# Minimum bars required for valid analysis
# If a trade has fewer than this many bars before entry, skip it
MIN_BARS_REQUIRED = 10

# =============================================================================
# TREND/MOMENTUM LABELS
# =============================================================================
TREND_LABELS = {
    "rising": "RISING",
    "falling": "FALLING",
    "flat": "FLAT",
}

MOMENTUM_LABELS = {
    "building": "BUILDING",      # Second half > First half
    "fading": "FADING",          # Second half < First half
    "stable": "STABLE",          # Minimal change
}

# =============================================================================
# STRUCTURE CONSISTENCY LABELS
# =============================================================================
# For categorical indicators (structure), we track consistency
STRUCTURE_CONSISTENCY_LABELS = {
    "consistent_bull": "CONSISTENT_BULL",
    "consistent_bear": "CONSISTENT_BEAR",
    "consistent_neutral": "CONSISTENT_NEUTRAL",
    "mixed": "MIXED",
    "flip_to_bull": "FLIP_TO_BULL",
    "flip_to_bear": "FLIP_TO_BEAR",
}
