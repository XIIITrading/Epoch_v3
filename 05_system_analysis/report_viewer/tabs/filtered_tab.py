"""
================================================================================
EPOCH TRADING SYSTEM - Filtered Tab (Base Class)
XIII Trading LLC
================================================================================

Base class for date-filtered analysis tabs (Daily, Weekly, Monthly).
Shows the same 4 report sections as Overview, but with date-filtered data.

Subclasses only need to set the tab_label via __init__.

================================================================================
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from styles import COLORS
from tabs.section_builder import clear_layout, build_all_sections


class FilteredTab(QWidget):
    """
    Tab that displays the same 4 report sections as Overview,
    but with data from a date-filtered DataProvider.

    Subclasses set tab_label for display purposes.
    """

    def __init__(self, tab_label: str = "Filtered"):
        super().__init__()
        self._tab_label = tab_label
        self._setup_ui()

    def _setup_ui(self):
        """Build scrollable layout with placeholder."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(20)

        placeholder = QLabel(f"Click Refresh to load {self._tab_label} data")
        placeholder.setObjectName("placeholderLabel")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont("Segoe UI", 12))
        placeholder.setMinimumHeight(200)
        self._layout.addWidget(placeholder)
        self._layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def update_data(self, provider, date_label: str = ""):
        """
        Rebuild all sections from a date-filtered DataProvider.

        Args:
            provider: DataProvider with date-filtered data already loaded
            date_label: Human-readable date range string for display
        """
        clear_layout(self._layout)

        if not provider.is_loaded or provider.trade_count == 0:
            no_data = QLabel(f"No trades found for {date_label}")
            no_data.setObjectName("placeholderLabel")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setFont(QFont("Segoe UI", 12))
            no_data.setStyleSheet(f"color: {COLORS['text_muted']};")
            no_data.setMinimumHeight(200)
            self._layout.addWidget(no_data)
        else:
            build_all_sections(provider, self._layout, date_label=date_label)

        self._layout.addStretch()
