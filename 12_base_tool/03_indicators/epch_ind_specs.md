# EPCH Volume-Price Action Indicator Suite
## Technical Specification for PineScript Development

**Version:** 1.0  
**Author:** XIII Trading LLC  
**Purpose:** Support EPCH trading system entry/exit decisions by identifying continuation vs reversal probability at HVN zones

---

# PROJECT OVERVIEW

## Suite Structure

Six independent PineScript indicators that work together to identify:
- **EPCH1/EPCH3 (Continuation):** Zone failure, price moves through
- **EPCH2/EPCH4 (Reversal):** Zone holds, price reverses

## File Naming Convention

```
EPCH_01_RollingDelta.pine
EPCH_02_DeltaROC.pine
EPCH_03_RVOL.pine
EPCH_04_Momentum.pine
EPCH_05_Absorption.pine
EPCH_06_BodyRatio.pine
```

## Common Standards (Apply to ALL Scripts)

### Script Header Template
```pinescript
// This Pine Script™ code is subject to the terms of the Mozilla Public License 2.0
// © XIIITrading
//
// EPCH Indicator Suite - [Indicator Name]
// Version: 1.0
// Purpose: [Brief description]
```

### Version and Overlay Settings
```pinescript
//@version=5
indicator("[EPCH] Indicator Name", shorttitle="EPCH-XX", overlay=false)
// NOTE: overlay=true for candle-based visuals, false for separate pane
```

### Color Scheme (Consistent Across Suite)
```pinescript
// Standard Colors
color_bull_strong = color.new(color.green, 0)      // #00FF00
color_bull_medium = color.new(color.green, 30)
color_bull_weak   = color.new(color.green, 60)
color_bear_strong = color.new(color.red, 0)        // #FF0000
color_bear_medium = color.new(color.red, 30)
color_bear_weak   = color.new(color.red, 60)
color_neutral     = color.new(color.gray, 50)
color_signal      = color.new(color.yellow, 0)     // #FFFF00
color_absorption  = color.new(color.orange, 20)    // Absorption highlight
```

### Input Group Names (Consistent Across Suite)
```pinescript
// Group names for organized inputs
GRP_PARAMS = "Parameters"
GRP_THRESH = "Thresholds"
GRP_VISUAL = "Visual Settings"
GRP_ALERTS = "Alerts"
```

---

# CANDLE COLOR LEGEND

## Quick Reference for M1 Chart Reading

When both Momentum and Absorption indicators are active, candle colors tell you instantly what type of candle you're looking at:

| Candle Color | Hex Code | Indicator | Meaning | EPCH Implication |
|--------------|----------|-----------|---------|------------------|
| **Bright Green** | #00FF00 | Momentum | Bullish momentum (high vol + large up move) | Continuation up (EPCH3) |
| **Bright Red** | #FF0000 | Momentum | Bearish momentum (high vol + large down move) | Continuation down (EPCH1) |
| **Gold** | #FFD700 | Absorption | Buying absorption at recent low | Reversal up (EPCH2) |
| **Dark Orange** | #FF8C00 | Absorption | Selling absorption at recent high | Reversal down (EPCH4) |
| **Orange** | #FFA500 | Absorption | Absorption (location unclear) | Watch for direction |
| **Normal** | (default) | Neither | Normal candle | No signal |

## Visual Priority

If a candle meets BOTH momentum and absorption criteria (rare but possible), the **last indicator loaded** will control the candle color. Recommend loading order:
1. RVOL (separate pane)
2. Rolling Delta (separate pane)
3. Delta ROC (separate pane)
4. Body Ratio (separate pane)
5. **Momentum (overlay)** — load first of the two overlay indicators
6. **Absorption (overlay)** — load second, will override if conflict

This means absorption takes visual priority, which aligns with the reversal signal being more actionable at EPCH zones.

### Technical Note: barcolor() Limitation

TradingView only allows ONE `barcolor()` to be active per candle. When multiple overlay indicators use `barcolor()`, the last-loaded indicator wins. 

**If this becomes problematic**, we can create a combined overlay indicator (EPCH_07_CandleSignals.pine) that:
- Calculates both momentum AND absorption in one script
- Uses explicit priority logic (absorption > momentum)
- Single `barcolor()` with combined logic

For V1, we'll keep them separate for easier testing and iteration.

## At Your EPCH Zones

**Price enters your support zone (looking for EPCH2 long):**
- Gold/Orange candles = Absorption = Zone holding = TAKE THE TRADE
- Bright Red candles = Momentum = Zone failing = WAIT or FADE

**Price enters your resistance zone (looking for EPCH4 short):**
- Dark Orange candles = Absorption = Zone holding = TAKE THE TRADE  
- Bright Green candles = Momentum = Zone failing = WAIT or FADE

---

# INDICATOR 1: ROLLING DELTA

## File: `EPCH_01_RollingDelta.pine`

## Purpose
Replace session-anchored CVD with rolling window delta that remains contextually relevant throughout the trading day. Provides directional bias for entry decisions.

