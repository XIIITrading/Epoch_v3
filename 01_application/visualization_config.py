"""
Visualization Configuration for Epoch Analysis Tool.
Epoch Trading System v2.0 - XIII Trading LLC

Chart colors imported from shared infrastructure (EPOCH_DARK palette).
Module-specific chart parameters (dimensions, fonts, table layout) remain local.
"""

import sys
from pathlib import Path

# Ensure shared is importable
EPOCH_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(EPOCH_DIR / "00_shared"))

from charts.colors import EPOCH_DARK, RANK_COLORS, TIER_COLORS

# =============================================================================
# COLOR SCHEME (from shared EPOCH_DARK palette)
# =============================================================================

# Build VIZ_COLORS from EPOCH_DARK for backward compatibility
VIZ_COLORS = {
    # Background colors
    'dark_bg': EPOCH_DARK['background'],
    'dark_bg_lighter': EPOCH_DARK['dark_bg_lighter'],
    'table_bg': EPOCH_DARK['table_bg'],
    'notes_bg': EPOCH_DARK['notes_bg'],

    # Text colors
    'text_primary': EPOCH_DARK['text'],
    'text_muted': EPOCH_DARK['text_muted'],
    'text_dim': EPOCH_DARK['text_dim'],

    # Zone colors (90% transparency = alpha 0.15)
    'primary_blue': EPOCH_DARK['zone_primary'],
    'primary_blue_fill': EPOCH_DARK['zone_primary'],
    'secondary_red': EPOCH_DARK['zone_secondary'],
    'secondary_red_fill': EPOCH_DARK['zone_secondary'],
    'pivot_purple': EPOCH_DARK['pivot_purple'],

    # Direction colors
    'bull': EPOCH_DARK['bull'],
    'bear': EPOCH_DARK['bear'],
    'neutral': EPOCH_DARK['neutral'],

    # Candlestick colors
    'candle_green': EPOCH_DARK['candle_up'],
    'candle_red': EPOCH_DARK['candle_down'],

    # UI elements
    'border': EPOCH_DARK['border'],
    'border_light': EPOCH_DARK['border_light'],
    'grid': EPOCH_DARK['grid'],
}

# Alias for compatibility
COLORS = VIZ_COLORS

# Zone fill alpha (matching PineScript color.new with 90 transparency)
ZONE_FILL_ALPHA = EPOCH_DARK['zone_opacity']

# =============================================================================
# CHART PARAMETERS (module-specific, not shared)
# =============================================================================

# Candlestick settings
CANDLE_TIMEFRAME = 60          # H1 in minutes (1 hour)
CANDLE_BAR_COUNT = 120         # ~18 trading days at H1

# Volume Profile settings
VBP_TIMEFRAME = 15             # M15 for VbP
VBP_COLOR = EPOCH_DARK['vbp']
VBP_GRANULARITY = 0.01         # $0.01 fidelity (matches Excel)

# POC Lines (from HVN calculation)
POC_LINE_STYLE = '--'          # Dashed
POC_LINE_COLOR = EPOCH_DARK['poc']
POC_LINE_ALPHA = EPOCH_DARK['poc_opacity']

# Chart dimensions - 1920x1080 pixels at 100 DPI = 19.2 x 10.8 inches
FIGURE_WIDTH = 19.2
FIGURE_HEIGHT = 10.8
DPI = 100  # 100 DPI gives exactly 1920x1080 pixels

# Preview uses same dimensions (no separate preview mode)
PREVIEW_FIGURE_WIDTH = 19.2
PREVIEW_FIGURE_HEIGHT = 10.8
PREVIEW_DPI = 100  # Same as full resolution

# Y-axis padding (percentage of range)
YAXIS_PADDING_PCT = 0.02       # 2% padding

# =============================================================================
# TABLE LAYOUT
# =============================================================================

# Left panel table height ratios
TABLE_HEIGHT_RATIOS = [1.0, 1.2, 1.8, 1.4, 0.8]  # Market, Ticker, Zones, Setup, Notes

# =============================================================================
# FONT SIZES (EXACT match to working chart_builder.py)
# =============================================================================

FONT_TITLE = 16       # Main title (suptitle)
FONT_SUBTITLE = 11    # Subtitle below title
FONT_HEADER = 9       # Table headers (bold)
FONT_TABLE = 9        # Table row data
FONT_TABLE_BOLD = 10  # Bold table values (direction, rank, tier)
FONT_LABEL = 8        # Small labels
FONT_AXIS = 9         # Axis tick labels
FONT_AXIS_LABEL = 11  # Axis title labels
FONT_POC_LABEL = 7    # POC price labels on chart
