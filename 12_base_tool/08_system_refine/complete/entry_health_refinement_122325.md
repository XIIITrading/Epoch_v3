> *Purpose:*

> The purpose of this update is to align the entry_events health score calculation with the DOW_AI source of truth methodology. Currently, entry_events uses pre-computed TEXT signals (e.g., "Above Avg", "Bullish", "Rising", "WIDENING") from upstream data, while exit_events recalculates health from raw numeric data using specific thresholds. This mismatch causes the entry health score to differ from the exit_events calculated health at the same bar, creating confusion in downstream analysis (optimal_trade) and preventing accurate health decay tracking.

*Dev Rules:*

1. Do not generate any code without my explicit instructions
2. Do not assume anything (naming convention, modules, directories). Ask for clarification or for files you would like to read directly.
3. Always include .txt documentation at the end in two files
   1. AI readable and understandable with enough description and specific script context to be used in other AI conversations without having to provide the full script directory.
   2. Human readable version to reviewed by me, with the intent to teach me how the script works and how I would implement it elsewhere as I learn to code Python.

*Description:*

Location: `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\entry_events\`

Source of Truth: `C:\XIIITradingSystems\Epoch\04_dow_ai\`

Documentation Output: `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\reports\`

---

## Problem Statement

Health score calculations differ between entry_events and exit_events due to input type mismatch:

| Module | Input Type | Example |
|--------|-----------|---------|
| entry_events (`health_score.py`) | Pre-computed TEXT signals | `volume_roc_signal == "Above Avg"` |
| exit_events (`health_calculator_v2.py`) | Raw numeric values | `vol_roc > 20.0%` |

This causes:
- ENTRY event shows health=8, but recalculated health at same bar shows different value
- HEALTH_CHANGE event fires on bar 0 (entry bar) showing discrepancy
- Downstream optimal_trade analysis gets inconsistent health data

---

## Root Cause Analysis

### Entry_Events Current Implementation (`health_score.py`)

Relies on TEXT signal matching:

```python
# Volume ROC - expects pre-computed text signal
volume_roc_healthy = volume_roc_signal == "Above Avg"

# Volume Delta - expects pre-computed text signal
if is_long:
    volume_delta_healthy = volume_delta_signal == "Bullish"
else:
    volume_delta_healthy = volume_delta_signal == "Bearish"

# CVD - expects pre-computed text signal
if is_long:
    cvd_trend_healthy = cvd_trend == "Rising"
else:
    cvd_trend_healthy = cvd_trend == "Falling"

# SMA Momentum - expects pre-computed text signal
sma_momentum_healthy = sma_spread_momentum == "WIDENING"
```

### Exit_Events Current Implementation (`health_calculator_v2.py`)

Calculates from raw numeric values with explicit thresholds:

```python
# Thresholds matching DOW_AI
VOLUME_ROC_THRESHOLD = 20.0       # +20% = Above Avg
CVD_SLOPE_THRESHOLD = 0.1         # Normalized slope threshold
SMA_MOMENTUM_RATIO = 1.1          # 10% increase = WIDENING

# Volume ROC - calculated from raw data
vol_roc = ((volume - volume_baseline) / volume_baseline) * 100
result.volume_roc_healthy = (vol_roc > self.VOLUME_ROC_THRESHOLD)

# Volume Delta - calculated from OHLCV
if is_long:
    result.volume_delta_healthy = (bar_delta > 0)
else:
    result.volume_delta_healthy = (bar_delta < 0)

# CVD - calculated from slope
if is_long:
    result.cvd_healthy = (cvd_slope > self.CVD_SLOPE_THRESHOLD)
else:
    result.cvd_healthy = (cvd_slope < -self.CVD_SLOPE_THRESHOLD)

# SMA Momentum - calculated from spread comparison
if prev_spread > 0:
    result.sma_momentum_healthy = (current_spread > prev_spread * self.SMA_MOMENTUM_RATIO)