## Core Concept
- **Candle Delta:** Assign full candle volume as positive (green candle) or negative (red candle)
- **Rolling Sum:** Sum delta over configurable lookback windows
- **Dual Timeframe:** Fast window for timing, slow window for bias

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `fast_length` | int | 10 | 3 | 50 | Parameters | Fast rolling window for entry timing |
| `slow_length` | int | 30 | 10 | 100 | Parameters | Slow rolling window for directional bias |
| `show_fast` | bool | true | — | — | Visual Settings | Display fast delta histogram |
| `show_slow` | bool | true | — | — | Visual Settings | Display slow delta line |
| `show_fill` | bool | true | — | — | Visual Settings | Fill between fast histogram and zero |
| `show_bias_bg` | bool | false | — | — | Visual Settings | Background color based on slow delta |
| `alert_cross` | bool | true | — | — | Alerts | Alert on fast delta zero cross |

## Calculations

```
// Step 1: Calculate candle delta
candle_delta = 
    if close > open:
        volume  // Bullish candle = positive delta
    else if close < open:
        -volume  // Bearish candle = negative delta
    else:
        0  // Doji = neutral

// Step 2: Rolling sums
fast_delta = sum(candle_delta, fast_length)
slow_delta = sum(candle_delta, slow_length)

// Step 3: Zero cross detection
fast_cross_up = ta.crossover(fast_delta, 0)
fast_cross_down = ta.crossunder(fast_delta, 0)

// Step 4: Bias determination
bias = slow_delta > 0 ? 1 : slow_delta < 0 ? -1 : 0
```

## Outputs / Plots

```
// Primary: Fast delta as histogram
plot(show_fast ? fast_delta : na, 
     title="Fast Delta", 
     style=plot.style_histogram,
     color=fast_delta >= 0 ? color_bull_medium : color_bear_medium,
     linewidth=2)

// Secondary: Slow delta as line
plot(show_slow ? slow_delta : na,
     title="Slow Delta",
     style=plot.style_line,
     color=slow_delta >= 0 ? color_bull_strong : color_bear_strong,
     linewidth=2)

// Zero line
hline(0, "Zero", color=color_neutral, linestyle=hline.style_dashed)

// Background bias shading (optional)
bgcolor(show_bias_bg ? (slow_delta > 0 ? color_bull_weak : slow_delta < 0 ? color_bear_weak : na) : na,
        title="Bias Background")

// Cross markers
plotshape(fast_cross_up, title="Cross Up", location=location.bottom, 
          style=shape.triangleup, color=color_bull_strong, size=size.tiny)
plotshape(fast_cross_down, title="Cross Down", location=location.top,
          style=shape.triangledown, color=color_bear_strong, size=size.tiny)
```

## Alerts

```
alertcondition(fast_cross_up, 
               title="Fast Delta Cross Up",
               message="EPCH Rolling Delta: Fast crossed above zero (bullish)")

alertcondition(fast_cross_down,
               title="Fast Delta Cross Down", 
               message="EPCH Rolling Delta: Fast crossed below zero (bearish)")
```

## Display Panel (Info Box)

```
// Table in top-right showing current values
var table panel = table.new(position.top_right, 2, 3, 
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "Fast Δ", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(fast_delta, format.volume), 
               text_color=fast_delta >= 0 ? color_bull_strong : color_bear_strong)
    table.cell(panel, 0, 1, "Slow Δ", text_color=color.white)
    table.cell(panel, 1, 1, str.tostring(slow_delta, format.volume),
               text_color=slow_delta >= 0 ? color_bull_strong : color_bear_strong)
    table.cell(panel, 0, 2, "Bias", text_color=color.white)
    table.cell(panel, 1, 2, bias > 0 ? "BULL" : bias < 0 ? "BEAR" : "NEUTRAL",
               text_color=bias > 0 ? color_bull_strong : bias < 0 ? color_bear_strong : color_neutral)
```

## Testing Criteria

1. [ ] Fast and slow lengths are independently adjustable
2. [ ] Histogram correctly colors green for positive, red for negative
3. [ ] Zero crosses are detected and marked
4. [ ] Info panel displays current values
5. [ ] Alerts fire on zero crosses
6. [ ] Works on M1, M5, M15 timeframes without errors
7. [ ] No repainting issues

---

# INDICATOR 2: DELTA ROC (Rate of Change)

## File: `EPCH_02_DeltaROC.pine`

## Purpose
Detect acceleration/deceleration in buying/selling pressure. This is the early reversal signal — shows when pressure is SHIFTING before the absolute delta flips.

