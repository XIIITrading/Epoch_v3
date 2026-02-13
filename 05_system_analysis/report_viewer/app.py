"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 05: SYSTEM ANALYSIS
Dashboard - Application Entry Point
XIII Trading LLC
================================================================================

Launches the PyQt6 System Analysis Dashboard.

Usage:
    python app.py

================================================================================
"""
import sys
from pathlib import Path

# Add report_viewer to path
gui_path = Path(__file__).parent
sys.path.insert(0, str(gui_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from main_window import ReportDashboardWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show window
    window = ReportDashboardWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
