"""
Epoch Trading System - Chart Renderer for Trade Reel
Converts Plotly figures to QPixmap for PyQt6 display.
Adapted from 06_training/ui/chart_renderer.py.
"""

import tempfile
import os
import logging
from PyQt6.QtWidgets import QLabel, QSizePolicy, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

RENDER_WIDTH = 1600
CHART_HEIGHT = 450
RENDER_SCALE = 2


class AspectRatioLabel(QLabel):
    """QLabel that maintains aspect ratio of its pixmap during resize."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aspect_ratio = 0.5
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background-color: #1E222D; border: 1px solid #2A2E39;")
        self.setText("Loading chart...")

    def setPixmap(self, pixmap: QPixmap):
        if not pixmap.isNull() and pixmap.width() > 0:
            self._aspect_ratio = pixmap.height() / pixmap.width()
        super().setPixmap(pixmap)
        self.updateGeometry()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width: int) -> int:
        return int(width * self._aspect_ratio)

    def sizeHint(self) -> QSize:
        w = self.width() if self.width() > 100 else 1400
        return QSize(w, int(w * self._aspect_ratio))

    def minimumSizeHint(self) -> QSize:
        return QSize(300, int(300 * self._aspect_ratio))


def render_chart_to_label(
    fig: go.Figure,
    label: QLabel,
    width: int = RENDER_WIDTH,
    height: int = CHART_HEIGHT,
    scale: int = RENDER_SCALE,
):
    """Render Plotly figure to QLabel as PNG."""
    fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)

    try:
        fig.write_image(temp_path, format='png', width=width, height=height, scale=scale)
        pixmap = QPixmap(temp_path)

        if not pixmap.isNull():
            label.setPixmap(pixmap)
            if not isinstance(label, AspectRatioLabel):
                display_width = label.width()
                if display_width < 200:
                    screen = QApplication.primaryScreen()
                    display_width = screen.availableGeometry().width() - 160 if screen else 1400
                aspect = pixmap.height() / pixmap.width()
                label.setFixedHeight(int(display_width * aspect))
        else:
            label.setText("Chart rendering failed")
    except Exception as e:
        logger.error(f"Error rendering chart: {e}")
        label.setText(f"Chart error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def create_chart_label(min_height: int = 300) -> AspectRatioLabel:
    """Create a pre-configured AspectRatioLabel."""
    label = AspectRatioLabel()
    label.setMinimumHeight(min_height)
    return label
