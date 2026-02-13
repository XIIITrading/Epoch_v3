"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Win Rate by Model (CALC-001) - REFERENCE FILE
XIII Trading LLC
================================================================================

PURPOSE:
    Calculate win/loss statistics for each trading model (EPCH01-04).
    This is a foundational metric for Monte Carlo simulation that shows
    the performance breakdown between different entry models.

MODELS:
    - EPCH01: Primary Zone Continuation
    - EPCH02: Primary Zone Rejection
    - EPCH03: Secondary Zone Continuation
    - EPCH04: Secondary Zone Rejection

USAGE:
    from calculations.model.win_rate_by_model import (
        calculate_win_rate_by_model,
        render_model_summary_table,
        render_model_win_loss_chart
    )

    # Get the statistics
    model_stats = calculate_win_rate_by_model(trades)

    # Display in Streamlit
    render_model_summary_table(model_stats)
    render_model_win_loss_chart(model_stats)

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# pandas: A library for working with tabular data (like Excel in Python)
import pandas as pd

# typing: Helps document what types of data functions expect and return
from typing import List, Dict, Any

# streamlit: The web framework for building our dashboard
import streamlit as st

# plotly.graph_objects: Library for creating interactive charts
import plotly.graph_objects as go


# =============================================================================
# CONFIGURATION
# =============================================================================
# Define the models we expect to see (in display order)
MODELS = ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]

# Chart colors that match the existing dashboard theme
CHART_COLORS = {
    "win": "#26a69a",      # Teal green for wins
    "loss": "#ef5350",     # Red for losses
    "background": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0"
}


# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================
def calculate_win_rate_by_model(trades: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculate win/loss statistics grouped by trading model.

    This function takes raw trade data and produces a summary showing:
    - Number of wins per model
    - Number of losses per model
    - Win percentage per model
    - Expectancy (average R per trade) per model

    Parameters:
    -----------
    trades : List[Dict[str, Any]]
        A list of trade dictionaries from the database.
        Each dictionary must have 'model' and 'is_winner' keys.
        Optionally includes 'pnl_r' for expectancy calculation.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with columns: Model, Wins, Losses, Win%, Expectancy
        Rows are ordered: EPCH01, EPCH02, EPCH03, EPCH04

    Example:
    --------
    >>> trades = [
    ...     {"model": "EPCH01", "is_winner": True, "pnl_r": 1.5},
    ...     {"model": "EPCH01", "is_winner": False, "pnl_r": -1.0},
    ...     {"model": "EPCH02", "is_winner": True, "pnl_r": 2.0},
    ... ]
    >>> df = calculate_win_rate_by_model(trades)
    >>> print(df)
       Model  Wins  Losses  Win%  Expectancy
    0  EPCH01    1       1  50.0        0.25
    1  EPCH02    1       0 100.0        2.00
    """

    # -------------------------------------------------------------------------
    # STEP 1: Handle empty data
    # -------------------------------------------------------------------------
    # If no trades provided, return an empty DataFrame with the correct columns
    if not trades:
        return pd.DataFrame(columns=["Model", "Wins", "Losses", "Win%", "Expectancy"])

    # -------------------------------------------------------------------------
    # STEP 2: Convert list of dictionaries to a pandas DataFrame
    # -------------------------------------------------------------------------
    # This is like creating a spreadsheet from a list of rows
    # Each dictionary becomes one row, each key becomes a column
    df = pd.DataFrame(trades)

    # -------------------------------------------------------------------------
    # STEP 3: Validate required columns exist
    # -------------------------------------------------------------------------
    # We need 'model' to group by and 'is_winner' to count wins/losses
    if "model" not in df.columns or "is_winner" not in df.columns:
        return pd.DataFrame(columns=["Model", "Wins", "Losses", "Win%", "Expectancy"])

    # -------------------------------------------------------------------------
    # STEP 4: Normalize model names (handle EPCH1 vs EPCH01 variations)
    # -------------------------------------------------------------------------
    # Some data might use "EPCH1" while we want "EPCH01"
    # This creates a mapping function to standardize names
    def normalize_model(model_name):
        """Convert EPCH1 -> EPCH01, EPCH2 -> EPCH02, etc."""
        if model_name is None:
            return None
        # If it's already in the right format, return as-is
        if model_name in MODELS:
            return model_name
        # Try to convert short form to long form
        model_map = {
            "EPCH1": "EPCH01", "EPCH2": "EPCH02",
            "EPCH3": "EPCH03", "EPCH4": "EPCH04"
        }
        return model_map.get(model_name, model_name)

    # Apply the normalization to all model values
    df["model"] = df["model"].apply(normalize_model)

    # -------------------------------------------------------------------------
    # STEP 5: Group by model and count wins/losses
    # -------------------------------------------------------------------------
    # groupby() splits the data into groups based on the 'model' column
    # agg() then applies functions to each group
    #
    # Think of it like:
    # 1. Put all EPCH01 trades in one pile
    # 2. Put all EPCH02 trades in another pile
    # 3. Count wins and total trades in each pile

    # -------------------------------------------------------------------------
    # STEP 5a: Check if pnl_r column exists for expectancy calculation
    # -------------------------------------------------------------------------
    has_pnl_r = "pnl_r" in df.columns

    if has_pnl_r:
        # Include pnl_r in aggregation for expectancy
        stats = df.groupby("model").agg(
            # Count how many True values in 'is_winner' (this counts wins)
            Wins=("is_winner", "sum"),
            # Count total trades in each group
            Total=("is_winner", "count"),
            # Calculate average R per trade (expectancy)
            Expectancy=("pnl_r", "mean")
        ).reset_index()
    else:
        stats = df.groupby("model").agg(
            # Count how many True values in 'is_winner' (this counts wins)
            Wins=("is_winner", "sum"),
            # Count total trades in each group
            Total=("is_winner", "count")
        ).reset_index()
        # Add placeholder expectancy column if pnl_r doesn't exist
        stats["Expectancy"] = 0.0

    # -------------------------------------------------------------------------
    # STEP 6: Calculate losses and win percentage
    # -------------------------------------------------------------------------
    # Losses = Total - Wins
    stats["Losses"] = stats["Total"] - stats["Wins"]

    # Win% = (Wins / Total) * 100
    # Using a lambda (inline function) to handle division by zero
    stats["Win%"] = stats.apply(
        lambda row: round((row["Wins"] / row["Total"]) * 100, 1) if row["Total"] > 0 else 0,
        axis=1  # axis=1 means apply to each row
    )

    # Round expectancy to 2 decimal places for clean display
    stats["Expectancy"] = stats["Expectancy"].round(2)

    # -------------------------------------------------------------------------
    # STEP 7: Rename and reorder columns for display
    # -------------------------------------------------------------------------
    stats = stats.rename(columns={"model": "Model"})

    # Keep only the columns we want, in the order we want
    stats = stats[["Model", "Wins", "Losses", "Win%", "Expectancy"]]

    # -------------------------------------------------------------------------
    # STEP 8: Ensure all models are present and in correct order
    # -------------------------------------------------------------------------
    # Create a DataFrame with all models to ensure consistent display
    all_models = pd.DataFrame({"Model": MODELS})

    # Merge with our stats - left merge keeps all models even if no trades
    result = all_models.merge(stats, on="Model", how="left")

    # Fill missing values with 0 (models with no trades)
    result = result.fillna(0)

    # Convert numeric columns to integers (they may be floats after fillna)
    result["Wins"] = result["Wins"].astype(int)
    result["Losses"] = result["Losses"].astype(int)

    return result


# =============================================================================
# STREAMLIT DISPLAY FUNCTIONS
# =============================================================================
def render_model_summary_table(model_stats: pd.DataFrame) -> None:
    """
    Display the model statistics as a formatted Streamlit table.

    This creates a clean table with:
    - Column headers: EPCH01, EPCH02, EPCH03, EPCH04
    - Row headers: Wins, Losses, Win%, Expectancy

    Parameters:
    -----------
    model_stats : pd.DataFrame
        Output from calculate_win_rate_by_model()
    """

    # -------------------------------------------------------------------------
    # STEP 1: Handle empty data
    # -------------------------------------------------------------------------
    if model_stats.empty:
        st.info("No trade data available for model breakdown")
        return

    # -------------------------------------------------------------------------
    # STEP 2: Transpose the DataFrame for the desired layout
    # -------------------------------------------------------------------------
    # We want models as COLUMNS, not rows
    # transpose() flips rows and columns

    # Set Model as the index first
    display_df = model_stats.set_index("Model")

    # Transpose: rows become columns, columns become rows
    display_df = display_df.T

    # -------------------------------------------------------------------------
    # STEP 3: Format the Win% and Expectancy rows for display
    # -------------------------------------------------------------------------
    # Create a copy to avoid modifying the original
    formatted_df = display_df.copy()

    # Format the Win% row with percentage symbol
    if "Win%" in formatted_df.index:
        formatted_df.loc["Win%"] = formatted_df.loc["Win%"].apply(
            lambda x: f"{x:.1f}%"
        )

    # Format the Expectancy row with R suffix (e.g., "0.25R")
    if "Expectancy" in formatted_df.index:
        formatted_df.loc["Expectancy"] = formatted_df.loc["Expectancy"].apply(
            lambda x: f"{x:.2f}R"
        )

    # -------------------------------------------------------------------------
    # STEP 4: Display using Streamlit's dataframe function
    # -------------------------------------------------------------------------
    # use_container_width=True makes it fill the available space
    st.dataframe(
        formatted_df,
        use_container_width=True,
        height=180  # Increased height for 4 rows
    )


def render_model_win_loss_chart(model_stats: pd.DataFrame) -> None:
    """
    Display a grouped bar chart showing wins and losses per model.

    Creates a chart with:
    - X-axis: Model names (EPCH01-04)
    - Y-axis: Count of trades
    - Two bars per model: green for wins, red for losses

    Parameters:
    -----------
    model_stats : pd.DataFrame
        Output from calculate_win_rate_by_model()
    """

    # -------------------------------------------------------------------------
    # STEP 1: Handle empty data
    # -------------------------------------------------------------------------
    if model_stats.empty:
        st.info("No trade data available for chart")
        return

    # -------------------------------------------------------------------------
    # STEP 2: Create the Plotly figure
    # -------------------------------------------------------------------------
    # go.Figure() creates an empty chart that we'll add bars to
    fig = go.Figure()

    # -------------------------------------------------------------------------
    # STEP 3: Add the Wins bars (first bar in each group)
    # -------------------------------------------------------------------------
    fig.add_trace(
        go.Bar(
            name="Wins",                           # Legend label
            x=model_stats["Model"],                # X-axis values (model names)
            y=model_stats["Wins"],                 # Y-axis values (win counts)
            marker_color=CHART_COLORS["win"],      # Bar color (teal green)
            text=model_stats["Wins"],              # Text labels on bars
            textposition="auto"                    # Auto-position the labels
        )
    )

    # -------------------------------------------------------------------------
    # STEP 4: Add the Losses bars (second bar in each group)
    # -------------------------------------------------------------------------
    fig.add_trace(
        go.Bar(
            name="Losses",                         # Legend label
            x=model_stats["Model"],                # X-axis values (model names)
            y=model_stats["Losses"],               # Y-axis values (loss counts)
            marker_color=CHART_COLORS["loss"],     # Bar color (red)
            text=model_stats["Losses"],            # Text labels on bars
            textposition="auto"                    # Auto-position the labels
        )
    )

    # -------------------------------------------------------------------------
    # STEP 5: Configure the chart layout
    # -------------------------------------------------------------------------
    fig.update_layout(
        # Title
        title="Win/Loss Count by Model",

        # Bar mode: 'group' places bars side by side (vs 'stack')
        barmode="group",

        # Colors to match dashboard theme
        paper_bgcolor=CHART_COLORS["paper"],
        plot_bgcolor=CHART_COLORS["background"],
        font=dict(color=CHART_COLORS["text"]),

        # Chart dimensions
        height=400,

        # Legend position
        legend=dict(
            orientation="h",      # Horizontal legend
            yanchor="bottom",
            y=1.02,               # Position above chart
            xanchor="right",
            x=1
        ),

        # Margins
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # -------------------------------------------------------------------------
    # STEP 6: Configure axes
    # -------------------------------------------------------------------------
    fig.update_xaxes(title="Model")
    fig.update_yaxes(title="Number of Trades")

    # -------------------------------------------------------------------------
    # STEP 7: Display the chart in Streamlit
    # -------------------------------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# CONVENIENCE FUNCTION: Render Both Together
# =============================================================================
def render_model_breakdown(trades: List[Dict[str, Any]]) -> None:
    """
    Calculate and render both the table and chart for model breakdown.

    This is a convenience function that:
    1. Calculates the statistics
    2. Displays the summary table
    3. Displays the bar chart

    Parameters:
    -----------
    trades : List[Dict[str, Any]]
        Raw trade data from the database

    Usage:
    ------
    # In app.py, just call this one function:
    render_model_breakdown(trades)
    """

    # Calculate the statistics
    model_stats = calculate_win_rate_by_model(trades)

    # Add a section header
    st.subheader("Win Rate by Model")
    st.markdown("*Performance breakdown by entry model (unfiltered)*")

    # Display the table
    st.markdown("**Summary Table**")
    render_model_summary_table(model_stats)

    # Add some spacing
    st.markdown("")

    # Display the chart
    st.markdown("**Win/Loss Distribution**")
    render_model_win_loss_chart(model_stats)


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================
if __name__ == "__main__":
    # This code only runs if you execute this file directly
    # It won't run when imported into app.py

    # Example trade data for testing (now includes pnl_r for expectancy)
    sample_trades = [
        {"model": "EPCH01", "is_winner": True, "pnl_r": 1.5},
        {"model": "EPCH01", "is_winner": True, "pnl_r": 2.0},
        {"model": "EPCH01", "is_winner": False, "pnl_r": -1.0},
        {"model": "EPCH02", "is_winner": True, "pnl_r": 1.0},
        {"model": "EPCH02", "is_winner": False, "pnl_r": -1.0},
        {"model": "EPCH02", "is_winner": False, "pnl_r": -1.0},
        {"model": "EPCH03", "is_winner": True, "pnl_r": 3.0},
        {"model": "EPCH04", "is_winner": False, "pnl_r": -1.0},
    ]

    # Calculate and print results
    result = calculate_win_rate_by_model(sample_trades)
    print("\nModel Win Rate Statistics:")
    print("=" * 50)
    print(result.to_string(index=False))
    print("\nExpected output:")
    print("  EPCH01: 2 wins, 1 loss, 66.7%, Expectancy = 0.83R")
    print("  EPCH02: 1 win, 2 losses, 33.3%, Expectancy = -0.33R")
    print("  EPCH03: 1 win, 0 losses, 100%, Expectancy = 3.00R")
    print("  EPCH04: 0 wins, 1 loss, 0%, Expectancy = -1.00R")
