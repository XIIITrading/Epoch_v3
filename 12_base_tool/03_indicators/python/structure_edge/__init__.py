"""
Market Structure Edge Analysis Module

CALC-011 implementation for testing multi-timeframe market structure indicator edge.
Tests H4, H1, M15, M5 structure direction and alignment with trade direction.
"""

from .structure_edge import run_full_analysis, main

__all__ = ['run_full_analysis', 'main']
