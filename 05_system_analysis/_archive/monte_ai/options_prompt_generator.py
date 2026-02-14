"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Options Prompt Generator
XIII Trading LLC
================================================================================

Assembles complete prompts for Options Analysis tab by combining:
1. Options context (from options_prompts.py)
2. Section-specific background and analysis requests (from options_prompts.py)
3. Current options data

================================================================================
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from monte_ai.options_prompts import (
    OPTIONS_CONTEXT,
    OPTIONS_DATA_SCHEMA,
    get_options_tab_prompt,
    get_options_full_prompt_template,
    format_options_mfe_mae_stats,
    format_options_leverage_stats,
    format_options_sequence_stats,
    format_options_win_rate_by_model,
    format_options_win_rate_with_stop,
    format_options_filters,
    format_options_stop_analysis,
    format_options_simulated_outcomes
)


# =============================================================================
# DATA COLLECTION FOR OPTIONS
# =============================================================================

def collect_options_data(
    section_name: str,
    mfe_mae_stats: Dict[str, Any] = None,
    model_stats: Any = None,
    sequence_stats: Dict[str, Any] = None,
    leverage_stats: Dict[str, Any] = None,
    stop_analysis: Dict[str, Any] = None,
    simulated_stats: Dict[str, Any] = None,
    filters: Dict[str, Any] = None,
    raw_data: List[Dict[str, Any]] = None,
    stop_name: str = "25%"
) -> str:
    """
    Collect and format all options data for a prompt.

    Args:
        section_name: Name of the section being analyzed
        mfe_mae_stats: Output from calculate_options_mfe_mae_summary()
        model_stats: Output from calculate_options_win_rate_by_model() or similar
        sequence_stats: Output from calculate_options_sequence_summary()
        leverage_stats: Output from calculate_leverage_comparison()
        stop_analysis: Output from render_op_stop_analysis_section()
        simulated_stats: Output from render_simulated_outcomes_section()
        filters: Current filter settings
        raw_data: Raw options data records (optional, for sample)
        stop_name: Display name of stop type used for model stats

    Returns:
        Formatted string of all data for prompt
    """
    sections = []

    # Filters
    if filters:
        sections.append(format_options_filters(filters))
        sections.append("")

    # Stop Analysis (CALC-O09) - NEW
    if stop_analysis:
        sections.append(format_options_stop_analysis(stop_analysis))
        sections.append("")

    # Win Rate by Model (using stop-based outcomes)
    if model_stats is not None:
        sections.append(format_options_win_rate_with_stop(model_stats, stop_name))
        sections.append("")

    # MFE/MAE Statistics
    if mfe_mae_stats:
        sections.append(format_options_mfe_mae_stats(mfe_mae_stats))
        sections.append("")

    # Sequence/Timing Statistics
    if sequence_stats:
        sections.append(format_options_sequence_stats(sequence_stats))
        sections.append("")

    # Simulated Outcomes (CALC-O05) - NEW
    if simulated_stats:
        sections.append(format_options_simulated_outcomes(simulated_stats))
        sections.append("")

    # Leverage Statistics
    if leverage_stats:
        sections.append(format_options_leverage_stats(leverage_stats))
        sections.append("")

    # Sample data (if provided)
    if raw_data and len(raw_data) > 0:
        sections.append("SAMPLE OPTIONS DATA (first 10 records):")
        sections.append("-" * 60)

        sample = raw_data[:10] if len(raw_data) > 10 else raw_data
        for record in sample:
            ticker = record.get('ticker', 'N/A')
            model = record.get('model', 'N/A')
            contract = record.get('contract_type', 'N/A')
            mfe = record.get('mfe_pct', 0)
            mae = record.get('mae_pct', 0)
            exit_pct = record.get('exit_pct', 0)
            sections.append(
                f"  {ticker} | {model} | {contract} | MFE:{mfe:.1f}% MAE:{mae:.1f}% Exit:{exit_pct:.1f}%"
            )

        sections.append("")

    if not sections:
        sections.append("No data available for this section.")

    return "\n".join(sections)


# =============================================================================
# PROMPT GENERATION
# =============================================================================

