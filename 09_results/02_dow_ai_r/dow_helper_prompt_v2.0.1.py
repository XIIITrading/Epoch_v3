"""
DOW AI Helper Prompt - Single Source of Truth
Epoch Trading System v2.0.1 - XIII Trading LLC

This is the v2.0.1 version that achieved 84-86% accuracy.
Key changes from v2.0:
- Made H1 alignment the dominant edge (+36pp) that can override other concerns
- Removed rigid candle range filter that was blocking valid trades
- Added context that base win rate is ~45%, goal is finding positive edge
- ONLY hard blockers: H1 BULL + SHORT, or triple conflict

Usage:
    from ai_context.dow_helper_prompt import (
        DOW_PROMPT_TEMPLATE_V2,
        PROMPT_VERSION,
        build_prompt_v2,
    )
"""

# =============================================================================
# PROMPT VERSION
# =============================================================================
PROMPT_VERSION = "v2.0.1"  # 2026-01-24: Fixed over-filtering - H1 alignment is primary, soft thresholds

# =============================================================================
# DIRECTION-SPECIFIC RULES
# =============================================================================
DIRECTION_RULES = {
    'LONG': """For LONG trades:
- Positive Vol Delta = buying pressure (supportive)
- Negative Vol Delta = selling pressure (opposing)
- SMA BULL = aligned. SMA BEAR = counter-trend.
- H1 BULL = supportive. H1 BEAR = opposing.""",

    'SHORT': """For SHORT trades:
- Negative Vol Delta = selling pressure (supportive)
- Positive Vol Delta = buying pressure (opposing)
- SMA BEAR = aligned. SMA BULL = counter-trend.
- H1 BEAR = supportive. H1 BULL = opposing."""
}

# =============================================================================
# V2.0.1 PROMPT TEMPLATE - CLAUDE AS DECISION ENGINE
# =============================================================================
# Key insight: H1 alignment is the dominant edge (+36pp)
# Don't over-filter on candle range - it's a soft guideline, not a blocker

DOW_PROMPT_TEMPLATE_V2 = """You are DOW, an AI trading decision engine for the Epoch system.

CRITICAL CONTEXT: The base win rate without any filtering is ~45%. Your job is to identify setups with positive edge, not perfect setups. A trade with H1 alignment (+36pp edge) can overcome minor weaknesses.

═══════════════════════════════════════════════════════════════════════════════
TRADE SETUP: {ticker} {direction}
═══════════════════════════════════════════════════════════════════════════════
{price_line}

RAW INDICATORS (5-bar averages):
- Candle Range: {candle_range:.3f}%
- Volume Delta: {vol_delta:+,.0f} (Z-Score: {vol_delta_zscore:+.2f})
- Volume ROC: {vol_roc:+.1f}%
- SMA: {sma_config} | H1: {h1_structure}

═══════════════════════════════════════════════════════════════════════════════
LEARNED EDGES (from {context_date_range})
═══════════════════════════════════════════════════════════════════════════════

EDGE HIERARCHY (by impact):
1. H1 Structure Alignment: +36pp (MOST POWERFUL - can override other concerns)
2. SMA Spread Magnitude: +16.4pp
3. Candle Range >= 0.15%: +15.7pp
4. Vol Delta Alignment: +4-10pp

DIRECTION STATS:
{model_stats_formatted}

ZONE WIN RATES:
{zone_performance_formatted}

═══════════════════════════════════════════════════════════════════════════════
DECISION LOGIC
═══════════════════════════════════════════════════════════════════════════════

For {direction}: {vol_delta_interpretation}
Structure: {structure_interpretation}

WHEN TO SAY TRADE:
- H1 aligned with direction = strong positive edge, lean TRADE
- Both H1 and SMA aligned = very strong, TRADE with HIGH confidence
- H1 aligned but SMA opposing = still tradeable if H1 edge (+36pp) > SMA drag

WHEN TO SAY NO_TRADE:
- H1 BULL + SHORT direction = 31.8% WR (critical blocker)
- Triple conflict (SMA opposing + H1 opposing + Vol Delta opposing)
- Very low candle range (<0.08%) with no compensating alignment

NOTE: Low candle range alone is NOT a blocker - LONG trades at low range still show 54.7% WR historically. Weight the H1 alignment heavily.

═══════════════════════════════════════════════════════════════════════════════
YOUR DECISION
═══════════════════════════════════════════════════════════════════════════════

RESPOND EXACTLY:

[TRADE or NO_TRADE] | Confidence: [HIGH/MEDIUM/LOW]

ANALYSIS:
- Candle: {candle_range:.3f}% [adequate/low/very low]
- Vol Delta Z: {vol_delta_zscore:+.2f} [supportive/neutral/opposing]
- SMA: {sma_config} [aligned/neutral/opposing]
- H1: {h1_structure} [aligned/neutral/opposing] (MOST IMPORTANT)

REASONING: [1-2 sentences - focus on H1 alignment as primary factor]"""

