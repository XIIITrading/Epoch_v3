"""
DOW AI Prompt Generator Module for Epoch Training System.

Generates copy-paste prompts for Claude Desktop analysis of:
- Pre-trade entry evaluation (with footprint metrics)
- Post-trade review and exit signal analysis
"""

from .prompt_generator import generate_pre_trade_prompt, generate_post_trade_prompt
from .data_fetcher import DOWAIDataFetcher
from .ui import render_dow_ai_section, render_pre_trade_dow_ai, render_post_trade_dow_ai

__all__ = [
    'generate_pre_trade_prompt',
    'generate_post_trade_prompt',
    'DOWAIDataFetcher',
    'render_dow_ai_section',
    'render_pre_trade_dow_ai',
    'render_post_trade_dow_ai',
]
