"""
Response Parser
Parses Claude API responses into structured predictions.
Matches live DOW AI Entry Qualifier format exactly.
"""

import re
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.prediction import AIPrediction
from models.trade_context import TradeContext


@dataclass
class ParsedIndicators:
    """Parsed indicator values from Claude response - matches live format."""
    candle_pct: Optional[float] = None
    candle_status: Optional[str] = None  # GOOD, OK, SKIP
    vol_delta: Optional[float] = None
    vol_delta_status: Optional[str] = None  # FAVORABLE, NEUTRAL, WEAK
    vol_roc: Optional[float] = None
    vol_roc_status: Optional[str] = None  # ELEVATED, NORMAL
    sma: Optional[str] = None  # B+, B-, N
    h1_struct: Optional[str] = None  # B+, B-, N
    snapshot: Optional[str] = None


class ResponseParser:
    """Parses Claude responses into AIPrediction objects - matches live format."""

    def parse_response(
        self,
        response_text: str,
        trade: TradeContext,
        model_used: str = "claude-sonnet-4-20250514",
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ) -> AIPrediction:
        """
        Parse Claude response into structured prediction.
        Extracts live-format indicators exactly as Entry Qualifier does.

        Args:
            response_text: Raw response text from Claude
            trade: TradeContext for metadata
            model_used: Claude model identifier
            tokens_input: Input token count
            tokens_output: Output token count
            processing_time_ms: Processing time in milliseconds

        Returns:
            AIPrediction object
        """
        # Extract prediction and confidence
        prediction, confidence = self._extract_prediction(response_text)

        # Extract individual indicators (live format)
        indicators = self._extract_indicators(response_text)

        # If parsing failed, use fallback based on health score
        if prediction is None:
            prediction, confidence = self._fallback_prediction(trade)

        ind = trade.indicators
        outcome = 'WIN' if trade.is_winner else 'LOSS'

        return AIPrediction(
            trade_id=trade.trade_id,
            prediction=prediction,
            confidence=confidence,
            reasoning=response_text,
            # Live-format indicator fields
            candle_pct=indicators.candle_pct,
            candle_status=indicators.candle_status,
            vol_delta=indicators.vol_delta,
            vol_delta_status=indicators.vol_delta_status,
            vol_roc=indicators.vol_roc,
            vol_roc_status=indicators.vol_roc_status,
            sma=indicators.sma,
            h1_struct=indicators.h1_struct,
            snapshot=indicators.snapshot,
            # Actual outcome
            actual_outcome=outcome,
            actual_pnl_r=trade.pnl_r,
            # Metadata
            model_used=model_used,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            processing_time_ms=processing_time_ms,
        )

    def _extract_indicators(self, text: str) -> ParsedIndicators:
        """
        Extract individual indicators from response text.
        Matches live DOW AI format exactly.

        Expected format:
        INDICATORS:
        - Candle %: 0.18% (GOOD)
        - Vol Delta: +45k (FAVORABLE)
        - Vol ROC: +65% (ELEVATED)
        - SMA: BULL
        - H1 Struct: NEUT

        SNAPSHOT: [2-3 sentences]
        """
        result = ParsedIndicators()

        # Candle %: value (status)
        candle_match = re.search(r'Candle\s*%?:\s*([\d.]+)%?\s*\(?(GOOD|OK|SKIP)\)?', text, re.IGNORECASE)
        if candle_match:
            result.candle_pct = float(candle_match.group(1))
            result.candle_status = candle_match.group(2).upper()

        # Vol Delta: value (status)
        delta_match = re.search(r'Vol\s*Delta:\s*([+-]?[\d,.]+)[kKmM]?\s*\(?(FAVORABLE|NEUTRAL|WEAK)\)?', text, re.IGNORECASE)
        if delta_match:
            delta_str = delta_match.group(1).replace(',', '')
            result.vol_delta = float(delta_str)
            # Handle k/M suffixes
            if 'k' in text[delta_match.start():delta_match.end()].lower():
                result.vol_delta *= 1000
            elif 'm' in text[delta_match.start():delta_match.end()].lower():
                result.vol_delta *= 1000000
            result.vol_delta_status = delta_match.group(2).upper()

        # Vol ROC: value (status)
        roc_match = re.search(r'Vol\s*ROC:\s*([+-]?[\d.]+)%?\s*\(?(ELEVATED|NORMAL)\)?', text, re.IGNORECASE)
        if roc_match:
            result.vol_roc = float(roc_match.group(1))
            result.vol_roc_status = roc_match.group(2).upper()

        # SMA: value
        sma_match = re.search(r'SMA:\s*(B\+|B-|N)', text)
        if sma_match:
            result.sma = sma_match.group(1)

        # H1 Struct: value
        h1_match = re.search(r'H1\s*Struct(?:ure)?:\s*(B\+|B-|N)', text)
        if h1_match:
            result.h1_struct = h1_match.group(1)

        # SNAPSHOT: text
        snapshot_match = re.search(r'SNAPSHOT:\s*(.+?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
        if snapshot_match:
            result.snapshot = snapshot_match.group(1).strip()

        return result

    def _extract_prediction(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract prediction and confidence from response text.

        Expected format: [TRADE or NO TRADE] | Confidence: [HIGH/MEDIUM/LOW]

        Returns:
            (prediction, confidence) tuple, or (None, None) if parsing fails
        """
        # Normalize text
        text_upper = text.upper()

        # Pattern 1: Standard format
        # [TRADE] | Confidence: HIGH
        # [NO TRADE] | Confidence: MEDIUM
        pattern1 = r'\[(TRADE|NO\s*TRADE)\]\s*\|\s*Confidence:\s*(HIGH|MEDIUM|LOW)'
        match = re.search(pattern1, text_upper)
        if match:
            prediction = 'NO_TRADE' if 'NO' in match.group(1) else 'TRADE'
            confidence = match.group(2)
            return prediction, confidence

        # Pattern 2: Without brackets
        # TRADE | Confidence: HIGH
        # NO TRADE | Confidence: LOW
        pattern2 = r'(NO\s*TRADE|TRADE)\s*\|\s*Confidence:\s*(HIGH|MEDIUM|LOW)'
        match = re.search(pattern2, text_upper)
        if match:
            prediction = 'NO_TRADE' if 'NO' in match.group(1) else 'TRADE'
            confidence = match.group(2)
            return prediction, confidence

        # Pattern 3: Just the decision word at start
        if text_upper.strip().startswith('NO TRADE') or text_upper.strip().startswith('NO_TRADE'):
            prediction = 'NO_TRADE'
        elif text_upper.strip().startswith('TRADE'):
            prediction = 'TRADE'
        else:
            prediction = None

        # Try to find confidence anywhere
        conf_match = re.search(r'Confidence:\s*(HIGH|MEDIUM|LOW)', text_upper)
        confidence = conf_match.group(1) if conf_match else None

        if prediction and confidence:
            return prediction, confidence

        # Pattern 4: Look for keywords in text
        no_trade_indicators = ['NO TRADE', 'NO_TRADE', 'AVOID', 'SKIP', 'DO NOT ENTER']
        trade_indicators = ['TAKE THE TRADE', 'ENTER', 'PROCEED']

        for indicator in no_trade_indicators:
            if indicator in text_upper:
                return 'NO_TRADE', confidence or 'MEDIUM'

        for indicator in trade_indicators:
            if indicator in text_upper:
                return 'TRADE', confidence or 'MEDIUM'

        return None, None

    def _fallback_prediction(self, trade: TradeContext) -> Tuple[str, str]:
        """
        Fallback prediction based on health score.

        Used when Claude response parsing fails.
        """
        ind = trade.indicators

        if ind is None or ind.health_score is None:
            return 'NO_TRADE', 'LOW'

        health = ind.health_score

        # High health = TRADE
        if health >= 7:
            return 'TRADE', 'HIGH'
        elif health >= 5:
            return 'TRADE', 'MEDIUM'
        elif health >= 4:
            return 'NO_TRADE', 'MEDIUM'
        else:
            return 'NO_TRADE', 'HIGH'

    def create_rule_based_prediction(self, trade: TradeContext) -> AIPrediction:
        """
        Create prediction using rule-based logic only (no Claude API).

        Useful for testing or when API is unavailable.
        """
        prediction, confidence = self._fallback_prediction(trade)

        ind = trade.indicators
        outcome = 'WIN' if trade.is_winner else 'LOSS'

        # Generate reasoning
        reasoning = self._generate_rule_reasoning(trade, prediction, confidence)

        return AIPrediction(
            trade_id=trade.trade_id,
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            health_score=ind.health_score if ind else None,
            health_label=ind.health_label if ind else None,
            structure_score=ind.structure_score if ind else None,
            volume_score=ind.volume_score if ind else None,
            price_score=ind.price_score if ind else None,
            total_healthy_count=ind.total_healthy_count if ind else None,
            actual_outcome=outcome,
            actual_pnl_r=trade.pnl_r,
            model_used='rule_based',
            prompt_version='rules_v1.0',
        )

    def _generate_rule_reasoning(
        self,
        trade: TradeContext,
        prediction: str,
        confidence: str
    ) -> str:
        """Generate reasoning text for rule-based prediction."""
        ind = trade.indicators
        if ind is None:
            return f"[{prediction}] | Confidence: {confidence}\n\nNo indicator data available."

        lines = [
            f"[{prediction}] | Confidence: {confidence}",
            "",
            "INDICATORS:",
            f"- Health: {ind.health_score}/10 ({ind.health_label})",
            f"- Structure: {ind.structure_score}/4 aligned",
            f"- Volume: {ind.volume_score}/3 aligned",
            f"- Price: {ind.price_score}/3 aligned",
            "",
            "SNAPSHOT: "
        ]

        # Build snapshot based on indicators
        reasons = []

        if ind.health_score >= 6:
            reasons.append(f"Health score {ind.health_score}/10 indicates favorable conditions")
        else:
            reasons.append(f"Health score {ind.health_score}/10 is below optimal threshold")

        if ind.volume_score == 0:
            reasons.append("Volume indicators completely misaligned")
        elif ind.volume_score == 3:
            reasons.append("Volume strongly supports entry")

        if ind.structure_score >= 3:
            reasons.append("Multi-timeframe structure aligned")
        elif ind.structure_score == 0:
            reasons.append("Structure misaligned across timeframes")

        lines.append(" ".join(reasons[:2]) + ".")

        return "\n".join(lines)
