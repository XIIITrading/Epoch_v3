"""
Epoch Trading System - Shared UI Components
============================================

Centralized PyQt6 UI components for all Epoch modules.

Provides:
- Base window class with consistent styling
- Color theme and stylesheet
- Reusable widgets
- Chart components

Usage:
    from shared.ui import BaseWindow, COLORS, DARK_STYLESHEET
    from shared.ui.widgets import StatusBar, TickerInput
    from shared.ui.charts import CandlestickChart

    class MyWindow(BaseWindow):
        def __init__(self):
            super().__init__(title="My Module")
            self.setup_ui()
"""

from .styles import COLORS, DARK_STYLESHEET, CELL_STYLES, get_delta_style, get_score_style
from .base_window import BaseWindow

__all__ = [
    "COLORS",
    "DARK_STYLESHEET",
    "CELL_STYLES",
    "get_delta_style",
    "get_score_style",
    "BaseWindow",
]
