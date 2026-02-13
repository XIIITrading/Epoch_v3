"""
Global Control Panel Widget
Epoch Trading System v3.0 - XIII Trading LLC

Control panel for DOW AI dual-pass queries with:
- Ticker selection
- Direction radio buttons
- User notes input (Pass 1 - trader's perspective)
- Ask DOW AI button (triggers Pass 2 with backtested context)
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QRadioButton, QButtonGroup, QPushButton,
    QTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List

from ui.styles import COLORS


class GlobalControlPanel(QFrame):
    """
    Global control panel for DOW AI dual-pass queries.

    v3.0 Dual-Pass System:
    - Pass 1: User enters their perspective/notes in the text area
    - Pass 2: System runs analysis with backtested context

    Emits ai_query_requested signal with (ticker, direction, user_notes)
    when the Ask DOW AI button is clicked.
    """

    # Signal emitted when AI query is requested (v3.0: includes user notes)
    ai_query_requested = pyqtSignal(str, str, str)  # ticker, direction, user_notes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("globalControlPanel")
        self.setFixedHeight(120)  # Compact height for notes input
        self._setup_ui()

    def _setup_ui(self):
        """Set up the control panel UI with dual-pass support."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 8, 15, 8)
        main_layout.setSpacing(8)

        # ===== Top Row: Ticker, Direction, Button =====
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        # Ticker Selection
        ticker_layout = QHBoxLayout()
        ticker_layout.setSpacing(8)

        ticker_label = QLabel("Ticker:")
        ticker_label.setObjectName("controlLabel")
        ticker_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.ticker_combo = QComboBox()
        self.ticker_combo.setObjectName("tickerCombo")
        self.ticker_combo.setMinimumWidth(100)
        self.ticker_combo.setMaximumWidth(130)
        self.ticker_combo.setPlaceholderText("Select")
        self.ticker_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['border_light']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['button_primary']};
            }}
        """)

        ticker_layout.addWidget(ticker_label)
        ticker_layout.addWidget(self.ticker_combo)
        top_row.addLayout(ticker_layout)

        # Separator
        top_row.addWidget(self._create_separator())

        # Direction Selection
        direction_layout = QHBoxLayout()
        direction_layout.setSpacing(12)

        direction_label = QLabel("Direction:")
        direction_label.setObjectName("controlLabel")
        direction_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        direction_layout.addWidget(direction_label)

        self.direction_group = QButtonGroup(self)
        for i, direction in enumerate(['LONG', 'SHORT']):
            rb = QRadioButton(direction)
            rb.setObjectName("directionRadio")

            # Color-code direction
            if direction == 'LONG':
                color = COLORS['positive']
            else:
                color = COLORS['negative']

            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {color};
                    spacing: 5px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QRadioButton::indicator:unchecked {{
                    border: 2px solid {COLORS['border_light']};
                    border-radius: 8px;
                    background-color: transparent;
                }}
                QRadioButton::indicator:checked {{
                    border: 2px solid {color};
                    border-radius: 8px;
                    background-color: {color};
                }}
            """)

            self.direction_group.addButton(rb, i)
            direction_layout.addWidget(rb)
            if i == 0:
                rb.setChecked(True)

        top_row.addLayout(direction_layout)

        # Stretch to push button to right
        top_row.addStretch()

        # Ask DOW AI Button
        self.ask_btn = QPushButton("Ask DOW AI")
        self.ask_btn.setObjectName("askButton")
        self.ask_btn.setFixedWidth(120)
        self.ask_btn.setFixedHeight(34)
        self.ask_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ask_btn.setStyleSheet(f"""
            QPushButton#askButton {{
                background-color: {COLORS['bg_header']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton#askButton:hover {{
                background-color: {COLORS['button_hover']};
                border-color: {COLORS['positive']};
            }}
            QPushButton#askButton:pressed {{
                background-color: {COLORS['button_pressed']};
            }}
            QPushButton#askButton:disabled {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_muted']};
                border-color: {COLORS['border']};
            }}
        """)
        self.ask_btn.clicked.connect(self._on_ask_clicked)
        top_row.addWidget(self.ask_btn)

        main_layout.addLayout(top_row)

        # ===== Bottom Row: User Notes Input (Pass 1) =====
        notes_layout = QHBoxLayout()
        notes_layout.setSpacing(8)

        notes_label = QLabel("Your Perspective (Pass 1):")
        notes_label.setObjectName("controlLabel")
        notes_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        notes_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        self.notes_input = QTextEdit()
        self.notes_input.setObjectName("notesInput")
        self.notes_input.setPlaceholderText(
            "Enter your read of the market... (e.g., 'H1 bullish structure, volume delta positive, "
            "SMA spread widening. Looking for continuation.')"
        )
        self.notes_input.setMaximumHeight(45)
        self.notes_input.setFont(QFont("Consolas", 9))
        self.notes_input.setStyleSheet(f"""
            QTextEdit#notesInput {{
                background-color: #0a0a0a;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QTextEdit#notesInput:focus {{
                border-color: {COLORS['border_light']};
            }}
        """)

        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_input, 1)

        main_layout.addLayout(notes_layout)

        # Set panel style
        self.setStyleSheet(f"""
            QFrame#globalControlPanel {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        return sep

    def update_tickers(self, tickers: List[str]):
        """
        Update the ticker dropdown with the current active tickers.

        Args:
            tickers: List of ticker symbols currently loaded in Entry Qualifier
        """
        current = self.ticker_combo.currentText()
        self.ticker_combo.clear()

        if tickers:
            self.ticker_combo.addItems(sorted(tickers))
            # Restore previous selection if still valid
            if current in tickers:
                self.ticker_combo.setCurrentText(current)
            else:
                self.ticker_combo.setCurrentIndex(0)

        # Disable button if no tickers
        self.ask_btn.setEnabled(len(tickers) > 0)

    def _on_ask_clicked(self):
        """Handle Ask DOW AI button click."""
        ticker = self.ticker_combo.currentText()
        if not ticker:
            return

        # Get selected direction
        direction_btn = self.direction_group.checkedButton()
        direction = direction_btn.text() if direction_btn else 'LONG'

        # Get user notes (Pass 1)
        user_notes = self.notes_input.toPlainText().strip()

        self.ai_query_requested.emit(ticker, direction, user_notes)

    def get_current_selection(self) -> tuple:
        """
        Get the current selection (ticker, direction, user_notes).

        Returns:
            Tuple of (ticker, direction, user_notes)
        """
        ticker = self.ticker_combo.currentText()

        direction_btn = self.direction_group.checkedButton()
        direction = direction_btn.text() if direction_btn else 'LONG'

        user_notes = self.notes_input.toPlainText().strip()

        return ticker, direction, user_notes

    def get_user_notes(self) -> str:
        """Get the user's perspective notes."""
        return self.notes_input.toPlainText().strip()

    def clear_notes(self):
        """Clear the user notes input."""
        self.notes_input.clear()

    def set_enabled(self, enabled: bool):
        """Enable or disable the control panel."""
        self.ticker_combo.setEnabled(enabled)
        self.notes_input.setEnabled(enabled)
        for btn in self.direction_group.buttons():
            btn.setEnabled(enabled)
        self.ask_btn.setEnabled(enabled and bool(self.ticker_combo.currentText()))
