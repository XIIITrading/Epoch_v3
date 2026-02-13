"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTEST PROCESSOR
R-Level Events Configuration
XIII Trading LLC
================================================================================

Configuration for R-level crossing event detection.
================================================================================
"""

# =============================================================================
# R-Level Event Types
# =============================================================================
# These are ADDED to existing event types (ENTRY, MFE, MAE, EXIT)
R_LEVEL_EVENT_TYPES = ['R1_CROSS', 'R2_CROSS', 'R3_CROSS']

# All valid event types (existing + new)
ALL_EVENT_TYPES = ['ENTRY', 'MFE', 'MAE', 'EXIT', 'R1_CROSS', 'R2_CROSS', 'R3_CROSS']

# =============================================================================
# R-Level Definitions
# =============================================================================
R_LEVELS = {
    'R1': 1.0,  # 1R target
    'R2': 2.0,  # 2R target
    'R3': 3.0,  # 3R target
}

# =============================================================================
# Stop Type for R Calculation
# =============================================================================
# Use zone_buffer stop from stop_analysis table
DEFAULT_STOP_TYPE = 'zone_buffer'

# Fallback: Zone edge + 5% buffer if stop_analysis not available
ZONE_BUFFER_PERCENT = 0.05

# =============================================================================
# Time Boundaries
# =============================================================================
# Only detect crossings between entry and EOD exit
EOD_EXIT_TIME = "15:30:00"

# =============================================================================
# Database Configuration
# =============================================================================
# Reuse from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from config import SUPABASE_CONFIG
    DB_CONFIG = SUPABASE_CONFIG
except ImportError:
    # Fallback configuration
    DB_CONFIG = {
        "host": "db.pdbmcskznoaiybdiobje.supabase.co",
        "port": 5432,
        "database": "postgres",
        "user": "postgres",
        "password": "guid-saltation-covet",
        "sslmode": "require"
    }

# =============================================================================
# Batch Processing
# =============================================================================
BATCH_SIZE = 100  # Process trades in batches
LOG_INTERVAL = 10  # Log progress every N trades
