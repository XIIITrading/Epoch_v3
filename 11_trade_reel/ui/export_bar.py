"""
Epoch Trading System - Export Bar
Bottom bar with platform export buttons.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TV_COLORS


# Platform button styles
PLATFORM_STYLES = {
    'twitter': {
        'label': 'Export X / Twitter',
        'bg': '#000000',
        'hover': '#1A1A1A',
        'border': '#D1D4DC',
    },
    'instagram': {
        'label': 'Export Instagram',
        'bg': '#E1306C',
        'hover': '#C2185B',
        'border': '#E1306C',
    },
    'stocktwits': {
        'label': 'Export StockTwits',
        'bg': '#F57C00',
        'hover': '#E65100',
        'border': '#F57C00',
    },
    'discord': {
        'label': 'Export Discord',
        'bg': '#5865F2',
        'hover': '#4752C4',
        'border': '#5865F2',
    },
}


class ExportBar(QFrame):
    """Bottom bar with export buttons for each platform."""

    export_requested = pyqtSignal(str)      # Emits platform name
    export_all_requested = pyqtSignal()     # Export all platforms

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(f"background-color: {TV_COLORS['bg_secondary']}; "
                           f"border-top: 1px solid {TV_COLORS['border']};")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Select All / Deselect
        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {TV_COLORS['bg_primary']};
                color: {TV_COLORS['text_primary']};
                border: 1px solid {TV_COLORS['border']};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {TV_COLORS['border']}; }}
        """)
        layout.addWidget(self._select_all_btn)

        self._deselect_btn = QPushButton("Deselect All")
        self._deselect_btn.setStyleSheet(self._select_all_btn.styleSheet())
        layout.addWidget(self._deselect_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {TV_COLORS['border']};")
        layout.addWidget(sep)

        # Platform export buttons
        self._platform_btns = {}
        for platform, style in PLATFORM_STYLES.items():
            btn = QPushButton(style['label'])
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {style['bg']};
                    color: white;
                    border: 1px solid {style['border']};
                    padding: 6px 14px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: {style['hover']}; }}
                QPushButton:disabled {{ background-color: #2A2E39; color: #787B86; border-color: #2A2E39; }}
            """)
            btn.clicked.connect(lambda checked, p=platform: self.export_requested.emit(p))
            self._platform_btns[platform] = btn
            layout.addWidget(btn)

        # Separator before Export All
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet(f"color: {TV_COLORS['border']};")
        layout.addWidget(sep2)

        # Export All button
        self._export_all_btn = QPushButton("Export All")
        self._export_all_btn.setFixedHeight(36)
        self._export_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0F3D3E;
                color: white;
                border: 1px solid #0F3D3E;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #1A5C5E; }}
            QPushButton:disabled {{ background-color: #2A2E39; color: #787B86; border-color: #2A2E39; }}
        """)
        self._export_all_btn.clicked.connect(self.export_all_requested.emit)
        layout.addWidget(self._export_all_btn)

        layout.addStretch()

        # Status label
        self._status = QLabel("")
        self._status.setFont(QFont("Trebuchet MS", 10))
        self._status.setStyleSheet(f"color: {TV_COLORS['text_muted']};")
        layout.addWidget(self._status)

    @property
    def select_all_btn(self) -> QPushButton:
        return self._select_all_btn

    @property
    def deselect_btn(self) -> QPushButton:
        return self._deselect_btn

    def set_exporting(self, exporting: bool):
        """Disable buttons during export."""
        for btn in self._platform_btns.values():
            btn.setEnabled(not exporting)
        self._export_all_btn.setEnabled(not exporting)
        self._select_all_btn.setEnabled(not exporting)
        self._deselect_btn.setEnabled(not exporting)

    def set_export_enabled(self, enabled: bool):
        """Enable/disable export buttons based on selection."""
        for btn in self._platform_btns.values():
            btn.setEnabled(enabled)
        self._export_all_btn.setEnabled(enabled)

    def show_export_result(self, count: int, path: str):
        """Show export result in status label."""
        self._status.setText(f"Exported {count} images to {path}")
        self._status.setStyleSheet(f"color: {TV_COLORS['bull']};")

    def show_export_progress(self, current: int, total: int):
        """Show export progress."""
        self._status.setText(f"Exporting {current}/{total}...")
        self._status.setStyleSheet(f"color: {TV_COLORS['accent']};")

    def clear_status(self):
        self._status.setText("")