## Core Concept
- Measures HOW FAST delta is changing
- Positive ROC = buying pressure increasing (regardless of absolute level)
- Negative ROC = selling pressure increasing
- Zero crosses = momentum shift

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `delta_length` | int | 10 | 3 | 50 | Parameters | Rolling delta window (source for ROC) |
| `roc_method` | string | "Simple" | — | — | Parameters | Options: "Simple", "Smoothed" |
| `roc_lookback` | int | 5 | 2 | 20 | Parameters | Bars back for simple ROC |
| `smooth_fast` | int | 5 | 2 | 15 | Parameters | Fast SMA for smoothed method |
| `smooth_slow` | int | 15 | 5 | 30 | Parameters | Slow SMA for smoothed method |
| `show_histogram` | bool | true | — | — | Visual Settings | Show ROC as histogram |
| `show_signal_line` | bool | true | — | — | Visual Settings | Show smoothed signal line |
| `signal_smooth` | int | 3 | 2 | 10 | Visual Settings | Signal line smoothing |
| `alert_cross` | bool | true | — | — | Alerts | Alert on zero cross |
| `alert_divergence` | bool | true | — | — | Alerts | Alert on price/ROC divergence |

## Calculations

```
// Step 1: Calculate rolling delta (same as Indicator 1)
candle_delta = close > open ? volume : close < open ? -volume : 0
rolling_delta = math.sum(candle_delta, delta_length)

// Step 2: Calculate ROC based on method
delta_roc = switch roc_method
    "Simple" => rolling_delta - rolling_delta[roc_lookback]
    "Smoothed" => ta.sma(rolling_delta, smooth_fast) - ta.sma(rolling_delta, smooth_slow)

// Step 3: Signal line (smoothed ROC)
signal_line = ta.sma(delta_roc, signal_smooth)

// Step 4: Zero cross detection
roc_cross_up = ta.crossover(delta_roc, 0)
roc_cross_down = ta.crossunder(delta_roc, 0)

// Step 5: Divergence detection
// Bullish divergence: price makes lower low, ROC makes higher low
price_lower_low = low < ta.lowest(low, 5)[1]
roc_higher_low = ta.lowest(delta_roc, 5) > ta.lowest(delta_roc, 5)[5]
bull_divergence = price_lower_low and roc_higher_low and delta_roc < 0

// Bearish divergence: price makes higher high, ROC makes lower high
price_higher_high = high > ta.highest(high, 5)[1]
roc_lower_high = ta.highest(delta_roc, 5) < ta.highest(delta_roc, 5)[5]
bear_divergence = price_higher_high and roc_lower_high and delta_roc > 0
```

## Outputs / Plots

```
// ROC histogram
roc_color = delta_roc >= 0 ? 
            (delta_roc >= delta_roc[1] ? color_bull_strong : color_bull_weak) :
            (delta_roc <= delta_roc[1] ? color_bear_strong : color_bear_weak)

plot(show_histogram ? delta_roc : na,
     title="Delta ROC",
     style=plot.style_histogram,
     color=roc_color,
     linewidth=2)

// Signal line
plot(show_signal_line ? signal_line : na,
     title="Signal Line",
     style=plot.style_line,
     color=color.new(color.white, 30),
     linewidth=1)

// Zero line
hline(0, "Zero", color=color_neutral, linestyle=hline.style_solid)

// Cross markers
plotshape(roc_cross_up, title="ROC Cross Up", location=location.bottom,
          style=shape.circle, color=color_bull_strong, size=size.tiny)
plotshape(roc_cross_down, title="ROC Cross Down", location=location.top,
          style=shape.circle, color=color_bear_strong, size=size.tiny)

// Divergence markers
plotshape(bull_divergence, title="Bull Divergence", location=location.bottom,
          style=shape.diamond, color=color_signal, size=size.small)
plotshape(bear_divergence, title="Bear Divergence", location=location.top,
          style=shape.diamond, color=color_signal, size=size.small)
```

## Alerts

```
alertcondition(roc_cross_up,
               title="Delta ROC Cross Up",
               message="EPCH Delta ROC: Buying pressure accelerating")

alertcondition(roc_cross_down,
               title="Delta ROC Cross Down",
               message="EPCH Delta ROC: Selling pressure accelerating")

alertcondition(bull_divergence,
               title="Bullish Divergence",
               message="EPCH Delta ROC: Bullish divergence detected (reversal warning)")

alertcondition(bear_divergence,
               title="Bearish Divergence", 
               message="EPCH Delta ROC: Bearish divergence detected (reversal warning)")
```

## Display Panel

```
var table panel = table.new(position.top_right, 2, 3,
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "ROC", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(delta_roc, format.volume),
               text_color=delta_roc >= 0 ? color_bull_strong : color_bear_strong)
    table.cell(panel, 0, 1, "Trend", text_color=color.white)
    roc_trend = delta_roc > delta_roc[1] ? "▲ Rising" : delta_roc < delta_roc[1] ? "▼ Falling" : "— Flat"
    table.cell(panel, 1, 1, roc_trend,
               text_color=delta_roc > delta_roc[1] ? color_bull_strong : color_bear_strong)
    table.cell(panel, 0, 2, "Signal", text_color=color.white)
    table.cell(panel, 1, 2, bull_divergence ? "BULL DIV" : bear_divergence ? "BEAR DIV" : 
               roc_cross_up ? "CROSS UP" : roc_cross_down ? "CROSS DN" : "—",
               text_color=color_signal)
```

## Testing Criteria