```

---

## DOW_AI Thresholds (Source of Truth)

From `C:\XIIITradingSystems\Epoch\04_dow_ai\`:

| Factor | Threshold | Source File |
|--------|-----------|-------------|
| Volume ROC | `> +20%` = "Above Avg" | `calculations/volume_analysis.py:228-229` |
| CVD Slope | `> +0.1` = "Rising", `< -0.1` = "Falling" | `calculations/volume_analysis.py:186-193` |
| SMA Spread Momentum | `> 1.1x previous` = "WIDENING" | `calculations/moving_averages.py:100` |
| Volume Delta | Positive = "Bullish", Negative = "Bearish" | `calculations/volume_analysis.py:219-224` |

---

## Files Requiring Analysis

### Primary File to Modify
| File | Purpose |
|------|---------|
| `entry_events/health_score.py` | Main health calculator - needs to calculate from raw values |

### Upstream Files to Trace
| File | Question |
|------|----------|
| `entry_events/entry_enricher.py` | Where do the text signals come from? |
| `entry_events/entry_processor.py` | What data is passed to health_score.py? |
| Bar data source | Are raw OHLCV values available? |

### Reference Implementation
| File | Purpose |
|------|---------|
| `exit_events/health_calculator_v2.py` | Reference for numeric threshold logic |
| `04_dow_ai/calculations/volume_analysis.py` | Source of truth for volume thresholds |
| `04_dow_ai/calculations/moving_averages.py` | Source of truth for SMA thresholds |

---

## Implementation Options

### Option A: Modify entry_events to Calculate from Raw Values (Recommended)

**Approach:** Update `health_score.py` to accept raw numeric values and calculate health factors using the same thresholds as exit_events and DOW_AI.

**Pros:**
- Single source of truth for thresholds
- Matches exit_events exactly
- No dependency on upstream text signal generation

**Cons:**
- Requires raw OHLCV and indicator values to be passed in
- May require changes to upstream callers

### Option B: Standardize Upstream Text Signal Generation

**Approach:** Trace where the text signals originate and ensure they use the exact DOW_AI thresholds.

**Pros:**
- Minimal changes to health_score.py
- May fix other consumers of these signals

**Cons:**
- Need to find and modify upstream signal generation
- Risk of multiple places needing updates
- Harder to verify consistency

### Option C: Create Shared Health Calculator Module

**Approach:** Create a single `shared_health_calculator.py` that both entry_events and exit_events import.

**Pros:**
- Guaranteed consistency
- Single file to maintain
- Could live in a common location

**Cons:**
- Requires refactoring both modules
- Import path considerations

---

## Required Data for Numeric Calculation

If implementing Option A, entry_events needs access to:

| Data | Purpose | Currently Available? |
|------|---------|---------------------|
| Bar OHLCV | Calculate bar_delta | TBD - need to check |
| 20-bar volume average | Calculate volume ROC | TBD |
| Last 15 bar deltas | Calculate CVD slope | TBD |
| Previous SMA spread | Calculate SMA momentum | TBD |

---

## Specific Differences to Resolve

| Factor | Entry_Events Logic | Exit_Events Logic | Issue |
|--------|-------------------|-------------------|-------|
| Volume Delta | Text match: `"Bullish"` | Numeric: `bar_delta > 0` | "Neutral" signal but delta is +0.01 |
| CVD | Text match: `"Rising"` | Numeric: `slope > 0.1` | Different threshold upstream? |
| SMA Momentum | Text match: `"WIDENING"` | Numeric: `spread > prev * 1.1` | Different lookback? |
| Volume ROC | Text match: `"Above Avg"` | Numeric: `roc > 20%` | Different threshold upstream? |

---

## Questions to Answer Before Implementation

1. **Where do the text signals originate?**
   - Which module generates "Above Avg", "Bullish", "Rising", "WIDENING"?
   - What thresholds do they use?

2. **Is raw OHLCV data available at entry time?**
   - Can we access the bar data to calculate bar_delta?
   - Is the 20-bar volume baseline available?

3. **Should we maintain backward compatibility?**
   - Keep the text signal interface as fallback?
   - Add new numeric parameters alongside existing ones?

4. **What about the entry_events worksheet schema?**
   - Does it need new columns for raw indicator values?
   - Should it store the individual factor states like exit_events does?

---

## Expected Outcome

After this refinement:
- Entry health score = Exit_events calculated health at bar 0
- No HEALTH_CHANGE event fires on the entry bar
- Consistent health tracking from entry through exit
- optimal_trade gets reliable health data for analysis

---

## Documentation Deliverables

Upon completion, create:

1. **AI-Readable Documentation** (`entry_health_refinement_ai.txt`)
   - Full technical context for future AI conversations
   - Threshold values and calculation formulas
   - File relationships and dependencies

2. **Human-Readable Documentation** (`entry_health_refinement_human.txt`)
   - Explanation of the 10-factor health methodology
   - How to verify calculations are correct
   - How to extend or modify thresholds in the future
