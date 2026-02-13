"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Options Summary Card Components
XIII Trading LLC
================================================================================

Summary cards specifically for the Options Analysis tab.
Displays key metrics for options trades including win rate, MFE/MAE, and leverage.

================================================================================
"""

import streamlit as st
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHART_CONFIG


def render_options_overview_cards(stats: Dict[str, Any]) -> None:
    """
    Render overview summary cards for options trades.

    Parameters:
    -----------
    stats : Dict[str, Any]
        Summary statistics from get_options_summary() or calculate_options_mfe_mae_summary()
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)

    with col1:
        st.metric(
            label="Options Trades",
            value=f"{total:,}"
        )

    with col2:
        st.metric(
            label="Win Rate",
            value=f"{win_rate:.1f}%",
            help="Exit % > 0 = Win"
        )

    with col3:
        st.metric(
            label="Wins / Losses",
            value=f"{wins} / {losses}"
        )

    with col4:
        avg_exit = stats.get("avg_exit_pct", stats.get("median_exit_pct", 0))
        st.metric(
            label="Avg Exit %",
            value=f"{avg_exit:+.1f}%",
            help="Average exit percentage"
        )

    with col5:
        median_mfe = stats.get("median_mfe_pct", 0)
        st.metric(
            label="Median MFE",
            value=f"{median_mfe:.1f}%",
            help="Median maximum favorable excursion"
        )


def render_options_mfe_mae_cards(stats: Dict[str, Any]) -> None:
    """
    Render MFE/MAE specific cards for options.

    Parameters:
    -----------
    stats : Dict[str, Any]
        Statistics from calculate_options_mfe_mae_summary()
    """
    if not stats or stats.get('total_trades', 0) == 0:
        st.info("No options MFE/MAE data available")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Median MFE",
            f"{stats['median_mfe_pct']:.1f}%",
            help="Typical max favorable movement for options"
        )
    with col2:
        st.metric(
            "Median MAE",
            f"{stats['median_mae_pct']:.1f}%",
            help="Typical max adverse movement for options"
        )
    with col3:
        st.metric(
            "MFE/MAE Ratio",
            f"{stats['median_mfe_mae_ratio']:.2f}",
            help="Favorable vs adverse movement (higher = better)"
        )
    with col4:
        st.metric(
            "Trades",
            f"{stats['total_trades']:,}",
            help="Total options trades analyzed"
        )

    # Second row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Median Exit",
            f"{stats.get('median_exit_pct', 0):.1f}%",
            help="Typical P/L at 15:30 ET"
        )
    with col2:
        st.metric(
            "MFE > 25%",
            f"{stats.get('pct_mfe_above_25', 0):.1f}%",
            help="Trades reaching 25% favorable move"
        )
    with col3:
        st.metric(
            "MFE > 50%",
            f"{stats.get('pct_mfe_above_50', 0):.1f}%",
            help="Trades reaching 50% favorable move"
        )
    with col4:
        mae_q25 = stats.get('mae_pct_q25', 0)
        mae_q75 = stats.get('mae_pct_q75', 0)
        st.metric(
            "MAE Range",
            f"{mae_q25:.1f}% - {mae_q75:.1f}%",
            help="25th to 75th percentile MAE"
        )


def render_options_leverage_cards(stats: Dict[str, Any]) -> None:
    """
    Render leverage comparison cards (options vs underlying).

    Parameters:
    -----------
    stats : Dict[str, Any]
        Statistics from calculate_leverage_comparison()
    """
    if not stats or stats.get('trades_with_comparison', 0) == 0:
        st.info("No leverage comparison data available")
        return

    st.markdown("**Effective Leverage**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "MFE Leverage",
            f"{stats['median_mfe_leverage']:.1f}x",
            help="Options MFE % / Underlying MFE %"
        )
    with col2:
        st.metric(
            "MAE Leverage",
            f"{stats['median_mae_leverage']:.1f}x",
            help="Options MAE % / Underlying MAE %"
        )
    with col3:
        st.metric(
            "Exit Leverage",
            f"{stats['median_exit_leverage']:.1f}x",
            help="Options Exit % / Underlying Exit %"
        )
    with col4:
        st.metric(
            "Trades Compared",
            f"{stats['trades_with_comparison']:,}",
            help="Trades with both options and underlying data"
        )

    st.markdown("**Movement Comparison**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Options MFE",
            f"{stats['median_options_mfe']:.1f}%"
        )
    with col2:
        st.metric(
            "Underlying MFE",
            f"{stats['median_underlying_mfe']:.2f}%"
        )
    with col3:
        st.metric(
            "Options MAE",
            f"{stats['median_options_mae']:.1f}%"
        )
    with col4:
        st.metric(
            "Underlying MAE",
            f"{stats['median_underlying_mae']:.2f}%"
        )


