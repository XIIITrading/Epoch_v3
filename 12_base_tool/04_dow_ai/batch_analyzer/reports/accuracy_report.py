"""
Accuracy Report Generator
Generates reports on DOW AI prediction accuracy.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG


class AccuracyReporter:
    """Generates accuracy reports for AI predictions."""

    def get_overall_summary(self) -> Dict[str, Any]:
        """Get overall accuracy summary."""
        query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_count,
            SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_count,
            SUM(CASE WHEN prediction = 'TRADE' AND prediction_correct THEN 1 ELSE 0 END) as trade_correct,
            SUM(CASE WHEN prediction = 'NO_TRADE' AND prediction_correct THEN 1 ELSE 0 END) as no_trade_correct,
            SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
            SUM(CASE WHEN actual_outcome = 'LOSS' THEN 1 ELSE 0 END) as actual_losses
        FROM ai_predictions
        WHERE prediction_correct IS NOT NULL
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            row = dict(cur.fetchone())
        conn.close()

        # Calculate rates
        total = row['total'] or 1
        trade_total = row['trade_count'] or 1
        no_trade_total = row['no_trade_count'] or 1

        return {
            'total_predictions': row['total'],
            'overall_accuracy': round(100.0 * (row['correct'] or 0) / total, 1),
            'trade_predictions': row['trade_count'],
            'trade_accuracy': round(100.0 * (row['trade_correct'] or 0) / trade_total, 1),
            'no_trade_predictions': row['no_trade_count'],
            'no_trade_accuracy': round(100.0 * (row['no_trade_correct'] or 0) / no_trade_total, 1),
            'actual_wins': row['actual_wins'],
            'actual_losses': row['actual_losses'],
            'actual_win_rate': round(100.0 * (row['actual_wins'] or 0) / total, 1),
        }

    def get_accuracy_by_confidence(self) -> List[Dict[str, Any]]:
        """Get accuracy breakdown by confidence level."""
        query = """
        SELECT
            confidence,
            COUNT(*) as total,
            SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
            ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy
        FROM ai_predictions
        WHERE prediction_correct IS NOT NULL
        GROUP BY confidence
        ORDER BY
            CASE confidence
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
            END
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = [dict(row) for row in cur.fetchall()]
        conn.close()

        return rows

    def get_accuracy_by_health_score(self) -> List[Dict[str, Any]]:
        """Get accuracy breakdown by health score."""
        query = """
        SELECT
            health_score,
            health_label,
            prediction,
            COUNT(*) as total,
            SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
            ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy
        FROM ai_predictions
        WHERE prediction_correct IS NOT NULL
          AND health_score IS NOT NULL
        GROUP BY health_score, health_label, prediction
        ORDER BY health_score, prediction
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = [dict(row) for row in cur.fetchall()]
        conn.close()

        return rows

    def get_accuracy_by_model(self) -> List[Dict[str, Any]]:
        """Get accuracy breakdown by EPCH model."""
        query = """
        SELECT
            model,
            direction,
            COUNT(*) as total,
            SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
            ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
            SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_count,
            SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_count
        FROM ai_predictions
        WHERE prediction_correct IS NOT NULL
        GROUP BY model, direction
        ORDER BY model, direction
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = [dict(row) for row in cur.fetchall()]
        conn.close()

        return rows

    def get_confusion_matrix(self) -> Dict[str, int]:
        """Get confusion matrix (prediction vs actual outcome)."""
        query = """
        SELECT
            prediction,
            actual_outcome,
            COUNT(*) as count
        FROM ai_predictions
        WHERE actual_outcome IS NOT NULL
        GROUP BY prediction, actual_outcome
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
        conn.close()

        matrix = {
            'trade_win': 0,      # True positive
            'trade_loss': 0,    # False positive
            'no_trade_win': 0,  # False negative
            'no_trade_loss': 0, # True negative
        }

        for row in rows:
            key = f"{row['prediction'].lower()}_{row['actual_outcome'].lower()}"
            matrix[key] = row['count']

        return matrix

    def get_false_predictions(self, limit: int = 20) -> Dict[str, List[Dict]]:
        """Get recent false predictions for analysis."""
        # False positives: TRADE predictions that were LOSS
        fp_query = """
        SELECT
            trade_id, ticker, trade_date, direction, model,
            health_score, health_label,
            prediction, confidence, actual_pnl_r,
            LEFT(reasoning, 200) as reasoning_preview
        FROM ai_predictions
        WHERE prediction = 'TRADE' AND actual_outcome = 'LOSS'
        ORDER BY trade_date DESC
        LIMIT %s
        """

        # False negatives: NO_TRADE predictions that were WIN
        fn_query = """
        SELECT
            trade_id, ticker, trade_date, direction, model,
            health_score, health_label,
            prediction, confidence, actual_pnl_r,
            LEFT(reasoning, 200) as reasoning_preview
        FROM ai_predictions
        WHERE prediction = 'NO_TRADE' AND actual_outcome = 'WIN'
        ORDER BY trade_date DESC
        LIMIT %s
        """

        conn = psycopg2.connect(**DB_CONFIG)

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(fp_query, (limit,))
            false_positives = [dict(row) for row in cur.fetchall()]

            cur.execute(fn_query, (limit,))
            false_negatives = [dict(row) for row in cur.fetchall()]

        conn.close()

        return {
            'false_positives': false_positives,
            'false_negatives': false_negatives,
        }

    def print_report(self):
        """Print formatted accuracy report to console."""
        print("=" * 70)
        print("DOW AI PREDICTION ACCURACY REPORT")
        print("=" * 70)

        # Overall summary
        summary = self.get_overall_summary()
        print("\nOVERALL SUMMARY")
        print("-" * 40)
        print(f"Total Predictions:     {summary['total_predictions']:,}")
        print(f"Overall Accuracy:      {summary['overall_accuracy']}%")
        print(f"")
        print(f"TRADE Predictions:     {summary['trade_predictions']:,} ({summary['trade_accuracy']}% correct)")
        print(f"NO_TRADE Predictions:  {summary['no_trade_predictions']:,} ({summary['no_trade_accuracy']}% correct)")
        print(f"")
        print(f"Actual Win Rate:       {summary['actual_win_rate']}% ({summary['actual_wins']} wins / {summary['actual_losses']} losses)")

        # Confusion matrix
        matrix = self.get_confusion_matrix()
        print("\nCONFUSION MATRIX")
        print("-" * 40)
        print("                    Actual WIN    Actual LOSS")
        print(f"Predicted TRADE:    {matrix['trade_win']:>8}      {matrix['trade_loss']:>8}")
        print(f"Predicted NO_TRADE: {matrix['no_trade_win']:>8}      {matrix['no_trade_loss']:>8}")

        # By confidence
        by_conf = self.get_accuracy_by_confidence()
        print("\nACCURACY BY CONFIDENCE")
        print("-" * 40)
        print(f"{'Confidence':<12} {'Total':>8} {'Correct':>8} {'Accuracy':>10}")
        for row in by_conf:
            print(f"{row['confidence']:<12} {row['total']:>8} {row['correct']:>8} {row['accuracy']:>9}%")

        # By model
        by_model = self.get_accuracy_by_model()
        print("\nACCURACY BY MODEL & DIRECTION")
        print("-" * 40)
        print(f"{'Model':<8} {'Dir':<6} {'Total':>6} {'Acc':>6} {'TRADE':>7} {'NO_TRADE':>10}")
        for row in by_model:
            print(f"{row['model']:<8} {row['direction']:<6} {row['total']:>6} {row['accuracy']:>5}% {row['trade_count']:>7} {row['no_trade_count']:>10}")

        # By health score
        by_health = self.get_accuracy_by_health_score()
        print("\nACCURACY BY HEALTH SCORE")
        print("-" * 40)
        print(f"{'Health':>6} {'Label':<10} {'Pred':<10} {'Total':>6} {'Accuracy':>10}")
        for row in by_health:
            print(f"{row['health_score']:>6} {row['health_label'] or 'N/A':<10} {row['prediction']:<10} {row['total']:>6} {row['accuracy']:>9}%")

        print("\n" + "=" * 70)


def main():
    """Generate and print accuracy report."""
    reporter = AccuracyReporter()
    reporter.print_report()


if __name__ == '__main__':
    main()
