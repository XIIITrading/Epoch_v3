"""
Epoch Trading System - Data Layer
==================================

Centralized data access for all Epoch modules.

Provides:
- Polygon.io client for market data
- Supabase client for database operations
- Caching and rate limiting

Usage:
    from shared.data.polygon import PolygonClient
    from shared.data.supabase import SupabaseClient

    # Get market data
    client = PolygonClient()
    df = client.get_bars("AAPL", "5min", start_date, end_date)

    # Get database data
    db = SupabaseClient()
    zones = db.get_zones("AAPL", date.today())
"""

from .polygon import PolygonClient
from .supabase import SupabaseClient

__all__ = ["PolygonClient", "SupabaseClient"]
