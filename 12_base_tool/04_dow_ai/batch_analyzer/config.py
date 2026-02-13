"""
Batch Analyzer Configuration
Epoch Trading System v1 - XIII Trading LLC
"""

import os
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
MODULE_DIR = Path(__file__).parent
DOW_AI_DIR = MODULE_DIR.parent
EPOCH_DIR = DOW_AI_DIR.parent
AI_CONTEXT_DIR = DOW_AI_DIR / "ai_context"

# =============================================================================
# Supabase Configuration
# =============================================================================
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require"
}

# =============================================================================
# Claude API Configuration
# =============================================================================
# Import API key from main DOW AI config using importlib to avoid collision
# with installed 'config' package in site-packages
import importlib.util
_config_path = DOW_AI_DIR / "config.py"
_spec = importlib.util.spec_from_file_location("dow_ai_config", _config_path)
_dow_config = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_dow_config)
    ANTHROPIC_API_KEY = _dow_config.ANTHROPIC_API_KEY
except Exception:
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Model selection
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Cost-effective for batch
CLAUDE_MODEL_OPUS = "claude-opus-4-5-20251101"  # Highest quality

# API rate limiting
REQUESTS_PER_MINUTE = 50  # Conservative limit
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0
BATCH_SIZE = 100  # Checkpoint every N trades

# Token limits
MAX_INPUT_TOKENS = 1500
MAX_OUTPUT_TOKENS = 300

# =============================================================================
# Batch Processing Configuration
# =============================================================================
# M1 ramp-up bars to include
M1_RAMPUP_BARS = 15

# Checkpoint file for resuming interrupted batches
CHECKPOINT_FILE = MODULE_DIR / "data" / "batch_checkpoint.json"

# =============================================================================
# Prediction Thresholds (for rule-based fallback)
# =============================================================================
HEALTH_THRESHOLDS = {
    "TRADE": 5,      # Health >= 5 suggests TRADE
    "NO_TRADE": 4,   # Health <= 4 suggests NO TRADE
}

CONFIDENCE_THRESHOLDS = {
    "HIGH": {"health_min": 7, "healthy_factors_min": 7},
    "MEDIUM": {"health_min": 5, "healthy_factors_min": 5},
    "LOW": {"health_min": 0, "healthy_factors_min": 0},
}

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FILE = MODULE_DIR / "logs" / "batch_analyzer.log"
