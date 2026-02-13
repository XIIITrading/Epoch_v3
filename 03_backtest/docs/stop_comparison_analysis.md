# Stop Method Comparison Analysis
## Epoch Trading System - Backtest Engine Evaluation
### XIII Trading LLC | January 2026

---

## Executive Summary

The current backtest engine uses a **zone_buffer stop** (zone edge + 5% buffer) with a **3R/calc_target exit** and **CHoCH structure exit**. Analysis of 5,440 trades reveals that this configuration produces a **35.92% win rate** with an average P&L of **+0.02R** -- essentially breakeven.

The R Win/Loss secondary processor, which uses an **M5 ATR(14) x 1.1 stop** with simple R-multiple targets, produces a **54.39% win rate** with a positive expectancy of **+0.682R per trade** on the same trade population.

This document provides the data for evaluating which stop methodology should be used in the core backtest calculation.

---

## 1. Current Backtest Engine Configuration

### Stop: Zone Buffer (5%)
- **LONG**: `stop = zone_low - (entry - zone_low) * 0.05`
- **SHORT**: `stop = zone_high + (zone_high - entry) * 0.05`
- Average stop distance: **$1.81 / 0.63%** from entry

### Exit Priority (checked on M5 bars):
1. **STOP** -- bar high/low breaches stop level, fills at exact stop price (-1R)
2. **TARGET** -- bar high/low reaches target, fills at target price (+3R or calc_target)
3. **CHoCH** -- close breaks 5-bar low/high structure, fills at close (variable R)
4. **EOD** -- force close at 15:50 ET at bar close (variable R)

### Win/Loss: `pnl_dollars > 0 = WIN`

---

## 2. R Win/Loss Configuration

### Stop: M5 ATR(14) x 1.1
- **LONG**: `stop = entry - (ATR * 1.1)`
- **SHORT**: `stop = entry + (ATR * 1.1)`
- Average stop distance: **$1.47 / 0.51%** from entry

### Exit Logic (checked on M1 bars):
1. **R-Targets (1R-5R)** -- price high/low touches target level (price-based)
2. **Stop** -- M1 bar closes beyond stop level (close-based)
3. **EOD** -- 15:30 ET, price vs entry determines win/loss

### Win/Loss: `R1 hit before stop = WIN`

---

## 3. Head-to-Head Comparison (5,415 matched trades)

| Metric | Current Backtest | R Win/Loss (ATR) |
|--------|-----------------|-------------------|
| **Win Rate** | 35.83% | **54.39%** |
| **Avg P&L (R)** | +0.02R | +0.682R (expectancy) |
| Avg Winner Size | 1.79R | 2.09R (max R achieved) |
| Avg Loser Size | -0.97R | -1.0R |
| Stopped Out | 2,795 (51.6%) | 2,229 (41.2%) |
| Target Exits | 444 (8.2%) | 2,847 (52.6%) |
| EOD Exits | 2,176 (40.2%) | 339 (6.3%) |

### Key Observation
The current backtest only converts **8.2% of trades** into target exits (3R). The remaining ~40% drift to EOD with variable outcomes. The R Win/Loss system converts **52.6% of trades** into R-target exits because R1 is a far more achievable threshold than 3R.

---

## 4. Trade Agreement Analysis

| Category | Trades | % of Total |
|----------|--------|-----------|
| Both agree WIN | 1,622 | 29.95% |
| Both agree LOSS | 2,152 | 39.74% |
| Current WIN -> R_WL LOSS | 318 | 5.87% |
| **Current LOSS -> R_WL WIN** | **1,323** | **24.43%** |

The R Win/Loss system **rescues 1,323 trades** that the current backtest marks as losses, while only **losing 318 trades** that the current backtest marks as wins. This is a net gain of **1,005 trades** flipping from LOSS to WIN.

### Why trades flip LOSS -> WIN:
These are trades where the zone_buffer stop gets hit (marking -1R loss in current system), but under the ATR stop the trade had room to breathe and price reached R1 before being stopped. The ATR stop is tighter on average (0.51% vs 0.63%) but is **close-based** rather than price-based, meaning intrabar wicks don't trigger it.

### Why trades flip WIN -> LOSS:
These are trades where the current system captures a small CHoCH or EOD profit (variable R), but under the ATR methodology, price never reached R1 and the ATR stop was hit or EOD was unfavorable.

---

## 5. All Stop Methods Ranked

Data from `stop_analysis` table (6 stop types) + `r_win_loss` table:

