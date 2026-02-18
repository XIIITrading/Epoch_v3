"""
Epoch Trading System - Journal Trade Table
QTableWidget with checkboxes and 5 fixed-width data columns.
Multi-row selection via checkboxes triggers export; single-row click triggers chart rendering.
Modeled on 11_trade_reel/ui/highlight_table.py.

Columns: [checkbox] | Date | Ticker | Dir | Entry | Seq
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QWidget, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont
from typing import List, Optional

from .config import TV_COLORS
from .trade_adapter import JournalHighlight


# Fixed columns: checkbox + 5 data columns
COLUMNS = ['', 'Date', 'Ticker', 'Dir', 'Entry', 'Seq']
COL_WIDTHS = {
    0: 30,    # Checkbox
    1: 95,    # Date
    2: 55,    # Ticker
    3: 55,    # Direction
    4: 55,    # Entry time
    5: 40,    # Sequence number
}


class TradeTable(QFrame):
    """Table displaying journal trades with selection checkboxes."""

    selection_changed = pyqtSignal(object)  # Emits JournalHighlight or None
    checked_changed = pyqtSignal(list)      # Emits list of checked trade_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trades: List[JournalHighlight] = []
        self._checkboxes: List[QCheckBox] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(COLUMNS))
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Fixed column widths -- set once at startup, never resized
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        for col, width in COL_WIDTHS.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(col, width)

        # Lock table width to exactly the sum of column widths + frame
        total_w = sum(COL_WIDTHS.values()) + 2  # +2 for frame border
        self._table.setFixedWidth(total_w)
        self.setFixedWidth(total_w)

        # Row click
        self._table.currentCellChanged.connect(self._on_row_changed)

        layout.addWidget(self._table)

    def set_trades(self, trades: List[JournalHighlight]):
        """Populate table rows -- columns are already configured."""
        self._trades = trades
        self._checkboxes.clear()
        self._table.setRowCount(len(trades))

        for row, hl in enumerate(trades):
            # Checkbox
            cb = QCheckBox()
            cb.stateChanged.connect(self._on_check_changed)
            self._checkboxes.append(cb)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(row, 0, cb_widget)

            # Date
            self._set_item(row, 1, str(hl.date))

            # Ticker
            self._set_item(row, 2, hl.ticker, bold=True)

            # Direction (color-coded)
            dir_color = TV_COLORS['bull'] if hl.direction == 'LONG' else TV_COLORS['bear']
            self._set_item(row, 3, hl.direction, color=dir_color, bold=True)

            # Entry time (HH:MM)
            entry_str = hl.entry_time.strftime('%H:%M') if hl.entry_time else ''
            self._set_item(row, 4, entry_str)

            # Sequence number (row index, 1-based)
            self._set_item(row, 5, str(row + 1))

        self._table.resizeRowsToContents()

    def _set_item(self, row: int, col: int, text: str,
                  color: Optional[str] = None, bold: bool = False):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if color:
            item.setForeground(QColor(color))
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        self._table.setItem(row, col, item)

    def _on_row_changed(self, row, col, prev_row, prev_col):
        if 0 <= row < len(self._trades):
            self.selection_changed.emit(self._trades[row])
        else:
            self.selection_changed.emit(None)

    def _on_check_changed(self):
        self.checked_changed.emit(self.get_checked_ids())

    def get_checked_ids(self) -> List[str]:
        """Return trade_ids of checked rows."""
        ids = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked() and i < len(self._trades):
                ids.append(self._trades[i].trade_id)
        return ids

    def get_checked_highlights(self) -> List[JournalHighlight]:
        """Return JournalHighlight objects for checked rows."""
        result = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked() and i < len(self._trades):
                result.append(self._trades[i])
        return result

    def select_all(self):
        for cb in self._checkboxes:
            cb.setChecked(True)

    def deselect_all(self):
        for cb in self._checkboxes:
            cb.setChecked(False)

    def get_trade_at(self, row: int) -> Optional[JournalHighlight]:
        if 0 <= row < len(self._trades):
            return self._trades[row]
        return None
