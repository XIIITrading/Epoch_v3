# EPCH Indicators v1.0 - Technical Specification

**Version:** 1.0
**Date:** 2026-01-17
**Purpose:** Training rubric and indicator specification for zone-based trade evaluation

---

## Overview

EPCH Indicators v1.0 defines a standardized set of 5 technical indicators used to evaluate whether price action will **continue through a zone** or **reject off a zone**. This specification provides direction-specific interpretations based on statistical edge analysis of historical trade data.

### Core Indicators

| # | Indicator | Data Source | Primary Function |
|---|-----------|-------------|------------------|
| 1 | Candle Range | `candle_range_pct` | Zone significance / Skip filter |
| 2 | Volume Delta | `volume_delta` | Buyer/seller conviction |
| 3 | Volume ROC | `volume_roc_20` | Momentum acceleration |
| 4 | SMA Config | `sma_edge` table | Trend context |
| 5 | H1 Structure | `entry_indicators` | Market structure state |

---

## Trade Scenario Definitions

The system evaluates 4 distinct trade scenarios based on **direction** and **trade type**:

### LONG Trades

| Scenario | Models | Description |
|----------|--------|-------------|
| **LONG CONTINUATION** | EPCH1, EPCH3 | Price approaches from BELOW the zone, pushes THROUGH the zone top, continues upward |
| **LONG REJECTION** | EPCH2, EPCH4 | Price approaches from ABOVE the zone, enters the zone top, bounces BACK UP through the top |

### SHORT Trades

| Scenario | Models | Description |
|----------|--------|-------------|
| **SHORT CONTINUATION** | EPCH1, EPCH3 | Price approaches from ABOVE the zone, pushes THROUGH the zone bottom, continues downward |
| **SHORT REJECTION** | EPCH2, EPCH4 | Price approaches from BELOW the zone, enters the zone bottom, pushes BACK DOWN through the bottom |

### Key Concept

- **CONTINUATION** = Momentum play - price pushes THROUGH the zone
- **REJECTION** = Reversal play - price bounces BACK OUT the way it entered

---

## Indicator Specifications

### 1. Candle Range (`candle_range_pct`)

**Definition:** High-Low range of the entry candle as percentage of price

**Function:** Determines zone significance and acts as primary skip filter

| Value | Classification | Action | Win Rate |
|-------|----------------|--------|----------|
| < 0.12% | Absorption Zone | **SKIP** | 33% |
| 0.12% - 0.15% | Low Range | Caution | ~40% |
| >= 0.15% | Normal Range | Trade | 52%+ |
| >= 0.20% | High Range | Strong signal | 55%+ |

**Edge:** +20pp advantage for >= 0.15% vs < 0.12%

**Rule:** Always skip trades with candle_range < 0.12% (Absorption Zone Skip Rule)

---

### 2. Volume Delta (`volume_delta`)

**Definition:** Net buying vs selling pressure (positive = buyers dominating)

**Function:** Conviction measurement with direction-specific interpretation

| Direction | Favorable Signal | Interpretation | Effect Size |
|-----------|------------------|----------------|-------------|
| **LONG** | High magnitude (either direction) | Strong conviction present | +5-7pp |
| **SHORT** | **POSITIVE** delta | Exhausted buyers / failed rally | **+10.7pp** |

**Paradox Explanation (SHORT):**
- Positive delta on SHORT trades = buyers tried but failed
- Indicates exhaustion / trapped longs
- Catching the reversal after buying pressure fails

---

### 3. Volume ROC (`volume_roc_20`)

**Definition:** Rate of change in volume vs 20-period average

**Function:** Momentum/acceleration confirmation

| Value | Classification | Interpretation |
|-------|----------------|----------------|
| < 0% | Declining volume | Low conviction |
| 0% - 30% | Normal volume | Baseline conditions |
| >= 30% | Elevated volume | Momentum confirmation |
| >= 50% | High volume | Strong momentum |

**Application:** Both LONG and SHORT benefit from elevated volume (>= 30%)

**Effect Size:** +6-8pp for high volume conditions

---

### 4. SMA Configuration (`sma_edge`)

**Definition:** Relationship between SMA9, SMA21, and price position

**Components:**
- `sma_spread_pct`: Distance between SMA9 and SMA21
- `sma_config`: BULLISH (9 > 21) or BEARISH (9 < 21)
- `price_position`: ABOVE_BOTH, BETWEEN, BELOW_BOTH

**Direction-Specific Signals:**

| Direction | Favorable Config | Favorable Position | Effect Size |
|-----------|------------------|-------------------|-------------|
| **LONG** | Wide spread (>= 0.15%) | Trending alignment | +7-9pp |
| **SHORT** | **BULLISH** config | **ABOVE_BOTH** | **+9.3pp / +14.1pp** |

**Paradox Explanation (SHORT):**
- BULLISH SMA config on SHORT = price was rallying, now reversing
- Price ABOVE_BOTH on SHORT = extended rally, catching the failure
- Looking for exhaustion at the top of a move

---

### 5. H1 Structure (`entry_indicators.h1_structure`)

**Definition:** Market structure state on H1 timeframe (BULL, BEAR, NEUTRAL)

**Function:** Identify optimal market conditions

