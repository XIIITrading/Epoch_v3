"""
Terminal Panel Widget
Epoch Trading System v3.0 - XIII Trading LLC

Terminal panel for displaying DOW AI dual-pass responses.
Shows the trader's perspective (Pass 1) and system recommendation (Pass 2).
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from datetime import datetime

from ui.styles import COLORS


class TerminalPanel(QFrame):
    """
    Terminal panel for displaying DOW AI dual-pass responses.

    v3.0 Dual-Pass Display:
    - Shows trader's perspective (Pass 1) as header context
    - Shows system recommendation (Pass 2) with backtested edges

    Fixed height panel that shows:
    - Header with "DOW AI TERMINAL v3.0" title and status indicator
    - Response text area (read-only) with monospace font
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self.setMinimumHeight(200)  # Minimum height; stretches to fill remaining space
        self._setup_ui()

    def _setup_ui(self):
        """Set up the terminal panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # ===== Header Row =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Title
        self.title_label = QLabel("DOW AI TERMINAL v3.0")
        self.title_label.setObjectName("terminalTitle")
        title_font = QFont("Consolas", 11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("terminalStatus")
        self.status_label.setFont(QFont("Consolas", 10))
        self.status_label.setStyleSheet(f"color: {COLORS['status_live']};")

        # Timestamp
        self.timestamp_label = QLabel("")
        self.timestamp_label.setObjectName("terminalTimestamp")
        self.timestamp_label.setFont(QFont("Consolas", 10))
        self.timestamp_label.setStyleSheet(f"color: {COLORS['text_muted']};")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.timestamp_label)

        layout.addLayout(header_layout)

        # ===== Response Text Area =====
        self.response_text = QTextEdit()
        self.response_text.setObjectName("terminalText")
        self.response_text.setReadOnly(True)
        self.response_text.setFont(QFont("Consolas", 11))
        self.response_text.setPlaceholderText(
            "DUAL-PASS ANALYSIS v3.0\n\n"
            "1. Enter your perspective in the notes field above (Pass 1)\n"
            "2. Click 'Ask DOW AI' to get system recommendation (Pass 2)\n\n"
            "The system will:\n"
            "  - Compare your read to the live indicator data\n"
            "  - Apply backtested edges (H1 Structure +36pp, etc.)\n"
            "  - Provide a recommendation with confidence level"
        )
        self.response_text.setStyleSheet(f"""
            QTextEdit#terminalText {{
                background-color: #0a0a0a;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {COLORS['button_primary']};
            }}
        """)

        layout.addWidget(self.response_text)

        # Set panel style
        self.setStyleSheet(f"""
            QFrame#terminalPanel {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

    def set_loading(self, ticker: str, direction: str = None):
        """
        Show loading state while waiting for AI response.

        Args:
            ticker: The ticker being analyzed
            direction: Optional direction being analyzed
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.status_label.setText("Analyzing...")
        self.status_label.setStyleSheet(f"color: {COLORS['status_paused']};")
        self.timestamp_label.setText(timestamp)

        context = f"{ticker}"
        if direction:
            context += f" | {direction}"

        self.response_text.setPlainText(
            f"[{timestamp}] Starting DOW AI query for {context}...\n"
            f"{'-' * 50}\n"
        )

    def set_response(self, response: str, ticker: str, direction: str, user_notes: str = ""):
        """
        Display the AI dual-pass response.

        Args:
            response: The AI-generated response text (Pass 2)
            ticker: The analyzed ticker
            direction: The trade direction analyzed
            user_notes: User's perspective (Pass 1) - optional for backwards compat
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.status_label.setText("Complete")
        self.status_label.setStyleSheet(f"color: {COLORS['status_live']};")
        self.timestamp_label.setText(timestamp)

        # Format the response with dual-pass header
        header = f"[{timestamp}] {ticker} | {direction} | DUAL-PASS ANALYSIS"
        separator = "=" * 60

        # Build formatted response
        parts = [header, separator]

        # Include user notes if provided
        if user_notes:
            parts.append("")
            parts.append("PASS 1 - YOUR PERSPECTIVE:")
            parts.append("-" * 40)
            parts.append(user_notes)
            parts.append("")
            parts.append("PASS 2 - SYSTEM RECOMMENDATION:")
            parts.append("-" * 40)
        else:
            parts.append("")
            parts.append("SYSTEM RECOMMENDATION:")
            parts.append("-" * 40)

        parts.append("")
        parts.append(response)

        formatted_response = "\n".join(parts)

        self.response_text.setPlainText(formatted_response)

        # Scroll to top
        cursor = self.response_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.response_text.setTextCursor(cursor)

    def set_error(self, error_msg: str):
        """
        Display an error message.

        Args:
            error_msg: The error message to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"color: {COLORS['status_error']};")
        self.timestamp_label.setText(timestamp)

        self.response_text.setPlainText(
            f"ERROR [{timestamp}]\n"
            f"{'-' * 50}\n\n"
            f"{error_msg}\n\n"
            "Please check:\n"
            "  - Network connection\n"
            "  - API key configuration\n"
            "  - Supabase connectivity"
        )

    def clear(self):
        """Clear the terminal and reset to ready state."""
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['status_live']};")
        self.timestamp_label.setText("")
        self.response_text.clear()

    def append_message(self, message: str):
        """
        Append a message to the terminal (for logging/debugging).

        Args:
            message: The message to append
        """
        current = self.response_text.toPlainText()
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_text = f"{current}\n[{timestamp}] {message}"
        self.response_text.setPlainText(new_text)

        # Scroll to bottom
        cursor = self.response_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.response_text.setTextCursor(cursor)
