"""
Progress Display Component - Shows pipeline progress during analysis.

Displays:
- Overall progress bar
- Current stage
- Current ticker being processed
- Stage-by-stage status
"""
import streamlit as st
from typing import Optional

from core.state_manager import get_state


# Pipeline stages with descriptions and icons
PIPELINE_STAGES = [
    ("fetch_data", "Fetching Market Data", "download"),
    ("bar_data", "Calculating Bar Data", "bar-chart"),
    ("hvn_calc", "Identifying HVN POCs", "graph-up"),
    ("zone_calc", "Calculating Confluence Zones", "layers"),
    ("zone_filter", "Filtering Zones", "funnel"),
    ("setup_analysis", "Analyzing Setups", "bullseye"),
    ("complete", "Analysis Complete", "check-circle"),
]


def render_progress() -> None:
    """
    Render the progress display during pipeline execution.

    Shows:
    - Progress bar
    - Current stage name
    - Current ticker
    - Stage completion status
    """
    progress = get_state("pipeline_progress", 0.0)
    stage = get_state("pipeline_stage", "")
    status = get_state("pipeline_status", "")
    current_ticker = get_state("current_ticker", "")

    # Main progress container
    with st.container():
        st.subheader("Analysis Progress")

        # Progress bar with percentage
        progress_pct = int(progress * 100)
        st.progress(progress, text=f"{progress_pct}% complete")

        # Current status with styling
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if stage:
                stage_name = _get_stage_display_name(stage)
                if stage == "complete":
                    st.success(f"**{stage_name}**")
                else:
                    st.info(f"**Stage:** {stage_name}")

        with col2:
            if current_ticker:
                st.markdown(f"**Current:** `{current_ticker}`")

        with col3:
            if progress > 0:
                # Estimate remaining time (rough)
                if progress < 1.0:
                    st.caption(f"{progress_pct}%")

        if status and stage != "complete":
            st.caption(f"{status}")

        # Stage checklist
        st.markdown("---")
        render_stage_checklist(stage)


def render_stage_checklist(current_stage: str) -> None:
    """
    Render a checklist of pipeline stages.

    Args:
        current_stage: The current stage key
    """
    # Find index of current stage
    current_index = -1
    for i, (key, _, _) in enumerate(PIPELINE_STAGES):
        if key == current_stage:
            current_index = i
            break

    # Render each stage in a compact grid
    cols = st.columns(len(PIPELINE_STAGES))

    for i, (key, name, icon) in enumerate(PIPELINE_STAGES):
        with cols[i]:
            if i < current_index:
                # Completed - green check
                st.markdown(
                    f"<div style='text-align: center;'>"
                    f"<span style='color: #00C853; font-size: 20px;'>&#10003;</span><br/>"
                    f"<span style='color: #00C853; font-size: 11px;'>{name}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            elif i == current_index:
                # In progress - blue pulse
                st.markdown(
                    f"<div style='text-align: center;'>"
                    f"<span style='color: #2962FF; font-size: 20px;'>&#9711;</span><br/>"
                    f"<span style='color: #2962FF; font-size: 11px; font-weight: bold;'>{name}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                # Pending - gray
                st.markdown(
                    f"<div style='text-align: center;'>"
                    f"<span style='color: #666; font-size: 20px;'>&#9675;</span><br/>"
                    f"<span style='color: #666; font-size: 11px;'>{name}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )


def _get_stage_display_name(stage_key: str) -> str:
    """
    Get display name for a stage key.

    Args:
        stage_key: The stage key (e.g., 'bar_data')

    Returns:
        Display name (e.g., 'Calculating Bar Data')
    """
    for key, name, _ in PIPELINE_STAGES:
        if key == stage_key:
            return name
    return stage_key.replace("_", " ").title()


def render_ticker_progress(
    ticker: str,
    total_tickers: int,
    current_index: int,
    stages_complete: int = 0,
    total_stages: int = 4
) -> None:
    """
    Render progress for a specific ticker.

    Args:
        ticker: Current ticker symbol
        total_tickers: Total number of tickers to process
        current_index: Index of current ticker (0-based)
        stages_complete: Number of stages complete for this ticker
        total_stages: Total number of stages per ticker
    """
    # Overall progress
    ticker_progress = (current_index + (stages_complete / total_stages)) / total_tickers

    col1, col2 = st.columns([3, 1])

    with col1:
        st.progress(ticker_progress)

    with col2:
        st.caption(f"{current_index + 1} / {total_tickers}")

    st.caption(f"Processing: **{ticker}** ({stages_complete}/{total_stages} stages)")


def render_error_summary(errors: list) -> None:
    """
    Render a summary of errors encountered during analysis.

    Args:
        errors: List of error messages
    """
    if not errors:
        return

    st.markdown("---")
    st.subheader("Errors")

    for error in errors:
        st.error(error)


def render_completion_summary(
    total_tickers: int,
    successful: int,
    failed: int,
    elapsed_time: float
) -> None:
    """
    Render summary after pipeline completion.

    Args:
        total_tickers: Total tickers processed
        successful: Number of successful analyses
        failed: Number of failed analyses
        elapsed_time: Total elapsed time in seconds
    """
    st.markdown("---")
    st.subheader("Analysis Complete")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tickers", total_tickers)

    with col2:
        st.metric("Successful", successful)

    with col3:
        st.metric("Failed", failed)

    with col4:
        st.metric("Time", f"{elapsed_time:.1f}s")

    if successful == total_tickers:
        st.success("All tickers processed successfully!")
    elif failed > 0:
        st.warning(f"{failed} ticker(s) had errors. Check the error summary below.")
