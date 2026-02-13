"""
DOW AI v3.0 Prompt Templates
Epoch Trading System - XIII Trading LLC

Dual-Pass Analysis System:
- Pass 1 (Trader's Eye): Raw M1 bars with indicators - what would a skilled trader see?
- Pass 2 (System Decision): Same data + backtested edges - system recommendation

Key Design Principle:
Show Claude the FULL 15-bar context with ALL indicators, exactly as a human trader
would see when making a decision. No pre-aggregation, no hiding data.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import time


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class M1BarFull:
    """
    Complete M1 bar with all indicator fields from m1_indicator_bars table.
    This is what Claude sees - the full picture.
    """
    bar_index: int              # -15 to -1 (relative to entry)
    bar_time: time              # HH:MM:SS

    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: int

    # Volume Indicators
    vol_delta: float            # Buy volume - sell volume
    vol_roc: float              # Volume rate of change %
    cvd_slope: float            # Cumulative volume delta slope

    # Price Indicators
    candle_range_pct: float     # (high - low) / close * 100
    vwap: float                 # Volume weighted average price

    # SMA Indicators
    sma9: float
    sma21: float
    sma_spread: float           # sma9 - sma21 (positive = bullish)
    sma_momentum_label: str     # WIDENING, NARROWING, FLAT

    # Structure Indicators (multi-timeframe)
    h1_structure: str           # BULL, BEAR, NEUT
    m15_structure: str
    m5_structure: str
    m1_structure: str

    # Scores
    long_score: int             # 0-10 favorability for LONG
    short_score: int            # 0-10 favorability for SHORT


@dataclass
class TradeForAnalysis:
    """
    Complete trade data for dual-pass analysis.
    Loaded from trades + entry_indicators + m1_indicator_bars tables.
    """
    # Trade identification
    trade_id: str
    ticker: str
    trade_date: str             # YYYY-MM-DD
    entry_time: str             # HH:MM:SS
    direction: str              # LONG or SHORT
    entry_price: float

    # Trade context
    model: str                  # EPCH1, EPCH2, EPCH3, EPCH4
    zone_type: str              # PRIMARY, SECONDARY

    # M1 bars with full indicators (15 bars before entry)
    m1_bars: List[M1BarFull]

    # Actual outcome
    is_winner: bool
    pnl_r: Optional[float]

    @property
    def actual_outcome(self) -> str:
        return 'WIN' if self.is_winner else 'LOSS'


# =============================================================================
# PROMPT VERSION
# =============================================================================

PROMPT_VERSION = "v3.0.1"  # Added baseline context, shifted to TRADE-default framework


# =============================================================================
# PASS 1: TRADER'S EYE (No Backtested Context)
# =============================================================================

PASS1_TEMPLATE = """You are an experienced intraday trader analyzing a {direction} entry that has been PRE-QUALIFIED by a systematic trading system.

IMPORTANT CONTEXT:
- This trade is NOT random. It comes from a system with ~47% baseline win rate on 1.5R trades
- The system has already identified this as a high-volume-node zone entry
- Your job: Assess if the M1 price action SUPPORTS the trade. Default is TRADE unless you see clear warning signs.

DECISION FRAMEWORK:
- TRADE: Price action is neutral to supportive. No major red flags. Let the system work.
- NO_TRADE: You see CLEAR evidence against this setup (opposing structure, volume divergence, absorption)

================================================================================
TRADE SETUP
================================================================================

Ticker: {ticker}
Direction: {direction}
Entry Price: ${entry_price:.2f}
Entry Time: {entry_time}

================================================================================
M1 PRICE ACTION - 15 BARS BEFORE ENTRY
================================================================================

{m1_bars_table}

================================================================================
COLUMN GUIDE
================================================================================

