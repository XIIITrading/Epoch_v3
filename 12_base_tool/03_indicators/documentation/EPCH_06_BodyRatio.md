# EPCH_06_BodyRatio - Documentation

**Indicator:** Body Ratio
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

Body Ratio measures candle conviction - how much of the candle's range is "body" versus "wick." This is the simplest indicator in the suite, independent of volume, providing pure price action analysis.

**The Core Insight:**
- Large body = conviction (one side dominated)
- Small body = indecision (neither side won)
- Specific wick patterns = reversal signals

### The Body Ratio Scale

| Body Ratio | Classification | Meaning |
|------------|----------------|---------|
| 70%+ | Strong | Full conviction, one side dominated |
| 30-70% | Normal | Typical candle, moderate conviction |
| 5-30% | Weak/Indecision | Neither side won, potential reversal |
| <5% | Doji | Complete indecision, strong reversal signal |

### Primary Use Cases

#### Conviction Confirmation
- Strong body ratio + momentum = high confidence continuation
- Weak body ratio at key level = potential reversal
- Doji after trend = exhaustion warning

#### Pattern Recognition
The indicator automatically detects:
- **Doji:** Body < 5% of range
- **Hammer:** Small body at top, long lower wick (>60%)
- **Shooting Star:** Small body at bottom, long upper wick (>60%)
- **Spinning Top:** Small body with wicks on both sides

#### Entry Quality Filter
- Take entries on strong conviction candles
- Avoid entries on doji/indecision candles
- Use weak candles as reversal confirmation at zones

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Tall Green Column | Strong bullish conviction |
| Tall Red Column | Strong bearish conviction |
| Short Orange Column | Weak/indecision candle |
| Short Yellow Column | Doji detected |
| Arrow Up (bottom) | Strong bullish candle |
| Arrow Down (top) | Strong bearish candle |
| X Cross (top) | Doji candle |
| Diamond Up (bottom) | Hammer pattern |
| Diamond Down (top) | Shooting star pattern |

### Candle Patterns Detected

**Doji (Body < 5%):**
```
    |
   ─┼─
    |
Complete indecision. Strong reversal signal when at key levels.
```

**Hammer (Body < 30%, Lower Wick > 60%):**
```
    ─
    |
    |
    |
Bullish reversal. Sellers pushed down but buyers recovered.
```

**Shooting Star (Body < 30%, Upper Wick > 60%):**
```
    |
    |
    |
    ─
Bearish reversal. Buyers pushed up but sellers recovered.
```

**Spinning Top (Body < 30%, Balanced Wicks):**
```
    |
   ─┼─
    |
Indecision. Neither side dominated. Wait for confirmation.
```

### Trading Signals at EPCH Zones

**At Support Zones:**
```
Hammer or Doji appears
  = Sellers losing control
  = Potential EPCH2 long setup
  = Wait for confirmation candle
```

**At Resistance Zones:**
```
Shooting Star or Doji appears
  = Buyers losing control
  = Potential EPCH4 short setup
  = Wait for confirmation candle
```

**Trend Continuation:**
```
Strong body candle in trend direction
  = Conviction move
  = Hold position
  = Not a reversal signal
```

### Recommended Settings

| Parameter | Default | Aggressive | Conservative |
|-----------|---------|------------|--------------|
| Strong Threshold | 70% | 65% | 75% |
| Weak Threshold | 30% | 35% | 25% |
| Doji Threshold | 5% | 8% | 3% |

### Info Panel Interpretation

| Field | Meaning |
|-------|---------|
| Body% | Body as percentage of total range |
| Type | Classification (STRONG, WEAK, DOJI, HAMMER, etc.) |
| Wicks | Upper and lower wick percentages |
| Signal | CONVICTION, INDECISION, REVERSAL, or — |

---

## 2. TECHNICAL BASIS

### Why Body Ratio Matters

Body ratio is the purest measure of candle conviction:
- It's independent of volume (unlike Momentum/Absorption)
- It's independent of ATR (works on any instrument)
- It captures the fundamental battle between buyers and sellers

