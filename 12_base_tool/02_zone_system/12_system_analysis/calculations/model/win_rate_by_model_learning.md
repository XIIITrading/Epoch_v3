# Win Rate by Model - Learning Guide (CALC-001)

## What You'll Learn

By the end of this guide, you'll understand:
1. How to convert a list of dictionaries into a pandas DataFrame
2. How to use `groupby()` to split data into groups
3. How to use `agg()` to calculate statistics per group
4. How to display data in Streamlit tables
5. How to create bar charts with Plotly

---

## Prerequisites Check

Before starting, make sure you understand:
- Variables can hold different types of data
- Lists are ordered collections: `[1, 2, 3]`
- Dictionaries are key-value pairs: `{"name": "EPCH01", "wins": 5}`

---

## Concept 1: What is a DataFrame?

A **DataFrame** is like an Excel spreadsheet in Python.

Think of your trade data:
```
Each trade is a row:
  Row 1: model=EPCH01, is_winner=True
  Row 2: model=EPCH01, is_winner=False
  Row 3: model=EPCH02, is_winner=True
```

In Python, this comes as a **list of dictionaries**:
```python
trades = [
    {"model": "EPCH01", "is_winner": True},
    {"model": "EPCH01", "is_winner": False},
    {"model": "EPCH02", "is_winner": True}
]
```

### YOUR TURN: Experiment in Python Console

Open a Python console and type each line yourself:

```python
# Step 1: Import pandas (the data library)
import pandas as pd

# Step 2: Create sample data
trades = [
    {"model": "EPCH01", "is_winner": True},
    {"model": "EPCH01", "is_winner": False},
    {"model": "EPCH02", "is_winner": True}
]

# Step 3: Convert to DataFrame
df = pd.DataFrame(trades)

# Step 4: Look at what you created
print(df)
```

**What you should see:**
```
    model  is_winner
0  EPCH01       True
1  EPCH01      False
2  EPCH02       True
```

**Try these yourself:**
```python
# See just the model column
print(df["model"])

# See just the is_winner column
print(df["is_winner"])

# How many rows?
print(len(df))
```

---

## Concept 2: Grouping Data with groupby()

**The Problem:** You have 100 trades mixed together. You want to count wins for EACH model separately.

**The Solution:** `groupby()` splits your data into piles.

Imagine sorting cards by suit:
- All Hearts go in one pile
- All Spades go in another pile
- etc.

`groupby("model")` does the same thing:
- All EPCH01 trades go in one group
- All EPCH02 trades go in another group

### YOUR TURN: Try groupby

```python
# Continuing from before...

# Group the data by model
grouped = df.groupby("model")

# This returns a GroupBy object - it's a set of groups!
# To see what's in each group:
for name, group in grouped:
    print(f"\n=== {name} ===")
    print(group)
```

**What you should see:**
```
=== EPCH01 ===
    model  is_winner
0  EPCH01       True
1  EPCH01      False

=== EPCH02 ===
    model  is_winner
2  EPCH02       True
```

---

## Concept 3: Aggregating with agg()

After grouping, you want to CALCULATE something for each group.

`agg()` (short for "aggregate") applies functions to each group.

### YOUR TURN: Try agg

```python
# Count trades in each group
counts = df.groupby("model").agg(
    total=("is_winner", "count")
)
print(counts)
```

**What you should see:**
```
        total
model
EPCH01      2
EPCH02      1
```

**Now count wins (True values = 1 when summed):**
```python
stats = df.groupby("model").agg(
    wins=("is_winner", "sum"),     # sum() counts True values
    total=("is_winner", "count")   # count() counts all rows
)
print(stats)
```

**What you should see:**
```
        wins  total
model
EPCH01     1      2
EPCH02     1      1
```

---

## Concept 4: The Complete Calculation

Now let's put it all together:

### YOUR TURN: Build the Full Calculation

```python
import pandas as pd

# Sample data (more trades this time)
trades = [
    {"model": "EPCH01", "is_winner": True},
    {"model": "EPCH01", "is_winner": True},
    {"model": "EPCH01", "is_winner": False},
    {"model": "EPCH02", "is_winner": True},
    {"model": "EPCH02", "is_winner": False},
    {"model": "EPCH02", "is_winner": False},
]

# Convert to DataFrame
df = pd.DataFrame(trades)

# Group and aggregate
stats = df.groupby("model").agg(
    Wins=("is_winner", "sum"),
    Total=("is_winner", "count")
).reset_index()  # This makes 'model' a regular column again

# Calculate losses
stats["Losses"] = stats["Total"] - stats["Wins"]

# Calculate win percentage
stats["Win%"] = (stats["Wins"] / stats["Total"]) * 100

print(stats)
```

