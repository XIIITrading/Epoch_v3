"""
Epoch Trading System - Journal Export Bar
Bottom bar with Discord export button, select/deselect, and status.
Modeled on 11_trade_reel/ui/export_bar.py (Discord-only).
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from .config import TV_COLORS


class ExportBar(QFrame):
    """Bottom bar with Discord export button."""

    export_requested = pyqtSignal(str)      # Emits platform name ('discord')

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

        # Discord export button
        self._discord_btn = QPushButton("Export Discord")
        self._discord_btn.setFixedHeight(36)
        self._discord_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #5865F2;
                color: white;
                border: 1px solid #5865F2;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #4752C4; }}
            QPushButton:disabled {{ background-color: #2A2E39; color: #787B86; border-color: #2A2E39; }}
        """)
        self._discord_btn.clicked.connect(lambda: self.export_requested.emit('discord'))
        layout.addWidget(self._discord_btn)

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
        self._discord_btn.setEnabled(not exporting)
        self._select_all_btn.setEnabled(not exporting)
        self._deselect_btn.setEnabled(not exporting)

    def set_export_enabled(self, enabled: bool):
        """Enable/disable export button based on selection."""
        self._discord_btn.setEnabled(enabled)

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
