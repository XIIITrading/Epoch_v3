"""
Epoch Trading System - Polygon.io Data Client
==============================================

Centralized client for all Polygon.io API operations.

Features:
- Bar data fetching (M1, M5, M15, H1, H4, D1)
- Rate limiting and caching
- Websocket support for live data
- Error handling and retries

Usage:
    from shared.data.polygon import PolygonClient

    client = PolygonClient()
    df = client.get_bars("AAPL", "5min", "2024-01-01", "2024-01-31")
"""

from .client import PolygonClient

__all__ = ["PolygonClient"]
