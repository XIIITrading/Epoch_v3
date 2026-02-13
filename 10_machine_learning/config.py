"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Configuration
XIII Trading LLC
================================================================================

Central configuration for the Machine Learning module.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict

# =============================================================================
# DATABASE CONFIGURATION
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
    "sslmode": "require",
}

# =============================================================================
# PATHS
# =============================================================================

# Module root
MODULE_ROOT = Path(__file__).parent

# Export directories
EXPORTS_DIR = MODULE_ROOT / "exports"
DAILY_EXPORTS_DIR = EXPORTS_DIR / "daily"
WEEKLY_EXPORTS_DIR = EXPORTS_DIR / "weekly"
REFERENCE_DIR = EXPORTS_DIR / "reference"

# State directory
STATE_DIR = MODULE_ROOT / "state"
CHANGELOG_DIR = STATE_DIR / "changelog"

# State JSON files (machine-readable, source of truth for state)
SYSTEM_STATE_JSON = STATE_DIR / "system_state.json"
HYPOTHESIS_TRACKER_JSON = STATE_DIR / "hypothesis_tracker.json"
PENDING_EDGES_JSON = STATE_DIR / "pending_edges.json"

# Analysis archive
ANALYSIS_DIR = MODULE_ROOT / "analysis"
EDGE_AUDITS_DIR = ANALYSIS_DIR / "edge_audits"
HYPOTHESES_DIR = ANALYSIS_DIR / "hypotheses"
PATTERNS_DIR = ANALYSIS_DIR / "patterns"

# Prompts
PROMPTS_DIR = MODULE_ROOT / "prompts"

# SQL
SQL_DIR = MODULE_ROOT / "sql"

# Docs
DOCS_DIR = MODULE_ROOT / "docs"

# =============================================================================
# CANONICAL WIN CONDITION
# =============================================================================

# This is the SINGLE SOURCE OF TRUTH for win/loss classification
CANONICAL_OUTCOME = {
    "table": "trades_m5_r_win",
    "stop_type": "m5_atr",
    "atr_period": 14,
    "atr_multiplier": 1.1,
    "trigger": "close",  # Close-based, not price-based
    "win_field": "is_winner",
    "outcome_field": "outcome",  # WIN/LOSS
}

# =============================================================================
# STATISTICAL THRESHOLDS
# =============================================================================

EDGE_CRITERIA = {
    "p_value_threshold": 0.05,       # Statistical significance
    "effect_size_threshold": 3.0,    # Practical significance (percentage points)
    "min_sample_medium": 30,         # MEDIUM confidence
    "min_sample_high": 100,          # HIGH confidence
}

# =============================================================================
# INDICATOR THRESHOLDS
# =============================================================================

CANDLE_RANGE = {
    "absorption_threshold": 0.12,    # Below = SKIP
    "normal_threshold": 0.15,        # Above = TRADEABLE
    "high_threshold": 0.20,          # Above = STRONG
}

VOLUME_ROC = {
    "baseline_period": 20,
    "elevated_threshold": 30,        # Momentum present
    "high_threshold": 50,            # Strong momentum
}

CVD_SLOPE = {
    "window": 15,
    "rising_threshold": 0.1,
    "falling_threshold": -0.1,
}

SMA_CONFIG = {
    "fast_period": 9,
    "slow_period": 21,
    "wide_spread_threshold": 0.15,
    "momentum_lookback": 10,
    "widening_threshold": 1.1,
    "narrowing_threshold": 0.9,
}

VOLUME_DELTA = {
    "rolling_period": 5,
    "magnitude_threshold": 100000,
}

HEALTH_SCORE = {
    "max_score": 10,
    "strong_threshold": 8,
    "moderate_threshold": 6,
    "weak_threshold": 4,
    # Factor weights (all 1.0 for equal weighting)
    "weights": {
        "h4_structure": 1.0,
        "h1_structure": 1.0,
        "m15_structure": 1.0,
        "m5_structure": 1.0,
        "vol_roc": 1.0,
        "vol_delta": 1.0,
        "cvd_slope": 1.0,
        "sma_alignment": 1.0,
        "sma_momentum": 1.0,
        "vwap_position": 1.0,
    }
}

# =============================================================================
# ENTRY MODELS
# =============================================================================

