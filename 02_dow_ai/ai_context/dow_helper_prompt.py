"""
DOW AI Helper Prompt - Single Source of Truth
Epoch Trading System v2.0 - XIII Trading LLC

This module contains the DOW AI prompt template and direction-specific rules.
Both live Entry Qualifier and batch analyzer import from here to ensure consistency.

v2.0 Architecture - Claude as Decision Engine:
- Claude receives RAW indicator values (no pre-calculated labels)
- Claude receives full context files as "learned knowledge"
- Claude applies reasoning using context to make TRADE/NO_TRADE decisions
- Continuous learning loop: context files updated from backtesting feedback

Previous versions:
- v1.2.2: Z-score normalization for vol delta
- v1.2.1: Simpler prompt, kept vol delta direction fix
- v1.2: Pre-calculated analysis (too conservative)

Usage:
    from ai_context.dow_helper_prompt import (
        DOW_PROMPT_TEMPLATE_V2,
        PROMPT_VERSION,
        build_prompt_v2,
        # Legacy exports for backwards compatibility
        DOW_PROMPT_TEMPLATE,
        build_prompt
    )
"""

# =============================================================================
# PROMPT VERSION
# =============================================================================
PROMPT_VERSION = "v2.0.1"  # 2026-01-24: Fixed over-filtering - H1 alignment is primary, soft thresholds

# =============================================================================
# DIRECTION-SPECIFIC RULES
# =============================================================================
# These rules help Claude understand how to interpret indicators based on
# trade direction. Critical for correct prediction logic.

DIRECTION_RULES = {
    'LONG': """For LONG trades:
- Positive Vol Delta = buying pressure (supportive)
- Negative Vol Delta = selling pressure (opposing)
- SMA B+ = aligned. SMA B- = counter-trend.
- H1 B+ = supportive. H1 B- = opposing.""",

    'SHORT': """For SHORT trades:
- Negative Vol Delta = selling pressure (supportive)
- Positive Vol Delta = buying pressure (opposing)
- SMA B- = aligned. SMA B+ = counter-trend.
- H1 B- = supportive. H1 B+ = opposing."""
}

# =============================================================================
# PROMPT TEMPLATE
# =============================================================================
# Main DOW AI prompt template. Uses Python format strings for variable injection.
# Both live and batch systems use this exact template.

DOW_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for the Epoch system.

TRADE: {ticker} | {direction}
{price_line}

INDICATORS (5-bar avg):
- Candle: {candle_range:.2f}% ({candle_status})
- Vol Delta: {vol_delta:+,.0f} ({vol_delta_status})
- Vol ROC: {vol_roc:+.0f}% ({vol_roc_status})
- SMA: {sma_config}
- H1: {h1_structure}

{direction_rules}

CONTEXT:
- {direction} win rate: {direction_win_rate}%
{edge_summary}

ZONE:
{zone_info}

Analyze the indicators for this {direction} trade. Consider alignment of SMA, H1, and volume with the trade direction.

RESPOND EXACTLY:

[TRADE or NO TRADE] | Confidence: [HIGH/MEDIUM/LOW]

INDICATORS:
- Candle %: [value] ([status])
- Vol Delta: [value] ([status])
- Vol ROC: [value] ([status])
- SMA: [value]
- H1 Struct: [value]

SNAPSHOT: [1-2 sentences on key factors]

