"""
Epoch Trading System - Bookmap Panel
Displays Bookmap snapshot images in a collapsible section.
"""

import logging
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl

logger = logging.getLogger(__name__)


class BookmapPanel(QFrame):
    """Collapsible bookmap snapshot display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._network.finished.connect(self._on_image_loaded)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Collapsible toggle
        self._toggle_btn = QPushButton("> Bookmap Snapshot")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(False)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px;
                padding: 6px; text-align: left; font-weight: bold;
            }
            QPushButton:checked { background-color: #3a3a5e; }
        """)
        self._toggle_btn.toggled.connect(self._toggle_content)
        layout.addWidget(self._toggle_btn)

        # Content frame
        self._content = QFrame()
        self._content.setVisible(False)
        self._content.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 8px;")
        content_layout = QVBoxLayout(self._content)

        self._image_label = QLabel("Loading bookmap image...")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumHeight(200)
        self._image_label.setStyleSheet("color: #888888;")
        content_layout.addWidget(self._image_label)

        self._caption = QLabel("Bookmap snapshot at trade entry")
        self._caption.setFont(QFont("Segoe UI", 10))
        self._caption.setStyleSheet("color: #888888;")
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self._caption)

        layout.addWidget(self._content)

    def _toggle_content(self, checked: bool):
        self._content.setVisible(checked)
        arrow = "v" if checked else ">"
        self._toggle_btn.setText(f"{arrow} Bookmap Snapshot")

    def update_bookmap(self, bookmap_url: str = None):
        """Load and display bookmap image from URL."""
        if not bookmap_url:
            self.setVisible(False)
            return

        self.setVisible(True)
        self._image_label.setText("Loading bookmap image...")

        try:
            request = QNetworkRequest(QUrl(bookmap_url))
            self._network.get(request)
        except Exception as e:
            logger.error(f"Failed to request bookmap: {e}")
            self._image_label.setText(f"Failed to load: {e}")

    def _on_image_loaded(self, reply: QNetworkReply):
        """Handle image download completion."""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._image_label.setText(f"Failed to load image: {reply.errorString()}")
            reply.deleteLater()
            return

        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)

        if not pixmap.isNull():
            target_width = self._image_label.width() if self._image_label.width() > 200 else 800
            scaled = pixmap.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)
            self._image_label.setPixmap(scaled)
        else:
            self._image_label.setText("Failed to decode image")

        reply.deleteLater()

    def clear(self):
        """Reset panel."""
        self.setVisible(False)
        self._image_label.clear()
        self._image_label.setText("Loading bookmap image...")
        self._toggle_btn.setChecked(False)
