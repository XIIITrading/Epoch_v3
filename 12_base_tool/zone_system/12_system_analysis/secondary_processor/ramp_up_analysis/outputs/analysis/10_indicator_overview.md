# Indicator Overview & Methodology

## Metadata
- **System**: EPOCH Trading System - Ramp-Up Analysis
- **Purpose**: Reference document for Claude analysis of indicator behavior
- **Lookback Period**: 15 M1 bars before entry (bar -15 to bar -1) plus entry bar (bar 0)
- **Stop Type**: m5_atr (5-minute ATR-based stop)
- **Total Trades**: 2,768

---

## Trade Outcome Classification

### Outcome Determination Logic
Outcomes are classified based on the relationship between **MFE (Max Favorable Excursion)** timing and **Stop Hit** timing:

| Outcome | Logic | Description |
|---------|-------|-------------|
| **WIN** | MFE ≥ Profit Target | Price reached profit target |
| **PARTIAL** | mfe_time < stop_hit_time | Price moved favorably FIRST, then reversed to hit stop |
| **LOSS** | mfe_time > stop_hit_time | Stop hit FIRST, before any favorable move |

### Complete Outcome Breakdown

| Outcome | Stop Status | Count | Avg R | Interpretation |
|---------|-------------|-------|-------|----------------|
| **WIN** | No Stop Hit | 1,058 | +3.09R | Hit profit target cleanly - price never returned to stop |
| **WIN** | Stop Hit | 455 | +2.02R | Hit profit target, then later hit stop (trailing stop or continued hold) |
| **PARTIAL** | No Stop Hit | 131 | +0.65R | EOD closure at 15:30 cutoff - didn't hit stop or target |
| **PARTIAL** | Stop Hit | 588 | +0.38R | Trade worked initially (MFE first), then reversed to stop |
| **LOSS** | Stop Hit | 537 | -1.00R | Stop hit before any meaningful favorable move |

### Key Insight: PARTIAL ≠ Failed Trade
PARTIAL trades (719 total) represent a **distinct pattern**:
- Price moved in the trade direction first (recorded as MFE)
- Then reversed and hit the stop
- Average R achieved: +0.43R (still positive!)

This suggests PARTIAL trades may have **similar entry indicator patterns to WIN trades** but different behavior post-entry. The indicator analysis focuses on WIN vs LOSS to identify what distinguishes trades that work from trades that never worked.

### Analysis Methodology
- **Current Analysis**: WIN vs LOSS only (excludes PARTIAL)
- **WIN Rate Calculation**: 1,513 / (1,513 + 537) = **73.8%**
- **Conservative Rate** (PARTIAL as LOSS): 1,513 / 2,768 = **54.7%**
- **System Expectancy**: +1.43R per trade average

---

## Outcome Breakdown by Direction

### LONG (1,366 trades)
| Outcome | Stop Status | Count | Avg R | Notes |
|---------|-------------|-------|-------|-------|
| WIN | No Stop Hit | 534 | +3.01R | Clean winners |
| WIN | Stop Hit | 211 | +1.94R | Hit target, then stop |
| PARTIAL | No Stop Hit | 54 | +0.64R | EOD closure |
| PARTIAL | Stop Hit | 282 | +0.35R | Worked then reversed |
| LOSS | Stop Hit | 285 | -1.00R | Pure losses |

**LONG Win Rate (W/L only)**: 745 / 1,030 = **72.3%**

### SHORT (1,402 trades)
| Outcome | Stop Status | Count | Avg R | Notes |
|---------|-------------|-------|-------|-------|
| WIN | No Stop Hit | 524 | +3.17R | Clean winners |
| WIN | Stop Hit | 244 | +2.09R | Hit target, then stop |
| PARTIAL | No Stop Hit | 77 | +0.66R | EOD closure |
| PARTIAL | Stop Hit | 306 | +0.40R | Worked then reversed |
| LOSS | Stop Hit | 252 | -1.00R | Pure losses |

**SHORT Win Rate (W/L only)**: 768 / 1,020 = **75.3%**

---

## Outcome Breakdown by Model

### EPCH1 - Continuation / Primary Zone / With Trend (147 trades)
| Outcome | Stop Status | Count | Avg R |
|---------|-------------|-------|-------|
| WIN | No Stop Hit | 46 | +3.12R |
| WIN | Stop Hit | 22 | +2.41R |
| PARTIAL | No Stop Hit | 2 | +0.81R |
| PARTIAL | Stop Hit | 46 | +0.38R |
| LOSS | Stop Hit | 28 | -1.00R |

