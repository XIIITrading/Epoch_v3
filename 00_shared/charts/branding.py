"""
Epoch Trading System - Branding Configuration
==============================================

GrowthHub brand identity for social media exports and watermarks.
Brand palette, export size presets, and header configuration.
"""

# =====================================================================
# BRAND PALETTE
# =====================================================================
BRAND_COLORS = {
    'forest_green': '#0F3D3E',
    'cream': '#F5F2EB',
    'charcoal': '#1C1C1C',
    'terracotta': '#C8754A',
    'sage': '#A8B39A',
    'light_stone': '#D6D2C4',
}

# =====================================================================
# EXPORT SIZE PRESETS (width, height) per platform
# =====================================================================
EXPORT_SIZES = {
    'twitter': (1600, 900),
    'instagram': (1080, 1920),
    'stocktwits': (1200, 630),
    'discord': (1920, 1080),
}

# =====================================================================
# BRANDING IDENTITY
# =====================================================================
BRANDING = {
    'title': 'GROWTH HUB',
    'subtitle': '@codycsilva',
    'header_height': 80,
    'header_bg': BRAND_COLORS['charcoal'],
    'header_accent': BRAND_COLORS['forest_green'],
    # Font file basenames (module resolves full path from its own assets dir)
    'font_header': 'Anton-Regular.ttf',
    'font_title': 'RobotoCondensed.ttf',
    'font_body': 'Roboto-Regular.ttf',
    'font_accent': 'PlayfairDisplay-Italic.ttf',
}

# =====================================================================
# WATERMARK
# =====================================================================
WATERMARK_HANDLE = '@codycsilva'
