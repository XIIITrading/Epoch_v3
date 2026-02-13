# EPOCH Trading System - Claude Desktop Framework
## Complete Reference for AI-Assisted Trade Analysis

**Version:** 1.0
**Last Updated:** January 20, 2026
**Data Source:** 2,788 validated trades (Dec 15, 2025 - Jan 16, 2026)

---

## Quick Reference Card

### Universal Entry Filters

| Check | Threshold | Action | Effect |
|-------|-----------|--------|--------|
| Candle Range | < 0.12% | **SKIP** | -11pp (Absorption zone) |
| Candle Range | ≥ 0.15% | PROCEED | +10pp baseline |
| Health Score | < 4 | CAUTION | Low probability |
| Zone Rank | L1-L2 | CAUTION | Lower win rates |

### Model Win Rates (Baseline Reference)

| Model | Type | Baseline WR | Best Conditions |
|-------|------|-------------|-----------------|
| EPCH1 | Primary Continuation | ~46% | H1 NEUTRAL, Range ≥ 0.15% |
| EPCH2 | Primary Rejection | ~44% | Vol Delta paradox applies |
| EPCH3 | Secondary Continuation | ~45% | Health Score ≥ 7 |
| EPCH4 | Secondary Rejection | ~43% | Structure divergence |

---

## System Overview

### What is EPOCH?

EPOCH is an institutional-grade trading system that identifies high-probability trading zones based on:
- **Volume Profile Analysis**: High Volume Nodes (HVNs) at $0.01 granularity
- **Multi-Timeframe Confluence**: 13 category types with weighted scoring
- **10-Factor Health Scoring**: Real-time entry quality assessment

### The 4 Entry Models

```
PRIMARY ZONES (Higher conviction setups)
├── EPCH_01: Primary Continuation
│   └── Trade WITH zone direction
│   └── Example: Zone is BULLISH, enter LONG
│
└── EPCH_02: Primary Rejection
    └── Trade AGAINST zone direction
    └── Example: Zone is BULLISH, enter SHORT (fade)

SECONDARY ZONES (Counter-trend opportunities)
├── EPCH_03: Secondary Continuation
│   └── Trade WITH secondary zone direction
│
└── EPCH_04: Secondary Rejection
    └── Trade AGAINST secondary zone direction
```

---

## Validated Indicator Edges

### CRITICAL: These are statistically validated findings from 2,788 trades

### Universal Edges (Apply to ALL trades)

#### Candle Range (STRONGEST indicator - 18-31pp effect)

| Condition | Win Rate | Effect | Action |
|-----------|----------|--------|--------|
| < 0.12% (Absorption) | 33% | -11pp | **ALWAYS SKIP** |
| 0.12% - 0.15% | 42% | -2pp | CAUTION |
| ≥ 0.15% (Normal) | 54% | +10pp | PROCEED |
| ≥ 0.20% (High) | 61% | +17pp | STRONG PROCEED |

**Rule:** Never enter on absorption bars (< 0.12% range)

#### H1 Structure (30-54pp effect - PARADOXICAL)

| H1 Direction | Win Rate | Effect | Notes |
|--------------|----------|--------|-------|
| **NEUTRAL** | 53% | +40pp | **OPTIMAL** |
| ALIGNED with trade | 20% | -24pp | AVOID |
| OPPOSITE to trade | 35% | -9pp | Moderate |

**Paradox Explanation:** NEUTRAL H1 indicates a transition zone where price is consolidating. This creates less crowded conditions and the zone becomes a decision point rather than a continuation area.

---

### LONG-Specific Edges

#### Volume Delta Magnitude

| Magnitude | Win Rate | Effect | Notes |
|-----------|----------|--------|-------|
| Q1-Q2 (Low) | 41% | -3pp | Weak momentum |
| Q3 (Medium) | 45% | +1pp | Average |
| **Q4-Q5 (High)** | 57% | **+13pp** | **Strong momentum** |

**Rule for LONG:** Look for high-magnitude volume delta (Q4-Q5)

#### Volume ROC

| Condition | Win Rate | Effect | Notes |
|-----------|----------|--------|-------|
| < 0% | 42% | -2pp | Declining volume |
| 0% - 30% | 44% | 0pp | Normal |
| **≥ 30%** | 52% | **+8pp** | **Momentum confirmation** |
| ≥ 50% | 55% | +11pp | Strong momentum |

---

### SHORT-Specific Edges (Note the Paradoxes!)

#### Volume Delta Sign (PARADOX - 10.7pp effect)

| Delta Sign | Win Rate | Effect | Notes |
|------------|----------|--------|-------|
| NEGATIVE | 40% | -4pp | Expected but worse |
| **POSITIVE** | 51% | **+11pp** | **Exhausted buyers** |

**Paradox Explanation:** For SHORT trades, POSITIVE volume delta indicates buyers are exhausted. They're still buying but price isn't moving up - a sign of distribution.

#### CVD Slope (PARADOX - 15-27pp effect)

