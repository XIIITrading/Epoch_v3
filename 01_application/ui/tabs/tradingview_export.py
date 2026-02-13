"""
TradingView Export Tab
Epoch Trading System v2.0 - XIII Trading LLC

Exports analysis data in a table format for TradingView PineScript integration.
Each cell can be copied individually for easy data transfer.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS


class TradingViewExportTab(BaseTab):
    """
    TradingView Export Tab

    Features:
    - Table with all export data
    - Click any cell to copy its value
    - Copy row button for full row data
    - Export all to clipboard
    """

    # Column definitions
    COLUMNS = [
        ("Ticker", 70),
        ("Ticker_ID", 100),
        ("Date", 90),
        ("Top_Zone_ID", 100),
        ("Top_Zone_POC", 100),
        ("Top_Zone_Rank", 90),
        ("Top_Zone_Score", 100),
        ("Epoch_Start", 90),
        ("POC1", 70),
        ("POC2", 70),
        ("POC3", 70),
        ("POC4", 70),
        ("POC5", 70),
        ("POC6", 70),
        ("POC7", 70),
        ("POC8", 70),
        ("POC9", 70),
        ("POC10", 70),
        ("PineScript_6", 250),
        ("PineScript_16", 450),
        ("Export_Time", 120),
    ]

    def __init__(self, analysis_results):
        super().__init__(analysis_results)

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title section
        title_layout = QHBoxLayout()

        title = QLabel("TRADINGVIEW EXPORT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Instructions
        instructions = QLabel("Click any cell to copy its value")
        instructions.setStyleSheet(f"color: {COLORS['text_secondary']}; font-style: italic;")
        title_layout.addWidget(instructions)

        layout.addLayout(title_layout)

        # Control buttons
        button_frame = self._create_button_section()
        layout.addWidget(button_frame)

        # Status
        self.status_label = QLabel("Run analysis to populate export data")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)

        # Table
        self.table = self._create_table()
        layout.addWidget(self.table)

    def _create_button_section(self) -> QFrame:
        """Create the button section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh Data")
        self.refresh_button.clicked.connect(self._refresh_data)
        layout.addWidget(self.refresh_button)

        # Copy all button
        self.copy_all_button = QPushButton("📋 Copy All (TSV)")
        self.copy_all_button.setToolTip("Copy entire table as tab-separated values for Excel/Sheets")
        self.copy_all_button.clicked.connect(self._copy_all_to_clipboard)
        layout.addWidget(self.copy_all_button)

        # Copy headers button
        self.copy_headers_button = QPushButton("📋 Copy Headers")
        self.copy_headers_button.clicked.connect(self._copy_headers)
        layout.addWidget(self.copy_headers_button)

        layout.addStretch()

        # Row count label
        self.row_count_label = QLabel("0 rows")
        self.row_count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.row_count_label)

        return frame

    def _create_table(self) -> QTableWidget:
        """Create the export table."""
        table = QTableWidget()
        table.setColumnCount(len(self.COLUMNS))
        table.setHorizontalHeaderLabels([col[0] for col in self.COLUMNS])

        # Set column widths
        for i, (_, width) in enumerate(self.COLUMNS):
            table.setColumnWidth(i, width)

        # Table settings
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Enable horizontal scrolling
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Styling - use correct COLORS keys from styles.py
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_table']};
                alternate-background-color: {COLORS['bg_table_alt']};
                gridline-color: {COLORS['border']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            QTableWidget::item {{
                padding: 4px 8px;
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['bg_header']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_header']};
                color: {COLORS['text_primary']};
                padding: 6px;
                border: 1px solid {COLORS['border']};
                font-weight: bold;
            }}
        """)

        # Connect cell click to copy
        table.cellClicked.connect(self._on_cell_clicked)

        return table

    def _on_cell_clicked(self, row: int, column: int):
        """Handle cell click - copy value to clipboard."""
        item = self.table.item(row, column)
        if item:
            text = item.text()
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # Update status
            col_name = self.COLUMNS[column][0]
            self.status_label.setText(f"Copied: {col_name} = '{text[:50]}...' " if len(text) > 50 else f"Copied: {col_name} = '{text}'")
            self.status_label.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

    def _copy_all_to_clipboard(self):
        """Copy entire table as TSV."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data to copy. Run analysis first.")
            return

        lines = []

        # Headers
        headers = [col[0] for col in self.COLUMNS]
        lines.append("\t".join(headers))

        # Data rows
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            lines.append("\t".join(row_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(lines))

        self.status_label.setText(f"Copied all {self.table.rowCount()} rows to clipboard (TSV format)")
        self.status_label.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

    def _copy_headers(self):
        """Copy just the headers."""
        headers = [col[0] for col in self.COLUMNS]
        clipboard = QApplication.clipboard()
        clipboard.setText("\t".join(headers))

        self.status_label.setText("Headers copied to clipboard")
        self.status_label.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

    def _refresh_data(self):
        """Refresh data from analysis results."""
        results = self.get_results()

        if not results.get("run_complete"):
            self.status_label.setText("No analysis data available. Run analysis first.")
            self.status_label.setStyleSheet(f"color: {COLORS['status_error']};")
            return

        self._populate_table(results)

    def _populate_table(self, results: Dict[str, Any]):
        """Populate the table with analysis results."""
        all_results = results.get("index", []) + results.get("custom", [])
        successful = [r for r in all_results if r.get("success")]

        if not successful:
            self.status_label.setText("No successful results to export")
            self.status_label.setStyleSheet(f"color: {COLORS['status_error']};")
            return

        # Clear existing data
        self.table.setRowCount(0)
        self.table.setRowCount(len(successful))

        analysis_date = results.get("analysis_date", date.today())
        if isinstance(analysis_date, str):
            analysis_date = datetime.strptime(analysis_date, '%Y-%m-%d').date()

        export_time = datetime.now().strftime("%m/%d/%Y %H:%M")

        for row_idx, result in enumerate(successful):
            self._populate_row(row_idx, result, analysis_date, export_time)

        self.row_count_label.setText(f"{len(successful)} rows")
        self.status_label.setText(f"Loaded {len(successful)} tickers - click any cell to copy")
        self.status_label.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

    def _populate_row(self, row_idx: int, result: Dict, analysis_date: date, export_time: str):
        """Populate a single row with result data."""
        ticker = result.get("ticker", "")

        # Get HVN result for epoch and POCs
        hvn_result = result.get("hvn_result", {})
        epoch_start = hvn_result.get("start_date", "")
        if isinstance(epoch_start, date):
            epoch_start = epoch_start.strftime("%m/%d/%Y")
        elif isinstance(epoch_start, str) and "-" in epoch_start:
            # Convert from YYYY-MM-DD to M/D/YYYY
            try:
                dt = datetime.strptime(epoch_start, "%Y-%m-%d")
                epoch_start = dt.strftime("%-m/%-d/%Y") if sys.platform != "win32" else dt.strftime("%#m/%#d/%Y")
            except:
                pass

        # Get POCs (top 10) - HVNResult uses 'pocs' key (List[POCResult])
        poc_list = hvn_result.get("pocs", [])
        pocs = []
        for i in range(10):
            if i < len(poc_list):
                poc_data = poc_list[i]
                if isinstance(poc_data, dict):
                    pocs.append(poc_data.get("price", 0))
                else:
                    pocs.append(poc_data)
            else:
                pocs.append(0)

        # Get top zone (primary setup)
        primary_setup = result.get("primary_setup", {})
        secondary_setup = result.get("secondary_setup", {})

        # Use primary setup as top zone, or best filtered zone
        top_zone_id = ""
        top_zone_poc = 0
        top_zone_rank = ""
        top_zone_score = 0

        if primary_setup and primary_setup.get("hvn_poc", 0) > 0:
            top_zone_id = primary_setup.get("zone_id", "").replace(f"{ticker}_", "")
            top_zone_poc = primary_setup.get("hvn_poc", 0)
            top_zone_rank = self._clean_rank(primary_setup.get("rank", ""))
            top_zone_score = primary_setup.get("score", 0)
        else:
            # Fall back to filtered zones
            filtered_zones = result.get("filtered_zones", [])
            if filtered_zones:
                top = filtered_zones[0]
                top_zone_id = top.get("zone_id", "").replace(f"{ticker}_", "")
                top_zone_poc = top.get("hvn_poc", 0)
                top_zone_rank = self._clean_rank(top.get("rank", ""))
                top_zone_score = top.get("score", 0)

        # Build ticker ID (ticker + date)
        date_str = analysis_date.strftime("%m%d%y")
        ticker_id = f"{ticker}_{date_str}"

        # Format date for display
        display_date = analysis_date.strftime("%-m/%-d/%Y") if sys.platform != "win32" else analysis_date.strftime("%#m/%#d/%Y")

        # Build PineScript strings
        pinescript_6 = self._build_pinescript_6(primary_setup, secondary_setup)
        pinescript_16 = self._build_pinescript_16(primary_setup, secondary_setup, pocs)

        # Set table values
        col_data = [
            ticker,
            ticker_id,
            display_date,
            top_zone_id,
            f"{top_zone_poc:.2f}" if top_zone_poc else "",
            top_zone_rank,
            f"{top_zone_score:.2f}" if top_zone_score else "",
            epoch_start,
            f"{pocs[0]:.2f}" if pocs[0] else "",
            f"{pocs[1]:.2f}" if pocs[1] else "",
            f"{pocs[2]:.2f}" if pocs[2] else "",
            f"{pocs[3]:.2f}" if pocs[3] else "",
            f"{pocs[4]:.2f}" if pocs[4] else "",
            f"{pocs[5]:.2f}" if pocs[5] else "",
            f"{pocs[6]:.2f}" if pocs[6] else "",
            f"{pocs[7]:.2f}" if pocs[7] else "",
            f"{pocs[8]:.2f}" if pocs[8] else "",
            f"{pocs[9]:.2f}" if pocs[9] else "",
            pinescript_6,
            pinescript_16,
            export_time,
        ]

        for col_idx, value in enumerate(col_data):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color coding for rank column
            if col_idx == 5 and value:  # Top_Zone_Rank
                if "L5" in str(value):
                    item.setForeground(QColor("#00C853"))  # Green
                elif "L4" in str(value):
                    item.setForeground(QColor("#2196F3"))  # Blue
                elif "L3" in str(value):
                    item.setForeground(QColor("#FFC107"))  # Amber
                else:
                    item.setForeground(QColor("#9E9E9E"))  # Gray

            self.table.setItem(row_idx, col_idx, item)

    def _clean_rank(self, rank_val) -> str:
        """Clean rank value - remove 'Rank.' prefix."""
        if rank_val is None:
            return ""
        rank_str = str(rank_val)
        return rank_str.replace("Rank.", "").replace("rank.", "")

    def _build_pinescript_6(self, primary_setup: Dict, secondary_setup: Dict) -> str:
        """Build 6-value PineScript string (zone high/low for both setups + targets)."""
        values = []

        # Primary zone high, low, target
        if primary_setup:
            values.append(f"{primary_setup.get('zone_high', 0):.2f}")
            values.append(f"{primary_setup.get('zone_low', 0):.2f}")
            values.append(f"{primary_setup.get('hvn_poc', 0):.2f}")
        else:
            values.extend(["0", "0", "0"])

        # Secondary zone high, low, target
        if secondary_setup:
            values.append(f"{secondary_setup.get('zone_high', 0):.2f}")
            values.append(f"{secondary_setup.get('zone_low', 0):.2f}")
            values.append(f"{secondary_setup.get('hvn_poc', 0):.2f}")
        else:
            values.extend(["0", "0", "0"])

        return ",".join(values)

    def _build_pinescript_16(self, primary_setup: Dict, secondary_setup: Dict,
                             pocs: List[float]) -> str:
        """Build 16-value PineScript string (6 setup values + 10 POCs)."""
        # Start with the 6-value string
        pinescript_6 = self._build_pinescript_6(primary_setup, secondary_setup)

        # Add 10 POCs
        poc_values = [f"{p:.2f}" if p else "0" for p in pocs[:10]]

        return pinescript_6 + "," + ",".join(poc_values)

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update - auto-populate when analysis completes."""
        if results.get("run_complete"):
            self._populate_table(results)
