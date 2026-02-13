# EPOCH ML Analysis Report
## February 01, 2026

> This report explains your trading system's statistical edges in plain language.
> Every claim is backed by data from your actual trades in `trades_m5_r_win`.
> Read it front-to-back -- it's designed to teach as it goes.

---

## How to Read This Report

Before diving in, here are the key terms you'll see throughout:

| Term | What It Means |
|------|---------------|
| **Win Rate** | Percentage of trades that hit 1R profit before the stop was triggered |
| **Baseline** | Your overall win rate across ALL trades -- the number to beat |
| **Effect (pp)** | "Percentage points" -- how much better or worse than baseline. +5pp means the win rate is 5 points higher than average |
| **p-value** | The probability this result happened by pure chance. Below 0.05 = statistically significant. Think of it as a confidence meter -- lower is better |
| **Chi-squared** | The statistical test used to compare two groups. You don't need to understand the math -- just look at the p-value it produces |
| **Sample Size (N)** | How many trades are in the group. More trades = more trustworthy. We require at least 30 for any conclusion |
| **Significant** | Passes ALL three tests: p < 0.05, effect > 3pp, and N >= 30 |

---

## Your Baseline Performance

This is your system's overall performance -- the benchmark everything else is measured against.

| Metric | Value | What It Means |
|--------|-------|---------------|
| **Total Trades** | 4,800 | Number of trades in this analysis window |
| **Win Rate** | 53.7% | 4,800 trades, 2,578 winners |
| **Average R** | +0.746 | Each trade averages +0.746R profit. Positive = profitable system |
| **Std Dev R** | 1.886 | How much individual trades vary. Higher = more volatile results |
| **Period** | 2026-01-05 to 2026-01-30 | Date range of trades analyzed |

**Bottom line**: Your system wins 53.7% of the time with an average return of +0.746R per trade. Every edge below is compared against this 53.7% baseline.

---

## Health Check: Your Existing Validated Edges

These are the edges you previously identified and built into your trading rules.
This section checks whether they still hold up against fresh data.


---

## Newly Discovered Edges

The system scanned 12 indicator columns across all 4,800 trades. Below are the groups that showed a statistically significant difference from your baseline.

**What "significant" means**: Each of these passed three tests:
1. The effect is large enough to matter (> 3.0pp)
2. The result is unlikely to be random chance (p < 0.05)
3. There are enough trades to trust the result (N >= 30)


### 1. cont_score = STRONG (8-10) [POSITIVE (trade)]

- **Win Rate**: 72.3% vs 53.7% baseline
- **Effect**: +18.6pp -- massive -- win rate is 18.6 percentage points higher than your overall average
- **Evidence**: p = 0.0163 -- statistically significant (less than 5% chance this is random)
- **Sample**: MEDIUM confidence (47 trades -- usable but monitor closely)


**Interpretation**: When the Continuation Score (the composite of all 10 indicators, formerly called "health score") is 8 or above, your system dramatically outperforms. This makes intuitive sense -- when everything is aligned in one direction, continuation trades work especially well. The sample is small (MEDIUM confidence) so this needs monitoring, but the effect size is huge.



**By Direction** (Is the STRONG edge biased toward LONGs or SHORTs?)

| Direction | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| LONG | 24 | 58.3% | 52.8% | +5.5pp | +1.071 |
| SHORT | 23 | 87.0% | 54.5% | +32.5pp | +1.348 |

**By Zone Type** (Primary vs Secondary)

| Zone Type | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| PRIMARY | 33 | 72.7% | 55.1% | +17.6pp | +1.324 |
| SECONDARY | 14 | 71.4% | 52.0% | +19.4pp | +0.929 |

**By Entry Model** (Continuation vs Rejection -- is the score biased?)

| Model Type | Trades | WR | Baseline | Effect | Avg R |
|------------|--------|----|---------:|-------:|------:|
| CONTINUATION | 11 | 81.8% | 53.7% | +28.1pp | +1.455 |
| REJECTION | 36 | 69.4% | 53.7% | +15.7pp | +1.131 |


### 2. cont_score = MODERATE (6-7) [POSITIVE (trade)]

