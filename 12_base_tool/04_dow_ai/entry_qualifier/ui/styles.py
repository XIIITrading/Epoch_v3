"""
Dark Theme Stylesheet
Epoch Trading System v1 - XIII Trading LLC

Trading terminal style dark theme for the Entry Qualifier.
"""

# Color palette
COLORS = {
    # Base colors
    'bg_primary': '#000000',      # Main background (pure black)
    'bg_secondary': '#000000',    # Panel background (pure black)
    'bg_header': '#0f3460',       # Header background (blue - kept)
    'bg_cell': '#000000',         # Cell background (pure black)
    'border': '#2a2a4a',          # Border color
    'border_light': '#3a3a5a',    # Light border

    # Text colors
    'text_primary': '#e8e8e8',    # Primary text
    'text_secondary': '#a0a0a0',  # Secondary text
    'text_muted': '#707070',      # Muted text

    # Indicator colors
    'positive': '#26a69a',        # Green for positive values
    'negative': '#ef5350',        # Red for negative values
    'neutral': '#9E9E9E',         # Gray for zero/neutral

    # Score background colors
    'score_high': '#1B5E20',      # Green background (7-10)
    'score_mid': '#F57F17',       # Yellow/amber background (4-6)
    'score_low': '#B71C1C',       # Red background (0-3)

    # Status colors
    'status_live': '#26a69a',     # Live indicator (green)
    'status_paused': '#FFD600',   # Paused indicator
    'status_error': '#ef5350',    # Error indicator (red)

    # Absorption zone (dimmed) colors
    'dimmed_bg': '#1a1a1a',       # Slightly lighter than black for dimmed columns
    'dimmed_text': '#4a4a4a',     # Very muted text for absorption zones

    # Button colors
    'button_primary': '#0f3460',
    'button_hover': '#1a4a7a',
    'button_pressed': '#0a2540',
    'button_danger': '#c62828',
    'button_danger_hover': '#e53935',
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

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel#headerLabel {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    padding: 5px;
}}

QLabel#statusLabel {{
    font-size: 11px;
    color: {COLORS['text_secondary']};
    padding: 2px 5px;
}}

QLabel#tickerLabel {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS['text_primary']};
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
    padding: 6px 12px;
    font-weight: bold;
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

QPushButton#addButton {{
    background-color: {COLORS['button_primary']};
    min-width: 100px;
}}

QPushButton#removeButton {{
    background-color: transparent;
    border: none;
    color: {COLORS['text_secondary']};
    font-size: 14px;
    padding: 2px 6px;
}}

QPushButton#removeButton:hover {{
    color: {COLORS['button_danger']};
    background-color: transparent;
}}

/* Line Edit */
QLineEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {COLORS['button_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_light']};
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
    padding: 4px;
    border: none;
    font-size: 10pt;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['button_primary']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px;
    font-weight: bold;
    font-size: 8pt;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* Group Box (Ticker Panel) */
QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin-top: 12px;
    padding: 10px;
    padding-top: 25px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: {COLORS['text_primary']};
    font-weight: bold;
    font-size: 13px;
}}

/* Frame (for panels) */
QFrame#tickerPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QFrame#headerFrame {{
    background-color: {COLORS['bg_header']};
    border: none;
    border-radius: 4px;
}}

QFrame#statusBar {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['border']};
}}

/* Dialog */
QDialog {{
    background-color: {COLORS['bg_primary']};
}}

QDialog QLabel {{
    color: {COLORS['text_primary']};
}}

/* Message Box */
QMessageBox {{
    background-color: {COLORS['bg_primary']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}

/* Global Control Panel */
QFrame#globalControlPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QLabel#controlLabel {{
    color: {COLORS['text_secondary']};
    font-weight: bold;
}}

/* Terminal Panel */
QFrame#terminalPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QLabel#terminalTitle {{
    color: {COLORS['text_secondary']};
    font-family: 'Consolas', monospace;
}}

QLabel#terminalStatus {{
    font-family: 'Consolas', monospace;
}}

QLabel#terminalTimestamp {{
    color: {COLORS['text_muted']};
    font-family: 'Consolas', monospace;
}}

QTextEdit#terminalText {{
    background-color: #0a0a0a;
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    font-family: 'Consolas', monospace;
    selection-background-color: {COLORS['button_primary']};
}}

/* Combo Box for Ticker Selection */
QComboBox#tickerCombo {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QComboBox#tickerCombo:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox#tickerCombo QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['button_primary']};
}}

/* Ask DOW AI Button */
QPushButton#askButton {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 12px;
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
"""

# Cell-specific styles for conditional formatting
CELL_STYLES = {
    'positive_text': f"color: {COLORS['positive']};",
    'negative_text': f"color: {COLORS['negative']};",
    'neutral_text': f"color: {COLORS['neutral']};",
    'score_high_bg': f"background-color: {COLORS['score_high']}; color: white;",
    'score_mid_bg': f"background-color: {COLORS['score_mid']}; color: black;",
    'score_low_bg': f"background-color: {COLORS['score_low']}; color: white;",
}


def get_delta_style(value: float) -> str:
    """Get text color style for volume delta values."""
    if value > 0:
        return CELL_STYLES['positive_text']
    elif value < 0:
        return CELL_STYLES['negative_text']
    else:
        return CELL_STYLES['neutral_text']


def get_score_style(score: int) -> str:
    """Get background color style for score values."""
    if score >= 7:
        return CELL_STYLES['score_high_bg']
    elif score >= 4:
        return CELL_STYLES['score_mid_bg']
    else:
        return CELL_STYLES['score_low_bg']
