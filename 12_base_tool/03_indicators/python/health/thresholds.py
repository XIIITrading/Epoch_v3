"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Health Score Thresholds
XIII Trading LLC
================================================================================

Thresholds and labels for health score calculation.

================================================================================
"""

import sys
from pathlib import Path

# Add parent to path for relative imports within shared library
_LIB_DIR = Path(__file__).parent.parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _internal import HEALTH_CONFIG, VOLUME_ROC_CONFIG, CVD_CONFIG


# =============================================================================
# THRESHOLDS
# =============================================================================
THRESHOLDS = {
    "volume_roc": VOLUME_ROC_CONFIG["above_avg_threshold"],
    "cvd_slope": CVD_CONFIG["rising_threshold"],
}


# =============================================================================
# LABEL FUNCTIONS
# =============================================================================
def get_health_label(score: int) -> str:
    """
    Get health label for a given score.

    Args:
        score: Health score (0-10)

    Returns:
        Label: 'STRONG', 'MODERATE', 'WEAK', or 'CRITICAL'
    """
    labels = HEALTH_CONFIG["labels"]

    if score >= labels["strong"]["min"]:
        return labels["strong"]["label"]
    elif score >= labels["moderate"]["min"]:
        return labels["moderate"]["label"]
    elif score >= labels["weak"]["min"]:
        return labels["weak"]["label"]
    else:
        return labels["critical"]["label"]


def get_health_color(label: str) -> str:
    """
    Get display color for a health label.

    Args:
        label: Health label ('STRONG', 'MODERATE', 'WEAK', 'CRITICAL')

    Returns:
        Hex color code
    """
    colors = {
        "STRONG": "#00C853",    # Green
        "MODERATE": "#FFC107",  # Yellow/Amber
        "WEAK": "#FF9800",      # Orange
        "CRITICAL": "#FF1744",  # Red
    }
    return colors.get(label, "#888888")
