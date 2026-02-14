# EPCH Model Definitions

## Claude Instructions

**IMPORTANT**: Before beginning any analysis or development work in this module:
1. Review `config.py` in both `12_system_analysis/` and `ramp_up_analysis/` for existing definitions
2. Review `ENTRY_MODELS`, `CONTINUATION_MODELS`, `REJECTION_MODELS` in the parent config
3. Do not ask clarifying questions about information already documented in config files
4. Cross-reference any model, indicator, or threshold assumptions against existing configuration

---

## Overview

The EPCH (Epoch) trading system uses four models based on two dimensions:
1. **Zone Type**: Primary (with macro trend) vs Secondary (counter-trend zone)
2. **Trade Type**: Continuation (breakout through zone) vs Rejection (reversal at zone)

---

## Model Matrix

| Model | Zone Type | Trade Type | Trade Direction | Description |
|-------|-----------|------------|-----------------|-------------|
| **EPCH1** | Primary | Continuation | With Trend | Momentum continuation through HVN in direction of macro trend |
| **EPCH2** | Primary | Rejection | Counter Trend | Rejection at primary zone, reversal against macro trend |
| **EPCH3** | Secondary | Continuation | Counter Trend | Continuation through secondary zone against macro trend |
| **EPCH4** | Secondary | Rejection | With Trend | Rejection at secondary zone, reversal back toward macro trend |

---

## Detailed Model Descriptions

### EPCH1 - Primary Zone Continuation (With Trend)

**Scenario**: Price is in a macro bullish trend (D2, H4, H1, M15 composite showing bullish). Price pulls back to a primary demand zone (HVN - High Volume Node). The trend side (buyers) pushes through with momentum.

**Expected Indicator Behavior**:
- vol_delta: Building in trade direction (buyers stepping in)
- vol_roc: Increasing as momentum builds toward breakout
- long_score: Building as conditions align

**Trade**: Long at primary zone, expecting continuation higher

---

### EPCH2 - Primary Zone Rejection (Counter Trend)

**Scenario**: Price approaches a primary zone from below (in bullish macro) but the opposition (sellers) holds the zone and turns the tide.

**Expected Indicator Behavior**:
- vol_delta: Initially bullish, then absorption (shrinking), then flipping to sellers
- vol_roc: Decreasing on approach (exhaustion), then expanding on rejection
- short_score: May build as absorption occurs before rejection triggers

**Trade**: Short at primary zone rejection, expecting move against macro trend

---

### EPCH3 - Secondary Zone Continuation (Counter Trend)

**Scenario**: Price moves to a secondary zone (counter-trend zone below current price in bullish macro) and continues through it, moving against the primary trend.

**Expected Indicator Behavior**:
- vol_delta: Building in counter-trend direction
- vol_roc: Increasing as counter-trend momentum builds
- Directional score building in trade direction

**Trade**: Trade in direction of secondary zone breakout (against macro trend)

---

### EPCH4 - Secondary Zone Rejection (With Trend)

**Scenario**: Price moves to secondary zone for liquidity grab, then rejects and moves back in line with the primary macro trend. This is a "fake-out" where price tests the secondary zone but fails to continue through.

**Expected Indicator Behavior**:
- vol_delta: Initially with the counter-trend move, then absorption, then flipping back to trend direction
- vol_roc: Decreasing on approach to secondary zone, then expanding on rejection
- Trend-aligned score building after rejection triggers

**Trade**: Trade the rejection back toward primary trend direction

---

## Analysis Groupings

For statistical analysis with sufficient sample sizes (~500 trades per bucket):

### Grouping Option A: By Trade Outcome Direction
- **With Trend Trades**: EPCH1 + EPCH4 (both result in trades aligned with macro trend)
- **Counter Trend Trades**: EPCH2 + EPCH3 (both result in trades against macro trend)

### Grouping Option B: By Trade Mechanics
- **Continuation Trades**: EPCH1 + EPCH3 (momentum through zone)
- **Rejection Trades**: EPCH2 + EPCH4 (reversal at zone)

### Grouping Option C: By Zone Type
- **Primary Zone Trades**: EPCH1 + EPCH2
- **Secondary Zone Trades**: EPCH3 + EPCH4

---

## Key Insight

The fundamental difference between continuation and rejection trades:

**Continuation (EPCH1/EPCH3)**:
- Momentum breaking through HVN
- Side currently in control pushes through
- Look for: Building vol_delta in trade direction, increasing vol_roc

**Rejection (EPCH2/EPCH4)**:
- Opposition holds the zone and turns the tide
- Absorption pattern followed by directional flip
- Look for: Shrinking vol_delta (absorption), then expansion in rejection direction
