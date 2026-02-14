"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 05: SYSTEM ANALYSIS v2.0
Configuration
XIII Trading LLC
================================================================================
"""
from pathlib import Path

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
MODULE_ROOT = Path(__file__).parent
ML_STATE_DIR = MODULE_ROOT.parent / "10_machine_learning" / "state"

# =============================================================================
# DATA TABLES (from 03_backtest pipeline)
# =============================================================================
TABLE_TRADES = "trades_m5_r_win_2"
TABLE_M1_ATR = "m1_atr_stop_2"
TABLE_M5_ATR = "m5_atr_stop_2"
TABLE_INDICATORS = "m1_indicator_bars_2"

# =============================================================================
# MODELS & LABELS
# =============================================================================
ENTRY_MODELS = {
    "EPCH1": "Continuation (Primary)",
    "EPCH2": "Rejection (Primary)",
    "EPCH3": "Continuation (Secondary)",
    "EPCH4": "Rejection (Secondary)",
}

DIRECTIONS = ["LONG", "SHORT"]
ZONE_TYPES = ["PRIMARY", "SECONDARY"]