### The Math Behind Conviction

```
Body Ratio = Body Size / Total Range
           = |Close - Open| / (High - Low)
```

A high ratio means price closed near its extreme - one side dominated.
A low ratio means price closed near where it opened - no clear winner.

### Wick Analysis

Wicks represent rejected price movement:

```
Upper Wick = High - Max(Open, Close)
  → Buyers pushed up but got rejected

Lower Wick = Min(Open, Close) - Low
  → Sellers pushed down but got rejected
```

The location and size of wicks tells you who tried and failed.

### Pattern Recognition Logic

**Hammer Detection:**
```
is_hammer = body_ratio <= 0.30
        AND lower_wick_ratio > 0.60
        AND upper_wick_ratio < 0.10
```

**Shooting Star Detection:**
```
is_shooting_star = body_ratio <= 0.30
               AND upper_wick_ratio > 0.60
               AND lower_wick_ratio < 0.10
```

**Doji Detection:**
```
is_doji = body_ratio <= 0.05
```

### Volume Independence

Unlike Momentum and Absorption, Body Ratio doesn't require volume. This makes it:
- Useful on instruments with unreliable volume
- A pure price action confirmation tool
- Complementary to volume-based indicators

Combine with RVOL for best results:
- High RVOL + Strong Body = High conviction signal
- High RVOL + Weak Body = Absorption (see EPCH_05)
- Low RVOL + Any Body = Likely noise

---

## 3. CALCULATIONS

### Step-by-Step Calculation

#### Step 1: Calculate Components
```
body = ABS(close - open)
range_size = high - low
```

#### Step 2: Body Ratio
```
IF range_size > 0:
    body_ratio = body / range_size
ELSE:
    body_ratio = 0.5    // Handle flat candles
```

#### Step 3: Classification
```
is_strong = body_ratio >= 0.70
is_weak   = body_ratio <= 0.30
is_doji   = body_ratio <= 0.05
is_normal = NOT is_strong AND NOT is_weak
```

#### Step 4: Direction
```
is_bullish = close > open
is_bearish = close < open

is_strong_bull = is_strong AND is_bullish
is_strong_bear = is_strong AND is_bearish
```

#### Step 5: Wick Ratios
```
upper_wick = high - MAX(open, close)
lower_wick = MIN(open, close) - low

upper_wick_ratio = upper_wick / range_size
lower_wick_ratio = lower_wick / range_size
```

#### Step 6: Pattern Detection
```
is_hammer = is_weak
        AND lower_wick_ratio > 0.60
        AND upper_wick_ratio < 0.10

is_shooting_star = is_weak
               AND upper_wick_ratio > 0.60
               AND lower_wick_ratio < 0.10

is_spinning_top = is_weak
              AND NOT is_hammer
              AND NOT is_shooting_star
              AND NOT is_doji
```

### Numerical Examples

**Example 1: Strong Bullish Candle**
```
Open:  100.00
High:  101.00
Low:    99.80
Close: 100.90

body = |100.90 - 100.00| = 0.90
range = 101.00 - 99.80 = 1.20
body_ratio = 0.90 / 1.20 = 0.75 (75%)

Result: STRONG BULLISH (75% > 70%)
```

**Example 2: Hammer Pattern**
```
Open:  100.50
High:  100.60
Low:    99.50
Close: 100.55

body = |100.55 - 100.50| = 0.05
range = 100.60 - 99.50 = 1.10
body_ratio = 0.05 / 1.10 = 0.045 (4.5%)

upper_wick = 100.60 - 100.55 = 0.05 (4.5%)
lower_wick = 100.50 - 99.50 = 1.00 (91%)

Result: HAMMER (body < 30%, lower wick > 60%, upper < 10%)
```

**Example 3: Doji**
```
Open:  100.00
High:  100.50
Low:    99.50
Close: 100.02

body = |100.02 - 100.00| = 0.02
range = 100.50 - 99.50 = 1.00
body_ratio = 0.02 / 1.00 = 0.02 (2%)

Result: DOJI (2% < 5%)
```

