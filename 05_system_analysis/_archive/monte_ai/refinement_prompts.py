"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Prompt Templates for Indicator Refinement (CALC-010)
XIII Trading LLC
================================================================================

Specialized prompts for analyzing Continuation and Rejection qualification scores.

================================================================================
"""

# =============================================================================
# SYSTEM PROMPT FOR INDICATOR REFINEMENT ANALYSIS
# =============================================================================

REFINEMENT_ANALYSIS_SYSTEM_PROMPT = """You are Monte, an AI research assistant specializing in quantitative trading system analysis for XIII Trading LLC's Epoch Trading System.

## Your Current Task
Analyze the Indicator Refinement results (CALC-010) for Continuation and Rejection trade qualification scores and provide:
1. Key findings on score effectiveness
2. Indicator-level analysis
3. Optimization recommendations
4. Areas requiring further investigation

## Context
The Epoch Trading System uses two distinct scoring systems based on trade type:

**CONTINUATION TRADES (EPCH1, EPCH3)** - Score 0-10:
Trade with the trend at a zone, expecting price to continue in the trend direction.

Indicators (10 points total):
- CONT-01: MTF Alignment (0-4 pts) - Multi-timeframe structure alignment (M5->H4)
- CONT-02: SMA Momentum (0-2 pts) - 9/21 SMA spread widening in trade direction
- CONT-03: Volume Thrust (0-2 pts) - Above-average volume with aligned delta
- CONT-04: Pullback Quality (0-2 pts) - Healthy retracement depth and CVD divergence

Score Labels:
- STRONG: 8-10 (high probability continuation)
- GOOD: 6-7 (favorable setup)
- WEAK: 4-5 (proceed with caution)
- AVOID: 0-3 (skip trade)

**REJECTION TRADES (EPCH2, EPCH4)** - Score 0-11:
Counter-trend trade at a zone, expecting mean reversion/rejection.

Indicators (11 points total):
- REJ-01: Structure Divergence (0-3 pts) - Higher TF vs lower TF conflict
- REJ-02: SMA Exhaustion (0-2 pts) - Extended price beyond SMAs
- REJ-03: Delta Absorption (0-2 pts) - Aggressive volume absorbed at zone
- REJ-04: Volume Climax (0-2 pts) - Spike volume indicating exhaustion
- REJ-05: CVD Extreme (0-2 pts) - Extreme CVD reading with potential reversal

Score Labels:
- STRONG: 9-11 (high probability rejection)
- GOOD: 6-8 (favorable setup)
- WEAK: 4-5 (proceed with caution)
- AVOID: 0-3 (skip trade)

## Analysis Framework
When analyzing results, consider:
1. Win rate correlation with qualification score
2. Individual indicator contribution to winning trades
3. Score threshold optimization for trade filtering
4. Model-specific patterns (primary vs secondary zones)

## Output Format
Provide structured recommendations with:
- Finding (what the data shows)
- Statistical confidence (based on sample size)
- Recommendation (specific action)
- Priority (P1/P2/P3)
"""


# =============================================================================
# ANALYSIS TEMPLATES
# =============================================================================

CONTINUATION_ANALYSIS_TEMPLATE = """
## Continuation Trade Qualification Analysis

### Data Summary
{data_summary}

### Key Questions
1. Does the Continuation Score (0-10) predict win rate effectively?
2. Which indicators contribute most to winning trades?
3. What is the optimal score threshold for filtering?
4. Are there indicator combinations that signal higher probability?

### Required Output
- Score-to-win-rate correlation assessment
- Indicator importance ranking
- Recommended minimum score threshold
- Indicator weight adjustment suggestions
"""

REJECTION_ANALYSIS_TEMPLATE = """
## Rejection Trade Qualification Analysis

### Data Summary
{data_summary}

### Key Questions
1. Does the Rejection Score (0-11) predict win rate effectively?
2. Which indicators contribute most to winning rejection trades?
3. What is the optimal score threshold for filtering?
4. Do exhaustion indicators (Volume Climax, CVD Extreme) outperform others?

### Required Output
- Score-to-win-rate correlation assessment
- Indicator importance ranking
- Recommended minimum score threshold
- Key exhaustion signals to prioritize
"""

REFINEMENT_SYNTHESIS_TEMPLATE = """
## Comprehensive Indicator Refinement Analysis

You have been provided with Continuation and Rejection trade qualification results.

### Combined Data Summary
{data_summary}

### Synthesis Questions
1. Which trade type (Continuation vs Rejection) has better score predictiveness?
2. What are the key differences in indicator effectiveness between trade types?
3. What minimum score thresholds should be enforced for each trade type?
4. Which indicators should be weighted differently or removed?

### Required Output
1. **Executive Summary** (3-5 bullet points)
2. **Continuation Score Recommendations**
   - Threshold: Recommended minimum score
   - Indicators to prioritize
   - Indicators to de-weight or remove
3. **Rejection Score Recommendations**
   - Threshold: Recommended minimum score
   - Indicators to prioritize
   - Indicators to de-weight or remove
4. **Implementation Priority**
5. **Further Investigation Needed**
"""


# =============================================================================
# DATA FORMATTING TEMPLATES
# =============================================================================

CONTINUATION_DATA_FORMAT = """
### Continuation Score Statistics
- Total Trades: {total_trades:,}
- Overall Win Rate: {overall_win_rate:.1f}%
- Average Score: {avg_score:.1f}/10

### Win Rate by Score Label
| Label | Score Range | Trades | Win Rate | Lift vs Baseline |
|-------|-------------|--------|----------|------------------|
{score_label_table}

### Indicator Contribution (Winners vs Losers)
| Indicator | Max Pts | Winners Avg | Losers Avg | Delta |
|-----------|---------|-------------|------------|-------|
{indicator_table}
"""

REJECTION_DATA_FORMAT = """
### Rejection Score Statistics
- Total Trades: {total_trades:,}
- Overall Win Rate: {overall_win_rate:.1f}%
- Average Score: {avg_score:.1f}/11

### Win Rate by Score Label
| Label | Score Range | Trades | Win Rate | Lift vs Baseline |
|-------|-------------|--------|----------|------------------|
{score_label_table}

### Indicator Contribution (Winners vs Losers)
| Indicator | Max Pts | Winners Avg | Losers Avg | Delta |
|-----------|---------|-------------|------------|-------|
{indicator_table}
"""

COMBINED_DATA_FORMAT = """
### Overview Statistics
| Trade Type | Total Trades | Win Rate | Avg Score |
|------------|--------------|----------|-----------|
| Continuation | {cont_trades:,} | {cont_wr:.1f}% | {cont_avg:.1f}/10 |
| Rejection | {rej_trades:,} | {rej_wr:.1f}% | {rej_avg:.1f}/11 |

### Continuation Details
{continuation_details}

### Rejection Details
{rejection_details}

### Score Label Performance Comparison
**Continuation:**
{cont_score_table}

**Rejection:**
{rej_score_table}
"""
