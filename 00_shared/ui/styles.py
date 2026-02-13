"""
Epoch Trading System - Dark Theme Stylesheet
=============================================

Trading terminal style dark theme for all Epoch modules.
Consistent styling across all PyQt6 applications.

Usage:
    from shared.ui.styles import COLORS, DARK_STYLESHEET
    self.setStyleSheet(DARK_STYLESHEET)
"""

# =============================================================================
# COLOR PALETTE
# =============================================================================
COLORS = {
    # Base colors
    'bg_primary': '#000000',      # Main background (pure black)
    'bg_secondary': '#000000',    # Panel background (pure black)
    'bg_header': '#0f3460',       # Header background (blue)
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

    # Direction colors
    'bull': '#26a69a',            # Bullish (green)
    'bear': '#ef5350',            # Bearish (red)

    # Score background colors
    'score_high': '#1B5E20',      # Green background (7-10)
    'score_mid': '#F57F17',       # Yellow/amber background (4-6)
    'score_low': '#B71C1C',       # Red background (0-3)

    # Status colors
    'status_live': '#26a69a',     # Live indicator (green)
    'status_paused': '#FFD600',   # Paused indicator
    'status_error': '#ef5350',    # Error indicator (red)
    'status_loading': '#2196F3',  # Loading indicator (blue)

    # Absorption zone (dimmed) colors
    'dimmed_bg': '#1a1a1a',       # Slightly lighter than black for dimmed columns
    'dimmed_text': '#4a4a4a',     # Very muted text for absorption zones

    # Table/terminal backgrounds
    'bg_table': '#0d0d0d',           # Table background
    'bg_table_alt': '#141414',       # Alternating row background
    'bg_terminal': '#0a0a0a',        # Terminal background
    'text_terminal': '#e8e8e8',      # Terminal text (matches text_primary)

    # Status aliases (semantic names for cross-module consistency)
    'status_ready': '#26a69a',       # Ready state (same as status_live)
    'status_running': '#FFD600',     # Running state (same as status_paused)
    'status_complete': '#26a69a',    # Complete state (same as status_live)

    # Tier UI colors (softer colors for UI text, distinct from chart TIER_COLORS)
    'tier_t3': '#26a69a',            # T3 - Best (green)
    'tier_t2': '#ff9800',            # T2 - Medium (orange)
    'tier_t1': '#FFD600',            # T1 - Basic (yellow)

    # Progress bar
    'progress_bg': '#1a1a2e',
    'progress_fill': '#0f3460',

    # Button colors
    'button_primary': '#0f3460',
    'button_hover': '#1a4a7a',
    'button_pressed': '#0a2540',
    'button_danger': '#c62828',
    'button_danger_hover': '#e53935',
    'button_success': '#1B5E20',
    'button_success_hover': '#2E7D32',
    'button_stop': '#c62828',        # Alias for button_danger
    'button_stop_hover': '#e53935',  # Alias for button_danger_hover
}

# =============================================================================
# MAIN STYLESHEET
# =============================================================================
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

QScrollBar:horizontal {{
    background-color: {COLORS['bg_secondary']};
    height: 12px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_light']};
    border-radius: 4px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
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

QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    padding: 5px 0;
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

QPushButton#primaryButton {{
    background-color: {COLORS['button_primary']};
    min-width: 100px;
}}

QPushButton#dangerButton {{
    background-color: {COLORS['button_danger']};
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS['button_danger_hover']};
}}

QPushButton#successButton {{
    background-color: {COLORS['button_success']};
}}

QPushButton#successButton:hover {{
    background-color: {COLORS['button_success_hover']};
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

QLineEdit:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_muted']};
}}

/* Text Edit */
QTextEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {COLORS['button_primary']};
}}

QTextEdit:focus {{
    border-color: {COLORS['border_light']};
}}

/* Plain Text Edit */
QPlainTextEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    font-family: 'Consolas', monospace;
    selection-background-color: {COLORS['button_primary']};
}}

/* Combo Box */
QComboBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['button_primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

/* Spin Box */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['border_light']};
}}

