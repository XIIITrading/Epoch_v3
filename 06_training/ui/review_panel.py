"""
Epoch Trading System - Review Panel
Trade review form with simplified inputs:
  Box 1: Accuracy (True/False)
  Box 2: Quality (True/False)
  Box 3: Stop Placement (single select: Prior Candle / Two Candle / ATR Stop / Zone Edge)
  Box 4: Context (single select: With Trend / Counter Trend / In Range / Break Range / Wick Stop)
  Box 5: Post Stop Win (True/False)
  Notes + Next Trade button
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QCheckBox, QComboBox, QTextEdit, QPushButton, QButtonGroup,
    QRadioButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics, TradeReview

# Stop placement options: display label -> DB value
STOP_OPTIONS = [
    ("Prior Candle", "prior_candle"),
    ("Two Candle", "two_candle"),
    ("ATR Stop", "atr_stop"),
    ("Zone Edge", "zone_edge"),
]

# Context options: display label -> DB value
CONTEXT_OPTIONS = [
    ("With Trend", "with_trend"),
    ("Counter Trend", "counter_trend"),
    ("In Range", "in_range"),
    ("Break Range", "break_range"),
    ("Wick Stop", "wick_stop"),
]

# Shared styles
GROUP_STYLE = """
    QGroupBox {
        color: #e0e0e0; border: 1px solid #333;
        border-radius: 4px; margin-top: 8px; padding-top: 16px;
        font-size: 10pt;
    }
    QGroupBox::title { subcontrol-position: top left; padding: 0 4px; }
