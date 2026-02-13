# EPCH_04_Momentum - Documentation

**Indicator:** Momentum Detector
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

Momentum detects candles where high volume SUCCEEDS in moving price. This efficiency signals that orders are pushing through with minimal resistance - continuation is likely.

**The Core Insight:**
- High volume + large move = Momentum (continuation)
- High volume + small move = Absorption (reversal)

When you see a bright green or red candle, the market is moving with conviction. Someone is aggressively pushing price, and there's not enough opposing flow to stop them.

### The Momentum Formula

```
Momentum = Large Price Move + High Volume
         = (Body >= 0.75 ATR) + (RVOL >= 1.5x)
```

Both conditions must be met. Large move without volume = fake move. High volume without movement = absorption.

### Primary Use Cases

#### Zone Failure Detection (EPCH1/EPCH3)
Momentum is the PRIMARY zone failure signal:
- **At Support (EPCH1):** Bright red candle = sellers broke through = zone FAILED = bearish continuation
- **At Resistance (EPCH3):** Bright green candle = buyers broke through = zone FAILED = bullish continuation

#### Trend Confirmation
- Multiple momentum candles in same direction = strong trend
- Momentum in direction of your trade = confirmation to hold
- Momentum against your trade = warning to exit

#### Breakout Validation
- Breakout with momentum = likely real
- Breakout without momentum = likely fake

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Bright Green Candle (#00FF00) | Bullish momentum - continuation UP |
| Bright Red Candle (#FF0000) | Bearish momentum - continuation DOWN |
| Normal Candle | No momentum (either low volume or small move) |
| Triangle Up (below bar) | Optional arrow for bullish momentum |
| Triangle Down (above bar) | Optional arrow for bearish momentum |

### Momentum vs Absorption: The Key Distinction

| Characteristic | Momentum | Absorption |
|----------------|----------|------------|
| Volume | High (1.5x+) | High (2.0x+) |
| Body Size | Large (>0.75 ATR) | Small (<0.30 ATR) |
| Wicks | Minimal | Prominent |
| Signal | CONTINUATION | REVERSAL |
| Candle Color | Bright Green/Red | Gold/Orange |
| Zone Meaning | Zone FAILS | Zone HOLDS |
| EPCH Trade | EPCH1/EPCH3 | EPCH2/EPCH4 |

### Trading Signals at EPCH Zones

**At Support Zones:**
```
Bright RED candle appears
  = Bearish momentum
  = Sellers broke through support
  = Zone FAILED (EPCH1)
  = DO NOT go long here
  = Consider short or wait for new zone
```

**At Resistance Zones:**
```
Bright GREEN candle appears
  = Bullish momentum
  = Buyers broke through resistance
  = Zone FAILED (EPCH3)
  = DO NOT go short here
  = Consider long or wait for new zone
```

### Recommended Settings

| Parameter | Scalping (M1) | Day Trading (M5) | Swing (M15) |
|-----------|---------------|------------------|-------------|
| ATR Length | 14 | 14 | 20 |
| RVOL Length | 20 | 20 | 30 |
| Move Threshold | 0.75 | 0.75 | 0.80 |
| RVOL Threshold | 1.5 | 1.5 | 1.3 |
| Use Body | true | true | true |

### Info Panel Interpretation

| Field | Meaning | Signal Threshold |
|-------|---------|------------------|
| Move | Body size in ATR units | >= 0.75 ATR (yellow) |
| RVOL | Relative volume | >= 1.5x (yellow) |
| ATR | Current ATR value | Reference only |
| Signal | Current signal status | BULL MOM / BEAR MOM |

---

## 2. TECHNICAL BASIS

### The Mechanics of Momentum

When a market participant places a large order that moves price efficiently:

```
Large buy order hits the market
  → Sweeps through ask levels
  → Price moves up significantly
  → Full-bodied green candle
  → Little resistance encountered
  → CONTINUATION signal
```

This is the opposite of absorption, where orders get matched without moving price.

### Why Momentum Predicts Continuation

1. **Path of Least Resistance:** If price moved easily, the path ahead is clear
2. **Order Flow Dominance:** One side clearly overwhelmed the other
3. **Institutional Aggression:** Large players are pushing in a direction
4. **Breakout Confirmation:** Volume validates the price movement

### The Two-Criteria Filter

**Criterion 1: Large Body (Move Threshold)**
- Uses ATR normalization for cross-instrument comparison
- 0.75 ATR means body is 75% of typical range
- Filters out normal candles and dojis

**Criterion 2: High Volume (RVOL Threshold)**
- Compares current volume to 20-bar average
- 1.5x means 50% above average
- Filters out low-volume moves (gaps, thin markets)

### Body vs Range Setting

**Use Body (Default: true):**
- Measures close-open distance
- Ignores wicks
- Better for pure momentum detection

**Use Range (false):**
- Measures high-low distance
- Includes wicks
- Detects volatile candles even with wicks

### Streak Detection

The indicator tracks consecutive momentum candles:
```
bull_streak: Count of consecutive bullish momentum bars
bear_streak: Count of consecutive bearish momentum bars
```

Multiple momentum bars in sequence = strong directional conviction.

---

## 3. CALCULATIONS

### Step-by-Step Calculation

#### Step 1: ATR Calculation
```
IF atr_source == "Auto":
    atr_value = ATR(atr_length)    // Default: 14-bar ATR
ELSE:
    atr_value = manual_atr          // User-defined fixed value
```

#### Step 2: Move Size
```
IF use_body:
    move_size = ABS(close - open)   // Body only
ELSE:
    move_size = high - low          // Full range
```

#### Step 3: Move Ratio
```
move_ratio = move_size / atr_value
```

#### Step 4: RVOL
```
avg_volume = SMA(volume, rvol_length)  // Default: 20-bar
rvol = volume / avg_volume
```

#### Step 5: Momentum Detection
```
is_large_move  = move_ratio >= move_threshold   // Default: >= 0.75
is_high_volume = rvol >= rvol_threshold         // Default: >= 1.5

is_momentum = is_large_move AND is_high_volume
```

#### Step 6: Direction
```
is_bull_momentum = is_momentum AND close > open
is_bear_momentum = is_momentum AND close < open
```

#### Step 7: Strength Score
```
momentum_strength = is_momentum ? (move_ratio * rvol) : 0
```

### Numerical Example

Given this candle data:
```
Open:   100.00
High:   101.20
Low:     99.90
Close:  101.00
Volume: 35,000
ATR(14): 0.80
Avg Volume(20): 20,000
```

**Calculations:**
```
move_size (body) = |101.00 - 100.00| = 1.00
move_ratio = 1.00 / 0.80 = 1.25    ✓ (>= 0.75)
rvol = 35,000 / 20,000 = 1.75x     ✓ (>= 1.5)

is_momentum = TRUE (both criteria met)
close > open → is_bull_momentum = TRUE

momentum_strength = 1.25 * 1.75 = 2.19
```

**Result:** Bullish momentum candle detected. Candle will be colored bright green.

### Color Assignment Logic

```
IF is_bull_momentum:
    color = BRIGHT_GREEN (#00FF00)
ELSE IF is_bear_momentum:
    color = BRIGHT_RED (#FF0000)
ELSE:
    color = na (no coloring)
```

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_04_Momentum.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - Standard suite colors                     |
| - Momentum-specific: bright green, red      |
+---------------------------------------------+
| Input Group Constants                       |
+---------------------------------------------+
| Input Definitions                           |
| - ATR settings (length, source, manual)     |
| - RVOL settings (length)                    |
| - Thresholds (move, rvol)                   |
| - use_body toggle                           |
| - Visual and alert toggles                  |
+---------------------------------------------+
| Core Calculations                           |
| - ATR (auto or manual)                      |
| - Move size (body or range)                 |
| - Move ratio                                |
| - RVOL                                      |
| - Momentum detection (2 criteria)           |
| - Direction detection                       |
| - Streak counting                           |
+---------------------------------------------+
| Visual Outputs (overlay=true)               |
| - barcolor (green/red candles)              |
| - plotshape (optional arrows)               |
+---------------------------------------------+
| Alert Conditions                            |
| - Bullish momentum                          |
| - Bearish momentum                          |
| - Any momentum                              |
| - Streak alerts                             |
+---------------------------------------------+
| Info Panel (Table)                          |
| - Move, RVOL, ATR, Signal                   |
+---------------------------------------------+
| Export Plots (display=none)                 |
| - Momentum flags for other indicators       |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `ta.atr(length)` | Average True Range calculation |
| `ta.sma(source, length)` | Simple moving average for RVOL |
| `math.abs(value)` | Absolute value for body size |
| `barcolor(color)` | Colors price candles |
| `plotshape()` | Optional arrow markers |

### Modification Guide

#### To Adjust Momentum Sensitivity

**More Signals (Catch smaller moves):**
```pinescript
move_threshold = 0.50   // Lower move requirement
rvol_threshold = 1.3    // Lower volume requirement
```

**Fewer Signals (Only strong moves):**
```pinescript
move_threshold = 1.0    // Require full ATR move
rvol_threshold = 2.0    // Require double volume
```

#### To Add Momentum Intensity Gradient
Color intensity based on strength:
```pinescript
// Calculate intensity (0-100)
intensity = math.min(100, momentum_strength * 30)

// Apply to color
bull_color = color.new(#00FF00, 100 - intensity)
bear_color = color.new(#FF0000, 100 - intensity)

barcolor(is_bull_momentum ? bull_color :
         is_bear_momentum ? bear_color : na)
```

#### To Add Higher Timeframe Confirmation
Check if momentum aligns with higher timeframe:
```pinescript
htf = input.timeframe("15", title="Higher Timeframe")
htf_close = request.security(syminfo.tickerid, htf, close)
htf_open = request.security(syminfo.tickerid, htf, open)
htf_bullish = htf_close > htf_open

// Stronger signal when aligned
aligned_bull = is_bull_momentum and htf_bullish
aligned_bear = is_bear_momentum and not htf_bullish
```

#### To Add Exhaustion Detection
Detect potential exhaustion after momentum streak:
```pinescript
// After 3+ momentum bars, watch for failure
bull_exhaustion = bull_streak[1] >= 3 and not is_bull_momentum
bear_exhaustion = bear_streak[1] >= 3 and not is_bear_momentum

plotshape(bull_exhaustion, title="Bull Exhaustion",
          location=location.abovebar, style=shape.xcross,
          color=color.orange, size=size.tiny)
```

#### To Integrate with EPCH_03 RVOL
Instead of calculating RVOL internally, reference EPCH_03:
```pinescript
// Note: Would require EPCH_03 to be on chart
// This is a conceptual example
external_rvol = request.security(syminfo.tickerid, timeframe.period, close)
```

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] Momentum fires only when BOTH criteria met
- [ ] Large move alone does NOT trigger
- [ ] High volume alone does NOT trigger
- [ ] Bright green appears on bullish momentum
- [ ] Bright red appears on bearish momentum
- [ ] Manual ATR override works
- [ ] Body vs Range toggle changes behavior
- [ ] Arrows appear correctly when enabled
- [ ] Streak counting increments properly
- [ ] Info panel displays all four rows
- [ ] Works on different instruments
- [ ] Candle coloring doesn't conflict with Absorption (load order)

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| No momentum signals | Thresholds too strict | Lower move to 0.60, RVOL to 1.3 |
| Too many signals | Thresholds too loose | Raise move to 0.90, RVOL to 1.8 |
| Colors overwritten | Absorption loaded after | Load Momentum after Absorption |
| Wrong ATR scale | Different instrument | Use Manual ATR for consistency |
| Streaks not counting | Logic error | Check var declarations |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `atr_value` | float | ATR (auto or manual) |
| `move_size` | float | Body or range size |
| `move_ratio` | float | move_size / atr_value |
| `rvol` | float | volume / avg_volume |
| `is_large_move` | bool | move_ratio >= threshold |
| `is_high_volume` | bool | rvol >= threshold |
| `is_momentum` | bool | Both criteria met |
| `is_bull_momentum` | bool | Momentum + bullish |
| `is_bear_momentum` | bool | Momentum + bearish |
| `momentum_strength` | float | move_ratio * rvol |
| `bull_streak` | int | Consecutive bull momentum bars |
| `bear_streak` | int | Consecutive bear momentum bars |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `atr_length` | int | 14 | 5-50 | ATR calculation period |
| `atr_source` | string | "Auto" | Auto/Manual | ATR method |
| `manual_atr` | float | 0.50 | 0.01-100 | Fixed ATR value |
| `rvol_length` | int | 20 | 5-100 | RVOL lookback |
| `move_threshold` | float | 0.75 | 0.3-2.0 | Min move for momentum |
| `rvol_threshold` | float | 1.5 | 1.1-3.0 | Min RVOL for momentum |
| `use_body` | bool | true | - | Body vs range |
| `show_arrows` | bool | false | - | Show arrow markers |
| `show_panel` | bool | true | - | Show info panel |
| `alert_bull_momentum` | bool | true | - | Bullish alerts |
| `alert_bear_momentum` | bool | true | - | Bearish alerts |

### Relationship to Other EPCH Indicators

| Indicator | Relationship |
|-----------|--------------|
| EPCH_01 (Rolling Delta) | Momentum + delta alignment = stronger signal |
| EPCH_02 (Delta ROC) | ROC confirms momentum direction |
| EPCH_03 (RVOL) | Shares RVOL calculation |
| EPCH_05 (Absorption) | OPPOSITE signal - same barcolor(), load order matters |
| EPCH_06 (Body Ratio) | Momentum implies high body ratio |

### Visual Priority Note

Both Momentum (EPCH_04) and Absorption (EPCH_05) use `barcolor()`. TradingView only allows one `barcolor()` per candle.

**Recommended load order:**
1. EPCH_04 Momentum (load first)
2. EPCH_05 Absorption (load second - takes priority)

Absorption overriding Momentum is correct for EPCH trading because:
- Momentum at zones = zone failure = don't trade
- Absorption at zones = zone holds = trade opportunity

You want to SEE the absorption signal when it matters.

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