1. [ ] Both ROC methods (Simple, Smoothed) calculate correctly
2. [ ] Histogram colors show increasing/decreasing intensity
3. [ ] Zero crosses detected accurately
4. [ ] Divergence detection works (test with known divergence patterns)
5. [ ] Signal line smooths appropriately
6. [ ] Alerts fire correctly
7. [ ] No repainting

---

# INDICATOR 3: RELATIVE VOLUME (RVOL)

## File: `EPCH_03_RVOL.pine`

## Purpose
Filter for significant volume candles. Only signals from high-volume candles should be acted upon. This indicator identifies when institutional-level volume is present.

## Core Concept
- Compare current volume to average volume
- Multiple threshold levels for different significance
- Used as a filter for Momentum and Absorption indicators

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `avg_length` | int | 20 | 5 | 100 | Parameters | Lookback for average volume |
| `threshold_1` | float | 1.5 | 1.1 | 3.0 | Thresholds | Elevated volume threshold |
| `threshold_2` | float | 2.5 | 1.5 | 5.0 | Thresholds | Significant volume threshold |
| `threshold_3` | float | 4.0 | 2.5 | 10.0 | Thresholds | Institutional volume threshold |
| `highlight_candles` | bool | true | — | — | Visual Settings | Highlight candles on price chart |
| `show_rvol_pane` | bool | true | — | — | Visual Settings | Show RVOL in separate pane |
| `show_avg_line` | bool | true | — | — | Visual Settings | Show average volume line |
| `alert_elevated` | bool | false | — | — | Alerts | Alert on elevated volume |
| `alert_significant` | bool | true | — | — | Alerts | Alert on significant volume |
| `alert_institutional` | bool | true | — | — | Alerts | Alert on institutional volume |

## Calculations

```
// Step 1: Calculate average volume
avg_volume = ta.sma(volume, avg_length)

// Step 2: Calculate RVOL
rvol = volume / avg_volume

// Step 3: Threshold classifications
is_elevated = rvol >= threshold_1 and rvol < threshold_2
is_significant = rvol >= threshold_2 and rvol < threshold_3
is_institutional = rvol >= threshold_3

// Step 4: Combined flag for any elevated
is_notable = rvol >= threshold_1
```

## Outputs / Plots

```
// RVOL in separate pane (if overlay=false)
rvol_color = is_institutional ? color.new(color.purple, 0) :
             is_significant ? color.new(color.orange, 0) :
             is_elevated ? color.new(color.yellow, 30) :
             color_neutral

plot(show_rvol_pane ? rvol : na,
     title="RVOL",
     style=plot.style_columns,
     color=rvol_color)

// Threshold lines
hline(threshold_1, "Elevated", color=color.new(color.yellow, 50), linestyle=hline.style_dotted)
hline(threshold_2, "Significant", color=color.new(color.orange, 50), linestyle=hline.style_dotted)
hline(threshold_3, "Institutional", color=color.new(color.purple, 50), linestyle=hline.style_dotted)
hline(1.0, "Average", color=color_neutral, linestyle=hline.style_dashed)

// Background highlighting for candles (requires overlay version or separate script)
// This would need to be overlay=true for candle highlighting
bgcolor(highlight_candles ? 
        (is_institutional ? color.new(color.purple, 85) :
         is_significant ? color.new(color.orange, 85) :
         is_elevated ? color.new(color.yellow, 90) : na) : na,
        title="Volume Highlight")
```

## Alerts

```
alertcondition(is_elevated and not is_elevated[1],
               title="Elevated Volume",
               message="EPCH RVOL: Elevated volume detected (>" + str.tostring(threshold_1) + "x)")

alertcondition(is_significant and not is_significant[1],
               title="Significant Volume",
               message="EPCH RVOL: Significant volume detected (>" + str.tostring(threshold_2) + "x)")

alertcondition(is_institutional and not is_institutional[1],
               title="Institutional Volume",
               message="EPCH RVOL: Institutional volume detected (>" + str.tostring(threshold_3) + "x)")
```

## Display Panel

```
var table panel = table.new(position.top_right, 2, 3,
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "RVOL", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(rvol, "#.##") + "x",
               text_color=rvol_color)
    table.cell(panel, 0, 1, "Volume", text_color=color.white)
    table.cell(panel, 1, 1, str.tostring(volume, format.volume), text_color=color.white)
    table.cell(panel, 0, 2, "Level", text_color=color.white)
    level_text = is_institutional ? "INSTITUTIONAL" :
                 is_significant ? "SIGNIFICANT" :
                 is_elevated ? "ELEVATED" : "NORMAL"
    table.cell(panel, 1, 2, level_text, text_color=rvol_color)
```

## Export Variable (for use by other indicators)

```
// Export RVOL value for other scripts to reference
// Other scripts can use: rvol_value = request.security(syminfo.tickerid, timeframe.period, rvol)

// Or use plot with display=display.none for script communication
plot(rvol, title="RVOL_Export", display=display.none)
plot(is_notable ? 1 : 0, title="Notable_Flag", display=display.none)
```

