"""
Prediction Storage
Stores AI predictions to Supabase.
Matches live DOW AI format exactly.
"""

import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG
from models.prediction import AIPrediction
from models.trade_context import TradeContext


class PredictionStorage:
    """Stores and retrieves AI predictions from Supabase - matches live format."""

    def save_prediction(self, prediction: AIPrediction, trade: TradeContext) -> bool:
        """
        Save a single prediction to the database.
        Uses live-format indicator fields.

        Args:
            prediction: AIPrediction object with live-format fields
            trade: TradeContext with trade metadata

        Returns:
            True if saved successfully
        """
        # Simple INSERT - no upsert logic, all predictions stored
        # Unique constraint on trade_id must be removed from Supabase for this to work
        query = """
        INSERT INTO ai_predictions (
            trade_id, ticker, trade_date, direction, model, zone_type,
            entry_price, entry_time,
            prediction, confidence, reasoning,
            candle_pct, candle_status,
            vol_delta, vol_delta_status,
            vol_roc, vol_roc_status,
            sma, h1_struct, snapshot,
            actual_outcome, actual_pnl_r,
            model_used, prompt_version, tokens_input, tokens_output, processing_time_ms
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s
        )
        """

        outcome = 'WIN' if trade.is_winner else 'LOSS'

        params = (
            trade.trade_id,
            trade.ticker,
            trade.trade_date,
            trade.direction,
            trade.model,
            trade.zone_type,
            trade.entry_price,
            trade.entry_time,
            prediction.prediction,
            prediction.confidence,
            prediction.reasoning,
            # Live-format indicators
            prediction.candle_pct,
            prediction.candle_status,
            prediction.vol_delta,
            prediction.vol_delta_status,
            prediction.vol_roc,
            prediction.vol_roc_status,
            prediction.sma,
            prediction.h1_struct,
            prediction.snapshot,
            # Outcome
            outcome,
            trade.pnl_r,
            # Metadata
            prediction.model_used,
            prediction.prompt_version,
            prediction.tokens_input,
            prediction.tokens_output,
            prediction.processing_time_ms,
        )

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving prediction for {trade.trade_id}: {e}", flush=True)
            print(f"  candle_status={prediction.candle_status}, vol_delta_status={prediction.vol_delta_status}", flush=True)
            print(f"  vol_roc_status={prediction.vol_roc_status}, sma={prediction.sma}, h1_struct={prediction.h1_struct}", flush=True)
            return False

    def save_predictions_batch(
        self,
        predictions: List[tuple]  # List of (AIPrediction, TradeContext)
    ) -> int:
        """
        Save multiple predictions in a batch.

        Args:
            predictions: List of (prediction, trade) tuples

        Returns:
            Number of predictions saved
        """
        saved = 0
        for prediction, trade in predictions:
            if self.save_prediction(prediction, trade):
                saved += 1
        return saved

    def get_processed_trade_ids(self) -> set:
        """Get set of trade_ids that have already been processed."""
        query = "SELECT trade_id FROM ai_predictions"

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(query)
            trade_ids = {row[0] for row in cur.fetchall()}
        conn.close()

        return trade_ids

    def check_exact_duplicates(self, trade_ids: List[str], model_used: str, prompt_version: str) -> Dict[str, Dict]:
        """
        Check for exact duplicate predictions in the database.

        An exact duplicate means same trade_id, model_used, and prompt_version.

        Args:
            trade_ids: List of trade_ids to check
            model_used: The Claude model being used
            prompt_version: The prompt version being used

        Returns:
            Dict mapping trade_id to existing prediction data for duplicates
        """
        if not trade_ids:
            return {}

        query = """
        SELECT trade_id, prediction, confidence, model_used, prompt_version, created_at
        FROM ai_predictions
        WHERE trade_id = ANY(%s)
          AND model_used = %s
          AND prompt_version = %s
        """

        duplicates = {}
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute(query, (trade_ids, model_used, prompt_version))
                for row in cur.fetchall():
                    duplicates[row[0]] = {
                        'prediction': row[1],
                        'confidence': row[2],
                        'model_used': row[3],
                        'prompt_version': row[4],
                        'created_at': row[5]
                    }
            conn.close()
        except Exception as e:
            print(f"Error checking duplicates: {e}", flush=True)

        return duplicates

    def get_accuracy_summary(self) -> Dict[str, Any]:
        """Get summary accuracy statistics."""
        query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_predictions,
            SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_predictions,
            SUM(CASE WHEN prediction = 'TRADE' AND prediction_correct THEN 1 ELSE 0 END) as trade_correct,
            SUM(CASE WHEN prediction = 'NO_TRADE' AND prediction_correct THEN 1 ELSE 0 END) as no_trade_correct
        FROM ai_predictions
        WHERE prediction_correct IS NOT NULL
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            result = dict(cur.fetchone())
        conn.close()

        # Calculate percentages
        total = result['total'] or 1
        result['overall_accuracy'] = round(100.0 * (result['correct'] or 0) / total, 1)

        trade_total = result['trade_predictions'] or 1
        result['trade_accuracy'] = round(100.0 * (result['trade_correct'] or 0) / trade_total, 1)

        no_trade_total = result['no_trade_predictions'] or 1
        result['no_trade_accuracy'] = round(100.0 * (result['no_trade_correct'] or 0) / no_trade_total, 1)

        return result
