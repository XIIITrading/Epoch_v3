"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Monte AI - Prompt Templates for Indicator Analysis (CALC-005 through CALC-008)
XIII Trading LLC
================================================================================

Specialized prompts for analyzing indicator effectiveness and generating
DOW AI configuration recommendations.

================================================================================
"""

# =============================================================================
# SYSTEM PROMPT FOR INDICATOR ANALYSIS
# =============================================================================

INDICATOR_ANALYSIS_SYSTEM_PROMPT = """You are Monte, an AI research assistant specializing in quantitative trading system analysis for XIII Trading LLC's Epoch Trading System.

## Your Current Task
Analyze the indicator analysis results (CALC-005 through CALC-008) and provide:
1. Key findings synthesis
2. Statistical validation assessment
3. DOW AI configuration recommendations
4. Areas requiring further investigation

## Context
The Epoch Trading System uses a 10-factor Health Score to evaluate trade setups:

STRUCTURE FACTORS (4 points):
- H4 Structure: 4-hour timeframe trend alignment
- H1 Structure: 1-hour timeframe trend alignment
- M15 Structure: 15-minute timeframe trend alignment
- M5 Structure: 5-minute timeframe trend alignment

VOLUME FACTORS (3 points):
- Volume ROC: Volume above 20% baseline threshold
- Volume Delta: Rolling 5-bar delta aligned with direction
- CVD Slope: Cumulative volume delta trend aligned

PRICE FACTORS (3 points):
- SMA Alignment: SMA9 vs SMA21 position
- SMA Momentum: Spread widening (ratio > 1.1)
- VWAP Position: Price vs VWAP alignment

ENTRY MODELS:
- EPCH1: Continuation at primary zone (trade WITH trend)
- EPCH2: Rejection at primary zone (trade AGAINST trend - mean reversion)
- EPCH3: Continuation at secondary zone
- EPCH4: Rejection at secondary zone

## Analysis Framework
When analyzing results, consider:
1. Statistical significance (n >= 30 required for confidence)
2. Effect size (lift > 5pp considered meaningful)
3. Model-specific patterns (continuation vs rejection)
4. Practical implementation complexity

## Output Format
Provide structured recommendations with:
- Finding (what the data shows)
- Confidence level (HIGH/MEDIUM/LOW based on sample size)
- Recommendation (specific action for DOW AI)
- Priority (P1/P2/P3)
"""


# =============================================================================
# ANALYSIS TEMPLATES
# =============================================================================

CALC_005_ANALYSIS_TEMPLATE = """
## CALC-005: Health Score Correlation Analysis

### Data Summary
{data_summary}

### Key Questions
1. Does Health Score have meaningful predictive value (r > 0.1)?
2. What is the win rate spread between STRONG (8-10) and CRITICAL (0-3)?
3. What is the optimal filtering threshold?
4. Is the relationship consistent across models?

### Required Output
- Correlation assessment and statistical significance
- Lift analysis by health bucket
- Recommended Health Score threshold for DOW AI
- Model-specific observations
"""

CALC_006_ANALYSIS_TEMPLATE = """
## CALC-006: Individual Factor Predictiveness

### Data Summary
{data_summary}

### Key Questions
1. Which factors have the highest lift (healthy vs unhealthy)?
2. Which factors are "dead" (lift < 2pp)?
3. Are there factor groups that outperform others?
4. Are any factors redundant (highly correlated)?

### Required Output
- Ranked factor importance list
- Weight adjustment recommendations for DOW AI
- Factors to potentially remove
- Factor interaction observations
"""

CALC_007_ANALYSIS_TEMPLATE = """
## CALC-007: Indicator Progression Analysis

### Data Summary
{data_summary}

### Key Questions
1. Do winners and losers start with different indicator states?
2. What indicator changes predict trade failure?
3. What early warning signals have highest lift?
4. At what point do winner/loser paths diverge?

