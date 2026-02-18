"""
AI Prediction Model
Represents a DOW AI prediction for a trade.
Matches live Entry Qualifier format exactly.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AIPrediction:
    """
    AI prediction result for a trade.
    Fields match live DOW AI Entry Qualifier output exactly.
    """
    # Trade reference
    trade_id: str

    # Prediction (matches live format)
    prediction: str  # 'TRADE' or 'NO_TRADE'
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    reasoning: str   # Full response text

    # Live-format indicators (EXACTLY matches Entry Qualifier)
    candle_pct: Optional[float] = None      # e.g., 0.18
    candle_status: Optional[str] = None     # GOOD, OK, SKIP
    vol_delta: Optional[float] = None       # e.g., 45000
    vol_delta_status: Optional[str] = None  # FAVORABLE, NEUTRAL, WEAK
    vol_roc: Optional[float] = None         # e.g., 65
    vol_roc_status: Optional[str] = None    # ELEVATED, NORMAL
    sma: Optional[str] = None               # B+, B-, N
    h1_struct: Optional[str] = None         # B+, B-, N
    snapshot: Optional[str] = None          # 2-3 sentence summary

    # Actual outcome
    actual_outcome: Optional[str] = None  # 'WIN' or 'LOSS'
    actual_pnl_r: Optional[float] = None

    # Metadata
    model_used: str = "claude-sonnet-4-20250514"
    prompt_version: str = "v2.0"  # Updated for live-format
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    @property
    def prediction_correct(self) -> Optional[bool]:
        """
        Determine if prediction was correct.
        TRADE is correct if outcome is WIN.
        NO_TRADE is correct if outcome is LOSS.
        """
        if self.actual_outcome is None:
            return None

        if self.prediction == 'TRADE':
            return self.actual_outcome == 'WIN'
        else:  # NO_TRADE
            return self.actual_outcome == 'LOSS'

    def to_db_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            'trade_id': self.trade_id,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            # Live-format indicators
            'candle_pct': self.candle_pct,
            'candle_status': self.candle_status,
            'vol_delta': self.vol_delta,
            'vol_delta_status': self.vol_delta_status,
            'vol_roc': self.vol_roc,
            'vol_roc_status': self.vol_roc_status,
            'sma': self.sma,
            'h1_struct': self.h1_struct,
            'snapshot': self.snapshot,
            # Outcome
            'actual_outcome': self.actual_outcome,
            'actual_pnl_r': self.actual_pnl_r,
            # Metadata
            'model_used': self.model_used,
            'prompt_version': self.prompt_version,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'processing_time_ms': self.processing_time_ms,
        }
