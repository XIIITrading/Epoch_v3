"""
Epoch Trading System - Trade Reel Module Configuration
Highlight trade viewer and social media image exporter.
"""

import os
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
MODULE_DIR = Path(__file__).parent
BASE_DIR = MODULE_DIR.parent  # C:\XIIITradingSystems\Epoch
EXPORT_DIR = MODULE_DIR / "exports"

# =============================================================================
# Supabase Configuration
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# =============================================================================
# Polygon API
# =============================================================================
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_')
API_DELAY = 0.25
API_RETRIES = 3
API_RETRY_DELAY = 2.0

# =============================================================================
# TradingView Dark Theme - Colors
# =============================================================================
TV_COLORS = {
    'bg_primary': '#131722',        # Mirage background
    'bg_secondary': '#1E222D',      # Panel/input background
    'border': '#2A2E39',            # Grid lines, borders
    'accent': '#2962FF',            # Dodger Blue - primary action
    'accent_hover': '#1E4BD8',      # Darker accent on hover
    'bull': '#089981',              # Teal - bullish/up
    'bear': '#F23645',              # Red - bearish/down
    'text_primary': '#D1D4DC',      # Silver text
    'text_muted': '#787B86',        # Gray muted text
    'text_white': '#FFFFFF',        # White text on buttons
}

# =============================================================================
# Chart Configuration (TradingView Dark)
# =============================================================================
CHART_COLORS = {
    # Plotly layout
    'background': '#000000',
    'paper': '#000000',
    'grid': '#2A2E39',
    'text': '#D1D4DC',
    'text_muted': '#787B86',

    # Candlesticks (muted: TradingView colors at 50% opacity on black)
    'candle_up': '#13534D',
    'candle_down': '#782A28',

    # Trade markers
    'entry': '#2962FF',             # Blue
    'stop': '#F23645',              # Red
    'mfe': '#2962FF',              # Blue

    # R-level colors (gradient from teal to green)
    'r1': '#26A69A',                # Light teal
    'r2': '#089981',                # Teal
    'r3': '#FF9800',                # Gold
    'r4': '#FF6F00',                # Orange
    'r5': '#00C853',                # Bright green

    # Zone overlay
    'zone_fill': 'rgba(41,98,255,0.12)',
    'zone_border': '#2962FF',
}

# =============================================================================
# Highlight Configuration
# =============================================================================
HIGHLIGHT_CONFIG = {
    'min_r_default': 3,             # Default minimum R for highlights
    'outcome_filter': 'WIN',        # Only show wins
    'default_limit': 200,           # Max highlights to load
}

# =============================================================================
# Export Sizes (width, height) per platform
# =============================================================================
EXPORT_SIZES = {
    'twitter': (1600, 900),
    'instagram': (1080, 1920),
    'stocktwits': (1200, 630),
    'discord': (1920, 1080),
}

# =============================================================================
# GrowthHub Brand Colors
# =============================================================================
BRAND_COLORS = {
    'forest_green': '#0F3D3E',      # Primary
    'cream': '#F5F2EB',             # Primary text on dark
    'charcoal': '#1C1C1C',          # Primary dark bg
    'terracotta': '#C8754A',        # Secondary accent
    'sage': '#A8B39A',              # Secondary muted
    'light_stone': '#D6D2C4',       # Secondary light text
}

# =============================================================================
# Branding
# =============================================================================
FONTS_DIR = MODULE_DIR / "assets" / "fonts"

BRANDING = {
    'title': 'GROWTH HUB',
    'subtitle': '@codycsilva',
    'header_height': 80,
    'header_bg': BRAND_COLORS['charcoal'],
    'header_accent': BRAND_COLORS['forest_green'],
    # Font files (relative to FONTS_DIR)
    'font_header': 'Anton-Regular.ttf',           # H1 headers
    'font_title': 'RobotoCondensed.ttf',          # H2/H3 titles
    'font_body': 'Roboto-Regular.ttf',            # Body text
    'font_accent': 'PlayfairDisplay-Italic.ttf',  # Optional accent
}

# =============================================================================
# TradingView Dark QSS Stylesheet
# =============================================================================
TV_DARK_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #131722;
    color: #D1D4DC;
    font-family: "Trebuchet MS", sans-serif;
}

QLabel {
    color: #D1D4DC;
}

QLineEdit, QTextEdit, QSpinBox, QDateEdit, QComboBox {
    background-color: #1E222D;
    border: 1px solid #2A2E39;
    color: #D1D4DC;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 12px;
}

QComboBox::drop-down {
    border: none;
    background: #2A2E39;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #1E222D;
    border: 1px solid #2A2E39;
    color: #D1D4DC;
    selection-background-color: #2962FF;
}

QTableWidget, QTableView {
    background-color: #131722;
    alternate-background-color: #1E222D;
    border: 1px solid #2A2E39;
    color: #D1D4DC;
    gridline-color: #2A2E39;
    selection-background-color: #2962FF;
    selection-color: white;
}

QHeaderView::section {
    background-color: #1E222D;
    border: 1px solid #2A2E39;
    color: #D1D4DC;
    padding: 6px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton {
    background-color: #2962FF;
    color: white;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 12px;
    border: none;
}

QPushButton:hover {
    background-color: #1E4BD8;
}

QPushButton:pressed {
    background-color: #1539B0;
}

QPushButton:disabled {
    background-color: #2A2E39;
    color: #787B86;
}

QScrollBar:vertical {
    border: none;
    background: #131722;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #2A2E39;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #131722;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background: #2A2E39;
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QFrame {
    border: none;
}

QStatusBar {
    background-color: #131722;
    color: #787B86;
    border-top: 1px solid #2A2E39;
}

QMenuBar {
    background-color: #131722;
    color: #D1D4DC;
    border-bottom: 1px solid #2A2E39;
}

QMenuBar::item:selected {
    background-color: #2962FF;
}

QMenu {
    background-color: #1E222D;
    color: #D1D4DC;
    border: 1px solid #2A2E39;
}

QMenu::item:selected {
    background-color: #2962FF;
}

QCheckBox {
    color: #D1D4DC;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #2A2E39;
    border-radius: 3px;
    background: #1E222D;
}

QCheckBox::indicator:checked {
    background: #2962FF;
    border-color: #2962FF;
}

QToolTip {
    background-color: #1E222D;
    color: #D1D4DC;
    border: 1px solid #2A2E39;
    padding: 4px;
}

QProgressBar {
    background-color: #1E222D;
    border: 1px solid #2A2E39;
    border-radius: 4px;
    text-align: center;
    color: #D1D4DC;
}

QProgressBar::chunk {
    background-color: #2962FF;
    border-radius: 3px;
}
"""

# =============================================================================
# Time Settings
# =============================================================================
DISPLAY_TIMEZONE = 'America/New_York'
MARKET_OPEN_HOUR = 8
MARKET_CLOSE_HOUR = 20
