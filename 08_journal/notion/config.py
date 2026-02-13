"""
Notion-specific configuration for the EPOCH Trade Journal.

Imports DB_CONFIG from the existing 08_journal/config.py.
All Notion IDs, rate limits, tag definitions, and signal thresholds live here.
"""

import sys
from pathlib import Path

# Add parent so we can import from 08_journal/config.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG  # noqa: E402

# =============================================================================
# Notion Database IDs
# =============================================================================
# Existing "Trade Journal" database under "Data Management" page
NOTION_DATABASE_ID = "2fef98ca811d8013b83ac85f36ba5cc2"
NOTION_DATA_SOURCE_ID = "2fef98ca-811d-809f-a5bd-000babdcb0d4"
NOTION_PARENT_PAGE_ID = "2a8f98ca811d8099b24df5071a720600"

# =============================================================================
# Rate Limiting
# =============================================================================
NOTION_CALL_DELAY = 0.5   # seconds between individual Notion MCP calls
BATCH_SIZE = 10            # pages per batch before pause
BATCH_PAUSE = 2.0          # seconds between batches

# =============================================================================
# Predefined Tags (multi_select options)
# =============================================================================
TAGS = [
    {"name": "Clean Entry", "color": "green"},
    {"name": "Messy Entry", "color": "red"},
    {"name": "Absorption Skip", "color": "orange"},
    {"name": "H1 Neutral Edge", "color": "blue"},
    {"name": "With Trend", "color": "green"},
    {"name": "Counter Trend", "color": "purple"},
    {"name": "Fast R1", "color": "green"},
    {"name": "Slow R1", "color": "yellow"},
    {"name": "Max Pain", "color": "red"},
    {"name": "Perfect Setup", "color": "green"},
    {"name": "Review Again", "color": "yellow"},
    {"name": "Pattern Example", "color": "blue"},
    {"name": "Edge Validated", "color": "green"},
    {"name": "Edge Violated", "color": "red"},
]

# =============================================================================
# Signal Classification Thresholds
# =============================================================================
ABSORPTION_THRESHOLD = 0.12     # candle_range_pct below this = absorption skip
NORMAL_THRESHOLD = 0.15         # candle_range_pct above this = normal/tradeable
VOL_ROC_ELEVATED = 30           # volume ROC above this = elevated
SMA_WIDE_SPREAD = 0.15          # SMA spread % above this = wide
CVD_RISING = 0.1                # CVD slope above this = bullish aligned
CVD_FALLING = -0.1              # CVD slope below this = bearish aligned

# Health score label mapping
HEALTH_LABELS = {
    (8, 10): "STRONG",
    (6, 7): "MODERATE",
    (4, 5): "WEAK",
    (0, 3): "CRITICAL",
}


def get_health_label(score) -> str:
    """Return health label for a numeric score."""
    if score is None:
        return "N/A"
    try:
        s = int(score)
    except (TypeError, ValueError):
        return "N/A"
    if s >= 8:
        return "STRONG"
    elif s >= 6:
        return "MODERATE"
    elif s >= 4:
        return "WEAK"
    else:
        return "CRITICAL"