- Delta: Buy - Sell volume (positive = buying pressure). For {direction}, want {delta_preference}.
- Range%: Candle volatility. >=0.12% shows movement; <0.10% suggests absorption/chop.
- Spread: SMA9 - SMA21. For LONG want positive; for SHORT want negative.
- H1/M15/M5/M1: Multi-timeframe structure (BULL/BEAR/NEUT). Higher timeframes matter most.
- L/S: Long and Short scores (0-10). Higher = more favorable for that direction.

================================================================================
QUICK CHECK FOR {direction}
================================================================================

1. STRUCTURE: Is H1 at least NEUTRAL toward {direction}? (BULL ok for LONG, BEAR ok for SHORT, NEUT ok)
2. SCORES: Is the {direction_score} score >= 4?
3. VOLATILITY: Is Range% >= 0.10% on recent bars? (shows market is moving)

If ANY check shows STRONG opposition (H1 directly against you, score < 3, absorption), consider NO_TRADE.
If checks are neutral or supportive, TRADE.

================================================================================
YOUR RESPONSE
================================================================================

DECISION: [TRADE or NO_TRADE]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [2-3 sentences. What did you observe? Reference specific bars/values.]
"""


# =============================================================================
# PASS 2: SYSTEM DECISION (With Backtested Context)
# =============================================================================

PASS2_TEMPLATE = """You are DOW, the AI trading analyst for the EPOCH system.

CRITICAL CONTEXT:
- This trade is PRE-QUALIFIED by the EPOCH system ({model}, {zone_type} zone)
- System baseline: ~47% win rate on 1.5R trades = positive expectancy
- Backtested edges below show what IMPROVES our win rate further
- Default is TRADE. Only say NO_TRADE if indicators are CLEARLY unfavorable.

================================================================================
TRADE SETUP
================================================================================

Ticker: {ticker}
Direction: {direction}
Entry Price: ${entry_price:.2f}
Entry Time: {entry_time}
Model: {model}
Zone: {zone_type}

================================================================================
M1 PRICE ACTION - 15 BARS BEFORE ENTRY
================================================================================

{m1_bars_table}

================================================================================
BACKTESTED EDGES (from {total_trades:,} trades)
================================================================================

These show the WIN RATE IMPROVEMENT when conditions are met.
The "pp" = percentage points above our ~47% baseline.

H1 STRUCTURE EDGE (+36pp when aligned - THIS IS THE STRONGEST EDGE):
{structure_edges}

SMA SPREAD EDGE:
{sma_edges}

CANDLE RANGE EDGE:
{candle_range_edges}

VOLUME DELTA EDGE:
{vol_delta_edges}

================================================================================
ZONE PERFORMANCE
================================================================================

{zone_performance}

================================================================================
DECISION RULES
================================================================================

CHECK THE STRONGEST EDGE FIRST: H1 Structure
- H1 ALIGNED with {direction} (BULL for LONG, BEAR for SHORT): Strong TRADE signal (+36pp edge)
- H1 NEUTRAL: Trade is acceptable (neutral edge)
- H1 OPPOSED (BEAR for LONG, BULL for SHORT): Caution - consider NO_TRADE only if MULTIPLE other factors also unfavorable

Then check supporting indicators:
- {direction_score} score >= 5: Supportive
- Range% >= 0.12%: Movement present (favorable)
- SMA Spread aligned: Additional edge

REMEMBER: We need ~33% win rate to break even on 1.5R. Our baseline is 47%.
Even a "mediocre" setup has positive expectancy. Only reject CLEARLY BAD setups.

================================================================================
YOUR RESPONSE
================================================================================

INDICATORS (from last 5 bars):
- H1 Structure: [value] -> [ALIGNED/NEUTRAL/OPPOSED]
- {direction_score} Score: [value] -> [HIGH >=6 / MED 4-5 / LOW <4]
- Avg Range%: [value] -> [GOOD >=0.12% / LOW <0.12%]
- SMA Spread: [value] -> [ALIGNED/NEUTRAL/OPPOSED]

