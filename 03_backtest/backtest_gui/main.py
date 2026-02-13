"""
Backtest Runner GUI Entry Point
Epoch Trading System v2.0 - XIII Trading LLC

Launches the PyQt6 Backtest Runner window.
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from main_window import BacktestRunnerWindow


def main():
    """Main entry point for the Backtest Runner GUI."""
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show window
    window = BacktestRunnerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
