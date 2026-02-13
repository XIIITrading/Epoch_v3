"""
DOW AI v3.0 Dual Pass Storage
Epoch Trading System - XIII Trading LLC

Handles saving dual-pass analysis results to Supabase.
"""

import logging
from typing import Optional, Set
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG

# Import from analyzer
sys.path.insert(0, str(Path(__file__).parent.parent / 'analyzer'))
from dual_pass_analyzer import DualPassResult


logger = logging.getLogger(__name__)


class DualPassStorage:
    """
    Handles persistence of dual-pass analysis results.

    Uses upsert logic to allow re-running analysis on same trades
    with updated prompts.
    """

    def __init__(self):
        """Initialize storage with database config."""
        self.table = "dual_pass_analysis"

    def save_result(self, result: DualPassResult) -> bool:
        """
        Save a dual-pass result to the database.

        Uses upsert (ON CONFLICT UPDATE) to allow re-processing trades.

        Args:
            result: DualPassResult from analyzer

        Returns:
            True if saved successfully
        """
        query = """
        INSERT INTO dual_pass_analysis (
            trade_id,
            ticker, trade_date, entry_time, direction, entry_price,
            model, zone_type,

            -- Pass 1
            pass1_decision, pass1_confidence, pass1_reasoning,
            pass1_tokens_input, pass1_tokens_output, pass1_latency_ms,

            -- Pass 2
            pass2_decision, pass2_confidence, pass2_reasoning,
            pass2_tokens_input, pass2_tokens_output, pass2_latency_ms,

            -- Extracted indicators (from Pass 2)
            candle_pct, candle_status,
            vol_delta, vol_delta_status,
            vol_roc, vol_roc_status,
            sma_spread, sma_status,
            h1_structure, h1_status,

            -- Outcome
            actual_outcome, actual_pnl_r,

            -- Metadata
            prompt_version, model_used, analyzed_at
        ) VALUES (
            %s,
            %s, %s, %s, %s, %s,
            %s, %s,

            %s, %s, %s,
            %s, %s, %s,

            %s, %s, %s,
            %s, %s, %s,

            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,

            %s, %s,

            %s, %s, %s
        )
        ON CONFLICT (trade_id) DO UPDATE SET
            pass1_decision = EXCLUDED.pass1_decision,
            pass1_confidence = EXCLUDED.pass1_confidence,
            pass1_reasoning = EXCLUDED.pass1_reasoning,
            pass1_tokens_input = EXCLUDED.pass1_tokens_input,
            pass1_tokens_output = EXCLUDED.pass1_tokens_output,
            pass1_latency_ms = EXCLUDED.pass1_latency_ms,

            pass2_decision = EXCLUDED.pass2_decision,
            pass2_confidence = EXCLUDED.pass2_confidence,
            pass2_reasoning = EXCLUDED.pass2_reasoning,
            pass2_tokens_input = EXCLUDED.pass2_tokens_input,
            pass2_tokens_output = EXCLUDED.pass2_tokens_output,
            pass2_latency_ms = EXCLUDED.pass2_latency_ms,

            candle_pct = EXCLUDED.candle_pct,
            candle_status = EXCLUDED.candle_status,
            vol_delta = EXCLUDED.vol_delta,
            vol_delta_status = EXCLUDED.vol_delta_status,
            vol_roc = EXCLUDED.vol_roc,
            vol_roc_status = EXCLUDED.vol_roc_status,
            sma_spread = EXCLUDED.sma_spread,
            sma_status = EXCLUDED.sma_status,
            h1_structure = EXCLUDED.h1_structure,
            h1_status = EXCLUDED.h1_status,

            prompt_version = EXCLUDED.prompt_version,
            model_used = EXCLUDED.model_used,
            analyzed_at = EXCLUDED.analyzed_at
        """

        params = (
            result.trade_id,
            result.ticker,
            result.trade_date,
            result.entry_time,
            result.direction,
            float(result.entry_price),
            result.model,
            result.zone_type,

            # Pass 1
            result.pass1.decision,
            result.pass1.confidence,
            result.pass1.reasoning,
            result.pass1_tokens_input,
            result.pass1_tokens_output,
            result.pass1_latency_ms,

            # Pass 2
            result.pass2.decision,
            result.pass2.confidence,
            result.pass2.reasoning,
            result.pass2_tokens_input,
            result.pass2_tokens_output,
            result.pass2_latency_ms,

            # Extracted indicators
            result.pass2.candle_pct,
            result.pass2.candle_status,
            result.pass2.vol_delta,
            result.pass2.vol_delta_status,
            result.pass2.vol_roc,
            result.pass2.vol_roc_status,
            result.pass2.sma_spread,
            result.pass2.sma_status,
            result.pass2.h1_structure,
            result.pass2.h1_status,

            # Outcome
            result.actual_outcome,
            float(result.actual_pnl_r) if result.actual_pnl_r else None,

            # Metadata
            'v3.0',
            'claude-sonnet-4-20250514',
            datetime.now()
        )

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute(query, params)
            conn.commit()
            conn.close()

            logger.debug(f"Saved result for {result.trade_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save {result.trade_id}: {e}")
            return False

    def get_analyzed_trade_ids(self) -> Set[str]:
        """
        Get set of trade IDs that have already been analyzed.

        Used for resume functionality - skip trades already processed.

        Returns:
            Set of trade_id strings
        """
        query = "SELECT trade_id FROM dual_pass_analysis"

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            conn.close()

            return {row[0] for row in rows}

        except Exception as e:
            logger.error(f"Failed to get analyzed trade IDs: {e}")
            return set()

    def get_accuracy_summary(self) -> dict:
        """
        Get quick accuracy summary for console display.

        Returns:
            Dict with pass1_accuracy, pass2_accuracy, agreement_rate, etc.
        """
        query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END) as pass1_trades,
            SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END) as pass2_trades,
            SUM(CASE WHEN pass1_correct THEN 1 ELSE 0 END) as pass1_correct,
            SUM(CASE WHEN pass2_correct THEN 1 ELSE 0 END) as pass2_correct,
            SUM(CASE WHEN passes_agree THEN 1 ELSE 0 END) as agreements,
            SUM(CASE WHEN disagreement_winner = 'PASS1' THEN 1 ELSE 0 END) as pass1_wins,
            SUM(CASE WHEN disagreement_winner = 'PASS2' THEN 1 ELSE 0 END) as pass2_wins,
            SUM(CASE WHEN disagreement_winner = 'BOTH_WRONG' THEN 1 ELSE 0 END) as both_wrong
        FROM dual_pass_analysis
        WHERE actual_outcome IS NOT NULL
        """

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                row = cur.fetchone()
            conn.close()

            if not row or row['total'] == 0:
                return {'total': 0}

            total = row['total']
            return {
                'total': total,
                'pass1_trade_rate': row['pass1_trades'] / total * 100,
                'pass2_trade_rate': row['pass2_trades'] / total * 100,
                'pass1_accuracy': row['pass1_correct'] / total * 100,
                'pass2_accuracy': row['pass2_correct'] / total * 100,
                'agreement_rate': row['agreements'] / total * 100,
                'pass1_wins_disagreement': row['pass1_wins'],
                'pass2_wins_disagreement': row['pass2_wins'],
                'both_wrong_disagreement': row['both_wrong']
            }

        except Exception as e:
            logger.error(f"Failed to get accuracy summary: {e}")
            return {'total': 0, 'error': str(e)}
