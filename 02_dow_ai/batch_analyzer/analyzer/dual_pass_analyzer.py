"""
DOW AI v3.0 Dual Pass Analyzer
Epoch Trading System - XIII Trading LLC

Orchestrates dual-pass analysis:
- Pass 1 (Trader's Eye): Raw M1 bars + indicators, no backtested context
- Pass 2 (System Decision): Same data + learned edges from backtesting

The key insight: Pass 1 measures Claude's native pattern recognition.
Pass 2 measures the value added by backtested knowledge.
Comparing them tells us if the context helps or hurts.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import anthropic

# Import v3.0 prompt templates
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ai_context'))

from prompt_v3 import (
    M1BarFull,
    TradeForAnalysis,
    PROMPT_VERSION,
    build_pass1_prompt,
    build_pass2_prompt,
    parse_pass1_response,
    parse_pass2_response,
    Pass1Result,
    Pass2Result,
    estimate_tokens
)


logger = logging.getLogger(__name__)


@dataclass
class DualPassResult:
    """
    Combined result from both passes.
    This is what gets saved to dual_pass_analysis table.
    """
    # Trade identification
    trade_id: str
    ticker: str
    trade_date: str
    entry_time: str
    direction: str
    entry_price: float
    model: str
    zone_type: str

    # Pass 1 results
    pass1: Pass1Result
    pass1_tokens_input: int
    pass1_tokens_output: int
    pass1_latency_ms: int

    # Pass 2 results
    pass2: Pass2Result
    pass2_tokens_input: int
    pass2_tokens_output: int
    pass2_latency_ms: int

    # Actual outcome
    actual_outcome: str
    actual_pnl_r: Optional[float]

    @property
    def passes_agree(self) -> bool:
        """Do both passes make the same decision?"""
        return self.pass1.decision == self.pass2.decision

    @property
    def pass1_correct(self) -> Optional[bool]:
        """Was Pass 1 prediction correct?"""
        if not self.actual_outcome:
            return None
        if self.pass1.decision == "TRADE":
            return self.actual_outcome == "WIN"
        elif self.pass1.decision == "NO_TRADE":
            return self.actual_outcome == "LOSS"
        return None

    @property
    def pass2_correct(self) -> Optional[bool]:
        """Was Pass 2 prediction correct?"""
        if not self.actual_outcome:
            return None
        if self.pass2.decision == "TRADE":
            return self.actual_outcome == "WIN"
        elif self.pass2.decision == "NO_TRADE":
            return self.actual_outcome == "LOSS"
        return None

    @property
    def disagreement_winner(self) -> Optional[str]:
        """When passes disagree, who was right?"""
        if self.passes_agree:
            return None

        p1_correct = self.pass1_correct
        p2_correct = self.pass2_correct

        if p1_correct and not p2_correct:
            return 'PASS1'
        elif p2_correct and not p1_correct:
            return 'PASS2'
        elif not p1_correct and not p2_correct:
            return 'BOTH_WRONG'
        else:
            return None  # Shouldn't happen if they disagree


class DualPassAnalyzer:
    """
    Runs dual-pass analysis on trades.

    Pass 1: Trader's Eye
        - Claude sees: ticker, direction, 15 M1 bars with all indicators
        - Claude does NOT see: backtested edges, zone performance
        - Purpose: What would a skilled discretionary trader see?

    Pass 2: System Decision
        - Claude sees: Everything from Pass 1 PLUS learned edges
        - Purpose: System recommendation with statistical backing
        - Authority: This is the trusted recommendation
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 500,
        ai_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the analyzer.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
            model: Claude model to use
            max_tokens: Max response tokens
            ai_context: Pre-loaded AI context (indicator_edges, zone_performance, model_stats)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.ai_context = ai_context or {}

        logger.info(f"DualPassAnalyzer initialized with model={model}, max_tokens={max_tokens}")

    def analyze_trade(self, trade: TradeForAnalysis) -> DualPassResult:
        """
        Run both passes for a single trade.

        Args:
            trade: TradeForAnalysis with all M1 bar data

        Returns:
            DualPassResult with both pass results and metrics
        """
        logger.info(f"Analyzing {trade.trade_id}: {trade.ticker} {trade.direction}")

        # Validate we have M1 bars
        if not trade.m1_bars or len(trade.m1_bars) < 5:
            raise ValueError(f"Insufficient M1 bars for {trade.trade_id}: got {len(trade.m1_bars) if trade.m1_bars else 0}")

        # === PASS 1: Trader's Eye ===
        pass1_prompt = build_pass1_prompt(
            ticker=trade.ticker,
            direction=trade.direction,
            entry_price=trade.entry_price,
            entry_time=trade.entry_time,
            m1_bars=trade.m1_bars
        )

        logger.debug(f"Pass 1 prompt: {estimate_tokens(pass1_prompt)} estimated tokens")

        start_time = time.time()
        pass1_response = self._call_claude(pass1_prompt)
        pass1_latency = int((time.time() - start_time) * 1000)

        pass1_result = parse_pass1_response(pass1_response['content'])

        logger.info(f"  Pass 1: {pass1_result.decision} ({pass1_result.confidence}) - {pass1_latency}ms")

        # Small delay between calls to be respectful of rate limits
        time.sleep(0.5)

        # === PASS 2: System Decision ===
        pass2_prompt = build_pass2_prompt(
            ticker=trade.ticker,
            direction=trade.direction,
            entry_price=trade.entry_price,
            entry_time=trade.entry_time,
            m1_bars=trade.m1_bars,
            model=trade.model,
            zone_type=trade.zone_type,
            indicator_edges=self.ai_context.get('indicator_edges', {}),
            zone_performance=self.ai_context.get('zone_performance', {}),
            model_stats=self.ai_context.get('model_stats', {})
        )

        logger.debug(f"Pass 2 prompt: {estimate_tokens(pass2_prompt)} estimated tokens")

        start_time = time.time()
        pass2_response = self._call_claude(pass2_prompt)
        pass2_latency = int((time.time() - start_time) * 1000)

        pass2_result = parse_pass2_response(pass2_response['content'])

        logger.info(f"  Pass 2: {pass2_result.decision} ({pass2_result.confidence}) - {pass2_latency}ms")

        # Build combined result
        result = DualPassResult(
            trade_id=trade.trade_id,
            ticker=trade.ticker,
            trade_date=trade.trade_date,
            entry_time=trade.entry_time,
            direction=trade.direction,
            entry_price=trade.entry_price,
            model=trade.model,
            zone_type=trade.zone_type,
            pass1=pass1_result,
            pass1_tokens_input=pass1_response['input_tokens'],
            pass1_tokens_output=pass1_response['output_tokens'],
            pass1_latency_ms=pass1_latency,
            pass2=pass2_result,
            pass2_tokens_input=pass2_response['input_tokens'],
            pass2_tokens_output=pass2_response['output_tokens'],
            pass2_latency_ms=pass2_latency,
            actual_outcome=trade.actual_outcome,
            actual_pnl_r=trade.pnl_r
        )

        # Log comparison
        agree_str = "AGREE" if result.passes_agree else "DISAGREE"
        p1_correct = "CORRECT" if result.pass1_correct else "WRONG"
        p2_correct = "CORRECT" if result.pass2_correct else "WRONG"
        logger.info(f"  Outcome: {trade.actual_outcome} | {agree_str} | P1:{p1_correct} P2:{p2_correct}")

        return result

    def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """
        Make a Claude API call.

        Returns:
            Dict with 'content', 'input_tokens', 'output_tokens'
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                'content': response.content[0].text,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }

        except anthropic.RateLimitError:
            logger.warning("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return self._call_claude(prompt)

        except anthropic.APIError as e:
            logger.error(f"API error: {e}")
            raise

    def analyze_batch(
        self,
        trades: List[TradeForAnalysis],
        delay_between_trades: float = 2.5
    ) -> List[DualPassResult]:
        """
        Analyze multiple trades with rate limiting.

        Args:
            trades: List of trades to analyze
            delay_between_trades: Seconds to wait between trades (2 API calls each)

        Returns:
            List of DualPassResult objects
        """
        results = []

        for i, trade in enumerate(trades, 1):
            logger.info(f"\n[{i}/{len(trades)}] Processing {trade.trade_id}")

            try:
                result = self.analyze_trade(trade)
                results.append(result)

                # Rate limiting - we make 2 calls per trade
                # At 50 req/min, that's 25 trades/min max
                if i < len(trades):
                    logger.debug(f"Waiting {delay_between_trades}s before next trade...")
                    time.sleep(delay_between_trades)

            except Exception as e:
                logger.error(f"Failed to analyze {trade.trade_id}: {e}")
                continue

        return results
