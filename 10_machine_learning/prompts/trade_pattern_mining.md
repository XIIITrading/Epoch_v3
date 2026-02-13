# EPOCH Trade Pattern Mining Prompt

## Context

You are analyzing EPOCH 2.0 trade data to discover recurring patterns that may indicate
new edges or confirm existing ones. All outcomes use `trades_m5_r_win.is_winner`.

## Data Provided

Trade records with the following fields:
- **Identity**: trade_id, date, ticker, model, direction
- **Zone**: zone_type, zone_high, zone_low
- **Entry/Exit**: entry_price, entry_time, exit_price, exit_time, exit_reason
- **Outcome**: is_winner, outcome (WIN/LOSS), pnl_r, reached_2r, reached_3r
- **Indicators**: health_score, h1_structure, m15_structure, m5_structure
- **Volume**: vol_roc, vol_delta, cvd_slope
- **Price**: sma_spread, sma_momentum_label, vwap

## Analysis Tasks

### 1. Winner/Loser Profile
Create a statistical profile of winners vs losers:
- Which indicator values are most common in winners?
- Which indicator values are most common in losers?
- Are there clear separation boundaries?

### 2. Model-Specific Patterns
For each entry model (EPCH1-4):
- What conditions produce the best results?
- What conditions should be avoided?
- Any model-specific indicator interactions?

### 3. Time-Based Patterns
- Do certain times of day produce better results?
- Are there day-of-week effects?
- Entry time vs outcome correlation?

### 4. Cluster Analysis
Group trades by indicator combinations:
- Which 2-3 indicator combinations have the highest win rate?
- Which combinations have the worst win rate?
- Are there natural clusters in the data?

### 5. Sequence Patterns
- Do winners tend to cluster (momentum days)?
- After a losing trade, what happens next?
- Are there reversal patterns across consecutive trades?

## Output Format

1. **Key Findings** (top 3-5 patterns with statistical support)
2. **Winner Profile** (table of indicator distributions)
3. **Loser Profile** (table of indicator distributions)
4. **Proposed Filters** (conditions that would improve win rate)
5. **Caveats** (sample size concerns, potential overfitting risks)

## Statistical Requirements

- Report sample sizes for every claim
- Note when samples are below 30 (unreliable)
- Calculate effect sizes (percentage point differences)
- Flag any pattern that could be coincidental (p > 0.05)

---

*Paste trade data below this line*
