"""
Epoch Backtest Journal - Theme Configuration
Colors and fonts matching the Epoch visualization style.
"""

# =============================================================================
# COLOR SCHEME (Matching PineScript/Module 08)
# =============================================================================

COLORS = {
    # Background colors
    'dark_bg': '#1a1a2e',
    'dark_bg_lighter': '#16213e',
    'table_bg': '#0f0f1a',
    'notes_bg': '#0a0a12',
    'chart_bg': '#1a1a2e',

    # Text colors
    'text_primary': '#e0e0e0',
    'text_muted': '#888888',
    'text_dim': '#666666',
    'text_header': '#ffffff',

    # Zone colors
    'primary_zone': '#90bff9',      # Blue for primary zones
    'secondary_zone': '#faa1a4',    # Red/pink for secondary zones

    # Performance colors
    'positive': '#26a69a',          # Teal/green for wins
    'negative': '#ef5350',          # Red for losses
    'neutral': '#888888',

    # Model colors (for charts)
    'epch1': '#4fc3f7',             # Light blue
    'epch2': '#81c784',             # Light green
    'epch3': '#ffb74d',             # Orange
    'epch4': '#f06292',             # Pink

    # Table colors
    'table_header_bg': '#2a2a4e',
    'table_row_alt': '#12121f',
    'table_border': '#333333',
    'table_highlight': '#3a3a5e',

    # UI elements
    'border': '#333333',
    'border_light': '#444444',
    'grid': '#2a2a4e',
    'divider': '#404060',
}

# =============================================================================
# FONT SETTINGS
# =============================================================================

FONTS = {
    'family': 'DejaVu Sans',
    'title_size': 16,
    'header_size': 12,
    'body_size': 10,
    'small_size': 8,
    'table_size': 9,
}

# =============================================================================
# MATPLOTLIB STYLE SETTINGS
# =============================================================================

def get_dark_style():
    """Return matplotlib style dict for dark theme."""
    return {
        'figure.facecolor': COLORS['dark_bg'],
        'axes.facecolor': COLORS['chart_bg'],
        'axes.edgecolor': COLORS['border'],
        'axes.labelcolor': COLORS['text_primary'],
        'axes.titlecolor': COLORS['text_header'],
        'text.color': COLORS['text_primary'],
        'xtick.color': COLORS['text_muted'],
        'ytick.color': COLORS['text_muted'],
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.3,
        'legend.facecolor': COLORS['dark_bg_lighter'],
        'legend.edgecolor': COLORS['border'],
        'legend.labelcolor': COLORS['text_primary'],
    }

# =============================================================================
# TABLE FORMATTING
# =============================================================================

TABLE_STYLE = {
    'header_bg': COLORS['table_header_bg'],
    'row_bg': COLORS['table_bg'],
    'row_alt_bg': COLORS['table_row_alt'],
    'border_color': COLORS['table_border'],
    'text_color': COLORS['text_primary'],
    'header_text_color': COLORS['text_header'],
}
