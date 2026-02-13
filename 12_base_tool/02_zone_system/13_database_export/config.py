"""
Epoch Trading System - Database Export Configuration
Supabase connection settings and paths.

v3.0.0: Removed entry_events and exit_events worksheets (deprecated)
        Added trade_bars worksheet
"""

import os
from pathlib import Path

# =============================================================================
# Supabase Configuration
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

# Connection string for psycopg2
DATABASE_URL = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DATABASE}"

# Connection dict for psycopg2.connect()
DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# =============================================================================
# File Paths
# =============================================================================
# Excel source file
EXCEL_PATH = Path(r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm")

# Module directory
MODULE_DIR = Path(__file__).parent

# Schema directory
SCHEMA_DIR = MODULE_DIR / "schema"

# =============================================================================
# Worksheet Names
# =============================================================================
WORKSHEETS = {
    "market_overview": "market_overview",
    "bar_data": "bar_data",
    "raw_zones": "raw_zones",
    "zone_results": "zone_results",
    "analysis": "Analysis",
    "backtest": "backtest",
    "trade_bars": "trade_bars",
    "optimal_trade": "optimal_trade",
    "options_analysis": "options_analysis"
}

# =============================================================================
# Export Version
# =============================================================================
EXPORT_VERSION = "3.0.0"
