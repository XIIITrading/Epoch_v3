"""
Candle Range Edge Analysis Module

CALC-011 implementation for testing Candle Range indicator edge.

Candle Range Calculation:
    candle_range_pct = (high - low) / open * 100

Key Thresholds:
    - < 0.12%: Absorption zone (SKIP filter)
    - >= 0.15%: Large range (momentum indicator)
    - >= 0.20%: Very large range (strong momentum)
"""

from .candle_range_edge import run_full_analysis, main

__all__ = ['run_full_analysis', 'main']
