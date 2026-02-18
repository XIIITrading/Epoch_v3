#!/usr/bin/env python3
"""
DOW AI v3.0 Production Batch Analyzer
Epoch Trading System - XIII Trading LLC

PRODUCTION MODE: Single-pass analysis using Pass 2 logic only.
- Runs Pass 2 (with backtested context) on all trades
- Stores results in ai_predictions table
- Used for weekly batch processing of new trades

For validation runs (dual-pass), use batch_analyze_v3.py instead.

Usage:
    python batch_analyze_production.py [options]

Options:
    --limit N           Process at most N trades (default: all unprocessed)
    --ticker SYMBOL     Filter by ticker symbol
    --direction DIR     Filter by LONG or SHORT
    --model MODEL       Filter by model (EPCH1, EPCH2, EPCH3, EPCH4)
    --date-from DATE    Filter trades from this date (YYYY-MM-DD)
    --date-to DATE      Filter trades to this date (YYYY-MM-DD)
    --reprocess         Reprocess trades that already have predictions
    --dry-run           Show what would be processed without calling API
    --save-results      Save results to timestamped txt file
    --output-dir DIR    Output directory for results (default: test/)
"""

import argparse
import time
import sys
import logging
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BATCH_DIR = SCRIPT_DIR.parent.resolve()
DOW_AI_DIR = BATCH_DIR.parent.resolve()
TEST_OUTPUT_DIR = BATCH_DIR / "test"

sys.path.insert(0, str(BATCH_DIR))
sys.path.insert(0, str(BATCH_DIR / 'data'))
sys.path.insert(0, str(DOW_AI_DIR))
sys.path.insert(0, str(DOW_AI_DIR / 'ai_context'))

import anthropic

# Import batch_analyzer config using importlib to avoid collision
_batch_config_path = BATCH_DIR / "config.py"
_spec = importlib.util.spec_from_file_location("batch_config", _batch_config_path)
_batch_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_batch_config)

ANTHROPIC_API_KEY = _batch_config.ANTHROPIC_API_KEY
CLAUDE_MODEL = _batch_config.CLAUDE_MODEL
PROMPT_VERSION = _batch_config.PROMPT_VERSION
MAX_OUTPUT_TOKENS = _batch_config.MAX_OUTPUT_TOKENS
BATCH_SIZE = _batch_config.BATCH_SIZE
DB_CONFIG = _batch_config.DB_CONFIG

# Import from batch_analyzer/data (direct import since path is set)
from trade_loader_v3 import TradeLoaderV3
from prediction_storage import PredictionStorage

# Import from batch_analyzer/models
sys.path.insert(0, str(BATCH_DIR / 'models'))
from prediction import AIPrediction

