# app.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\
# Purpose: Streamlit application for Epoch visualization (V2)

"""
Module 08 Visualization V2 - Streamlit Application

Key changes from V1:
- H1 candles (240 bars) for multi-week context
- Full epoch VbP from user-defined start dates
- POC lines from Module 04 Excel data
- Epoch range on y-axis
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
    COLORS, CANDLE_BAR_COUNT, CANDLE_TIMEFRAME, VBP_TIMEFRAME,
    SESSION_LABELS, WORKBOOK_PATH, DPI
)
from data_readers.excel_reader import EpochExcelReader, VisualizationData, EpochData
from data_readers.polygon_fetcher import PolygonDataFetcher, ChartData
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
                        
                        # Build epoch mapping (ticker -> start_date)
                        ticker_epochs = {}
                        for ticker, vd in st.session_state.viz_data.items():
                            if vd.epoch and vd.epoch.start_date:
                                ticker_epochs[ticker] = vd.epoch.start_date
                            else:
                                # Default to 30 days ago if no epoch set
                                ticker_epochs[ticker] = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
                        
                        # Fetch Polygon data for each ticker
                        fetcher = PolygonDataFetcher()
                        tickers = list(st.session_state.viz_data.keys())
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, ticker in enumerate(tickers):
                            epoch_start = ticker_epochs[ticker]
                            status_text.text(f"Fetching H1 candles + M{VBP_TIMEFRAME} VbP for {ticker} (epoch: {epoch_start})...")
                            
                            st.session_state.chart_data[ticker] = fetcher.fetch_chart_data(
                                ticker=ticker,
                                epoch_start_date=epoch_start,
                                candle_bars=CANDLE_BAR_COUNT,
                                candle_tf=CANDLE_TIMEFRAME,
                                vbp_tf=VBP_TIMEFRAME
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
                import traceback
                st.code(traceback.format_exc())
    
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
            
            # Epoch info
            if viz.epoch:
                st.markdown("### Epoch Info")
                st.metric("Start Date", viz.epoch.start_date)
                poc_count = sum(1 for p in viz.epoch.hvn_pocs if p > 0)
                st.metric("POCs", f"{poc_count}/10")
            
            # Chart data stats
            if selected in st.session_state.chart_data:
                cd = st.session_state.chart_data[selected]
                st.markdown("### Chart Data")
                st.metric("H1 Candles", cd.candle_count)
                st.metric("VbP Bars", cd.vbp_bar_count)
                st.metric("Epoch Range", f"${cd.epoch_low:.2f} - ${cd.epoch_high:.2f}")
    
    st.markdown("---")
    st.markdown("*XIII Trading LLC*")
    st.markdown(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*")


# =============================================================================
# MAIN CONTENT
# =============================================================================

if not st.session_state.charts_generated:
    # Welcome screen
    st.title("Epoch Trading System - Visualization Module V2")
    
    st.markdown("""
    ### Welcome to Module 08
    
    This module generates visual reports for your trading setups.
    
    **To get started:**
    1. Ensure `epoch_v1.xlsm` is open in Excel
    2. Run Modules 01-07 to populate the data
    3. Click **Generate All Reports** in the sidebar
    
    **V2 Features:**
    - H1 candlesticks (240 bars = ~36 trading days)
    - Full epoch VbP from user-defined start dates
    - 10 POC lines from Module 04 (dashed white)
    - Y-axis spans full epoch range
    - Zone overlays (Primary/Secondary)
    - Target lines
    """)
    
    st.markdown("### Configuration")
    st.code(f"""
Candle Timeframe: H{CANDLE_TIMEFRAME // 60}
Candle Count: {CANDLE_BAR_COUNT}
VbP Timeframe: M{VBP_TIMEFRAME}
VbP Granularity: $0.01
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
        
        # Notes input below chart
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.session_state[notes_key] = st.text_area(
                "Notes",
                value=st.session_state[notes_key],
                height=100,
                key=f"notes_input_{ticker}"
            )
        
        with col2:
            # Download button
            png_bytes = builder.to_bytes()
            if png_bytes:
                filename = f"{ticker}_{session_type}_{datetime.now().strftime('%Y%m%d')}.png"
                st.download_button(
                    "📥 Download PNG",
                    data=png_bytes,
                    file_name=filename,
                    mime="image/png",
                    use_container_width=True
                )
        
        # PineScript string - Full 16-value format with POCs
        st.markdown("**PineScript Setup String (16 values):**")
        st.code(viz_data.full_pinescript_string)
        
        # Also show the original 6-value string for reference
        with st.expander("📝 Original 6-value string"):
            st.code(viz_data.setup.setup_string if viz_data.setup.setup_string else "0,0,0,0,0,0")
        
        # Expandable details
        with st.expander("📋 Zone Details"):
            if viz_data.zones:
                zone_df = pd.DataFrame([
                    {
                        'Zone ID': z.zone_id.replace(f'{ticker}_', ''),
                        'POC': f"${z.hvn_poc:.2f}",
                        'High': f"${z.zone_high:.2f}",
                        'Low': f"${z.zone_low:.2f}",
                        'Rank': z.rank,
                        'Score': z.score
                    }
                    for z in viz_data.zones
                ])
                st.dataframe(zone_df, use_container_width=True)
            else:
                st.info("No zones for this ticker")
        
        with st.expander("📊 Epoch POCs (from Module 04)"):
            if viz_data.epoch and viz_data.epoch.hvn_pocs:
                poc_df = pd.DataFrame([
                    {'Rank': f'POC{i+1}', 'Price': f"${p:.2f}" if p > 0 else "-"}
                    for i, p in enumerate(viz_data.epoch.hvn_pocs)
                ])
                st.dataframe(poc_df, use_container_width=True)
            else:
                st.info("No epoch POCs found. Run Module 04 first.")
        
        with st.expander("📊 Chart Data Info"):
            st.markdown(f"**Candles:** {chart_data.candle_count} H{CANDLE_TIMEFRAME//60} bars")
            st.markdown(f"**VbP Bars:** {chart_data.vbp_bar_count} M{VBP_TIMEFRAME} bars")
            st.markdown(f"**Epoch:** {chart_data.epoch_start_date}")
            st.markdown(f"**Epoch Range:** ${chart_data.epoch_low:.2f} - ${chart_data.epoch_high:.2f}")
            st.markdown(f"**VbP Levels:** {len(chart_data.vbp_volume_profile)}")
            st.markdown(f"**Fetch Time:** {chart_data.fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clean up
        builder.close()
    
    else:
        st.warning("Select a ticker from the sidebar to view its report")
