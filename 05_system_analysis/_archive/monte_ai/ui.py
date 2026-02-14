"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - UI Component
XIII Trading LLC
================================================================================

Streamlit UI component for Monte AI prompt generation.
Provides a polished dropdown, "Generate Prompt" button, and copy functionality.

================================================================================
"""

import streamlit as st
from typing import Dict, Any, Optional, Callable
import pandas as pd

from monte_ai.prompt_generator import generate_prompt, generate_quick_prompt, get_prompt_stats
from monte_ai.prompts import TAB_PROMPTS


# =============================================================================
# UI CONFIGURATION
# =============================================================================

PROMPT_TYPES = {
    "full": {
        "label": "Full Analysis (with schema reference)",
        "description": "Complete prompt with database schema for first-time analysis",
        "include_schema": True
    },
    "quick": {
        "label": "Quick Analysis (data only)",
        "description": "Shorter prompt for follow-up queries in same session",
        "include_schema": False
    }
}


# =============================================================================
# MAIN UI COMPONENT
# =============================================================================

def render_monte_ai_section(
    tab_name: str,
    tab_data: Dict[str, Any],
    section_title: str = "Monte AI Research Assistant",
    expanded: bool = False
):
    """
    Render the Monte AI prompt generation section.

    Prompt is auto-generated on page load (no button required).

    Args:
        tab_name: Name of the current tab (e.g., "metrics_overview")
        tab_data: Dictionary of data to include in the prompt
        section_title: Title for the expander section
        expanded: Whether the section is initially expanded
    """
    # Check if tab has prompts configured
    if tab_name not in TAB_PROMPTS:
        st.info(f"Monte AI prompts not yet configured for this tab.")
        return

    with st.expander(f"🔬 {section_title}", expanded=expanded):
        st.markdown("""
        **Monte AI** helps you analyze trading system data using Claude's capabilities.
        Copy the prompt below and paste into Claude Desktop for deep analysis.
        """)

        st.markdown("---")

        # Prompt type selection
        prompt_type = st.selectbox(
            "Prompt Type",
            options=list(PROMPT_TYPES.keys()),
            format_func=lambda x: PROMPT_TYPES[x]["label"],
            key=f"monte_prompt_type_{tab_name}",
            help="Full analysis includes database schema reference"
        )

        # Show description
        st.caption(PROMPT_TYPES[prompt_type]["description"])

        # Auto-generate prompt on page load
        include_schema = PROMPT_TYPES[prompt_type]["include_schema"]
        prompt = generate_prompt(
            tab_name=tab_name,
            tab_data=tab_data,
            include_schema=include_schema
        )

        # Get prompt statistics
        stats = get_prompt_stats(prompt)

        st.markdown("---")

        # Prompt statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Characters", f"{stats['characters']:,}")
        with col2:
            st.metric("Words", f"{stats['words']:,}")
        with col3:
            st.metric("Lines", f"{stats['lines']:,}")
        with col4:
            st.metric("Est. Tokens", f"~{stats['estimated_tokens']:,}")

        st.markdown("---")

        # Display prompt in code block
        st.markdown("**Generated Prompt:**")
        st.code(prompt, language=None)

        # Action buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            # Download button
            st.download_button(
                label="📥 Download as TXT",
                data=prompt,
                file_name=f"monte_ai_{tab_name}.txt",
                mime="text/plain",
                key=f"monte_download_{tab_name}",
                use_container_width=True
            )

        with col2:
            # Copy button (JavaScript-based)
            _render_copy_button(prompt, f"copy_{tab_name}")

        # Instructions
        st.markdown("---")
        st.markdown("""
        **How to use:**
        1. Click **Copy to Clipboard** (or download the file)
        2. Open **Claude Desktop** (or claude.ai)
        3. Paste the prompt and submit
        4. Review Claude's analysis and recommendations
        """)


def _render_copy_button(text: str, key: str):
    """
    Render a JavaScript-based copy-to-clipboard button.

    Args:
        text: Text to copy
        key: Unique key for the button
    """
    # Escape the text for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace("'", "\\'")

    copy_button_html = f"""
    <style>
    .monte-copy-btn {{
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        cursor: pointer;
        border-radius: 4px;
        width: 100%;
        transition: background-color 0.3s;
    }}
    .monte-copy-btn:hover {{
        background-color: #45a049;
    }}
    .monte-copy-btn.copied {{
        background-color: #2196F3;
    }}
    </style>
    <button class="monte-copy-btn" onclick="monteCopyToClipboard_{key}()" id="monte_btn_{key}">
        📋 Copy to Clipboard
    </button>
    <script>
    function monteCopyToClipboard_{key}() {{
        const text = `{escaped_text}`;
        navigator.clipboard.writeText(text).then(function() {{
            const btn = document.getElementById('monte_btn_{key}');
            btn.textContent = '✅ Copied!';
            btn.classList.add('copied');
            setTimeout(function() {{
                btn.textContent = '📋 Copy to Clipboard';
                btn.classList.remove('copied');
            }}, 2000);
        }}, function(err) {{
            console.error('Could not copy text: ', err);
            alert('Copy failed. Please use the download button instead.');
        }});
    }}
    </script>
    """

    st.components.v1.html(copy_button_html, height=45)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def render_metrics_overview_monte_ai(
    model_stats: pd.DataFrame,
    overall_stats: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    available_calculations: Optional[list] = None,
    mfe_mae_stats: Optional[Dict[str, Any]] = None,
    mfe_mae_by_model: Optional[pd.DataFrame] = None,
    sequence_stats: Optional[Dict[str, Any]] = None,
    simulated_stats: Optional[Dict[str, Any]] = None,
    stop_analysis: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to render Monte AI for Metrics Overview tab.

    Args:
        model_stats: DataFrame from calculate_win_rate_by_model
        overall_stats: Dict with overall statistics
        filters: Current filter state
        available_calculations: List of available calculations
        mfe_mae_stats: Dict with MFE/MAE summary statistics from calculate_mfe_mae_summary
        mfe_mae_by_model: DataFrame with MFE/MAE stats by model from calculate_mfe_mae_by_model
        sequence_stats: Dict with MFE/MAE sequence statistics from calculate_sequence_summary
        simulated_stats: Dict with simulated outcome statistics from calculate_simulated_stats
        stop_analysis: Dict with stop type analysis results from render_stop_analysis_section_simple
    """
    tab_data = {
        "model_stats": model_stats,
        "overall_stats": overall_stats,
        "filters": filters,
        "available_calculations": available_calculations,
        "mfe_mae_stats": mfe_mae_stats,
        "mfe_mae_by_model": mfe_mae_by_model,
        "sequence_stats": sequence_stats,
        "simulated_stats": simulated_stats,
        "stop_analysis": stop_analysis
    }

    render_monte_ai_section(
        tab_name="metrics_overview",
        tab_data=tab_data,
        section_title="Monte AI - System Performance Analysis"
    )