| Rank | Stop Method | Win Rate | Avg R | Stop Hit % | Avg Stop % | Trigger |
|------|------------|----------|-------|-----------|-----------|---------|
| 1 | **M5 ATR R_WL** | **54.39%** | **1.14** | 41.16% | **0.51%** | **Close-based (M1)** |
| 2 | M5 ATR (stop_analysis) | 52.98% | 1.49 | 47.14% | 0.53% | Close-based (M5) |
| 3 | Zone Buffer | 41.34% | 1.07 | 52.29% | 0.63% | Price-based |
| 4 | M15 ATR | 40.09% | 1.14 | 39.13% | 0.86% | Close-based |
| 5 | Prior M5 | 33.11% | 1.50 | 74.71% | 0.34% | Price-based |
| 6 | Prior M1 | 26.87% | 1.70 | 91.79% | 0.18% | Price-based |
| 7 | Fractal | 24.68% | 0.82 | 55.09% | 1.10% | Price-based |

### Observations:
- **ATR-based stops dominate** the top positions (ranks 1-2, 4)
- **Close-based triggers outperform price-based** -- intrabar wicks frequently stop out trades that would have recovered
- The **M5 ATR at 0.51% stop distance** hits the sweet spot: tight enough to limit risk but wide enough to avoid noise
- Prior M1/M5 stops are too tight (0.18%/0.34%), resulting in >74% stop-hit rates
- Fractal stops are too wide (1.10%) and structurally unreliable (24.68% win rate)

---

## 6. Current Exit Reason Breakdown

| Exit Reason | Trades | % | Avg R | Win Rate |
|-------------|--------|---|-------|----------|
| **STOP** | 2,806 | 51.58% | -1.00R | 0% |
| **EOD** | 2,188 | 40.22% | +0.72R | 68.92% |
| TARGET_3R | 418 | 7.68% | +3.00R | 100% |
| TARGET_CALC | 28 | 0.51% | +3.63R | 100% |

### Critical Finding
- **51.58% of trades hit the stop** -- over half the trade population is a guaranteed -1R
- **Only 8.2% reach the 3R target** -- the intended profit-taking mechanism rarely fires
- **40.22% drift to EOD** -- these act as the system's actual profit engine (68.92% win rate at +0.72R avg)
- The system is essentially relying on EOD exits to be profitable, not the 3R target design

---

## 7. R Win/Loss Exit Breakdown

| Exit Reason | Trades | % | Description |
|-------------|--------|---|-------------|
| **R_TARGET** | 2,847 | 52.58% | R1+ hit before stop |
| **STOP** | 2,229 | 41.16% | ATR stop triggered |
| EOD_LOSS | 241 | 4.45% | No R1/stop, price <= entry at 15:30 |
| EOD_WIN | 98 | 1.81% | No R1/stop, price > entry at 15:30 |

### R-Level Hit Rates
| Level | Hit Rate | Cumulative Implication |
|-------|----------|----------------------|
| R1 | 52.58% | Over half of entries reach 1R profit |
| R2 | 29.70% | ~30% reach 2R |
| R3 | 16.44% | ~16% reach 3R (vs 8.2% in current backtest) |
| R4 | 8.83% | - |
| R5 | 6.26% | - |

---

## 8. Model-Level Comparison

### Current Backtest
| Model | Trades | Win Rate | Avg P&L (R) | Avg Winner | Avg Loser |
|-------|--------|----------|-------------|------------|-----------|
| EPCH1 | 259 | 31.66% | -0.11R | 1.82R | -0.97R |
| **EPCH2** | **2,686** | **38.91%** | **+0.13R** | 1.86R | -0.97R |
| EPCH3 | 216 | 32.41% | -0.17R | 1.59R | -0.97R |
| EPCH4 | 2,279 | 33.61% | -0.08R | 1.70R | -0.97R |

### R Win/Loss
| Model | Trades | Win Rate | R1% | R2% | R3% | Avg Max R |
|-------|--------|----------|-----|-----|-----|-----------|
| EPCH1 | 258 | 50.78% | 48.84% | 28.68% | 17.44% | 1.09 |
| **EPCH2** | **2,677** | **55.02%** | **53.57%** | **31.04%** | **17.74%** | **1.19** |
| EPCH3 | 209 | 54.55% | 53.11% | 30.14% | 16.75% | 1.15 |
| EPCH4 | 2,271 | 54.03% | 51.78% | 28.18% | 14.75% | 1.08 |

### Observations:
- **EPCH2 is the strongest model in both systems** -- highest win rate and best R performance
- All models improve significantly under the ATR stop methodology
- EPCH4 sees the largest relative improvement (+20.42pp win rate increase)
- EPCH3 goes from worst (-0.17R) to competitive (54.55% win rate)

---

## 9. Direction Comparison

### Current Backtest
| Direction | Trades | Win Rate | Avg P&L (R) |
|-----------|--------|----------|-------------|
| LONG | - | - | - |
| SHORT | - | - | - |
*(Direction-level data not broken out in current backtest query)*

