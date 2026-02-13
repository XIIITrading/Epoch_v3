# EPCH_03_RVOL - Documentation

**Indicator:** Relative Volume (RVOL)
**Suite:** EPCH Volume-Price Action Indicator Suite
**Version:** 1.0
**Author:** XIII Trading LLC

---

## 1. TRADING APPLICATION

### What This Indicator Tells You

RVOL measures current volume relative to the average volume. It answers the question: "Is this candle's volume notable compared to what's normal?"

This is the **foundation indicator** for the EPCH suite - signals from other indicators (Momentum, Absorption) are only meaningful when accompanied by significant volume.

### The Volume Hierarchy

| Level | RVOL | Color | Meaning |
|-------|------|-------|---------|
| Normal | < 1.5x | Gray | Retail flow, noise |
| Elevated | 1.5x - 2.5x | Yellow | Above average interest |
| Significant | 2.5x - 4.0x | Orange | Institutional participation likely |
| Institutional | > 4.0x | Purple | Major player activity |

### Primary Use Cases

#### Volume Filter for Other Signals
- Only act on Momentum signals when RVOL > 1.5x
- Only act on Absorption signals when RVOL > 2.0x
- Higher RVOL = higher confidence in the signal

#### Market Open/News Detection
- Institutional volume often spikes at market open
- News events trigger volume spikes
- Purple bars = something significant is happening

#### Exhaustion Identification
- Multiple institutional volume bars in sequence
- Followed by declining volume = exhaustion
- Potential reversal setup

### How to Read the Indicator

| Visual Element | Meaning |
|----------------|---------|
| Gray Column | Normal volume, no significance |
| Yellow Column | Elevated - worth watching |
| Orange Column | Significant - pay attention |
| Purple Column | Institutional - major activity |
| Yellow Background | Elevated volume on price chart |
| Orange Background | Significant volume on price chart |
| Purple Background | Institutional volume on price chart |
| Dotted Lines | Threshold levels for reference |

### Trading Rules

**Rule 1: Volume Validates Everything**
```
Signal without volume = noise
Signal with volume = actionable
```

**Rule 2: Higher Volume = Higher Confidence**
```
RVOL 1.5x signal = maybe
RVOL 2.5x signal = probably
RVOL 4.0x signal = definitely pay attention
```

**Rule 3: Context Matters**
```
First bar of day at 4.0x = normal (market open)
Mid-day bar at 4.0x = unusual (something happening)
```

### Recommended Settings

| Market | Avg Length | Elevated | Significant | Institutional |
|--------|------------|----------|-------------|---------------|
| Stocks (M1) | 20 | 1.5 | 2.5 | 4.0 |
| Futures (M1) | 20 | 1.5 | 2.5 | 4.0 |
| Crypto (M1) | 30 | 2.0 | 3.0 | 5.0 |
| Low Volume Stock | 30 | 2.0 | 3.5 | 5.0 |

### Info Panel Interpretation

| Field | Meaning |
|-------|---------|
| RVOL | Current relative volume (multiple of average) |
| Volume | Raw volume for the current bar |
| Level | Classification: NORMAL, ELEVATED, SIGNIFICANT, INSTITUTIONAL |

---

## 2. TECHNICAL BASIS

### Why Relative Volume Matters

Absolute volume is meaningless without context:
- 1 million shares on SPY = low volume
- 1 million shares on a small cap = massive volume

RVOL normalizes volume across all instruments by comparing to that instrument's own average.

### The SMA Baseline

We use a Simple Moving Average of volume as the baseline:
- Default: 20 bars
- Represents "typical" volume for this instrument/timeframe
- Adapts as market conditions change

### Threshold Selection Rationale

**1.5x (Elevated):**
- One standard deviation above mean for most instruments
- Filters out 70%+ of bars as "normal"
- Minimum threshold for signal consideration

**2.5x (Significant):**
- Clear departure from normal activity
- Typically indicates institutional order flow beginning
- Good filter for Momentum/Absorption signals

**4.0x (Institutional):**
- Rare occurrence (typically <5% of bars)
- Almost certainly large player activity
- News, block trades, or aggressive accumulation/distribution

### Alert Logic: New Threshold Breach

Alerts fire on NEW threshold breaches, not every bar above threshold:
```
new_elevated = currently elevated AND NOT previously elevated
```

