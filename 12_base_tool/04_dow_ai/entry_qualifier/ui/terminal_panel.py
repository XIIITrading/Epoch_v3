"""
Terminal Panel Widget
Epoch Trading System v1 - XIII Trading LLC

Terminal panel for displaying DOW AI responses.
Shows the most recent AI analysis with timestamp and status.
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
    Terminal panel for displaying DOW AI responses.

    Fixed height panel that shows:
    - Header with "DOW AI TERMINAL" title and status indicator
    - Response text area (read-only) with monospace font
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self.setFixedHeight(260)
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
        self.title_label = QLabel("DOW AI TERMINAL")
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
            "Select a ticker and click 'Ask DOW AI' for entry analysis...\n\n"
            "The AI will analyze:\n"
            "  - Live 25-bar indicator data\n"
            "  - Historical performance data\n"
            "  - Validated indicator edges"
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

    def set_response(self, response: str, ticker: str, direction: str):
        """
        Display the AI response.

        Args:
            response: The AI-generated response text
            ticker: The analyzed ticker
            direction: The trade direction analyzed
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.status_label.setText("Complete")
        self.status_label.setStyleSheet(f"color: {COLORS['status_live']};")
        self.timestamp_label.setText(timestamp)

        # Format the response with header
        header = f"[{timestamp}] {ticker} | {direction}"
        separator = "-" * 50

        formatted_response = f"{header}\n{separator}\n\n{response}"

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
