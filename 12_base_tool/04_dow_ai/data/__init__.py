"""
DOW AI - Data Module
Handles data fetching from Polygon API, Excel workbook, and Supabase.
"""

from .data_models import (
    BarData,
    MarketStructureResult,
    VolumeAnalysis,
    CandlestickPattern,
    ZoneContext,
    AnalysisRequest,
    AnalysisResult
)
from .polygon_fetcher import PolygonFetcher
from .epoch_reader import EpochReader
from .supabase_reader import SupabaseReader

__all__ = [
    'BarData',
    'MarketStructureResult',
    'VolumeAnalysis',
    'CandlestickPattern',
    'ZoneContext',
    'AnalysisRequest',
    'AnalysisResult',
    'PolygonFetcher',
    'EpochReader',
    'SupabaseReader'
]
