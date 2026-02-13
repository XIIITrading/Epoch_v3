"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
H1 Bars Storage Module
XIII Trading LLC
================================================================================

Fetches and stores 1-hour bar data from Polygon API to Supabase.
Used for H1 market structure analysis in the training module.

Stores ~30 H1 bars before market open plus trading day bars for each
unique ticker-date combination from the trades table.

Version: 1.0.0
================================================================================
"""

from .h1_bars_storage import H1BarsStorage
from .h1_fetcher import H1Fetcher

__all__ = ['H1BarsStorage', 'H1Fetcher']
__version__ = '1.0.0'