Maximum 60 words."""

# =============================================================================
# V2.0 PROMPT TEMPLATE - CLAUDE AS DECISION ENGINE
# =============================================================================
# In v2.0, Claude receives raw indicator values + full context files.
# Claude applies the reasoning itself using the learned knowledge from context.
# This enables continuous learning as context files are updated from feedback.

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
- H1 B+ + SHORT direction = 31.8% WR (critical blocker)
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
# Centralized thresholds for indicator status assignment.
# Ensures consistent logic between live and batch processing.

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
    """
    Get candle range status based on percentage and direction (v1.2).

    Direction-aware logic:
    - LONG: LOW (<0.12%) shows 54.7% WR (consolidation breakout potential)
    - SHORT: SKIP (<0.12%) shows 42.6% WR (insufficient momentum)

    Args:
        candle_range_pct: Average candle range as percentage
        direction: Trade direction (LONG or SHORT), optional for backwards compat

    Returns:
        Status string: GOOD, OK, LOW (LONG), or SKIP (SHORT)
    """
    if candle_range_pct >= CANDLE_RANGE_THRESHOLDS['GOOD']:
        return "GOOD"
    elif candle_range_pct >= CANDLE_RANGE_THRESHOLDS['OK']:
        return "OK"
    else:
        # Direction-specific low volatility interpretation
        if direction == 'LONG':
            return "LOW"   # Consolidation - 54.7% WR historically
        else:
            return "SKIP"  # Insufficient momentum for shorts


def calculate_vol_delta_zscore(vol_delta: float, rampup_deltas: list) -> float:
    """
    Calculate Z-score for vol delta relative to ramp-up period (v1.2.2).

    This normalizes vol delta to account for ticker volume differences
    and time-of-day variations.

    Args:
        vol_delta: Current 5-bar average vol delta
        rampup_deltas: List of vol delta values from ramp-up bars

    Returns:
        Z-score (standard deviations from mean)
    """
    if not rampup_deltas or len(rampup_deltas) < 3:
        return 0.0  # Not enough data, return neutral

    # Filter out None values
    valid_deltas = [d for d in rampup_deltas if d is not None]
    if len(valid_deltas) < 3:
        return 0.0

    # Calculate mean and std
    mean_delta = sum(valid_deltas) / len(valid_deltas)

    # Calculate standard deviation
    variance = sum((d - mean_delta) ** 2 for d in valid_deltas) / len(valid_deltas)
    std_delta = variance ** 0.5

    # Avoid division by zero - if no variance, can't calculate z-score
    if std_delta < 1:  # Minimum threshold to avoid noise
        std_delta = 1

    # Calculate z-score
    zscore = (vol_delta - mean_delta) / std_delta

    return zscore


def get_vol_delta_status(vol_delta: float, direction: str, rampup_deltas: list = None) -> str:
    """
    Get volume delta status based on value and trade direction.

    v1.2.2: Now uses Z-score normalization when rampup_deltas provided.
    This accounts for ticker volume differences and time-of-day variations.

    Direction-aware logic:
    - LONG: Positive Z-score (above mean) = FAVORABLE, Negative = WEAK
    - SHORT: Negative Z-score (below mean) = FAVORABLE, Positive = WEAK

    Args:
        vol_delta: Average volume delta value (5-bar)
        direction: Trade direction (LONG or SHORT)
        rampup_deltas: Optional list of vol delta values from ramp-up bars for Z-score

    Returns:
        Status string: FAVORABLE, NEUTRAL, or WEAK
    """
    # Use Z-score if ramp-up data provided (v1.2.2)
    if rampup_deltas and len(rampup_deltas) >= 3:
        zscore = calculate_vol_delta_zscore(vol_delta, rampup_deltas)
        strong_z = VOL_DELTA_THRESHOLDS['ZSCORE_STRONG']  # 1.5

        if direction == 'LONG':
            # For LONG: positive z-score (unusually high buying) = good
            if zscore > strong_z:
                return "FAVORABLE"
            elif zscore < -strong_z:
                return "WEAK"
            else:
                return "NEUTRAL"
        else:  # SHORT
            # For SHORT: negative z-score (unusually high selling) = good
            if zscore < -strong_z:
                return "FAVORABLE"
            elif zscore > strong_z:
                return "WEAK"
            else:
                return "NEUTRAL"

    # Fallback to absolute thresholds (v1.2 behavior)
    strong_threshold = VOL_DELTA_THRESHOLDS['STRONG']  # 100000

    if direction == 'LONG':
        if vol_delta > strong_threshold:
            return "FAVORABLE"   # Strong buying supports longs
        elif vol_delta < -strong_threshold:
            return "WEAK"        # Strong selling opposes longs
        else:
            return "NEUTRAL"
    else:  # SHORT
        if vol_delta < -strong_threshold:
            return "FAVORABLE"   # Strong selling supports shorts
        elif vol_delta > strong_threshold:
            return "WEAK"        # Strong buying opposes shorts
        else:
            return "NEUTRAL"


def get_vol_roc_status(vol_roc: float) -> str:
    """
    Get volume ROC status based on percentage.

    Args:
        vol_roc: Volume rate of change percentage

    Returns:
        Status string: ELEVATED or NORMAL
    """
    if vol_roc >= VOL_ROC_THRESHOLDS['ELEVATED']:
        return "ELEVATED"
    else:
        return "NORMAL"


def get_direction_rules(direction: str) -> str:
    """
    Get direction-specific rules for prompt inclusion.

    Args:
        direction: Trade direction (LONG or SHORT)

    Returns:
        Direction rules string for prompt
    """
    return DIRECTION_RULES.get(direction, "")


def calculate_alignment_score(
    direction: str,
    sma_config: str,
    h1_structure: str,
    vol_delta: float
) -> int:
    """
    Calculate composite alignment score for trade direction (v1.2).

    Score Range: -3 to +3
    - Positive scores favor TRADE
    - Negative scores favor NO_TRADE
    - Zero is neutral

    Args:
        direction: 'LONG' or 'SHORT'
        sma_config: 'B+', 'B-', or 'N'
        h1_structure: 'B+', 'B-', or 'N'
        vol_delta: Average volume delta value

    Returns:
        Integer alignment score from -3 to +3
    """
    score = 0
    vol_threshold = VOL_DELTA_THRESHOLDS['STRONG']  # 100000

    if direction == 'LONG':
        # SMA alignment for LONG
        if sma_config == 'B+':
            score += 1
        elif sma_config == 'B-':
            score -= 1

        # H1 alignment for LONG
        if h1_structure == 'B+':
            score += 1
        elif h1_structure == 'B-':
            score -= 1

        # Vol Delta alignment for LONG
        if vol_delta > vol_threshold:
            score += 1
        elif vol_delta < -vol_threshold:
            score -= 1

    else:  # SHORT
        # SMA alignment for SHORT
        if sma_config == 'B-':
            score += 1
        elif sma_config == 'B+':
            score -= 1

        # H1 alignment for SHORT
        if h1_structure == 'B-':
            score += 1
        elif h1_structure == 'B+':
            score -= 1  # Critical: 31.8% win rate when opposed

        # Vol Delta alignment for SHORT
        if vol_delta < -vol_threshold:
            score += 1
        elif vol_delta > vol_threshold:
            score -= 1

    return score


def detect_critical_conflicts(
    direction: str,
    sma_config: str,
    h1_structure: str,
    vol_delta: float
) -> list:
    """
    Detect critical conflict conditions (v1.2).

    Returns list of conflict flags that should trigger NO_TRADE.

    Args:
        direction: 'LONG' or 'SHORT'
        sma_config: 'B+', 'B-', or 'N'
        h1_structure: 'B+', 'B-', or 'N'
        vol_delta: Average volume delta value

    Returns:
        List of conflict strings (empty if no conflicts)
    """
    conflicts = []
    vol_threshold = VOL_DELTA_THRESHOLDS['STRONG']  # 100000

    # Rule 1: H1 B+ + SHORT (31.8% win rate - WORST)
    if direction == 'SHORT' and h1_structure == 'B+':
        conflicts.append("H1_BULL_SHORT_CONFLICT")

    # Rule 2: H1 B- + LONG (counter-trend)
    if direction == 'LONG' and h1_structure == 'B-':
        conflicts.append("H1_BEAR_LONG_CONFLICT")

    # Rule 3: Vol Delta strong opposition
    if direction == 'LONG' and vol_delta < -vol_threshold:
        conflicts.append("VOL_DELTA_OPPOSES_LONG")
    if direction == 'SHORT' and vol_delta > vol_threshold:
        conflicts.append("VOL_DELTA_OPPOSES_SHORT")

    # Rule 4: Triple conflict (automatic NO_TRADE)
    sma_counter = (direction == 'LONG' and sma_config == 'B-') or \
                  (direction == 'SHORT' and sma_config == 'B+')
    h1_counter = (direction == 'LONG' and h1_structure == 'B-') or \
                 (direction == 'SHORT' and h1_structure == 'B+')
    vol_opposes = (direction == 'LONG' and vol_delta < -vol_threshold) or \
                  (direction == 'SHORT' and vol_delta > vol_threshold)

    if sma_counter and h1_counter and vol_opposes:
        conflicts.append("TRIPLE_CONFLICT")

    return conflicts


def get_alignment_status(score: int) -> tuple:
    """
    Get alignment status text and recommended action from score.

    Args:
        score: Alignment score from -3 to +3

    Returns:
        Tuple of (status_text, recommended_action, confidence)
    """
    if score >= 3:
        return ("Fully Aligned", "TRADE", "HIGH")
    elif score == 2:
        return ("Well Aligned", "TRADE", "MEDIUM-HIGH")
    elif score == 1:
        return ("Slightly Aligned", "TRADE", "MEDIUM")
    elif score == 0:
        return ("Neutral", "NO_TRADE", "MEDIUM")
    elif score == -1:
        return ("Slightly Opposed", "NO_TRADE", "MEDIUM")
    elif score == -2:
        return ("Moderately Opposed", "NO_TRADE", "HIGH")
    else:  # score <= -3
        return ("Fully Opposed", "NO_TRADE", "HIGH")


# =============================================================================
# PROMPT BUILDING HELPERS
# =============================================================================

def format_price_line_live(current_price: float, timestamp: str) -> str:
    """Format price line for live trading."""
    return f"Current Price: ${current_price:.2f} | Time: {timestamp}"


def format_price_line_batch(entry_price: float, trade_date: str, entry_time: str) -> str:
    """Format price line for batch analysis."""
    return f"Entry Price: ${entry_price:.2f} | Date: {trade_date} | Time: {entry_time}"


def build_alignment_analysis(
    direction: str,
    sma_config: str,
    h1_structure: str,
    vol_delta: float,
    vol_delta_status: str
) -> str:
    """
    Build pre-calculated alignment analysis string for the prompt.

    This applies the v1.2 refinements:
    - Alignment score calculation
    - Critical conflict detection
    - Clear recommendation based on score

    Args:
        direction: LONG or SHORT
        sma_config: SMA alignment (B+/B-/N)
        h1_structure: H1 structure (B+/B-/N)
        vol_delta: Volume delta value
        vol_delta_status: Pre-calculated vol delta status

    Returns:
        Formatted analysis string
    """
    # Calculate alignment score
    score = calculate_alignment_score(direction, sma_config, h1_structure, vol_delta)

    # Detect conflicts
    conflicts = detect_critical_conflicts(direction, sma_config, h1_structure, vol_delta)

    # Build score breakdown
    if direction == 'LONG':
        sma_contrib = "+1" if sma_config == 'B+' else ("-1" if sma_config == 'B-' else "0")
        h1_contrib = "+1" if h1_structure == 'B+' else ("-1" if h1_structure == 'B-' else "0")
    else:  # SHORT
        sma_contrib = "+1" if sma_config == 'B-' else ("-1" if sma_config == 'B+' else "0")
        h1_contrib = "+1" if h1_structure == 'B-' else ("-1" if h1_structure == 'B+' else "0")

    vol_contrib = "+1" if vol_delta_status == 'FAVORABLE' else ("-1" if vol_delta_status == 'WEAK' else "0")

    # Determine recommendation
    if "TRIPLE_CONFLICT" in conflicts:
        recommendation = "NO_TRADE (triple conflict - all factors oppose)"
    elif "H1_BULL_SHORT_CONFLICT" in conflicts:
        recommendation = "NO_TRADE (H1 B+ vs SHORT = 31.8% historical WR)"
    elif score >= 2:
        recommendation = "TRADE (strong alignment)"
    elif score == 1:
        recommendation = "TRADE (moderate alignment)"
    elif score == 0:
        recommendation = "LEAN NO_TRADE (neutral - no edge)"
    elif score == -1:
        recommendation = "NO_TRADE (slight opposition)"
    else:
        recommendation = "NO_TRADE (strong opposition)"

    analysis = f"""- Alignment Score: {score} (SMA:{sma_contrib} + H1:{h1_contrib} + VolDelta:{vol_contrib})