DECISION: [TRADE or NO_TRADE]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [2-3 sentences connecting observations to edges. If NO_TRADE, explain what specific red flags you saw.]
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_m1_bars_table(bars: List[M1BarFull]) -> str:
    """
    Format M1 bars as a comprehensive table showing all indicators.
    This is the key view - what a trader sees on their screen.
    """
    # Header row 1: Price data
    header1 = "Bar |  Time |    Open |    High |     Low |   Close |     Vol |"
    # Header row 2: Volume indicators
    header2 = "    Delta |  ROC% |   CVD |"
    # Header row 3: Price indicators
    header3 = "Range% |    VWAP |"
    # Header row 4: SMA indicators
    header4 = "   SMA9 |  SMA21 | Spread |  Mom |"
    # Header row 5: Structure
    header5 = " H1 | M15 |  M5 |  M1 |"
    # Header row 6: Scores
    header6 = " L | S"

    full_header = header1 + header2 + header3 + header4 + header5 + header6

    # Simplified single-line header for readability
    header = (
        "Bar | Time  |   Close |     Vol |   Delta |  ROC% | Range% | Spread |  Mom | "
        " H1 | M15 |  M5 |  M1 |  L |  S"
    )
    separator = "-" * len(header)

    rows = [header, separator]

    for bar in bars:
        # Format time as HH:MM
        time_str = bar.bar_time.strftime("%H:%M") if hasattr(bar.bar_time, 'strftime') else str(bar.bar_time)[:5]

        # Format SMA momentum (abbreviate)
        mom = bar.sma_momentum_label or "N/A"
        if mom == "WIDENING":
            mom = "WIDE"
        elif mom == "NARROWING":
            mom = "NARR"
        elif mom == "FLAT":
            mom = "FLAT"
        else:
            mom = mom[:4] if len(mom) > 4 else mom

        # Format structure values (abbreviate to 4 chars)
        h1 = (bar.h1_structure or "N/A")[:4]
        m15 = (bar.m15_structure or "N/A")[:4]
        m5 = (bar.m5_structure or "N/A")[:4]
        m1 = (bar.m1_structure or "N/A")[:4]

        # Handle None values
        vol_delta = bar.vol_delta if bar.vol_delta is not None else 0
        vol_roc = bar.vol_roc if bar.vol_roc is not None else 0
        candle_range = bar.candle_range_pct if bar.candle_range_pct is not None else 0
        sma_spread = bar.sma_spread if bar.sma_spread is not None else 0
        long_score = bar.long_score if bar.long_score is not None else 0
        short_score = bar.short_score if bar.short_score is not None else 0

        row = (
            f"{bar.bar_index:>3} | {time_str} | "
            f"{bar.close:>7.2f} | {bar.volume:>7,} | {vol_delta:>+7,.0f} | {vol_roc:>+5.0f}% | "
            f"{candle_range:>5.2f}% | {sma_spread:>+6.2f} | {mom:>4} | "
            f"{h1:>4} | {m15:>3} | {m5:>3} | {m1:>3} | "
            f"{long_score:>2} | {short_score:>2}"
        )
        rows.append(row)

    return "\n".join(rows)


def format_m1_bars_detailed(bars: List[M1BarFull]) -> str:
    """
    Alternative format: More detailed with all columns including OHLC.
    Use if the condensed format loses too much information.
    """
    lines = []

    for bar in bars:
        time_str = bar.bar_time.strftime("%H:%M") if hasattr(bar.bar_time, 'strftime') else str(bar.bar_time)[:5]

        line = (
            f"Bar {bar.bar_index:>3} | {time_str} | "
            f"O:{bar.open:.2f} H:{bar.high:.2f} L:{bar.low:.2f} C:{bar.close:.2f} | "
            f"Vol:{bar.volume:,} Delta:{bar.vol_delta:+,.0f} ROC:{bar.vol_roc:+.0f}% | "
            f"Range:{bar.candle_range_pct:.3f}% | "
            f"SMA:{bar.sma_spread:+.2f} ({bar.sma_momentum_label}) | "
            f"H1:{bar.h1_structure} M15:{bar.m15_structure} M5:{bar.m5_structure} M1:{bar.m1_structure} | "
            f"Scores: L={bar.long_score} S={bar.short_score}"
        )
        lines.append(line)

    return "\n".join(lines)


