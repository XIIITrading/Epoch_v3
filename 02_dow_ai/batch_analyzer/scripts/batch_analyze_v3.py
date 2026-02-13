"""
DOW AI v3.0 Batch Analyzer
Epoch Trading System - XIII Trading LLC

Dual-pass analysis on historical trades:
- Pass 1 (Trader's Eye): Raw M1 bars + indicators, no backtested context
- Pass 2 (System Decision): Same data + learned edges from backtesting

Usage:
    python batch_analyze_v3.py --limit 10           # Process 10 trades
    python batch_analyze_v3.py --limit 100          # Process 100 trades
    python batch_analyze_v3.py --dry-run            # Show trades without API calls
    python batch_analyze_v3.py --reprocess          # Re-analyze already processed trades
    python batch_analyze_v3.py --ticker NVDA        # Filter by ticker
    python batch_analyze_v3.py --direction LONG     # Filter by direction
    python batch_analyze_v3.py --save-results       # Save results to test folder
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import importlib.util

# Set up paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BATCH_DIR = SCRIPT_DIR.parent.resolve()
DOW_AI_DIR = BATCH_DIR.parent.resolve()

# Add all necessary paths
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BATCH_DIR))
sys.path.insert(0, str(BATCH_DIR / 'data'))
sys.path.insert(0, str(BATCH_DIR / 'analyzer'))
sys.path.insert(0, str(DOW_AI_DIR))
sys.path.insert(0, str(DOW_AI_DIR / 'ai_context'))

# Import config using importlib to avoid collision
_batch_config_path = BATCH_DIR / "config.py"
_spec = importlib.util.spec_from_file_location("batch_config", _batch_config_path)
_batch_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_batch_config)

ANTHROPIC_API_KEY = _batch_config.ANTHROPIC_API_KEY

# Import v3 modules
from trade_loader_v3 import TradeLoaderV3
from dual_pass_storage import DualPassStorage
from dual_pass_analyzer import DualPassAnalyzer, DualPassResult

# Import prompt version and builder for debug
from prompt_v3 import PROMPT_VERSION, build_pass1_prompt, build_pass2_prompt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Output directory for saved results
TEST_OUTPUT_DIR = BATCH_DIR / "test"


def sanitize_text(text: str) -> str:
    """Remove unicode characters that cause encoding issues."""
    replacements = {
        '\u2192': '->',  # right arrow
        '\u2190': '<-',  # left arrow
        '\u2191': '^',   # up arrow
        '\u2193': 'v',   # down arrow
        '\u2713': '[x]', # checkmark
        '\u2717': '[ ]', # x mark
        '\u2022': '-',   # bullet
        '\u2014': '--',  # em dash
        '\u2013': '-',   # en dash
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text.encode('ascii', 'replace').decode('ascii')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DOW AI v3.0 Dual-Pass Batch Analyzer'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=10,
        help='Number of trades to process (default: 10)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show trades without making API calls'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Re-analyze trades already in dual_pass_analysis'
    )
    parser.add_argument(
        '--ticker',
        type=str,
        help='Filter by ticker symbol'
    )
    parser.add_argument(
        '--direction',
        type=str,
        choices=['LONG', 'SHORT'],
        help='Filter by direction'
    )
    parser.add_argument(
        '--model',
        type=str,
        choices=['EPCH1', 'EPCH2', 'EPCH3', 'EPCH4'],
        help='Filter by model'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print full prompt for first trade (for debugging)'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save results to test folder as timestamped txt file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Custom output directory for results (default: batch_analyzer/test)'
    )
    return parser.parse_args()


class OutputCapture:
    """Captures output for both console and file."""
    def __init__(self, save_to_file: bool = False):
        self.save_to_file = save_to_file
        self.lines = []

    def log(self, msg: str = ""):
        """Log a message to console and optionally capture for file."""
        print(msg)
        if self.save_to_file:
            self.lines.append(sanitize_text(msg))

    def get_output(self) -> str:
        """Get all captured output as a string."""
        return "\n".join(self.lines)


def run_analysis(args, start_time: datetime) -> tuple:
    """Run the analysis and return (output_capture, results)."""
    output = OutputCapture(save_to_file=args.save_results)

    # Header
    output.log("=" * 80)
    output.log("DOW AI v3.0 DUAL-PASS BATCH ANALYZER")
    output.log("=" * 80)
    output.log(f"Analysis Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Prompt Version: {PROMPT_VERSION}")
    output.log()
    output.log("PASS 1 (Trader's Eye):")
    output.log("  - Claude sees: Ticker, Direction, 15 M1 bars with ALL indicators")
    output.log("  - Claude does NOT see: Backtested edges, zone performance")
    output.log()
    output.log("PASS 2 (System Decision):")
    output.log("  - Claude sees: Everything from Pass 1 + learned edges")
    output.log("  - This is the authoritative system recommendation")
    output.log("=" * 80)

    # Parse dates if provided
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()

    # Initialize components
    loader = TradeLoaderV3()
    storage = DualPassStorage()

    # Show filters
    output.log()
    output.log("FILTERS:")
    output.log(f"  Limit: {args.limit}")
    output.log(f"  Ticker: {args.ticker or 'ALL'}")
    output.log(f"  Direction: {args.direction or 'ALL'}")
    output.log(f"  Model: {args.model or 'ALL'}")
    output.log(f"  Date Range: {start_date or 'ANY'} to {end_date or 'ANY'}")
    output.log(f"  Reprocess: {args.reprocess}")

    # Get trade count
    trade_count = loader.get_trade_count(
        start_date=start_date,
        end_date=end_date,
        ticker=args.ticker,
        model=args.model,
        direction=args.direction,
        exclude_analyzed=not args.reprocess
    )
    output.log(f"\nTrades available: {trade_count}")

    if trade_count == 0:
        output.log("No trades to process!")
        return output, []

    # Load trades
    output.log(f"\nLoading up to {args.limit} trades...")
    trades = loader.load_trades(
        start_date=start_date,
        end_date=end_date,
        ticker=args.ticker,
        model=args.model,
        direction=args.direction,
        exclude_analyzed=not args.reprocess,
        limit=args.limit
    )
    output.log(f"Loaded {len(trades)} trades with M1 bar data")

    if not trades:
        output.log("No trades with sufficient M1 data!")
        return output, []

    # Dry run - just show trades
    if args.dry_run:
        output.log()
        output.log("-" * 80)
        output.log("DRY RUN - Trades that would be processed:")
        output.log("-" * 80)
        for trade in trades:
            bars_info = f"{len(trade.m1_bars)} bars"
            output.log(f"  {trade.trade_id}: {trade.ticker} {trade.direction} | {bars_info} | {trade.actual_outcome}")
        output.log(f"\n{len(trades)} trades would be processed. No API calls made.")
        return output, []

    # Load AI context for Pass 2
    output.log("\nLoading AI context...")
    ai_context = loader.load_ai_context()
    output.log(f"  Loaded: indicator_edges, zone_performance, model_stats")

    # Initialize analyzer
    output.log(f"\nInitializing analyzer...")
    analyzer = DualPassAnalyzer(
        api_key=ANTHROPIC_API_KEY,
        ai_context=ai_context
    )

    # Process trades
    output.log()
    output.log("=" * 80)
    output.log("TRADE RESULTS")
    output.log("=" * 80)

    results = []
    total_tokens_in = 0
    total_tokens_out = 0

    for i, trade in enumerate(trades, 1):
        output.log(f"\n[{i}/{len(trades)}] {trade.trade_id}")
        output.log(f"  {trade.ticker} {trade.direction} | {trade.trade_date} {trade.entry_time}")
        output.log(f"  Entry: ${trade.entry_price:.2f} | Model: {trade.model} | Zone: {trade.zone_type}")

        # Debug: print full prompt for first trade (console only, not in file)
        if args.debug and i == 1:
            print("\n" + "=" * 70)
            print("DEBUG: PASS 1 PROMPT")
            print("=" * 70)
            p1_prompt = build_pass1_prompt(
                ticker=trade.ticker,
                direction=trade.direction,
                entry_price=trade.entry_price,
                entry_time=trade.entry_time,
                m1_bars=trade.m1_bars
            )
            print(p1_prompt)
            print("\n" + "=" * 70)
            print("DEBUG: PASS 2 PROMPT")
            print("=" * 70)
            p2_prompt = build_pass2_prompt(
                ticker=trade.ticker,
                direction=trade.direction,
                entry_price=trade.entry_price,
                entry_time=trade.entry_time,
                m1_bars=trade.m1_bars,
                model=trade.model,
                zone_type=trade.zone_type,
                indicator_edges=ai_context.get('indicator_edges', {}),
                zone_performance=ai_context.get('zone_performance', {}),
                model_stats=ai_context.get('model_stats', {})
            )
            print(p2_prompt)
            print("=" * 70 + "\n")

        try:
            result = analyzer.analyze_trade(trade)
            results.append(result)

            # Accumulate tokens
            total_tokens_in += result.pass1_tokens_input + result.pass2_tokens_input
            total_tokens_out += result.pass1_tokens_output + result.pass2_tokens_output

            # Display result
            agree_str = "AGREE" if result.passes_agree else "DISAGREE"
            p1_mark = "+" if result.pass1_correct else "-"
            p2_mark = "+" if result.pass2_correct else "-"

            output.log()
            output.log(f"  Pass 1: {result.pass1.decision:9} ({result.pass1.confidence}) [{p1_mark}]")
            output.log(f"  Pass 2: {result.pass2.decision:9} ({result.pass2.confidence}) [{p2_mark}]")
            output.log(f"  Actual: {result.actual_outcome} | {agree_str}")
            output.log()
            output.log(f"  Pass 1 Reasoning: {sanitize_text(result.pass1.reasoning)}")
            output.log(f"  Pass 2 Reasoning: {sanitize_text(result.pass2.reasoning)}")

            # Show key indicators from M1 bars
            if trade.m1_bars:
                last_bar = trade.m1_bars[-1]
                output.log()
                output.log(f"  Last Bar Indicators:")
                output.log(f"    H1={last_bar.h1_structure}, M15={last_bar.m15_structure}, M5={last_bar.m5_structure}, M1={last_bar.m1_structure}")
                output.log(f"    L_Score={last_bar.long_score}, S_Score={last_bar.short_score}")
                output.log(f"    Range%={last_bar.candle_range_pct:.3f}%, SMA_Spread={last_bar.sma_spread:.2f}")

            output.log("-" * 80)

            # Save to database
            if storage.save_result(result):
                logger.debug(f"Saved to database")
            else:
                logger.error(f"Failed to save to database")

        except Exception as e:
            output.log(f"  ERROR: {e}")
            output.log("-" * 80)
            logger.error(f"Failed to analyze: {e}")
            continue

    # Summary
    output.log()
    output.log("=" * 80)
    output.log("SUMMARY")
    output.log("=" * 80)

    if results:
        total = len(results)
        pass1_trades = sum(1 for r in results if r.pass1.decision == 'TRADE')
        pass2_trades = sum(1 for r in results if r.pass2.decision == 'TRADE')
        pass1_correct = sum(1 for r in results if r.pass1_correct)
        pass2_correct = sum(1 for r in results if r.pass2_correct)
        agreements = sum(1 for r in results if r.passes_agree)
        actual_wins = sum(1 for r in results if r.actual_outcome == 'WIN')

        output.log()
        output.log(f"Trades Analyzed: {total}")
        output.log(f"Actual Win Rate: {actual_wins}/{total} ({actual_wins/total*100:.1f}%)")
        output.log()
        output.log("PASS COMPARISON:")
        output.log("-" * 50)
        output.log(f"{'Metric':<30} {'Pass 1':>10} {'Pass 2':>10}")
        output.log("-" * 50)
        output.log(f"{'TRADE Calls':<30} {pass1_trades:>10} {pass2_trades:>10}")
        output.log(f"{'TRADE Rate':<30} {pass1_trades/total*100:>9.1f}% {pass2_trades/total*100:>9.1f}%")
        output.log(f"{'Correct Predictions':<30} {pass1_correct:>10} {pass2_correct:>10}")
        output.log(f"{'Accuracy':<30} {pass1_correct/total*100:>9.1f}% {pass2_correct/total*100:>9.1f}%")
        output.log("-" * 50)
        output.log()
        output.log(f"Agreement Rate: {agreements}/{total} ({agreements/total*100:.1f}%)")

        # Disagreement analysis
        disagreements = [r for r in results if not r.passes_agree]
        if disagreements:
            pass1_wins = sum(1 for r in disagreements if r.pass1_correct and not r.pass2_correct)
            pass2_wins = sum(1 for r in disagreements if r.pass2_correct and not r.pass1_correct)
            both_wrong = sum(1 for r in disagreements if not r.pass1_correct and not r.pass2_correct)
            output.log()
            output.log(f"DISAGREEMENTS ({len(disagreements)} trades):")
            output.log(f"  Pass 1 correct: {pass1_wins}")
            output.log(f"  Pass 2 correct: {pass2_wins}")
            output.log(f"  Both wrong: {both_wrong}")

        # Breakdown by outcome
        output.log()
        output.log("BREAKDOWN BY ACTUAL OUTCOME:")
        wins = [r for r in results if r.actual_outcome == 'WIN']
        losses = [r for r in results if r.actual_outcome == 'LOSS']

        if wins:
            wins_trade_p1 = sum(1 for r in wins if r.pass1.decision == 'TRADE')
            wins_trade_p2 = sum(1 for r in wins if r.pass2.decision == 'TRADE')
            output.log(f"  WINS ({len(wins)}): P1 said TRADE on {wins_trade_p1}, P2 said TRADE on {wins_trade_p2}")

        if losses:
            losses_notrade_p1 = sum(1 for r in losses if r.pass1.decision == 'NO_TRADE')
            losses_notrade_p2 = sum(1 for r in losses if r.pass2.decision == 'NO_TRADE')
            output.log(f"  LOSSES ({len(losses)}): P1 said NO_TRADE on {losses_notrade_p1}, P2 said NO_TRADE on {losses_notrade_p2}")

        # Cost
        input_cost = (total_tokens_in / 1_000_000) * 3.00
        output_cost = (total_tokens_out / 1_000_000) * 15.00
        total_cost = input_cost + output_cost
        output.log()
        output.log("API USAGE:")
        output.log(f"  Input tokens:  {total_tokens_in:,}")
        output.log(f"  Output tokens: {total_tokens_out:,}")
        output.log(f"  Total cost:    ${total_cost:.4f}")

        # Cumulative stats
        output.log()
        output.log("CUMULATIVE DATABASE STATS:")
        stats = storage.get_accuracy_summary()
        if stats.get('total', 0) > 0:
            output.log(f"  Total analyzed: {stats['total']}")
            output.log(f"  Pass 1 accuracy: {stats['pass1_accuracy']:.1f}%")
            output.log(f"  Pass 2 accuracy: {stats['pass2_accuracy']:.1f}%")
            output.log(f"  Agreement rate: {stats['agreement_rate']:.1f}%")
            if stats['pass1_wins_disagreement'] + stats['pass2_wins_disagreement'] > 0:
                output.log(f"  Disagreement winners: P1={stats['pass1_wins_disagreement']}, P2={stats['pass2_wins_disagreement']}, Both Wrong={stats['both_wrong_disagreement']}")

    # End timestamp
    end_time = datetime.now()
    duration = end_time - start_time
    output.log()
    output.log("=" * 80)
    output.log(f"Analysis Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Analysis Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    output.log(f"Duration: {duration}")
    output.log("=" * 80)
    output.log("END OF REPORT")
    output.log("=" * 80)

    return output, results


def main():
    args = parse_args()
    start_time = datetime.now()

    # Run analysis
    output, results = run_analysis(args, start_time)

    # Save to file if requested
    if args.save_results and not args.dry_run:
        # Determine output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = TEST_OUTPUT_DIR

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with start timestamp
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        direction_str = f"_{args.direction}" if args.direction else ""
        ticker_str = f"_{args.ticker}" if args.ticker else ""
        filename = f"batch_results_{timestamp}{ticker_str}{direction_str}.txt"

        # Save to file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output.get_output())

        print(f"\n\nResults saved to: {output_path}")

    print("\nDone!")


if __name__ == '__main__':
    main()
