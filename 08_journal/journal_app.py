"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 08: JOURNAL TRADE VIEWER v2.0
Application Entry Point
XIII Trading LLC
================================================================================

Launches the PyQt6 Journal Trade Viewer GUI.

1:1 clone of 11_trade_reel (Trade Reel) adapted for journal trade data:
- 6-row chart layout: Weekly+Daily, H1+M15, M5+M1 Ramp-Up, Pre-trade
  indicators, Post-trade indicators, M1 Action
- TradingView Dark theme
- Entry/exit markers, zone overlays, R-level lines
- Volume by Price overlays (epoch anchor -> trade date)
- M5 ATR(14) stop + R-level computation (pre-computed or on-the-fly)
- Multiple exit triangles from FIFO partial exits
- Pre-trade and post-trade indicator tables

Data sources:
- j_trades_m5_r_win (primary, pre-computed ATR/R data)
- journal_trades (fallback, ATR computed on-the-fly)
- j_m1_indicator_bars (ramp-up and post-trade indicator tables)
- zones + setups (zone overlays)
- Polygon API (Weekly, Daily, H1, M15, M5, M1 bars)

Usage:
    python journal_app.py    # Launch GUI

================================================================================
"""
import os
import sys
import logging
from pathlib import Path

# Fix Qt platform plugin discovery on Windows
# qwindows.dll depends on Qt6Core.dll/Qt6Gui.dll in PyQt6/Qt6/bin/
# Python 3.8+ on Windows requires os.add_dll_directory() for DLL search
import importlib.util as _ilu
_spec = _ilu.find_spec("PyQt6")
if _spec and _spec.origin:
    _pyqt6_dir = Path(_spec.origin).parent
    _qt6_bin = _pyqt6_dir / "Qt6" / "bin"
    if _qt6_bin.exists():
        os.add_dll_directory(str(_qt6_bin))
        os.environ["PATH"] = str(_qt6_bin) + os.pathsep + os.environ.get("PATH", "")
    _qt_plugins = _pyqt6_dir / "Qt6" / "plugins"
    if _qt_plugins.exists():
        os.environ["QT_PLUGIN_PATH"] = str(_qt_plugins)

# Add module directory to path for relative imports
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Add 11_trade_reel to path for chart imports
TRADE_REEL_DIR = MODULE_DIR.parent / "11_trade_reel"
sys.path.insert(0, str(TRADE_REEL_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from viewer.main_window import JournalViewerWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Trebuchet MS", 10)
    app.setFont(font)

    # Create and show window
    window = JournalViewerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
