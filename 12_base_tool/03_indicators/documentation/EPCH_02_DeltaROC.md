# EPCH_02_DeltaROC - Documentation

**Indicator:** Delta ROC (Rate of Change)
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

Delta ROC measures HOW FAST buying/selling pressure is changing. This is an early reversal signal - it shows when pressure is SHIFTING before the absolute delta actually flips direction.

Think of it like acceleration vs velocity:
- **Rolling Delta (EPCH_01)** = velocity (current direction)
- **Delta ROC (EPCH_02)** = acceleration (change in direction)

A car heading north but decelerating will eventually stop and reverse. Delta ROC catches that deceleration early.

### Primary Use Cases

#### Early Reversal Detection
- **Positive ROC while delta is negative:** Selling pressure weakening - potential bottom
- **Negative ROC while delta is positive:** Buying pressure weakening - potential top
- **Divergences:** Price makes new extreme but pressure is fading

#### Momentum Confirmation
- **Rising ROC + Rising Price:** Strong bullish momentum
- **Falling ROC + Falling Price:** Strong bearish momentum
- **ROC and Price aligned:** Trend likely to continue

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Bright Green Histogram | ROC positive AND increasing (strong bullish acceleration) |
| Faded Green Histogram | ROC positive but decreasing (bullish but weakening) |
| Bright Red Histogram | ROC negative AND decreasing (strong bearish acceleration) |
| Faded Red Histogram | ROC negative but increasing (bearish but weakening) |
| White Signal Line | Smoothed ROC for trend confirmation |
| Circle Up (bottom) | ROC just crossed above zero |
| Circle Down (top) | ROC just crossed below zero |
| Yellow Diamond (bottom) | Bullish divergence detected |
| Yellow Diamond (top) | Bearish divergence detected |

### Trading Signals at EPCH Zones

When price reaches your HVN (High Volume Node) zones:

**At Support Zones (Looking for EPCH2 Long):**
- Yellow diamond (bullish divergence) = High probability reversal signal
- ROC crossing UP from negative = Selling pressure exhausting
- Faded red bars = Bears losing steam, watch for entry

**At Resistance Zones (Looking for EPCH4 Short):**
- Yellow diamond (bearish divergence) = High probability reversal signal
- ROC crossing DOWN from positive = Buying pressure exhausting
- Faded green bars = Bulls losing steam, watch for entry

### The Power of Divergences

Divergences are the highest-probability signals this indicator produces:

**Bullish Divergence:**
```
Price:  Lower Low
ROC:    Higher Low
Result: Reversal UP likely
```

**Bearish Divergence:**
```
Price:  Higher High
ROC:    Lower High
Result: Reversal DOWN likely
```

### Recommended Settings by Timeframe

| Timeframe | Delta Length | ROC Lookback | Signal Smooth | Notes |
|-----------|--------------|--------------|---------------|-------|
| M1 (Scalping) | 10 | 5 | 3 | Default - responsive |
| M5 (Day Trading) | 12 | 6 | 4 | Slightly smoothed |
| M15 (Swing) | 15 | 8 | 5 | Less noise |

### ROC Method Selection

**Simple (Default):**
- Direct difference: current delta minus delta N bars ago
- More responsive, more signals
- Better for scalping and quick entries

**Smoothed:**
- Difference between fast and slow SMAs of delta
- Fewer false signals, smoother output
- Better for swing trading and cleaner trends

---

## 2. TECHNICAL BASIS

### Why Rate of Change Matters

Absolute delta tells you WHO is in control. ROC tells you if they're GAINING or LOSING control.

Consider this scenario:
- Rolling delta = -50,000 (sellers in control)
- But ROC = +10,000 (selling pressure decreasing)

The sellers are still winning, but they're losing momentum. This is often the earliest warning of a reversal.

### Mathematical Foundation

Rate of Change is a first derivative - it measures the slope of the delta curve:
- **Positive ROC:** Delta curve is sloping upward (buying pressure increasing)
- **Negative ROC:** Delta curve is sloping downward (selling pressure increasing)
- **Zero ROC:** Delta is flat (equilibrium)

### Two ROC Calculation Methods

**Simple ROC:**
```
ROC = Delta[now] - Delta[N bars ago]
```
- Direct, unfiltered measurement
- Captures sudden shifts immediately
- Can be noisy in choppy markets

**Smoothed ROC:**
```
ROC = SMA(Delta, fast) - SMA(Delta, slow)
```
- Similar to MACD concept applied to delta
- Filters out noise
- Slightly lagging but cleaner signals

### Divergence Theory

Divergences occur when price and an oscillator disagree:
- Price makes a new extreme (higher high or lower low)
- But the oscillator fails to confirm (makes a lesser extreme)