This prevents alert spam during sustained high-volume periods.

---

## 3. CALCULATIONS

### Step-by-Step Calculation

#### Step 1: Average Volume
```
avg_volume = SMA(volume, avg_length)  // Default: 20 bars
```

#### Step 2: Relative Volume
```
rvol = volume / avg_volume
```

#### Step 3: Classification
```
is_elevated     = rvol >= 1.5 AND rvol < 2.5
is_significant  = rvol >= 2.5 AND rvol < 4.0
is_institutional = rvol >= 4.0
is_notable      = rvol >= 1.5  // Any elevated+
```

#### Step 4: New Breach Detection (for alerts)
```
new_elevated = is_elevated AND NOT was_elevated_last_bar
new_significant = is_significant AND NOT was_significant_last_bar
new_institutional = is_institutional AND NOT was_institutional_last_bar
```

### Numerical Example

Given 5 bars of volume data:
| Bar | Volume | 5-bar SMA | RVOL | Classification |
|-----|--------|-----------|------|----------------|
| 1 | 10,000 | 10,000 | 1.00x | Normal |
| 2 | 12,000 | 10,400 | 1.15x | Normal |
| 3 | 18,000 | 11,600 | 1.55x | Elevated |
| 4 | 35,000 | 15,800 | 2.22x | Elevated |
| 5 | 50,000 | 25,000 | 2.00x | Elevated |

Note: As high-volume bars enter the average, RVOL can decrease even if absolute volume stays high.

### Color Assignment Logic

```
IF rvol >= threshold_3 (4.0):
    color = PURPLE
ELSE IF rvol >= threshold_2 (2.5):
    color = ORANGE
ELSE IF rvol >= threshold_1 (1.5):
    color = YELLOW
ELSE:
    color = GRAY
```

---

## 4. AI IMPLEMENTATION GUIDE

### File Location
```
C:\XIIITradingSystems\Epoch\03_indicators\EPCH_03_RVOL.pine
```

### Code Structure Overview

```
+---------------------------------------------+
| Header (License, Version, Purpose)          |
+---------------------------------------------+
| Color Scheme Constants                      |
| - Standard suite colors                     |
| - RVOL-specific: elevated, significant,     |
|   institutional                             |
+---------------------------------------------+
| Input Group Constants                       |
+---------------------------------------------+
| Input Definitions                           |
| - avg_length                                |
| - threshold_1, threshold_2, threshold_3     |
| - Visual toggles                            |
| - Alert toggles                             |
+---------------------------------------------+
| Core Calculations                           |
| - avg_volume (SMA)                          |
| - rvol (ratio)                              |
| - Classification flags                      |
| - New breach detection                      |
+---------------------------------------------+
| Visual Outputs (overlay=false)              |
| - plot (RVOL columns)                       |
| - hline (threshold levels)                  |
| - bgcolor (optional highlighting)           |
+---------------------------------------------+
| Alert Conditions                            |
| - New elevated, significant, institutional  |
| - Any notable volume                        |
+---------------------------------------------+
| Info Panel (Table)                          |
| - RVOL, Volume, Level                       |
+---------------------------------------------+
| Export Plots (display=none)                 |
| - RVOL value, Notable flag, Level code      |
+---------------------------------------------+
```

### Key PineScript Functions Used

| Function | Purpose |
|----------|---------|
| `ta.sma(source, length)` | Simple moving average for baseline |
| `plot(..., style=plot.style_columns)` | Renders volume-style columns |
| `hline(price, ...)` | Horizontal reference lines |
| `bgcolor(color)` | Background highlighting |
| `format.volume` | Formats large numbers (K, M) |

### Modification Guide

#### To Use EMA Instead of SMA
```pinescript
// Replace:
avg_volume = ta.sma(volume, avg_length)

// With:
avg_volume = ta.ema(volume, avg_length)
```
EMA will be more responsive to recent volume changes.

#### To Add Time-of-Day Filtering
Filter out market open volume spikes:
```pinescript
market_open_minutes = input.int(30, title="Market Open Filter (minutes)")
is_market_open = (hour == 9 and minute < 30 + market_open_minutes) or (hour == 9 and minute >= 30)

// Modify classification
is_notable_filtered = is_notable and not is_market_open
```