# =============================================================================
# INDICATOR STATUS THRESHOLDS
# =============================================================================
CANDLE_RANGE_THRESHOLDS = {
    'GOOD': 0.15,      # >= 0.15% is GOOD
    'OK': 0.12,        # >= 0.12% is OK
    # < 0.12% is SKIP
}

VOL_DELTA_THRESHOLDS = {
    'STRONG': 100000,   # Fallback threshold for FAVORABLE/WEAK status (v1.2)
    'WEAK': 50000,      # Moderate threshold for NEUTRAL boundary
    'ZSCORE_STRONG': 1.5,   # Z-score threshold for FAVORABLE/WEAK (v1.2.2)
    'ZSCORE_MODERATE': 0.75,  # Z-score threshold for slight signal
}

VOL_ROC_THRESHOLDS = {
    'ELEVATED': 30,    # >= 30% is ELEVATED
    # < 30% is NORMAL
}


# =============================================================================
# STATUS CALCULATION FUNCTIONS
# =============================================================================

def get_candle_status(candle_range_pct: float, direction: str = None) -> str:
    """Get candle range status based on percentage and direction."""
    if candle_range_pct >= CANDLE_RANGE_THRESHOLDS['GOOD']:
        return "GOOD"
    elif candle_range_pct >= CANDLE_RANGE_THRESHOLDS['OK']:
        return "OK"
    else:
        if direction == 'LONG':
            return "LOW"   # Consolidation - 54.7% WR historically
        else:
            return "SKIP"  # Insufficient momentum for shorts


def calculate_vol_delta_zscore(vol_delta: float, rampup_deltas: list) -> float:
    """Calculate Z-score for vol delta relative to ramp-up period."""
    if not rampup_deltas or len(rampup_deltas) < 3:
        return 0.0

    valid_deltas = [d for d in rampup_deltas if d is not None]
    if len(valid_deltas) < 3:
        return 0.0

    mean_delta = sum(valid_deltas) / len(valid_deltas)
    variance = sum((d - mean_delta) ** 2 for d in valid_deltas) / len(valid_deltas)
    std_delta = variance ** 0.5

    if std_delta < 1:
        std_delta = 1

    zscore = (vol_delta - mean_delta) / std_delta
    return zscore


def get_vol_delta_status(vol_delta: float, direction: str, rampup_deltas: list = None) -> str:
    """Get volume delta status based on value and trade direction."""
    if rampup_deltas and len(rampup_deltas) >= 3:
        zscore = calculate_vol_delta_zscore(vol_delta, rampup_deltas)
        strong_z = VOL_DELTA_THRESHOLDS['ZSCORE_STRONG']

        if direction == 'LONG':
            if zscore > strong_z:
                return "FAVORABLE"
            elif zscore < -strong_z:
                return "WEAK"
            else:
                return "NEUTRAL"
        else:  # SHORT
            if zscore < -strong_z:
                return "FAVORABLE"
            elif zscore > strong_z:
                return "WEAK"
            else:
                return "NEUTRAL"

    # Fallback to absolute thresholds
    strong_threshold = VOL_DELTA_THRESHOLDS['STRONG']

    if direction == 'LONG':
        if vol_delta > strong_threshold:
            return "FAVORABLE"
        elif vol_delta < -strong_threshold:
            return "WEAK"
        else:
            return "NEUTRAL"
    else:  # SHORT
        if vol_delta < -strong_threshold:
            return "FAVORABLE"
        elif vol_delta > strong_threshold:
            return "WEAK"
        else:
            return "NEUTRAL"


def get_vol_roc_status(vol_roc: float) -> str:
    """Get volume ROC status based on percentage."""
    if vol_roc >= VOL_ROC_THRESHOLDS['ELEVATED']:
        return "ELEVATED"
    else:
        return "NORMAL"


def get_direction_rules(direction: str) -> str:
    """Get direction-specific rules for prompt inclusion."""
    return DIRECTION_RULES.get(direction, "")


# =============================================================================
# V2.0 PROMPT BUILDER HELPERS
# =============================================================================

