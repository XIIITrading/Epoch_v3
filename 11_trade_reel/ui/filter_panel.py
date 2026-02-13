"""
Epoch Trading System - Trade Reel Filter Panel
Sidebar with date range, min R, model, direction, ticker filters.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QDateEdit, QSpinBox, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from PyQt6.QtGui import QFont
from datetime import date, timedelta
from typing import Optional, List


class FilterPanel(QFrame):
    """Sidebar filter panel for highlight trade loading."""

    load_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title
        title = QLabel("Trade Reel")
        title.setFont(QFont("Trebuchet MS", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #D1D4DC;")
        layout.addWidget(title)

        subtitle = QLabel("Highlight Trades")
        subtitle.setFont(QFont("Trebuchet MS", 11))
        subtitle.setStyleSheet("color: #787B86;")
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2A2E39;")
        layout.addWidget(sep)

        # Date From
        layout.addWidget(self._make_label("Date From"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        default_from = date.today() - timedelta(days=90)
        self._date_from.setDate(QDate(default_from.year, default_from.month, default_from.day))
        layout.addWidget(self._date_from)

        # Date To
        layout.addWidget(self._make_label("Date To"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        today = date.today()
        self._date_to.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self._date_to)

        # Min R
        layout.addWidget(self._make_label("Minimum R"))
        self._min_r = QSpinBox()
        self._min_r.setMinimum(1)
        self._min_r.setMaximum(5)
        self._min_r.setValue(3)
        self._min_r.setSuffix("R")
        layout.addWidget(self._min_r)

        # Model
        layout.addWidget(self._make_label("Model"))
        self._model = QComboBox()
        self._model.addItem("All Models", None)
        for m in ['EPCH1', 'EPCH2', 'EPCH3', 'EPCH4']:
            self._model.addItem(m, m)
        layout.addWidget(self._model)

        # Direction
        layout.addWidget(self._make_label("Direction"))
        self._direction = QComboBox()
        self._direction.addItem("All Directions", None)
        self._direction.addItem("LONG", "LONG")
        self._direction.addItem("SHORT", "SHORT")
        layout.addWidget(self._direction)

        # Ticker
        layout.addWidget(self._make_label("Ticker"))
        self._ticker = QComboBox()
        self._ticker.addItem("All Tickers", None)
        layout.addWidget(self._ticker)

        # Load button
        self._load_btn = QPushButton("LOAD HIGHLIGHTS")
        self._load_btn.setFixedHeight(40)
        self._load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2962FF;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1E4BD8; }
            QPushButton:disabled { background-color: #2A2E39; color: #787B86; }
        """)
        self._load_btn.clicked.connect(self._on_load_clicked)
        layout.addWidget(self._load_btn)

        # Results info
        self._results_label = QLabel("")
        self._results_label.setStyleSheet("color: #787B86; font-size: 11px;")
        self._results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._results_label)

        layout.addStretch()

        # Footer
        footer = QLabel("XIII Trading LLC")
        footer.setStyleSheet("color: #2A2E39; font-size: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def _make_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #787B86; font-size: 11px; margin-top: 4px;")
        return label

    def _on_load_clicked(self):
        self.load_requested.emit(self.get_filters())

    def get_filters(self) -> dict:
        """Extract current filter values."""
        qd_from = self._date_from.date()
        qd_to = self._date_to.date()
        return {
            'date_from': date(qd_from.year(), qd_from.month(), qd_from.day()),
            'date_to': date(qd_to.year(), qd_to.month(), qd_to.day()),
            'min_r': self._min_r.value(),
            'model': self._model.currentData(),
            'direction': self._direction.currentData(),
            'ticker': self._ticker.currentData(),
        }

    def set_loading(self, loading: bool):
        """Toggle load button state."""
        self._load_btn.setEnabled(not loading)
        self._load_btn.setText("LOADING..." if loading else "LOAD HIGHLIGHTS")

    def set_tickers(self, tickers: List[str]):
        """Populate ticker dropdown."""
        current = self._ticker.currentData()
        self._ticker.clear()
        self._ticker.addItem("All Tickers", None)
        for t in tickers:
            self._ticker.addItem(t, t)
        # Restore selection if possible
        if current:
            idx = self._ticker.findData(current)
            if idx >= 0:
                self._ticker.setCurrentIndex(idx)

    def update_results_info(self, count: int):
        """Update results count label."""
        if count > 0:
            self._results_label.setText(f"{count} highlights found")
            self._results_label.setStyleSheet("color: #089981; font-size: 11px;")
        else:
            self._results_label.setText("No highlights found")
            self._results_label.setStyleSheet("color: #787B86; font-size: 11px;")

    def set_date_range(self, min_date: Optional[date], max_date: Optional[date]):
        """Set date picker range from DB data."""
        if min_date:
            self._date_from.setDate(QDate(min_date.year, min_date.month, min_date.day))
        if max_date:
            self._date_to.setDate(QDate(max_date.year, max_date.month, max_date.day))
