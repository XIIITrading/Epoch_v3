"""
Epoch Trading System - Trade Reel
Highlight trade viewer and social media image exporter.

Usage: python 11_trade_reel/app.py
"""

import sys
import logging
from pathlib import Path

# Module path setup
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
)

from PyQt6.QtWidgets import QApplication
from ui.main_window import TradeReelWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Epoch Trade Reel")

    window = TradeReelWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
