# MFE/MAE Distribution Analysis - Integration Guide (CALC-002)

## How to Add This Calculation to app.py

This guide shows you exactly how to integrate the MFE/MAE analysis into the Streamlit application.

---

## Quick Start (5 minutes)

### Step 1: Add Import (after line 58)

Open `app.py` and add this import after the existing CALC-001 import:

```python
# CALC-001: Win Rate by Model (YOUR file - build step by step!)
from calculations.model.win_rate_by_model import (
    calculate_win_rate_by_model,
    render_model_summary_table,
    render_model_win_loss_chart
)

# CALC-002: MFE/MAE Distribution Analysis
from calculations.trade_management.mfe_mae_stats import (
    calculate_mfe_mae_summary,
    render_mfe_mae_summary_cards,
    render_mfe_histogram,
    render_mae_histogram,
    render_mfe_mae_scatter,
    render_mfe_capture_histogram,
    render_model_mfe_mae_table,
    render_trade_management_analysis
)
```

### Step 2: Add to Metrics Overview Tab (around line 290)

In the "Metrics Overview" tab, after the Win Rate by Model section, add:

```python
        st.markdown("---")

        # =================================================================
        # CALC-002: MFE/MAE Distribution Analysis
        # =================================================================
        st.subheader("Trade Management Efficiency")
        st.markdown("*MFE/MAE analysis - are you capturing available profits?*")

        # Use all_trades (unfiltered) for system baseline
        with st.spinner("Analyzing trade management..."):
            mfe_mae_stats = calculate_mfe_mae_summary(all_trades)

        # Display summary cards
        render_mfe_mae_summary_cards(mfe_mae_stats)

        st.markdown("---")

        # Histograms side by side
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**MFE Distribution**")
            render_mfe_histogram(all_trades)

        with col2:
            st.markdown("**MAE Distribution**")
            render_mae_histogram(all_trades)

        st.markdown("---")

        # Scatter plot and capture histogram
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**MFE vs MAE Scatter**")
            render_mfe_mae_scatter(all_trades)

        with col2:
            st.markdown("**MFE Capture Distribution**")
            render_mfe_capture_histogram(all_trades)

        st.markdown("---")

        # Model breakdown table
        st.markdown("**MFE/MAE by Model**")
        render_model_mfe_mae_table(all_trades)
```

### Step 3: Update Monte AI Available Calculations

Find the `render_metrics_overview_monte_ai` call and update the `available_calculations` list:

```python
        render_metrics_overview_monte_ai(
            model_stats=model_stats,
            overall_stats=overall_stats,
            filters={
                "date_from": date_from,
                "date_to": date_to,
                "models": selected_models,
                "directions": selected_directions,
                "tickers": selected_tickers,
                "outcome": outcome_filter
            },
            available_calculations=[
                "CALC-001: Win Rate by Model (unfiltered system baseline)",
                "CALC-002: MFE/MAE Distribution Analysis (trade management efficiency)"
            ]
        )
```

---

## Alternative: One-Line Integration

If you prefer a simpler approach, use the convenience function:

```python
        # =================================================================
        # CALC-002: MFE/MAE Distribution Analysis
        # =================================================================
        render_trade_management_analysis(all_trades)
```

This single function renders all components in a predefined layout.

---

## Full Context: Where in app.py

Here's the surrounding context to help you find the right location:

```python
        # ... existing code ...

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
        # CALC-002: MFE/MAE Distribution Analysis  <-- ADD HERE
        # =================================================================
        # ... your new code ...

        st.markdown("---")

        # =================================================================
        # Monte AI - Research Assistant
        # =================================================================
        render_metrics_overview_monte_ai(...)
```

---

## Filtered vs Unfiltered Data

### System Baseline (Recommended)

Use `all_trades` for unfiltered analysis:
```python
# Bypass sidebar filters for true system performance
mfe_mae_stats = calculate_mfe_mae_summary(all_trades)
```

### Filtered Analysis

Use `trades` for filtered analysis:
```python
# Respects sidebar filters (model, direction, ticker, outcome)
mfe_mae_stats = calculate_mfe_mae_summary(trades)
```

You can display both:
```python
with st.expander("System Baseline (All Trades)"):
    render_mfe_mae_summary_cards(calculate_mfe_mae_summary(all_trades))

with st.expander("Filtered Analysis"):
    render_mfe_mae_summary_cards(calculate_mfe_mae_summary(trades))
```

---

## Adding to Sidebar Filters

If you want to add MFE/MAE specific filters:

```python
# In sidebar
with st.sidebar.expander("MFE/MAE Filters"):
    min_mfe = st.slider("Min MFE (R)", 0.0, 5.0, 0.0)
    max_mae = st.slider("Max MAE (R)", 0.0, 2.0, 2.0)

# Apply filters
df = pd.DataFrame(all_trades)
filtered = df[(df['mfe_r'] >= min_mfe) & (df['mae_r'] <= max_mae)]
mfe_mae_stats = calculate_mfe_mae_summary(filtered.to_dict('records'))
```

---

## Testing Your Integration

### Quick Test

1. Start the app: `streamlit run app.py --server.port 8502`
2. Navigate to "Metrics Overview" tab
3. Scroll down past "Win Rate by Model"
4. You should see MFE/MAE summary cards and charts

### Verify Data

Add debug output temporarily:
```python
st.write(f"Processing {len(all_trades)} trades")
st.write(f"MFE range: {min(t.get('mfe_r', 0) for t in all_trades):.2f} to {max(t.get('mfe_r', 0) for t in all_trades):.2f}")
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "No data available" | Check that trades have mfe_r, mae_r, pnl_r columns |
| Charts not rendering | Verify plotly is imported correctly |
| ImportError | Check the import path matches folder structure |
| Empty histograms | Verify numeric conversion in _prepare_dataframe() |

---

## Sample Output

When working correctly, you should see:

### Summary Cards Row 1
```
| Median MFE | Median MAE | MFE Capture | Trades  |
|------------|------------|-------------|---------|
| 1.75R      | 0.42R      | 58%         | 1,122   |
```

### Summary Cards Row 2
```
| % Hit 1R | % Hit 2R | % Hit 3R | Winners w/ Heat |
|----------|----------|----------|-----------------|
| 72.3%    | 45.1%    | 22.8%    | 38.5%           |
```

### Charts
- **MFE Histogram**: Blue bars showing profit distribution
- **MAE Histogram**: Red bars showing drawdown distribution
- **Scatter Plot**: Green winners (top-left), Red losers (bottom-right)
- **Capture Histogram**: Purple bars showing efficiency distribution

---

## Priority Analysis Order

Based on your January 1, 2026 analysis findings:

1. **Run on ALL trades first** - Establish baseline
2. **Filter to EPCH02 only** - Understand the profitable model
3. **Compare EPCH02 winners vs losers** - What separates them?
4. **Compare EPCH02 vs EPCH04** - Why does Primary rejection work but Secondary fail?

Add model-specific views:
```python
# EPCH02 only
epch02_trades = [t for t in all_trades if t.get('model') in ['EPCH02', 'EPCH2']]
st.markdown("### EPCH02 Analysis")
render_mfe_mae_summary_cards(calculate_mfe_mae_summary(epch02_trades))
```

---

## Next Calculations to Build

After CALC-002, consider:

- **CALC-003**: Time-based Analysis (MFE/MAE by time of day)
- **CALC-004**: Consecutive Win/Loss Patterns
- **CALC-005**: Indicator Correlation with MFE Capture

---

*CALC-002 Integration Guide | XIII Trading LLC | Epoch Trading System*