This disagreement signals that the underlying momentum (in this case, volume-weighted buying/selling pressure) is not supporting the price move. Such moves often fail and reverse.

---

## 3. CALCULATIONS

### Step-by-Step Calculation

#### Step 1: Calculate Rolling Delta (from EPCH_01)
```
candle_delta = close > open ? +volume : close < open ? -volume : 0
rolling_delta = SUM(candle_delta, delta_length)
```

#### Step 2: Calculate ROC (Method Dependent)

**Simple Method:**
```
delta_roc = rolling_delta - rolling_delta[roc_lookback]
```

**Smoothed Method:**
```
fast_sma = SMA(rolling_delta, smooth_fast)
slow_sma = SMA(rolling_delta, smooth_slow)
delta_roc = fast_sma - slow_sma
```

#### Step 3: Signal Line
```
signal_line = SMA(delta_roc, signal_smooth)
```

#### Step 4: Zero Cross Detection
```
roc_cross_up   = delta_roc crosses ABOVE 0
roc_cross_down = delta_roc crosses BELOW 0
```

#### Step 5: Divergence Detection

**Bullish Divergence:**
```
price_lower_low = LOWEST(low, N) < LOWEST(low, N)[N]
roc_higher_low  = LOWEST(roc, N) > LOWEST(roc, N)[N]
bull_divergence = price_lower_low AND roc_higher_low AND roc < 0
```

**Bearish Divergence:**
```
price_higher_high = HIGHEST(high, N) > HIGHEST(high, N)[N]
roc_lower_high    = HIGHEST(roc, N) < HIGHEST(roc, N)[N]
bear_divergence   = price_higher_high AND roc_lower_high AND roc > 0
```

### Numerical Example

Given rolling delta over 8 bars:
| Bar | Rolling Delta | Simple ROC (5-bar) |
|-----|---------------|-------------------|
| 1 | +10,000 | — |
| 2 | +12,000 | — |
| 3 | +8,000 | — |
| 4 | +5,000 | — |
| 5 | +3,000 | — |
| 6 | +2,000 | +2,000 - 10,000 = **-8,000** |
| 7 | +4,000 | +4,000 - 12,000 = **-8,000** |
| 8 | +7,000 | +7,000 - 8,000 = **-1,000** |

Interpretation at Bar 8:
- Delta is still positive (+7,000) - buyers nominally in control
- ROC is negative (-1,000) - but buying pressure is lower than 5 bars ago
- ROC is RISING (-8,000 → -1,000) - selling pressure deceleration
- Signal: Potential shift back to bullish acceleration

### Histogram Color Logic

```
IF roc >= 0:
    IF roc > roc[1]: BRIGHT GREEN (positive and increasing)
    ELSE: FADED GREEN (positive but decreasing)
ELSE:
    IF roc < roc[1]: BRIGHT RED (negative and decreasing)
    ELSE: FADED RED (negative but increasing)
```

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_02_DeltaROC.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - color_bull_strong/weak                    |
| - color_bear_strong/weak                    |
| - color_neutral, color_signal               |
+---------------------------------------------+
| Input Group Constants                       |
| - GRP_PARAMS, GRP_THRESH, GRP_VISUAL,       |
|   GRP_ALERTS                                |
+---------------------------------------------+
| Input Definitions                           |
| - delta_length, roc_method, roc_lookback    |
| - smooth_fast, smooth_slow, signal_smooth   |
| - div_lookback                              |
| - show_* toggles, alert_* toggles           |
+---------------------------------------------+
| Core Calculations                           |
| - candle_delta, rolling_delta               |
| - delta_roc (method-dependent)              |
| - signal_line                               |
| - cross detection                           |
| - divergence detection                      |
+---------------------------------------------+
| Visual Outputs                              |
| - hline (zero line)                         |
| - plot (histogram with intensity colors)    |
| - plot (signal line)                        |
| - plotshape (cross markers)                 |
| - plotshape (divergence markers)            |
+---------------------------------------------+
| Alert Conditions                            |
| - Cross up, cross down                      |
| - Bullish divergence, bearish divergence    |
+---------------------------------------------+
| Info Panel (Table)                          |
| - ROC value                                 |
| - Trend direction                           |
| - Signal status                             |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `math.sum(source, length)` | Rolling sum for delta |
| `ta.sma(source, length)` | Simple moving average for smoothed ROC |
| `ta.crossover(a, b)` | Detects when `a` crosses above `b` |
| `ta.crossunder(a, b)` | Detects when `a` crosses below `b` |
| `ta.lowest(source, length)` | Lowest value over period (for divergence) |
| `ta.highest(source, length)` | Highest value over period (for divergence) |
| `switch` | Method selection for ROC calculation |

### Modification Guide

