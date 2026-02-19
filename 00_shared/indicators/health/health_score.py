"""
DEPRECATED - Health scoring has been removed per SWH-6.
All scoring systems are deprecated (no validated edge).
This file is retained as a placeholder during migration.
"""

import warnings

def calculate_health_score(*args, **kwargs):
    warnings.warn(
        "calculate_health_score is deprecated and will be removed. "
        "All scoring systems have been deprecated per SWH-6.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None