- **Win Rate**: 63.2% vs 53.7% baseline
- **Effect**: +9.5pp -- meaningful -- win rate is 9.5 percentage points higher than your overall average
- **Evidence**: p = 0.0000 -- extremely strong evidence (less than 0.1% chance this is random noise)
- **Sample**: HIGH confidence (996 trades -- large enough sample to trust)


**Interpretation**: Continuation Scores of 6-7 also show a clear advantage. With nearly 1,000 trades, this is a reliable finding. It suggests your indicator framework genuinely captures something meaningful about trade quality -- specifically, how well conditions support a continuation move.



**By Direction** (Is the MODERATE edge biased toward LONGs or SHORTs?)

| Direction | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| LONG | 404 | 59.9% | 52.8% | +7.1pp | +1.041 |
| SHORT | 592 | 65.4% | 54.5% | +10.9pp | +1.467 |

**By Zone Type** (Primary vs Secondary)

| Zone Type | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| PRIMARY | 524 | 59.4% | 55.1% | +4.3pp | +1.213 |
| SECONDARY | 472 | 67.4% | 52.0% | +15.4pp | +1.384 |

**By Entry Model** (Continuation vs Rejection -- is the score biased?)

| Model Type | Trades | WR | Baseline | Effect | Avg R |
|------------|--------|----|---------:|-------:|------:|
| CONTINUATION | 120 | 60.8% | 53.7% | +7.1pp | +1.123 |
| REJECTION | 876 | 63.5% | 53.7% | +9.8pp | +1.318 |


### 3. m15_structure = BEAR [NEGATIVE (skip/avoid)]

- **Win Rate**: 45.1% vs 53.7% baseline
- **Effect**: -8.6pp -- meaningful -- win rate is 8.6 percentage points lower than your overall average
- **Evidence**: p = 0.0000 -- extremely strong evidence (less than 0.1% chance this is random noise)
- **Sample**: HIGH confidence (1553 trades -- large enough sample to trust)


**Interpretation**: When the M15 timeframe shows bearish structure, your trades underperform significantly. This is a strong skip signal -- regardless of other factors, M15 BEAR structure is a headwind.


### 4. stop_distance_bucket = TIGHT (<0.12%) [POSITIVE (trade)]

- **Win Rate**: 60.7% vs 53.7% baseline
- **Effect**: +7.0pp -- meaningful -- win rate is 7.0 percentage points higher than your overall average
- **Evidence**: p = 0.0271 -- statistically significant (less than 5% chance this is random)
- **Sample**: HIGH confidence (275 trades -- large enough sample to trust)


**Interpretation**: Tight zones (very small stop distance) perform well. This may be because tight zones represent precise, high-conviction levels where price respects the zone boundary cleanly. Note: this contradicts the original "Absorption Zone Skip" edge which claimed small zones should be skipped. The difference is likely due to the switch from `trades` to `trades_m5_r_win` win classification.


### 5. m15_structure = BULL [POSITIVE (trade)]

- **Win Rate**: 59.6% vs 53.7% baseline
- **Effect**: +5.9pp -- meaningful -- win rate is 5.9 percentage points higher than your overall average
- **Evidence**: p = 0.0001 -- extremely strong evidence (less than 0.1% chance this is random noise)
- **Sample**: HIGH confidence (1574 trades -- large enough sample to trust)


**Interpretation**: M15 bullish structure is a tailwind for your trades. This makes sense -- when the 15-minute chart agrees with your trade direction, you have structural support. Combined with the BEAR finding, M15 structure is clearly an important filter.


### 6. h1_structure = BEAR [POSITIVE (trade)]

- **Win Rate**: 59.1% vs 53.7% baseline
- **Effect**: +5.4pp -- meaningful -- win rate is 5.4 percentage points higher than your overall average
- **Evidence**: p = 0.0072 -- very strong evidence (less than 1% chance this is random)
- **Sample**: HIGH confidence (745 trades -- large enough sample to trust)


**Interpretation**: This is counterintuitive. Your original validated edge claimed H1 NEUTRAL was the sweet spot (+36pp). But with `trades_m5_r_win` as sole source, H1 BEAR actually shows a positive edge while NEUTRAL is flat. This suggests the original H1 NEUTRAL finding may have been an artifact of the old win calculation.


### 7. cont_score = WEAK (4-5) [NEGATIVE (skip/avoid)]