ENTRY_MODELS = {
    "EPCH1": {"type": "continuation", "zone": "primary"},
    "EPCH2": {"type": "rejection", "zone": "primary"},
    "EPCH3": {"type": "continuation", "zone": "secondary"},
    "EPCH4": {"type": "rejection", "zone": "secondary"},
}

CONTINUATION_MODELS = ["EPCH1", "EPCH3"]
REJECTION_MODELS = ["EPCH2", "EPCH4"]
PRIMARY_MODELS = ["EPCH1", "EPCH2"]
SECONDARY_MODELS = ["EPCH3", "EPCH4"]

# =============================================================================
# STOP TYPES
# =============================================================================

STOP_TYPES = {
    "zone_buffer": {"trigger": "price", "description": "Zone edge + 5% buffer"},
    "prior_m1": {"trigger": "price", "description": "Prior M1 bar high/low"},
    "prior_m5": {"trigger": "price", "description": "Prior M5 bar high/low"},
    "m5_atr": {"trigger": "close", "description": "M5 ATR(14) x 1.1 (CANONICAL)"},
    "m15_atr": {"trigger": "close", "description": "M15 ATR(14) x 1.1"},
    "fractal": {"trigger": "price", "description": "M5 fractal high/low"},
}

DEFAULT_STOP_TYPE = "m5_atr"

# =============================================================================
# EXPORT CONFIGURATION
# =============================================================================

EXPORT_CONFIG = {
    "date_format": "%Y%m%d",
    "timestamp_format": "%Y-%m-%d %H:%M:%S",
    "json_indent": 2,
    "max_trades_per_file": 10000,
}

# =============================================================================
# VALIDATED EDGES (Updated from edge testing)
# =============================================================================

VALIDATED_EDGES = [
    {
        "name": "H1 Structure NEUTRAL",
        "indicator": "h1_structure",
        "condition": "NEUTRAL",
        "effect_size_pp": 36.0,
        "confidence": "HIGH",
        "action": "TRADE when H1 = NEUTRAL",
        "validated_date": "2026-01-31",
    },
    {
        "name": "Absorption Zone Skip",
        "indicator": "candle_range_pct",
        "condition": "< 0.12%",
        "effect_size_pp": -17.0,
        "confidence": "HIGH",
        "action": "SKIP - do not trade",
        "validated_date": "2026-01-31",
    },
    {
        "name": "Volume Delta Paradox",
        "indicator": "vol_delta_alignment",
        "condition": "MISALIGNED",
        "effect_size_pp": 13.0,  # Average of 5-21pp range
        "confidence": "MEDIUM",
        "action": "Trade against order flow",
        "validated_date": "2026-01-31",
    },
]

# =============================================================================
# EDGE DEFINITIONS (SQL queries for validation)
# =============================================================================
# Each validated edge needs a group query and baseline query.
# Group query: trades matching the edge condition
# Baseline query: all trades (for comparison)
# Both return: (wins, total)

