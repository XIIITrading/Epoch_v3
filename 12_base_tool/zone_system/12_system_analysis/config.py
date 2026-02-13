"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Configuration Settings
XIII Trading LLC
================================================================================

Central configuration for the Indicator Analysis module.
Contains database settings, calculation parameters, and UI configuration.

================================================================================
"""

from pathlib import Path
from credentials import (
    SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DATABASE,
    SUPABASE_USER, SUPABASE_PASSWORD, POLYGON_API_KEY
)

# =============================================================================
# Paths
# =============================================================================
MODULE_DIR = Path(__file__).parent
BASE_DIR = MODULE_DIR.parent.parent  # C:\XIIITradingSystems\Epoch

# =============================================================================
# Database Configuration
# =============================================================================
DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# =============================================================================
# Polygon API Configuration
# =============================================================================
POLYGON_CONFIG = {
    "api_key": POLYGON_API_KEY,
    "delay": 0.25,
    "retries": 3,
    "retry_delay": 2.0
}

# =============================================================================
# Entry Model Definitions
# =============================================================================
ENTRY_MODELS = {
    "EPCH1": {"type": "continuation", "zone": "primary"},
    "EPCH2": {"type": "rejection", "zone": "primary"},
    "EPCH3": {"type": "continuation", "zone": "secondary"},
    "EPCH4": {"type": "rejection", "zone": "secondary"},
}

CONTINUATION_MODELS = ["EPCH1", "EPCH3"]
REJECTION_MODELS = ["EPCH2", "EPCH4"]

# =============================================================================
# Calculation Parameters
# =============================================================================

SMA_CONFIG = {
    "fast_period": 9,
    "slow_period": 21,
    "momentum_lookback": 10,
    "widening_threshold": 1.1,
    "narrowing_threshold": 0.9,
}

VOLUME_ROC_CONFIG = {
    "baseline_period": 20,
    "above_avg_threshold": 20,
    "below_avg_threshold": -20,
}

VOLUME_DELTA_CONFIG = {
    "rolling_period": 5,
}

CVD_CONFIG = {
    "window": 15,
    "rising_threshold": 0.1,
    "falling_threshold": -0.1,
}

STRUCTURE_CONFIG = {
    "fractal_length": 5,
}

# =============================================================================
# Health Score Configuration
# =============================================================================
HEALTH_CONFIG = {
    "max_score": 10,
    "labels": {
        "strong": {"min": 8, "max": 10, "label": "STRONG"},
        "moderate": {"min": 6, "max": 7, "label": "MODERATE"},
        "weak": {"min": 4, "max": 5, "label": "WEAK"},
        "critical": {"min": 0, "max": 3, "label": "CRITICAL"},
    },
    "weights": {
        "h4_structure": 1.0,
        "h1_structure": 1.0,
        "m15_structure": 1.0,
        "m5_structure": 1.0,
        "volume_roc": 1.0,
        "volume_delta": 1.0,
        "cvd": 1.0,
        "sma_alignment": 1.0,
        "sma_momentum": 1.0,
        "vwap": 1.0,
    }
}

# =============================================================================
# Analysis Configuration
# =============================================================================
ANALYSIS_CONFIG = {
    "event_types": ["ENTRY", "MFE", "MAE", "EXIT"],
    "directions": ["LONG", "SHORT"],
    "outcomes": ["WIN", "LOSS"],
    "default_limit": 10000,
}

# =============================================================================
# Streamlit UI Configuration
# =============================================================================
STREAMLIT_CONFIG = {
    "port": 8502,
    "page_title": "Epoch Indicator Analysis",
    "page_icon": "📊",
    "layout": "wide",
}

CHART_CONFIG = {
    "background_color": "#1a1a2e",
    "paper_color": "#1a1a2e",
    "grid_color": "#2a2a4e",
    "text_color": "#e0e0e0",
    "text_muted": "#888888",
    "win_color": "#26a69a",
    "loss_color": "#ef5350",
    "continuation_color": "#2196F3",
    "rejection_color": "#FF9800",
    "long_color": "#00C853",
    "short_color": "#FF1744",
    "strong_color": "#00C853",
    "moderate_color": "#FFC107",
    "weak_color": "#FF9800",
    "critical_color": "#FF1744",
    "default_height": 400,
}

DATE_FILTER_CONFIG = {
    "default_range": "all",
    "options": {
        "all": "All Data",
        "year": "This Year",
        "month": "This Month",
        "week": "This Week",
        "day": "Today",
    }
}

DISPLAY_TIMEZONE = "America/New_York"

# =============================================================================
# INDICATOR ANALYSIS CONFIGURATION (CALC-005+)
# =============================================================================

INDICATOR_ANALYSIS_CONFIG = {
    # Health Score Buckets for CALC-005
    "health_buckets": {
        "CRITICAL": (0, 3),
        "WEAK": (4, 5),
        "MODERATE": (6, 7),
        "STRONG": (8, 10)
    },

    # Minimum trades for statistical relevance
    "min_trades_for_analysis": 30,

    # Confidence interval for charts
    "confidence_interval": 0.95,

    # Individual indicator thresholds (for CALC-006)
    "indicator_thresholds": {
        "vol_roc": 20.0,           # Above average threshold
        "cvd_slope_bullish": 0.1,  # Rising threshold
        "cvd_slope_bearish": -0.1, # Falling threshold
        "sma_widening": 1.1,       # Momentum ratio threshold
    },

    # Time-to-MFE buckets for CALC-008 (in minutes)
    "time_to_mfe_buckets": {
        "FAST": (0, 5),      # Within 1 M5 bar
        "QUICK": (5, 15),    # Within 3 M5 bars
        "NORMAL": (15, 30),  # Within 6 M5 bars
        "SLOW": (30, 999)    # Beyond 30 minutes
    }
}

# Health Score Factor Groups (for CALC-006 grouping)
HEALTH_FACTOR_GROUPS = {
    "structure": ["h4_structure", "h1_structure", "m15_structure", "m5_structure"],
    "volume": ["vol_roc", "vol_delta", "cvd_slope"],
    "price": ["sma_alignment", "sma_momentum", "vwap_position"]
}

# Model Type Classification
MODEL_TYPES = {
    "continuation": ["EPCH1", "EPCH3"],
    "rejection": ["EPCH2", "EPCH4"]
}


def get_model_type(model: str) -> str:
    """Return 'continuation' or 'rejection' based on model."""
    if model in MODEL_TYPES["continuation"]:
        return "continuation"
    elif model in MODEL_TYPES["rejection"]:
        return "rejection"
    return "unknown"


# =============================================================================
# WIN CONDITION CONFIGURATION
# =============================================================================
# All win/loss calculations use stop-based outcomes from the stop_analysis table.
# Win = MFE reached (>=1R) before stop hit
# Loss = Stop hit before reaching 1R
# Partial = Stop hit after some MFE but < 1R

WIN_CONDITION_CONFIG = {
    # Default stop type for all indicator analysis calculations
    "default_stop_type": "zone_buffer",

    # Available stop types with display names
    "stop_types": {
        "zone_buffer": "Zone + 5% Buffer",
        "prior_m1": "Prior M1 H/L",
        "prior_m5": "Prior M5 H/L",
        "m5_atr": "M5 ATR (Close)",
        "m15_atr": "M15 ATR (Close)",
        "fractal": "M5 Fractal H/L"
    },

    # Short display names for compact UI elements
    "stop_types_short": {
        "zone_buffer": "Zone+5%",
        "prior_m1": "Prior M1",
        "prior_m5": "Prior M5",
        "m5_atr": "M5 ATR",
        "m15_atr": "M15 ATR",
        "fractal": "Fractal"
    },

    # Order for display in dropdowns
    "stop_type_order": [
        "zone_buffer",
        "prior_m1",
        "prior_m5",
        "m5_atr",
        "m15_atr",
        "fractal"
    ]
}