## Testing Criteria

1. [ ] RVOL calculates correctly (verify manually: volume / SMA)
2. [ ] Threshold levels display correctly
3. [ ] Colors match threshold breaches
4. [ ] Background highlighting appears on correct candles
5. [ ] Alerts fire only on NEW threshold breaches (not every bar above)
6. [ ] Works across different volume scales (penny stocks to SPY)
7. [ ] No division by zero errors

---

# INDICATOR 4: MOMENTUM DETECTOR

## File: `EPCH_04_Momentum.pine`

## Purpose
Identify efficient price movement where volume IS moving price. High volume + large price move = momentum (continuation signal, zone failure).

## Core Concept
- Momentum = significant volume + significant price movement
- Indicates orders are pushing through with minimal resistance
- At EPCH zones: suggests continuation (EPCH1/EPCH3)

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `atr_length` | int | 14 | 5 | 50 | Parameters | ATR calculation period |
| `atr_source` | string | "Auto" | — | — | Parameters | Options: "Auto", "Manual" |
| `manual_atr` | float | 0.50 | 0.01 | 100 | Parameters | Manual ATR value (if Manual selected) |
| `move_threshold` | float | 0.75 | 0.3 | 2.0 | Thresholds | ATR multiplier for "large move" |
| `rvol_threshold` | float | 1.5 | 1.1 | 3.0 | Thresholds | Minimum RVOL for momentum |
| `rvol_length` | int | 20 | 5 | 100 | Parameters | RVOL lookback period |
| `use_body` | bool | true | — | — | Parameters | Use candle body (vs full range) |
| `show_arrows` | bool | false | — | — | Visual Settings | Show momentum arrows (in addition to candle color) |
| `alert_bull_momentum` | bool | true | — | — | Alerts | Alert on bullish momentum |
| `alert_bear_momentum` | bool | true | — | — | Alerts | Alert on bearish momentum |

## Calculations

```
// Step 1: ATR
atr_value = atr_source == "Auto" ? ta.atr(atr_length) : manual_atr

// Step 2: Price move size
move_size = use_body ? math.abs(close - open) : (high - low)

// Step 3: Move ratio (relative to ATR)
move_ratio = move_size / atr_value

// Step 4: RVOL (inline calculation)
avg_volume = ta.sma(volume, rvol_length)
rvol = volume / avg_volume

// Step 5: Momentum detection
is_large_move = move_ratio >= move_threshold
is_high_volume = rvol >= rvol_threshold

is_momentum = is_large_move and is_high_volume

// Step 6: Direction
is_bull_momentum = is_momentum and close > open
is_bear_momentum = is_momentum and close < open

// Step 7: Momentum strength (for visual intensity)
momentum_strength = is_momentum ? (move_ratio * rvol) : 0
```

## Outputs / Plots

```
// This indicator should be overlay=true

// PRIMARY VISUAL: Candle coloring for momentum candles
// Bright, saturated colors to stand out
color_momentum_bull = color.new(#00FF00, 0)  // Bright green
color_momentum_bear = color.new(#FF0000, 0)  // Bright red

barcolor(is_bull_momentum ? color_momentum_bull :
         is_bear_momentum ? color_momentum_bear : na,
         title="Momentum Candle Color")

// OPTIONAL: Small arrows for additional clarity (off by default)
plotshape(show_arrows and is_bull_momentum,
          title="Bullish Momentum Arrow",
          location=location.belowbar,
          style=shape.triangleup,
          color=color_momentum_bull,
          size=size.tiny)

plotshape(show_arrows and is_bear_momentum,
          title="Bearish Momentum Arrow",
          location=location.abovebar,
          style=shape.triangledown,
          color=color_momentum_bear,
          size=size.tiny)
```

## Alerts

```
alertcondition(is_bull_momentum,
               title="Bullish Momentum",
               message="EPCH Momentum: Bullish momentum candle (high vol + large up move)")

alertcondition(is_bear_momentum,
               title="Bearish Momentum",
               message="EPCH Momentum: Bearish momentum candle (high vol + large down move)")
```

## Display Panel

```
var table panel = table.new(position.top_right, 2, 4,
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "Move", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(move_ratio, "#.##") + " ATR",
               text_color=is_large_move ? color_signal : color_neutral)
    table.cell(panel, 0, 1, "RVOL", text_color=color.white)
    table.cell(panel, 1, 1, str.tostring(rvol, "#.##") + "x",
               text_color=is_high_volume ? color_signal : color_neutral)
    table.cell(panel, 0, 2, "ATR", text_color=color.white)
    table.cell(panel, 1, 2, str.tostring(atr_value, "#.####"), text_color=color.white)
    table.cell(panel, 0, 3, "Signal", text_color=color.white)
    table.cell(panel, 1, 3, is_bull_momentum ? "▲ BULL MOM" : 
                           is_bear_momentum ? "▼ BEAR MOM" : "—",
               text_color=is_momentum ? color_signal : color_neutral)
```

## Testing Criteria

