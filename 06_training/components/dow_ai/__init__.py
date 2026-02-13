"""
DOW AI Prompt Generator Module for Epoch Training System.

Generates copy-paste prompts for Claude Desktop analysis of:
- Pre-trade entry evaluation (with footprint metrics)
- Post-trade review and exit signal analysis

Streamlit UI components archived in _archive_streamlit/.
"""

from .prompt_generator import generate_pre_trade_prompt, generate_post_trade_prompt
from .data_fetcher import DOWAIDataFetcher

__all__ = [
    'generate_pre_trade_prompt',
    'generate_post_trade_prompt',
    'DOWAIDataFetcher',
]