**EPCH1 Win Rate**: 68 / 96 = **70.8%**

### EPCH2 - Rejection / Primary Zone / Counter Trend (1,415 trades)
| Outcome | Stop Status | Count | Avg R |
|---------|-------------|-------|-------|
| WIN | No Stop Hit | 477 | +2.86R |
| WIN | Stop Hit | 253 | +2.18R |
| PARTIAL | No Stop Hit | 41 | +0.68R |
| PARTIAL | Stop Hit | 331 | +0.38R |
| LOSS | Stop Hit | 304 | -1.00R |

**EPCH2 Win Rate**: 730 / 1,034 = **70.6%**

### EPCH3 - Continuation / Secondary Zone / Counter Trend (120 trades)
| Outcome | Stop Status | Count | Avg R |
|---------|-------------|-------|-------|
| WIN | No Stop Hit | 48 | +3.40R |
| WIN | Stop Hit | 18 | +1.43R |
| PARTIAL | No Stop Hit | 6 | +0.44R |
| PARTIAL | Stop Hit | 29 | +0.33R |
| LOSS | Stop Hit | 15 | -1.00R |

**EPCH3 Win Rate**: 66 / 81 = **81.5%** (Highest!)

### EPCH4 - Rejection / Secondary Zone / With Trend (1,111 trades)
| Outcome | Stop Status | Count | Avg R |
|---------|-------------|-------|-------|
| WIN | No Stop Hit | 487 | +3.28R |
| WIN | Stop Hit | 162 | +1.79R |
| PARTIAL | No Stop Hit | 82 | +0.65R |
| PARTIAL | Stop Hit | 182 | +0.38R |
| LOSS | Stop Hit | 190 | -1.00R |

**EPCH4 Win Rate**: 649 / 839 = **77.4%**

---

## Raw Indicators (from m1_indicator_bars table)

### 1. candle_range_pct
**Description**: Candle size as percentage of price
**Calculation**: `(high - low) / close * 100`
**Interpretation**:
- Higher values = larger candles, more volatility/conviction
- Lower values = compression, indecision
- For **Continuation trades**: Look for expanding range as momentum builds
- For **Rejection trades**: May see compression before the flip

### 2. vol_delta
**Description**: Net buying vs selling volume differential
**Calculation**: `buy_volume - sell_volume` (tick-level aggregation)
**Interpretation**:
- **Positive**: More aggressive buying (bullish pressure)
- **Negative**: More aggressive selling (bearish pressure)
- **Near zero**: Balanced, no clear aggressor
- For **LONG trades**: Want positive vol_delta building
- For **SHORT trades**: Want negative vol_delta building
- For **Rejection trades**: Look for absorption (delta fading) before flip

### 3. vol_roc
**Description**: Volume Rate of Change - measures volume acceleration
**Calculation**: `(current_volume - prior_volume) / prior_volume * 100`
**Interpretation**:
- **Positive**: Volume increasing (participation growing)
- **Negative**: Volume decreasing (participation waning)
- High vol_roc with matching vol_delta = strong conviction move
- Fading vol_roc may signal exhaustion

### 4. sma_spread
**Description**: Distance between fast and slow SMA as percentage
**Calculation**: `(fast_sma - slow_sma) / slow_sma * 100`
**Interpretation**:
- **Positive**: Fast SMA above slow (bullish alignment)
- **Negative**: Fast SMA below slow (bearish alignment)
- **Widening spread**: Trend strengthening
- **Narrowing spread**: Trend weakening, possible reversal

### 5. sma_momentum_ratio
**Description**: Ratio measuring SMA configuration momentum
**Calculation**: Proprietary ratio of SMA slopes and spacing
**Interpretation**:
- **> 1.0**: Bullish momentum configuration
- **< 1.0**: Bearish momentum configuration
- **= 1.0**: Neutral/transitioning
- Higher magnitude = stronger momentum alignment

### 6. long_score
**Description**: Composite score favoring long entries (0-10 scale)
**Calculation**: Weighted combination of:
- Volume delta direction
- SMA configuration
- Structure alignment
- Momentum indicators
**Interpretation**:
- **7-10**: Strong long setup conditions
- **4-6**: Neutral/mixed conditions
- **0-3**: Conditions favor shorts

### 7. short_score
**Description**: Composite score favoring short entries (0-10 scale)
**Calculation**: Inverse weighting of long_score components
**Interpretation**:
- **7-10**: Strong short setup conditions
- **4-6**: Neutral/mixed conditions
- **0-3**: Conditions favor longs