1. [ ] ATR calculates correctly (verify against TradingView built-in)
2. [ ] Manual ATR override works
3. [ ] Body vs range calculation differs correctly
4. [ ] Momentum only fires when BOTH conditions met
5. [ ] Direction (bull/bear) aligns with candle color
6. [ ] Arrows appear in correct location
7. [ ] Alerts fire correctly
8. [ ] Works on different instruments with varying ATR scales

---

# INDICATOR 5: ABSORPTION DETECTOR

## File: `EPCH_05_Absorption.pine`

## Purpose
Identify inefficient price movement where volume is NOT moving price. High volume + small price move = absorption (reversal signal, zone holds).

## Core Concept
- Absorption = significant volume + minimal price movement
- Indicates orders are being absorbed/matched without pushing price
- At EPCH zones: suggests reversal (EPCH2/EPCH4)

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `atr_length` | int | 14 | 5 | 50 | Parameters | ATR calculation period |
| `atr_source` | string | "Auto" | — | — | Parameters | Options: "Auto", "Manual" |
| `manual_atr` | float | 0.50 | 0.01 | 100 | Parameters | Manual ATR value (if Manual selected) |
| `move_threshold` | float | 0.30 | 0.1 | 0.5 | Thresholds | ATR multiplier for "small move" |
| `rvol_threshold` | float | 2.0 | 1.5 | 5.0 | Thresholds | Minimum RVOL for absorption |
| `rvol_length` | int | 20 | 5 | 100 | Parameters | RVOL lookback period |
| `body_ratio_max` | float | 0.35 | 0.1 | 0.5 | Thresholds | Max body ratio (wick analysis) |
| `show_markers` | bool | false | — | — | Visual Settings | Show absorption markers (in addition to candle color) |
| `alert_absorption` | bool | true | — | — | Alerts | Alert on any absorption |
| `alert_at_extreme` | bool | true | — | — | Alerts | Alert on absorption at high/low |

## Calculations

```
// Step 1: ATR
atr_value = atr_source == "Auto" ? ta.atr(atr_length) : manual_atr

// Step 2: Price move size (use body for absorption)
body_size = math.abs(close - open)
range_size = high - low

// Step 3: Move ratio (body relative to ATR)
move_ratio = body_size / atr_value

// Step 4: Body ratio (body relative to range)
body_ratio = range_size > 0 ? body_size / range_size : 1

// Step 5: RVOL
avg_volume = ta.sma(volume, rvol_length)
rvol = volume / avg_volume

// Step 6: Absorption detection
is_small_move = move_ratio <= move_threshold
is_high_volume = rvol >= rvol_threshold
has_wicks = body_ratio <= body_ratio_max

is_absorption = is_small_move and is_high_volume and has_wicks

// Step 7: Location context (is this at recent high or low?)
recent_high = ta.highest(high, 10)
recent_low = ta.lowest(low, 10)

at_high = high >= recent_high * 0.998  // Within 0.2% of recent high
at_low = low <= recent_low * 1.002     // Within 0.2% of recent low

absorption_at_high = is_absorption and at_high
absorption_at_low = is_absorption and at_low

// Step 8: Implied direction (where are wicks?)
upper_wick = high - math.max(open, close)
lower_wick = math.min(open, close) - low

bullish_absorption = is_absorption and lower_wick > upper_wick  // Buying the dip
bearish_absorption = is_absorption and upper_wick > lower_wick  // Selling the rip
```

## Outputs / Plots

```
// This indicator should be overlay=true

// PRIMARY VISUAL: Candle coloring for absorption candles
// Orange/yellow tones to distinguish from Momentum (green/red)
color_absorption_bull = color.new(#FFD700, 0)  // Gold (buying absorption at lows)
color_absorption_bear = color.new(#FF8C00, 0)  // Dark orange (selling absorption at highs)
color_absorption_neutral = color.new(#FFA500, 0)  // Orange (absorption, location unclear)

// Color based on location context
absorption_color = absorption_at_low ? color_absorption_bull :
                   absorption_at_high ? color_absorption_bear :
                   color_absorption_neutral

barcolor(is_absorption ? absorption_color : na,
         title="Absorption Candle Color")

// OPTIONAL: Small markers for additional clarity (off by default)
plotshape(show_markers and absorption_at_low,
          title="Bullish Absorption",
          location=location.belowbar,
          style=shape.diamond,
          color=color_absorption_bull,
          size=size.tiny)

plotshape(show_markers and absorption_at_high,
          title="Bearish Absorption",
          location=location.abovebar,
          style=shape.diamond,
          color=color_absorption_bear,
          size=size.tiny)
```

## Alerts

```
alertcondition(is_absorption,
               title="Absorption Detected",
               message="EPCH Absorption: High volume absorption candle detected")

alertcondition(absorption_at_high,
               title="Absorption at High",
               message="EPCH Absorption: Selling absorption at recent high (bearish reversal signal)")

alertcondition(absorption_at_low,
               title="Absorption at Low",
               message="EPCH Absorption: Buying absorption at recent low (bullish reversal signal)")
```

## Display Panel

