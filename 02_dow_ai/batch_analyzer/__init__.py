"""
DOW AI Batch Analyzer Module
Epoch Trading System v1 - XIII Trading LLC

Runs Claude AI analysis on historical backtest trades at scale.
Stores predictions in Supabase for accuracy tracking and training integration.

Usage:
    python -m batch_analyzer.scripts.run_batch --date-range 2025-12-15 2026-01-22
    python -m batch_analyzer.scripts.run_batch --limit 100
    python -m batch_analyzer.scripts.accuracy_report
"""

__version__ = "1.0.0"
__author__ = "XIII Trading LLC"