| H1 State | Win Rate | Interpretation |
|----------|----------|----------------|
| ALIGNED (with trade) | 20% | **Avoid** - overcrowded/extended |
| CONTRARY (against trade) | 40% | Baseline conditions |
| **NEUTRAL** | **53%** | **Best conditions** - transition state |

**Key Finding:** NEUTRAL structure wins across ALL scenarios

**Why NEUTRAL Works:**
- Represents transition/consolidation state
- Less crowded - not everyone sees the move
- Zone becomes decision point rather than trend continuation

**Application:** Prefer trades when H1 = NEUTRAL regardless of direction

---

## Training Cheat Sheet

### Universal Rules (All Scenarios)

| Check | Condition | Action |
|-------|-----------|--------|
| Candle Range | < 0.12% | **SKIP** |
| Candle Range | >= 0.15% | Proceed |
| H1 Structure | NEUTRAL | Strong preference |
| Volume ROC | >= 30% | Confirmation |

### LONG Trades

```
LONG CONTINUATION (Price from below, through zone, continues up)
+----------------------------------------+
| Indicator      | Look For              |
+----------------+-----------------------+
| Candle Range   | >= 0.15%              |
| Vol Delta      | High magnitude        |
| Vol ROC        | >= 30%                |
| SMA Config     | Wide spread           |
| H1 Structure   | NEUTRAL preferred     |
+----------------------------------------+

LONG REJECTION (Price from above, bounces back up through top)
+----------------------------------------+
| Indicator      | Look For              |
+----------------+-----------------------+
| Candle Range   | >= 0.15%              |
| Vol Delta      | High magnitude        |
| Vol ROC        | >= 30%                |
| SMA Config     | Wide spread           |
| H1 Structure   | NEUTRAL preferred     |
+----------------------------------------+
```

### SHORT Trades (Note the Paradoxes)

```
SHORT CONTINUATION (Price from above, through zone, continues down)
+----------------------------------------+
| Indicator      | Look For              |
+----------------+-----------------------+
| Candle Range   | >= 0.15%              |
| Vol Delta      | POSITIVE (paradox)    |
| Vol ROC        | >= 30%                |
| SMA Config     | BULLISH (paradox)     |
| H1 Structure   | NEUTRAL preferred     |
+----------------------------------------+

SHORT REJECTION (Price from below, pushes back down through bottom)
+----------------------------------------+
| Indicator      | Look For              |
+----------------+-----------------------+
| Candle Range   | >= 0.15%              |
| Vol Delta      | POSITIVE (paradox)    |
| Vol ROC        | >= 30%                |
| SMA Config     | BULLISH (paradox)     |
| H1 Structure   | NEUTRAL preferred     |
+----------------------------------------+
```

### Paradox Summary for SHORT Trades

| Indicator | Expected | Actual Winner | Why |
|-----------|----------|---------------|-----|
| Vol Delta | Negative (sellers) | **Positive** | Exhausted buyers, catching failure |
| SMA Config | Bearish | **Bullish** | Failed rally, catching reversal |
| Price Position | Below SMAs | **Above Both** | Extended rally, catching top |

**Interpretation:** SHORT trades work best when catching **failed bullish moves**, not confirming bearish momentum.

---

## Win Rate Expectations

### Baseline Performance

| Condition | Win Rate |
|-----------|----------|
| Unfiltered trades | ~40% |
| With Absorption Skip | ~45% |
| With full rubric | 50-55% |

### Edge Contributions

| Indicator | Best Condition | Edge |
|-----------|----------------|------|
| Candle Range >= 0.15% | All | +20pp |
| Vol Delta POSITIVE | SHORT | +10.7pp |
| SMA BULLISH | SHORT | +9.3pp |
| Price ABOVE_BOTH | SHORT | +14.1pp |
| H1 NEUTRAL | All | +13pp vs ALIGNED |

---

## Implementation Notes

### Data Sources

```
entry_indicators table:
- h4_structure, h1_structure, m15_structure, m5_structure
- candle_range_pct
- volume_delta
- volume_roc_20

sma_edge table:
- sma9, sma21
- sma_spread_pct
- sma_config (BULLISH/BEARISH)
- price_position (ABOVE_BOTH/BETWEEN/BELOW_BOTH)
```

### Calculation Priority

1. **First:** Check Candle Range - Skip if < 0.12%
2. **Second:** Check H1 Structure - Prefer NEUTRAL
3. **Third:** Apply direction-specific indicator checks
4. **Fourth:** Calculate overall signal strength

### Signal Scoring (Optional)

Each favorable condition adds to signal score:

| Condition Met | Points |
|---------------|--------|
| Candle Range >= 0.15% | +2 |
| H1 NEUTRAL | +2 |
| Vol ROC >= 30% | +1 |
| Direction-specific delta | +1 |
| Direction-specific SMA | +1 |

**Score Interpretation:**
- 0-2: Weak signal
- 3-4: Moderate signal
- 5-7: Strong signal

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-17 | Initial specification with 5 core indicators |

---

## References

- `Indicator_Validation_Pipeline.md` - Full edge analysis methodology
- `candle_range/results/` - Candle range edge analysis
- `volume_delta/results/` - Volume delta edge analysis
- `volume_roc/results/` - Volume ROC edge analysis
- `sma_edge/results/` - SMA configuration edge analysis
- `structure_edge/results/` - Market structure edge analysis