```
var table panel = table.new(position.top_right, 2, 5,
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "Body", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(move_ratio, "#.##") + " ATR",
               text_color=is_small_move ? color_signal : color_neutral)
    table.cell(panel, 0, 1, "RVOL", text_color=color.white)
    table.cell(panel, 1, 1, str.tostring(rvol, "#.##") + "x",
               text_color=is_high_volume ? color_signal : color_neutral)
    table.cell(panel, 0, 2, "Body%", text_color=color.white)
    table.cell(panel, 1, 2, str.tostring(body_ratio * 100, "#") + "%",
               text_color=has_wicks ? color_signal : color_neutral)
    table.cell(panel, 0, 3, "Location", text_color=color.white)
    table.cell(panel, 1, 3, at_high ? "@ HIGH" : at_low ? "@ LOW" : "MID",
               text_color=at_high ? color_bear_strong : at_low ? color_bull_strong : color_neutral)
    table.cell(panel, 0, 4, "Signal", text_color=color.white)
    table.cell(panel, 1, 4, absorption_at_high ? "▼ SELL ABS" :
                           absorption_at_low ? "▲ BUY ABS" :
                           is_absorption ? "● ABSORB" : "—",
               text_color=is_absorption ? color_absorption : color_neutral)
```

## Testing Criteria

1. [ ] Absorption only fires when ALL three conditions met (small move + high vol + wicks)
2. [ ] Location detection (at high/low) works correctly
3. [ ] Body ratio calculation is accurate
4. [ ] Different visual for absorption at highs vs lows
5. [ ] Does NOT fire on normal small candles (requires high volume)
6. [ ] Alerts distinguish between generic absorption and location-specific
7. [ ] Works alongside Momentum indicator without conflict

---

# INDICATOR 6: BODY RATIO

## File: `EPCH_06_BodyRatio.pine`

## Purpose
Simple candle conviction measurement independent of volume. Used as confirmation layer — particularly useful when combined with RVOL.

## Core Concept
- Body Ratio = how much of the candle range is "body" vs "wick"
- High body ratio = strong conviction (full-bodied candle)
- Low body ratio = indecision (doji, hammer, shooting star)

## Inputs

| Input Name | Type | Default | Min | Max | Group | Tooltip |
|------------|------|---------|-----|-----|-------|---------|
| `strong_threshold` | float | 0.70 | 0.5 | 0.9 | Thresholds | Body ratio for "strong conviction" |
| `weak_threshold` | float | 0.30 | 0.1 | 0.5 | Thresholds | Body ratio for "indecision" |
| `show_as_histogram` | bool | true | — | — | Visual Settings | Show body ratio histogram |
| `color_candles` | bool | false | — | — | Visual Settings | Color candles by conviction |
| `show_markers` | bool | true | — | — | Visual Settings | Mark strong/weak candles |
| `alert_strong` | bool | false | — | — | Alerts | Alert on strong conviction |
| `alert_weak` | bool | true | — | — | Alerts | Alert on weak/indecision |

## Calculations

```
// Step 1: Calculate components
body = math.abs(close - open)
range_size = high - low

// Step 2: Body ratio (handle zero range)
body_ratio = range_size > 0 ? body / range_size : 0.5

// Step 3: Classification
is_strong = body_ratio >= strong_threshold
is_weak = body_ratio <= weak_threshold
is_normal = not is_strong and not is_weak

// Step 4: Direction with conviction
is_strong_bull = is_strong and close > open
is_strong_bear = is_strong and close < open
is_weak_bull = is_weak and close > open   // Hammer-like
is_weak_bear = is_weak and close < open   // Shooting star-like
is_doji = is_weak and math.abs(close - open) < (range_size * 0.05)
```

## Outputs / Plots

```
// Body ratio histogram (overlay=false)
ratio_color = is_strong ? (close > open ? color_bull_strong : color_bear_strong) :
              is_weak ? color_signal :
              color_neutral

plot(show_as_histogram ? body_ratio : na,
     title="Body Ratio",
     style=plot.style_columns,
     color=ratio_color)

// Threshold lines
hline(strong_threshold, "Strong", color=color.new(color.green, 50), linestyle=hline.style_dotted)
hline(weak_threshold, "Weak", color=color.new(color.orange, 50), linestyle=hline.style_dotted)
hline(0.5, "Neutral", color=color_neutral, linestyle=hline.style_dashed)

// Markers for overlay version (if overlay=true)
plotshape(show_markers and is_strong_bull,
          title="Strong Bull",
          location=location.belowbar,
          style=shape.arrowup,
          color=color_bull_strong,
          size=size.tiny)

plotshape(show_markers and is_strong_bear,
          title="Strong Bear",
          location=location.abovebar,
          style=shape.arrowdown,
          color=color_bear_strong,
          size=size.tiny)

plotshape(show_markers and is_doji,
          title="Doji",
          location=location.abovebar,
          style=shape.xcross,
          color=color_signal,
          size=size.tiny)

// Candle coloring
barcolor(color_candles ? ratio_color : na,
         title="Conviction Color")
```