def get_direction_guidance(direction: str) -> str:
    """Get direction-specific interpretation guidance."""
    if direction == "LONG":
        return """- Positive Vol Delta = buying pressure (SUPPORTIVE)
- Negative Vol Delta = selling pressure (OPPOSING)
- Positive SMA Spread = bullish alignment (SUPPORTIVE)
- H1 BULL = trend aligned (SUPPORTIVE), H1 BEAR = counter-trend (OPPOSING)
- Higher Long Score = more favorable conditions"""
    else:  # SHORT
        return """- Negative Vol Delta = selling pressure (SUPPORTIVE)
- Positive Vol Delta = buying pressure (OPPOSING)
- Negative SMA Spread = bearish alignment (SUPPORTIVE)
- H1 BEAR = trend aligned (SUPPORTIVE), H1 BULL = counter-trend (OPPOSING)
- Higher Short Score = more favorable conditions"""


def format_indicator_edges(edges_data: Dict[str, Any], direction: str) -> Dict[str, str]:
    """Format indicator edges from context file for prompt inclusion."""
    edges = edges_data.get('edges', {})
    formatted = {}

    # Structure edges
    if 'structure_edge' in edges:
        struct = edges['structure_edge']
        lines = struct.get('favorable', [])[:3]  # Top 3
        formatted['structure'] = '\n'.join(f"  - {line}" for line in lines) if lines else '  - No significant edges'
    else:
        formatted['structure'] = '  - No data available'

    # SMA edges
    if 'sma_edge' in edges:
        sma = edges['sma_edge']
        lines = sma.get('favorable', [])[:3]
        formatted['sma'] = '\n'.join(f"  - {line}" for line in lines) if lines else '  - No significant edges'
    else:
        formatted['sma'] = '  - No data available'

    # Candle range edges
    if 'candle_range' in edges:
        candle = edges['candle_range']
        lines = candle.get('favorable', [])[:2] + candle.get('unfavorable', [])[:1]
        formatted['candle_range'] = '\n'.join(f"  - {line}" for line in lines) if lines else '  - No significant edges'
    else:
        formatted['candle_range'] = '  - No data available'

    # Volume delta edges
    if 'volume_delta' in edges:
        delta = edges['volume_delta']
        lines = delta.get('favorable', [])[:3]
        formatted['vol_delta'] = '\n'.join(f"  - {line}" for line in lines) if lines else '  - No significant edges'
    else:
        formatted['vol_delta'] = '  - No data available'

    # Volume ROC edges
    if 'volume_roc' in edges:
        roc = edges['volume_roc']
        lines = roc.get('favorable', [])[:3]
        formatted['vol_roc'] = '\n'.join(f"  - {line}" for line in lines) if lines else '  - No significant edges'
    else:
        formatted['vol_roc'] = '  - No data available'

    return formatted


def format_zone_performance(zone_data: Dict[str, Any], direction: str) -> str:
    """Format zone performance data for prompt inclusion."""
    if not zone_data:
        return "  - No zone performance data available"

    lines = []

    # Primary zones
    primary = zone_data.get('primary', {})
    if direction in primary:
        d = primary[direction]
        lines.append(f"  PRIMARY {direction}: Low={d.get('low', 'N/A')}%, Mid={d.get('mid', 'N/A')}%, High={d.get('high', 'N/A')}%")

    # Secondary zones
    secondary = zone_data.get('secondary', {})
    if direction in secondary:
        d = secondary[direction]
        lines.append(f"  SECONDARY {direction}: Low={d.get('low', 'N/A')}%, Mid={d.get('mid', 'N/A')}%, High={d.get('high', 'N/A')}%")

    return '\n'.join(lines) if lines else "  - No zone data for this direction"


# =============================================================================
# PROMPT BUILDERS
# =============================================================================

