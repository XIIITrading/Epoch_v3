"""
Visualization Configuration for Epoch Analysis Tool.

Color scheme matching PineScript indicators.
Chart parameters for matplotlib rendering.
"""

# =============================================================================
# CHART PARAMETERS
# =============================================================================

# Candlestick settings
CANDLE_TIMEFRAME = 60          # H1 in minutes (1 hour)
CANDLE_BAR_COUNT = 120         # ~18 trading days at H1

# Volume Profile settings
VBP_TIMEFRAME = 15             # M15 for VbP
VBP_COLOR = '#5c6bc0'          # Indigo
VBP_GRANULARITY = 0.01         # $0.01 fidelity (matches Excel)

# POC Lines (from HVN calculation)
POC_LINE_STYLE = '--'          # Dashed
POC_LINE_COLOR = '#ffffff'     # White
POC_LINE_ALPHA = 0.3           # 70% transparent

# Chart dimensions (inches) - sized for 4K display
FIGURE_WIDTH = 20
FIGURE_HEIGHT = 12
DPI = 300  # High resolution for PDF export

# Preview dimensions (smaller for Streamlit display)
PREVIEW_FIGURE_WIDTH = 14
PREVIEW_FIGURE_HEIGHT = 8
PREVIEW_DPI = 100  # Lower DPI for web preview

# Y-axis padding (percentage of range)
YAXIS_PADDING_PCT = 0.02       # 2% padding

# =============================================================================
# COLOR SCHEME (Matching PineScript)
# =============================================================================

COLORS = {
    # Background colors
    'dark_bg': '#1a1a2e',
    'dark_bg_lighter': '#16213e',
    'table_bg': '#0f0f1a',
    'notes_bg': '#0a0a12',

    # Text colors
    'text_primary': '#e0e0e0',
    'text_muted': '#888888',
    'text_dim': '#666666',

    # Zone colors (90% transparency = alpha 0.15)
    'primary_blue': '#90bff9',
    'primary_blue_fill': '#90bff9',
    'secondary_red': '#faa1a4',
    'secondary_red_fill': '#faa1a4',
    'pivot_purple': '#b19cd9',

    # Direction colors
    'bull': '#26a69a',
    'bear': '#ef5350',
    'neutral': '#888888',

    # Candlestick colors
    'candle_green': '#26a69a',
    'candle_red': '#ef5350',

    # UI elements
    'border': '#333333',
    'border_light': '#444444',
    'grid': '#2a2a4e',
}

# Zone fill alpha (matching PineScript color.new with 90 transparency)
ZONE_FILL_ALPHA = 0.15

# =============================================================================
# TIER COLORS
# =============================================================================

TIER_COLORS = {
    'T3': '#00C853',  # Green - High Quality (L4-L5)
    'T2': '#FFC107',  # Yellow/Amber - Medium Quality (L3)
    'T1': '#9E9E9E',  # Gray - Lower Quality (L1-L2)
}

# =============================================================================
# RANK COLORS (for Zone Results table)
# =============================================================================

RANK_COLORS = {
    'L5': '#00C853',  # Green - best
    'L4': '#2196F3',  # Blue
    'L3': '#FFC107',  # Yellow/Amber
    'L2': '#9E9E9E',  # Gray
    'L1': '#616161',  # Dark gray
}

# =============================================================================
# TABLE LAYOUT
# =============================================================================

# Left panel table height ratios
TABLE_HEIGHT_RATIOS = [1.0, 1.2, 1.8, 1.4, 0.8]  # Market, Ticker, Zones, Setup, Notes

# =============================================================================
# SESSION LABELS
# =============================================================================

SESSION_LABELS = {
    'premarket': 'Pre-Market Report',
    'postmarket': 'Post-Market Report',
    'analysis': 'Analysis Report'
}