- Conflicts: {', '.join(conflicts) if conflicts else 'None'}
- Recommendation: {recommendation}"""

    return analysis


def build_prompt(
    ticker: str,
    direction: str,
    price_line: str,
    candle_range: float,
    vol_delta: float,
    vol_roc: float,
    sma_config: str,
    h1_structure: str,
    direction_win_rate: str,
    edge_summary: str,
    zone_info: str,
    rampup_deltas: list = None
) -> str:
    """
    Build complete DOW AI prompt from components.

    This is the main prompt builder used by both live and batch systems.
    All indicator status values are calculated using the shared functions.
    v1.2.2: Added rampup_deltas for Z-score vol delta normalization.

    Args:
        ticker: Stock symbol
        direction: LONG or SHORT
        price_line: Formatted price/time line (live or batch format)
        candle_range: 5-bar average candle range %
        vol_delta: 5-bar average volume delta
        vol_roc: 5-bar average volume ROC %
        sma_config: SMA alignment (B+/B-/N)
        h1_structure: H1 structure (B+/B-/N)
        direction_win_rate: Historical win rate for direction
        edge_summary: Formatted edge conditions
        zone_info: Formatted zone data
        rampup_deltas: Optional list of vol delta values from ramp-up bars for Z-score

    Returns:
        Complete prompt string ready for Claude API
    """
    # Calculate status values using shared functions (v1.2.2: Z-score aware)
    candle_status = get_candle_status(candle_range, direction)
    vol_delta_status = get_vol_delta_status(vol_delta, direction, rampup_deltas)
    vol_roc_status = get_vol_roc_status(vol_roc)
    direction_rules = get_direction_rules(direction)

    # Build prompt from template (v1.2.1: simpler, no pre-calculated analysis)
    prompt = DOW_PROMPT_TEMPLATE.format(
        ticker=ticker,
        direction=direction,
        price_line=price_line,
        candle_range=candle_range,
        candle_status=candle_status,
        vol_delta=vol_delta,
        vol_delta_status=vol_delta_status,
        vol_roc=vol_roc,
        vol_roc_status=vol_roc_status,
        sma_config=sma_config,
        h1_structure=h1_structure,
        direction_rules=direction_rules,
        direction_win_rate=direction_win_rate,
        edge_summary=edge_summary,
        zone_info=zone_info
    )

    return prompt


def estimate_tokens(prompt: str) -> int:
    """
    Estimate token count for a prompt.

    Rough approximation: ~4 characters per token for English text.

    Args:
        prompt: Prompt string

    Returns:
        Estimated token count
    """
    return len(prompt) // 4


# =============================================================================
# V2.0 PROMPT BUILDER - CLAUDE AS DECISION ENGINE
# =============================================================================

def format_indicator_edges(edges_data: dict, direction: str) -> str:
    """
    Format indicator edges from context for Claude to interpret.

    Args:
        edges_data: Raw edges dict from indicator_edges.json
        direction: LONG or SHORT

    Returns:
        Formatted string of relevant edges
    """
    if not edges_data:
        return "- No validated edges available"

    lines = []

    for indicator, edge_info in edges_data.items():
        favorable = edge_info.get('favorable', [])
        best_for = edge_info.get('best_for', 'ALL')
        max_effect = edge_info.get('max_effect_pp', 0)

        # Include if relevant to direction or ALL
        if best_for in [direction, 'ALL'] or direction in str(favorable):
            # Take top 2 favorable conditions
            top_conditions = favorable[:2] if favorable else []
            for cond in top_conditions:
                lines.append(f"  - {indicator}: {cond}")

    if not lines:
        return "  - No edges specific to this direction"

    return "\n".join(lines)


def format_model_stats(model_stats: dict, direction: str) -> str:
    """
    Format model performance stats for Claude.

    Args:
        model_stats: Raw model stats from model_stats.json
        direction: LONG or SHORT

    Returns:
        Formatted string of model performance
    """
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
    """
    Format zone performance for Claude.

    Args:
        zone_perf: Raw zone performance from zone_performance.json
        direction: LONG or SHORT

    Returns:
        Formatted string of zone performance
    """
    if not zone_perf:
        return "- No zone performance data available"

    lines = []

    # Primary zones
    primary = zone_perf.get('primary', {}).get(direction, {})
    if primary:
        mid_wr = primary.get('mid', 'N/A')
        high_wr = primary.get('high', 'N/A')
        low_wr = primary.get('low', 'N/A')
        lines.append(f"  - Primary zones: Low={low_wr}%, Mid={mid_wr}%, High={high_wr}%")

    # Secondary zones
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
        aligned_sma = sma_config == 'B+'
        aligned_h1 = h1_structure == 'B+'
        target = 'B+'
    else:
        aligned_sma = sma_config == 'B-'
        aligned_h1 = h1_structure == 'B-'
        target = 'B-'

    parts = []
    if aligned_sma and aligned_h1:
        parts.append(f"Both SMA and H1 show {target} = fully aligned")
    elif aligned_sma:
        parts.append(f"SMA aligned ({target}), H1 neutral/opposing")
    elif aligned_h1:
        parts.append(f"H1 aligned ({target}), SMA neutral/opposing")
    else:
        parts.append(f"Neither SMA nor H1 aligned with {direction}")

    return "; ".join(parts)


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
    Build v2.0 DOW AI prompt - Claude as decision engine.

    In v2.0, Claude receives:
    - Raw indicator values (no pre-calculated labels)
    - Full context files as "learned knowledge"
    - Interpretation guidelines

    Claude applies the reasoning itself using the context.

    Args:
        ticker: Stock symbol
        direction: LONG or SHORT
        price_line: Formatted price/time line
        candle_range: 5-bar average candle range %
        vol_delta: 5-bar average volume delta
        vol_roc: 5-bar average volume ROC %
        sma_config: SMA alignment (B+/B-/N)
        h1_structure: H1 structure (B+/B-/N)
        rampup_deltas: List of vol delta values from ramp-up bars
        indicator_edges: Full indicator_edges.json content
        model_stats: Full model_stats.json content
        zone_performance: Full zone_performance.json content

    Returns:
        Complete v2.0 prompt string ready for Claude API
    """
    # Calculate Z-score for vol delta
    vol_delta_zscore = calculate_vol_delta_zscore(vol_delta, rampup_deltas)

    # Get context date range
    context_date_range = model_stats.get('date_range', {})
    date_range_str = f"{context_date_range.get('from', 'N/A')} to {context_date_range.get('to', 'N/A')}"

    # Format context sections
    edges_data = indicator_edges.get('edges', {})
    indicator_edges_formatted = format_indicator_edges(edges_data, direction)
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
