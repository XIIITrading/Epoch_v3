"""
DOW AI Analysis Tool - Main Entry Point
Epoch Trading System v2.0 - XIII Trading LLC

PyQt6 GUI for running batch analysis with real-time terminal output.

Usage:
    python main.py
"""
import sys
from pathlib import Path

# Setup paths
_this_dir = str(Path(__file__).parent.resolve())
_dow_ai_dir = str(Path(__file__).parent.parent.resolve())
_epoch_dir = str(Path(__file__).parent.parent.parent.resolve())

if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
if _dow_ai_dir not in sys.path:
    sys.path.insert(1, _dow_ai_dir)
if _epoch_dir not in sys.path:
    sys.path.insert(2, _epoch_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from main_window import DOWAnalysisWindow


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
    window = DOWAnalysisWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
