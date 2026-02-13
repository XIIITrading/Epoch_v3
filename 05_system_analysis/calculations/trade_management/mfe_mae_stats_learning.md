# MFE/MAE Distribution Analysis - Learning Guide (CALC-002)

## Overview

This guide teaches you how to analyze trade management efficiency through Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE) metrics.

---

## What You'll Learn

### New Python Concepts

1. **Percentile calculations with pandas**
2. **Boolean aggregation for counting**
3. **Conditional calculations with masks**
4. **Dictionary returns from functions**
5. **Plotly histograms with reference lines**
6. **Scatter plots with color encoding**

### Trading Concepts

1. **MFE (Max Favorable Excursion)**: The maximum profit a trade reached before exit
2. **MAE (Max Adverse Excursion)**: The maximum drawdown a trade experienced
3. **MFE Capture Ratio**: How much of available profit was actually captured
4. **R-multiples**: Profit/loss measured in units of initial risk

---

## Step-by-Step Tutorial

### Step 1: Understanding the Data

Our trades have these key columns:
```python
{
    "trade_id": "abc123",
    "model": "EPCH02",
    "mfe_r": 2.5,       # Max profit was 2.5R
    "mae_r": 0.3,       # Max drawdown was 0.3R
    "pnl_r": 2.0,       # Actual profit was 2.0R
    "is_winner": True
}
```

**Key insight**: This trade had 2.5R available but only captured 2.0R (80% capture).

---

### Step 2: Percentile Calculations

Pandas makes percentile calculations easy:

```python
# Get the median (50th percentile)
df['mfe_r'].quantile(0.5)   # Median MFE

# Get quartiles
df['mfe_r'].quantile(0.25)  # Q1 (25th percentile)
df['mfe_r'].quantile(0.75)  # Q3 (75th percentile)

# Example output:
# If median MFE is 1.75R, half your trades had more than 1.75R available
```

**Why this matters**: Median is more robust than mean for skewed distributions (which trading P&L always is).

---

### Step 3: Boolean Aggregation

Count how many trades meet a condition:

```python
# What % of trades reached 1R profit at some point?
(df['mfe_r'] >= 1.0).mean()  # Returns 0.0 to 1.0

# Count how many trades reached 2R
(df['mfe_r'] >= 2.0).sum()   # Returns integer count

# Example:
# If 70% of trades reached 1R, you have good trade selection
# If only 20% reach 2R, your 2:1 targets may be unrealistic
```

**Trading insight**: This tells you if your profit targets are achievable.

---

### Step 4: Conditional Calculations

Calculate only where certain conditions are met:

```python
# MFE Capture = pnl_r / mfe_r
# But we can't divide by zero!

# Method 1: Boolean mask
mask = df['mfe_r'] > 0
df.loc[mask, 'capture'] = df.loc[mask, 'pnl_r'] / df.loc[mask, 'mfe_r']

# Method 2: Apply with lambda
df['capture'] = df.apply(
    lambda row: row['pnl_r'] / row['mfe_r'] if row['mfe_r'] > 0 else None,
    axis=1
)
```

**Why we need this**: Division by zero breaks calculations. Mask first, calculate second.

---

### Step 5: Dictionary Returns

Functions can return multiple values as a dictionary:

```python
def calculate_stats(df):
    return {
        'median_mfe': df['mfe_r'].median(),
        'median_mae': df['mae_r'].median(),
        'pct_hit_1r': (df['mfe_r'] >= 1.0).mean() * 100
    }

# Usage:
stats = calculate_stats(df)
print(f"Median MFE: {stats['median_mfe']:.2f}R")
print(f"% Hit 1R: {stats['pct_hit_1r']:.1f}%")
```

**Benefit**: Clean, self-documenting return values. Better than tuples.

---

### Step 6: Plotly Histograms

Create interactive histograms:

```python
import plotly.express as px

fig = px.histogram(
    df,
    x='mfe_r',
    nbins=30,
    title='MFE Distribution',
    labels={'mfe_r': 'MFE (R-multiples)'}
)

# Add vertical reference line at 1R
fig.add_vline(
    x=1.0,
    line_dash="dash",
    line_color="green",
    annotation_text="1R Target"
)

st.plotly_chart(fig, use_container_width=True)
```

**Why histograms matter**: They show the SHAPE of your profit distribution, not just averages.

---

### Step 7: Scatter Plots with Color Encoding

Visualize two variables with outcome coloring:

```python
fig = px.scatter(
    df,
    x='mae_r',           # X-axis: heat taken
    y='mfe_r',           # Y-axis: profit available
    color='outcome',     # Color by winner/loser
    color_discrete_map={
        'Winner': '#2ECC71',  # Green
        'Loser': '#E74C3C'    # Red
    },
    title='MFE vs MAE by Outcome'
)

# Add diagonal line (MFE = MAE)
fig.add_shape(
    type='line',
    x0=0, y0=0, x1=3, y1=3,
    line=dict(color='gray', dash='dot')
)
```

