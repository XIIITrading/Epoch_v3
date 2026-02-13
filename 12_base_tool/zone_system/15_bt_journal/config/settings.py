"""
Epoch Backtest Journal - Configuration Settings
Database connection and paths.
"""

import os
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
MODULE_DIR = BASE_DIR / "02_zone_system" / "12_bt_journal"
REPORTS_DIR = MODULE_DIR / "reports"

# Ensure reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# SUPABASE DATABASE CONFIGURATION
# =============================================================================

SUPABASE_HOST = os.getenv("SUPABASE_HOST", "db.pdbmcskznoaiybdiobje.supabase.co")
SUPABASE_PORT = int(os.getenv("SUPABASE_PORT", 5432))
SUPABASE_DATABASE = os.getenv("SUPABASE_DATABASE", "postgres")
SUPABASE_USER = os.getenv("SUPABASE_USER", "postgres")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "guid-saltation-covet")

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

DATABASE_URL = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DATABASE}"

# =============================================================================
# REPORT SETTINGS
# =============================================================================

REPORT_DPI = 150
REPORT_FIGSIZE = (11, 8.5)  # Letter size landscape

# =============================================================================
# MODEL DEFINITIONS
# =============================================================================

PRIMARY_MODELS = ["EPCH1", "EPCH2"]
SECONDARY_MODELS = ["EPCH3", "EPCH4"]
ALL_MODELS = PRIMARY_MODELS + SECONDARY_MODELS

MODEL_ZONE_MAPPING = {
    "EPCH1": "PRIMARY",
    "EPCH2": "PRIMARY",
    "EPCH3": "SECONDARY",
    "EPCH4": "SECONDARY"
}
