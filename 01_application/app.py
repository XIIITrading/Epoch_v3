"""
Epoch Trading System - Main Application
Epoch Trading System v2.0 - XIII Trading LLC

Main entry point for the PyQt6 trading analysis application.
"""

import sys
import os
from pathlib import Path

# Add application directory to path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Set up environment before importing PyQt6
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Epoch Trading System")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("XIII Trading LLC")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
