"""
DOW AI v3.0 Test Runner
Runs batch analysis and saves output to file for review.

Usage:
    python run_test_batch.py                    # 20 trades, mixed
    python run_test_batch.py --limit 50         # 50 trades
    python run_test_batch.py --direction LONG   # Only LONG trades
    python run_test_batch.py --debug            # Include debug prompts
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import importlib.util
from io import StringIO

# Set up paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BATCH_DIR = SCRIPT_DIR.parent.resolve()
DOW_AI_DIR = BATCH_DIR.parent.resolve()

# Add all necessary paths
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BATCH_DIR))
sys.path.insert(0, str(BATCH_DIR / 'data'))
sys.path.insert(0, str(BATCH_DIR / 'analyzer'))
sys.path.insert(0, str(BATCH_DIR / 'scripts'))
sys.path.insert(0, str(DOW_AI_DIR))
sys.path.insert(0, str(DOW_AI_DIR / 'ai_context'))

# Import config
_batch_config_path = BATCH_DIR / "config.py"
_spec = importlib.util.spec_from_file_location("batch_config", _batch_config_path)
_batch_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_batch_config)

ANTHROPIC_API_KEY = _batch_config.ANTHROPIC_API_KEY

# Import v3 modules
from trade_loader_v3 import TradeLoaderV3
from dual_pass_storage import DualPassStorage
from dual_pass_analyzer import DualPassAnalyzer, DualPassResult
from prompt_v3 import PROMPT_VERSION, build_pass1_prompt, build_pass2_prompt

# Set up logging to capture to string
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """Remove unicode characters that cause encoding issues."""
    # Replace common unicode arrows and symbols with ASCII equivalents
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
    # Remove any remaining non-ASCII characters
    return text.encode('ascii', 'replace').decode('ascii')


def parse_args():
    parser = argparse.ArgumentParser(description='DOW AI v3.0 Test Runner')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Number of trades (default: 20)')
    parser.add_argument('--direction', type=str, choices=['LONG', 'SHORT'], help='Filter by direction')
    parser.add_argument('--ticker', type=str, help='Filter by ticker')
    parser.add_argument('--debug', action='store_true', help='Include full prompts for first trade')
    parser.add_argument('--reprocess', action='store_true', help='Re-analyze already processed trades')
    parser.add_argument('--output', '-o', type=str, help='Output filename (default: auto-generated)')
    return parser.parse_args()


def run_analysis(args) -> str:
    """Run the analysis and return output as string."""
    output = []

    def log(msg=""):
        output.append(msg)
        print(msg)

    # Header
    log("=" * 80)
    log("DOW AI v3.0 TEST BATCH RESULTS")
    log("=" * 80)
    log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Prompt Version: {PROMPT_VERSION}")
    log()
    log("FILTERS:")
    log(f"  Limit: {args.limit}")
    log(f"  Direction: {args.direction or 'ALL'}")
    log(f"  Ticker: {args.ticker or 'ALL'}")
    log(f"  Reprocess: {args.reprocess}")
    log()

    # Initialize
    loader = TradeLoaderV3()
    storage = DualPassStorage()

    # Load trades
    log("Loading trades...")
    trades = loader.load_trades(
        ticker=args.ticker,
        direction=args.direction,
        exclude_analyzed=not args.reprocess,
        limit=args.limit
    )
    log(f"Loaded {len(trades)} trades with M1 bar data")

    if not trades:
        log("No trades to process!")
        return "\n".join(output)

    # Load AI context
    log("\nLoading AI context...")
    ai_context = loader.load_ai_context()

    # Initialize analyzer
    analyzer = DualPassAnalyzer(
        api_key=ANTHROPIC_API_KEY,
        ai_context=ai_context
    )

    # Process trades
    log("\n" + "=" * 80)
    log("TRADE RESULTS")
    log("=" * 80)

    results = []
    total_tokens_in = 0
    total_tokens_out = 0

    for i, trade in enumerate(trades, 1):
        log(f"\n[{i}/{len(trades)}] {trade.trade_id}")
        log(f"  {trade.ticker} {trade.direction} | {trade.trade_date} {trade.entry_time}")
        log(f"  Entry: ${trade.entry_price:.2f} | Model: {trade.model} | Zone: {trade.zone_type}")

        # Debug: print full prompt for first trade
        if args.debug and i == 1:
            log("\n" + "-" * 80)
            log("DEBUG: PASS 1 PROMPT")
            log("-" * 80)
            p1_prompt = build_pass1_prompt(
                ticker=trade.ticker,
                direction=trade.direction,
                entry_price=trade.entry_price,
                entry_time=trade.entry_time,
                m1_bars=trade.m1_bars
            )
            log(p1_prompt)
            log("-" * 80)

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

            log()
            log(f"  Pass 1: {result.pass1.decision:9} ({result.pass1.confidence}) [{p1_mark}]")
            log(f"  Pass 2: {result.pass2.decision:9} ({result.pass2.confidence}) [{p2_mark}]")
            log(f"  Actual: {result.actual_outcome} | {agree_str}")
            log()
            log(f"  Pass 1 Reasoning: {sanitize_text(result.pass1.reasoning)}")
            log(f"  Pass 2 Reasoning: {sanitize_text(result.pass2.reasoning)}")

            # Show key indicators from M1 bars
            if trade.m1_bars:
                last_bar = trade.m1_bars[-1]
                log()
                log(f"  Last Bar Indicators:")
                log(f"    H1={last_bar.h1_structure}, M15={last_bar.m15_structure}, M5={last_bar.m5_structure}, M1={last_bar.m1_structure}")
                log(f"    L_Score={last_bar.long_score}, S_Score={last_bar.short_score}")
                log(f"    Range%={last_bar.candle_range_pct:.3f}%, SMA_Spread={last_bar.sma_spread:.2f}")

            log("-" * 80)

            # Save to database
            storage.save_result(result)

        except Exception as e:
            log(f"  ERROR: {e}")
            log("-" * 80)
            continue

    # Summary
    log("\n" + "=" * 80)
    log("SUMMARY")
    log("=" * 80)

    if results:
        total = len(results)
        pass1_trades = sum(1 for r in results if r.pass1.decision == 'TRADE')
        pass2_trades = sum(1 for r in results if r.pass2.decision == 'TRADE')
        pass1_correct = sum(1 for r in results if r.pass1_correct)
        pass2_correct = sum(1 for r in results if r.pass2_correct)
        agreements = sum(1 for r in results if r.passes_agree)
        actual_wins = sum(1 for r in results if r.actual_outcome == 'WIN')

        log()
        log(f"Trades Analyzed: {total}")
        log(f"Actual Win Rate: {actual_wins}/{total} ({actual_wins/total*100:.1f}%)")
        log()
        log("PASS COMPARISON:")
        log("-" * 50)
        log(f"{'Metric':<30} {'Pass 1':>10} {'Pass 2':>10}")
        log("-" * 50)
        log(f"{'TRADE Calls':<30} {pass1_trades:>10} {pass2_trades:>10}")
        log(f"{'TRADE Rate':<30} {pass1_trades/total*100:>9.1f}% {pass2_trades/total*100:>9.1f}%")
        log(f"{'Correct Predictions':<30} {pass1_correct:>10} {pass2_correct:>10}")
        log(f"{'Accuracy':<30} {pass1_correct/total*100:>9.1f}% {pass2_correct/total*100:>9.1f}%")
        log("-" * 50)
        log()
        log(f"Agreement Rate: {agreements}/{total} ({agreements/total*100:.1f}%)")

        # Disagreement analysis
        disagreements = [r for r in results if not r.passes_agree]
        if disagreements:
            pass1_wins = sum(1 for r in disagreements if r.pass1_correct and not r.pass2_correct)
            pass2_wins = sum(1 for r in disagreements if r.pass2_correct and not r.pass1_correct)
            both_wrong = sum(1 for r in disagreements if not r.pass1_correct and not r.pass2_correct)
            log()
            log(f"DISAGREEMENTS ({len(disagreements)} trades):")
            log(f"  Pass 1 correct: {pass1_wins}")
            log(f"  Pass 2 correct: {pass2_wins}")
            log(f"  Both wrong: {both_wrong}")

        # Breakdown by outcome
        log()
        log("BREAKDOWN BY ACTUAL OUTCOME:")
        wins = [r for r in results if r.actual_outcome == 'WIN']
        losses = [r for r in results if r.actual_outcome == 'LOSS']

        if wins:
            wins_trade_p1 = sum(1 for r in wins if r.pass1.decision == 'TRADE')
            wins_trade_p2 = sum(1 for r in wins if r.pass2.decision == 'TRADE')
            log(f"  WINS ({len(wins)}): P1 said TRADE on {wins_trade_p1}, P2 said TRADE on {wins_trade_p2}")

        if losses:
            losses_notrade_p1 = sum(1 for r in losses if r.pass1.decision == 'NO_TRADE')
            losses_notrade_p2 = sum(1 for r in losses if r.pass2.decision == 'NO_TRADE')
            log(f"  LOSSES ({len(losses)}): P1 said NO_TRADE on {losses_notrade_p1}, P2 said NO_TRADE on {losses_notrade_p2}")

        # Cost
        input_cost = (total_tokens_in / 1_000_000) * 3.00
        output_cost = (total_tokens_out / 1_000_000) * 15.00
        total_cost = input_cost + output_cost
        log()
        log("API USAGE:")
        log(f"  Input tokens:  {total_tokens_in:,}")
        log(f"  Output tokens: {total_tokens_out:,}")
        log(f"  Total cost:    ${total_cost:.4f}")

    log()
    log("=" * 80)
    log("END OF REPORT")
    log("=" * 80)

    return "\n".join(output)


def main():
    args = parse_args()

    # Run analysis
    output = run_analysis(args)

    # Generate output filename
    if args.output:
        filename = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        direction_str = f"_{args.direction}" if args.direction else ""
        filename = f"test_results_{timestamp}{direction_str}.txt"

    # Save to file (use utf-8 encoding to handle any unicode)
    output_path = SCRIPT_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\n\nResults saved to: {output_path}")


if __name__ == '__main__':
    main()
