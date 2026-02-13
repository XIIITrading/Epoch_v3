# EPCH_01_RollingDelta - Documentation

**Indicator:** Rolling Delta
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

Rolling Delta measures the cumulative buying vs selling pressure over a rolling window. Unlike session-anchored CVD (Cumulative Volume Delta) that resets each day, this indicator maintains contextually relevant readings throughout the trading session.

### Primary Use Cases

#### Directional Bias Identification
- **Positive Slow Delta:** Buyers have been in control over the lookback period - bullish bias
- **Negative Slow Delta:** Sellers have been in control - bearish bias
- **Near Zero:** Balanced market, no clear directional conviction

#### Entry Timing
- **Fast Delta Cross Up:** Short-term buying pressure emerging - potential long entry timing
- **Fast Delta Cross Down:** Short-term selling pressure emerging - potential short entry timing

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Green Histogram | Fast delta is positive (recent buying pressure) |
| Red Histogram | Fast delta is negative (recent selling pressure) |
| Green Line | Slow delta is positive (overall bullish bias) |
| Red Line | Slow delta is negative (overall bearish bias) |
| Triangle Up (bottom) | Fast delta just crossed above zero |
| Triangle Down (top) | Fast delta just crossed below zero |

### Trading Signals at EPCH Zones

When price reaches your HVN (High Volume Node) zones from the Epoch system:

**At Support Zones (Looking for EPCH2 Long):**
- Fast delta crossing UP + Slow delta positive = Strong long signal
- Fast delta crossing UP + Slow delta negative = Weaker long (counter-trend)
- Fast delta negative and falling = Wait, zone may fail

**At Resistance Zones (Looking for EPCH4 Short):**
- Fast delta crossing DOWN + Slow delta negative = Strong short signal
- Fast delta crossing DOWN + Slow delta positive = Weaker short (counter-trend)
- Fast delta positive and rising = Wait, zone may fail

### Recommended Settings by Timeframe

| Timeframe | Fast Length | Slow Length | Notes |
|-----------|-------------|-------------|-------|
| M1 (Scalping) | 10 | 30 | Default - responsive for quick entries |
| M5 (Day Trading) | 12 | 36 | Slightly smoothed |
| M15 (Swing Intraday) | 15 | 45 | Less noise, bigger moves |

### Info Panel Interpretation

The top-right panel shows:
- **Fast Delta:** Current fast delta value (volume units)
- **Slow Delta:** Current slow delta value (volume units)
- **Bias:** BULL / BEAR / NEUTRAL based on slow delta sign

---

## 2. TECHNICAL BASIS

### The Problem with Traditional CVD

Session-anchored Cumulative Volume Delta (CVD) has limitations:
1. **Resets daily** - loses context from previous session
2. **Drift problem** - naturally trends in one direction as day progresses
3. **Scale changes** - hard to compare morning vs afternoon readings
4. **Gap sensitivity** - overnight gaps create artificial jumps

### The Rolling Delta Solution

Rolling delta solves these issues by:
1. **Always relevant** - lookback window means recent data always matters
2. **No drift** - positive/negative readings represent actual recent imbalance
3. **Consistent scale** - readings are always over the same number of bars
4. **Gap resilient** - old data naturally rolls out of the window

### Dual Timeframe Approach

**Fast Window (Default: 10 bars)**
- Captures immediate momentum shifts
- Responsive to short-term order flow changes
- Used for entry timing decisions
- Zero crosses indicate momentum reversals

**Slow Window (Default: 30 bars)**
- Represents broader market bias
- Filters out noise from fast readings
- Determines trend direction context
- Supports with/against trend entry decisions

### Volume as Proxy for Order Flow

True delta (bid-ask trade assignment) requires tick data. On standard OHLCV charts, we approximate:
- **Green candle (close > open):** Assume buyers were in control - assign +volume
- **Red candle (close < open):** Assume sellers were in control - assign -volume
- **Doji (close = open):** No clear winner - assign 0

This approximation works because candle direction reflects which side "won" that bar.

---

## 3. CALCULATIONS

### Step-by-Step Calculation

#### Step 1: Candle Delta (Per Bar)
```
IF close > open THEN
    candle_delta = +volume    (bullish candle)
ELSE IF close < open THEN
    candle_delta = -volume    (bearish candle)
ELSE
    candle_delta = 0          (doji)
```

#### Step 2: Rolling Sums
```
fast_delta = SUM(candle_delta, fast_length)   // Default: 10 bars
slow_delta = SUM(candle_delta, slow_length)   // Default: 30 bars
```

#### Step 3: Zero Cross Detection
```
fast_cross_up   = fast_delta crosses ABOVE 0
fast_cross_down = fast_delta crosses BELOW 0
```

#### Step 4: Bias Determination
```
IF slow_delta > 0 THEN bias = "BULL"
ELSE IF slow_delta < 0 THEN bias = "BEAR"
ELSE bias = "NEUTRAL"
```

### Numerical Example

Given 5 bars of data:

| Bar | Close | Open | Direction | Volume | Candle Delta |
|-----|-------|------|-----------|--------|--------------|
| 1 | 100.50 | 100.00 | Up | 1000 | +1000 |
| 2 | 100.25 | 100.50 | Down | 1500 | -1500 |
| 3 | 100.75 | 100.25 | Up | 2000 | +2000 |
| 4 | 100.60 | 100.75 | Down | 800 | -800 |
| 5 | 100.60 | 100.60 | Doji | 500 | 0 |

**5-bar Rolling Delta:** +1000 - 1500 + 2000 - 800 + 0 = **+700**

