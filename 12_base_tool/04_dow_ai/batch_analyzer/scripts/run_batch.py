"""
Run Batch Analysis
Main script to run DOW AI analysis on historical trades.

Usage:
    python run_batch.py --limit 100
    python run_batch.py --start-date 2025-12-15 --end-date 2026-01-22
    python run_batch.py --ticker TSLA --direction LONG
    python run_batch.py --rule-based  # Use rule-based predictions (no API)
    python run_batch.py --dry-run     # Show what would be processed
"""

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path

# Add batch_analyzer directory to path (NOT parent to avoid collision with 04_dow_ai)
BATCH_ANALYZER_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BATCH_ANALYZER_DIR))

# Import from batch_analyzer modules using relative structure
from config import CLAUDE_MODEL, BATCH_SIZE, CHECKPOINT_FILE

# Import data modules directly to avoid collision with 04_dow_ai/data
import importlib.util
spec = importlib.util.spec_from_file_location("trade_loader", BATCH_ANALYZER_DIR / "data" / "trade_loader.py")
trade_loader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trade_loader_module)
TradeLoader = trade_loader_module.TradeLoader

spec = importlib.util.spec_from_file_location("prediction_storage", BATCH_ANALYZER_DIR / "data" / "prediction_storage.py")
prediction_storage_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prediction_storage_module)
PredictionStorage = prediction_storage_module.PredictionStorage

spec = importlib.util.spec_from_file_location("claude_client", BATCH_ANALYZER_DIR / "analyzer" / "claude_client.py")
claude_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claude_client_module)
ClaudeBatchClient = claude_client_module.ClaudeBatchClient

spec = importlib.util.spec_from_file_location("response_parser", BATCH_ANALYZER_DIR / "analyzer" / "response_parser.py")
response_parser_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(response_parser_module)
ResponseParser = response_parser_module.ResponseParser

spec = importlib.util.spec_from_file_location("batch_prompt", BATCH_ANALYZER_DIR / "prompts" / "batch_prompt.py")
batch_prompt_module = importlib.util.spec_from_file_location("batch_prompt", BATCH_ANALYZER_DIR / "prompts" / "batch_prompt.py")
batch_prompt_module = importlib.util.module_from_spec(batch_prompt_module)
importlib.util.spec_from_file_location("batch_prompt", BATCH_ANALYZER_DIR / "prompts" / "batch_prompt.py").loader.exec_module(batch_prompt_module)
BatchPromptBuilder = batch_prompt_module.BatchPromptBuilder


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run DOW AI batch analysis on historical trades'
    )

    # Date filters
    parser.add_argument(
        '--start-date', '-s',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date', '-e',
        type=str,
        help='End date (YYYY-MM-DD)'
    )

    # Other filters
    parser.add_argument(
        '--ticker', '-t',
        type=str,
        help='Filter by ticker'
    )
    parser.add_argument(
        '--model', '-m',
        type=str,
        help='Filter by model (EPCH1-4)'
    )
    parser.add_argument(
        '--direction', '-d',
        type=str,
        choices=['LONG', 'SHORT'],
        help='Filter by direction'
    )

    # Processing options
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Maximum number of trades to process'
    )
    parser.add_argument(
        '--include-processed',
        action='store_true',
        help='Re-process already processed trades'
    )
    parser.add_argument(
        '--rule-based',
        action='store_true',
        help='Use rule-based predictions (no API calls)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without making changes'
    )

    # Model selection
    parser.add_argument(
        '--claude-model',
        type=str,
        default=CLAUDE_MODEL,
        help=f'Claude model to use (default: {CLAUDE_MODEL})'
    )

    return parser.parse_args()


