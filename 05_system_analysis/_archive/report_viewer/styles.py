"""
Dark Theme Stylesheet
Epoch Trading System v2.0 - XIII Trading LLC

Clean terminal-style dark theme for the System Analysis Dashboard.
Extends the shared color palette with dashboard-specific styles.
"""

# Color palette — matches 00_shared/ui/styles.py
COLORS = {
    # Base colors
    'bg_primary': '#000000',
    'bg_secondary': '#0a0a0a',
    'bg_header': '#0f3460',
    'bg_cell': '#000000',
    'bg_terminal': '#0a0a0a',
    'border': '#2a2a4a',
    'border_light': '#3a3a5a',

    # Text colors
    'text_primary': '#e8e8e8',
    'text_secondary': '#a0a0a0',
    'text_muted': '#707070',
    'text_terminal': '#e8e8e8',

    # Indicator colors (conditional formatting)
    'positive': '#26a69a',
    'negative': '#ef5350',
    'neutral': '#9E9E9E',

    # Status colors
    'status_ready': '#26a69a',
    'status_running': '#FFD600',
    'status_error': '#ef5350',
    'status_complete': '#26a69a',

    # Progress colors
    'progress_bg': '#1a1a2e',
    'progress_fill': '#0f3460',

    # Button colors
    'button_primary': '#0f3460',
    'button_hover': '#1a4a7a',
    'button_pressed': '#0a2540',
    'button_stop': '#c62828',
    'button_stop_hover': '#e53935',
}

# Main stylesheet
DARK_STYLESHEET = f"""
/* Main Window */
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 11px;
}}

/* Scroll Area */
QScrollArea {{
    background-color: {COLORS['bg_primary']};
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: {COLORS['bg_primary']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel#headerLabel {{
    font-size: 20px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    padding: 5px;
}}

QLabel#statusLabel {{
    font-size: 11px;
    color: {COLORS['text_secondary']};
}}

QLabel#sectionLabel {{
    font-size: 12px;
    font-weight: bold;
    color: {COLORS['text_secondary']};
}}

QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    padding: 5px 0;
}}

QLabel#placeholderLabel {{
    font-size: 12px;
    color: {COLORS['text_muted']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['button_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['button_hover']};
    border-color: {COLORS['border_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['button_pressed']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_muted']};
}}

QPushButton#refreshButton {{
    background-color: {COLORS['button_primary']};
    min-width: 140px;
    min-height: 36px;
    font-size: 10pt;
    padding: 8px 20px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_primary']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: bold;
    font-size: 10pt;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_primary']};
}}

QTabBar::tab:hover {{
    background-color: {COLORS['button_hover']};
}}

/* Table Widget */
QTableWidget {{
    background-color: {COLORS['bg_cell']};
    color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: {COLORS['button_primary']};
}}

QTableWidget::item {{
    padding: 4px 8px;
    border: none;
    font-size: 10pt;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['button_primary']};
}}

QTableWidget::item:alternate {{
    background-color: #050510;
}}

QHeaderView::section {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px 8px;
    font-weight: bold;
    font-size: 9pt;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* Section Frames */
QFrame#sectionFrame {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

/* Control Panel */
QFrame#controlPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

/* Status Bar */
QFrame#statusBar {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['border']};
}}

/* Scroll Bar */
QScrollBar:vertical {{
    background-color: {COLORS['bg_secondary']};
    width: 12px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_light']};
    border-radius: 4px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Date Edit Widget */
QDateEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10pt;
}}

QDateEdit:hover {{
    border-color: {COLORS['border_light']};
}}

QDateEdit:focus {{
    border-color: {COLORS['button_primary']};
}}

QDateEdit:disabled {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_muted']};
}}

QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {COLORS['border']};
    background-color: {COLORS['button_primary']};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}}

QDateEdit::down-arrow {{
    image: none;
    width: 12px;
    height: 12px;
}}

/* Calendar popup */
QCalendarWidget {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QCalendarWidget QToolButton {{
    background-color: {COLORS['button_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 4px 8px;
    font-weight: bold;
    min-width: 40px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {COLORS['button_hover']};
}}

QCalendarWidget QMenu {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QCalendarWidget QMenu::item:selected {{
    background-color: {COLORS['button_primary']};
}}

QCalendarWidget QSpinBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 2px;
}}

QCalendarWidget QAbstractItemView {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['button_primary']};
    selection-color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
    font-size: 10pt;
}}

QCalendarWidget QAbstractItemView:enabled {{
    color: {COLORS['text_primary']};
}}

QCalendarWidget QAbstractItemView:disabled {{
    color: {COLORS['text_muted']};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {COLORS['bg_header']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['progress_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text_primary']};
    font-weight: bold;
}}

QProgressBar::chunk {{
    background-color: {COLORS['progress_fill']};
    border-radius: 3px;
}}
"""
