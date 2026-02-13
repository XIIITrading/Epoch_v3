"""
DOW AI UI Component - Renders copy-paste prompt sections in the training module.

Provides expandable sections with copy-to-clipboard functionality for
both pre-trade and post-trade prompts. Also handles saving/displaying
Claude's analysis responses.
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.trade import TradeWithMetrics, TradeAnalysis
from components.dow_ai.data_fetcher import DOWAIDataFetcher
from components.dow_ai.prompt_generator import generate_pre_trade_prompt, generate_post_trade_prompt

logger = logging.getLogger(__name__)


def render_dow_ai_section(
    trade: TradeWithMetrics,
    events: Dict[str, Dict],
    supabase_client,
    mode: str = 'pre_trade'
):
    """
    Render DOW AI prompt section with copy-to-clipboard functionality.

    Args:
        trade: TradeWithMetrics object
        events: Dict of optimal_trade events
        supabase_client: SupabaseClient for fetching additional context
        mode: 'pre_trade' or 'post_trade'
    """
    # Determine zone type from trade
    zone_type = trade.zone_type or 'PRIMARY'

    # Fetch additional context
    fetcher = DOWAIDataFetcher(supabase_client)
    context = fetcher.fetch_all_context(
        ticker=trade.ticker,
        trade_date=trade.date,
        zone_type=zone_type
    )

    # Check for missing data
    missing_data = _check_missing_data(context)

    # Fetch existing analysis if any
    existing_analysis = None
    try:
        existing_analysis = supabase_client.fetch_analysis(trade.trade_id, mode)
    except Exception as e:
        logger.warning(f"Could not fetch existing analysis: {e}")

    # Generate appropriate prompt
    if mode == 'pre_trade':
        prompt = generate_pre_trade_prompt(trade, events, context)
        section_title = "DOW AI Pre-Trade Query"
        section_icon = "🤖"
    else:
        prompt = generate_post_trade_prompt(trade, events, context)
        section_title = "DOW AI Post-Trade Review"
        section_icon = "📊"

    # Add indicator if analysis exists
    if existing_analysis:
        section_title += " ✓"

    # Render the section
    _render_prompt_section(
        prompt=prompt,
        title=section_title,
        icon=section_icon,
        missing_data=missing_data,
        trade_id=trade.trade_id,
        mode=mode,
        supabase_client=supabase_client,
        existing_analysis=existing_analysis
    )


def _check_missing_data(context: Dict[str, Any]) -> list:
    """
    Check for missing data and return list of warnings.

    Args:
        context: Dict with bar_data, hvn_pocs, market_structure, setup

    Returns:
        List of warning messages for missing data
    """
    warnings = []

    if context.get('bar_data') is None:
        warnings.append("Bar data (ATR, Camarilla) not found in database")

    if context.get('hvn_pocs') is None:
        warnings.append("HVN POC levels not found in database")

    if context.get('market_structure') is None:
        warnings.append("Market structure data not found in database")

    if context.get('setup') is None:
        warnings.append("Setup data not found in database")

    return warnings


def _render_prompt_section(
    prompt: str,
    title: str,
    icon: str,
    missing_data: list,
    trade_id: str,
    mode: str,
    supabase_client=None,
    existing_analysis: Optional[TradeAnalysis] = None
):
    """
    Render the prompt section with copy button and response paste area.

    Args:
        prompt: Generated prompt text
        title: Section title
        icon: Section icon
        missing_data: List of warning messages
        trade_id: Trade ID for unique keys
        mode: 'pre_trade' or 'post_trade'
        supabase_client: SupabaseClient for saving analysis
        existing_analysis: Existing TradeAnalysis if already saved
    """
    with st.expander(f"{icon} {title}", expanded=True):
        # Show existing analysis if available
        if existing_analysis:
            st.success("Analysis saved")
            with st.container():
                st.markdown("**Saved Analysis:**")
                st.markdown(existing_analysis.response_text)
                if existing_analysis.updated_at:
                    st.caption(f"Last updated: {existing_analysis.updated_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown("---")

        # Show missing data warnings
        if missing_data:
            st.warning("**Some data not available:**\n- " + "\n- ".join(missing_data))

        # Instructions
        st.markdown("""
        **How to use:**
        1. Click the copy button below to copy the prompt
        2. Open Claude Desktop
        3. Paste the prompt and submit
        4. Paste Claude's response below and save
        """)

        st.markdown("---")

        # Prompt display with copy functionality
        st.markdown("**Prompt:**")
        st.code(prompt, language=None)

        # Copy button using Streamlit's built-in functionality
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Create a download button as a fallback for copy
            st.download_button(
                label="Download Prompt",
                data=prompt,
                file_name=f"dow_ai_{mode}_{trade_id}.txt",
                mime="text/plain",
                key=f"download_{mode}_{trade_id}",
                use_container_width=True
            )

        # Add JavaScript-based copy button
        _add_copy_button(prompt, f"copy_{mode}_{trade_id}")

        # Show prompt stats
        st.caption(f"Prompt length: {len(prompt):,} characters | {len(prompt.split()):,} words")

        # Response paste section
        st.markdown("---")
        st.markdown("**Paste Claude's Response:**")

        # Session state key for the text area
        response_key = f"claude_response_{mode}_{trade_id}"

        # Pre-populate with existing analysis if available
        default_value = existing_analysis.response_text if existing_analysis else ""

        response_text = st.text_area(
            "Claude's Analysis",
            value=default_value,
            height=200,
            key=response_key,
            placeholder="Paste Claude's response here...",
            label_visibility="collapsed"
        )

        # Save button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Save Analysis",
                key=f"save_analysis_{mode}_{trade_id}",
                use_container_width=True,
                type="primary",
                disabled=not response_text.strip()
            ):
                if supabase_client and response_text.strip():
                    success = supabase_client.upsert_analysis(
                        trade_id=trade_id,
                        analysis_type=mode,
                        response_text=response_text.strip(),
                        prompt_text=prompt
                    )
                    if success:
                        st.toast(f"{mode.replace('_', '-').title()} analysis saved!", icon="✅")
                        st.rerun()
                    else:
                        st.error("Failed to save analysis")


def _add_copy_button(text: str, key: str):
    """
    Add a JavaScript-based copy to clipboard button.

    Args:
        text: Text to copy
        key: Unique key for the button
    """
    # Escape the text for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

    # Create the copy button using Streamlit's HTML component
    copy_button_html = f"""
    <style>
    .copy-btn {{
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        width: 100%;
    }}
    .copy-btn:hover {{
        background-color: #45a049;
    }}
    .copy-btn.copied {{
        background-color: #2196F3;
    }}
    </style>
    <button class="copy-btn" onclick="copyToClipboard_{key}()" id="btn_{key}">
        📋 Copy to Clipboard
    </button>
    <script>
    function copyToClipboard_{key}() {{
        const text = `{escaped_text}`;
        navigator.clipboard.writeText(text).then(function() {{
            const btn = document.getElementById('btn_{key}');
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

    st.components.v1.html(copy_button_html, height=50)


def render_pre_trade_dow_ai(
    trade: TradeWithMetrics,
    events: Dict[str, Dict],
    supabase_client
):
    """
    Convenience function to render pre-trade DOW AI section.

    Args:
        trade: TradeWithMetrics object
        events: Dict of optimal_trade events
        supabase_client: SupabaseClient instance
    """
    render_dow_ai_section(
        trade=trade,
        events=events,
        supabase_client=supabase_client,
        mode='pre_trade'
    )


def render_post_trade_dow_ai(
    trade: TradeWithMetrics,
    events: Dict[str, Dict],
    supabase_client
):
    """
    Convenience function to render post-trade DOW AI section.

    Args:
        trade: TradeWithMetrics object
        events: Dict of optimal_trade events
        supabase_client: SupabaseClient instance
    """
    render_dow_ai_section(
        trade=trade,
        events=events,
        supabase_client=supabase_client,
        mode='post_trade'
    )