### Color Assignment Logic

```
IF is_doji:
    color = YELLOW
ELSE IF is_strong_bull:
    color = BRIGHT_GREEN
ELSE IF is_strong_bear:
    color = BRIGHT_RED
ELSE IF is_weak:
    color = ORANGE
ELSE IF is_bullish:
    color = FADED_GREEN
ELSE IF is_bearish:
    color = FADED_RED
ELSE:
    color = GRAY
```

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_06_BodyRatio.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - Standard suite colors                     |
| - Additional: indecision (orange)           |
+---------------------------------------------+
| Input Group Constants                       |
+---------------------------------------------+
| Input Definitions                           |
| - Thresholds (strong, weak, doji)           |
| - Visual toggles                            |
| - Alert toggles                             |
+---------------------------------------------+
| Core Calculations                           |
| - Body and range measurements               |
| - Body ratio                                |
| - Classification (strong/weak/doji)         |
| - Direction detection                       |
| - Wick analysis                             |
| - Pattern detection (hammer, star, etc.)    |
+---------------------------------------------+
| Visual Outputs (overlay=false)              |
| - plot (body ratio histogram)               |
| - hline (threshold levels)                  |
| - plotshape (pattern markers)               |
| - barcolor (optional candle coloring)       |
+---------------------------------------------+
| Alert Conditions                            |
| - Strong bull/bear                          |
| - Indecision, doji                          |
| - Hammer, shooting star                     |
+---------------------------------------------+
| Info Panel (Table)                          |
| - Body%, Type, Wicks, Signal                |
+---------------------------------------------+
| Export Plots (display=none)                 |
| - Body ratio, flags, pattern codes          |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `math.abs(value)` | Absolute value for body size |
| `math.max(a, b)` | Max of open/close for upper wick |
| `math.min(a, b)` | Min of open/close for lower wick |
| `plot(..., style=plot.style_columns)` | Histogram display |
| `plotshape()` | Pattern markers |
| `hline()` | Threshold reference lines |

### Modification Guide

#### To Adjust Pattern Sensitivity

**More Pattern Detection:**
```pinescript
weak_threshold = 0.35      // More candles qualify as weak
doji_threshold = 0.08      // More dojis detected
// In hammer/star detection:
lower_wick_min = 0.55      // Lower requirement for hammer
upper_wick_min = 0.55      // Lower requirement for star
```

**Stricter Pattern Detection:**
```pinescript
weak_threshold = 0.25
doji_threshold = 0.03
lower_wick_min = 0.70
upper_wick_min = 0.70
```

#### To Add Engulfing Pattern Detection
```pinescript
// Bullish engulfing: current body engulfs previous body
prev_body = math.abs(close[1] - open[1])
curr_body = math.abs(close - open)

bullish_engulfing = is_bearish[1] and is_bullish
                and open <= close[1] and close >= open[1]
                and curr_body > prev_body

bearish_engulfing = is_bullish[1] and is_bearish
                and open >= close[1] and close <= open[1]
                and curr_body > prev_body

plotshape(bullish_engulfing, title="Bullish Engulfing",
          location=location.belowbar, style=shape.labelup,
          color=color_bull_strong, text="BE", size=size.tiny)
```

#### To Add Morning/Evening Star Detection
```pinescript
// Morning Star (3-bar pattern)
is_morning_star = is_strong_bear[2]           // Bar 1: Strong bearish
              and is_weak[1]                   // Bar 2: Indecision
              and is_strong_bull               // Bar 3: Strong bullish
              and close > (open[2] + close[2]) / 2  // Closes above midpoint of Bar 1

// Evening Star (opposite)
is_evening_star = is_strong_bull[2]
              and is_weak[1]
              and is_strong_bear
              and close < (open[2] + close[2]) / 2
```