| CVD Direction | Win Rate | Effect | Notes |
|---------------|----------|--------|-------|
| NEGATIVE | 38% | -6pp | Expected but worse |
| FLAT | 44% | 0pp | Neutral |
| **POSITIVE** | 54% | **+10pp** | **Exhaustion signal** |
| **EXTREME_POS** | 62% | **+18pp** | **Strong exhaustion** |

**Paradox Explanation:** Extreme positive CVD slope for SHORT entries catches the end of buying exhaustion.

#### SMA Configuration (PARADOX - 9-14pp effect)

| SMA Config | Win Rate | Effect | Notes |
|------------|----------|--------|-------|
| BEARISH | 39% | -5pp | Expected but worse |
| **BULLISH** | 53% | **+14pp** | **Failed rally setup** |
| Price ABOVE_BOTH | 54% | +14pp | Catching extended rally |

**Paradox Explanation:** Entering SHORT when SMA is BULLISH catches failed rallies at extended levels.

---

## 10-Factor Health Score System

### Factor Breakdown

| # | Factor | Points | LONG Healthy | SHORT Healthy |
|---|--------|--------|--------------|---------------|
| 1 | H4 Structure | 1 | BULL or NEUTRAL | BEAR or NEUTRAL |
| 2 | H1 Structure | 1 | BULL or NEUTRAL | BEAR or NEUTRAL |
| 3 | M15 Structure | 1 | BULL or NEUTRAL | BEAR or NEUTRAL |
| 4 | M5 Structure | 1 | BULL or NEUTRAL | BEAR or NEUTRAL |
| 5 | Volume ROC | 1 | > +20% | > +20% |
| 6 | Volume Delta | 1 | POSITIVE | NEGATIVE |
| 7 | CVD Direction | 1 | RISING | FALLING |
| 8 | SMA Alignment | 1 | SMA9 > SMA21 | SMA9 < SMA21 |
| 9 | SMA Spread | 1 | WIDENING | WIDENING |
| 10 | VWAP Position | 1 | ABOVE VWAP | BELOW VWAP |

### Score Interpretation

| Score | Label | Win Rate* | Recommendation |
|-------|-------|-----------|----------------|
| 8-10 | STRONG | ~55% | High probability - proceed |
| 6-7 | MODERATE | ~48% | Proceed with confirmation |
| 4-5 | WEAK | ~42% | Additional confirmation required |
| 0-3 | CRITICAL | ~35% | Likely skip |

*Win rates are approximate and vary by model

### Health Score Correlation

**Validated Finding:**
- Average health score for WINNERS: 6.8
- Average health score for LOSERS: 5.2
- **Recommended threshold: Health ≥ 6 for HIGH confidence**

---

## Zone Ranking System

### Zone Score → Rank Mapping

| Rank | Score Range | Description | Win Rate* |
|------|-------------|-------------|-----------|
| L5 | ≥ 12.0 | BEST - Highest confluence | ~55% |
| L4 | 9.0 - 11.99 | GOOD - Strong confluence | ~50% |
| L3 | 6.0 - 8.99 | MODERATE - Average | ~45% |
| L2 | 3.0 - 5.99 | LOW - Weak confluence | ~40% |
| L1 | < 3.0 | WORST - Minimal confluence | ~35% |

### Zone Quality Recommendation

| Rank | Action |
|------|--------|
| L5 | Trade with standard stops |
| L4 | Trade with standard stops |
| L3 | Require extra confirmation |
| L2 | Consider skipping or tight stops |
| L1 | Generally skip |

---

## Stop Type Analysis

### Stop Performance by Type

| Stop Type | Description | Win Rate | Best For |
|-----------|-------------|----------|----------|
| Zone Buffer (+5%) | Zone edge + 5% buffer | 45% | All models |
| Prior M5 H/L | Previous M5 bar extreme | 48% | EPCH1/EPCH3 |
| Prior M1 H/L | Previous M1 bar extreme | 46% | Scalping |
| M5 ATR (1.1x) | 1.1 × M5 ATR from entry | 46% | Volatile tickers |
| M15 ATR (1.1x) | 1.1 × M15 ATR from entry | 44% | Swing trades |
| Fractal | Williams fractal swing | 44% | EPCH2/EPCH4 |

### Stop Recommendation by Model

| Model | Recommended Stop | Rationale |
|-------|------------------|-----------|
| EPCH1 | Prior M5 H/L | Continuation needs structure |
| EPCH2 | Zone Buffer | Rejection uses zone as stop |
| EPCH3 | Prior M5 H/L | Secondary continuation |
| EPCH4 | Zone Buffer + Fractal | Rejection with structure |

---

## Decision Framework

### Step-by-Step Analysis Workflow

