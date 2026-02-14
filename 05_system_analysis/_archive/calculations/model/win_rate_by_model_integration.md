# Win Rate by Model - Integration Guide (CALC-001)

## Quick Reference

| Item | Value |
|------|-------|
| Calculation ID | CALC-001 |
| Module Path | `calculations/model/win_rate_by_model.py` (YOUR file) |
| Reference File | `calculations/model/win_rate_by_model_complete.py` (check your work) |
| Tab Location | Metrics Overview |
| Position | Below Summary Cards, above "My Custom Analysis" |
| Filters Apply | No (shows full system metrics) |

---

## Step 1: Import Statement

**ALREADY DONE!** The import is already in `app.py` (lines 53-58):

```python
# CALC-001: Win Rate by Model (YOUR file - build step by step!)
from calculations.model.win_rate_by_model import (
    calculate_win_rate_by_model,
    render_model_summary_table,
    render_model_win_loss_chart
)
```

This imports from YOUR file (`win_rate_by_model.py`), not the complete version.
As you build out your file, the dashboard will use your code!

---

## Step 2: Where to Add the Code

In `app.py`, locate the **Metrics Overview tab** (around line 218).

Find this section (around lines 218-231):

```python
with tab_metrics:
    st.header("Metrics Overview")
    st.markdown("*Your analysis sandbox - build calculations here*")

    # Summary cards (KEEP - already working)
    overall_stats = get_trade_statistics(trades)
    render_summary_cards(overall_stats)

    st.markdown("---")

    # =================================================================
    # YOUR CALCULATIONS GO BELOW THIS LINE
    # =================================================================
```

---

## Step 3: Add the Calculation Code

Insert the following code AFTER `st.markdown("---")` and BEFORE the comment about custom analysis:

```python
    st.markdown("---")

    # =================================================================
    # CALC-001: Win Rate by Model (Full System - Not Filtered)
    # =================================================================
    # Note: We use 'trades' directly, not the filtered version
    # This shows the FULL system breakdown for Monte Carlo baseline

    st.subheader("Win Rate by Model")
    st.markdown("*Full system performance breakdown (unfiltered)*")

    # Load ALL trades for this section (bypass filters)
    # We'll use the cached data but ignore filter selections
    with st.spinner("Calculating model breakdown..."):
        # Get unfiltered trades for true system performance
        all_trades = load_trades(
            date_from=date_from,
            date_to=date_to,
            models=None,      # No model filter
            directions=None,  # No direction filter
            tickers=None      # No ticker filter
        )

        # Calculate the statistics
        model_stats = calculate_win_rate_by_model(all_trades)

    # Display Summary Table
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Summary Table**")
        render_model_summary_table(model_stats)

    with col2:
        st.markdown("**Win/Loss Distribution**")
        render_model_win_loss_chart(model_stats)

    st.markdown("---")

    # =================================================================
    # YOUR CALCULATIONS GO BELOW THIS LINE
    # =================================================================
```

---

## Step 4: Full Updated Section

Here's how the complete `tab_metrics` section should look:

```python
    # ==========================================================================
    # Tab 1: Metrics Overview (Learning Sandbox)
    # ==========================================================================
    with tab_metrics:
        st.header("Metrics Overview")
        st.markdown("*Your analysis sandbox - build calculations here*")

        # Summary cards (KEEP - already working)
        overall_stats = get_trade_statistics(trades)
        render_summary_cards(overall_stats)

        st.markdown("---")

        # =================================================================
        # CALC-001: Win Rate by Model (Full System - Not Filtered)
        # =================================================================
        st.subheader("Win Rate by Model")
        st.markdown("*Full system performance breakdown (unfiltered)*")

        with st.spinner("Calculating model breakdown..."):
            all_trades = load_trades(
                date_from=date_from,
                date_to=date_to,
                models=None,
                directions=None,
                tickers=None
            )
            model_stats = calculate_win_rate_by_model(all_trades)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Summary Table**")
            render_model_summary_table(model_stats)

        with col2:
            st.markdown("**Win/Loss Distribution**")
            render_model_win_loss_chart(model_stats)

        st.markdown("---")

        # =================================================================
        # YOUR CALCULATIONS GO BELOW THIS LINE
        # =================================================================

        st.subheader("My Custom Analysis")
        st.info("This is where you'll add your own calculations!")

        # ... rest of the tab continues
```

---

## Step 5: Test the Integration

1. **Run the Streamlit app:**
   ```bash
   cd C:\XIIITradingSystems\Epoch\02_zone_system\12_indicator_analysis
   streamlit run app.py --server.port 8502
   ```

2. **Navigate to the Metrics Overview tab**

3. **Verify you see:**
   - Summary cards at the top (existing)
   - "Win Rate by Model" section with:
     - Summary table showing EPCH01-04 with Wins, Losses, Win%
     - Bar chart with green/red bars for each model
   - "My Custom Analysis" section below

---

## How It Connects to Your Data

### Data Flow

```
Supabase DB
    |
    v
load_trades() function (already exists in app.py)
    |
    v
Returns: List[Dict] - your trade records
    |
    v
calculate_win_rate_by_model(trades)
    |
    v
Returns: pd.DataFrame with Model, Wins, Losses, Win%
    |
    v
render_model_summary_table() --> Displays table
render_model_win_loss_chart() --> Displays chart
```

### Key Database Columns Used

From the `trades` table:
- `model`: The entry model (EPCH01, EPCH02, EPCH03, EPCH04)
- `is_winner`: Boolean indicating if trade was profitable

---

## Troubleshooting

### "Module not found" Error

Make sure the `__init__.py` file exists:
```
calculations/
    model/
        __init__.py                    <-- This file is required!
        win_rate_by_model_complete.py
```

### No Data Showing

1. Check that trades are loading:
   ```python
   st.write(f"Loaded {len(all_trades)} trades")
   ```

2. Check if model column exists:
   ```python
   if all_trades:
       st.write(f"Columns: {list(all_trades[0].keys())}")
   ```

### Wrong Model Names

The calculation handles both `EPCH1` and `EPCH01` formats automatically.
If your data uses different names, update the `MODELS` list in the complete.py file.

---

## Optional: Alternative Display Layout

If you prefer the chart below the table instead of side-by-side:

```python
# Vertical layout
st.subheader("Win Rate by Model")
st.markdown("*Full system performance breakdown (unfiltered)*")

model_stats = calculate_win_rate_by_model(all_trades)

st.markdown("**Summary Table**")
render_model_summary_table(model_stats)

st.markdown("**Win/Loss Distribution**")
render_model_win_loss_chart(model_stats)
```

---

## Next Calculations

Once this is working, you can add more calculations following the same pattern:

1. Create a new folder: `calculations/[category]/`
2. Create the three files: `[name]_complete.py`, `[name]_learning.md`, `[name]_integration.md`
3. Import and call in `app.py`

Suggested next calculations:
- CALC-002: Win Rate by Day of Week
- CALC-003: Win Rate by Time of Day
- CALC-004: Average R by Model