**Trading insight**: Winners should cluster in top-left (high MFE, low MAE). Losers cluster in bottom-right.

---

## Key Calculations Explained

### MFE Capture Ratio

```
MFE Capture = Actual Profit / Max Available Profit
            = pnl_r / mfe_r
```

| Capture | Interpretation |
|---------|----------------|
| 1.0 | Perfect - captured all available profit |
| 0.8 | Good - left 20% on the table |
| 0.5 | Fair - exited at half the potential |
| 0.2 | Poor - barely scratched the surface |
| < 0 | Loser - gave back profits and then some |

### Winner Heat Analysis

```python
# What % of winners took significant heat (>0.5R drawdown)?
winners = df[df['is_winner'] == True]
pct_with_heat = (winners['mae_r'] >= 0.5).mean() * 100
```

| % With Heat | Interpretation |
|-------------|----------------|
| < 30% | Stops well-placed, trades worked quickly |
| 30-50% | Normal - some trades need room to breathe |
| > 50% | Stops may be too tight, getting lucky |
| > 70% | Danger - surviving on luck, not edge |

---

## What Good Looks Like

### Trade Management Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| MFE Capture | < 40% | 40-60% | 60-80% | > 80% |
| % Hit 1R | < 50% | 50-65% | 65-80% | > 80% |
| Winners w/ Heat | > 60% | 40-60% | 20-40% | < 20% |
| Median MFE | < 1.0R | 1.0-1.5R | 1.5-2.0R | > 2.0R |

### Red Flags to Watch

1. **MFE Capture < 40%**: You're exiting way too early
2. **Winners with Heat > 60%**: Stops too tight, surviving on luck
3. **Loser MAE > Winner MFE**: Risk/reward is inverted
4. **No trades reaching 2R**: Your targets may be unrealistic

---

## Practical Exercises

### Exercise 1: Calculate Summary Stats
```python
# Given this data:
trades = [
    {"mfe_r": 2.0, "mae_r": 0.3, "pnl_r": 1.5, "is_winner": True},
    {"mfe_r": 1.5, "mae_r": 0.5, "pnl_r": 1.0, "is_winner": True},
    {"mfe_r": 0.5, "mae_r": 1.0, "pnl_r": -1.0, "is_winner": False},
]

# Calculate:
# 1. Median MFE
# 2. % that reached 1R
# 3. Average MFE capture (for trades with mfe_r > 0)
```

**Solution:**
```python
df = pd.DataFrame(trades)
median_mfe = df['mfe_r'].median()  # 1.5R
pct_1r = (df['mfe_r'] >= 1.0).mean() * 100  # 66.7%
mask = df['mfe_r'] > 0
avg_capture = (df.loc[mask, 'pnl_r'] / df.loc[mask, 'mfe_r']).mean()  # 0.167
```

### Exercise 2: Identify the Problem
```python
# System stats:
# - Median MFE: 2.5R (trades often have 2.5R available)
# - MFE Capture: 35% (only capturing 35% of available)
# - % Hit 1R: 75% (75% of trades hit 1R at some point)

# What's the problem and solution?
```

**Answer:** Exiting too early. 75% of trades hit 1R but only capturing 35% of 2.5R = 0.875R average. Should hold longer or trail stops.

---

## Common Mistakes

### Mistake 1: Dividing Without Checking for Zero
```python
# WRONG:
df['capture'] = df['pnl_r'] / df['mfe_r']  # ZeroDivisionError!

# RIGHT:
mask = df['mfe_r'] > 0
df.loc[mask, 'capture'] = df.loc[mask, 'pnl_r'] / df.loc[mask, 'mfe_r']
```

### Mistake 2: Using Mean Instead of Median
```python
# Mean is skewed by outliers
# One 10R winner makes mean look great

# Use median for typical trade, mean for total impact
median_mfe = df['mfe_r'].median()  # Typical trade
mean_mfe = df['mfe_r'].mean()      # Total impact
```

### Mistake 3: Forgetting to Normalize Models
```python
# Data might have "EPCH1" or "EPCH01"
# Always normalize before grouping

def normalize_model(m):
    model_map = {"EPCH1": "EPCH01", "EPCH2": "EPCH02", ...}
    return model_map.get(m, m)

df['model'] = df['model'].apply(normalize_model)
```

---

## Next Steps

After completing this module, you'll be able to:

1. **Identify trade management issues** - Are you exiting too early?
2. **Set realistic targets** - What % of trades actually reach 2R?
3. **Evaluate stop placement** - Are winners taking too much heat?
4. **Compare models** - Which model has best MFE capture?

### Integration

See `mfe_mae_stats_integration.md` for how to add this to app.py.

---

## Reference Files

- `mfe_mae_stats.py` - Your working file (build step by step)
- `mfe_mae_stats_complete.py` - Reference implementation (check your work)
- `mfe_mae_stats_integration.md` - How to connect to app.py

---

*CALC-002 | XIII Trading LLC | Epoch Trading System*
