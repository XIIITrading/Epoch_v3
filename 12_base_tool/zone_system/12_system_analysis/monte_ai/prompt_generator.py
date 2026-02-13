"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Prompt Generator
XIII Trading LLC
================================================================================

Assembles complete prompts by combining:
1. System context (from prompts.py)
2. Tab-specific background and analysis requests (from prompts.py)
3. Current tab data (from data_collector.py)

================================================================================
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from monte_ai.prompts import (
    SYSTEM_CONTEXT,
    AVAILABLE_DATA_SCHEMA,
    get_tab_prompt,
    get_full_prompt_template
)
from monte_ai.data_collector import collect_tab_data


# =============================================================================
# PROMPT GENERATION
# =============================================================================

def generate_prompt(
    tab_name: str,
    tab_data: Dict[str, Any],
    include_schema: bool = True,
    include_timestamp: bool = True
) -> str:
    """
    Generate a complete prompt for a specific tab.

    Args:
        tab_name: Name of the tab (e.g., "metrics_overview")
        tab_data: Dictionary of data to include in the prompt
        include_schema: Whether to include the database schema reference
        include_timestamp: Whether to include generation timestamp

    Returns:
        Complete prompt string ready for copy-paste to Claude
    """
    # Get tab configuration
    tab_config = get_tab_prompt(tab_name)

    # Collect and format tab data
    data_section = collect_tab_data(tab_name, **tab_data)

    # Build the complete prompt
    sections = []

    # Header with timestamp
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# Monte AI Analysis Request - Generated {timestamp}")
        sections.append("")

    # System context
    sections.append(SYSTEM_CONTEXT)
    sections.append("")

    # Tab-specific header
    sections.append("=" * 80)
    sections.append(f"  {tab_config['title'].upper()}")
    sections.append("=" * 80)
    sections.append("")

    # Tab background
    sections.append(tab_config['background'].strip())
    sections.append("")

    # Database schema reference (optional)
    if include_schema:
        sections.append("=" * 80)
        sections.append("  AVAILABLE DATA REFERENCE")
        sections.append("=" * 80)
        sections.append(AVAILABLE_DATA_SCHEMA)
        sections.append("")

    # Analysis request
    sections.append("=" * 80)
    sections.append("  ANALYSIS REQUEST")
    sections.append("=" * 80)
    sections.append(tab_config['analysis_request'].strip())
    sections.append("")

    # Data section
    sections.append("=" * 80)
    sections.append("  DATA FROM CURRENT VIEW")
    sections.append("=" * 80)
    sections.append("")
    sections.append(data_section)

    return "\n".join(sections)


def generate_quick_prompt(
    tab_name: str,
    tab_data: Dict[str, Any]
) -> str:
    """
    Generate a shorter prompt without schema reference.
    Useful for follow-up queries in the same session.

    Args:
        tab_name: Name of the tab
        tab_data: Dictionary of data to include

    Returns:
        Shorter prompt string
    """
    return generate_prompt(
        tab_name=tab_name,
        tab_data=tab_data,
        include_schema=False,
        include_timestamp=True
    )


# =============================================================================
# PROMPT STATISTICS
# =============================================================================

def get_prompt_stats(prompt: str) -> Dict[str, int]:
    """
    Get statistics about a generated prompt.

    Args:
        prompt: The generated prompt string

    Returns:
        Dict with character count, word count, line count
    """
    return {
        "characters": len(prompt),
        "words": len(prompt.split()),
        "lines": len(prompt.splitlines()),
        "estimated_tokens": len(prompt) // 4  # Rough estimate
    }
