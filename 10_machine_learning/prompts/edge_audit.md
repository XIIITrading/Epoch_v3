# EPOCH Weekly Edge Audit Prompt

## Context

You are analyzing the EPOCH 2.0 trading system's performance for the past week.
Use the canonical win condition: M5 ATR(14) x 1.1, close-based stop.
All outcomes reference `trades_m5_r_win.is_winner`.

## Data Provided

1. **trades_YYYYMMDD.json** - Daily trade data with:
   - Entry/exit details
   - Canonical outcomes (is_winner, pnl_r)
   - Entry indicators (health_score, structure, volume metrics)

2. **edge_analysis_YYYYMMDD.md** - Edge summary with:
   - Validated edges and effect sizes
   - Baseline win rate
   - Statistical thresholds

3. **system_metrics_YYYYMMDD.json** - Performance metrics:
   - 30-day and 7-day performance
   - Model breakdown
   - Direction breakdown

4. **weekly_report_YYYYMMDD.md** - Weekly aggregation:
   - Daily breakdown
   - Model performance
   - Edge effectiveness
   - Health score distribution

## Analysis Request

### 1. Performance Review
- Compare this week to 30-day baseline
- Identify any significant deviations
- Note model-specific performance changes

### 2. Edge Validation
- Are validated edges still holding? (H1 NEUTRAL, Absorption skip, Vol Delta paradox)
- Any edges showing degradation?
- New potential edges emerging?

### 3. Indicator Patterns
- Which indicators predicted winners vs losers this week?
- Any unusual indicator combinations?
- Health score distribution for winners vs losers?

### 4. Hypothesis Generation
Based on this week's data, propose 1-2 testable hypotheses:
- What patterns show promise?
- What sample size needed to validate?
- What would prove/disprove the hypothesis?

### 5. Action Items
- What should be investigated further?
- Any parameters to consider adjusting?
- Risk management observations?

## Output Format

Please structure your response as:

1. **Executive Summary** (2-3 sentences)
2. **Performance Analysis** (bullet points)
3. **Edge Status** (table format)
4. **New Hypotheses** (structured proposals)
5. **Recommended Actions** (prioritized list)

---

*Paste data below this line*
