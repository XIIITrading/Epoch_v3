"""
Ticker Dialog
Epoch Trading System v1 - XIII Trading LLC

Dialog for adding new tickers to the Entry Qualifier.
"""
import sys
from pathlib import Path

# Ensure entry_qualifier is at the front of sys.path
_entry_qualifier_dir = str(Path(__file__).parent.parent.resolve())
if _entry_qualifier_dir not in sys.path:
    sys.path.insert(0, _entry_qualifier_dir)
elif sys.path[0] != _entry_qualifier_dir:
    sys.path.remove(_entry_qualifier_dir)
    sys.path.insert(0, _entry_qualifier_dir)

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from data.data_worker import TickerValidationWorker
from ui.styles import COLORS


class TickerDialog(QDialog):
    """
    Dialog for adding a new ticker.

    Validates the ticker against the Polygon API before accepting.
    """

    # Signal emitted when a valid ticker is added
    ticker_added = pyqtSignal(str)  # ticker

    def __init__(self, existing_tickers: list = None, parent=None):
        super().__init__(parent)
        self.existing_tickers = [t.upper() for t in (existing_tickers or [])]
        self._validation_worker = None

        self.setWindowTitle("Add Ticker")
        self.setFixedSize(350, 150)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Label
        label = QLabel("Enter ticker symbol:")
        font = QFont()
        font.setPointSize(11)
        label.setFont(font)
        layout.addWidget(label)

        # Input field
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("e.g., SPY, QQQ, AAPL")
        self.ticker_input.setMaxLength(10)
        self.ticker_input.returnPressed.connect(self._on_add_clicked)
        font = QFont()
        font.setPointSize(11)
        self.ticker_input.setFont(font)
        layout.addWidget(self.ticker_input)

        # Progress bar (hidden initially)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("Add")
        self.add_btn.setDefault(True)
        self.add_btn.clicked.connect(self._on_add_clicked)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.add_btn)

        layout.addLayout(button_layout)

        # Focus the input
        self.ticker_input.setFocus()

    def _on_add_clicked(self):
        """Handle add button click."""
        ticker = self.ticker_input.text().upper().strip()

        if not ticker:
            self._show_error("Please enter a ticker symbol.")
            return

        # Check if already exists
        if ticker in self.existing_tickers:
            self._show_error(f"'{ticker}' is already being tracked.")
            return

        # Basic format validation
        if not ticker.isalpha() or len(ticker) > 5:
            self._show_error("Invalid ticker format. Use 1-5 letters (e.g., AAPL).")
            return

        # Disable UI and show progress
        self._set_loading(True)

        # Start validation worker
        self._validation_worker = TickerValidationWorker(ticker, self)
        self._validation_worker.validation_complete.connect(self._on_validation_complete)
        self._validation_worker.start()

    def _on_validation_complete(self, ticker: str, is_valid: bool, error_msg: str):
        """Handle validation result."""
        self._set_loading(False)

        if is_valid:
            self.ticker_added.emit(ticker)
            self.accept()
        else:
            self._show_error(error_msg or f"Invalid ticker: {ticker}")

    def _set_loading(self, loading: bool):
        """Set loading state."""
        self.ticker_input.setEnabled(not loading)
        self.add_btn.setEnabled(not loading)
        self.cancel_btn.setEnabled(not loading)

        if loading:
            self.progress.show()
            self.add_btn.setText("Validating...")
        else:
            self.progress.hide()
            self.add_btn.setText("Add")

    def _show_error(self, message: str):
        """Show error message."""
        QMessageBox.warning(self, "Error", message)
        self.ticker_input.setFocus()
        self.ticker_input.selectAll()

    def closeEvent(self, event):
        """Handle dialog close."""
        # Stop any running worker
        if self._validation_worker and self._validation_worker.isRunning():
            self._validation_worker.terminate()
            self._validation_worker.wait()
        super().closeEvent(event)
