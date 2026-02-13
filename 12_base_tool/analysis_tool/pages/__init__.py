"""
Epoch Analysis Tool - Pages Module
Contains Streamlit page definitions.

Note: All page files are prefixed with underscore (_) to hide them from
Streamlit's auto-detection. Navigation is handled through the sidebar in app.py.
"""
from pages._analysis import render_analysis_page, render_setup_summary
from pages._scanner import render_scanner_page, render_scanner_tab
from pages._visualization import (
    render_visualization_page,
    render_visualization_tab,
    render_chart_preview,
    render_export_button,
)
from pages._pre_market_report import render_pre_market_report

__all__ = [
    "render_analysis_page",
    "render_setup_summary",
    "render_scanner_page",
    "render_scanner_tab",
    "render_visualization_page",
    "render_visualization_tab",
    "render_chart_preview",
    "render_export_button",
    "render_pre_market_report",
]