def build_pass1_prompt(
    ticker: str,
    direction: str,
    entry_price: float,
    entry_time: str,
    m1_bars: List[M1BarFull]
) -> str:
    """
    Build Pass 1 (Trader's Eye) prompt.

    Claude sees: Ticker, direction, 15 M1 bars with all indicators
    Claude does NOT see: Backtested edges, zone performance, historical stats
    """
    # Direction-specific parameters
    delta_preference = "positive delta (buying pressure)" if direction == "LONG" else "negative delta (selling pressure)"
    direction_score = "Long" if direction == "LONG" else "Short"

    return PASS1_TEMPLATE.format(
        ticker=ticker,
        direction=direction,
        entry_price=entry_price,
        entry_time=entry_time,
        m1_bars_table=format_m1_bars_table(m1_bars),
        delta_preference=delta_preference,
        direction_score=direction_score
    )


def build_pass2_prompt(
    ticker: str,
    direction: str,
    entry_price: float,
    entry_time: str,
    m1_bars: List[M1BarFull],
    model: str,
    zone_type: str,
    indicator_edges: Dict[str, Any],
    zone_performance: Dict[str, Any],
    model_stats: Dict[str, Any]
) -> str:
    """
    Build Pass 2 (System Decision) prompt.

    Claude sees: Everything from Pass 1 PLUS backtested edges and zone performance.
    This is the authoritative system recommendation.
    """
    # Get total trades and date range from model stats
    total_trades = 0
    models = model_stats.get('models', {})
    for model_data in models.values():
        for dir_data in model_data.values():
            if isinstance(dir_data, dict):
                total_trades += dir_data.get('trades', 0)

    date_range = model_stats.get('date_range', {})
    date_range_str = f"{date_range.get('from', 'N/A')} to {date_range.get('to', 'N/A')}"

    # Format edges
    formatted_edges = format_indicator_edges(indicator_edges, direction)

    # Format zone performance
    formatted_zones = format_zone_performance(zone_performance, direction)

    # Get direction guidance
    direction_guidance = get_direction_guidance(direction)

    # Direction-specific parameters
    direction_score = "Long" if direction == "LONG" else "Short"

    return PASS2_TEMPLATE.format(
        ticker=ticker,
        direction=direction,
        entry_price=entry_price,
        entry_time=entry_time,
        model=model or "N/A",
        zone_type=zone_type or "N/A",
        m1_bars_table=format_m1_bars_table(m1_bars),
        total_trades=total_trades if total_trades > 0 else 3615,
        structure_edges=formatted_edges.get('structure', '  - No data'),
        sma_edges=formatted_edges.get('sma', '  - No data'),
        candle_range_edges=formatted_edges.get('candle_range', '  - No data'),
        vol_delta_edges=formatted_edges.get('vol_delta', '  - No data'),
        zone_performance=formatted_zones,
        direction_score=direction_score
    )


# =============================================================================
# RESPONSE PARSING
# =============================================================================

import re
from dataclasses import dataclass, field


@dataclass
class Pass1Result:
    """Parsed result from Pass 1 (Trader's Eye)."""
    decision: str               # TRADE or NO_TRADE
    confidence: str             # HIGH, MEDIUM, LOW
    reasoning: str
    raw_response: str


@dataclass
class Pass2Result:
    """Parsed result from Pass 2 (System Decision)."""
    decision: str               # TRADE or NO_TRADE
    confidence: str             # HIGH, MEDIUM, LOW
    reasoning: str
    raw_response: str

    # Extracted indicators (Claude calculates from M1 bars)
    candle_pct: Optional[float] = None
    candle_status: Optional[str] = None     # FAVORABLE, NEUTRAL, UNFAVORABLE
    vol_delta: Optional[float] = None
    vol_delta_status: Optional[str] = None  # ALIGNED, NEUTRAL, OPPOSING
    vol_roc: Optional[float] = None
    vol_roc_status: Optional[str] = None    # ELEVATED, NORMAL, LOW
    sma_spread: Optional[float] = None
    sma_status: Optional[str] = None        # ALIGNED, NEUTRAL, OPPOSING
    h1_structure: Optional[str] = None
    h1_status: Optional[str] = None         # ALIGNED, NEUTRAL, OPPOSING


