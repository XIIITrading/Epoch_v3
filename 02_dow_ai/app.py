"""
DOW AI Module - Application Launcher
Epoch Trading System v2.0 - XIII Trading LLC

Launches the DOW AI tools:
1. Entry Qualifier - Real-time trading indicator display
2. DOW Analysis - Batch analyzer with terminal output

Usage:
    python app.py                    # Shows launcher
    python app.py --entry-qualifier  # Launch Entry Qualifier directly
    python app.py --dow-analysis     # Launch DOW Analysis directly
"""
import sys
import argparse
from pathlib import Path

# Setup paths
_this_dir = str(Path(__file__).parent.resolve())
_epoch_dir = str(Path(__file__).parent.parent.resolve())

if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
if _epoch_dir not in sys.path:
    sys.path.insert(1, _epoch_dir)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import subprocess


# Shared dark theme
COLORS = {
    'bg_primary': '#000000',
    'bg_secondary': '#0a0a0a',
    'bg_header': '#0f3460',
    'border': '#2a2a4a',
    'text_primary': '#e8e8e8',
    'text_secondary': '#a0a0a0',
    'text_muted': '#707070',
}

LAUNCHER_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Consolas', monospace;
}}

QLabel#headerLabel {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel#descLabel {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

QPushButton {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 20px 30px;
    font-size: 14px;
    font-weight: bold;
    min-width: 200px;
}}

QPushButton:hover {{
    background-color: #1a4a7a;
}}

QPushButton:pressed {{
    background-color: #0a2540;
}}

QFrame#toolCard {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
"""


class LauncherWindow(QMainWindow):
    """Launcher for DOW AI tools."""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the launcher UI."""
        self.setWindowTitle("DOW AI - Epoch Trading System v2.0")
        self.setMinimumSize(600, 400)
        self.resize(700, 450)
        self.setStyleSheet(LAUNCHER_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)

        # Header
        header = QLabel("DOW AI")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        subtitle = QLabel("Epoch Trading System v2.0 - XIII Trading LLC")
        subtitle.setObjectName("descLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        main_layout.addSpacing(20)

        # Tool cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Entry Qualifier card
        eq_card = self._create_tool_card(
            "Entry Qualifier",
            "Real-time indicator display for up to 6 tickers.\nUsed during live trading.",
            self._launch_entry_qualifier
        )
        cards_layout.addWidget(eq_card)

        # DOW Analysis card
        da_card = self._create_tool_card(
            "DOW Analysis",
            "Batch analyzer with terminal output.\nTest DOW implementations.",
            self._launch_dow_analysis
        )
        cards_layout.addWidget(da_card)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

    def _create_tool_card(self, title: str, description: str, callback) -> QFrame:
        """Create a tool card widget."""
        frame = QFrame()
        frame.setObjectName("toolCard")
        frame.setFixedHeight(200)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(title)
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("descLabel")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)

        # Launch button
        launch_btn = QPushButton("Launch")
        launch_btn.clicked.connect(callback)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(launch_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return frame

    def _launch_entry_qualifier(self):
        """Launch Entry Qualifier tool."""
        script_path = Path(__file__).parent / "entry_qualifier" / "main.py"
        subprocess.Popen([sys.executable, str(script_path)])

    def _launch_dow_analysis(self):
        """Launch DOW Analysis tool."""
        script_path = Path(__file__).parent / "dow_analysis" / "main.py"
        subprocess.Popen([sys.executable, str(script_path)])


def main():
    """Application entry point."""
    parser = argparse.ArgumentParser(description="DOW AI Module Launcher")
    parser.add_argument("--entry-qualifier", action="store_true",
                        help="Launch Entry Qualifier directly")
    parser.add_argument("--dow-analysis", action="store_true",
                        help="Launch DOW Analysis directly")
    args = parser.parse_args()

    if args.entry_qualifier:
        # Launch Entry Qualifier directly
        from entry_qualifier.main import main as eq_main
        eq_main()
    elif args.dow_analysis:
        # Launch DOW Analysis directly
        from dow_analysis.main import main as da_main
        da_main()
    else:
        # Show launcher
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(sys.argv)
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        window = LauncherWindow()
        window.show()

        sys.exit(app.exec())


if __name__ == '__main__':
    main()
