"""
Indicator Edge Testing Framework (CALC-011+)

Standalone modules to test individual indicators for statistical edge.
Run from terminal, outputs markdown reports for Claude analysis.

Usage:
    python -m calculations.indicator_edge.vwap_edge
    python -m calculations.indicator_edge.vwap_edge --models EPCH01,EPCH03
"""

from .base_tester import EdgeTestResult, fetch_entry_data
from .edge_report import generate_markdown_report, print_console_summary

__version__ = "1.0.0"
__all__ = [
    "EdgeTestResult",
    "fetch_entry_data",
    "generate_markdown_report",
    "print_console_summary",
]