- **Win Rate**: 49.9% vs 53.7% baseline
- **Effect**: -3.8pp -- moderate -- win rate is 3.8 percentage points lower than your overall average
- **Evidence**: p = 0.0070 -- very strong evidence (less than 1% chance this is random)
- **Sample**: HIGH confidence (1677 trades -- large enough sample to trust)


**Interpretation**: When the Continuation Score drops to 4-5, performance falls below average. This is the mirror image of the STRONG/MODERATE findings -- fewer indicators aligned means weaker continuation conditions. These setups may actually be better suited for rejection plays.



**By Direction** (Is the WEAK edge biased toward LONGs or SHORTs?)

| Direction | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| LONG | 774 | 50.4% | 52.8% | -2.4pp | +0.714 |
| SHORT | 903 | 49.4% | 54.5% | -5.1pp | +0.467 |

**By Zone Type** (Primary vs Secondary)

| Zone Type | Trades | WR | Baseline | Effect | Avg R |
|-----------|--------|----|---------:|-------:|------:|
| PRIMARY | 831 | 51.4% | 55.1% | -3.7pp | +0.732 |
| SECONDARY | 846 | 48.3% | 52.0% | -3.7pp | +0.432 |

**By Entry Model** (Continuation vs Rejection -- is the score biased?)

| Model Type | Trades | WR | Baseline | Effect | Avg R |
|------------|--------|----|---------:|-------:|------:|
| CONTINUATION | 159 | 47.2% | 53.7% | -6.5pp | +0.490 |
| REJECTION | 1518 | 50.1% | 53.7% | -3.6pp | +0.591 |


### 8. sma_alignment = BULL [NEGATIVE (skip/avoid)]

- **Win Rate**: 49.9% vs 53.7% baseline
- **Effect**: -3.8pp -- moderate -- win rate is 3.8 percentage points lower than your overall average
- **Evidence**: p = 0.0026 -- very strong evidence (less than 1% chance this is random)
- **Sample**: HIGH confidence (2324 trades -- large enough sample to trust)


**Interpretation**: This is counterintuitive -- when SMA9 is above SMA21 (bullish alignment), your trades actually perform *worse* than average. This could mean your system works better in mean-reversion contexts rather than trend-following ones, or that "obvious" bullish alignment attracts crowded trades.


### 9. sma_alignment = BEAR [POSITIVE (trade)]

- **Win Rate**: 57.2% vs 53.7% baseline
- **Effect**: +3.5pp -- moderate -- win rate is 3.5 percentage points higher than your overall average
- **Evidence**: p = 0.0046 -- very strong evidence (less than 1% chance this is random)
- **Sample**: HIGH confidence (2476 trades -- large enough sample to trust)


**Interpretation**: Bearish SMA alignment (SMA9 below SMA21) shows better performance. Combined with the BULL alignment finding, this suggests your zone-based entries work better when going against the short-term SMA trend -- a contrarian signal.


---

## What Showed No Edge

These indicators were scanned but showed NO statistically significant difference from baseline. This is actually useful information -- it tells you what does NOT matter for your system.

| Indicator | What It Means |
|-----------|---------------|

| direction | LONG vs SHORT -- your system performs equally in both directions |