# =============================================================================
# INDICATOR ANALYSIS MONTE AI
# =============================================================================

def render_indicator_analysis_monte_ai(
    calc_005_result=None,
    calc_006_result=None,
    calc_007_result=None,
    calc_008_result=None
):
    """
    Render Monte AI section for Indicator Analysis tab.

    Prompt is auto-generated on page load (no button required).

    Parameters:
        calc_005_result: HealthCorrelationResult (optional)
        calc_006_result: FactorImportanceResult (optional)
        calc_007_result: IndicatorProgressionResult (optional)
        calc_008_result: RejectionDynamicsResult (optional)
    """
    from .indicator_prompt_generator import (
        generate_calc_005_prompt,
        generate_calc_006_prompt,
        generate_calc_007_prompt,
        generate_calc_008_prompt,
        generate_synthesis_prompt
    )

    with st.expander("Monte AI - Indicator Analysis", expanded=False):
        st.markdown("""
        **Monte AI** synthesizes indicator analysis results and generates prompts
        for Claude to provide DOW AI configuration recommendations.
        Copy the prompt below and paste into Claude Desktop for deep analysis.
        """)

        st.markdown("---")

        # Check what results are available
        available = []
        if calc_005_result:
            available.append("CALC-005: Health Correlation")
        if calc_006_result:
            available.append("CALC-006: Factor Importance")
        if calc_007_result:
            available.append("CALC-007: Progression")
        if calc_008_result:
            available.append("CALC-008: Rejection Dynamics")

        if not available:
            st.warning("No analysis results available. Run the CALC modules first.")
            st.info("Navigate through the CALC-005 to CALC-008 tabs to generate analysis results.")
            return

        st.success(f"**Available Results:** {', '.join(available)}")

        # Analysis type selector
        analysis_options = ["Synthesis (All Available)"]
        if calc_005_result:
            analysis_options.append("CALC-005: Health Correlation")
        if calc_006_result:
            analysis_options.append("CALC-006: Factor Importance")
        if calc_007_result:
            analysis_options.append("CALC-007: Progression")
        if calc_008_result:
            analysis_options.append("CALC-008: Rejection Dynamics")

        selected_analysis = st.selectbox(
            "Select Analysis Type",
            analysis_options,
            key="indicator_monte_analysis_type"
        )

        # Auto-generate prompt on page load
        try:
            if selected_analysis == "Synthesis (All Available)":
                prompt = generate_synthesis_prompt(
                    calc_005_result, calc_006_result, calc_007_result, calc_008_result
                )
            elif "CALC-005" in selected_analysis and calc_005_result:
                prompt = generate_calc_005_prompt(calc_005_result)
            elif "CALC-006" in selected_analysis and calc_006_result:
                prompt = generate_calc_006_prompt(calc_006_result)
            elif "CALC-007" in selected_analysis and calc_007_result:
                prompt = generate_calc_007_prompt(calc_007_result)
            elif "CALC-008" in selected_analysis and calc_008_result:
                prompt = generate_calc_008_prompt(calc_008_result)
            else:
                st.warning(f"No results available for {selected_analysis}")
                return

        except Exception as e:
            st.error(f"Error generating prompt: {e}")
            import traceback
            st.code(traceback.format_exc())
            return

        st.markdown("---")

        # Prompt statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Analysis Type", prompt.analysis_type.split(":")[0])
        with col2:
            st.metric("Est. Tokens", f"~{prompt.estimated_tokens:,}")
        with col3:
            st.metric("Data Length", f"{len(prompt.data_summary):,} chars")

        st.markdown("---")

        # Full prompt text area
        full_prompt = f"{prompt.system_prompt}\n\n---\n\n{prompt.user_prompt}"

        st.code(full_prompt, language=None)

        # Action buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            st.download_button(
                label="📥 Download as TXT",
                data=full_prompt,
                file_name=f"monte_ai_{prompt.analysis_type.lower().replace(' ', '_').replace(':', '')}.txt",
                mime="text/plain",
                key="indicator_monte_download",
                use_container_width=True
            )

        with col2:
            _render_copy_button(full_prompt, "indicator_monte")

        # Instructions
        st.markdown("---")
        st.markdown("""
        **How to use:**
        1. Click **Copy to Clipboard** (or download the file)
        2. Open **Claude Desktop** (or claude.ai)
        3. Paste the prompt and submit
        4. Review Claude's analysis and DOW AI recommendations
        """)


