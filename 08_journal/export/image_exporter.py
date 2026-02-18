"""
Epoch Trading System - Journal Image Exporter
Delegates to 11_trade_reel/export/image_exporter.py for actual rendering.
This thin wrapper resolves imports and provides the journal-specific output directory.
"""

import sys
from pathlib import Path

# Ensure trade_reel is importable
_TRADE_REEL_DIR = Path(__file__).parent.parent.parent / "11_trade_reel"
if str(_TRADE_REEL_DIR) not in sys.path:
    sys.path.insert(0, str(_TRADE_REEL_DIR))

from export.image_exporter import export_highlight_image  # noqa: F401
