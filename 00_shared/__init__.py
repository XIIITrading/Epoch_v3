"""
Epoch Trading System - Shared Infrastructure
============================================

This package provides centralized infrastructure for all Epoch modules:
- Configuration and credentials management
- Data clients (Polygon, Supabase)
- Shared indicator library
- Common data models
- PyQt UI components
- Utility functions

Installation:
    pip install -e ./00_shared

Usage:
    from shared.config import credentials
    from shared.data.polygon import PolygonClient
    from shared.data.supabase import SupabaseClient
    from shared.indicators.core import sma, vwap, atr
    from shared.ui.base_window import BaseWindow
"""

__version__ = "2.0.0"
__author__ = "XIII Trading Systems"
