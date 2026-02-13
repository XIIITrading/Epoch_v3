"""
Epoch Trading System - Filter Panel (Sidebar)
Date, ticker, model filters, toggles, load button, queue info.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QCheckBox, QPushButton, QProgressBar, QSpinBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from datetime import date, timedelta


class FilterPanel(QFrame):
    """Sidebar filter panel with date range, ticker, model, and queue controls."""

    load_requested = pyqtSignal(dict)      # Emitted with filter dict
    shuffle_requested = pyqtSignal()       # Emitted when shuffle clicked
    jump_requested = pyqtSignal(int)       # Emitted with 0-indexed trade number

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: #16213e;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Epoch Review")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)

        caption = QLabel("Flash Card Training System")
        caption.setFont(QFont("Segoe UI", 10))
        caption.setStyleSheet("color: #888888;")
        layout.addWidget(caption)

        self._add_separator(layout)

        # --- Filters ---
        filters_label = QLabel("Filters")
        filters_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        filters_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(filters_label)

        # Date range
        date_row = QHBoxLayout()
        date_from_layout = QVBoxLayout()
        date_from_label = QLabel("From")
        date_from_label.setStyleSheet("color: #888888; font-size: 10pt;")
        date_from_layout.addWidget(date_from_label)
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addDays(-30))
        self._date_from.setStyleSheet(self._date_style())
        date_from_layout.addWidget(self._date_from)
        date_row.addLayout(date_from_layout)

        date_to_layout = QVBoxLayout()
        date_to_label = QLabel("To")
        date_to_label.setStyleSheet("color: #888888; font-size: 10pt;")
        date_to_layout.addWidget(date_to_label)
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet(self._date_style())
        date_to_layout.addWidget(self._date_to)
        date_row.addLayout(date_to_layout)
        layout.addLayout(date_row)

        # Ticker
        ticker_label = QLabel("Ticker")
        ticker_label.setStyleSheet("color: #888888; font-size: 10pt;")
        layout.addWidget(ticker_label)
        self._ticker = QComboBox()
        self._ticker.addItem("All Tickers")
        self._ticker.setStyleSheet(self._combo_style())
        layout.addWidget(self._ticker)

        # Model
        model_label = QLabel("Model")
        model_label.setStyleSheet("color: #888888; font-size: 10pt;")
        layout.addWidget(model_label)
        self._model = QComboBox()
        self._model.addItems(["All Models", "EPCH1", "EPCH2", "EPCH3", "EPCH4"])
        self._model.setStyleSheet(self._combo_style())
        layout.addWidget(self._model)

        self._add_separator(layout)

        # Toggles
        self._unreviewed = QCheckBox("Unreviewed Only")
        self._unreviewed.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._unreviewed)

        self._ai_validated = QCheckBox("AI Validated")
        self._ai_validated.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._ai_validated)

        # Load button
        self._load_btn = QPushButton("Load Trades")
        self._load_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._load_btn.setStyleSheet("""
            QPushButton {
                background-color: #00C853; color: #ffffff;
                border: none; border-radius: 6px; padding: 10px;
            }
            QPushButton:hover { background-color: #00E676; }
            QPushButton:pressed { background-color: #00B848; }
            QPushButton:disabled { background-color: #555555; }
        """)
        self._load_btn.clicked.connect(self._on_load)
        layout.addWidget(self._load_btn)

        self._add_separator(layout)

        # --- Queue Info ---
        self._queue_frame = QFrame()
        self._queue_frame.setVisible(False)
        queue_layout = QVBoxLayout(self._queue_frame)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(4)

        self._queue_size_label = QLabel("Queue: 0")
        self._queue_size_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._queue_size_label.setStyleSheet("color: #e0e0e0;")
        queue_layout.addWidget(self._queue_size_label)

        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4e; border: 1px solid #333;
                border-radius: 4px; text-align: center; color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #00C853; border-radius: 3px;
            }
        """)
        queue_layout.addWidget(self._progress)

        self._progress_label = QLabel("0 of 0 reviewed")
        self._progress_label.setFont(QFont("Segoe UI", 10))
        self._progress_label.setStyleSheet("color: #888888;")
        queue_layout.addWidget(self._progress_label)

        # Shuffle button
        self._shuffle_btn = QPushButton("Shuffle Queue")
        self._shuffle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 6px;
            }
            QPushButton:hover { background-color: #3a3a5e; }
        """)
        self._shuffle_btn.clicked.connect(self.shuffle_requested.emit)
        queue_layout.addWidget(self._shuffle_btn)

        # Jump to trade
        jump_row = QHBoxLayout()
        jump_label = QLabel("Jump to #")
        jump_label.setStyleSheet("color: #888888;")
        jump_row.addWidget(jump_label)

        self._jump_spin = QSpinBox()
        self._jump_spin.setMinimum(1)
        self._jump_spin.setMaximum(1)
        self._jump_spin.setStyleSheet("""
            QSpinBox {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 2px;
            }
        """)
        jump_row.addWidget(self._jump_spin)

        jump_btn = QPushButton("Go")
        jump_btn.setFixedWidth(40)
        jump_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 4px;
            }
            QPushButton:hover { background-color: #3a3a5e; }
        """)
        jump_btn.clicked.connect(self._on_jump)
        jump_row.addWidget(jump_btn)

        queue_layout.addLayout(jump_row)
        layout.addWidget(self._queue_frame)

        # Spacer
        layout.addStretch()

        # Footer
        self._add_separator(layout)
        footer = QLabel("XIII Trading LLC")
        footer.setFont(QFont("Segoe UI", 10))
        footer.setStyleSheet("color: #555555; font-style: italic;")
        layout.addWidget(footer)

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #333333;")
        layout.addWidget(sep)

    def _date_style(self) -> str:
        return """
            QDateEdit {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 4px;
            }
            QDateEdit::drop-down { border: none; }
        """

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 4px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2a2a4e; color: #e0e0e0;
                selection-background-color: #3a3a5e;
            }
        """

    def _on_load(self):
        """Emit load_requested with current filter values."""
        qd_from = self._date_from.date()
        qd_to = self._date_to.date()

        filters = {
            'date_from': date(qd_from.year(), qd_from.month(), qd_from.day()),
            'date_to': date(qd_to.year(), qd_to.month(), qd_to.day()),
            'ticker': None if self._ticker.currentText() == "All Tickers" else self._ticker.currentText(),
            'model': None if self._model.currentText() == "All Models" else self._model.currentText(),
            'unreviewed_only': self._unreviewed.isChecked(),
            'ai_validated_only': self._ai_validated.isChecked(),
        }
        self.load_requested.emit(filters)

    def _on_jump(self):
        """Emit jump_requested with 0-indexed trade number."""
        self.jump_requested.emit(self._jump_spin.value() - 1)

    def set_loading(self, loading: bool):
        """Toggle loading state on the load button."""
        self._load_btn.setEnabled(not loading)
        self._load_btn.setText("Loading..." if loading else "Load Trades")

    def set_tickers(self, tickers: list):
        """Update available tickers in the dropdown."""
        current = self._ticker.currentText()
        self._ticker.clear()
        self._ticker.addItem("All Tickers")
        self._ticker.addItems(tickers)
        # Restore selection if still valid
        idx = self._ticker.findText(current)
        if idx >= 0:
            self._ticker.setCurrentIndex(idx)

    def update_queue_info(self, current_index: int, total: int):
        """Update queue progress display."""
        self._queue_frame.setVisible(total > 0)
        self._queue_size_label.setText(f"Queue: {total}")

        pct = int((current_index / total) * 100) if total > 0 else 0
        self._progress.setValue(pct)
        self._progress_label.setText(f"{current_index} of {total} reviewed")

        self._jump_spin.setMaximum(max(1, total))

    def get_filters(self) -> dict:
        """Get current filter values."""
        qd_from = self._date_from.date()
        qd_to = self._date_to.date()
        return {
            'date_from': date(qd_from.year(), qd_from.month(), qd_from.day()),
            'date_to': date(qd_to.year(), qd_to.month(), qd_to.day()),
            'ticker': None if self._ticker.currentText() == "All Tickers" else self._ticker.currentText(),
            'model': None if self._model.currentText() == "All Models" else self._model.currentText(),
            'unreviewed_only': self._unreviewed.isChecked(),
            'ai_validated_only': self._ai_validated.isChecked(),
        }
