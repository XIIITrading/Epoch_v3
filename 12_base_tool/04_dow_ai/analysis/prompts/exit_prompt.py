"""
DOW AI - Exit Analysis Prompt Template
Epoch Trading System v1 - XIII Trading LLC

Prompt template for Claude to analyze exit opportunities.
"""

EXIT_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for intraday analysis. You are analyzing a potential exit for a {position_type} position in {ticker}.

POSITION CONTEXT:
- Ticker: {ticker}
- Position: {position_type}
- Exit Action: {exit_action}
- Model Used: {model_name}

CURRENT MARKET STATE:
- Current Price: ${current_price:.2f}
- Target Price: ${target_price:.2f} ({target_id})
- Distance to Target: ${distance_to_target:.2f} ({distance_percent:.1f}%)
- Analysis Time: {analysis_time}

ZONE CONTEXT:
{zone_context}

MARKET STRUCTURE (Multi-Timeframe):
{structure_table}

VOLUME ANALYSIS:
- Volume Delta (5-bar): {delta_5bar:+,.0f} ({delta_signal})
- Volume ROC: {roc_percent:+.1f}% vs 20-bar avg ({roc_signal})
- CVD Trend: {cvd_trend}

CANDLESTICK PATTERNS DETECTED:
{patterns_list}

KEY LEVELS:
- HVN POCs: {hvn_pocs}
- Strong Levels (potential reversals): {strong_levels}
- Weak Levels (continuation targets): {weak_levels}

---

Provide analysis in this EXACT format:

RECOMMENDATION: [FULL EXIT / PARTIAL EXIT (X%) / HOLD / TRAIL STOP]
CONFIDENCE: [HIGH/MEDIUM/LOW]

ASSESSMENT:
[List 3-5 bullet points with warning for exit signals, checkmark for hold signals]

ACTION:
[Specific action steps - price levels for exits, stop adjustments]

HOLD TRIGGERS (if recommending hold or partial):
[What would need to happen to continue holding / add to position]

Keep response concise - trader is actively monitoring markets."""


def build_exit_prompt(
    ticker: str,
    position_type: str,  # 'LONG' or 'SHORT'
    exit_action: str,    # 'SELL' or 'COVER'
    model_name: str,
    current_price: float,
    target_price: float,
    target_id: str,
    analysis_time: str,
    zone_context: str,
    structure_table: str,
    delta_5bar: float,
    delta_signal: str,
    roc_percent: float,
    roc_signal: str,
    cvd_trend: str,
    patterns_list: str,
    hvn_pocs: str,
    strong_levels: str,
    weak_levels: str
) -> str:
    """
    Build the complete exit analysis prompt.

    Args:
        ticker: Stock symbol
        position_type: 'LONG' or 'SHORT'
        exit_action: 'SELL' or 'COVER'
        model_name: Model ID used for entry
        current_price: Current stock price
        target_price: Target price from zone
        target_id: Target zone/level ID
        analysis_time: Formatted analysis timestamp
        zone_context: Formatted zone information
        structure_table: Formatted market structure table
        delta_5bar: 5-bar volume delta
        delta_signal: Delta signal
        roc_percent: Volume ROC percentage
        roc_signal: ROC signal
        cvd_trend: CVD trend
        patterns_list: Formatted patterns list
        hvn_pocs: Formatted HVN POC levels
        strong_levels: Formatted strong (invalidation) levels
        weak_levels: Formatted weak (continuation) levels

    Returns:
        Complete prompt string for Claude
    """
    distance_to_target = abs(target_price - current_price)
    distance_percent = (distance_to_target / current_price) * 100 if current_price > 0 else 0

    return EXIT_PROMPT_TEMPLATE.format(
        ticker=ticker,
        position_type=position_type,
        exit_action=exit_action,
        model_name=model_name,
        current_price=current_price,
        target_price=target_price,
        target_id=target_id,
        distance_to_target=distance_to_target,
        distance_percent=distance_percent,
        analysis_time=analysis_time,
        zone_context=zone_context,
        structure_table=structure_table,
        delta_5bar=delta_5bar,
        delta_signal=delta_signal,
        roc_percent=roc_percent,
        roc_signal=roc_signal,
        cvd_trend=cvd_trend,
        patterns_list=patterns_list,
        hvn_pocs=hvn_pocs,
        strong_levels=strong_levels,
        weak_levels=weak_levels
    )
