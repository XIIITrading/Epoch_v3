"""
Entry Qualifier - Main Entry Point
Epoch Trading System v1 - XIII Trading LLC

Displays rolling indicator data for up to 6 tickers to assist with trade entry qualification.

Usage:
    python main.py
"""
import sys
from pathlib import Path

# Setup paths - entry_qualifier at position 0, parent at position 1
# This ensures local modules found first, then parent config.py, then site-packages
_this_dir = str(Path(__file__).parent.resolve())
_parent_dir = str(Path(__file__).parent.parent.resolve())

# Entry qualifier at front - ensure it's position 0
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
elif sys.path[0] != _this_dir:
    sys.path.remove(_this_dir)
    sys.path.insert(0, _this_dir)

# Parent dir at position 1 for API keys from parent config
if _parent_dir not in sys.path:
    sys.path.insert(1, _parent_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