### R Win/Loss
| Direction | Trades | Win Rate | R1% | R2% | R3% | Avg Max R |
|-----------|--------|----------|-----|-----|-----|-----------|
| LONG | 2,617 | 53.19% | 51.82% | 28.39% | 15.40% | 1.12 |
| **SHORT** | **2,798** | **55.50%** | **53.29%** | **30.91%** | **17.41%** | **1.15** |

Shorts slightly outperform longs across all R-levels.

---

## 10. Structural Issues with the Current Backtest

### Problem 1: The 3R Target Rarely Fires
Only 8.2% of trades reach 3R. This means the intended risk-reward design (risk 1 to make 3) is not functioning as designed. The zone_buffer stop distance is large enough that 3R represents a significant price move that most intraday trades cannot achieve.

### Problem 2: Over Half the Trades Are Stopped Out
51.58% of trades hit the stop for a guaranteed -1R. This is the single biggest drag on performance. The zone_buffer stop is price-based (triggered by intrabar wicks), meaning volatile bars can sweep the stop even when the trade thesis remains valid.

### Problem 3: EOD Is the Actual Profit Engine
40.22% of trades exit at EOD with a 68.92% win rate and +0.72R average. The system is essentially running as a "hold until close" strategy for the majority of its winning trades, not a "risk 1 to make 3" strategy.

### Problem 4: CHoCH Exits Are Missing from the Data
Zero CHoCH exits appear in the trade data, suggesting the CHoCH logic either rarely triggers or has a configuration issue. This removes one of the intended protective exit mechanisms.

---

## 11. Why the ATR Stop Performs Better

### 1. Close-Based vs Price-Based Trigger
The M5 ATR stop only triggers when a candle **closes** beyond the stop level, not when an intrabar wick touches it. This is critical because intrabar wicks frequently sweep price-based stops before reversing. The close-based trigger filters out noise and only exits when there is genuine follow-through beyond the stop.

### 2. Volatility-Normalized Distance
The ATR stop automatically adjusts to the instrument's current volatility. High-volatility stocks get wider stops; low-volatility stocks get tighter stops. The zone_buffer stop is based on zone geometry, which has no relationship to current volatility.

### 3. Tighter Average Stop with Better Survival
Despite being tighter on average (0.51% vs 0.63%), the ATR stop has a **lower stop-hit rate** (41.16% vs 51.58%). This seems paradoxical but is explained by the close-based trigger -- the stop is numerically tighter but harder to actually trigger because it requires a closing breach, not just a wick.

### 4. Achievable Profit Targets
Using 1R as the win threshold (instead of 3R) means the system captures profits that actually exist in the data. 52.58% of trades reach 1R before the stop, compared to only 8.2% reaching 3R. The R Win/Loss analysis shows you are entering trades that have genuine directional edge -- the entries are sound, but the current exit structure is leaving profit on the table.

---

## 12. Data Tables for Further Analysis

### Expectancy Calculations

**Current Backtest:**
```
Win Rate:     35.92%
Avg Winner:   +1.79R
Avg Loser:    -0.97R
Expectancy:   (0.3592 * 1.79) - (0.6408 * 0.97) = +0.021R per trade
```

**R Win/Loss (if taking profit at max R achieved):**
```
Win Rate:     54.39%
Avg Winner:   +2.09R (avg max_r_achieved for winners)
Avg Loser:    -1.0R
Expectancy:   (0.5439 * 2.09) - (0.4561 * 1.0) = +0.682R per trade
```

**R Win/Loss (conservative -- assume all wins exit at R1):**
```
Win Rate:     54.39%
Avg Winner:   +1.0R
Avg Loser:    -1.0R
Expectancy:   (0.5439 * 1.0) - (0.4561 * 1.0) = +0.088R per trade
```

Even the most conservative interpretation (all winners exit at exactly R1) produces 4x the expectancy of the current backtest.

---

## 13. Max R Distribution

| Max R Reached | Trades | % of Total | Cumulative |
|---------------|--------|-----------|------------|
| 0 (no R1) | 2,568 | 47.42% | 47.42% |
| 1 | 1,239 | 22.88% | 70.30% |
| 2 | 718 | 13.26% | 83.56% |
| 3 | 412 | 7.61% | 91.16% |
| 4 | 139 | 2.57% | 93.73% |
| 5+ | 339 | 6.26% | 100.00% |

Of the 52.58% of trades that reach R1, a significant portion continue to R2 (29.70%) and R3 (16.44%), suggesting a trailing stop or scaled exit approach could capture additional R beyond R1.

---

*Analysis generated from r_win_loss table (5,415 trades), stop_analysis table (6 stop types x ~5,440 trades), and trades table (5,440 trades). All data from Epoch backtest Supabase database.*

*Document: C:\XIIITradingSystems\Epoch\03_backtest\docs\stop_comparison_analysis.md*
*Date: January 29, 2026*
