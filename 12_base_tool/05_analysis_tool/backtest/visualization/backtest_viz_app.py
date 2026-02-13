# backtest_viz_app.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\
# Purpose: Streamlit app for backtest trade visualization

"""
EPOCH Backtest Visualization App

Streamlit application for visualizing backtest trade results.
Integrates with existing visualization as a toggle option.

Features:
- Trade selection from backtest worksheet
- 4-quadrant visualization (metrics, M5, H1, M15 charts)
- Single trade PDF export
- Batch PDF export with summary
- Filtering by ticker, model, direction, date range

Usage:
    streamlit run backtest_viz_app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import io
import base64

# Add module paths
module_dir = Path(__file__).parent
sys.path.insert(0, str(module_dir))
sys.path.insert(0, str(module_dir / 'data_readers'))
sys.path.insert(0, str(module_dir / 'charts'))
sys.path.insert(0, str(module_dir / 'export'))
sys.path.insert(0, str(module_dir / 'config'))

# Page config
st.set_page_config(
    page_title="EPOCH Backtest Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a2e;
    }
    .stSidebar {
        background-color: #16213e;
    }
    .stSelectbox, .stMultiSelect {
        background-color: #0f0f1a;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #e0e0e0 !important;
    }
    .metric-card {
        background-color: #16213e;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
    }
    .win-text { color: #26a69a; }
    .loss-text { color: #ef5350; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'trades_loaded' not in st.session_state:
        st.session_state.trades_loaded = False
    if 'trades_df' not in st.session_state:
        st.session_state.trades_df = None
    if 'selected_trade_id' not in st.session_state:
        st.session_state.selected_trade_id = None
    if 'chart_data_cache' not in st.session_state:
        st.session_state.chart_data_cache = {}


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_trades_from_excel():
    """Load trades from Excel backtest worksheet"""
    try:
        from backtest_reader import BacktestResultsReader
        
        reader = BacktestResultsReader()
        if not reader.connect():
            return None, "Could not connect to Excel. Ensure epoch_v1.xlsm is open."
        
        trades = reader.read_trades()
        if not trades:
            return None, "No trades found in backtest worksheet."
        
        df = reader.to_dataframe(trades)
        return df, None
        
    except ImportError as e:
        return None, f"Import error: {e}"
    except Exception as e:
        return None, f"Error loading trades: {e}"


def get_filtered_trades(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply filters to trades DataFrame"""
    filtered = df.copy()
    
    if filters.get('ticker'):
        filtered = filtered[filtered['ticker'].isin(filters['ticker'])]
    
    if filters.get('model'):
        filtered = filtered[filtered['model'].isin(filters['model'])]
    
    if filters.get('direction'):
        filtered = filtered[filtered['direction'].isin(filters['direction'])]
    
    if filters.get('zone_type'):
        filtered = filtered[filtered['zone_type'].isin(filters['zone_type'])]
    
    if filters.get('start_date'):
        filtered = filtered[filtered['date'] >= filters['start_date']]
    
    if filters.get('end_date'):
        filtered = filtered[filtered['date'] <= filters['end_date']]
    
    if filters.get('win_only') is not None:
        if filters['win_only'] == 'Winners':
            filtered = filtered[filtered['win'] == True]
        elif filters['win_only'] == 'Losers':
            filtered = filtered[filtered['win'] == False]
    
    return filtered


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_trade_visualization(trade_row: pd.Series):
    """Create 4-quadrant visualization for a trade"""
    try:
        from trade_chart_builder import TradeChartBuilder
        from chart_data_fetcher import TradeChartDataProvider
        from backtest_reader import TradeRecord
        
        # Convert row to TradeRecord
        trade = TradeRecord(
            trade_id=trade_row['trade_id'],
            date=trade_row['date'],
            ticker=trade_row['ticker'],
            model=trade_row['model'],
            zone_type=trade_row['zone_type'],
            direction=trade_row['direction'],
            zone_high=trade_row['zone_high'],
            zone_low=trade_row['zone_low'],
            entry_price=trade_row['entry_price'],
            entry_time=trade_row['entry_time'],
            stop_price=trade_row['stop_price'],
            target_3r=trade_row['target_3r'],
            target_calc=trade_row['target_calc'],
            target_used=trade_row['target_used'],
            exit_price=trade_row['exit_price'],
            exit_time=trade_row['exit_time'],
            exit_reason=trade_row['exit_reason'],
            pnl_dollars=trade_row['pnl_dollars'],
            pnl_r=trade_row['pnl_r'],
            risk=trade_row['risk'],
            win=trade_row['win']
        )
        
        # Check cache
        cache_key = trade.trade_id
        if cache_key in st.session_state.chart_data_cache:
            viz_data = st.session_state.chart_data_cache[cache_key]
        else:
            # Fetch data
            with st.spinner(f"Fetching chart data for {trade.ticker}..."):
                provider = TradeChartDataProvider()
                viz_data = provider.get_trade_visualization_data(trade)
                st.session_state.chart_data_cache[cache_key] = viz_data
        
        # Build chart
        builder = TradeChartBuilder()
        fig = builder.build(
            trade=trade,
            m5_bars=viz_data['m5_bars'],
            h1_bars=viz_data['h1_bars'],
            m15_bars=viz_data['m15_bars'],
            zones=viz_data['zones'],
            hvn_pocs=viz_data['hvn_pocs']
        )
        
        return fig, trade
        
    except Exception as e:
        st.error(f"Error creating visualization: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 for download"""
    buf = io.BytesIO()
    fig.savefig(buf, format='pdf', dpi=150, facecolor='#1a1a2e', 
               edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render sidebar with filters and controls"""
    st.sidebar.title("📊 EPOCH Backtest Viewer")
    
    # Visualization mode toggle
    st.sidebar.markdown("---")
    viz_mode = st.sidebar.radio(
        "Visualization Mode",
        ["Backtest Results", "Pre-Market Zones", "Post-Market Review"],
        help="Select visualization type"
    )
    
    st.sidebar.markdown("---")
    
    # Load/Refresh data button
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Load Data", use_container_width=True):
            st.cache_data.clear()
            st.session_state.trades_loaded = False
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.chart_data_cache = {}
            st.success("Cache cleared!")
    
    # Only show filters for backtest mode
    if viz_mode == "Backtest Results":
        render_backtest_filters()
    
    return viz_mode


def render_backtest_filters():
    """Render backtest-specific filters"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    
    filters = {}
    
    if st.session_state.trades_df is not None:
        df = st.session_state.trades_df
        
        # Ticker filter
        tickers = sorted(df['ticker'].unique())
        filters['ticker'] = st.sidebar.multiselect(
            "Ticker", tickers, default=None,
            help="Filter by ticker symbol"
        )
        
        # Model filter
        models = sorted(df['model'].unique())
        filters['model'] = st.sidebar.multiselect(
            "Model", models, default=None,
            help="Filter by entry model"
        )
        
        # Direction filter
        directions = sorted(df['direction'].unique())
        filters['direction'] = st.sidebar.multiselect(
            "Direction", directions, default=None,
            help="Filter by trade direction"
        )
        
        # Zone type filter
        zone_types = sorted(df['zone_type'].unique())
        filters['zone_type'] = st.sidebar.multiselect(
            "Zone Type", zone_types, default=None,
            help="Filter by zone type"
        )
        
        # Win/Loss filter
        filters['win_only'] = st.sidebar.selectbox(
            "Result", ["All", "Winners", "Losers"],
            help="Filter by trade result"
        )
        if filters['win_only'] == "All":
            filters['win_only'] = None
        
        # Date range filter
        st.sidebar.markdown("**Date Range**")
        dates = pd.to_datetime(df['date'])
        min_date = dates.min().date()
        max_date = dates.max().date()
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            filters['start_date'] = st.date_input(
                "From", min_date, min_value=min_date, max_value=max_date
            ).strftime('%Y-%m-%d')
        with col2:
            filters['end_date'] = st.date_input(
                "To", max_date, min_value=min_date, max_value=max_date
            ).strftime('%Y-%m-%d')
    
    st.session_state.filters = filters
    return filters


# =============================================================================
# MAIN CONTENT
# =============================================================================

def render_backtest_content():
    """Render main backtest visualization content"""
    
    # Load trades if not loaded
    if not st.session_state.trades_loaded:
        with st.spinner("Loading trades from Excel..."):
            df, error = load_trades_from_excel()
            
            if error:
                st.error(f"❌ {error}")
                st.info("Make sure epoch_v1.xlsm is open in Excel and the backtest worksheet has data.")
                return
            
            st.session_state.trades_df = df
            st.session_state.trades_loaded = True
    
    df = st.session_state.trades_df
    
    if df is None or df.empty:
        st.warning("No trades loaded. Click 'Load Data' to refresh.")
        return
    
    # Apply filters
    filters = st.session_state.get('filters', {})
    filtered_df = get_filtered_trades(df, filters)
    
    # Summary metrics
    st.markdown("### 📈 Performance Summary")
    render_summary_metrics(filtered_df)
    
    st.markdown("---")
    
    # Trade selection and visualization
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### 📋 Trade List")
        render_trade_list(filtered_df)
    
    with col2:
        st.markdown("### 📊 Trade Visualization")
        render_trade_chart()


def render_summary_metrics(df: pd.DataFrame):
    """Render summary metrics cards"""
    if df.empty:
        st.info("No trades match the current filters.")
        return
    
    total = len(df)
    winners = df['win'].sum()
    win_rate = winners / total * 100 if total > 0 else 0
    total_pnl_r = df['pnl_r'].sum()
    total_pnl_dollars = df['pnl_dollars'].sum()
    avg_pnl_r = df['pnl_r'].mean()
    
    # Profit factor
    gross_profit = df[df['pnl_dollars'] > 0]['pnl_dollars'].sum()
    gross_loss = abs(df[df['pnl_dollars'] < 0]['pnl_dollars'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Trades", total)
    
    with col2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col3:
        delta_color = "normal" if total_pnl_r >= 0 else "inverse"
        st.metric("Total P&L (R)", f"{total_pnl_r:+.2f}R", 
                 delta=f"{total_pnl_r:+.2f}", delta_color=delta_color)
    
    with col4:
        st.metric("Total P&L ($)", f"${total_pnl_dollars:+,.2f}")
    
    with col5:
        st.metric("Avg P&L (R)", f"{avg_pnl_r:+.2f}R")
    
    with col6:
        st.metric("Profit Factor", f"{profit_factor:.2f}")


def render_trade_list(df: pd.DataFrame):
    """Render scrollable trade list"""
    if df.empty:
        st.info("No trades to display.")
        return
    
    # Create display dataframe
    display_df = df[['date', 'ticker', 'model', 'direction', 'pnl_r', 'win']].copy()
    display_df['pnl_r'] = display_df['pnl_r'].apply(lambda x: f"{x:+.2f}R")
    display_df['result'] = display_df['win'].apply(lambda x: '✓ WIN' if x else '✗ LOSS')
    display_df = display_df.drop(columns=['win'])
    
    # Trade selection
    trade_options = [
        f"{row['date']} | {row['ticker']} | {row['model']} | {row['pnl_r']}"
        for _, row in df.iterrows()
    ]
    
    selected_idx = st.selectbox(
        "Select Trade",
        range(len(trade_options)),
        format_func=lambda x: trade_options[x],
        key="trade_selector"
    )
    
    if selected_idx is not None:
        st.session_state.selected_trade_id = df.iloc[selected_idx]['trade_id']
    
    # Show trade table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Export buttons
    st.markdown("---")
    st.markdown("**Export Options**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export Selected", use_container_width=True,
                    disabled=st.session_state.selected_trade_id is None):
            export_single_trade()
    
    with col2:
        if st.button("📚 Export All Filtered", use_container_width=True,
                    disabled=df.empty):
            export_batch_trades(df)


def render_trade_chart():
    """Render the selected trade's 4-quadrant chart"""
    if st.session_state.selected_trade_id is None:
        st.info("👈 Select a trade from the list to view visualization")
        return
    
    df = st.session_state.trades_df
    trade_row = df[df['trade_id'] == st.session_state.selected_trade_id].iloc[0]
    
    # Trade header
    result_emoji = "🟢" if trade_row['win'] else "🔴"
    st.markdown(f"""
    **{result_emoji} {trade_row['ticker']}** | {trade_row['date']} | 
    {trade_row['model']} | {trade_row['direction']} | 
    **{trade_row['pnl_r']:+.2f}R** (${trade_row['pnl_dollars']:+.2f})
    """)
    
    # Create visualization
    fig, trade = create_trade_visualization(trade_row)
    
    if fig is not None:
        st.pyplot(fig, use_container_width=True)
        
        # Download button
        pdf_b64 = fig_to_base64(fig)
        filename = f"{trade_row['ticker']}_{trade_row['date']}_{trade_row['model']}.pdf"
        
        st.download_button(
            label="📥 Download PDF",
            data=base64.b64decode(pdf_b64),
            file_name=filename,
            mime="application/pdf"
        )
        
        import matplotlib.pyplot as plt
        plt.close(fig)


def export_single_trade():
    """Export single selected trade to PDF"""
    st.info("Exporting single trade...")
    # Implementation would call pdf_exporter


def export_batch_trades(df: pd.DataFrame):
    """Export all filtered trades to PDF"""
    st.info(f"Exporting {len(df)} trades...")
    # Implementation would call pdf_exporter with batch mode


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main app entry point"""
    init_session_state()
    
    # Render sidebar and get mode
    viz_mode = render_sidebar()
    
    # Render content based on mode
    if viz_mode == "Backtest Results":
        render_backtest_content()
    
    elif viz_mode == "Pre-Market Zones":
        st.title("📍 Pre-Market Zone Visualization")
        st.info("This feature shows the morning zone calculations. Select 'Backtest Results' to view trade visualizations.")
        # This would integrate with existing zone visualization
    
    elif viz_mode == "Post-Market Review":
        st.title("📊 Post-Market Review")
        st.info("This feature shows end-of-day trade review. Select 'Backtest Results' to view trade visualizations.")
        # This would integrate with existing EOD visualization


if __name__ == "__main__":
    main()
