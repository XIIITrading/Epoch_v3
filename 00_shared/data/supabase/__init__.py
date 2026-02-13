"""
Epoch Trading System - Supabase Database Client
================================================

Centralized client for all Supabase/PostgreSQL operations.

Features:
- Zone data loading and saving
- Trade records management
- Analysis data storage
- Backtest results

Usage:
    from shared.data.supabase import SupabaseClient

    db = SupabaseClient()
    zones = db.get_zones("AAPL", date.today())
"""

from .client import SupabaseClient

__all__ = ["SupabaseClient"]