Interpretation: Net buying pressure of 700 volume units over the last 5 bars.

### Mathematical Properties

- **Range:** Theoretically unbounded (depends on volume scale)
- **Units:** Same as volume (shares, contracts, etc.)
- **Zero:** Represents perfect balance between buying and selling
- **Sign:** Positive = net buying, Negative = net selling

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_01_RollingDelta.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - color_bull_strong/medium/weak             |
| - color_bear_strong/medium/weak             |
| - color_neutral, color_signal               |
+---------------------------------------------+
| Input Group Constants                       |
| - GRP_PARAMS, GRP_VISUAL, GRP_ALERTS        |
+---------------------------------------------+
| Input Definitions                           |
| - fast_length, slow_length                  |
| - show_* toggles                            |
| - alert_cross                               |
+---------------------------------------------+
| Core Calculations                           |
| - candle_delta (per-bar volume sign)        |
| - fast_delta (rolling sum)                  |
| - slow_delta (rolling sum)                  |
| - cross detection                           |
| - bias determination                        |
+---------------------------------------------+
| Visual Outputs                              |
| - hline (zero line)                         |
| - plot (histogram, line)                    |
| - fill (area between zero and delta)        |
| - bgcolor (optional bias background)        |
| - plotshape (cross markers)                 |
+---------------------------------------------+
| Alert Conditions                            |
| - Cross up, cross down, any cross           |
+---------------------------------------------+
| Info Panel (Table)                          |
| - Fast Delta value                          |
| - Slow Delta value                          |
| - Bias text                                 |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `math.sum(source, length)` | Rolling sum over lookback period |
| `ta.crossover(a, b)` | Detects when `a` crosses above `b` |
| `ta.crossunder(a, b)` | Detects when `a` crosses below `b` |
| `plot(..., style=plot.style_histogram)` | Renders histogram bars |
| `plotshape()` | Renders markers at specific conditions |
| `table.new()` / `table.cell()` | Creates info panel |
| `barstate.islast` | Only update table on last bar (performance) |

### Modification Guide

#### To Change Default Parameters
Locate the `input.int()` and `input.bool()` calls and modify the second argument:
```pinescript
fast_length = input.int(10, ...)  // Change 10 to new default
slow_length = input.int(30, ...)  // Change 30 to new default
```

#### To Add a New Lookback Window (e.g., "Medium")
1. Add new input:
```pinescript
med_length = input.int(20, title="Medium Length", minval=5, maxval=75,
             group=GRP_PARAMS, tooltip="Medium rolling window")
```

2. Add calculation:
```pinescript
med_delta = math.sum(candle_delta, med_length)
```

3. Add plot:
```pinescript
plot(show_med ? med_delta : na, title="Med Delta",
     style=plot.style_line, color=color.new(color.orange, 30), linewidth=1)
```

4. Update info panel with new row.

#### To Change Candle Delta Logic
The core delta assignment is on this line:
```pinescript
candle_delta = close > open ? volume : close < open ? -volume : 0.0
```

To use body-weighted delta instead:
```pinescript
body_pct = math.abs(close - open) / (high - low)
candle_delta = close > open ? volume * body_pct : close < open ? -volume * body_pct : 0.0
```

#### To Add Smoothing
Apply EMA or SMA to the delta values:
```pinescript
smooth_fast = ta.ema(fast_delta, 3)  // 3-bar EMA smoothing
```

#### To Export Values for Other Indicators
Add hidden plots that other scripts can read via `request.security()`:
```pinescript
plot(fast_delta, title="Fast_Export", display=display.none)
plot(slow_delta, title="Slow_Export", display=display.none)
plot(bias, title="Bias_Export", display=display.none)
```

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] All inputs appear in settings panel
- [ ] Changing inputs updates the chart
- [ ] Histogram colors match delta sign
- [ ] Slow line colors match delta sign
- [ ] Cross markers appear on actual zero crosses
- [ ] Info panel updates on latest bar
- [ ] Alerts can be created from alert menu
- [ ] No repainting (historical signals don't change)
- [ ] Works on M1, M5, M15, H1 timeframes
- [ ] Works on different instruments (stocks, futures, crypto)

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Undeclared identifier" | Variable used before definition | Move variable declaration above usage |
| Info panel not showing | `show_panel` is false or `barstate.islast` not triggering | Check toggle, ensure chart has data |
| Crosses not detected | Delta never actually crosses zero | Lower thresholds or check data quality |
| Scale looks wrong | Volume units vary by instrument | This is expected; readings are relative |
| Fill not visible | `show_fill` or `show_fast` is false | Enable both toggles |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `candle_delta` | float | Single bar delta (+vol, -vol, or 0) |
| `fast_delta` | float | Rolling sum over fast_length bars |
| `slow_delta` | float | Rolling sum over slow_length bars |
| `fast_cross_up` | bool | True when fast_delta crosses above 0 |
| `fast_cross_down` | bool | True when fast_delta crosses below 0 |
| `bias` | int | 1 (bull), -1 (bear), or 0 (neutral) |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `fast_length` | int | 10 | 3-50 | Fast rolling window |
| `slow_length` | int | 30 | 10-100 | Slow rolling window |
| `show_fast` | bool | true | - | Toggle fast histogram |
| `show_slow` | bool | true | - | Toggle slow line |
| `show_fill` | bool | true | - | Toggle area fill |
| `show_bias_bg` | bool | false | - | Toggle background color |
| `show_panel` | bool | true | - | Toggle info panel |
| `alert_cross` | bool | true | - | Enable cross alerts |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
