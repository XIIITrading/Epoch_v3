"""
Epoch Trading System - Trading Journal
Main Streamlit application entry point.

Usage:
    streamlit run streamlit_app.py

Author: XIII Trading LLC
"""

import streamlit as st
import sys
from pathlib import Path

# Add module directory to path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from components.import_page import render_import_page
from components.review_page import render_review_page
from components.stats_page import render_stats_page
from components.export_page import render_export_page


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Epoch Journal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS — matches 06_training
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a2e;
    }
    .stSidebar {
        background-color: #16213e;
    }
    .stMarkdown, .stText {
        color: #e0e0e0;
    }
    div[data-testid="stMetricValue"] {
        color: #e0e0e0;
    }
    .stSelectbox label, .stRadio label, .stTextArea label {
        color: #e0e0e0 !important;
    }
    .stButton button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

st.sidebar.title("Epoch Journal")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Import", "Review", "Statistics", "Export"],
    label_visibility="collapsed",
)

st.sidebar.divider()


# =============================================================================
# PAGE ROUTING
# =============================================================================

if page == "Import":
    render_import_page()
elif page == "Review":
    render_review_page()
elif page == "Statistics":
    render_stats_page()
elif page == "Export":
    render_export_page()