## Alerts

```
alertcondition(is_strong_bull,
               title="Strong Bullish Candle",
               message="EPCH Body Ratio: Strong bullish conviction candle")

alertcondition(is_strong_bear,
               title="Strong Bearish Candle",
               message="EPCH Body Ratio: Strong bearish conviction candle")

alertcondition(is_weak,
               title="Indecision Candle",
               message="EPCH Body Ratio: Low conviction/indecision candle (potential reversal)")

alertcondition(is_doji,
               title="Doji Candle",
               message="EPCH Body Ratio: Doji detected (strong indecision)")
```

## Display Panel

```
var table panel = table.new(position.top_right, 2, 3,
                            bgcolor=color.new(color.black, 80))

if barstate.islast
    table.cell(panel, 0, 0, "Body%", text_color=color.white)
    table.cell(panel, 1, 0, str.tostring(body_ratio * 100, "#") + "%",
               text_color=ratio_color)
    table.cell(panel, 0, 1, "Type", text_color=color.white)
    type_text = is_doji ? "DOJI" :
                is_strong_bull ? "STRONG ▲" :
                is_strong_bear ? "STRONG ▼" :
                is_weak ? "WEAK" : "NORMAL"
    table.cell(panel, 1, 1, type_text, text_color=ratio_color)
    table.cell(panel, 0, 2, "Signal", text_color=color.white)
    table.cell(panel, 1, 2, is_strong ? "CONVICTION" : is_weak ? "INDECISION" : "—",
               text_color=is_strong or is_weak ? color_signal : color_neutral)
```

## Testing Criteria

1. [ ] Body ratio calculates correctly (verify: body / range)
2. [ ] Handles zero-range candles without error
3. [ ] Strong/weak classification matches thresholds
4. [ ] Doji detection works (very small body)
5. [ ] Colors align with direction
6. [ ] Works as both histogram (separate pane) and overlay
7. [ ] Alerts fire correctly

---

# DEVELOPMENT WORKFLOW

## Build Order

Build and test in this sequence (dependencies flow forward):

```
1. EPCH_03_RVOL.pine          (Foundation - used by others)
2. EPCH_01_RollingDelta.pine  (Core bias indicator)
3. EPCH_02_DeltaROC.pine      (Depends on delta logic)
4. EPCH_06_BodyRatio.pine     (Independent, simple)
5. EPCH_04_Momentum.pine      (Uses RVOL + ATR concepts)
6. EPCH_05_Absorption.pine    (Uses RVOL + ATR + body ratio concepts)
```

## Testing Protocol Per Indicator

### Unit Tests
1. Add indicator to 1-minute SPY chart
2. Verify all inputs appear in settings
3. Change each input and confirm behavior changes
4. Check visuals render correctly
5. Trigger alerts manually and verify they fire

### Integration Tests
1. Add all completed indicators to same chart
2. Verify no visual conflicts
3. Check info panels don't overlap
4. Confirm alerts from multiple indicators work
5. Test on multiple symbols (SPY, QQQ, lower-priced stock, higher-priced stock)

### Edge Cases
1. Pre-market / after-hours (low volume)
2. Market open (high volume spike)
3. Halt/resume scenarios
4. Weekend gaps on daily charts
5. Very low-priced stocks (penny stocks)
6. Very high-priced stocks (BRK.A)

## Iteration Notes

After each indicator is built and tested, document:
- Any parameter adjustments from defaults
- Edge cases discovered
- Visual improvements made
- Alert message refinements

---

# FUTURE ENHANCEMENTS (Post V1)

## V1 Design Philosophy: Zone Agnostic

V1 indicators identify signal candles (momentum/absorption) WITHOUT knowing where your EPCH zones are. This is intentional:

1. **Simpler to build and test** — each indicator is self-contained
2. **You bring the context** — you know where your HVN zones are from the Epoch system
3. **Flexible application** — signals work for any trading style, not just EPCH
4. **No input maintenance** — you don't have to update zone levels in TradingView

**Your workflow:** Run Epoch system → Know your zones → Watch M1 chart → See colored candles at your zones → Make entry decision

## Phase 2: Zone Integration

Once V1 indicators are proven, optionally add zone awareness:
- Manual zone input fields (zone_high, zone_low per ticker)
- Signals ONLY fire when price is within zone proximity
- Zone-anchored delta reset (delta restarts at zero when price enters zone)
- More focused alerts: "Absorption detected IN YOUR ZONE"

## Phase 3: Combined Signal Indicator

Create master indicator that:
- Reads signals from all 6 indicators
- Generates combined EPCH1/2/3/4 probability score
- Single alert for "high probability reversal" or "high probability continuation"
- Dashboard showing all indicator states at once

## Phase 4: Backtesting Framework

- Log signals with timestamps
- Export to CSV for analysis in Python
- Calculate signal accuracy at known zones
- Integrate with your existing Epoch backtesting infrastructure

---

*End of Specification Document*

**XIII Trading LLC | EPCH Indicator Suite v1.0**