"""

CHECKBOX_STYLE = "QCheckBox { color: #e0e0e0; font-size: 10pt; }"
RADIO_STYLE = "QRadioButton { color: #e0e0e0; font-size: 10pt; }"


class ReviewPanel(QFrame):
    """Trade review form with checkboxes, radio selects, notes, and navigation."""

    next_requested = pyqtSignal()  # Emitted when Next Trade is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trade = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Title
        title = QLabel("Trade Review")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)

        # Review inputs in a horizontal row
        groups_row = QHBoxLayout()

        # --- Box 0: Trade (True/False) - would I have taken this trade? ---
        trade_group = QGroupBox("Trade")
        trade_group.setStyleSheet(GROUP_STYLE)
        trade_layout = QVBoxLayout(trade_group)
        self._would_trade = QCheckBox("True")
        self._would_trade.setStyleSheet(CHECKBOX_STYLE)
        trade_layout.addWidget(self._would_trade)
        trade_layout.addStretch()
        groups_row.addWidget(trade_group)

        # --- Box 1: Accuracy (True/False) ---
        accuracy_group = QGroupBox("Accuracy")
        accuracy_group.setStyleSheet(GROUP_STYLE)
        acc_layout = QVBoxLayout(accuracy_group)
        self._accuracy = QCheckBox("True")
        self._accuracy.setStyleSheet(CHECKBOX_STYLE)
        acc_layout.addWidget(self._accuracy)
        acc_layout.addStretch()
        groups_row.addWidget(accuracy_group)

        # --- Box 2: Quality (True/False) ---
        quality_group = QGroupBox("Quality")
        quality_group.setStyleSheet(GROUP_STYLE)
        qual_layout = QVBoxLayout(quality_group)
        self._quality = QCheckBox("True")
        self._quality.setStyleSheet(CHECKBOX_STYLE)
        qual_layout.addWidget(self._quality)
        qual_layout.addStretch()
        groups_row.addWidget(quality_group)

        # --- Box 3: Stop Placement (radio single-select) ---
        stop_group = QGroupBox("Stop Placement")
        stop_group.setStyleSheet(GROUP_STYLE)
        stop_layout = QVBoxLayout(stop_group)
        self._stop_group = QButtonGroup(self)
        self._stop_group.setExclusive(True)
        self._stop_radios = {}
        for label, value in STOP_OPTIONS:
            radio = QRadioButton(label)
            radio.setStyleSheet(RADIO_STYLE)
            self._stop_group.addButton(radio)
            self._stop_radios[value] = radio
            stop_layout.addWidget(radio)
        stop_layout.addStretch()
        groups_row.addWidget(stop_group)

        # --- Box 4: Context (radio single-select) ---
        context_group = QGroupBox("Context")
        context_group.setStyleSheet(GROUP_STYLE)
        ctx_layout = QVBoxLayout(context_group)
        self._context_group = QButtonGroup(self)
        self._context_group.setExclusive(True)
        self._context_radios = {}
        for label, value in CONTEXT_OPTIONS:
            radio = QRadioButton(label)
            radio.setStyleSheet(RADIO_STYLE)
            self._context_group.addButton(radio)
            self._context_radios[value] = radio
            ctx_layout.addWidget(radio)
        ctx_layout.addStretch()
        groups_row.addWidget(context_group)

        # --- Box 5: Post Stop Win (True/False) ---
        psw_group = QGroupBox("Post Stop Win")
        psw_group.setStyleSheet(GROUP_STYLE)
        psw_layout = QVBoxLayout(psw_group)
        self._post_stop_win = QCheckBox("True")
        self._post_stop_win.setStyleSheet(CHECKBOX_STYLE)
        psw_layout.addWidget(self._post_stop_win)
        psw_layout.addStretch()
        groups_row.addWidget(psw_group)

        layout.addLayout(groups_row)

        # Notes
        notes_label = QLabel("Notes:")
        notes_label.setFont(QFont("Segoe UI", 10))
        notes_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(notes_label)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(80)
        self._notes.setPlaceholderText("What did you learn from this trade?")
        self._notes.setStyleSheet("""
            QTextEdit {
                background-color: #16213e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 6px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self._notes)

        # Next Trade button
        self._next_btn = QPushButton("Next Trade  ->")
        self._next_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._next_btn.setStyleSheet("""
            QPushButton {
                background-color: #00C853; color: #ffffff;
                border: none; border-radius: 6px; padding: 10px;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #00E676; }
            QPushButton:pressed { background-color: #00B848; }
        """)
        self._next_btn.clicked.connect(self.next_requested.emit)
        layout.addWidget(self._next_btn)

    def _get_selected_stop(self) -> Optional[str]:
        """Get selected stop placement value, or None if nothing selected."""
        for value, radio in self._stop_radios.items():
            if radio.isChecked():
                return value
        return None

    def _get_selected_context(self) -> Optional[str]:
        """Get selected context value, or None if nothing selected."""
        for value, radio in self._context_radios.items():
            if radio.isChecked():
                return value
        return None

    def get_review(self, trade: TradeWithMetrics) -> TradeReview:
        """Build TradeReview from current widget state."""
        actual_outcome = 'winner' if trade.is_winner else 'loser'

        return TradeReview(
            trade_id=trade.trade_id,
            actual_outcome=actual_outcome,
            notes=self._notes.toPlainText(),
            would_trade=self._would_trade.isChecked(),
            accuracy=self._accuracy.isChecked(),
            quality=self._quality.isChecked(),
            stop_placement=self._get_selected_stop(),
            context=self._get_selected_context(),
            post_stop_win=self._post_stop_win.isChecked(),
        )

    def load_review(self, review: TradeReview):
        """Populate widgets from an existing review."""
        self._would_trade.setChecked(review.would_trade)
        self._accuracy.setChecked(review.accuracy)
        self._quality.setChecked(review.quality)
        self._post_stop_win.setChecked(review.post_stop_win)

        # Stop placement radio
        self._stop_group.setExclusive(False)
        for radio in self._stop_radios.values():
            radio.setChecked(False)
        self._stop_group.setExclusive(True)
        if review.stop_placement and review.stop_placement in self._stop_radios:
            self._stop_radios[review.stop_placement].setChecked(True)

        # Context radio
        self._context_group.setExclusive(False)
        for radio in self._context_radios.values():
            radio.setChecked(False)
        self._context_group.setExclusive(True)
        if review.context and review.context in self._context_radios:
            self._context_radios[review.context].setChecked(True)

        self._notes.setPlainText(review.notes or '')

    def clear(self):
        """Reset all fields to defaults."""
        self._would_trade.setChecked(False)
        self._accuracy.setChecked(False)
        self._quality.setChecked(False)
        self._post_stop_win.setChecked(False)

        # Clear stop radios
        self._stop_group.setExclusive(False)
        for radio in self._stop_radios.values():
            radio.setChecked(False)
        self._stop_group.setExclusive(True)

        # Clear context radios
        self._context_group.setExclusive(False)
        for radio in self._context_radios.values():
            radio.setChecked(False)
        self._context_group.setExclusive(True)

        self._notes.clear()
