# app.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\
# Purpose: Streamlit application for Epoch visualization

"""
Module 08 Visualization - Streamlit Application

Features:
- Generate all ticker reports at once
- Toggle between tickers via dropdown
- Pre-market / Post-market label toggle
- User notes input
- PDF export capability
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import sys
from pathlib import Path

# Add module directory to path
MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from config.visualization_config import (
    COLORS, DEFAULT_BAR_COUNT, DEFAULT_BAR_TIMEFRAME, SESSION_LABELS, WORKBOOK_PATH, DPI
)
from data_readers.excel_reader import EpochExcelReader, VisualizationData
from data_readers.polygon_fetcher import PolygonBarFetcher, ChartData
from charts.chart_builder import VisualizationChartBuilder


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Epoch Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
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
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'viz_data' not in st.session_state:
    st.session_state.viz_data = {}  # Dict[ticker, VisualizationData]

if 'chart_data' not in st.session_state:
    st.session_state.chart_data = {}  # Dict[ticker, ChartData]

if 'charts_generated' not in st.session_state:
    st.session_state.charts_generated = False

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

if 'notes' not in st.session_state:
    st.session_state.notes = {}  # Dict[ticker, str]


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("📊 Epoch Visualization")
    st.markdown("---")
    
    # Session type selector
    session_type = st.radio(
        "Report Type",
        options=['premarket', 'postmarket'],
        format_func=lambda x: SESSION_LABELS[x],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Generate button
    if st.button("🔄 Generate All Reports", type="primary", use_container_width=True):
        with st.spinner("Loading data from Excel..."):
            try:
                # Read Excel data
                reader = EpochExcelReader()
                if reader.connect():
                    st.session_state.viz_data = reader.read_all_tickers()
                    
                    if st.session_state.viz_data:
                        st.success(f"Loaded {len(st.session_state.viz_data)} tickers from Excel")
                        
                        # Fetch Polygon data for each ticker
                        fetcher = PolygonBarFetcher()
                        tickers = list(st.session_state.viz_data.keys())
                        
                        # Get M5 ATRs from Excel data
                        m5_atrs = {}
                        for ticker, vd in st.session_state.viz_data.items():
                            if vd.ticker_structure.m5_atr > 0:
                                m5_atrs[ticker] = vd.ticker_structure.m5_atr
                            elif vd.ticker_structure.d1_atr > 0:
                                # Fallback: M5 ATR ≈ D1 ATR / 20
                                m5_atrs[ticker] = vd.ticker_structure.d1_atr / 20
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, ticker in enumerate(tickers):
                            status_text.text(f"Fetching M{DEFAULT_BAR_TIMEFRAME} data for {ticker}...")
                            st.session_state.chart_data[ticker] = fetcher.fetch_last_n_bars(
                                ticker, DEFAULT_BAR_COUNT, DEFAULT_BAR_TIMEFRAME,
                                m5_atr=m5_atrs.get(ticker)
                            )
                            progress_bar.progress((i + 1) / len(tickers))
                        
                        status_text.text("✅ All data loaded!")
                        st.session_state.charts_generated = True
                        
                        # Set default selected ticker
                        if tickers:
                            st.session_state.selected_ticker = tickers[0]
                    else:
                        st.warning("No tickers found in workbook")
                else:
                    st.error("Failed to connect to Excel workbook")
                    st.info(f"Ensure {WORKBOOK_PATH.name} is open")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Ticker selector (only shown after generation)
    if st.session_state.charts_generated and st.session_state.viz_data:
        tickers = list(st.session_state.viz_data.keys())
        
        selected = st.selectbox(
            "Select Ticker",
            options=tickers,
            index=tickers.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in tickers else 0
        )
        st.session_state.selected_ticker = selected
        
        # Quick stats for selected ticker
        if selected in st.session_state.viz_data:
            viz = st.session_state.viz_data[selected]
            
            st.markdown("### Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Composite", viz.ticker_structure.composite)
            with col2:
                st.metric("Zones", len(viz.zones))
            
            st.metric("Price", f"${viz.ticker_structure.price:.2f}")
            st.metric("D1 ATR", f"${viz.ticker_structure.d1_atr:.2f}")
            st.metric("M5 ATR (Excel)", f"${viz.ticker_structure.m5_atr:.2f}")
            
            # Show actual ATR used for HVN zones
            if selected in st.session_state.chart_data:
                cd = st.session_state.chart_data[selected]
                st.metric("M5 ATR (Used)", f"${cd.m5_atr:.2f}")
    
    st.markdown("---")
    st.markdown("*XIII Trading LLC*")
    st.markdown(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*")


# =============================================================================
# MAIN CONTENT
# =============================================================================

if not st.session_state.charts_generated:
    # Welcome screen
    st.title("Epoch Trading System - Visualization Module")
    
    st.markdown("""
    ### Welcome to Module 08
    
    This module generates visual reports for your trading setups.
    
    **To get started:**
    1. Ensure `epoch_v1.xlsm` is open in Excel
    2. Run Modules 01-07 to populate the data
    3. Click **Generate All Reports** in the sidebar
    
    **Features:**
    - Market Structure overview (SPY, QQQ, DIA)
    - Ticker Structure with Strong/Weak levels
    - Zone Results table (L2-L5 filtered)
    - Setup Analysis with Primary/Secondary zones
    - M5 candlestick chart with zone overlays
    - Volume Profile sidebar
    - Exportable to PDF
    """)
    
    # Show workbook path
    st.info(f"Looking for workbook at: `{WORKBOOK_PATH}`")

else:
    # Chart display
    ticker = st.session_state.selected_ticker
    
    if ticker and ticker in st.session_state.viz_data and ticker in st.session_state.chart_data:
        viz_data = st.session_state.viz_data[ticker]
        chart_data = st.session_state.chart_data[ticker]
        
        # Notes input
        notes_key = f"notes_{ticker}"
        if notes_key not in st.session_state:
            st.session_state[notes_key] = ""
        
        # Build chart
        builder = VisualizationChartBuilder()
        fig = builder.build(
            viz_data=viz_data,
            chart_data=chart_data,
            session_type=session_type,
            notes=st.session_state[notes_key]
        )
        
        # Display chart
        st.pyplot(fig)
        
        # Notes section below chart
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_notes = st.text_area(
                "Notes",
                value=st.session_state[notes_key],
                height=80,
                placeholder="Enter your trading notes here...",
                key=f"notes_input_{ticker}"
            )
            st.session_state[notes_key] = new_notes
        
        with col2:
            st.markdown("### Export")
            
            # PNG download
            png_bytes = builder.to_bytes()
            if png_bytes:
                filename = f"{ticker}_{session_type}_{datetime.now().strftime('%Y-%m-%d')}.png"
                st.download_button(
                    label="📥 Download PNG",
                    data=png_bytes,
                    file_name=filename,
                    mime="image/png",
                    use_container_width=True
                )
            
            # Setup string display
            st.markdown("### PineScript String")
            st.code(viz_data.setup.setup_string or "0,0,0,0,0,0", language=None)
        
        builder.close()
        
        # Additional info expander
        with st.expander("📋 Zone Details"):
            if viz_data.zones:
                zone_df = pd.DataFrame([
                    {
                        'Zone ID': z.zone_id.replace(f'{ticker}_', ''),
                        'Direction': z.direction,
                        'POC': f"${z.hvn_poc:.2f}",
                        'High': f"${z.zone_high:.2f}",
                        'Low': f"${z.zone_low:.2f}",
                        'Rank': z.rank,
                        'Score': f"{z.score:.1f}",
                        'Confluences': z.confluences[:50] + '...' if len(z.confluences) > 50 else z.confluences
                    }
                    for z in viz_data.zones
                ])
                st.dataframe(zone_df, use_container_width=True)
            else:
                st.info("No zones found for this ticker")
        
        with st.expander("📊 Chart Data Info"):
            st.markdown(f"**Bars Fetched:** {chart_data.bar_count} M{DEFAULT_BAR_TIMEFRAME} bars")
            st.markdown(f"**Fetch Time:** {chart_data.fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Price Range:** ${chart_data.price_range[0]:.2f} - ${chart_data.price_range[1]:.2f}")
            st.markdown(f"**Volume Profile Levels:** {len(chart_data.volume_profile)}")
            st.markdown(f"**HVN Zones Identified:** {len(chart_data.hvn_zones)}")
            if chart_data.hvn_zones:
                st.markdown("**Top 3 HVN POCs:**")
                for zone in chart_data.hvn_zones[:3]:
                    st.markdown(f"  - #{zone.rank}: ${zone.poc_price:.2f}")
    
    else:
        st.warning("Select a ticker from the sidebar")


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Module 08 Visualization | Epoch Trading System v1.0 | XIII Trading LLC"
    "</div>",
    unsafe_allow_html=True
)
