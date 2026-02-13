"""
DOW AI - Analysis Module
Aggregates data and interfaces with Claude API.
"""

from .claude_client import ClaudeClient
from .aggregator import AnalysisAggregator

__all__ = [
    'ClaudeClient',
    'AnalysisAggregator'
]
