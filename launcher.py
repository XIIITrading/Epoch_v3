"""
Epoch Trading System - Master Launcher
========================================

Central launcher for all Epoch modules.

Usage:
    python launcher.py

Or run individual modules directly:
    python 01_application/app.py
    python 02_dow_ai/app.py
    etc.
"""

import sys
from pathlib import Path

# Ensure shared package is importable
EPOCH_DIR = Path(__file__).parent
sys.path.insert(0, str(EPOCH_DIR / "00_shared"))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import subprocess

# Import shared components
from ui.styles import DARK_STYLESHEET, COLORS
from ui.base_window import BaseWindow


class ModuleButton(QPushButton):
    """Styled button for launching a module."""

    def __init__(self, title: str, description: str, module_path: str, parent=None):
        super().__init__(parent)
        self.module_path = module_path
        self.setMinimumSize(300, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(desc_label)

        # Check if module exists
        module_file = EPOCH_DIR / module_path
        if not module_file.exists():
            self.setEnabled(False)
            self.setToolTip("Module not yet migrated")


class LauncherWindow(BaseWindow):
    """Main launcher window for Epoch Trading System."""

    def __init__(self):
        super().__init__(
            title="Epoch Trading System v2.0 - Launcher",
            width=800,
            height=600,
            show_menu=False,
        )
        self._setup_ui()

    def _setup_ui(self):
        """Set up the launcher UI."""
        # Header
        header = QLabel("EPOCH TRADING SYSTEM")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 20px;")
        self.add_to_layout(header)

        subtitle = QLabel("Select a module to launch")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; padding-bottom: 20px;")
        self.add_to_layout(subtitle)

        # Module buttons container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(50, 0, 50, 0)

        # Define modules
        modules = [
            ("01 - Application", "Main trading application and zone analysis", "01_application/app.py"),
            ("02 - DOW AI", "AI-powered trading assistant and entry qualifier", "02_dow_ai/app.py"),
            ("03 - Backtest", "Trade simulation and performance analysis", "03_backtest/app.py"),
            ("04 - Indicators", "Indicator edge testing and documentation", "04_indicators/app.py"),
            ("05 - System Analysis", "Statistical analysis and Monte Carlo simulation", "05_system_analysis/app.py"),
            ("06 - Training", "Interactive training and flashcards", "06_training/app.py"),
        ]

        for title, desc, path in modules:
            btn = ModuleButton(title, desc, path)
            btn.clicked.connect(lambda checked, p=path: self._launch_module(p))
            button_layout.addWidget(btn)

        self.add_to_layout(button_container)
        self.add_stretch()

        # Footer
        footer = QLabel("XIII Trading LLC - Epoch Trading System v2.0")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 10px;")
        self.add_to_layout(footer)

    def _launch_module(self, module_path: str):
        """Launch a module in a new process."""
        full_path = EPOCH_DIR / module_path

        if not full_path.exists():
            QMessageBox.warning(
                self,
                "Module Not Available",
                f"The module '{module_path}' has not been migrated yet.\n\n"
                "Use the V1 version at:\n"
                "C:\\XIIITradingSystems\\Epoch_v1",
            )
            return

        try:
            subprocess.Popen([sys.executable, str(full_path)])
            self.set_status(f"Launched {module_path}", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Launch Error",
                f"Failed to launch module:\n{e}",
            )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