def render_options_sequence_cards(summary: Dict[str, Any]) -> None:
    """
    Render sequence analysis cards (MFE/MAE timing).

    Parameters:
    -----------
    summary : Dict[str, Any]
        Statistics from calculate_options_sequence_summary()
    """
    if not summary or summary.get('total_trades', 0) == 0:
        st.info("No options sequence data available")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="P(MFE First)",
            value=f"{summary['mfe_first_rate']:.1%}",
            help="Probability that favorable movement occurs before adverse"
        )

    with col2:
        st.metric(
            label="Time to MFE",
            value=f"{summary['median_time_to_mfe']:.0f} min",
            help="Median time for max favorable excursion"
        )

    with col3:
        st.metric(
            label="Time to MAE",
            value=f"{summary['median_time_to_mae']:.0f} min",
            help="Median time for max adverse excursion"
        )

    with col4:
        st.metric(
            label="Options Analyzed",
            value=f"{summary['total_trades']:,}",
            help="Total options trades in sample"
        )


def render_options_model_card(model_data: Dict[str, Any]) -> None:
    """
    Render a single options model performance card.

    Parameters:
    -----------
    model_data : Dict[str, Any]
        Model statistics dictionary
    """
    model_name = model_data.get("Model", "Unknown")
    win_rate = model_data.get("Win%", 0)
    trades = model_data.get("Trades", model_data.get("Wins", 0) + model_data.get("Losses", 0))
    avg_exit = model_data.get("Avg Exit%", 0)

    # Color based on win rate
    if win_rate >= 55:
        color = CHART_CONFIG.get("win_color", "#26a69a")
    elif win_rate >= 45:
        color = CHART_CONFIG.get("moderate_color", "#ffc107")
    else:
        color = CHART_CONFIG.get("loss_color", "#ef5350")

    st.markdown(f"""
    <div style="padding: 10px; border-left: 4px solid {color}; margin-bottom: 10px; background-color: #2a2a4e;">
        <h4 style="margin: 0; color: #e0e0e0;">{model_name}</h4>
        <p style="margin: 5px 0; color: #888;">
            {trades} trades | <span style="color: {color}">{win_rate:.1f}% win rate</span> | Avg Exit: {avg_exit:+.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_options_contract_card(
    contract_type: str,
    wins: int,
    losses: int,
    win_rate: float,
    avg_exit: float
) -> None:
    """
    Render a card for a specific contract type (CALL or PUT).

    Parameters:
    -----------
    contract_type : str
        "CALL" or "PUT"
    wins : int
        Number of winning trades
    losses : int
        Number of losing trades
    win_rate : float
        Win rate percentage
    avg_exit : float
        Average exit percentage
    """
    # Color based on contract type
    if contract_type.upper() == "CALL":
        color = CHART_CONFIG.get("win_color", "#26a69a")
    else:
        color = CHART_CONFIG.get("loss_color", "#ef5350")

    total = wins + losses

    st.markdown(f"""
    <div style="padding: 15px; border: 2px solid {color}; border-radius: 8px; margin-bottom: 10px; background-color: #2a2a4e;">
        <h3 style="margin: 0; color: {color};">{contract_type}</h3>
        <p style="margin: 10px 0 5px 0; color: #e0e0e0; font-size: 1.5em;">
            {total} trades
        </p>
        <p style="margin: 5px 0; color: #888;">
            {wins}W / {losses}L | {win_rate:.1f}% | Avg: {avg_exit:+.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)
