"""
Epoch Trading System - Training Module Launcher
Flash Card Review System for Deliberate Practice

Usage:
    python app.py

Author: XIII Trading LLC
Version: 2.0.0
"""

import sys
import logging
from pathlib import Path

# Set up module path (only MODULE_DIR - shared imports handled in main_window.py)
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Launch the PyQt6 training application."""
    from PyQt6.QtWidgets import QApplication
    from ui.main_window import TrainingWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Epoch Trade Review")
    app.setOrganizationName("XIII Trading LLC")

    window = TrainingWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
