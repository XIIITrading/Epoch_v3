"""
Base Tab Class
Epoch Trading System v2.0 - XIII Trading LLC

Base class for all application tabs with common functionality.
"""

from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.styles import COLORS


class BaseTab(QWidget):
    """
    Base class for all tabs.

    Provides common functionality:
    - Section frame creation
    - Table creation with full row display (no internal scrolling)
    - Results update handling
    - Common styling
    """

    def __init__(self, analysis_results):
        super().__init__()
        self.analysis_results = analysis_results
        self.analysis_results.results_updated.connect(self.on_results_updated)

        self._setup_ui()

    def _setup_ui(self):
        """Override in subclass to set up the tab UI."""
        pass

    def on_results_updated(self, results: Dict[str, Any]):
        """Override in subclass to handle results updates."""
        pass

    def create_section_frame(self, title: str) -> tuple:
        """
        Create a section frame with title.

        Returns:
            tuple: (frame, content_layout) for adding widgets to the section
        """
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Section title
        title_label = QLabel(title)
        title_label.setObjectName("sectionLabel")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        layout.addLayout(content_layout)

        return frame, content_layout

    def create_table(
        self,
        headers: List[str],
        data: List[List[Any]] = None,
        column_widths: List[int] = None
    ) -> QTableWidget:
        """
        Create a table that shows ALL rows (no internal scrolling).

        Args:
            headers: Column header labels
            data: Optional initial data rows
            column_widths: Optional list of column widths

        Returns:
            QTableWidget configured for full display
        """
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Configure for no internal scrolling - table shows all rows
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Header styling
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Set column widths if provided
        if column_widths:
            for i, width in enumerate(column_widths):
                if i < len(headers):
                    table.setColumnWidth(i, width)
        else:
            # Auto-resize columns
            for i in range(len(headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Alternating row colors
        table.setAlternatingRowColors(True)

        # Selection behavior
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Disable editing
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Populate with data if provided
        if data:
            self.populate_table(table, data)

        return table

    def populate_table(
        self,
        table: QTableWidget,
        data: List[List[Any]],
        colors: List[Optional[str]] = None
    ):
        """
        Populate a table with data and resize to fit all rows.

        Args:
            table: The table widget to populate
            data: List of rows, each row is a list of cell values
            colors: Optional list of row colors (hex strings or None)
        """
        table.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            row_color = colors[row_idx] if colors and row_idx < len(colors) else None

            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                # Apply row color if specified
                if row_color:
                    item.setForeground(QColor(row_color))

                table.setItem(row_idx, col_idx, item)

        # Resize table to fit all rows (no scrolling)
        self._resize_table_to_contents(table)

    def _resize_table_to_contents(self, table: QTableWidget):
        """Resize table height to show all rows without scrolling."""
        # Calculate total height needed
        header_height = table.horizontalHeader().height()
        row_height = table.verticalHeader().defaultSectionSize()
        total_rows = table.rowCount()

        # Add some padding
        total_height = header_height + (row_height * total_rows) + 4

        # Set minimum and fixed height
        table.setMinimumHeight(total_height)
        table.setMaximumHeight(total_height)

        # Ensure the table doesn't try to be larger than needed
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def create_metric_label(self, label: str, value: str, color: str = None) -> QWidget:
        """
        Create a metric display with label and value.

        Args:
            label: The metric label
            value: The metric value
            color: Optional color for the value

        Returns:
            Widget containing the metric display
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(label_widget)

        value_widget = QLabel(str(value))
        if color:
            value_widget.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            value_widget.setStyleSheet("font-weight: bold;")
        layout.addWidget(value_widget)

        layout.addStretch()

        return widget

    def get_results(self) -> Dict[str, Any]:
        """Get current analysis results."""
        return self.analysis_results.results

    def get_all_tickers_results(self) -> List[Dict[str, Any]]:
        """Get combined list of all ticker results (index + custom)."""
        results = self.get_results()
        all_results = []

        if results.get("index"):
            all_results.extend(results["index"])
        if results.get("custom"):
            all_results.extend(results["custom"])

        return all_results