| h4_structure | H4 structure -- all trades were in NEUTRAL (only one value, can't compare) |

| m5_structure | M5 structure -- close to significant but didn't pass the threshold |

| model | EPCH1 vs EPCH2 vs EPCH3 vs EPCH4 -- no model is significantly better than another |

| sma_momentum_label | SMA momentum (WIDENING/NARROWING/STABLE) -- suggestive but not significant |

| vwap_position | Price above/below VWAP -- doesn't affect your win rate |

| zone_type | PRIMARY vs SECONDARY zones -- both perform similarly |


**Why this matters**: You can stop worrying about these factors as trade filters. They don't meaningfully affect your outcomes. Focus your attention on the indicators that DO show edges (health score, M15 structure, SMA alignment).

---

## Pending Actions (10 items)

These items need your decision before the system will act on them.


### Edges to Consider Removing

These existing validated edges have degraded and may be doing more harm than good:


- **Volume Delta Paradox**: Was stored as +13.0pp, now measures at -2.5pp
  - To remove: `python scripts/run_ml_workflow.py remove-edge "Volume Delta Paradox"`


### New Edges to Consider Adding

These were discovered by the hypothesis engine and passed all statistical tests:


- **health_tier=STRONG (8-10) (positive edge)** (Hypothesis H001)
  - Effect: +18.7pp | Win Rate: 72.3% | N = 47 | p = 0.016017
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H001`


- **health_tier=MODERATE (6-7) (positive edge)** (Hypothesis H002)
  - Effect: +9.5pp | Win Rate: 63.2% | N = 996 | p = 0.0
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H002`


- **m15_structure=BEAR (negative edge)** (Hypothesis H003)
  - Effect: -8.6pp | Win Rate: 45.1% | N = 1553 | p = 0.0
  - Action: SKIP/AVOID
  - To approve: `python scripts/run_ml_workflow.py approve-edge H003`


- **stop_distance_bucket=TIGHT (<0.12%) (positive edge)** (Hypothesis H004)
  - Effect: +7.1pp | Win Rate: 60.7% | N = 275 | p = 0.026236
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H004`


- **m15_structure=BULL (positive edge)** (Hypothesis H005)
  - Effect: +5.9pp | Win Rate: 59.6% | N = 1574 | p = 4.6e-05
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H005`


- **h1_structure=BEAR (positive edge)** (Hypothesis H006)
  - Effect: +5.4pp | Win Rate: 59.1% | N = 745 | p = 0.006717
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H006`


- **health_tier=WEAK (4-5) (negative edge)** (Hypothesis H007)
  - Effect: -3.8pp | Win Rate: 49.9% | N = 1677 | p = 0.00768
  - Action: SKIP/AVOID
  - To approve: `python scripts/run_ml_workflow.py approve-edge H007`


- **sma_alignment=BULL (negative edge)** (Hypothesis H008)
  - Effect: -3.8pp | Win Rate: 49.9% | N = 2324 | p = 0.002861
  - Action: SKIP/AVOID
  - To approve: `python scripts/run_ml_workflow.py approve-edge H008`


- **sma_alignment=BEAR (positive edge)** (Hypothesis H009)
  - Effect: +3.6pp | Win Rate: 57.2% | N = 2476 | p = 0.004121
  - Action: TRADE when active
  - To approve: `python scripts/run_ml_workflow.py approve-edge H009`


**Important**: You don't have to act on all of these at once. Review the findings above, ask questions, and approve/remove edges when you're confident in the decision.

---

## Summary & Recommendations


1. **Strong new edges found**: 5 indicator conditions show meaningful effects with HIGH confidence. The Continuation Score tiers and M15 structure are particularly promising -- both have large samples and strong effects.


2. **Continuation Score is your best filter**: Multiple score tiers show significant edges. Higher score = better continuation performance. This validates that your 10-factor indicator framework captures real trading edge -- specifically how well conditions support a continuation move. Consider using CONT score >= 6 as a minimum threshold, and favor continuation entries (EPCH1/3) when score is 8+. See `docs/indicator_playbook.md` for the full CONT/REJECT signal mapping.


3. **M15 structure matters**: Both BULL and BEAR M15 structure show significant effects in opposite directions. M15 BULL is a strong go signal, M15 BEAR is a strong skip signal. This is an actionable filter for your live trading.


4. **SMA alignment is contrarian**: Your system performs better when SMA alignment is BEAR (SMA9 < SMA21) and worse when it's BULL. This suggests your zone-based entries work better as mean-reversion plays rather than trend-following. Worth investigating further.


---

## Next Steps

- **Ask questions**: This report is your starting point for discussion in Claude Code. Ask about anything that's unclear.
- **Deep dive**: Want more detail on a specific edge? Ask me to run `test-hypothesis` with different date ranges.
- **Approve edges**: When you're ready, use `approve-edge` to promote new edges into your validated set.
- **Remove edges**: Use `remove-edge` to clean out degraded edges.
- **Re-run**: After making changes, run `python scripts/run_ml_workflow.py cycle` to see the updated picture.

---

*Report generated 2026-02-01 13:27:07 by narrative_report.py*
*Data source: trades_m5_r_win (sole source of truth)*
*Statistical method: Chi-squared test with Yates correction (falls back to Fisher's exact for small samples)*
