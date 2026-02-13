"""
================================================================================
EPOCH TRADING SYSTEM - Overview Tab
XIII Trading LLC
================================================================================

Overview tab for the System Analysis dashboard.
Shows all 4 report sections with ALL data (no date filter).

Delegates section building to section_builder.py for reuse
across Overview, Daily, Weekly, and Monthly tabs.

================================================================================
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from tabs.section_builder import clear_layout, build_all_sections


class OverviewTab(QWidget):
    """
    Overview tab displaying all 4 summary report sections (all data).

    Sections:
        1. Stop Type Comparison
        2. Win Rate by Model (per stop type)
        3. Model-Direction Grid
        4. MFE/MAE Sequence Analysis
    """

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Build the scrollable layout with placeholder."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(20)

        # Placeholder
        placeholder = QLabel("Click Refresh to load data from Supabase")
        placeholder.setObjectName("placeholderLabel")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont("Segoe UI", 12))
        placeholder.setMinimumHeight(200)
        self._layout.addWidget(placeholder)
        self._layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def update_data(self, provider):
        """
        Rebuild all sections from DataProvider (all data, no date filter).

        Called by main_window after data refresh.
        """
        clear_layout(self._layout)
        build_all_sections(provider, self._layout)
        self._layout.addStretch()
