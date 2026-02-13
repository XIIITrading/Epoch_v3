"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
Stop Analysis Calculator - Configuration
XIII Trading LLC
================================================================================

Self-contained configuration for the Stop Analysis calculation module.
Calculates 6 different stop types and simulates outcomes for each trade.

Version: 1.0.0
================================================================================
"""

from datetime import time
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
# TRADING SESSION TIMES (Eastern Time)
# =============================================================================
MARKET_OPEN = time(9, 30)      # Regular trading hours start
EOD_CUTOFF = time(15, 30)      # End of day cutoff for stop analysis
MARKET_CLOSE = time(16, 0)     # Regular trading hours end

# =============================================================================
# STOP TYPE CONFIGURATION
# =============================================================================
STOP_TYPES = [
    'zone_buffer',   # Stop Type 1: Zone Boundary + 5% Buffer
    'prior_m1',      # Stop Type 2: Prior M1 Bar High/Low
    'prior_m5',      # Stop Type 3: Prior M5 Bar High/Low
    'm5_atr',        # Stop Type 4: M5 ATR (1.1x)
    'm15_atr',       # Stop Type 5: M15 ATR (1.1x)
    'fractal',       # Stop Type 6: M5 Fractal High/Low
]

STOP_TYPE_DISPLAY_NAMES = {
    'zone_buffer': 'Zone + 5% Buffer',
    'prior_m1': 'Prior M1 H/L',
    'prior_m5': 'Prior M5 H/L',
    'm5_atr': 'M5 ATR (1.1x)',
    'm15_atr': 'M15 ATR (1.1x)',
    'fractal': 'M5 Fractal H/L'
}

# Default stop type (aligns with backtest system)
DEFAULT_STOP_TYPE = 'zone_buffer'

# =============================================================================
# CALCULATION PARAMETERS
# =============================================================================
# Zone buffer percentage
ZONE_BUFFER_PCT = 0.05  # 5% buffer beyond zone boundary

# ATR parameters
ATR_PERIOD = 14          # 14-period ATR
ATR_MULTIPLIER = 1.1     # 1.1x ATR for stop distance

# Fractal parameters
FRACTAL_LENGTH = 2       # Bars on each side for fractal detection

# =============================================================================
# TABLE CONFIGURATION
# =============================================================================
SOURCE_TABLES = {
    'trades': 'trades',
    'mfe_mae': 'mfe_mae_potential',
    'm1_bars': 'm1_bars',
    'm5_bars': 'm5_trade_bars'
}
TARGET_TABLE = "stop_analysis"

# =============================================================================
# LOGGING
# =============================================================================
VERBOSE = True