#### To Add Cumulative RVOL
Track cumulative relative volume for the session:
```pinescript
var float cum_volume = 0.0
var float cum_avg = 0.0
var int bar_count = 0

if ta.change(time("D")) != 0
    cum_volume := 0.0
    cum_avg := 0.0
    bar_count := 0

cum_volume += volume
bar_count += 1
cum_avg += avg_volume

session_rvol = cum_avg > 0 ? cum_volume / cum_avg : 0
```

#### To Add Volume Trend
Detect if volume is increasing or decreasing:
```pinescript
rvol_sma = ta.sma(rvol, 5)
rvol_rising = rvol_sma > rvol_sma[1]
rvol_falling = rvol_sma < rvol_sma[1]
```

#### To Export for Other Indicators
The script already exports via hidden plots:
```pinescript
plot(rvol, title="RVOL_Export", display=display.none)
plot(is_notable ? 1 : 0, title="Notable_Flag", display=display.none)
```

Other indicators can read these using `request.security()`.

### Testing Checklist

After any modification:
- [ ] Script compiles without errors
- [ ] RVOL calculates correctly (verify: volume / SMA)
- [ ] Threshold levels display as dotted lines
- [ ] Column colors match threshold classifications
- [ ] Background highlighting matches column colors
- [ ] Alerts fire only on NEW threshold breaches
- [ ] No division by zero errors (check low-volume instruments)
- [ ] Works on stocks, futures, crypto
- [ ] Works on M1, M5, M15, H1 timeframes
- [ ] Info panel displays correct values

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| RVOL always near 1.0 | avg_length too short | Increase to 30-50 |
| Too many alerts | Thresholds too low | Raise thresholds |
| Columns not visible | show_rvol_pane is false | Enable toggle |
| Background too dark | Transparency too low | Adjust color alpha |
| No institutional bars | Instrument has low volume | Lower threshold_3 |

### Full Variable Reference

| Variable | Type | Description |
|----------|------|-------------|
| `avg_volume` | float | SMA of volume over avg_length |
| `rvol` | float | volume / avg_volume |
| `is_elevated` | bool | RVOL in elevated range |
| `is_significant` | bool | RVOL in significant range |
| `is_institutional` | bool | RVOL above institutional threshold |
| `is_notable` | bool | Any elevated or above |
| `is_bullish` | bool | close > open |
| `is_bearish` | bool | close < open |
| `new_elevated` | bool | Just entered elevated |
| `new_significant` | bool | Just entered significant |
| `new_institutional` | bool | Just entered institutional |

### Input Reference

| Input | Type | Default | Range | Purpose |
|-------|------|---------|-------|---------|
| `avg_length` | int | 20 | 5-100 | SMA lookback period |
| `threshold_1` | float | 1.5 | 1.1-3.0 | Elevated threshold |
| `threshold_2` | float | 2.5 | 1.5-5.0 | Significant threshold |
| `threshold_3` | float | 4.0 | 2.5-10.0 | Institutional threshold |
| `show_rvol_pane` | bool | true | - | Show RVOL columns |
| `show_avg_line` | bool | true | - | Show 1.0 reference line |
| `highlight_bg` | bool | true | - | Background highlighting |
| `show_panel` | bool | true | - | Show info panel |
| `alert_elevated` | bool | false | - | Alert on elevated |
| `alert_significant` | bool | true | - | Alert on significant |
| `alert_institutional` | bool | true | - | Alert on institutional |

### Relationship to Other EPCH Indicators

| Indicator | Relationship |
|-----------|--------------|
| EPCH_01 (Rolling Delta) | RVOL filters delta signals - only trust high-volume delta |
| EPCH_02 (Delta ROC) | RVOL + divergence = stronger signal |
| EPCH_04 (Momentum) | Momentum requires high RVOL by definition |
| EPCH_05 (Absorption) | Absorption requires high RVOL by definition |
| EPCH_06 (Body Ratio) | RVOL + high body ratio = conviction |

### Foundation Role

RVOL is the foundational filter for the entire suite:
```
Other indicators ask: "What is happening?"
RVOL asks: "Does it matter?"

Low RVOL + any signal = probably noise
High RVOL + any signal = probably meaningful
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial release |

---

*XIII Trading LLC | EPCH Indicator Suite*
