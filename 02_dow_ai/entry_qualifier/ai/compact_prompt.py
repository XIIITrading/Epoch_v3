"""
Compact Entry Prompt Builder v2.0
Epoch Trading System v2.0 - XIII Trading LLC

Builds prompts for DOW AI entry queries.
Supports v2.0 architecture where Claude is the decision engine.

v2.0: Claude receives raw data + full context files and applies reasoning.
Legacy: Claude receives pre-calculated labels + summarized edges.

Imports from shared dow_helper_prompt.py to ensure consistency with batch system.
"""

from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Ensure ai_context module is importable
_dow_ai_dir = Path(__file__).parent.parent.parent.resolve()
if str(_dow_ai_dir) not in sys.path:
    sys.path.insert(0, str(_dow_ai_dir))

# Ensure calculations module is importable
_entry_qualifier_dir = Path(__file__).parent.parent.resolve()
if str(_entry_qualifier_dir) not in sys.path:
    sys.path.insert(0, str(_entry_qualifier_dir))

# Import shared prompt components from ai_context
from ai_context.dow_helper_prompt import (
    # v2.0 imports
    DOW_PROMPT_TEMPLATE_V2,
    PROMPT_VERSION,
    build_prompt_v2,
    calculate_vol_delta_zscore,
    # Legacy imports
    DOW_PROMPT_TEMPLATE,
    DIRECTION_RULES,
    get_candle_status,
    get_vol_delta_status,
    get_vol_roc_status,
    get_direction_rules,
    format_price_line_live,
    build_prompt as build_shared_prompt,
    estimate_tokens as _estimate_tokens
)


def build_compact_prompt(
    ticker: str,
    direction: str,
    current_price: float,
    bars_data: List[Dict],
    ai_context: Dict,
    zone_data: Optional[Dict] = None,
    use_v2: bool = True
) -> str:
    """
    Build a prompt for DOW AI entry analysis.

    v2.0 (default): Claude receives raw data + full context files.
    Legacy: Claude receives pre-calculated labels + summarized edges.

    Args:
        ticker: Stock symbol (e.g., "SPY")
        direction: Trade direction (LONG or SHORT)
        current_price: Current price from latest bar
        bars_data: List of processed bar dicts from Entry Qualifier
        ai_context: Combined context from AIContextLoader.load_all()
        zone_data: Optional zone data from Supabase
        use_v2: If True, use v2.0 architecture. If False, use legacy.

    Returns:
        Formatted prompt string ready for Claude API
    """
    # Calculate 5-bar averages from bars data
    candle_range, vol_delta, vol_roc, sma_config, m5_structure, m15_structure, h1_structure = _calculate_5bar_averages(bars_data)

    # Extract ramp-up deltas for Z-score
    rampup_deltas = _extract_rampup_deltas(bars_data)

    # Format price line for live trading
    price_line = format_price_line_live(
        current_price=current_price,
        timestamp=datetime.now().strftime("%H:%M:%S ET")
    )

    if use_v2:
        # v2.0: Claude receives raw data + full context files
        prompt = build_prompt_v2(
            ticker=ticker,
            direction=direction,
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            rampup_deltas=rampup_deltas,
            indicator_edges=ai_context.get('indicator_edges', {}),
            model_stats=ai_context.get('model_stats', {}),
            zone_performance=ai_context.get('zone_performance', {})
        )
    else:
        # Legacy: Pre-calculated labels + summarized edges
        # Get historical direction stats from zone performance
        zone_perf = ai_context.get('zone_performance', {})
        primary_dir = zone_perf.get('primary', {}).get(direction, {})
        direction_win_rate = primary_dir.get('mid', 'N/A')

        # Get relevant edges
        edge_summary = _build_edge_summary(ai_context, direction)

        # Build zone info
        zone_info = _build_zone_info(zone_data, current_price)

        # Build prompt using shared function
        prompt = build_shared_prompt(
            ticker=ticker,
            direction=direction,
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            direction_win_rate=str(direction_win_rate),
            edge_summary=edge_summary,
            zone_info=zone_info,
            rampup_deltas=rampup_deltas
        )

    return prompt