EDGE_DEFINITIONS = {
    "H1 Structure NEUTRAL": {
        "group_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.h1_structure = 'NEUTRAL'
            AND m.date >= %s AND m.date <= %s
        """,
        "baseline_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.date >= %s AND m.date <= %s
        """,
    },
    "Absorption Zone Skip": {
        # NOTE: candle_range_pct not in entry_indicators.
        # Using stop_distance_pct < 0.12 as proxy.
        # This edge needs re-evaluation — stored effect may not match.
        "group_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.stop_distance_pct < 0.12
            AND m.date >= %s AND m.date <= %s
        """,
        "baseline_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.date >= %s AND m.date <= %s
        """,
    },
    "Volume Delta Paradox": {
        # Misaligned = vol_delta sign opposite to trade direction
        # LONG + negative delta, or SHORT + positive delta
        "group_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE (
                (m.direction = 'LONG' AND ei.vol_delta < 0)
                OR (m.direction = 'SHORT' AND ei.vol_delta > 0)
            )
            AND m.date >= %s AND m.date <= %s
        """,
        "baseline_query": """
            SELECT
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.vol_delta IS NOT NULL
            AND m.date >= %s AND m.date <= %s
        """,
    },
}

# =============================================================================
# INDICATOR SCAN QUERIES (for hypothesis generation)
# =============================================================================
# Each query returns distinct indicator values with win/loss counts.
# Used by hypothesis_engine to discover new candidate edges.

INDICATOR_SCAN_QUERIES = {
    "h1_structure": {
        "description": "H1 timeframe market structure",
        "query": """
            SELECT
                ei.h1_structure as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.h1_structure IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.h1_structure
        """,
    },
    "h4_structure": {
        "description": "H4 timeframe market structure",
        "query": """
            SELECT
                ei.h4_structure as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.h4_structure IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.h4_structure
        """,
    },
    "m15_structure": {
        "description": "M15 timeframe market structure",
        "query": """
            SELECT
                ei.m15_structure as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.m15_structure IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.m15_structure
        """,
    },
    "m5_structure": {
        "description": "M5 timeframe market structure",
        "query": """
            SELECT
                ei.m5_structure as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.m5_structure IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.m5_structure
        """,
    },
    "health_tier": {
        "description": "Continuation Score tier (STRONG/MODERATE/WEAK/CRITICAL) -- based on health_score field",
        "query": """
            SELECT
                CASE
                    WHEN ei.health_score >= 8 THEN 'STRONG (8-10)'
                    WHEN ei.health_score >= 6 THEN 'MODERATE (6-7)'
                    WHEN ei.health_score >= 4 THEN 'WEAK (4-5)'
                    ELSE 'CRITICAL (0-3)'
                END as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.health_score IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY indicator_value
        """,
    },
    "model": {
        "description": "Entry model (EPCH1-4)",
        "query": """
            SELECT
                m.model as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.date >= %s AND m.date <= %s
            GROUP BY m.model
        """,
    },
    "direction": {
        "description": "Trade direction (LONG/SHORT)",
        "query": """
            SELECT
                m.direction as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.date >= %s AND m.date <= %s
            GROUP BY m.direction
        """,
    },
    "sma_momentum_label": {
        "description": "SMA momentum classification",
        "query": """
            SELECT
                ei.sma_momentum_label as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.sma_momentum_label IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.sma_momentum_label
        """,
    },
    "vwap_position": {
        "description": "Price position relative to VWAP",
        "query": """
            SELECT
                ei.vwap_position as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.vwap_position IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.vwap_position
        """,
    },
    "sma_alignment": {
        "description": "SMA9/SMA21 alignment classification",
        "query": """
            SELECT
                ei.sma_alignment as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.sma_alignment IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY ei.sma_alignment
        """,
    },
    "stop_distance_bucket": {
        "description": "Stop distance as % of price (proxy for zone tightness)",
        "query": """
            SELECT
                CASE
                    WHEN m.stop_distance_pct < 0.12 THEN 'TIGHT (<0.12%%)'
                    WHEN m.stop_distance_pct < 0.25 THEN 'NORMAL (0.12-0.25%%)'
                    WHEN m.stop_distance_pct < 0.50 THEN 'WIDE (0.25-0.50%%)'
                    ELSE 'VERY_WIDE (>=0.50%%)'
                END as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.date >= %s AND m.date <= %s
            GROUP BY indicator_value
        """,
    },
    "zone_type": {
        "description": "Zone classification type",
        "query": """
            SELECT
                m.zone_type as indicator_value,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win m
            WHERE m.zone_type IS NOT NULL
            AND m.date >= %s AND m.date <= %s
            GROUP BY m.zone_type
        """,
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_daily_export_path(date: datetime = None, file_type: str = "trades") -> Path:
    """Get path for daily export file."""
    if date is None:
        date = datetime.now()
    date_str = date.strftime(EXPORT_CONFIG["date_format"])
    return DAILY_EXPORTS_DIR / f"{file_type}_{date_str}.json"


def get_weekly_export_path(file_type: str = "edge_trend_report") -> Path:
    """Get path for weekly export file."""
    return WEEKLY_EXPORTS_DIR / f"{file_type}.md"


def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DAILY_EXPORTS_DIR, WEEKLY_EXPORTS_DIR, REFERENCE_DIR,
        STATE_DIR, CHANGELOG_DIR,
        EDGE_AUDITS_DIR, HYPOTHESES_DIR, PATTERNS_DIR,
        PROMPTS_DIR, SQL_DIR, DOCS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