#### To Change ROC Calculation
The ROC calculation uses a switch statement:
```pinescript
delta_roc = switch roc_method
    "Simple" => rolling_delta - rolling_delta[roc_lookback]
    "Smoothed" => ta.sma(rolling_delta, smooth_fast) - ta.sma(rolling_delta, smooth_slow)
```

To add a new method (e.g., "EMA"):
1. Add option to input:
```pinescript
roc_method = input.string("Simple", title="ROC Method",
             options=["Simple", "Smoothed", "EMA"], ...)
```

2. Add case to switch:
```pinescript
delta_roc = switch roc_method
    "Simple" => rolling_delta - rolling_delta[roc_lookback]
    "Smoothed" => ta.sma(rolling_delta, smooth_fast) - ta.sma(rolling_delta, smooth_slow)
    "EMA" => ta.ema(rolling_delta, smooth_fast) - ta.ema(rolling_delta, smooth_slow)
```

#### To Adjust Divergence Sensitivity
The divergence lookback controls sensitivity:
```pinescript
div_lookback = input.int(5, title="Divergence Lookback", minval=3, maxval=15, ...)
```
- Lower values (3-5): More sensitive, more signals, more false positives
- Higher values (10-15): Less sensitive, fewer signals, higher quality

#### To Add Divergence Strength Filter
Add a minimum difference threshold:
```pinescript
div_min_diff = input.float(0.1, title="Min Divergence %", minval=0.01, maxval=1.0)

// Modify divergence conditions
roc_higher_low = roc_lowest > roc_lowest_prev * (1 + div_min_diff)
roc_lower_high = roc_highest < roc_highest_prev * (1 - div_min_diff)
```

#### To Export Values for Other Indicators
```pinescript
plot(delta_roc, title="ROC_Export", display=display.none)
plot(bull_divergence ? 1 : 0, title="BullDiv_Export", display=display.none)
plot(bear_divergence ? 1 : 0, title="BearDiv_Export", display=display.none)
```

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] Both ROC methods (Simple, Smoothed) calculate correctly
- [ ] Histogram colors show increasing/decreasing intensity
- [ ] Zero crosses detected and marked with circles
- [ ] Divergence detection works (test with known patterns)
- [ ] Signal line smooths appropriately
- [ ] Info panel displays current values
- [ ] Alerts fire correctly for all conditions
- [ ] No repainting (historical signals stable)
- [ ] Works on M1, M5, M15 timeframes
- [ ] Works alongside EPCH_01 without conflict

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Too many divergences | div_lookback too low | Increase to 8-10 |
| No divergences found | div_lookback too high or market trending | Decrease or wait for ranging market |
| ROC too noisy | Using Simple method in choppy market | Switch to Smoothed method |
| Signal line flat | signal_smooth too high | Decrease to 2-3 |
| Colors not changing | roc_rising/falling logic | Check comparison operators |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `candle_delta` | float | Single bar delta (+vol, -vol, or 0) |
| `rolling_delta` | float | Sum of candle_delta over delta_length |
| `delta_roc` | float | Rate of change of rolling_delta |
| `signal_line` | float | Smoothed ROC |
| `roc_cross_up` | bool | True when ROC crosses above 0 |
| `roc_cross_down` | bool | True when ROC crosses below 0 |
| `bull_divergence` | bool | True when bullish divergence detected |
| `bear_divergence` | bool | True when bearish divergence detected |
| `roc_rising` | bool | True when ROC > ROC[1] |
| `roc_falling` | bool | True when ROC < ROC[1] |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `delta_length` | int | 10 | 3-50 | Rolling delta window |
| `roc_method` | string | "Simple" | Simple/Smoothed | ROC calculation method |
| `roc_lookback` | int | 5 | 2-20 | Bars back for simple ROC |
| `smooth_fast` | int | 5 | 2-15 | Fast SMA for smoothed |
| `smooth_slow` | int | 15 | 5-30 | Slow SMA for smoothed |
| `signal_smooth` | int | 3 | 2-10 | Signal line smoothing |
| `div_lookback` | int | 5 | 3-15 | Divergence detection window |
| `show_histogram` | bool | true | - | Toggle histogram |
| `show_signal_line` | bool | true | - | Toggle signal line |
| `show_panel` | bool | true | - | Toggle info panel |
| `alert_cross` | bool | true | - | Enable cross alerts |
| `alert_divergence` | bool | true | - | Enable divergence alerts |

### Relationship to Other EPCH Indicators

| Indicator | Relationship |
|-----------|--------------|
| EPCH_01 (Rolling Delta) | Source data - ROC is derivative of delta |
| EPCH_03 (RVOL) | Filter - high RVOL + divergence = stronger signal |
| EPCH_04 (Momentum) | Opposite signal - momentum = continuation, divergence = reversal |
| EPCH_05 (Absorption) | Complementary - both indicate reversal potential |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