#### To Add Trend Context
Consider body ratio in context of recent candles:
```pinescript
avg_body_ratio = ta.sma(body_ratio, 10)
relative_strength = body_ratio / avg_body_ratio

// Strong relative to recent candles
is_relatively_strong = relative_strength > 1.5
```

#### To Integrate with RVOL
Combine body ratio with volume for weighted signals:
```pinescript
// External RVOL (would need EPCH_03 on chart)
// Or calculate inline:
avg_volume = ta.sma(volume, 20)
rvol = volume / avg_volume

// Combined signal
high_conviction = is_strong and rvol >= 1.5
low_conviction_warning = is_weak and rvol >= 2.0  // Absorption-like
```

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] Body ratio calculates correctly (verify: body / range)
- [ ] Handles zero-range candles without error
- [ ] Strong/weak/doji classification matches thresholds
- [ ] Hammer detection works (small body, long lower wick)
- [ ] Shooting star detection works (small body, long upper wick)
- [ ] Colors align with direction and conviction
- [ ] Histogram displays properly
- [ ] Markers appear at correct locations
- [ ] Info panel shows all four rows
- [ ] Alerts fire correctly for each pattern
- [ ] Works on M1, M5, M15, H1 timeframes

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Too many dojis | Threshold too high | Lower to 0.03 |
| No hammers detected | Wick requirement too strict | Lower to 0.55 |
| Colors conflict with other indicators | Multiple barcolor() active | Disable color_candles |
| Histogram too small | Low body ratios | This is correct; values are 0-1 |
| Markers overlapping | Both hammer and doji triggered | Logic should prevent this |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `body` | float | Absolute candle body size |
| `range_size` | float | High - Low |
| `body_ratio` | float | body / range_size (0 to 1) |
| `upper_wick` | float | Upper wick size |
| `lower_wick` | float | Lower wick size |
| `upper_wick_ratio` | float | Upper wick as % of range |
| `lower_wick_ratio` | float | Lower wick as % of range |
| `is_strong` | bool | body_ratio >= 0.70 |
| `is_weak` | bool | body_ratio <= 0.30 |
| `is_doji` | bool | body_ratio <= 0.05 |
| `is_normal` | bool | Between weak and strong |
| `is_bullish` | bool | close > open |
| `is_bearish` | bool | close < open |
| `is_strong_bull` | bool | Strong + bullish |
| `is_strong_bear` | bool | Strong + bearish |
| `is_hammer` | bool | Hammer pattern detected |
| `is_shooting_star` | bool | Shooting star detected |
| `is_spinning_top` | bool | Spinning top detected |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `strong_threshold` | float | 0.70 | 0.5-0.9 | Strong conviction threshold |
| `weak_threshold` | float | 0.30 | 0.1-0.5 | Indecision threshold |
| `doji_threshold` | float | 0.05 | 0.01-0.15 | Doji detection threshold |
| `show_histogram` | bool | true | - | Show body ratio histogram |
| `show_markers` | bool | true | - | Show pattern markers |
| `color_candles` | bool | false | - | Color candles by conviction |
| `show_panel` | bool | true | - | Show info panel |
| `alert_strong` | bool | false | - | Alert on strong conviction |
| `alert_weak` | bool | true | - | Alert on indecision |
| `alert_doji` | bool | true | - | Alert on doji |

### Relationship to Other EPCH Indicators

| Indicator | Relationship |
|-----------|--------------|
| EPCH_01 (Rolling Delta) | Body ratio confirms delta direction conviction |
| EPCH_02 (Delta ROC) | Weak body + divergence = stronger reversal signal |
| EPCH_03 (RVOL) | RVOL + body ratio = conviction with participation |
| EPCH_04 (Momentum) | Momentum requires high body ratio implicitly |
| EPCH_05 (Absorption) | Absorption requires low body ratio explicitly |

### Independent Nature

Body Ratio is the only purely price-action indicator in the suite:
- No volume dependency
- No ATR dependency
- Works on any instrument with OHLC data
- Simplest calculation in the suite

Use it as a confirmation layer for volume-based signals or as a standalone tool when volume data is unreliable.

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
