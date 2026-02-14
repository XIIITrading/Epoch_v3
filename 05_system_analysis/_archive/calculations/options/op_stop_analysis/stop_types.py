"""
Options Stop Type Definitions

Defines the stop types available for options analysis.
All stops are percentage-based from option entry price.
"""

from typing import Dict, Any


# Stop type definitions
# Key: internal identifier
# Value: metadata about the stop
OPTIONS_STOP_TYPES: Dict[str, Dict[str, Any]] = {
    "stop_10pct": {
        "display_name": "10% Stop",
        "short_name": "10%",
        "loss_pct": 10.0,
        "description": "Stop at 10% loss from entry",
        "risk_level": "tight"
    },
    "stop_15pct": {
        "display_name": "15% Stop",
        "short_name": "15%",
        "loss_pct": 15.0,
        "description": "Stop at 15% loss from entry",
        "risk_level": "tight"
    },
    "stop_20pct": {
        "display_name": "20% Stop",
        "short_name": "20%",
        "loss_pct": 20.0,
        "description": "Stop at 20% loss from entry",
        "risk_level": "moderate"
    },
    "stop_25pct": {
        "display_name": "25% Stop",
        "short_name": "25%",
        "loss_pct": 25.0,
        "description": "Stop at 25% loss from entry (recommended)",
        "risk_level": "moderate"
    },
    "stop_30pct": {
        "display_name": "30% Stop",
        "short_name": "30%",
        "loss_pct": 30.0,
        "description": "Stop at 30% loss from entry",
        "risk_level": "wide"
    },
    "stop_50pct": {
        "display_name": "50% Stop",
        "short_name": "50%",
        "loss_pct": 50.0,
        "description": "Stop at 50% loss from entry",
        "risk_level": "very_wide"
    }
}

# Default stop type
DEFAULT_OPTIONS_STOP_TYPE = "stop_25pct"

# Ordered list for display
STOP_TYPE_ORDER = [
    "stop_10pct",
    "stop_15pct",
    "stop_20pct",
    "stop_25pct",
    "stop_30pct",
    "stop_50pct"
]


def get_stop_type_display_name(stop_type: str, short: bool = False) -> str:
    """Get display name for a stop type."""
    if stop_type not in OPTIONS_STOP_TYPES:
        return stop_type

    key = "short_name" if short else "display_name"
    return OPTIONS_STOP_TYPES[stop_type][key]


def get_stop_loss_pct(stop_type: str) -> float:
    """Get the loss percentage for a stop type."""
    if stop_type not in OPTIONS_STOP_TYPES:
        return 25.0  # Default
    return OPTIONS_STOP_TYPES[stop_type]["loss_pct"]