# =============================================================================
# INDICATOR REFINEMENT MONTE AI
# =============================================================================

def render_indicator_refinement_monte_ai(
    refinement_df: pd.DataFrame
):
    """
    Render Monte AI section for Indicator Refinement tab.

    Prompt is auto-generated on page load (no button required).

    Parameters:
        refinement_df: DataFrame with indicator refinement data (both trade types)
    """
    from .refinement_prompt_generator import (
        generate_continuation_prompt,
        generate_rejection_prompt,
        generate_refinement_synthesis_prompt
    )

    with st.expander("Monte AI - Indicator Refinement Analysis", expanded=False):
        st.markdown("""
        **Monte AI** synthesizes Continuation and Rejection qualification scores
        and generates prompts for Claude to provide optimization recommendations.
        Copy the prompt below and paste into Claude Desktop for deep analysis.
        """)

        st.markdown("---")

        # Check if data is available
        if refinement_df is None or refinement_df.empty:
            st.warning("No indicator refinement data available. Run CALC-010 first.")
            st.info("""
            **To populate indicator_refinement table:**
            ```bash
            cd C:\\XIIITradingSystems\\Epoch\\02_zone_system\\09_backtest\\processor\\secondary_analysis\\indicator_refinement
            python runner.py --schema  # Create table first
            python runner.py           # Full calculation
            ```
            """)
            return

        # Split by trade type
        cont_df = refinement_df[refinement_df['trade_type'] == 'CONTINUATION'].copy()
        rej_df = refinement_df[refinement_df['trade_type'] == 'REJECTION'].copy()

        # Show available data
        available = []
        if len(cont_df) > 0:
            available.append(f"Continuation ({len(cont_df):,} trades)")
        if len(rej_df) > 0:
            available.append(f"Rejection ({len(rej_df):,} trades)")

        if available:
            st.success(f"**Available Data:** {', '.join(available)}")
        else:
            st.warning("No trades found in refinement data.")
            return

        # Analysis type selector
        analysis_options = ["Synthesis (Both Trade Types)"]
        if len(cont_df) > 0:
            analysis_options.append("Continuation Only")
        if len(rej_df) > 0:
            analysis_options.append("Rejection Only")

        selected_analysis = st.selectbox(
            "Select Analysis Type",
            analysis_options,
            key="refinement_monte_analysis_type"
        )

        # Auto-generate prompt on page load
        try:
            if selected_analysis == "Synthesis (Both Trade Types)":
                prompt = generate_refinement_synthesis_prompt(cont_df, rej_df)
            elif selected_analysis == "Continuation Only":
                prompt = generate_continuation_prompt(cont_df)
            elif selected_analysis == "Rejection Only":
                prompt = generate_rejection_prompt(rej_df)
            else:
                st.warning(f"No results available for {selected_analysis}")
                return

        except Exception as e:
            st.error(f"Error generating prompt: {e}")
            import traceback
            st.code(traceback.format_exc())
            return

        st.markdown("---")

        # Prompt statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Analysis Type", prompt.analysis_type.split(":")[0] if ":" in prompt.analysis_type else prompt.analysis_type)
        with col2:
            st.metric("Est. Tokens", f"~{prompt.estimated_tokens:,}")
        with col3:
            st.metric("Data Length", f"{len(prompt.data_summary):,} chars")

        st.markdown("---")

        # Full prompt text area
        full_prompt = f"{prompt.system_prompt}\n\n---\n\n{prompt.user_prompt}"

        st.code(full_prompt, language=None)

        # Action buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            st.download_button(
                label="Download as TXT",
                data=full_prompt,
                file_name=f"monte_ai_{prompt.analysis_type.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                key="refinement_monte_download",
                use_container_width=True
            )

        with col2:
            _render_copy_button(full_prompt, "refinement_monte")

        # Instructions
        st.markdown("---")
        st.markdown("""
        **How to use:**
        1. Click **Copy to Clipboard** (or download the file)
        2. Open **Claude Desktop** (or claude.ai)
        3. Paste the prompt and submit
        4. Review Claude's analysis and score optimization recommendations
        """)
