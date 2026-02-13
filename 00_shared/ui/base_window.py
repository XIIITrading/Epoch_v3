"""
Epoch Trading System - Base Window
===================================

Base window class for all Epoch PyQt6 applications.
Provides consistent styling and common functionality.

Usage:
    from shared.ui import BaseWindow

    class MyWindow(BaseWindow):
        def __init__(self):
            super().__init__(title="My Module", width=1200, height=800)
            self.setup_ui()

        def setup_ui(self):
            # Add your UI components here
            pass
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QMenuBar,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont
from datetime import datetime
from typing import Optional

from .styles import DARK_STYLESHEET, COLORS


class BaseWindow(QMainWindow):
    """
    Base window class for all Epoch PyQt6 applications.

    Provides:
    - Dark theme styling
    - Common header with title and clock
    - Status bar with market status
    - Menu bar structure
    - Common utility methods

    Subclass this for each module's main window.
    """

    # Default window size
    DEFAULT_WIDTH = 1400
    DEFAULT_HEIGHT = 900

    def __init__(
        self,
        title: str = "Epoch Trading System",
        width: Optional[int] = None,
        height: Optional[int] = None,
        show_menu: bool = True,
        show_status_bar: bool = True,
    ):
        """
        Initialize base window.

        Args:
            title: Window title
            width: Window width (defaults to DEFAULT_WIDTH)
            height: Window height (defaults to DEFAULT_HEIGHT)
            show_menu: Whether to show menu bar
            show_status_bar: Whether to show status bar
        """
        super().__init__()

        self._title = title
        self._width = width or self.DEFAULT_WIDTH
        self._height = height or self.DEFAULT_HEIGHT

        # Apply dark theme
        self.setStyleSheet(DARK_STYLESHEET)

        # Set window properties
        self.setWindowTitle(title)
        self.setMinimumSize(800, 600)
        self.resize(self._width, self._height)

        # Create central widget
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        self._main_layout = QVBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(15, 15, 15, 10)
        self._main_layout.setSpacing(10)

        # Create menu bar if requested
        if show_menu:
            self._setup_menu_bar()

        # Create status bar if requested
        if show_status_bar:
            self._setup_status_bar()

        # Clock timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)  # Update every second

    def _setup_menu_bar(self):
        """Set up the menu bar with common menus."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.on_refresh)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Store references for subclasses
        self._file_menu = file_menu
        self._view_menu = view_menu
        self._help_menu = help_menu

    def _setup_status_bar(self):
        """Set up the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Clock label on the right
        self._clock_label = QLabel()
        self._clock_label.setFont(QFont("Consolas", 9))
        status_bar.addPermanentWidget(self._clock_label)

        # Status message on the left
        self._status_label = QLabel("Ready")
        status_bar.addWidget(self._status_label)

        # Update clock immediately
        self._update_clock()

    def _update_clock(self):
        """Update the clock display."""
        if hasattr(self, '_clock_label'):
            now = datetime.now()
            self._clock_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))

    def set_status(self, message: str, timeout_ms: int = 0):
        """
        Set status bar message.

        Args:
            message: Status message to display
            timeout_ms: Clear after this many ms (0 = permanent)
        """
        if hasattr(self, '_status_label'):
            self._status_label.setText(message)
            if timeout_ms > 0:
                QTimer.singleShot(timeout_ms, lambda: self._status_label.setText("Ready"))

    def show_error(self, title: str, message: str):
        """Show error dialog."""
        QMessageBox.critical(self, title, message)

    def show_warning(self, title: str, message: str):
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)

    def show_info(self, title: str, message: str):
        """Show info dialog."""
        QMessageBox.information(self, title, message)

    def ask_confirmation(self, title: str, message: str) -> bool:
        """Show confirmation dialog. Returns True if user clicked Yes."""
        result = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def show_about(self):
        """Show about dialog. Override in subclasses for custom content."""
        QMessageBox.about(
            self,
            f"About {self._title}",
            f"""
            <h2>{self._title}</h2>
            <p>Epoch Trading System v2.0</p>
            <p>XIII Trading LLC</p>
            <p>Built with PyQt6</p>
            """,
        )

    def on_refresh(self):
        """
        Handle refresh action. Override in subclasses.
        """
        self.set_status("Refreshing...", 2000)

    def add_to_layout(self, widget: QWidget):
        """Add a widget to the main layout."""
        self._main_layout.addWidget(widget)

    def add_stretch(self):
        """Add stretch to the main layout."""
        self._main_layout.addStretch()

    @property
    def main_layout(self) -> QVBoxLayout:
        """Get the main layout for adding custom widgets."""
        return self._main_layout

    @property
    def file_menu(self) -> QMenu:
        """Get the File menu for adding custom actions."""
        return self._file_menu

    @property
    def view_menu(self) -> QMenu:
        """Get the View menu for adding custom actions."""
        return self._view_menu

    @property
    def help_menu(self) -> QMenu:
        """Get the Help menu for adding custom actions."""
        return self._help_menu

    def closeEvent(self, event):
        """Handle window close event. Override for cleanup."""
        self._clock_timer.stop()
        event.accept()