/* Check Box */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    background-color: {COLORS['bg_secondary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['button_primary']};
    border-color: {COLORS['button_primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['border_light']};
}}

/* Radio Button */
QRadioButton {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_secondary']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['button_primary']};
    border-color: {COLORS['button_primary']};
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

/* Tree Widget */
QTreeWidget {{
    background-color: {COLORS['bg_cell']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

QTreeWidget::item {{
    padding: 4px;
}}

QTreeWidget::item:selected {{
    background-color: {COLORS['button_primary']};
}}

/* List Widget */
QListWidget {{
    background-color: {COLORS['bg_cell']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

QListWidget::item {{
    padding: 4px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['button_primary']};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_secondary']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_primary']};
}}

QTabBar::tab:hover {{
    background-color: {COLORS['button_hover']};
}}

/* Group Box */
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

/* Frame */
QFrame#panel {{
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

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['button_primary']};
    border-radius: 3px;
}}

/* Slider */
QSlider::groove:horizontal {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {COLORS['button_primary']};
    border: none;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {COLORS['button_hover']};
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

/* Menu */
QMenu {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
}}

QMenu::item {{
    padding: 6px 20px;
    color: {COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {COLORS['button_primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 4px 10px;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['border']};
}}

QMenuBar::item {{
    padding: 6px 10px;
    color: {COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['button_primary']};
}}

/* Tool Bar */
QToolBar {{
    background-color: {COLORS['bg_secondary']};
    border: none;
    spacing: 4px;
    padding: 4px;
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px;
}}

QToolButton:hover {{
    background-color: {COLORS['button_hover']};
    border-color: {COLORS['border']};
}}

QToolButton:pressed {{
    background-color: {COLORS['button_pressed']};
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['border']};
    color: {COLORS['text_secondary']};
}}

/* Splitter */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Terminal Panel */
QFrame#terminalPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QTextEdit#terminalText {{
    background-color: #0a0a0a;
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    font-family: 'Consolas', monospace;
    selection-background-color: {COLORS['button_primary']};
}}

/* Tooltip */
QToolTip {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    padding: 4px;
}}

/* Section Frames */
QFrame#sectionFrame {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px;
}}

QLabel#sectionLabel {{
    font-size: 12px;
    font-weight: bold;
    color: {COLORS['text_secondary']};
    padding: 4px 0px;
}}

/* Control Panel */
QFrame#controlPanel {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

/* Terminal Frame & Output */
QFrame#terminalFrame {{
    background-color: {COLORS['bg_terminal']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QTextEdit#terminalOutput {{
    background-color: {COLORS['bg_terminal']};
    color: {COLORS['text_terminal']};
    border: none;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10pt;
    padding: 10px;
    selection-background-color: {COLORS['button_primary']};
}}

/* Action Buttons */
QPushButton#runButton {{
    background-color: {COLORS['button_success']};
    min-width: 120px;
    min-height: 36px;
    font-size: 11pt;
    padding: 8px 20px;
}}

QPushButton#runButton:hover {{
    background-color: {COLORS['button_success_hover']};
}}

QPushButton#stopButton {{
    background-color: {COLORS['button_stop']};
    min-width: 100px;
    min-height: 36px;
    font-size: 11pt;
    padding: 8px 20px;
}}

QPushButton#stopButton:hover {{
    background-color: {COLORS['button_stop_hover']};
}}

QPushButton#exportButton {{
    background-color: {COLORS['button_primary']};
    min-width: 140px;
    min-height: 36px;
    font-size: 11pt;
    padding: 8px 20px;
}}

QPushButton#clearButton {{
    background-color: #444444;
    min-width: 100px;
    min-height: 36px;
    font-size: 11pt;
    padding: 8px 20px;
}}

QPushButton#clearButton:hover {{
    background-color: #555555;
}}
"""

# =============================================================================
# CELL-SPECIFIC STYLES
# =============================================================================
CELL_STYLES = {
    'positive_text': f"color: {COLORS['positive']};",
    'negative_text': f"color: {COLORS['negative']};",
    'neutral_text': f"color: {COLORS['neutral']};",
    'bull_text': f"color: {COLORS['bull']};",
    'bear_text': f"color: {COLORS['bear']};",
    'score_high_bg': f"background-color: {COLORS['score_high']}; color: white;",
    'score_mid_bg': f"background-color: {COLORS['score_mid']}; color: black;",
    'score_low_bg': f"background-color: {COLORS['score_low']}; color: white;",
    'dimmed_bg': f"background-color: {COLORS['dimmed_bg']}; color: {COLORS['dimmed_text']};",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_delta_style(value: float) -> str:
    """Get text color style for volume delta values."""
    if value > 0:
        return CELL_STYLES['positive_text']
    elif value < 0:
        return CELL_STYLES['negative_text']
    else:
        return CELL_STYLES['neutral_text']


def get_score_style(score: int) -> str:
    """Get background color style for score values (0-10 scale)."""
    if score >= 7:
        return CELL_STYLES['score_high_bg']
    elif score >= 4:
        return CELL_STYLES['score_mid_bg']
    else:
        return CELL_STYLES['score_low_bg']


def get_direction_style(direction: str) -> str:
    """Get text color style for direction (BULL/BEAR)."""
    if direction.upper() in ('BULL', 'BULLISH', 'LONG', 'UP'):
        return CELL_STYLES['bull_text']
    elif direction.upper() in ('BEAR', 'BEARISH', 'SHORT', 'DOWN'):
        return CELL_STYLES['bear_text']
    else:
        return CELL_STYLES['neutral_text']