def generate_options_prompt(
    section_name: str,
    mfe_mae_stats: Dict[str, Any] = None,
    model_stats: Any = None,
    sequence_stats: Dict[str, Any] = None,
    leverage_stats: Dict[str, Any] = None,
    stop_analysis: Dict[str, Any] = None,
    simulated_stats: Dict[str, Any] = None,
    filters: Dict[str, Any] = None,
    raw_data: List[Dict[str, Any]] = None,
    stop_name: str = "25%",
    include_schema: bool = True,
    include_timestamp: bool = True
) -> str:
    """
    Generate a complete options analysis prompt.

    Args:
        section_name: Name of the section (e.g., "options_overview")
        mfe_mae_stats: MFE/MAE summary statistics
        model_stats: Win rate by model statistics
        sequence_stats: Timing/sequence statistics
        leverage_stats: Options vs underlying leverage statistics
        stop_analysis: Stop type analysis results (CALC-O09)
        simulated_stats: Simulated outcomes results (CALC-O05)
        filters: Current filter settings
        raw_data: Raw options data records (for sample)
        stop_name: Display name of stop type used
        include_schema: Whether to include database schema reference
        include_timestamp: Whether to include generation timestamp

    Returns:
        Complete prompt string ready for copy-paste to Claude
    """
    # Get section configuration
    section_config = get_options_tab_prompt(section_name)

    # Collect and format data
    data_section = collect_options_data(
        section_name=section_name,
        mfe_mae_stats=mfe_mae_stats,
        model_stats=model_stats,
        sequence_stats=sequence_stats,
        leverage_stats=leverage_stats,
        stop_analysis=stop_analysis,
        simulated_stats=simulated_stats,
        filters=filters,
        raw_data=raw_data,
        stop_name=stop_name
    )

    # Build the complete prompt
    sections = []

    # Header with timestamp
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# Monte AI OPTIONS Analysis Request - Generated {timestamp}")
        sections.append("")

    # System context
    sections.append(OPTIONS_CONTEXT)
    sections.append("")

    # Section-specific header
    sections.append("=" * 80)
    sections.append(f"  {section_config['title'].upper()}")
    sections.append("=" * 80)
    sections.append("")

    # Section background
    sections.append(section_config['background'].strip())
    sections.append("")

    # Database schema reference (optional)
    if include_schema:
        sections.append("=" * 80)
        sections.append("  OPTIONS DATA REFERENCE")
        sections.append("=" * 80)
        sections.append(OPTIONS_DATA_SCHEMA)
        sections.append("")

    # Analysis request
    sections.append("=" * 80)
    sections.append("  ANALYSIS REQUEST")
    sections.append("=" * 80)
    sections.append(section_config['analysis_request'].strip())
    sections.append("")

    # Data section
    sections.append("=" * 80)
    sections.append("  DATA FROM CURRENT VIEW")
    sections.append("=" * 80)
    sections.append("")
    sections.append(data_section)

    return "\n".join(sections)


def generate_options_quick_prompt(
    section_name: str,
    mfe_mae_stats: Dict[str, Any] = None,
    model_stats: Any = None,
    sequence_stats: Dict[str, Any] = None,
    leverage_stats: Dict[str, Any] = None,
    filters: Dict[str, Any] = None
) -> str:
    """
    Generate a shorter options prompt without schema reference.
    Useful for follow-up queries in the same session.

    Args:
        section_name: Name of the section
        (other args same as generate_options_prompt)

    Returns:
        Shorter prompt string
    """
    return generate_options_prompt(
        section_name=section_name,
        mfe_mae_stats=mfe_mae_stats,
        model_stats=model_stats,
        sequence_stats=sequence_stats,
        leverage_stats=leverage_stats,
        filters=filters,
        include_schema=False,
        include_timestamp=True
    )


# =============================================================================
# PROMPT STATISTICS
# =============================================================================

def get_options_prompt_stats(prompt: str) -> Dict[str, int]:
    """
    Get statistics about a generated options prompt.

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


# =============================================================================
# CONVENIENCE FUNCTIONS FOR UI
# =============================================================================

def generate_options_overview_prompt(
    mfe_mae_stats: Dict[str, Any] = None,
    model_stats: Any = None,
    sequence_stats: Dict[str, Any] = None,
    leverage_stats: Dict[str, Any] = None,
    stop_analysis: Dict[str, Any] = None,
    simulated_stats: Dict[str, Any] = None,
    filters: Dict[str, Any] = None,
    stop_name: str = "25%"
) -> str:
    """
    Generate the main Options Overview analysis prompt.

    This is the primary prompt for the Options Analysis tab.

    Args:
        mfe_mae_stats: MFE/MAE summary statistics
        model_stats: Win rate by model statistics (stop-based)
        sequence_stats: Timing/sequence statistics
        leverage_stats: Options vs underlying leverage statistics
        stop_analysis: Stop type analysis results (CALC-O09)
        simulated_stats: Simulated outcomes results (CALC-O05)
        filters: Current filter settings
        stop_name: Display name of stop type used (default: "25%")

    Returns:
        Complete prompt string ready for copy-paste to Claude

    Note:
        This prompt always uses the default stop type (25%) for consistency
        and reproducibility, regardless of what the user selected in the UI.
    """
    return generate_options_prompt(
        section_name="options_overview",
        mfe_mae_stats=mfe_mae_stats,
        model_stats=model_stats,
        sequence_stats=sequence_stats,
        leverage_stats=leverage_stats,
        stop_analysis=stop_analysis,
        simulated_stats=simulated_stats,
        filters=filters,
        stop_name=stop_name,
        include_schema=True
    )


def generate_options_mfe_mae_prompt(
    mfe_mae_stats: Dict[str, Any],
    model_stats: Any = None,
    filters: Dict[str, Any] = None
) -> str:
    """
    Generate focused MFE/MAE distribution analysis prompt.
    """
    return generate_options_prompt(
        section_name="options_mfe_mae",
        mfe_mae_stats=mfe_mae_stats,
        model_stats=model_stats,
        filters=filters,
        include_schema=False
    )


def generate_options_leverage_prompt(
    leverage_stats: Dict[str, Any],
    mfe_mae_stats: Dict[str, Any] = None,
    filters: Dict[str, Any] = None
) -> str:
    """
    Generate focused leverage analysis prompt.
    """
    return generate_options_prompt(
        section_name="options_vs_underlying",
        leverage_stats=leverage_stats,
        mfe_mae_stats=mfe_mae_stats,
        filters=filters,
        include_schema=False
    )
