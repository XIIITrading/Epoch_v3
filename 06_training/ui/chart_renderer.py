"""
Epoch Trading System - Chart Renderer
Converts Plotly figures to QPixmap for PyQt6 display.

Uses kaleido for PNG export, following the 05_system_analysis pattern.
Sized for 4K displays with dynamic resizing via heightForWidth.
"""

import tempfile
import os
import logging
from PyQt6.QtWidgets import QLabel, QSizePolicy, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# Render dimensions (Plotly figure size before scale multiplier)
RENDER_WIDTH = 1800
MAIN_CHART_HEIGHT = 900
RAMPUP_CHART_HEIGHT = 550
RENDER_SCALE = 2  # 2x for crisp rendering


class AspectRatioLabel(QLabel):
    """
    QLabel that maintains the aspect ratio of its pixmap during resize.

    Uses Qt's heightForWidth mechanism — the layout queries heightForWidth(w)
    to determine the correct height. This avoids setFixedHeight inside
    resizeEvent which causes infinite recursion crashes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aspect_ratio = 0.5  # height / width, default 2:1
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background-color: #1a1a2e; border: 1px solid #2a2a4e;")
        self.setText("Loading chart...")

    def setPixmap(self, pixmap: QPixmap):
        """Override to capture aspect ratio from the pixmap."""
        if not pixmap.isNull() and pixmap.width() > 0:
            self._aspect_ratio = pixmap.height() / pixmap.width()
        super().setPixmap(pixmap)
        self.updateGeometry()  # Tell layout to re-query heightForWidth

    def hasHeightForWidth(self):
        """Enable Qt's aspect-ratio layout support."""
        return True

    def heightForWidth(self, width: int) -> int:
        """Return the height that preserves the pixmap's aspect ratio."""
        return int(width * self._aspect_ratio)

    def sizeHint(self) -> QSize:
        """Provide a reasonable default size hint."""
        w = self.width() if self.width() > 100 else 1600
        return QSize(w, int(w * self._aspect_ratio))

    def minimumSizeHint(self) -> QSize:
        """Minimum size hint to prevent collapse."""
        return QSize(400, int(400 * self._aspect_ratio))


def render_chart_to_label(
    fig: go.Figure,
    label: QLabel,
    width: int = RENDER_WIDTH,
    height: int = MAIN_CHART_HEIGHT,
    scale: int = RENDER_SCALE
):
    """
    Render a Plotly figure to a QLabel as a static PNG image.

    For AspectRatioLabel: sets the pixmap and aspect ratio, then lets Qt's
    layout system handle sizing via heightForWidth.

    For plain QLabel: sets the pixmap with setFixedHeight as fallback.

    Args:
        fig: Plotly Figure object
        label: QLabel (preferably AspectRatioLabel) to display the chart in
        width: Image width in pixels (Plotly logical)
        height: Image height in pixels (Plotly logical)
        scale: Render scale factor (2 = retina)
    """
    fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)

    try:
        fig.write_image(temp_path, format='png', width=width, height=height, scale=scale)
        pixmap = QPixmap(temp_path)

        if not pixmap.isNull():
            label.setPixmap(pixmap)  # AspectRatioLabel captures ratio here

            # For plain QLabel fallback (not AspectRatioLabel), set fixed height
            if not isinstance(label, AspectRatioLabel):
                display_width = label.width()
                if display_width < 200:
                    screen = QApplication.primaryScreen()
                    if screen:
                        screen_width = screen.availableGeometry().width()
                        display_width = screen_width - 160
                    else:
                        display_width = 1600
                aspect = pixmap.height() / pixmap.width()
                display_height = int(display_width * aspect)
                label.setFixedHeight(display_height)
        else:
            logger.warning("Failed to load chart PNG into QPixmap")
            label.setText("Chart rendering failed")
    except Exception as e:
        logger.error(f"Error rendering chart: {e}")
        label.setText(f"Chart error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def create_chart_label(min_height: int = 400) -> AspectRatioLabel:
    """
    Create an AspectRatioLabel configured for chart display.

    Uses heightForWidth for dynamic aspect-ratio-preserving resize.
    No setFixedHeight — Qt's layout manages height automatically.

    Args:
        min_height: Minimum label height before chart loads

    Returns:
        Configured AspectRatioLabel
    """
    label = AspectRatioLabel()
    label.setMinimumHeight(min_height)
    return label