# Import v3.0 prompt components (from ai_context)
from prompt_v3 import (
    M1BarFull,
    TradeForAnalysis,
    build_pass2_prompt,
    parse_pass2_response,
    Pass2Result,
    estimate_tokens
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """Remove unicode characters that cause encoding issues."""
    replacements = {
        '\u2192': '->',
        '\u2190': '<-',
        '\u2191': '^',
        '\u2193': 'v',
        '\u2713': '[x]',
        '\u2717': '[ ]',
        '\u2022': '-',
        '\u2014': '--',
        '\u2013': '-',
        '\u201c': '"',
        '\u201d': '"',
        '\u2018': "'",
        '\u2019': "'",
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text.encode('ascii', 'replace').decode('ascii')


class OutputCapture:
    """Captures output for both console and file."""

    def __init__(self, save_to_file: bool = False):
        self.save_to_file = save_to_file
        self.lines = []

    def log(self, msg: str = ""):
        print(msg, flush=True)
        if self.save_to_file:
            self.lines.append(sanitize_text(msg))

    def get_output(self) -> str:
        return "\n".join(self.lines)


class ProductionAnalyzer:
    """
    Production analyzer using Pass 2 logic only.

    Pass 2 includes:
    - Full M1 bar data with all indicators
    - Backtested edges from ai_context
    - Zone performance data
    - Model statistics
    """

    def __init__(
        self,
        api_key: str,
        model: str = CLAUDE_MODEL,
        max_tokens: int = MAX_OUTPUT_TOKENS,
        ai_context: Optional[Dict[str, Any]] = None
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.ai_context = ai_context or {}

    def analyze_trade(self, trade: TradeForAnalysis) -> Dict[str, Any]:
        """
        Run Pass 2 analysis on a single trade.

        Returns dict with prediction, confidence, reasoning, tokens, latency.
        """
        # Build Pass 2 prompt with backtested context
        prompt = build_pass2_prompt(
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

        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse response
            result = parse_pass2_response(response.content[0].text)

            return {
                'decision': result.decision,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'raw_response': result.raw_response,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'latency_ms': latency_ms,
                # Extracted indicators
                'candle_pct': result.candle_pct,
                'candle_status': result.candle_status,
                'vol_delta': result.vol_delta,
                'vol_delta_status': result.vol_delta_status,
                'vol_roc': result.vol_roc,
                'vol_roc_status': result.vol_roc_status,
                'sma_spread': result.sma_spread,
                'sma_status': result.sma_status,
                'h1_structure': result.h1_structure,
                'h1_status': result.h1_status,
            }

        except anthropic.RateLimitError:
            logger.warning("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return self.analyze_trade(trade)

        except Exception as e:
            logger.error(f"API error for {trade.trade_id}: {e}")
            raise


def create_ai_prediction(result: Dict[str, Any], trade: TradeForAnalysis) -> AIPrediction:
    """Convert analysis result to AIPrediction for storage."""

    # Map status values to expected format
    candle_status_map = {
        'FAVORABLE': 'GOOD',
        'NEUTRAL': 'OK',
        'UNFAVORABLE': 'SKIP',
        'GOOD': 'GOOD',
        'OK': 'OK',
        'SKIP': 'SKIP',
    }

    vol_delta_status_map = {
        'ALIGNED': 'FAVORABLE',
        'NEUTRAL': 'NEUTRAL',
        'OPPOSING': 'WEAK',
        'FAVORABLE': 'FAVORABLE',
        'WEAK': 'WEAK',
    }

    vol_roc_status_map = {
        'ELEVATED': 'ELEVATED',
        'NORMAL': 'NORMAL',
        'LOW': 'NORMAL',
    }

    sma_map = {
        'ALIGNED': 'B+' if trade.direction == 'LONG' else 'B-',
        'NEUTRAL': 'N',
        'OPPOSING': 'B-' if trade.direction == 'LONG' else 'B+',
        'B+': 'B+',
        'B-': 'B-',
        'N': 'N',
    }

    h1_map = {
        'B+': 'B+',
        'B-': 'B-',
        'N': 'N',
        'NEUTRAL': 'N',
    }

    return AIPrediction(
        trade_id=trade.trade_id,
        prediction=result['decision'],
        confidence=result['confidence'],
        reasoning=result['raw_response'],
        candle_pct=result.get('candle_pct'),
        candle_status=candle_status_map.get(result.get('candle_status'), None),
        vol_delta=result.get('vol_delta'),
        vol_delta_status=vol_delta_status_map.get(result.get('vol_delta_status'), None),
        vol_roc=result.get('vol_roc'),
        vol_roc_status=vol_roc_status_map.get(result.get('vol_roc_status'), None),
        sma=sma_map.get(result.get('sma_status'), None),
        h1_struct=h1_map.get(result.get('h1_structure'), None),
        snapshot=result.get('reasoning', '')[:500],
        model_used=CLAUDE_MODEL,
        prompt_version='v3.0',
        tokens_input=result['input_tokens'],
        tokens_output=result['output_tokens'],
        processing_time_ms=result['latency_ms'],
    )


def main():
    parser = argparse.ArgumentParser(description="DOW AI v3.0 Production Batch Analyzer")
    parser.add_argument('--limit', type=int, help='Max trades to process')
    parser.add_argument('--ticker', type=str, help='Filter by ticker')
    parser.add_argument('--direction', type=str, choices=['LONG', 'SHORT'], help='Filter by direction')
    parser.add_argument('--model', type=str, help='Filter by model')
    parser.add_argument('--date-from', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-to', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--reprocess', action='store_true', help='Reprocess existing predictions')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--save-results', action='store_true', help='Save results to file')
    parser.add_argument('--output-dir', type=str, help='Output directory')

    args = parser.parse_args()

    # Setup output capture
    output = OutputCapture(save_to_file=args.save_results)
    start_time = datetime.now()

    # Header
    output.log("=" * 80)
    output.log("DOW AI v3.0 PRODUCTION BATCH ANALYZER")
    output.log("=" * 80)
    output.log(f"Analysis Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Prompt Version: v3.0 (Pass 2 Only)")
    output.log(f"Model: {CLAUDE_MODEL}")
    output.log("")
    output.log("MODE: PRODUCTION (Single-pass with backtested context)")
    output.log("  - Uses Pass 2 logic (includes indicator_edges, zone_performance)")
    output.log("  - Stores results in ai_predictions table")
    output.log("=" * 80)
    output.log("")

    # Filters
    output.log("FILTERS:")
    output.log(f"  Limit: {args.limit or 'ALL'}")
    output.log(f"  Ticker: {args.ticker or 'ALL'}")
    output.log(f"  Direction: {args.direction or 'ALL'}")
    output.log(f"  Model: {args.model or 'ALL'}")
    output.log(f"  Date Range: {args.date_from or 'ANY'} to {args.date_to or 'ANY'}")
    output.log(f"  Reprocess: {args.reprocess}")
    output.log("")

    # Initialize components
    loader = TradeLoaderV3()
    storage = PredictionStorage()

    # Parse dates if provided
    start_date = None
    end_date = None
    if args.date_from:
        start_date = datetime.strptime(args.date_from, '%Y-%m-%d').date()
    if args.date_to:
        end_date = datetime.strptime(args.date_to, '%Y-%m-%d').date()

    # Get already processed in ai_predictions (unless reprocessing)
    processed_ids = set()
    if not args.reprocess:
        processed_ids = storage.get_processed_trade_ids()
        output.log(f"Already in ai_predictions: {len(processed_ids)}")

    # Get total available trades (don't exclude dual_pass_analysis for production)
    available = loader.get_trade_count(
        ticker=args.ticker,
        direction=args.direction,
        model=args.model,
        start_date=start_date,
        end_date=end_date,
        exclude_analyzed=False  # Don't filter by dual_pass_analysis
    )
    output.log(f"Total trades in database: {available}")

    # Load trades (don't exclude by dual_pass_analysis for production mode)
    # We'll filter by ai_predictions after loading
    load_limit = (args.limit + len(processed_ids)) if args.limit else None
    output.log(f"\nLoading trades...")

    all_trades = loader.load_trades(
        limit=load_limit,
        ticker=args.ticker,
        direction=args.direction,
        model=args.model,
        start_date=start_date,
        end_date=end_date,
        exclude_analyzed=False  # Don't filter by dual_pass_analysis
    )

    # Filter out trades already in ai_predictions
    if not args.reprocess:
        trades = [t for t in all_trades if t.trade_id not in processed_ids]
    else:
        trades = all_trades

    # Apply limit after filtering
    if args.limit and len(trades) > args.limit:
        trades = trades[:args.limit]

    output.log(f"Loaded {len(trades)} trades to process (after filtering)")

    if not trades:
        output.log("\nNo trades to process.")
        return

    # Dry run - show what would be processed
    if args.dry_run:
        output.log("\nDRY RUN - Would process these trades:")
        for i, trade in enumerate(trades[:20], 1):
            output.log(f"  {i}. {trade.trade_id}: {trade.ticker} {trade.direction}")
        if len(trades) > 20:
            output.log(f"  ... and {len(trades) - 20} more")
        return

    # Load AI context
    output.log("\nLoading AI context...")
    ai_context = loader.load_ai_context()
    context_keys = [k for k in ai_context.keys() if not k.startswith('_')]
    output.log(f"  Loaded: {', '.join(context_keys)}")

    # Initialize analyzer
    output.log("\nInitializing production analyzer...")
    analyzer = ProductionAnalyzer(
        api_key=ANTHROPIC_API_KEY,
        model=CLAUDE_MODEL,
        ai_context=ai_context
    )

    # Process trades
    output.log("")
    output.log("=" * 80)
    output.log("PROCESSING TRADES")
    output.log("=" * 80)
    output.log("")

    results = []
    total_input_tokens = 0
    total_output_tokens = 0
    errors = 0

    for i, trade in enumerate(trades, 1):
        output.log(f"[{i}/{len(trades)}] {trade.trade_id}")
        output.log(f"  {trade.ticker} {trade.direction} | {trade.trade_date} {trade.entry_time}")
        output.log(f"  Entry: ${trade.entry_price:.2f} | Model: {trade.model} | Zone: {trade.zone_type}")

        try:
            # Analyze trade
            result = analyzer.analyze_trade(trade)

            # Determine correctness
            actual = trade.actual_outcome
            correct = (result['decision'] == 'TRADE' and actual == 'WIN') or \
                     (result['decision'] == 'NO_TRADE' and actual == 'LOSS')
            correct_str = "[+]" if correct else "[-]"

            output.log(f"  Decision: {result['decision']} ({result['confidence']}) {correct_str}")
            output.log(f"  Actual: {actual}")
            output.log(f"  Reasoning: {result['reasoning'][:100]}...")

            # Create prediction object and save
            prediction = create_ai_prediction(result, trade)

            # Need to create a compatible trade context for storage
            from models.trade_context import TradeContext
            trade_ctx = TradeContext(
                trade_id=trade.trade_id,
                ticker=trade.ticker,
                trade_date=datetime.strptime(trade.trade_date, '%Y-%m-%d').date(),
                entry_time=datetime.strptime(trade.entry_time, '%H:%M:%S').time() if isinstance(trade.entry_time, str) else trade.entry_time,
                direction=trade.direction,
                model=trade.model,
                zone_type=trade.zone_type,
                entry_price=trade.entry_price,
                is_winner=trade.is_winner,
                pnl_r=trade.pnl_r
            )

            if storage.save_prediction(prediction, trade_ctx):
                output.log(f"  Saved to ai_predictions")
            else:
                output.log(f"  FAILED to save")
                errors += 1

            # Track totals
            total_input_tokens += result['input_tokens']
            total_output_tokens += result['output_tokens']

            results.append({
                'trade_id': trade.trade_id,
                'decision': result['decision'],
                'confidence': result['confidence'],
                'actual': actual,
                'correct': correct,
            })

            output.log("-" * 60)

            # Rate limiting - 1 API call per trade
            if i < len(trades):
                time.sleep(1.2)  # ~50 req/min

        except Exception as e:
            output.log(f"  ERROR: {e}")
            errors += 1
            output.log("-" * 60)
            continue

    # Summary
    output.log("")
    output.log("=" * 80)
    output.log("SUMMARY")
    output.log("=" * 80)
    output.log("")

    total = len(results)
    if total > 0:
        correct_count = sum(1 for r in results if r['correct'])
        trade_calls = sum(1 for r in results if r['decision'] == 'TRADE')
        wins = sum(1 for r in results if r['actual'] == 'WIN')

        output.log(f"Trades Analyzed: {total}")
        output.log(f"Errors: {errors}")
        output.log(f"Actual Win Rate: {wins}/{total} ({100*wins/total:.1f}%)")
        output.log("")
        output.log("PASS 2 PERFORMANCE:")
        output.log(f"  TRADE Calls: {trade_calls} ({100*trade_calls/total:.1f}%)")
        output.log(f"  Correct Predictions: {correct_count}")
        output.log(f"  Accuracy: {100*correct_count/total:.1f}%")
        output.log("")
        output.log("API USAGE:")
        output.log(f"  Input tokens: {total_input_tokens:,}")
        output.log(f"  Output tokens: {total_output_tokens:,}")

        # Cost estimate (Sonnet pricing)
        cost = (total_input_tokens * 0.003 / 1000) + (total_output_tokens * 0.015 / 1000)
        output.log(f"  Estimated cost: ${cost:.4f}")

    # Timing
    end_time = datetime.now()
    duration = end_time - start_time

    output.log("")
    output.log("=" * 80)
    output.log(f"Analysis Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Analysis Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Duration: {duration}")
    output.log("=" * 80)
    output.log("END OF REPORT")
    output.log("=" * 80)

    # Save to file
    if args.save_results:
        output_dir = Path(args.output_dir) if args.output_dir else TEST_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        ticker_str = f"_{args.ticker}" if args.ticker else ""
        direction_str = f"_{args.direction}" if args.direction else ""
        filename = f"production_results_{timestamp}{ticker_str}{direction_str}.txt"
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output.get_output())

        print(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    main()
