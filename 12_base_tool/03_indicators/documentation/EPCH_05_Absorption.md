# EPCH_05_Absorption - Documentation

**Indicator:** Absorption Detector
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

Absorption detects candles where high volume FAILS to move price. This inefficiency signals that orders are being absorbed/matched by opposing flow without pushing price through.

**The Core Insight:**
- High volume + large move = Momentum (continuation)
- High volume + small move = Absorption (reversal)

When you see a high-volume candle that barely moves price, someone is absorbing all that selling (or buying) pressure. That "someone" is typically institutional - and they're building a position in the opposite direction.

### Primary Use Cases

#### Reversal Detection at Key Levels
Absorption is the primary reversal signal in the EPCH system:
- **At Support (EPCH2):** Gold candle = buyers absorbing sellers = zone holds = GO LONG
- **At Resistance (EPCH4):** Dark orange candle = sellers absorbing buyers = zone holds = GO SHORT

#### Failed Breakout Identification
When price attempts to break a level with high volume but the candle is small with wicks:
- The breakout is being absorbed
- High probability of reversal back into range

#### Institutional Accumulation/Distribution
Absorption often marks where large players are:
- **Accumulating:** Absorbing selling pressure at lows (gold candles)
- **Distributing:** Absorbing buying pressure at highs (dark orange candles)

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Gold Candle (#FFD700) | Absorption at recent LOW - buyers absorbing, bullish reversal |
| Dark Orange Candle (#FF8C00) | Absorption at recent HIGH - sellers absorbing, bearish reversal |
| Orange Candle (#FFA500) | Absorption detected but location unclear |
| Normal Candle | No absorption (either low volume or price moved efficiently) |
| Diamond Below (gold) | Optional marker for bullish absorption |
| Diamond Above (orange) | Optional marker for bearish absorption |

### The Three Absorption Criteria

All THREE must be met for absorption detection:

1. **Small Move (Body < 0.30 ATR)**
   - Price barely moved despite the volume
   - Body size relative to ATR, not absolute price

2. **High Volume (RVOL > 2.0x)**
   - Significantly above average volume
   - Institutional-level participation

3. **Prominent Wicks (Body < 35% of Range)**
   - Wicks show rejected price movement
   - Small body = indecision, large wicks = rejection

### Trading Signals at EPCH Zones

**At Support Zones (Looking for EPCH2 Long):**
```
Price enters your support zone
  + Gold candle appears
  = Zone is holding
  = Buyers absorbing sellers
  = HIGH PROBABILITY LONG ENTRY
```

**At Resistance Zones (Looking for EPCH4 Short):**
```
Price enters your resistance zone
  + Dark orange candle appears
  = Zone is holding
  = Sellers absorbing buyers
  = HIGH PROBABILITY SHORT ENTRY
```

### Absorption vs Momentum: The Key Distinction

| Characteristic | Absorption | Momentum |
|----------------|------------|----------|
| Volume | High (2x+) | High (1.5x+) |
| Body Size | Small (<0.30 ATR) | Large (>0.75 ATR) |
| Wicks | Prominent | Minimal |
| Body Ratio | <35% | >70% |
| Signal | REVERSAL | CONTINUATION |
| Candle Color | Gold/Orange | Bright Green/Red |
| Zone Meaning | Zone HOLDS | Zone FAILS |

### Recommended Settings

| Parameter | Scalping (M1) | Day Trading (M5) | Swing (M15) |
|-----------|---------------|------------------|-------------|
| ATR Length | 14 | 14 | 20 |
| RVOL Length | 20 | 20 | 30 |
| Move Threshold | 0.30 | 0.30 | 0.35 |
| RVOL Threshold | 2.0 | 2.0 | 1.8 |
| Body Ratio Max | 0.35 | 0.35 | 0.40 |
| Location Lookback | 10 | 15 | 20 |

### Info Panel Interpretation

| Field | Meaning | Signal Threshold |
|-------|---------|------------------|
| Body | Body size in ATR units | < 0.30 ATR (yellow) |
| RVOL | Relative volume | > 2.0x (yellow) |
| Body% | Body as % of range | < 35% (yellow) |
| Location | Position vs recent H/L | @ HIGH or @ LOW |
| Signal | Current signal status | BUY ABS / SELL ABS / ABSORB |

---

## 2. TECHNICAL BASIS

### The Mechanics of Absorption

When a market participant places a large order, two outcomes are possible:

**Scenario A: Order Moves Price (Momentum)**
```
Large buy order hits the market
  → Sweeps through ask levels
  → Price moves up significantly
  → Full-bodied green candle
  → CONTINUATION signal
```

**Scenario B: Order Gets Absorbed**
```
Large buy order hits the market
  → Large seller matches all buying
  → Price barely moves
  → Small body, large wicks
  → REVERSAL signal
```

Absorption means there's hidden liquidity opposing the visible order flow.

### Why Absorption Predicts Reversals

1. **Information Asymmetry:** The absorbing party often has better information
2. **Size Imbalance:** Institutional players can absorb retail flow all day
3. **Position Building:** Absorption often marks accumulation/distribution zones
4. **Failed Aggression:** Aggressive buyers/sellers failed to move price = exhaustion

### The Three-Criteria Filter

Each criterion filters out false signals:

**Criterion 1: Small Body (Move Threshold)**
- Uses ATR normalization for cross-instrument comparison
- 0.30 ATR means body is less than 30% of typical range
- Filters out normal consolidation candles

**Criterion 2: High Volume (RVOL Threshold)**
- Compares current volume to 20-bar average
- 2.0x means double the average volume
- Filters out low-volume dojis and inside bars

**Criterion 3: Prominent Wicks (Body Ratio)**
- Body / Range must be < 35%
- Large wicks = price was rejected
- Filters out small-range, small-body candles

### Location Context

Absorption at any price level is notable, but absorption at extremes is actionable:

**At Recent High:**
- Price tried to break higher
- Sellers absorbed all buying
- Bearish reversal likely

**At Recent Low:**
- Price tried to break lower
- Buyers absorbed all selling
- Bullish reversal likely

**Mid-Range:**
- Absorption detected but direction unclear
- Wait for additional confirmation

### Wick Analysis for Direction

Even when location is mid-range, wick structure provides directional bias:

```
Upper Wick > Lower Wick:
  → Price was rejected from highs
  → Bearish absorption

Lower Wick > Upper Wick:
  → Price was rejected from lows
  → Bullish absorption
```

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

#### Step 2: Candle Measurements
```
body_size  = ABS(close - open)
range_size = high - low
upper_wick = high - MAX(open, close)
lower_wick = MIN(open, close) - low
```

#### Step 3: Ratios
```
move_ratio = body_size / atr_value    // Body relative to ATR
body_ratio = body_size / range_size   // Body relative to candle range
```

#### Step 4: RVOL
```
avg_volume = SMA(volume, rvol_length)  // Default: 20-bar
rvol = volume / avg_volume
```

#### Step 5: Absorption Detection
```
is_small_move  = move_ratio <= move_threshold   // Default: <= 0.30
is_high_volume = rvol >= rvol_threshold         // Default: >= 2.0
has_wicks      = body_ratio <= body_ratio_max   // Default: <= 0.35

is_absorption = is_small_move AND is_high_volume AND has_wicks
```

#### Step 6: Location Context
```
recent_high = HIGHEST(high, location_lookback)  // Default: 10 bars
recent_low  = LOWEST(low, location_lookback)

at_high = high >= recent_high * (1 - location_tolerance)  // Within 0.2%
at_low  = low <= recent_low * (1 + location_tolerance)

absorption_at_high = is_absorption AND at_high
absorption_at_low  = is_absorption AND at_low
```

#### Step 7: Wick Direction
```
bullish_absorption = is_absorption AND lower_wick > upper_wick
bearish_absorption = is_absorption AND upper_wick > lower_wick
```

### Numerical Example

Given this candle data:
```
Open:   100.00
High:   100.50
Low:     99.50
Close:  100.10
Volume: 50,000
ATR(14): 0.80
Avg Volume(20): 20,000
Recent High(10): 100.60
Recent Low(10):   99.40
```

**Calculations:**
```
body_size  = |100.10 - 100.00| = 0.10
range_size = 100.50 - 99.50 = 1.00
upper_wick = 100.50 - 100.10 = 0.40
lower_wick = 100.00 - 99.50 = 0.50

move_ratio = 0.10 / 0.80 = 0.125  ✓ (< 0.30)
body_ratio = 0.10 / 1.00 = 0.10   ✓ (< 0.35)
rvol = 50,000 / 20,000 = 2.5x     ✓ (> 2.0)

is_absorption = TRUE (all three criteria met)

at_high = 100.50 >= 100.60 * 0.998 = 100.40? → TRUE
at_low  = 99.50 <= 99.40 * 1.002 = 99.60?  → TRUE

absorption_at_high = TRUE (price at recent high)
lower_wick (0.50) > upper_wick (0.40) → bullish_absorption = TRUE
```

**Result:** Absorption detected at high, but wick analysis suggests buying pressure (bullish). This is a conflicting signal - likely consolidation rather than clear reversal.

### Color Assignment Logic

```
IF absorption_at_low:
    color = GOLD (#FFD700)           // Bullish reversal
ELSE IF absorption_at_high:
    color = DARK_ORANGE (#FF8C00)    // Bearish reversal
ELSE IF is_absorption:
    color = ORANGE (#FFA500)         // Absorption, direction unclear
ELSE:
    color = na (no coloring)
```

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_05_Absorption.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - Standard suite colors                     |
| - Absorption-specific: gold, dark orange,   |
|   orange                                    |
+---------------------------------------------+
| Input Group Constants                       |
| - GRP_PARAMS, GRP_THRESH, GRP_VISUAL,       |
|   GRP_ALERTS                                |
+---------------------------------------------+
| Input Definitions                           |
| - ATR settings (length, source, manual)     |
| - RVOL settings (length)                    |
| - Thresholds (move, rvol, body ratio)       |
| - Location settings (lookback, tolerance)   |
| - Visual and alert toggles                  |
+---------------------------------------------+
| Core Calculations                           |
| - ATR (auto or manual)                      |
| - Body/range measurements                   |
| - Move ratio, body ratio                    |
| - RVOL                                      |
| - Absorption detection (3 criteria)         |
| - Location context (high/low)               |
| - Wick analysis                             |
+---------------------------------------------+
| Visual Outputs (overlay=true)               |
| - barcolor (gold/orange candles)            |
| - plotshape (optional diamond markers)      |
+---------------------------------------------+
| Alert Conditions                            |
| - Any absorption                            |
| - Absorption at high                        |
| - Absorption at low                         |
| - Absorption at any extreme                 |
+---------------------------------------------+
| Info Panel (Table)                          |
| - Body (ATR), RVOL, Body%, Location, Signal |
+---------------------------------------------+
| Export Plots (display=none)                 |
| - Absorption flags for other indicators     |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `ta.atr(length)` | Average True Range calculation |
| `ta.sma(source, length)` | Simple moving average for RVOL |
| `ta.highest(source, length)` | Recent high for location context |
| `ta.lowest(source, length)` | Recent low for location context |
| `math.abs(value)` | Absolute value for body size |
| `math.max(a, b)` | Max of open/close for upper wick |
| `math.min(a, b)` | Min of open/close for lower wick |
| `barcolor(color)` | Colors price candles |

### Modification Guide

#### To Adjust Absorption Sensitivity

**More Signals (Lower Quality):**
```pinescript
move_threshold = 0.40   // Allow larger moves
rvol_threshold = 1.5    // Lower volume requirement
body_ratio_max = 0.45   // Allow larger bodies
```

**Fewer Signals (Higher Quality):**
```pinescript
move_threshold = 0.20   // Require smaller moves
rvol_threshold = 2.5    // Higher volume requirement
body_ratio_max = 0.25   // Require more prominent wicks
```

#### To Add Volume Spike Filter
Add additional filter for extreme volume:
```pinescript
volume_spike_threshold = input.float(3.0, title="Volume Spike", ...)
is_volume_spike = rvol >= volume_spike_threshold

// Add to info panel
strong_absorption = is_absorption and is_volume_spike
```

#### To Add Multi-Bar Absorption Detection
Detect absorption clusters (multiple absorption bars in sequence):
```pinescript
absorption_count = input.int(2, title="Absorption Cluster", minval=1, maxval=5)

// Count recent absorption bars
abs_sum = math.sum(is_absorption ? 1 : 0, absorption_count)
is_cluster = abs_sum >= absorption_count

// Use cluster for stronger signal
plotshape(is_cluster, title="Absorption Cluster", ...)
```

#### To Weight by Wick Imbalance
Create a directional strength score:
```pinescript
wick_imbalance = (lower_wick - upper_wick) / range_size  // -1 to +1
// Positive = bullish (lower wick dominant)
// Negative = bearish (upper wick dominant)

absorption_direction = is_absorption ? wick_imbalance : 0
plot(absorption_direction, title="Absorption_Direction", display=display.none)
```

#### To Integrate with RVOL Indicator
Reference RVOL from EPCH_03:
```pinescript
// In a combined indicator, you could use:
rvol_from_03 = request.security(syminfo.tickerid, timeframe.period,
               close)  // Would need EPCH_03 to export rvol
```

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] Absorption fires only when ALL THREE criteria met
- [ ] Small move alone does NOT trigger (needs high vol + wicks)
- [ ] High volume alone does NOT trigger (needs small move + wicks)
- [ ] Location detection (at high/low) works correctly
- [ ] Body ratio calculation is accurate
- [ ] Gold color appears at lows, dark orange at highs
- [ ] Candle coloring does not conflict with Momentum indicator
- [ ] Info panel displays all five rows
- [ ] Alerts fire correctly for each condition
- [ ] Works on different instruments (stocks, futures, crypto)
- [ ] Manual ATR override works correctly

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| No absorption signals | Thresholds too strict | Lower RVOL to 1.8, raise body ratio to 0.40 |
| Too many signals | Thresholds too loose | Raise RVOL to 2.5, lower body ratio to 0.25 |
| Wrong location detection | Lookback too short/long | Adjust location_lookback (10-20 typical) |
| Colors not showing | Overlay mode issue | Ensure `overlay=true` in indicator() |
| Conflicts with Momentum | Both use barcolor() | Load Absorption AFTER Momentum |
| Division by zero | Zero range or zero ATR | Code handles with conditional checks |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `atr_value` | float | ATR (auto or manual) |
| `body_size` | float | Absolute candle body size |
| `range_size` | float | High - Low |
| `move_ratio` | float | body_size / atr_value |
| `body_ratio` | float | body_size / range_size |
| `rvol` | float | volume / avg_volume |
| `is_small_move` | bool | move_ratio <= threshold |
| `is_high_volume` | bool | rvol >= threshold |
| `has_wicks` | bool | body_ratio <= threshold |
| `is_absorption` | bool | All three criteria met |
| `at_high` | bool | Price near recent high |
| `at_low` | bool | Price near recent low |
| `absorption_at_high` | bool | Absorption + at high |
| `absorption_at_low` | bool | Absorption + at low |
| `upper_wick` | float | High - max(open, close) |
| `lower_wick` | float | Min(open, close) - low |
| `bullish_absorption` | bool | lower_wick > upper_wick |
| `bearish_absorption` | bool | upper_wick > lower_wick |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `atr_length` | int | 14 | 5-50 | ATR calculation period |
| `atr_source` | string | "Auto" | Auto/Manual | ATR method |
| `manual_atr` | float | 0.50 | 0.01-100 | Fixed ATR value |
| `rvol_length` | int | 20 | 5-100 | RVOL lookback |
| `move_threshold` | float | 0.30 | 0.1-0.5 | Max move for absorption |
| `rvol_threshold` | float | 2.0 | 1.5-5.0 | Min RVOL for absorption |
| `body_ratio_max` | float | 0.35 | 0.1-0.5 | Max body ratio |
| `location_lookback` | int | 10 | 5-30 | High/low detection period |
| `location_tolerance` | float | 0.002 | 0.001-0.01 | Proximity tolerance |
| `show_markers` | bool | false | - | Show diamond markers |
| `show_panel` | bool | true | - | Show info panel |
| `alert_absorption` | bool | true | - | Alert on any absorption |
| `alert_at_extreme` | bool | true | - | Alert at high/low |

### Relationship to Other EPCH Indicators

| Indicator | Relationship |
|-----------|--------------|
| EPCH_01 (Rolling Delta) | Complementary - delta bias + absorption = stronger signal |
| EPCH_02 (Delta ROC) | Both indicate reversal - divergence + absorption = high probability |
| EPCH_03 (RVOL) | Shares RVOL calculation - could consolidate |
| EPCH_04 (Momentum) | OPPOSITE signal - they use same barcolor(), load order matters |
| EPCH_06 (Body Ratio) | Shares body ratio concept - absorption is stricter (needs volume) |

### Visual Priority Note

Both Momentum (EPCH_04) and Absorption (EPCH_05) use `barcolor()`. TradingView only allows one `barcolor()` per candle. The LAST loaded indicator wins.

**Recommended load order:**
1. EPCH_04 Momentum (load first)
2. EPCH_05 Absorption (load second - takes priority)

This means absorption colors override momentum colors when both conditions are met, which is correct for EPCH trading (reversal signals are more actionable at zones).

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