def _extract_rampup_deltas(bars_data: List[Dict]) -> List[float]:
    """Extract vol delta values from all bars for Z-score calculation."""
    if not bars_data:
        return []
    return [b.get('roll_delta', 0) for b in bars_data if b.get('roll_delta') is not None]


def _calculate_5bar_averages(bars_data: List[Dict]) -> tuple:
    """Calculate 5-bar averages and get latest categorical indicators."""
    if not bars_data:
        return 0.0, 0.0, 0.0, "N/A", "N/A", "N/A", "N/A"

    # Take last 5 bars for averaging
    recent_bars = bars_data[-5:] if len(bars_data) >= 5 else bars_data

    # Calculate averages
    candle_ranges = [b.get('candle_range_pct', 0) for b in recent_bars]
    vol_deltas = [b.get('roll_delta', 0) for b in recent_bars if b.get('roll_delta') is not None]
    vol_rocs = [b.get('volume_roc', 0) for b in recent_bars if b.get('volume_roc') is not None]

    avg_candle_range = sum(candle_ranges) / len(candle_ranges) if candle_ranges else 0
    avg_vol_delta = sum(vol_deltas) / len(vol_deltas) if vol_deltas else 0
    avg_vol_roc = sum(vol_rocs) / len(vol_rocs) if vol_rocs else 0

    # Get most recent values for categorical indicators
    latest = recent_bars[-1] if recent_bars else {}
    sma_config = latest.get('sma_display', 'N/A')
    m5_structure = latest.get('m5_display', 'N/A')
    m15_structure = latest.get('m15_display', 'N/A')
    h1_structure = latest.get('h1_display', 'N/A')

    return avg_candle_range, avg_vol_delta, avg_vol_roc, sma_config, m5_structure, m15_structure, h1_structure


def _build_edge_summary(ai_context: Dict, direction: str) -> str:
    """Build edge summary from indicator edges context."""
    edges_data = ai_context.get('indicator_edges', {}).get('edges', {})

    if not edges_data:
        return "- No validated edges loaded"

    lines = []
    count = 0
    max_edges = 3

    for indicator, edge_info in edges_data.items():
        if count >= max_edges:
            break

        favorable = edge_info.get('favorable', [])
        best_for = edge_info.get('best_for', 'ALL')

        # Include if applicable to this direction
        if best_for in [direction, 'ALL'] and favorable:
            # Take first favorable condition
            condition = favorable[0] if isinstance(favorable, list) else favorable
            lines.append(f"- {indicator}: {condition}")
            count += 1

    if not lines:
        return "- No edges specific to this direction"

    return "\n".join(lines)


def _build_zone_info(zone_data: Optional[Dict], current_price: float) -> str:
    """Build zone information section."""
    if not zone_data:
        return "- Zone data unavailable"

    zone_id = zone_data.get('zone_id', 'N/A')
    zone_high = zone_data.get('zone_high')
    zone_low = zone_data.get('zone_low')

    lines = []

    if zone_high and zone_low:
        lines.append(f"- Zone: {zone_id} | Range: ${zone_low:.2f} - ${zone_high:.2f}")

        # Price position
        if current_price > zone_high:
            lines.append(f"- Position: ABOVE zone")
        elif current_price < zone_low:
            lines.append(f"- Position: BELOW zone")
        else:
            lines.append(f"- Position: INSIDE zone")

    return "\n".join(lines) if lines else "- Zone data incomplete"


def estimate_token_count(prompt: str) -> int:
    """Estimate token count for the prompt (rough approximation)."""
    return _estimate_tokens(prompt)


def get_prompt_version() -> str:
    """Return current prompt version."""
    return PROMPT_VERSION