def load_checkpoint() -> dict:
    """Load checkpoint file for resuming interrupted batches."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'processed_ids': [], 'last_run': None}


def save_checkpoint(data: dict):
    """Save checkpoint for resuming."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def main():
    """Main batch processing function."""
    args = parse_args()

    print("=" * 60)
    print("DOW AI BATCH ANALYZER")
    print("=" * 60)

    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()

    # Initialize components
    loader = TradeLoader()
    storage = PredictionStorage()

    # Get trade count (with all filters applied)
    total_count = loader.get_trade_count(
        start_date=start_date,
        end_date=end_date,
        ticker=args.ticker,
        model=args.model,
        direction=args.direction,
        exclude_processed=not args.include_processed
    )

    print(f"\nTrades available for processing: {total_count}")

    if args.dry_run:
        # Load sample trades for preview
        trades = loader.load_trades(
            start_date=start_date,
            end_date=end_date,
            ticker=args.ticker,
            model=args.model,
            direction=args.direction,
            exclude_processed=not args.include_processed,
            limit=5
        )

        print("\nSample trades that would be processed:")
        print("-" * 60)
        for trade in trades:
            outcome = 'WIN' if trade.is_winner else 'LOSS'
            health = trade.indicators.health_score if trade.indicators else 'N/A'
            print(f"  {trade.trade_id}: {trade.ticker} {trade.direction} | Health: {health}/10 | {outcome}")

        print("\nDry run complete. No changes made.")
        return

    # Load trades
    print(f"\nLoading trades...")
    trades = loader.load_trades(
        start_date=start_date,
        end_date=end_date,
        ticker=args.ticker,
        model=args.model,
        direction=args.direction,
        exclude_processed=not args.include_processed,
        limit=args.limit
    )

    if not trades:
        print("No trades to process.")
        return

    print(f"Loaded {len(trades)} trades for processing")

    # Initialize analyzer
    if args.rule_based:
        print("\nUsing RULE-BASED predictions (no API calls)")
        response_parser = ResponseParser()
        client = None
    else:
        print(f"\nUsing Claude API: {args.claude_model}")
        client = ClaudeBatchClient(model=args.claude_model)

    prompt_builder = BatchPromptBuilder()

    # Process trades
    print("\n" + "-" * 60)
    print("PROCESSING TRADES")
    print("-" * 60)

    processed = 0
    correct = 0
    errors = 0
    checkpoint_data = load_checkpoint()

    for i, trade in enumerate(trades, 1):
        try:
            # Load M1 ramp-up bars
            m1_bars = loader.load_m1_rampup(trade)
            trade.m1_bars = m1_bars

            # Generate prediction
            if args.rule_based:
                prediction = response_parser.create_rule_based_prediction(trade)
            else:
                prediction = client.analyze_trade(trade)

            # Save to database
            storage.save_prediction(prediction, trade)

            # Track accuracy
            processed += 1
            if prediction.prediction_correct:
                correct += 1

            # Progress output
            outcome = 'WIN' if trade.is_winner else 'LOSS'
            pred_correct = "OK" if prediction.prediction_correct else "WRONG"
            print(f"[{i}/{len(trades)}] {trade.trade_id}: {prediction.prediction} ({prediction.confidence}) vs {outcome} [{pred_correct}]")

            # Checkpoint every BATCH_SIZE trades
            if processed % BATCH_SIZE == 0:
                checkpoint_data['processed_ids'].append(trade.trade_id)
                checkpoint_data['last_run'] = datetime.now().isoformat()
                save_checkpoint(checkpoint_data)
                print(f"  Checkpoint saved ({processed} processed)")

        except Exception as e:
            print(f"  ERROR processing {trade.trade_id}: {e}")
            errors += 1
            continue

    # Final summary
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)

    accuracy = (correct / processed * 100) if processed > 0 else 0
    print(f"\nProcessed: {processed}")
    print(f"Correct:   {correct} ({accuracy:.1f}%)")
    print(f"Errors:    {errors}")

    if client and not args.rule_based:
        cost = client.estimate_cost()
        print(f"\nAPI Usage:")
        print(f"  Input tokens:  {cost['input_tokens']:,}")
        print(f"  Output tokens: {cost['output_tokens']:,}")
        print(f"  Total cost:    ${cost['total_cost']:.4f}")

    # Save final checkpoint
    checkpoint_data['last_run'] = datetime.now().isoformat()
    checkpoint_data['last_processed'] = processed
    checkpoint_data['last_accuracy'] = accuracy
    save_checkpoint(checkpoint_data)


if __name__ == '__main__':
    main()