### Required Output
- Entry state differences between winners/losers
- Best early warning signal specification
- Exit signal recommendation for DOW AI
- Timing observations
"""

CALC_008_ANALYSIS_TEMPLATE = """
## CALC-008: Rejection Dynamics Analysis

### Data Summary
{data_summary}

### Key Questions
1. Is Health Score inverted for rejection trades (EPCH2/4)?
2. Which factors have opposite meaning for rejection vs continuation?
3. Do rejection trades reach MFE faster?
4. What exhaustion indicators predict rejection success?

### Required Output
- Inversion verdict (does rejection need different scoring?)
- List of factors to invert for rejection trades
- Recommended exhaustion indicators
- Dual scoring system recommendation (if warranted)
"""

SYNTHESIS_ANALYSIS_TEMPLATE = """
## Comprehensive Indicator Analysis Synthesis

You have been provided with results from all four indicator analyses:
- CALC-005: Health Score correlation
- CALC-006: Factor importance
- CALC-007: Progression patterns
- CALC-008: Rejection dynamics

### Combined Data Summary
{data_summary}

### Synthesis Questions
1. What is the overall verdict on the Health Score system's effectiveness?
2. Which specific changes would have the highest impact on system performance?
3. What is the recommended implementation priority order?
4. What additional data or analysis is needed?

### Required Output
1. **Executive Summary** (3-5 bullet points)
2. **DOW AI Configuration Changes** (specific, implementable changes)
3. **Model-Specific Adjustments**
4. **Statistical Confidence Assessment**
5. **Next Steps / Further Research**
"""


# =============================================================================
# DATA FORMATTING TEMPLATES
# =============================================================================

CALC_005_DATA_FORMAT = """
### Health Score Correlation Statistics
- Total Trades: {total_trades}
- Overall Win Rate: {overall_win_rate:.1f}%
- Correlation Coefficient: r = {correlation:.3f} (p = {pvalue:.4f})
- Optimal Threshold: >= {optimal_threshold} (lift: +{optimal_lift:.1f}pp)

### Win Rate by Bucket
| Bucket | Trades | Win Rate | Lift vs Baseline |
|--------|--------|----------|------------------|
{bucket_table}

### Model-Direction Breakdown
{model_breakdown}
"""

CALC_006_DATA_FORMAT = """
### Factor Importance Ranking
| Rank | Factor | Group | Healthy Win% | Unhealthy Win% | Lift |
|------|--------|-------|--------------|----------------|------|
{factor_table}

### Factor Group Summary
| Group | Avg Lift | Best Factor |
|-------|----------|-------------|
{group_summary}

### Top Factors (lift > 5pp)
{top_factors}

### Dead Factors (lift < 2pp)
{dead_factors}
"""

CALC_007_DATA_FORMAT = """
### Progression Path Summary
| Outcome | Entry HS | Peak HS | Delta |
|---------|----------|---------|-------|
| Winners | {winner_entry:.1f} | {winner_peak:.1f} | {winner_delta:+.1f} |
| Losers | {loser_entry:.1f} | {loser_peak:.1f} | {loser_delta:+.1f} |

### Early Warning Signals
| Indicator | Threshold | Window | Loser Hit% | Winner Hit% | Lift |
|-----------|-----------|--------|------------|-------------|------|
{warning_table}

### Best Warning Signal
{best_warning}
"""

CALC_008_DATA_FORMAT = """
### Time-to-MFE Comparison
{time_table}

### Health Score Inversion Test
| Model Type | Correlation | STRONG Win% | CRITICAL Win% | Inverted? |
|------------|-------------|-------------|---------------|-----------|
{inversion_table}

### Factor Inversion Results
| Factor | Continuation Lift | Rejection Lift | Inverted |
|--------|-------------------|----------------|----------|
{factor_inversion_table}

### Inverted Factors
{inverted_factors}

### Verdict
{verdict}
"""
