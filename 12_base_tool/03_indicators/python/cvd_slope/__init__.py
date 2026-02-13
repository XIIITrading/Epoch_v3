"""
CVD Slope Edge Analysis Module

CALC-011 implementation for testing CVD Slope (Cumulative Volume Delta Slope) indicator edge.

CVD Slope measures the trend/direction of cumulative volume delta:
- Positive slope = CVD rising = increasing buying pressure (bullish order flow)
- Negative slope = CVD falling = increasing selling pressure (bearish order flow)

Key Tests:
- Direction: POSITIVE vs NEGATIVE
- Alignment: Does slope match trade direction?
- Magnitude: Quintile analysis of absolute slope
- Extreme: Top/bottom 20% vs normal
"""

from .cvd_slope_edge import run_full_analysis, main

__all__ = ['run_full_analysis', 'main']