**What you should see:**
```
    model  Wins  Total  Losses       Win%
0  EPCH01     2      3       1  66.666667
1  EPCH02     1      3       2  33.333333
```

---

## Concept 5: Displaying in Streamlit

Streamlit makes it easy to show data:

### st.dataframe() - Shows a Table

```python
import streamlit as st

# In your Streamlit app:
st.dataframe(stats)
```

This creates an interactive table that users can sort and scroll.

### st.table() - Shows a Static Table

```python
st.table(stats)
```

This creates a fixed, non-interactive table.

**When to use which:**
- `st.dataframe()` for data exploration (scrollable, sortable)
- `st.table()` for small, fixed displays

---

## Concept 6: Creating a Plotly Bar Chart

Plotly creates interactive charts. Here's the pattern:

### YOUR TURN: Understand the Bar Chart

```python
import plotly.graph_objects as go

# Create an empty figure
fig = go.Figure()

# Add a set of bars (called a "trace")
fig.add_trace(
    go.Bar(
        name="Wins",           # Legend label
        x=["EPCH01", "EPCH02"],  # X-axis values
        y=[2, 1],               # Y-axis values (heights)
        marker_color="green"    # Bar color
    )
)

# Add another set of bars
fig.add_trace(
    go.Bar(
        name="Losses",
        x=["EPCH01", "EPCH02"],
        y=[1, 2],
        marker_color="red"
    )
)

# Configure the layout
fig.update_layout(
    barmode="group"  # Side-by-side bars
)

# In Streamlit:
st.plotly_chart(fig)
```

**barmode options:**
- `"group"` - bars side by side
- `"stack"` - bars stacked on top of each other

---

## Common Mistakes to Avoid

### Mistake 1: Forgetting reset_index()

```python
# WRONG - model is the index, not a column
stats = df.groupby("model").agg(Wins=("is_winner", "sum"))
print(stats["model"])  # ERROR! 'model' is not a column

# RIGHT - reset_index() makes model a column again
stats = df.groupby("model").agg(Wins=("is_winner", "sum")).reset_index()
print(stats["model"])  # Works!
```

### Mistake 2: Division by Zero

```python
# WRONG - will crash if Total is 0
stats["Win%"] = stats["Wins"] / stats["Total"] * 100

# RIGHT - handle the zero case
stats["Win%"] = stats.apply(
    lambda row: (row["Wins"] / row["Total"]) * 100 if row["Total"] > 0 else 0,
    axis=1
)
```

### Mistake 3: Not Handling Missing Data

If a model has no trades, it won't appear in groupby results.

```python
# Create a list of all expected models
all_models = pd.DataFrame({"Model": ["EPCH01", "EPCH02", "EPCH03", "EPCH04"]})

# Merge to ensure all models appear
result = all_models.merge(stats, on="Model", how="left")

# Fill missing values with 0
result = result.fillna(0)
```

---

## Exercise: Build It Yourself

Before looking at the complete code, try writing your own version:

1. Create a function called `my_win_rate_calc(trades)`
2. It should:
   - Take a list of trade dictionaries
   - Return a DataFrame with columns: Model, Wins, Losses, Win%
3. Test it with sample data

```python
def my_win_rate_calc(trades):
    """
    YOUR CODE HERE

    Hints:
    1. Convert trades to DataFrame
    2. Use groupby("model") and agg()
    3. Calculate Losses and Win%
    4. Return the result
    """
    pass  # Replace this with your code


# Test your function
sample = [
    {"model": "EPCH01", "is_winner": True},
    {"model": "EPCH01", "is_winner": False},
    {"model": "EPCH02", "is_winner": True},
]

result = my_win_rate_calc(sample)
print(result)
```

---

## Key Takeaways

1. **DataFrame** = spreadsheet in Python
2. **groupby()** = split data into groups by a column
3. **agg()** = calculate statistics for each group
4. **reset_index()** = turn index back into a column
5. **st.dataframe()** = display table in Streamlit
6. **go.Bar()** = create bar chart in Plotly
7. **fig.add_trace()** = add data to a chart
8. **barmode="group"** = side-by-side bars

---

## Next Steps

1. Read `win_rate_by_model_complete.py` - the full implementation
2. Read `win_rate_by_model_integration.md` - how to add it to your dashboard
3. Try modifying the code:
   - Change bar colors
   - Add a third metric (like Total R)
   - Sort models by win rate instead of alphabetically
