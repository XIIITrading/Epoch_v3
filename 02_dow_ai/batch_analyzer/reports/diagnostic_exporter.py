"""
================================================================================
EPOCH TRADING SYSTEM - AI MODEL DIAGNOSTIC EXPORTER
Generates focused analysis documents for Claude Desktop review
XIII Trading LLC
================================================================================

Creates separate .txt files for each component of the AI model logic:
1. Indicator Logic & Calculations
2. Validation Rules & Thresholds
3. Model Reasoning Patterns
4. Per-Indicator Accuracy Analysis
5. Direction-Specific Logic Errors
6. Cumulative Performance Summary

Usage:
    python -m batch_analyzer.reports.diagnostic_exporter

    # Export specific reports only
    python -m batch_analyzer.reports.diagnostic_exporter --only indicator_logic validation_rules

================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging
import argparse
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG

logger = logging.getLogger(__name__)

# Output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'diagnostics'


class DiagnosticExporter:
    """
    Exports AI model diagnostic data to Claude-readable text files.
    Each export focuses on one component for granular analysis.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _fetch(self, query: str, params: list = None) -> List[Dict[str, Any]]:
        """Fetch data from database."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or [])
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []

    def _fetch_one(self, query: str, params: list = None) -> Optional[Dict[str, Any]]:
        """Fetch single row from database."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or [])
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Query error: {e}")
            return None

    # =========================================================================
    # EXPORT 1: INDICATOR LOGIC & CALCULATIONS
    # =========================================================================

    def export_indicator_logic(self) -> str:
        """
        Export the current indicator calculation logic and status assignment rules.
        This exposes HOW each indicator is computed and classified.
        """
        content = f"""================================================================================
EPOCH DOW AI - INDICATOR LOGIC & CALCULATIONS DIAGNOSTIC
Generated: {self.timestamp}
================================================================================

PURPOSE: Document the exact logic used for each indicator so Claude can identify
errors, inconsistencies, or improvements in the calculation methodology.

================================================================================
1. CANDLE RANGE PERCENTAGE
================================================================================

CALCULATION:
    candle_range_pct = ((high - low) / close) * 100

5-BAR AVERAGE:
    avg_candle_range = sum(last_5_bars.candle_range_pct) / 5

STATUS ASSIGNMENT:
    if avg_candle_range >= 0.15:
        status = "GOOD"      # Strong volatility, tradeable
    elif avg_candle_range >= 0.12:
        status = "OK"        # Marginal volatility
    else:
        status = "SKIP"      # Insufficient volatility

THRESHOLDS:
    GOOD threshold: 0.15%
    OK threshold:   0.12%
    SKIP: below 0.12%

QUESTIONS FOR REVIEW:
- Are these thresholds optimal based on historical win rates?
- Should thresholds differ by ticker or model type?

================================================================================
2. VOLUME DELTA
================================================================================

CALCULATION (Bar Position Method):
    bar_range = high - low
    position = (2 * (close - low) / bar_range) - 1  # Range: -1 to +1
    raw_delta = position * volume

    # Position meaning:
    # +1 = close at high (all buying pressure)
    # -1 = close at low (all selling pressure)
    #  0 = close at midpoint (neutral)

5-BAR AVERAGE:
    avg_vol_delta = sum(last_5_bars.vol_delta) / 5

STATUS ASSIGNMENT (CURRENT LOGIC - POTENTIAL BUG):

    For LONG trades:
        if avg_vol_delta > 0:
            status = "FAVORABLE"   # Buyers dominating - CORRECT
        else:
            status = "NEUTRAL"

    For SHORT trades:
        if avg_vol_delta > 0:
            status = "FAVORABLE"   # *** BUG: Buyers dominating is NOT favorable for shorts ***
        else:
            status = "WEAK"

EXPECTED CORRECT LOGIC FOR SHORT TRADES:
    For SHORT trades:
        if avg_vol_delta < 0:
            status = "FAVORABLE"   # Sellers dominating - supports short
        elif avg_vol_delta > some_threshold:
            status = "WEAK"        # Strong buying - opposes short
        else:
            status = "NEUTRAL"

BUG LOCATION:
    File: batch_analyzer/prompts/batch_prompt.py, lines 79-82
    File: entry_qualifier/ai/compact_prompt.py, lines 137-140

    Both contain the comment "# SHORT - paradox: positive delta is favorable"
    This is INCORRECT logic that misleads the AI model.

IMPACT ANALYSIS:
- For SHORT trades with positive vol_delta, the model receives "FAVORABLE" signal
- This contradicts the fundamental meaning of vol_delta (positive = buying pressure)
- Model may recommend SHORT entries during buying pressure (wrong)

================================================================================
3. VOLUME ROC (Rate of Change)
================================================================================

CALCULATION:
    vol_roc = ((current_volume - avg_volume) / avg_volume) * 100

    Where avg_volume = rolling average of prior N bars

5-BAR AVERAGE:
    avg_vol_roc = sum(last_5_bars.vol_roc) / 5

STATUS ASSIGNMENT:
    if avg_vol_roc >= 30:
        status = "ELEVATED"    # Volume surge, increased activity
    else:
        status = "NORMAL"

THRESHOLD:
    ELEVATED threshold: 30%

QUESTIONS FOR REVIEW:
- Should vol_roc status consider direction?
  (e.g., elevated volume during trend = good, against trend = bad)
- Is 30% the optimal threshold?

================================================================================
4. SMA CONFIGURATION
================================================================================

SOURCE:
    Retrieved from entry_indicators table: sma_alignment field

VALUES:
    "BULL" - SMA 9 > SMA 21, price above both (bullish alignment)
    "BEAR" - SMA 9 < SMA 21, price below both (bearish alignment)
    "NEUT" - Mixed or no clear alignment

EXPECTED LOGIC:
    LONG trades:  BULL = favorable, BEAR = unfavorable
    SHORT trades: BEAR = favorable, BULL = unfavorable

CURRENT IMPLEMENTATION:
    Passed directly to model without direction-specific interpretation
    Model must infer alignment quality from context

================================================================================
5. H1 STRUCTURE
================================================================================

SOURCE:
    Retrieved from entry_indicators table: h1_structure field
    Calculated from H1 timeframe fractal analysis

VALUES:
    "BULL" - Higher highs and higher lows on H1
    "BEAR" - Lower highs and lower lows on H1
    "NEUT" - No clear structure

EXPECTED LOGIC:
    LONG trades:  BULL = aligned, BEAR = counter-trend
    SHORT trades: BEAR = aligned, BULL = counter-trend

CURRENT IMPLEMENTATION:
    Passed directly to model without direction-specific interpretation

================================================================================
SUMMARY OF LOGIC ISSUES IDENTIFIED
================================================================================

CRITICAL:
1. Vol Delta status for SHORT trades is inverted (positive = FAVORABLE is wrong)

POTENTIAL IMPROVEMENTS:
2. SMA/H1 structure not explicitly labeled as aligned/counter to direction
3. Vol ROC doesn't consider direction context
4. No composite "alignment score" combining all direction-sensitive indicators

================================================================================
"""
        filepath = self.output_dir / '01_indicator_logic.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    # =========================================================================
    # EXPORT 2: VALIDATION RULES & THRESHOLDS
    # =========================================================================

    def export_validation_rules(self) -> str:
        """
        Export validation rules that determine TRADE vs NO_TRADE recommendations.
        """
        # Get current threshold performance from database
        candle_perf = self._fetch("""
            SELECT
                CASE
                    WHEN candle_pct >= 0.15 THEN 'GOOD (>=0.15%)'
                    WHEN candle_pct >= 0.12 THEN 'OK (0.12-0.15%)'
                    ELSE 'SKIP (<0.12%)'
                END as candle_bucket,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE candle_pct IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY
                CASE
                    WHEN candle_pct >= 0.15 THEN 'GOOD (>=0.15%)'
                    WHEN candle_pct >= 0.12 THEN 'OK (0.12-0.15%)'
                    ELSE 'SKIP (<0.12%)'
                END
            ORDER BY candle_bucket
        """)

        vol_delta_perf = self._fetch("""
            SELECT
                direction,
                vol_delta_status,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
                ROUND(AVG(vol_delta), 0) as avg_vol_delta
            FROM ai_predictions
            WHERE vol_delta_status IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY direction, vol_delta_status
            ORDER BY direction, vol_delta_status
        """)

        vol_roc_perf = self._fetch("""
            SELECT
                CASE
                    WHEN vol_roc >= 30 THEN 'ELEVATED (>=30%)'
                    ELSE 'NORMAL (<30%)'
                END as roc_bucket,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE vol_roc IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY
                CASE
                    WHEN vol_roc >= 30 THEN 'ELEVATED (>=30%)'
                    ELSE 'NORMAL (<30%)'
                END
            ORDER BY roc_bucket
        """)

        content = f"""================================================================================
EPOCH DOW AI - VALIDATION RULES & THRESHOLD PERFORMANCE
Generated: {self.timestamp}
================================================================================

PURPOSE: Document current validation thresholds and their actual performance
to identify which rules are working and which need adjustment.

================================================================================
1. CANDLE RANGE THRESHOLDS
================================================================================

CURRENT RULES:
    >= 0.15%  → GOOD  → Favor TRADE
    0.12-0.15% → OK   → Neutral
    < 0.12%   → SKIP  → Favor NO_TRADE

ACTUAL PERFORMANCE BY THRESHOLD:
"""
        content += "\n{:<25} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "Bucket", "Total", "Correct", "Accuracy", "Wins", "Win Rate")
        content += "-" * 75 + "\n"

        for row in candle_perf:
            content += "{:<25} {:>8} {:>8} {:>9}% {:>8} {:>9}%\n".format(
                row['candle_bucket'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['actual_wins'],
                row['win_rate']
            )

        content += """
ANALYSIS QUESTIONS:
- Does GOOD candle range actually correlate with higher win rates?
- Is the 0.12% SKIP threshold too conservative or too aggressive?
- Should thresholds vary by ticker volatility profile?

================================================================================
2. VOLUME DELTA STATUS THRESHOLDS
================================================================================

CURRENT RULES:
    LONG:  vol_delta > 0 → FAVORABLE, else NEUTRAL
    SHORT: vol_delta > 0 → FAVORABLE (BUG!), else WEAK

ACTUAL PERFORMANCE BY DIRECTION + STATUS:
"""
        content += "\n{:<10} {:<12} {:>8} {:>8} {:>10} {:>8} {:>10} {:>12}\n".format(
            "Direction", "Status", "Total", "Correct", "Accuracy", "Wins", "Win Rate", "Avg Delta")
        content += "-" * 90 + "\n"

        for row in vol_delta_perf:
            content += "{:<10} {:<12} {:>8} {:>8} {:>9}% {:>8} {:>9}% {:>+12.0f}\n".format(
                row['direction'],
                row['vol_delta_status'] or 'NULL',
                row['total'],
                row['correct'],
                row['accuracy'],
                row['actual_wins'],
                row['win_rate'],
                row['avg_vol_delta'] or 0
            )

        content += """
CRITICAL ANALYSIS:
- Compare SHORT + FAVORABLE win rate when avg_delta is POSITIVE vs baseline
- If positive delta hurts SHORT trades, this confirms the logic bug
- Expected: SHORT trades should have HIGHER win rate when delta is NEGATIVE

================================================================================
3. VOLUME ROC THRESHOLDS
================================================================================

CURRENT RULES:
    vol_roc >= 30% → ELEVATED
    vol_roc < 30%  → NORMAL

ACTUAL PERFORMANCE BY THRESHOLD:
"""
        content += "\n{:<25} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "ROC Bucket", "Total", "Correct", "Accuracy", "Wins", "Win Rate")
        content += "-" * 75 + "\n"

        for row in vol_roc_perf:
            content += "{:<25} {:>8} {:>8} {:>9}% {:>8} {:>9}%\n".format(
                row['roc_bucket'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['actual_wins'],
                row['win_rate']
            )

        content += """
ANALYSIS QUESTIONS:
- Does elevated volume actually improve trade outcomes?
- Should we distinguish between volume surge WITH trend vs AGAINST trend?

================================================================================
4. HEALTH SCORE THRESHOLDS (Rule-Based Fallback)
================================================================================

CURRENT RULES (used when API parsing fails):
    health_score >= 7 → TRADE, HIGH confidence
    health_score 5-6  → TRADE, MEDIUM confidence
    health_score = 4  → NO_TRADE, MEDIUM confidence
    health_score < 4  → NO_TRADE, HIGH confidence

These rules are used as fallback when Claude response parsing fails.

================================================================================
RECOMMENDATIONS FOR THRESHOLD OPTIMIZATION
================================================================================

1. IMMEDIATE FIX NEEDED:
   - Correct vol_delta status logic for SHORT trades
   - Negative delta should be FAVORABLE for shorts

2. DATA-DRIVEN THRESHOLD REVIEW:
   - Analyze optimal candle_range threshold by ticker
   - Analyze optimal vol_roc threshold by model type

3. DIRECTION-AWARE RULES:
   - Add explicit "aligned with direction" signals
   - Create composite alignment score

================================================================================
"""
        filepath = self.output_dir / '02_validation_rules.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    # =========================================================================
    # EXPORT 3: MODEL REASONING PATTERNS
    # =========================================================================

    def export_reasoning_patterns(self) -> str:
        """
        Export AI reasoning text samples to identify patterns in how the model
        interprets and explains indicator data.
        """
        # Get sample reasoning for correct TRADE predictions
        correct_trades = self._fetch("""
            SELECT
                trade_id, ticker, direction, model,
                prediction, confidence, actual_outcome,
                candle_pct, candle_status,
                vol_delta, vol_delta_status,
                vol_roc, vol_roc_status,
                sma, h1_struct,
                snapshot,
                LEFT(reasoning, 500) as reasoning_preview
            FROM ai_predictions
            WHERE prediction = 'TRADE' AND prediction_correct = true
            ORDER BY trade_date DESC
            LIMIT 10
        """)

        # Get sample reasoning for incorrect TRADE predictions (false positives)
        false_positives = self._fetch("""
            SELECT
                trade_id, ticker, direction, model,
                prediction, confidence, actual_outcome,
                candle_pct, candle_status,
                vol_delta, vol_delta_status,
                vol_roc, vol_roc_status,
                sma, h1_struct,
                snapshot,
                LEFT(reasoning, 500) as reasoning_preview
            FROM ai_predictions
            WHERE prediction = 'TRADE' AND prediction_correct = false
            ORDER BY trade_date DESC
            LIMIT 10
        """)

        # Get sample reasoning for correct NO_TRADE predictions
        correct_no_trades = self._fetch("""
            SELECT
                trade_id, ticker, direction, model,
                prediction, confidence, actual_outcome,
                candle_pct, candle_status,
                vol_delta, vol_delta_status,
                vol_roc, vol_roc_status,
                sma, h1_struct,
                snapshot,
                LEFT(reasoning, 500) as reasoning_preview
            FROM ai_predictions
            WHERE prediction = 'NO_TRADE' AND prediction_correct = true
            ORDER BY trade_date DESC
            LIMIT 10
        """)

        # Get sample reasoning for incorrect NO_TRADE predictions (false negatives)
        false_negatives = self._fetch("""
            SELECT
                trade_id, ticker, direction, model,
                prediction, confidence, actual_outcome,
                candle_pct, candle_status,
                vol_delta, vol_delta_status,
                vol_roc, vol_roc_status,
                sma, h1_struct,
                snapshot,
                LEFT(reasoning, 500) as reasoning_preview
            FROM ai_predictions
            WHERE prediction = 'NO_TRADE' AND prediction_correct = false
            ORDER BY trade_date DESC
            LIMIT 10
        """)

        def format_samples(samples: List[Dict], section_name: str) -> str:
            if not samples:
                return f"\n{section_name}\n{'=' * 60}\nNo samples available.\n"

            text = f"\n{section_name}\n{'=' * 60}\n"
            for i, s in enumerate(samples, 1):
                text += f"""
--- Sample {i} ---
Trade: {s['ticker']} {s['direction']} | Model: {s['model']}
Prediction: {s['prediction']} ({s['confidence']}) | Actual: {s['actual_outcome']}

Indicators Reported:
  Candle: {s['candle_pct']}% ({s['candle_status']})
  Vol Delta: {s['vol_delta']:+,.0f} ({s['vol_delta_status']}) {'*** CHECK THIS ***' if s['direction'] == 'SHORT' and s['vol_delta'] and s['vol_delta'] > 0 else ''}
  Vol ROC: {s['vol_roc']}% ({s['vol_roc_status']})
  SMA: {s['sma']} | H1: {s['h1_struct']}

Snapshot: {s['snapshot'] or 'N/A'}

Reasoning Preview:
{s['reasoning_preview'] or 'N/A'}

"""
            return text

        content = f"""================================================================================
EPOCH DOW AI - MODEL REASONING PATTERN ANALYSIS
Generated: {self.timestamp}
================================================================================

PURPOSE: Analyze HOW the model interprets indicator data in its reasoning.
Identify patterns in correct vs incorrect predictions.

KEY FOCUS AREAS:
1. How does the model describe vol_delta for SHORT trades?
2. Does the model correctly interpret "FAVORABLE" signals?
3. What reasoning patterns lead to false positives/negatives?

================================================================================
CORRECT TRADE PREDICTIONS (True Positives)
================================================================================
These are cases where the model said TRADE and the trade was a WIN.
Study these to understand what good reasoning looks like.
"""
        content += format_samples(correct_trades, "TRUE POSITIVES")

        content += """
================================================================================
INCORRECT TRADE PREDICTIONS (False Positives)
================================================================================
These are cases where the model said TRADE but the trade was a LOSS.
Study these to identify reasoning errors.
"""
        content += format_samples(false_positives, "FALSE POSITIVES - PREDICTED TRADE, ACTUAL LOSS")

        content += """
================================================================================
CORRECT NO_TRADE PREDICTIONS (True Negatives)
================================================================================
These are cases where the model said NO_TRADE and the trade was a LOSS.
The model correctly identified unfavorable conditions.
"""
        content += format_samples(correct_no_trades, "TRUE NEGATIVES")

        content += """
================================================================================
INCORRECT NO_TRADE PREDICTIONS (False Negatives)
================================================================================
These are cases where the model said NO_TRADE but the trade was a WIN.
The model missed a good trade opportunity. Study why.
"""
        content += format_samples(false_negatives, "FALSE NEGATIVES - PREDICTED NO_TRADE, ACTUAL WIN")

        content += """
================================================================================
PATTERN ANALYSIS QUESTIONS
================================================================================

1. VOL DELTA INTERPRETATION:
   - In SHORT trade samples, how does the model interpret positive vol_delta?
   - Does it correctly identify when buying pressure opposes the trade?

2. INDICATOR WEIGHTING:
   - Which indicators does the model emphasize most in its reasoning?
   - Are there indicators that should be weighted more/less heavily?

3. FALSE POSITIVE PATTERNS:
   - What common reasoning errors appear in false positives?
   - Are there specific indicator combinations that mislead the model?

4. FALSE NEGATIVE PATTERNS:
   - What conditions cause the model to miss good trades?
   - Is the model too conservative in certain scenarios?

================================================================================
"""
        filepath = self.output_dir / '03_reasoning_patterns.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    # =========================================================================
    # EXPORT 4: PER-INDICATOR ACCURACY BREAKDOWN
    # =========================================================================

    def export_indicator_accuracy(self) -> str:
        """
        Export detailed accuracy breakdown by each indicator value.
        """
        # Candle status accuracy
        candle_acc = self._fetch("""
            SELECT
                candle_status,
                direction,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE candle_status IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY candle_status, direction
            ORDER BY candle_status, direction
        """)

        # Vol delta status accuracy by direction - THE KEY DIAGNOSTIC
        vol_delta_detailed = self._fetch("""
            SELECT
                direction,
                vol_delta_status,
                CASE
                    WHEN vol_delta > 50000 THEN 'strong_positive'
                    WHEN vol_delta > 0 THEN 'weak_positive'
                    WHEN vol_delta > -50000 THEN 'weak_negative'
                    ELSE 'strong_negative'
                END as delta_magnitude,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as pred_accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE vol_delta IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY direction, vol_delta_status,
                CASE
                    WHEN vol_delta > 50000 THEN 'strong_positive'
                    WHEN vol_delta > 0 THEN 'weak_positive'
                    WHEN vol_delta > -50000 THEN 'weak_negative'
                    ELSE 'strong_negative'
                END
            ORDER BY direction, delta_magnitude
        """)

        # SMA alignment accuracy
        sma_acc = self._fetch("""
            SELECT
                sma,
                direction,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE sma IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY sma, direction
            ORDER BY sma, direction
        """)

        # H1 structure accuracy
        h1_acc = self._fetch("""
            SELECT
                h1_struct,
                direction,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE h1_struct IS NOT NULL AND prediction_correct IS NOT NULL
            GROUP BY h1_struct, direction
            ORDER BY h1_struct, direction
        """)

        content = f"""================================================================================
EPOCH DOW AI - PER-INDICATOR ACCURACY BREAKDOWN
Generated: {self.timestamp}
================================================================================

PURPOSE: Analyze prediction accuracy broken down by each indicator value.
Identify which indicator states correlate with correct vs incorrect predictions.

================================================================================
1. CANDLE STATUS ACCURACY BY DIRECTION
================================================================================
"""
        content += "\n{:<12} {:<10} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "Status", "Direction", "Total", "Correct", "Pred Acc", "Wins", "Win Rate")
        content += "-" * 75 + "\n"

        for row in candle_acc:
            content += "{:<12} {:<10} {:>8} {:>8} {:>9}% {:>8} {:>9}%\n".format(
                row['candle_status'] or 'NULL',
                row['direction'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['wins'],
                row['win_rate']
            )

        content += """
================================================================================
2. VOLUME DELTA - DETAILED ANALYSIS BY DIRECTION AND MAGNITUDE
================================================================================

*** THIS IS THE KEY DIAGNOSTIC FOR THE VOL DELTA BUG ***

For SHORT trades:
- "strong_positive" delta = heavy buying pressure = SHOULD hurt win rate
- "strong_negative" delta = heavy selling pressure = SHOULD help win rate

If strong_positive has HIGHER win rate for LONG but LOWER for SHORT,
the logic is working correctly in reality but the STATUS label is wrong.

"""
        content += "\n{:<10} {:<12} {:<18} {:>6} {:>8} {:>10} {:>6} {:>10}\n".format(
            "Direction", "Status", "Delta Magnitude", "Total", "Correct", "Pred Acc", "Wins", "Win Rate")
        content += "-" * 95 + "\n"

        for row in vol_delta_detailed:
            flag = ""
            # Flag suspicious patterns
            if row['direction'] == 'SHORT' and row['delta_magnitude'] == 'strong_positive':
                flag = " *** EXAMINE ***"
            elif row['direction'] == 'SHORT' and row['delta_magnitude'] == 'strong_negative':
                flag = " (should be best)"

            content += "{:<10} {:<12} {:<18} {:>6} {:>8} {:>9}% {:>6} {:>9}%{}\n".format(
                row['direction'],
                row['vol_delta_status'] or 'NULL',
                row['delta_magnitude'],
                row['total'],
                row['correct'],
                row['pred_accuracy'],
                row['wins'],
                row['win_rate'],
                flag
            )

        content += """
INTERPRETATION GUIDE:
- If SHORT + strong_negative has HIGHER win rate than SHORT + strong_positive,
  then the ACTUAL market behavior is correct but our STATUS LABELS are inverted.
- The model receives "FAVORABLE" for positive delta on shorts, but positive
  delta actually hurts short trades.

================================================================================
3. SMA ALIGNMENT ACCURACY BY DIRECTION
================================================================================

Expected patterns:
- LONG + BULL SMA should have higher win rate (aligned)
- SHORT + BEAR SMA should have higher win rate (aligned)
- Counter-aligned combinations should have lower win rates

"""
        content += "\n{:<8} {:<10} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "SMA", "Direction", "Total", "Correct", "Pred Acc", "Wins", "Win Rate")
        content += "-" * 70 + "\n"

        for row in sma_acc:
            expected = ""
            if (row['sma'] == 'B+' and row['direction'] == 'LONG') or \
               (row['sma'] == 'B-' and row['direction'] == 'SHORT'):
                expected = " (aligned)"
            elif (row['sma'] == 'B-' and row['direction'] == 'LONG') or \
                 (row['sma'] == 'B+' and row['direction'] == 'SHORT'):
                expected = " (counter)"

            content += "{:<8} {:<10} {:>8} {:>8} {:>9}% {:>8} {:>9}%{}\n".format(
                row['sma'] or 'NULL',
                row['direction'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['wins'],
                row['win_rate'],
                expected
            )

        content += """
================================================================================
4. H1 STRUCTURE ACCURACY BY DIRECTION
================================================================================

Expected patterns:
- LONG + B+ H1 should have higher win rate (aligned)
- SHORT + B- H1 should have higher win rate (aligned)

"""
        content += "\n{:<8} {:<10} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "H1", "Direction", "Total", "Correct", "Pred Acc", "Wins", "Win Rate")
        content += "-" * 70 + "\n"

        for row in h1_acc:
            expected = ""
            if (row['h1_struct'] == 'B+' and row['direction'] == 'LONG') or \
               (row['h1_struct'] == 'B-' and row['direction'] == 'SHORT'):
                expected = " (aligned)"
            elif (row['h1_struct'] == 'B-' and row['direction'] == 'LONG') or \
                 (row['h1_struct'] == 'B+' and row['direction'] == 'SHORT'):
                expected = " (counter)"

            content += "{:<8} {:<10} {:>8} {:>8} {:>9}% {:>8} {:>9}%{}\n".format(
                row['h1_struct'] or 'NULL',
                row['direction'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['wins'],
                row['win_rate'],
                expected
            )

        content += """
================================================================================
SUMMARY FINDINGS
================================================================================

Review the data above to answer:
1. Does the vol_delta bug actually hurt SHORT trade predictions?
2. Are aligned SMA/H1 structures predictive of wins?
3. Which indicator combinations are most/least reliable?

================================================================================
"""
        filepath = self.output_dir / '04_indicator_accuracy.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    # =========================================================================
    # EXPORT 5: DIRECTION-SPECIFIC ANALYSIS (SHORT FOCUS)
    # =========================================================================

    def export_direction_analysis(self) -> str:
        """
        Export detailed analysis of SHORT trades specifically to diagnose
        the vol_delta logic issue.
        """
        # Get SHORT trade breakdown
        short_summary = self._fetch_one("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_predictions,
                SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_predictions,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as actual_win_rate
            FROM ai_predictions
            WHERE direction = 'SHORT' AND prediction_correct IS NOT NULL
        """)

        # Get LONG trade breakdown for comparison
        long_summary = self._fetch_one("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_predictions,
                SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_predictions,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as actual_win_rate
            FROM ai_predictions
            WHERE direction = 'LONG' AND prediction_correct IS NOT NULL
        """)

        # Detailed SHORT analysis with vol_delta sign
        short_by_delta_sign = self._fetch("""
            SELECT
                CASE WHEN vol_delta >= 0 THEN 'positive' ELSE 'negative' END as delta_sign,
                vol_delta_status,
                prediction,
                COUNT(*) as total,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy
            FROM ai_predictions
            WHERE direction = 'SHORT'
              AND vol_delta IS NOT NULL
              AND prediction_correct IS NOT NULL
            GROUP BY
                CASE WHEN vol_delta >= 0 THEN 'positive' ELSE 'negative' END,
                vol_delta_status,
                prediction
            ORDER BY delta_sign, vol_delta_status, prediction
        """)

        # Sample SHORT trades with positive delta that LOST
        short_losses_positive_delta = self._fetch("""
            SELECT
                trade_id, ticker, model, trade_date,
                vol_delta, vol_delta_status,
                prediction, confidence,
                snapshot
            FROM ai_predictions
            WHERE direction = 'SHORT'
              AND vol_delta > 0
              AND actual_outcome = 'LOSS'
              AND prediction = 'TRADE'
            ORDER BY vol_delta DESC
            LIMIT 15
        """)

        # Sample SHORT trades with negative delta that WON
        short_wins_negative_delta = self._fetch("""
            SELECT
                trade_id, ticker, model, trade_date,
                vol_delta, vol_delta_status,
                prediction, confidence,
                snapshot
            FROM ai_predictions
            WHERE direction = 'SHORT'
              AND vol_delta < 0
              AND actual_outcome = 'WIN'
            ORDER BY vol_delta ASC
            LIMIT 15
        """)

        content = f"""================================================================================
EPOCH DOW AI - SHORT TRADE DIRECTION-SPECIFIC ANALYSIS
Generated: {self.timestamp}
================================================================================

PURPOSE: Deep analysis of SHORT trade predictions to diagnose the vol_delta
logic bug and understand its impact on prediction accuracy.

================================================================================
1. OVERALL DIRECTION COMPARISON
================================================================================

LONG TRADES:
"""
        if long_summary:
            content += f"""  Total Predictions:      {long_summary['total']:,}
  TRADE Predictions:      {long_summary['trade_predictions']:,}
  NO_TRADE Predictions:   {long_summary['no_trade_predictions']:,}
  Prediction Accuracy:    {long_summary['accuracy']}%
  Actual Win Rate:        {long_summary['actual_win_rate']}% ({long_summary['actual_wins']} wins)
"""

        content += "\nSHORT TRADES:\n"
        if short_summary:
            content += f"""  Total Predictions:      {short_summary['total']:,}
  TRADE Predictions:      {short_summary['trade_predictions']:,}
  NO_TRADE Predictions:   {short_summary['no_trade_predictions']:,}
  Prediction Accuracy:    {short_summary['accuracy']}%
  Actual Win Rate:        {short_summary['actual_win_rate']}% ({short_summary['actual_wins']} wins)
"""

        content += """
================================================================================
2. SHORT TRADES - VOL DELTA SIGN ANALYSIS
================================================================================

*** THIS IS THE CRITICAL DATA TO DIAGNOSE THE BUG ***

Current Logic (BUGGY):
  - Positive vol_delta → status = "FAVORABLE" (WRONG for shorts)
  - Negative vol_delta → status = "WEAK" (WRONG for shorts)

Expected Behavior:
  - Positive vol_delta (buying pressure) → HURTS short trades → lower win rate
  - Negative vol_delta (selling pressure) → HELPS short trades → higher win rate

Data breakdown:
"""
        content += "\n{:<12} {:<12} {:<10} {:>6} {:>6} {:>10} {:>8} {:>10}\n".format(
            "Delta Sign", "Status", "Prediction", "Total", "Wins", "Win Rate", "Correct", "Pred Acc")
        content += "-" * 90 + "\n"

        for row in short_by_delta_sign:
            flag = ""
            # Flag the key pattern
            if row['delta_sign'] == 'positive' and row['vol_delta_status'] == 'FAVORABLE':
                flag = " ← BUG: positive delta labeled FAVORABLE"
            elif row['delta_sign'] == 'negative' and row['vol_delta_status'] == 'WEAK':
                flag = " ← BUG: negative delta labeled WEAK"

            content += "{:<12} {:<12} {:<10} {:>6} {:>6} {:>9}% {:>8} {:>9}%{}\n".format(
                row['delta_sign'],
                row['vol_delta_status'] or 'NULL',
                row['prediction'],
                row['total'],
                row['wins'],
                row['win_rate'],
                row['correct'],
                row['accuracy'],
                flag
            )

        content += """
INTERPRETATION:
Compare win rates between positive and negative delta for SHORT trades:
- If NEGATIVE delta has HIGHER win rate → confirms proper market behavior
- If POSITIVE delta has LOWER win rate → confirms the label bug matters

The STATUS labels are inverted, causing the model to favor trades it should avoid.

================================================================================
3. SAMPLE: SHORT LOSSES WITH POSITIVE VOL DELTA
================================================================================

These are SHORT trades that:
- Had POSITIVE vol_delta (buying pressure - bad for shorts)
- Were labeled "FAVORABLE" by the buggy logic
- Model predicted TRADE
- Trade resulted in LOSS

These represent the cost of the bug:
"""
        for i, s in enumerate(short_losses_positive_delta, 1):
            content += f"""
--- Loss Sample {i} ---
Trade: {s['trade_id']} | {s['ticker']} | {s['model']} | {s['trade_date']}
Vol Delta: {s['vol_delta']:+,.0f} (STATUS: {s['vol_delta_status']})
Prediction: {s['prediction']} ({s['confidence']})
Snapshot: {s['snapshot'] or 'N/A'}
"""

        content += """
================================================================================
4. SAMPLE: SHORT WINS WITH NEGATIVE VOL DELTA
================================================================================

These are SHORT trades that:
- Had NEGATIVE vol_delta (selling pressure - good for shorts)
- Were mislabeled "WEAK" by the buggy logic
- Despite the wrong signal, the trade WON

These demonstrate what SHOULD be labeled "FAVORABLE" for shorts:
"""
        for i, s in enumerate(short_wins_negative_delta, 1):
            content += f"""
--- Win Sample {i} ---
Trade: {s['trade_id']} | {s['ticker']} | {s['model']} | {s['trade_date']}
Vol Delta: {s['vol_delta']:+,.0f} (STATUS: {s['vol_delta_status']} ← should be FAVORABLE)
Prediction: {s['prediction']} ({s['confidence']})
Snapshot: {s['snapshot'] or 'N/A'}
"""

        content += """
================================================================================
5. CORRECTED LOGIC RECOMMENDATION
================================================================================

CURRENT (BUGGY):
```python
if trade.direction == 'LONG':
    vol_delta_status = "FAVORABLE" if vol_delta > 0 else "NEUTRAL"
else:  # SHORT
    vol_delta_status = "FAVORABLE" if vol_delta > 0 else "WEAK"  # WRONG
```

CORRECTED:
```python
if trade.direction == 'LONG':
    if vol_delta > threshold:
        vol_delta_status = "FAVORABLE"  # Buyers support longs
    elif vol_delta < -threshold:
        vol_delta_status = "WEAK"       # Sellers oppose longs
    else:
        vol_delta_status = "NEUTRAL"
else:  # SHORT
    if vol_delta < -threshold:
        vol_delta_status = "FAVORABLE"  # Sellers support shorts
    elif vol_delta > threshold:
        vol_delta_status = "WEAK"       # Buyers oppose shorts
    else:
        vol_delta_status = "NEUTRAL"
```

FILES TO UPDATE:
1. batch_analyzer/prompts/batch_prompt.py (lines 79-82)
2. entry_qualifier/ai/compact_prompt.py (lines 137-140)

================================================================================
"""
        filepath = self.output_dir / '05_direction_analysis.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    # =========================================================================
    # EXPORT 6: CUMULATIVE PERFORMANCE SUMMARY
    # =========================================================================

    def export_cumulative_summary(self) -> str:
        """
        Export overall cumulative performance summary.
        """
        overall = self._fetch_one("""
            SELECT
                COUNT(*) as total_predictions,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN prediction = 'TRADE' THEN 1 ELSE 0 END) as trade_count,
                SUM(CASE WHEN prediction = 'NO_TRADE' THEN 1 ELSE 0 END) as no_trade_count,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as actual_wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as actual_win_rate
            FROM ai_predictions
            WHERE prediction_correct IS NOT NULL
        """)

        by_confidence = self._fetch("""
            SELECT
                confidence,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy
            FROM ai_predictions
            WHERE prediction_correct IS NOT NULL
            GROUP BY confidence
            ORDER BY CASE confidence WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END
        """)

        by_model = self._fetch("""
            SELECT
                model,
                direction,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) as correct,
                ROUND(100.0 * SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy,
                SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM ai_predictions
            WHERE prediction_correct IS NOT NULL
            GROUP BY model, direction
            ORDER BY model, direction
        """)

        confusion = self._fetch("""
            SELECT
                prediction,
                actual_outcome,
                COUNT(*) as count
            FROM ai_predictions
            WHERE actual_outcome IS NOT NULL
            GROUP BY prediction, actual_outcome
        """)

        matrix = {'trade_win': 0, 'trade_loss': 0, 'no_trade_win': 0, 'no_trade_loss': 0}
        for row in confusion:
            key = f"{row['prediction'].lower()}_{row['actual_outcome'].lower()}"
            matrix[key] = row['count']

        content = f"""================================================================================
EPOCH DOW AI - CUMULATIVE PERFORMANCE SUMMARY
Generated: {self.timestamp}
================================================================================

================================================================================
1. OVERALL METRICS
================================================================================
"""
        if overall:
            content += f"""
Total Predictions Analyzed: {overall['total_predictions']:,}
Overall Prediction Accuracy: {overall['accuracy']}%
  - Correct Predictions: {overall['correct']:,}

Prediction Breakdown:
  - TRADE predictions: {overall['trade_count']:,}
  - NO_TRADE predictions: {overall['no_trade_count']:,}

Actual Trade Outcomes:
  - Win Rate: {overall['actual_win_rate']}%
  - Total Wins: {overall['actual_wins']:,}
  - Total Losses: {overall['total_predictions'] - overall['actual_wins']:,}
"""

        content += """
================================================================================
2. CONFUSION MATRIX
================================================================================

                        Actual WIN    Actual LOSS
"""
        content += f"    Predicted TRADE:    {matrix['trade_win']:>8}      {matrix['trade_loss']:>8}\n"
        content += f"    Predicted NO_TRADE: {matrix['no_trade_win']:>8}      {matrix['no_trade_loss']:>8}\n"

        content += f"""
Interpretation:
  - True Positives (TRADE → WIN):   {matrix['trade_win']:,}
  - False Positives (TRADE → LOSS): {matrix['trade_loss']:,}
  - False Negatives (NO_TRADE → WIN): {matrix['no_trade_win']:,}
  - True Negatives (NO_TRADE → LOSS): {matrix['no_trade_loss']:,}
"""

        content += """
================================================================================
3. ACCURACY BY CONFIDENCE LEVEL
================================================================================
"""
        content += "\n{:<12} {:>10} {:>10} {:>12}\n".format(
            "Confidence", "Total", "Correct", "Accuracy")
        content += "-" * 50 + "\n"

        for row in by_confidence:
            content += "{:<12} {:>10} {:>10} {:>11}%\n".format(
                row['confidence'] or 'NULL',
                row['total'],
                row['correct'],
                row['accuracy']
            )

        content += """
================================================================================
4. ACCURACY BY MODEL & DIRECTION
================================================================================
"""
        content += "\n{:<8} {:<8} {:>8} {:>8} {:>10} {:>8} {:>10}\n".format(
            "Model", "Dir", "Total", "Correct", "Pred Acc", "Wins", "Win Rate")
        content += "-" * 70 + "\n"

        for row in by_model:
            content += "{:<8} {:<8} {:>8} {:>8} {:>9}% {:>8} {:>9}%\n".format(
                row['model'] or 'NULL',
                row['direction'],
                row['total'],
                row['correct'],
                row['accuracy'],
                row['wins'],
                row['win_rate']
            )

        content += """
================================================================================
5. KEY ISSUES IDENTIFIED IN THIS DIAGNOSTIC RUN
================================================================================

CRITICAL BUG:
- Vol Delta status logic is INVERTED for SHORT trades
- Positive vol_delta (buying pressure) is labeled "FAVORABLE" for shorts
- This causes the model to recommend shorts during buying pressure

IMPACT:
- SHORT trade prediction accuracy may be artificially reduced
- Model receives contradictory signals (favorable status, unfavorable reality)

RECOMMENDED ACTIONS:
1. Fix vol_delta logic in batch_prompt.py and compact_prompt.py
2. Re-run batch analysis after fix to measure improvement
3. Consider adding explicit "aligned with direction" indicators

================================================================================
6. NEXT STEPS FOR MODEL IMPROVEMENT
================================================================================

1. IMMEDIATE:
   - Fix the vol_delta status bug
   - Re-run batch analysis on affected trades

2. SHORT-TERM:
   - Add direction-aware composite scores
   - Review threshold values based on this analysis

3. LONG-TERM:
   - Build feedback loop from outcomes to threshold optimization
   - Consider model-specific indicator weightings

================================================================================
"""
        filepath = self.output_dir / '06_cumulative_summary.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)


def export_all_diagnostics(output_dir: Optional[Path] = None) -> List[str]:
    """
    Export all diagnostic reports.

    Returns:
        List of exported file paths
    """
    exporter = DiagnosticExporter(output_dir=output_dir)

    if not exporter.connect():
        print("ERROR: Failed to connect to database")
        return []

    try:
        exported = []

        exports = [
            ("Indicator Logic", exporter.export_indicator_logic),
            ("Validation Rules", exporter.export_validation_rules),
            ("Reasoning Patterns", exporter.export_reasoning_patterns),
            ("Indicator Accuracy", exporter.export_indicator_accuracy),
            ("Direction Analysis", exporter.export_direction_analysis),
            ("Cumulative Summary", exporter.export_cumulative_summary),
        ]

        for name, export_fn in exports:
            try:
                print(f"Exporting {name}...")
                path = export_fn()
                if path:
                    exported.append(path)
                    print(f"  [OK] {path}")
            except Exception as e:
                print(f"  [ERROR] Error in {name}: {e}")
                logger.error(f"Error in {name}: {e}")

        return exported

    finally:
        exporter.disconnect()


def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description='Export AI model diagnostics for Claude Desktop review'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory for diagnostic files'
    )
    parser.add_argument(
        '--only',
        nargs='+',
        choices=['indicator_logic', 'validation_rules', 'reasoning_patterns',
                 'indicator_accuracy', 'direction_analysis', 'cumulative_summary'],
        help='Export only specific reports'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("EPOCH DOW AI - DIAGNOSTIC EXPORTER")
    print("=" * 60)

    exported = export_all_diagnostics(output_dir=args.output_dir)

    print("\n" + "=" * 60)
    print(f"Exported {len(exported)} diagnostic files:")
    for path in exported:
        print(f"  - {path}")
    print("=" * 60)
    print("\nDrop these files into Claude Desktop for analysis.")


if __name__ == '__main__':
    main()