```
1. UNIVERSAL FILTERS (Must Pass)
   ├── Candle Range ≥ 0.15%? ──────────── If NO → SKIP
   └── Zone Rank ≥ L3? ────────────────── If NO → Extra caution

2. DIRECTION CHECK
   ├── LONG Analysis:
   │   ├── Volume Delta magnitude Q4-Q5? ── +13pp
   │   ├── Volume ROC ≥ 30%? ───────────── +8pp
   │   └── H1 Structure NEUTRAL? ────────── +40pp
   │
   └── SHORT Analysis (Watch for paradoxes):
       ├── Volume Delta POSITIVE? ───────── +11pp (PARADOX)
       ├── CVD Slope POSITIVE? ──────────── +10pp (PARADOX)
       ├── SMA Config BULLISH? ──────────── +14pp (PARADOX)
       └── H1 Structure NEUTRAL? ────────── +40pp

3. HEALTH SCORE ASSESSMENT
   ├── Score 8-10: HIGH confidence
   ├── Score 6-7: MEDIUM confidence
   └── Score < 6: LOW confidence (consider skipping)

4. ZONE QUALITY CHECK
   ├── L5/L4: Standard entry
   ├── L3: Need extra confirmation
   └── L1/L2: Generally skip

5. FORMULATE RECOMMENDATION
   ├── Entry triggers (what must happen)
   ├── Invalidation levels (where setup fails)
   └── Stop placement (based on model type)
```

---

## Key Paradoxes Summary

### Why Counter-Intuitive Signals Work

| Signal | Expected | Actual Winner | Why It Works |
|--------|----------|---------------|--------------|
| Vol Delta for SHORT | NEGATIVE | **POSITIVE** | Exhausted buyers = distribution |
| CVD for SHORT | FALLING | **RISING/EXTREME** | Buying exhaustion at top |
| SMA for SHORT | BEARISH | **BULLISH** | Failed rally = reversal |
| H1 Structure | ALIGNED | **NEUTRAL** | Transition = decision zone |
| Order Flow | WITH flow | **AGAINST flow** | Captures reversals |

### Practical Application

**For SHORT trades, LOOK FOR:**
1. Price extended after rally (SMA BULLISH)
2. Buyers still trying but failing (Vol Delta POSITIVE)
3. Cumulative buying exhausted (CVD POSITIVE)
4. H1 in transition (NEUTRAL)

**These signals together indicate exhaustion, not strength.**

---

## Sample Analysis Prompts

### Entry Analysis Template

```
Analyze this setup using the Epoch framework:

SETUP:
- Ticker: [SYMBOL]
- Direction: [LONG/SHORT]
- Zone Type: [PRIMARY/SECONDARY]
- Model: [EPCH_01/02/03/04]
- Zone Rank: [L1-L5]

CURRENT INDICATORS:
- Candle Range: [X.XX%]
- Health Score: [X/10]
- H1 Structure: [BULL/BEAR/NEUTRAL]
- Volume Delta: [POSITIVE/NEGATIVE, magnitude]
- Volume ROC: [XX%]
- CVD Slope: [RISING/FALLING/FLAT]
- SMA Config: [BULLISH/BEARISH/NEUTRAL]

Apply the validated edges and paradoxes.
What is your confidence level and recommendation?
```

### Exit Analysis Template

```
Evaluate this position for exit:

POSITION:
- Ticker: [SYMBOL]
- Direction: [LONG/SHORT]
- Current P&L: [X.X R]
- Time in trade: [X minutes]

CURRENT STATE:
- Distance to target: [X%]
- Health Score now: [X/10]
- Structure change?: [Yes/No]
- Volume shift?: [Yes/No]

What is your recommendation?
[FULL EXIT / PARTIAL / HOLD / TRAIL STOP]
```

---

## Quick Reference: Common Scenarios

### Scenario 1: HIGH Confidence LONG

✅ Candle Range ≥ 0.20%
✅ H1 Structure = NEUTRAL
✅ Vol Delta = HIGH magnitude (Q4-Q5)
✅ Vol ROC ≥ 30%
✅ Health Score ≥ 8
✅ Zone Rank = L4-L5

**Action:** Enter with standard stop at zone buffer

### Scenario 2: HIGH Confidence SHORT (Paradox Setup)

✅ Candle Range ≥ 0.15%
✅ H1 Structure = NEUTRAL
✅ Vol Delta = **POSITIVE** (paradox)
✅ CVD Slope = **POSITIVE** (paradox)
✅ SMA Config = **BULLISH** (paradox)
✅ Health Score ≥ 6

**Action:** Enter SHORT - catching exhaustion

### Scenario 3: SKIP Conditions

❌ Candle Range < 0.12% (Absorption)
❌ Zone Rank = L1
❌ Health Score < 4
❌ H1 Structure = ALIGNED (not NEUTRAL)

**Action:** Do not enter - wait for better setup

---

## Data Sources Reference

| Data Type | Source | Refresh |
|-----------|--------|---------|
| Zone Data | Supabase: zones, setups | Daily |
| Market Data | Polygon.io API | Real-time |
| Indicator Edges | 03_indicators/python/results/ | Weekly |
| Model Stats | ai_model_stats table | Weekly |
| Health Factors | Entry calculation | Real-time |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 20, 2026 | Initial release with validated edges |

---

*This framework is based on statistical analysis of 2,788 trades. All edges have p < 0.05 and effect sizes ≥ 3pp. Paradoxical findings have been validated across multiple market conditions.*
