"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Research Assistant for Trading System Optimization
XIII Trading LLC
================================================================================

Monte AI is a research assistant designed to help optimize the Epoch trading
system using statistical methods and Claude's analytical capabilities.

Unlike DOW AI (trading assistant for entry decisions), Monte AI focuses on:
- Statistical analysis of system performance
- Indicator effectiveness evaluation
- Recommendations for system improvements
- Identification of new indicators/structures to investigate

Usage:
    from monte_ai import render_monte_ai_section

    # In your Streamlit tab:
    render_monte_ai_section(
        tab_name="metrics_overview",
        tab_data={"model_stats": model_stats, "overall_stats": overall_stats}
    )

================================================================================
"""

from monte_ai.ui import render_monte_ai_section, render_indicator_analysis_monte_ai, render_indicator_refinement_monte_ai
from monte_ai.prompt_generator import generate_prompt
from monte_ai.data_collector import collect_tab_data
from monte_ai.indicator_prompt_generator import (
    generate_calc_005_prompt,
    generate_calc_006_prompt,
    generate_calc_007_prompt,
    generate_calc_008_prompt,
    generate_synthesis_prompt,
    IndicatorAnalysisPrompt
)
from monte_ai.refinement_prompt_generator import (
    generate_continuation_prompt,
    generate_rejection_prompt,
    generate_refinement_synthesis_prompt,
    RefinementAnalysisPrompt
)

__all__ = [
    "render_monte_ai_section",
    "render_indicator_analysis_monte_ai",
    "render_indicator_refinement_monte_ai",
    "generate_prompt",
    "collect_tab_data",
    "generate_calc_005_prompt",
    "generate_calc_006_prompt",
    "generate_calc_007_prompt",
    "generate_calc_008_prompt",
    "generate_synthesis_prompt",
    "IndicatorAnalysisPrompt",
    "generate_continuation_prompt",
    "generate_rejection_prompt",
    "generate_refinement_synthesis_prompt",
    "RefinementAnalysisPrompt",
]
