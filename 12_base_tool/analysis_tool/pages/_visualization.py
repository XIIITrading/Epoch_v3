"""
Visualization Page - Chart preview and PDF export.

Displays analysis charts and allows PDF report generation.
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import streamlit as st

from components.chart_builder import AnalysisChartBuilder, build_analysis_chart
from components.pdf_generator import PDFReportGenerator, generate_pdf_bytes

logger = logging.getLogger(__name__)


def render_visualization_page():
    """Render the visualization page with chart previews and PDF export."""
    st.header("Visualization & Export")

    # Check if we have analysis results
    results = st.session_state.get("analysis_results", {})

    if not results:
        st.info("No analysis results available. Run analysis first to generate visualizations.")
        return

    # Get both index and custom results
    custom_results = results.get("custom", [])
    index_results = results.get("index", [])

    # Combine successful results from both index and custom
    successful_custom = [r for r in custom_results if r.get("success")]
    successful_index = [r for r in index_results if r.get("success")]

    # All successful results for visualization
    all_successful = successful_index + successful_custom

    if not all_successful:
        st.warning("No successful analysis results to visualize.")
        return

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Index Tickers", len(successful_index))
    with col2:
        st.metric("Custom Tickers", len(successful_custom))
    with col3:
        total_zones = sum(r.get("zones_count", 0) for r in all_successful)
        st.metric("Total Zones", total_zones)

    st.markdown("---")

    # PDF Export Section
    st.subheader("PDF Report Export")

    col1, col2 = st.columns([2, 1])

    with col1:
        include_summary = st.checkbox("Include Summary Page", value=True)

    with col2:
        if st.button("Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_bytes = generate_pdf_bytes(results)

                    if pdf_bytes:
                        # Generate filename
                        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
                        filename = f"epoch_analysis_report_{timestamp}.pdf"

                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success(f"PDF report generated successfully ({len(pdf_bytes) / 1024:.1f} KB)")
                    else:
                        st.error("Failed to generate PDF report")

                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    logger.exception("PDF generation failed")

    st.markdown("---")

    # Chart Preview Section
    st.subheader("Chart Preview")

    # Ticker selector - show index tickers first, then custom
    index_tickers = [r.get("ticker") for r in successful_index if r.get("ticker")]
    custom_tickers = [r.get("ticker") for r in successful_custom if r.get("ticker")]

    # Create labeled options
    ticker_options = []
    if index_tickers:
        ticker_options.extend([(t, f"{t} (Index)") for t in index_tickers])
    if custom_tickers:
        ticker_options.extend([(t, f"{t} (Custom)") for t in custom_tickers])

    if not ticker_options:
        st.warning("No tickers available for preview")
        return

    # Format options for selectbox
    display_options = [opt[1] for opt in ticker_options]
    ticker_values = [opt[0] for opt in ticker_options]

    selected_idx = st.selectbox(
        "Select Ticker to Preview",
        options=range(len(display_options)),
        format_func=lambda x: display_options[x],
        index=0
    )

    selected_ticker = ticker_values[selected_idx]

    # Find the result for selected ticker (check both lists)
    selected_result = next(
        (r for r in all_successful if r.get("ticker") == selected_ticker),
        None
    )

    if selected_result:
        render_chart_preview(selected_result)


def render_chart_preview(result: Dict[str, Any]):
    """Render a single chart preview."""
    ticker = result.get("ticker", "Unknown")

    # Show result details
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Price", f"${result.get('price', 0):.2f}")
    with col2:
        st.metric("Direction", result.get("direction", "N/A"))
    with col3:
        st.metric("Zones", result.get("zones_count", 0))
    with col4:
        st.metric("Anchor", result.get("anchor_date", "N/A"))

    # Bull/Bear POCs
    col1, col2 = st.columns(2)
    with col1:
        bull_poc = result.get("bull_poc", "N/A")
        st.metric("Bull POC", bull_poc)
    with col2:
        bear_poc = result.get("bear_poc", "N/A")
        st.metric("Bear POC", bear_poc)

    # Primary/Secondary Setups
    primary = result.get("primary_setup")
    secondary = result.get("secondary_setup")

    if primary:
        st.markdown("**Primary Setup:**")
        st.write(f"- Zone: {primary.zone_id}")
        st.write(f"- Direction: {primary.direction.value}")
        st.write(f"- Range: ${primary.zone_low:.2f} - ${primary.zone_high:.2f}")
        if primary.target:
            st.write(f"- Target: ${primary.target:.2f}")

    if secondary:
        st.markdown("**Secondary Setup:**")
        st.write(f"- Zone: {secondary.zone_id}")
        st.write(f"- Direction: {secondary.direction.value}")
        st.write(f"- Range: ${secondary.zone_low:.2f} - ${secondary.zone_high:.2f}")
        if secondary.target:
            st.write(f"- Target: ${secondary.target:.2f}")

    # Generate and display chart
    st.markdown("---")
    st.markdown("**Chart Visualization:**")

    with st.spinner(f"Generating chart for {ticker}..."):
        try:
            fig = build_analysis_chart(result)

            if fig:
                # Display chart in Streamlit
                st.pyplot(fig)

                # Clean up
                import matplotlib.pyplot as plt
                plt.close(fig)
            else:
                st.warning("Unable to generate chart visualization")

        except Exception as e:
            st.error(f"Error generating chart: {str(e)}")
            logger.exception(f"Chart generation failed for {ticker}")


def render_visualization_tab():
    """Render visualization as a tab (for integration in app.py)."""
    render_visualization_page()


def render_export_button():
    """Render a compact export button for sidebar."""
    results = st.session_state.get("analysis_results", {})

    if not results:
        return

    custom_results = results.get("custom", [])
    successful_results = [r for r in custom_results if r.get("success")]

    if not successful_results:
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("Export")

    if st.sidebar.button("Generate PDF Report", use_container_width=True):
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = generate_pdf_bytes(results)

                if pdf_bytes:
                    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
                    filename = f"epoch_analysis_report_{timestamp}.pdf"

                    st.sidebar.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.sidebar.success(f"PDF ready ({len(pdf_bytes) / 1024:.1f} KB)")

            except Exception as e:
                st.sidebar.error(f"Error: {str(e)}")