def format_model_stats(model_stats: dict, direction: str) -> str:
    """Format model performance stats for Claude."""
    if not model_stats or 'models' not in model_stats:
        return "- No model stats available"

    lines = []
    models = model_stats.get('models', {})

    for model_name, model_data in models.items():
        dir_stats = model_data.get(direction, {})
        if dir_stats:
            trades = dir_stats.get('trades', 0)
            win_rate = dir_stats.get('win_rate', 0)
            best_wr = dir_stats.get('best_stop_win_rate', 0)
            lines.append(f"  - {model_name} {direction}: {win_rate:.1f}% base WR ({trades} trades), {best_wr:.1f}% with optimal stop")

    if not lines:
        return f"  - No {direction} stats available"

    return "\n".join(lines)


def format_zone_performance(zone_perf: dict, direction: str) -> str:
    """Format zone performance for Claude."""
    if not zone_perf:
        return "- No zone performance data available"

    lines = []

    primary = zone_perf.get('primary', {}).get(direction, {})
    if primary:
        mid_wr = primary.get('mid', 'N/A')
        high_wr = primary.get('high', 'N/A')
        low_wr = primary.get('low', 'N/A')
        lines.append(f"  - Primary zones: Low={low_wr}%, Mid={mid_wr}%, High={high_wr}%")

    secondary = zone_perf.get('secondary', {}).get(direction, {})
    if secondary:
        mid_wr = secondary.get('mid', 'N/A')
        lines.append(f"  - Secondary zones: Mid={mid_wr}%")

    if not lines:
        return f"  - No {direction} zone data"

    return "\n".join(lines)


def get_vol_delta_interpretation(direction: str) -> str:
    """Get interpretation guidance for vol delta based on direction."""
    if direction == 'LONG':
        return "Positive delta = buying pressure (supportive), Negative = selling (opposing)"
    else:
        return "Negative delta = selling pressure (supportive), Positive = buying (opposing)"


def get_structure_interpretation(direction: str, sma_config: str, h1_structure: str) -> str:
    """Get interpretation of structure alignment for direction."""
    if direction == 'LONG':
        aligned_sma = sma_config == 'BULL'
        aligned_h1 = h1_structure == 'BULL'
        target = 'BULL'
    else:
        aligned_sma = sma_config == 'BEAR'
        aligned_h1 = h1_structure == 'BEAR'
        target = 'BEAR'

    if aligned_sma and aligned_h1:
        return f"Both SMA and H1 show {target} = fully aligned"
    elif aligned_sma:
        return f"SMA aligned ({target}), H1 neutral/opposing"
    elif aligned_h1:
        return f"H1 aligned ({target}), SMA neutral/opposing"
    else:
        return f"Neither SMA nor H1 aligned with {direction}"


def build_prompt_v2(
    ticker: str,
    direction: str,
    price_line: str,
    candle_range: float,
    vol_delta: float,
    vol_roc: float,
    sma_config: str,
    h1_structure: str,
    rampup_deltas: list,
    indicator_edges: dict,
    model_stats: dict,
    zone_performance: dict
) -> str:
    """
    Build v2.0.1 DOW AI prompt - Claude as decision engine.

    This version achieved 84-86% accuracy by:
    - Making H1 alignment the dominant edge
    - Using soft thresholds instead of hard blockers
    - Focusing on finding positive edge, not perfection
    """
    # Calculate Z-score for vol delta
    vol_delta_zscore = calculate_vol_delta_zscore(vol_delta, rampup_deltas)

    # Get context date range
    context_date_range = model_stats.get('date_range', {})
    date_range_str = f"{context_date_range.get('from', 'N/A')} to {context_date_range.get('to', 'N/A')}"

    # Format context sections
    model_stats_formatted = format_model_stats(model_stats, direction)
    zone_performance_formatted = format_zone_performance(zone_performance, direction)

    # Get interpretation helpers
    vol_delta_interpretation = get_vol_delta_interpretation(direction)
    structure_interpretation = get_structure_interpretation(direction, sma_config, h1_structure)

    # Build prompt from v2 template
    prompt = DOW_PROMPT_TEMPLATE_V2.format(
        ticker=ticker,
        direction=direction,
        price_line=price_line,
        candle_range=candle_range,
        vol_delta=vol_delta,
        vol_delta_zscore=vol_delta_zscore,
        vol_roc=vol_roc,
        sma_config=sma_config,
        h1_structure=h1_structure,
        context_date_range=date_range_str,
        model_stats_formatted=model_stats_formatted,
        zone_performance_formatted=zone_performance_formatted,
        vol_delta_interpretation=vol_delta_interpretation,
        structure_interpretation=structure_interpretation
    )

    return prompt


def estimate_tokens(prompt: str) -> int:
    """Estimate token count for a prompt (~4 chars per token)."""
    return len(prompt) // 4
