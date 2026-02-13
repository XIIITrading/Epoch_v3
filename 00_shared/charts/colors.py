"""
Epoch Trading System - Chart Color Definitions
===============================================

Single source of truth for all chart rendering colors across Plotly,
Matplotlib, and PIL image export.

Two palette variants:
- EPOCH_DARK: Standard dark theme (#1a1a2e bg) used by most modules
- TV_DARK: TradingView-style dark theme (#000000 bg) used by trade_reel

Both share the same semantic key names so chart code can be palette-agnostic.
"""

# =====================================================================
# EPOCH DARK PALETTE (01_application, 05_system_analysis, 06_training)
# =====================================================================
EPOCH_DARK = {
    # Layout
    'background': '#1C1C1C',
    'paper': '#1C1C1C',
    'grid': '#2a2a4e',
    'text': '#e0e0e0',
    'text_muted': '#888888',

    # Candlesticks
    'candle_up': '#26a69a',
    'candle_down': '#ef5350',

    # Direction
    'bull': '#26a69a',
    'bear': '#ef5350',
    'neutral': '#888888',

    # Zone overlay
    'zone_primary': '#90bff9',
    'zone_secondary': '#faa1a4',
    'zone_opacity': 0.15,
    'zone_fill': 'rgba(144,191,249,0.15)',
    'zone_fill_secondary': 'rgba(250,161,164,0.15)',
    'zone_border': '#90bff9',
    'pivot_purple': '#b19cd9',

    # Trade markers
    'entry': '#00C853',
    'exit': '#FF1744',
    'stop': '#FF1744',
    'mfe': '#2196F3',
    'mae': '#FF9800',

    # R-level targets
    'r1': '#4CAF50',
    'r2': '#8BC34A',
    'r3': '#CDDC39',
    'r4': '#FF9800',
    'r5': '#00C853',
    'eod': '#9C27B0',

    # POC lines
    'poc': '#FFFFFF',
    'poc_opacity': 0.3,

    # Chart layout (matplotlib table/section backgrounds)
    'table_bg': '#0f0f1a',
    'notes_bg': '#0a0a12',
    'dark_bg_lighter': '#16213e',
    'text_dim': '#666666',
    'border': '#333333',
    'border_light': '#444444',

    # VbP
    'vbp': '#5c6bc0',
    'vbp_overlay': 'rgba(195,195,195,0.30)',

    # Analytics
    'win': '#26a69a',
    'loss': '#ef5350',
    'continuation': '#2196F3',
    'rejection': '#FF9800',
    'long': '#00C853',
    'short': '#FF1744',
    'strong': '#00C853',
    'moderate': '#FFC107',
    'weak': '#FF9800',
    'critical': '#FF1744',
}

# =====================================================================
# TRADINGVIEW DARK PALETTE (11_trade_reel)
# =====================================================================
TV_DARK = {
    # Layout
    'background': '#000000',
    'paper': '#000000',
    'grid': '#2A2E39',
    'text': '#D1D4DC',
    'text_muted': '#787B86',

    # Candlesticks (muted: TradingView colors at 50% on black)
    'candle_up': '#13534D',
    'candle_down': '#782A28',

    # Direction (full-intensity TradingView)
    'bull': '#089981',
    'bear': '#F23645',
    'neutral': '#787B86',

    # Zone overlay
    'zone_primary': '#90bff9',
    'zone_secondary': '#faa1a4',
    'zone_opacity': 0.15,
    'zone_fill': 'rgba(41,98,255,0.12)',
    'zone_fill_secondary': 'rgba(250,161,164,0.15)',
    'zone_border': '#2962FF',
    'pivot_purple': '#b19cd9',

    # Trade markers
    'entry': '#2962FF',
    'exit': '#F23645',
    'stop': '#F23645',
    'mfe': '#2962FF',
    'mae': '#FF9800',

    # R-level colors (gradient from teal to green)
    'r1': '#26A69A',
    'r2': '#089981',
    'r3': '#FF9800',
    'r4': '#FF6F00',
    'r5': '#00C853',
    'eod': '#9C27B0',

    # POC lines
    'poc': '#FFFFFF',
    'poc_opacity': 0.3,

    # VbP
    'vbp': '#5c6bc0',
    'vbp_overlay': 'rgba(195,195,195,0.30)',

    # Analytics
    'win': '#089981',
    'loss': '#F23645',
    'continuation': '#2196F3',
    'rejection': '#FF9800',
    'long': '#00C853',
    'short': '#FF1744',
    'strong': '#00C853',
    'moderate': '#FFC107',
    'weak': '#FF9800',
    'critical': '#FF1744',
}

# =====================================================================
# TRADINGVIEW UI COLORS (for PyQt TradingView-themed windows)
# =====================================================================
TV_UI = {
    'bg_primary': '#131722',
    'bg_secondary': '#1E222D',
    'border': '#2A2E39',
    'accent': '#2962FF',
    'accent_hover': '#1E4BD8',
    'bull': '#089981',
    'bear': '#F23645',
    'text_primary': '#D1D4DC',
    'text_muted': '#787B86',
    'text_white': '#FFFFFF',
}

# =====================================================================
# SHARED SEMANTIC COLORS (identical across all modules)
# =====================================================================
RANK_COLORS = {
    'L5': '#00C853',    # Green - best
    'L4': '#2196F3',    # Blue
    'L3': '#FFC107',    # Yellow/Amber
    'L2': '#9E9E9E',    # Gray
    'L1': '#616161',    # Dark gray
}

TIER_COLORS = {
    'T3': '#00C853',    # Green - High Quality (L4-L5)
    'T2': '#FFC107',    # Yellow/Amber - Medium Quality (L3)
    'T1': '#9E9E9E',    # Gray - Lower Quality (L1-L2)
}

INDICATOR_REFINEMENT_COLORS = {
    # Trade type
    'continuation': '#4CAF50',
    'rejection': '#FF9800',
    # Score labels
    'strong': '#00C853',
    'good': '#8BC34A',
    'weak': '#FF9800',
    'avoid': '#FF1744',
    # Boolean indicators
    'aligned': '#00C853',
    'divergent': '#FF1744',
    'neutral': '#888888',
}

# =====================================================================
# PLOTLY COLORWAY (standard trace cycle)
# =====================================================================
COLORWAY_DEFAULT = [
    '#2962FF', '#089981', '#F23645', '#FF9800',
    '#7c3aed', '#3b82f6', '#10b981', '#f59e0b',
]
