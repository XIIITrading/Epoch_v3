"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 08: JOURNAL PROCESSOR PIPELINE v1.0
Application Entry Point
XIII Trading LLC
================================================================================

Launches the PyQt6 Journal Processor GUI for running the 8 secondary
processors in dependency order.

Processors:
    1. j_m1_bars              - Fetch M1 bars from Polygon
    2. j_m1_indicator_bars    - Calculate 22 indicators
    3. j_m1_atr_stop          - M1 ATR stop simulation
    4. j_m5_atr_stop          - M5 ATR stop simulation
    5. j_trades_m5_r_win      - Consolidation / denormalization
    6. j_m1_trade_indicator   - Entry bar snapshot
    7. j_m1_ramp_up_indicator - 25 bars before entry
    8. j_m1_post_trade_indicator - 25 bars after entry

Usage:
    python processor_app.py

================================================================================
"""
import sys
from pathlib import Path

# Ensure processor directory is on path for sub-module imports
sys.path.insert(0, str(Path(__file__).parent / "processor"))

# Ensure processor_gui directory is on path so main_window can import styles
sys.path.insert(0, str(Path(__file__).parent / "processor_gui"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from processor_gui.main_window import ProcessorWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show window
    window = ProcessorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