def parse_pass1_response(response: str) -> Pass1Result:
    """Parse Pass 1 (Trader's Eye) response."""

    # Extract decision
    if 'NO_TRADE' in response.upper() or 'NO TRADE' in response.upper():
        decision = 'NO_TRADE'
    elif 'TRADE' in response.upper():
        decision = 'TRADE'
    else:
        decision = 'UNKNOWN'

    # Extract confidence
    conf_match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', response, re.IGNORECASE)
    confidence = conf_match.group(1).upper() if conf_match else 'MEDIUM'

    # Extract reasoning
    reasoning_match = re.search(r'REASONING:\s*(.+?)(?:\n\n|$)', response, re.IGNORECASE | re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    return Pass1Result(
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        raw_response=response
    )


def parse_pass2_response(response: str) -> Pass2Result:
    """Parse Pass 2 (System Decision) response."""

    # Extract decision
    if 'NO_TRADE' in response.upper() or 'NO TRADE' in response.upper():
        decision = 'NO_TRADE'
    elif 'TRADE' in response.upper():
        decision = 'TRADE'
    else:
        decision = 'UNKNOWN'

    # Extract confidence
    conf_match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', response, re.IGNORECASE)
    confidence = conf_match.group(1).upper() if conf_match else 'MEDIUM'

    # Extract reasoning
    reasoning_match = re.search(r'REASONING:\s*(.+?)(?:\n\n|$)', response, re.IGNORECASE | re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    result = Pass2Result(
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        raw_response=response
    )

    # Parse extracted indicators
    # Candle Range
    candle_match = re.search(
        r'Avg Candle Range:\s*([\d.]+)%?\s*-?>?\s*\[?(FAVORABLE|NEUTRAL|UNFAVORABLE)\]?',
        response, re.IGNORECASE
    )
    if candle_match:
        result.candle_pct = float(candle_match.group(1))
        result.candle_status = candle_match.group(2).upper()

    # Vol Delta
    delta_match = re.search(
        r'Avg Vol Delta:\s*([+-]?[\d,]+)\s*-?>?\s*\[?(ALIGNED|NEUTRAL|OPPOSING)\]?',
        response, re.IGNORECASE
    )
    if delta_match:
        result.vol_delta = float(delta_match.group(1).replace(',', ''))
        result.vol_delta_status = delta_match.group(2).upper()

    # Vol ROC
    roc_match = re.search(
        r'Avg Vol ROC:\s*([+-]?[\d.]+)%?\s*-?>?\s*\[?(ELEVATED|NORMAL|LOW)\]?',
        response, re.IGNORECASE
    )
    if roc_match:
        result.vol_roc = float(roc_match.group(1))
        result.vol_roc_status = roc_match.group(2).upper()

    # SMA Spread
    sma_match = re.search(
        r'SMA Spread:\s*([+-]?[\d.]+)\s*-?>?\s*\[?(ALIGNED|NEUTRAL|OPPOSING)\]?',
        response, re.IGNORECASE
    )
    if sma_match:
        result.sma_spread = float(sma_match.group(1))
        result.sma_status = sma_match.group(2).upper()

    # H1 Structure
    h1_match = re.search(
        r'H1 Structure:\s*(BULL|BEAR|NEUT)\w*\s*-?>?\s*\[?(ALIGNED|NEUTRAL|OPPOSING)\]?',
        response, re.IGNORECASE
    )
    if h1_match:
        result.h1_structure = h1_match.group(1).upper()
        result.h1_status = h1_match.group(2).upper()

    return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def estimate_tokens(prompt: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return len(prompt) // 4


def get_prompt_version() -> str:
    """Return current prompt version."""
    return PROMPT_VERSION
