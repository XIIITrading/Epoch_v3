"""
Batch Prompt Builder v2.0
Builds prompts for DOW AI batch analysis using v2.0 architecture.

v2.0 Architecture - Claude as Decision Engine:
- Claude receives RAW indicator values (no pre-calculated labels)
- Claude receives full context files as "learned knowledge"
- Claude applies reasoning using context to make TRADE/NO_TRADE decisions

Imports from shared dow_helper_prompt.py to ensure consistency with live system.
"""

from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Set up paths for imports
BATCH_DIR = Path(__file__).parent.parent.resolve()
DOW_AI_DIR = BATCH_DIR.parent.resolve()
sys.path.insert(0, str(BATCH_DIR))
sys.path.insert(0, str(DOW_AI_DIR))

from models.trade_context import TradeContext, M1Bar

# Import shared prompt components from ai_context
from ai_context.dow_helper_prompt import (
    # V2.0 imports
    DOW_PROMPT_TEMPLATE_V2,
    PROMPT_VERSION,
    build_prompt_v2,
    format_price_line_batch,
    estimate_tokens,
    calculate_vol_delta_zscore,
    # Legacy imports for backwards compatibility
    DOW_PROMPT_TEMPLATE,
    DIRECTION_RULES,
    get_candle_status,
    get_vol_delta_status,
    get_vol_roc_status,
    get_direction_rules,
    build_prompt as build_shared_prompt
)


class BatchPromptBuilder:
    """Builds prompts for batch DOW AI analysis - supports v1.x and v2.0 modes."""

    def __init__(self, use_v2: bool = True):
        """
        Initialize prompt builder.

        Args:
            use_v2: If True, use v2.0 architecture (Claude as decision engine).
                   If False, use v1.x legacy mode.
        """
        self.use_v2 = use_v2

    def build_prompt(self, trade: TradeContext) -> str:
        """
        Build a prompt for a trade.

        v2.0: Claude receives raw data + full context files.
        v1.x: Claude receives pre-calculated labels + summary edges.

        Args:
            trade: TradeContext with all indicators loaded

        Returns:
            Formatted prompt string
        """
        if self.use_v2:
            return self._build_prompt_v2(trade)
        else:
            return self._build_prompt_legacy(trade)

    def _build_prompt_v2(self, trade: TradeContext) -> str:
        """
        Build v2.0 prompt - Claude as decision engine.
        Claude receives raw indicators + full context files.
        """
        ind = trade.indicators

        # Calculate 5-bar averages from M1 bars
        candle_range, vol_delta, vol_roc = self._calculate_5bar_averages(trade.m1_bars)

        # Extract ramp-up deltas for Z-score calculation
        rampup_deltas = self._extract_rampup_deltas(trade.m1_bars)

        # Get SMA config and H1 structure from indicators
        sma_config = ind.sma_alignment or "N/A" if ind else "N/A"
        h1_structure = ind.h1_structure or "N/A" if ind else "N/A"

        # Format price line for batch (historical data)
        price_line = format_price_line_batch(
            entry_price=trade.entry_price,
            trade_date=trade.trade_date.strftime("%Y-%m-%d"),
            entry_time=trade.entry_time.strftime("%H:%M")
        )

        # Get full context files (not summaries)
        ai_context = trade.ai_context or {}
        indicator_edges = ai_context.get('indicator_edges', {})
        model_stats = ai_context.get('model_stats', {})
        zone_performance = ai_context.get('zone_performance', {})

        # Build v2.0 prompt with raw data + full context
        prompt = build_prompt_v2(
            ticker=trade.ticker,
            direction=trade.direction,
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            rampup_deltas=rampup_deltas,
            indicator_edges=indicator_edges,
            model_stats=model_stats,
            zone_performance=zone_performance
        )

        return prompt

    def _build_prompt_legacy(self, trade: TradeContext) -> str:
        """
        Build v1.x legacy prompt with pre-calculated labels.
        Kept for backwards compatibility and comparison testing.
        """
        ind = trade.indicators

        # Calculate 5-bar averages from M1 bars (matches live system)
        candle_range, vol_delta, vol_roc = self._calculate_5bar_averages(trade.m1_bars)

        # Get SMA config and H1 structure from indicators
        sma_config = ind.sma_alignment or "N/A" if ind else "N/A"
        h1_structure = ind.h1_structure or "N/A" if ind else "N/A"

        # Format edge summary
        edge_summary = self._format_edge_summary(trade.ai_context, trade.direction)

        # Get direction win rate from AI context
        direction_win_rate = self._get_direction_win_rate(trade.ai_context, trade.direction)

        # Format zone info
        zone_info = self._format_zone_info(trade)

        # Format price line for batch (historical data)
        price_line = format_price_line_batch(
            entry_price=trade.entry_price,
            trade_date=trade.trade_date.strftime("%Y-%m-%d"),
            entry_time=trade.entry_time.strftime("%H:%M")
        )

        # Extract ramp-up deltas for Z-score
        rampup_deltas = self._extract_rampup_deltas(trade.m1_bars)

        # Build prompt using shared function
        prompt = build_shared_prompt(
            ticker=trade.ticker,
            direction=trade.direction,
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            direction_win_rate=direction_win_rate,
            edge_summary=edge_summary,
            zone_info=zone_info,
            rampup_deltas=rampup_deltas
        )

        return prompt

    def _extract_rampup_deltas(self, bars: List[M1Bar]) -> List[float]:
        """Extract vol delta values from all bars for Z-score calculation."""
        if not bars:
            return []
        return [b.vol_delta for b in bars if b.vol_delta is not None]

    def _calculate_5bar_averages(self, bars: List[M1Bar]) -> tuple:
        """Calculate 5-bar rolling averages matching live system."""
        if not bars:
            return 0.0, 0.0, 0.0

        # Take last 5 bars
        recent = bars[-5:] if len(bars) >= 5 else bars

        # Calculate averages
        candle_ranges = [b.candle_range_pct or 0 for b in recent]
        vol_deltas = [b.vol_delta or 0 for b in recent if b.vol_delta is not None]
        vol_rocs = [b.vol_roc or 0 for b in recent if b.vol_roc is not None]

        avg_candle = sum(candle_ranges) / len(candle_ranges) if candle_ranges else 0
        avg_delta = sum(vol_deltas) / len(vol_deltas) if vol_deltas else 0
        avg_roc = sum(vol_rocs) / len(vol_rocs) if vol_rocs else 0

        return avg_candle, avg_delta, avg_roc

    def _get_direction_win_rate(self, ai_context: Optional[Dict[str, Any]], direction: str) -> str:
        """Get historical win rate for direction from AI context."""
        if not ai_context:
            return "N/A"

        zone_perf = ai_context.get('zone_performance', {})
        primary = zone_perf.get('primary', {}).get(direction, {})
        return str(primary.get('mid', 'N/A'))

    def _format_zone_info(self, trade: TradeContext) -> str:
        """Format zone information section."""
        # Use zone data from trade if available
        zone_type = trade.zone_type or "N/A"
        return f"- Zone Type: {zone_type}\n- Position: At entry"

    def _format_edge_summary(self, ai_context: Optional[Dict[str, Any]], direction: str) -> str:
        """Format edge summary from AI context - matches live format."""
        if not ai_context:
            return "- No validated edges loaded"

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
                condition = favorable[0] if isinstance(favorable, list) else favorable
                lines.append(f"- {indicator}: {condition}")
                count += 1

        if not lines:
            return "- No edges specific to this direction"

        return "\n".join(lines)

    def get_prompt_version(self) -> str:
        """Return current prompt version."""
        return PROMPT_VERSION