### 8. m15_structure
**Description**: 15-minute timeframe market structure classification
**Values**: `BULL`, `BEAR`, `NEUTRAL`
**Interpretation**:
- Reflects higher timeframe bias
- **BULL**: M15 showing higher highs/higher lows
- **BEAR**: M15 showing lower highs/lower lows
- **NEUTRAL**: Ranging/consolidating

### 9. h1_structure
**Description**: 1-hour timeframe market structure classification
**Values**: `BULL`, `BEAR`, `NEUTRAL`
**Interpretation**:
- Reflects macro trend direction
- More significant than M15 for trend trades
- Alignment with trade direction increases probability

---

## Derived Metrics (Calculated in Ramp-Up Analysis)

### Ramp Averages
**Calculation**: Simple mean across bars -15 to -1
**Purpose**: Baseline indicator level during ramp period
**Usage**: Compare entry bar values to ramp average

### Ramp Trends (Linear Regression)
**Calculation**: Linear regression slope over ramp period, normalized by value range
**Classification**:
- **RISING**: Normalized slope > 5% (indicator increasing toward entry)
- **FALLING**: Normalized slope < -5% (indicator decreasing toward entry)
- **FLAT**: Slope within +/- 5% (no clear direction)
**Purpose**: Identifies directional bias in indicator trajectory

### Ramp Momentum (First-Half vs Second-Half)
**Calculation**: Compare average of bars -15 to -8 vs bars -7 to -1
**Classification**:
- **BUILDING**: Second half > 10% higher than first half (accelerating)
- **FADING**: Second half > 10% lower than first half (decelerating)
- **STABLE**: Change within +/- 10% (consistent)
**Purpose**: Identifies acceleration/deceleration patterns

### Structure Consistency
**Calculation**: Percentage of ramp bars with same structure value
**Classification**:
- **CONSISTENT_BULL**: 80%+ bars show BULL structure
- **CONSISTENT_BEAR**: 80%+ bars show BEAR structure
- **FLIP_TO_BULL**: Started BEAR, ended BULL
- **FLIP_TO_BEAR**: Started BULL, ended BEAR
- **MIXED**: No dominant pattern
**Purpose**: Identifies structure alignment and transitions

---

## Model Context for Indicator Interpretation

### EPCH1 (Continuation - Primary Zone - With Trend)
**Expected patterns for winning trades**:
- vol_delta aligned with direction, BUILDING momentum
- vol_roc positive (increasing participation)
- Structure CONSISTENT with trade direction
- long_score/short_score building in trade direction

### EPCH2 (Rejection - Primary Zone - Counter Trend)
**Expected patterns for winning trades**:
- vol_delta showing absorption (FADING in prior direction)
- vol_roc may show exhaustion then revival
- Structure may show FLIP pattern
- Score in trade direction should be BUILDING

### EPCH3 (Continuation - Secondary Zone - Counter Trend)
**Expected patterns for winning trades**:
- Similar to EPCH1 but against macro trend
- Need stronger vol_delta conviction
- Structure alignment less important (trading against it)
- Scores should show clear directional bias

### EPCH4 (Rejection - Secondary Zone - With Trend)
**Expected patterns for winning trades**:
- vol_delta absorption then flip with macro trend
- Structure FLIP back toward macro trend
- Scores should show reversal pattern

---

## Entry Qualifier Tool Display Reference

Your PyQt Entry Qualifier tool displays these indicators in real-time:
| Display | Indicator | Key Question |
|---------|-----------|--------------|
| Candle Range % | candle_range_pct | Is volatility expanding or compressing? |
| Vol Delta | vol_delta | Who is the aggressor? |
| Vol ROC | vol_roc | Is participation increasing? |
| SMA Config | sma_spread + sma_momentum_ratio | Are moving averages aligned? |
| H1 Structure | h1_structure | What is the macro trend? |
| LONG Score | long_score | How favorable for longs? |
| SHORT Score | short_score | How favorable for shorts? |

---

## Analysis Framework

When analyzing indicator patterns, consider:

1. **Alignment**: Do indicators agree or conflict?
2. **Trajectory**: Are values moving in the right direction?
3. **Momentum**: Is the move accelerating or fading?
4. **Context**: Does the pattern fit the model type (Continuation vs Rejection)?
5. **Structure**: Is higher timeframe structure supportive?

The goal is to identify **signature patterns** that distinguish winning trades from losing trades for each Model + Direction combination.
