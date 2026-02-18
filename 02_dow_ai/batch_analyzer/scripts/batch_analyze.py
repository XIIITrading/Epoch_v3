"""
Batch Analyzer Script v2.0
Run DOW AI analysis on historical trades.

v2.0 Architecture: Claude as Decision Engine
- Claude receives RAW indicator values (no pre-calculated labels)
- Claude receives full context files as "learned knowledge"
- Claude applies reasoning using context to make TRADE/NO_TRADE decisions

Usage:
    python batch_analyze.py                    # Process 5 new trades (default, v2.0)
    python batch_analyze.py --limit 100        # Process 100 new trades
    python batch_analyze.py --limit 500        # Process 500 new trades
    python batch_analyze.py --dry-run          # Show trades without processing
    python batch_analyze.py --reprocess        # Re-analyze already processed trades
    python batch_analyze.py --reprocess -l 100 # Re-analyze 100 trades with new model
    python batch_analyze.py --legacy           # Use v1.x mode (pre-calculated labels)

The --reprocess flag includes trades that already have predictions and uses
upsert logic to UPDATE existing records. Use this when testing new prompt versions.
"""

import sys
import argparse
from pathlib import Path
import importlib.util

# Set up paths carefully
BATCH_DIR = Path(__file__).parent.parent.resolve()
DOW_AI_DIR = BATCH_DIR.parent.resolve()
sys.path.insert(0, str(BATCH_DIR))
sys.path.insert(0, str(DOW_AI_DIR))

# Import batch_analyzer config using importlib to avoid collision with site-packages 'config'
_batch_config_path = BATCH_DIR / "config.py"
_spec = importlib.util.spec_from_file_location("batch_config", _batch_config_path)
_batch_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_batch_config)

DB_CONFIG = _batch_config.DB_CONFIG
AI_CONTEXT_DIR = _batch_config.AI_CONTEXT_DIR
M1_RAMPUP_BARS = _batch_config.M1_RAMPUP_BARS
ANTHROPIC_API_KEY = _batch_config.ANTHROPIC_API_KEY

# Import shared prompt components from ai_context
from ai_context.dow_helper_prompt import (
    PROMPT_VERSION,
    # v2.0 imports
    build_prompt_v2,
    calculate_vol_delta_zscore,
    # v1.x legacy imports
    get_candle_status,
    get_vol_delta_status,
    get_vol_roc_status,
    get_direction_rules,
    format_price_line_batch,
    build_prompt as build_shared_prompt
)

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import anthropic
import time


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run DOW AI batch analysis on historical trades'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=5,
        help='Number of trades to process (default: 5)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show trades without processing'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Re-process already analyzed trades (updates existing predictions)'
    )
    parser.add_argument(
        '--legacy',
        action='store_true',
        help='Use v1.x legacy mode with pre-calculated labels (default is v2.0)'
    )
    return parser.parse_args()


def load_ai_context():
    """Load AI context files.

    v2.0: Load all three context files for full context injection.
    """
    context = {}

    # Indicator edges (validated edges from backtesting)
    edges_file = AI_CONTEXT_DIR / "indicator_edges.json"
    if edges_file.exists():
        with open(edges_file, 'r') as f:
            context['indicator_edges'] = json.load(f)

    # Zone performance (win rates by zone type)
    zone_file = AI_CONTEXT_DIR / "zone_performance.json"
    if zone_file.exists():
        with open(zone_file, 'r') as f:
            context['zone_performance'] = json.load(f)

    # Model stats (v2.0: full model performance by direction)
    stats_file = AI_CONTEXT_DIR / "model_stats.json"
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            context['model_stats'] = json.load(f)

    return context


def load_trades(limit=5, include_processed=False):
    """Load trades with entry indicators.

    Args:
        limit: Maximum number of trades to load
        include_processed: If True, include trades that already have predictions (for re-processing)
    """
    query = """
    SELECT
        t.trade_id, t.date, t.ticker, t.direction, t.model, t.zone_type,
        t.entry_price, t.entry_time, t.is_winner, t.pnl_r,
        ei.health_score, ei.health_label, ei.h1_structure, ei.sma_alignment,
        ei.vol_roc, ei.vol_delta
    FROM trades t
    JOIN entry_indicators ei ON t.trade_id = ei.trade_id
    WHERE ei.health_score IS NOT NULL
    """

    if not include_processed:
        query += """
    AND NOT EXISTS (SELECT 1 FROM ai_predictions ap WHERE ap.trade_id = t.trade_id)
    """

    query += """
    ORDER BY t.date DESC, t.entry_time DESC
    LIMIT %s
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def load_m1_bars(ticker, trade_date, entry_time, num_bars=15):
    """Load M1 bars before entry."""
    query = """
    SELECT bar_time, open, high, low, close, volume,
           candle_range_pct, vol_delta, vol_roc
    FROM m1_indicator_bars
    WHERE ticker = %s AND bar_date = %s AND bar_time < %s
    ORDER BY bar_time DESC
    LIMIT %s
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (ticker, trade_date, entry_time, num_bars))
        rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in reversed(rows)]


def calculate_5bar_averages(bars):
    """Calculate 5-bar rolling averages."""
    if not bars:
        return 0.0, 0.0, 0.0

    recent = bars[-5:] if len(bars) >= 5 else bars

    candle_ranges = [float(b['candle_range_pct'] or 0) for b in recent]
    vol_deltas = [float(b['vol_delta'] or 0) for b in recent]
    vol_rocs = [float(b['vol_roc'] or 0) for b in recent]

    avg_candle = sum(candle_ranges) / len(candle_ranges) if candle_ranges else 0
    avg_delta = sum(vol_deltas) / len(vol_deltas) if vol_deltas else 0
    avg_roc = sum(vol_rocs) / len(vol_rocs) if vol_rocs else 0

    return avg_candle, avg_delta, avg_roc


def extract_rampup_deltas(bars):
    """Extract vol delta values from ramp-up bars for Z-score calculation."""
    if not bars:
        return []
    return [float(b['vol_delta']) for b in bars if b.get('vol_delta') is not None]


def build_prompt(trade, m1_bars, ai_context, use_v2=True):
    """Build prompt using shared template from ai_context/dow_helper_prompt.py.

    Args:
        trade: Trade dict with entry indicators
        m1_bars: List of M1 bars before entry
        ai_context: Loaded AI context files
        use_v2: If True, use v2.0 (raw data + full context). If False, use legacy.

    Returns:
        Formatted prompt string
    """
    # Calculate 5-bar averages
    candle_range, vol_delta, vol_roc = calculate_5bar_averages(m1_bars)

    # Extract ramp-up deltas for Z-score normalization
    rampup_deltas = extract_rampup_deltas(m1_bars)

    sma_config = trade['sma_alignment'] or "N/A"
    h1_structure = trade['h1_structure'] or "N/A"

    # Format price line for batch (historical data)
    price_line = format_price_line_batch(
        entry_price=float(trade['entry_price']),
        trade_date=str(trade['date']),
        entry_time=str(trade['entry_time'])
    )

    if use_v2:
        # v2.0: Claude receives raw data + full context files
        prompt = build_prompt_v2(
            ticker=trade['ticker'],
            direction=trade['direction'],
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            rampup_deltas=rampup_deltas,
            indicator_edges=ai_context.get('indicator_edges', {}),
            model_stats=ai_context.get('model_stats', {}),
            zone_performance=ai_context.get('zone_performance', {})
        )
    else:
        # Legacy v1.x: Pre-calculated labels + summarized edges
        # Get win rate from context
        zone_perf = ai_context.get('zone_performance', {})
        primary = zone_perf.get('primary', {}).get(trade['direction'], {})
        direction_win_rate = str(primary.get('mid', 'N/A'))

        # Format edge summary (simplified for this script)
        edges_data = ai_context.get('indicator_edges', {}).get('edges', {})
        edge_lines = []
        count = 0
        for indicator, edge_info in edges_data.items():
            if count >= 3:
                break
            favorable = edge_info.get('favorable', [])
            best_for = edge_info.get('best_for', 'ALL')
            if best_for in [trade['direction'], 'ALL'] and favorable:
                condition = favorable[0] if isinstance(favorable, list) else favorable
                edge_lines.append(f"- {indicator}: {condition}")
                count += 1
        edge_summary = "\n".join(edge_lines) if edge_lines else "- No validated edges loaded"

        # Format zone info
        zone_info = f"- Zone Type: {trade['zone_type'] or 'N/A'}\n- Position: At entry"

        # Build prompt using shared function
        prompt = build_shared_prompt(
            ticker=trade['ticker'],
            direction=trade['direction'],
            price_line=price_line,
            candle_range=candle_range,
            vol_delta=vol_delta,
            vol_roc=vol_roc,
            sma_config=sma_config,
            h1_structure=h1_structure,
            direction_win_rate=direction_win_rate,
            edge_summary=edge_summary,
            zone_info=zone_info,
            rampup_deltas=rampup_deltas
        )

    return prompt


def parse_response(response_text, is_v2=True):
    """Parse Claude response.

    Args:
        response_text: Raw response from Claude
        is_v2: If True, parse v2.0 format. If False, parse legacy format.

    Returns:
        Dict with parsed fields
    """
    import re

    # Extract prediction (same for both versions)
    if 'NO TRADE' in response_text.upper() or 'NO_TRADE' in response_text.upper():
        prediction = 'NO_TRADE'
    else:
        prediction = 'TRADE'

    # Extract confidence
    conf_match = re.search(r'Confidence:\s*(HIGH|MEDIUM|LOW)', response_text, re.IGNORECASE)
    confidence = conf_match.group(1).upper() if conf_match else 'MEDIUM'

    # Extract indicators
    candle_match = re.search(r'Candle\s*%?:\s*([\d.]+)%?\s*\(?(GOOD|OK|SKIP)\)?', response_text, re.IGNORECASE)
    candle_pct = float(candle_match.group(1)) if candle_match else None
    candle_status = candle_match.group(2).upper() if candle_match else None

    delta_match = re.search(r'Vol\s*Delta:\s*([+-]?[\d,.]+)[kKmM]?\s*\(?(FAVORABLE|NEUTRAL|WEAK)\)?', response_text, re.IGNORECASE)
    if delta_match:
        vol_delta = float(delta_match.group(1).replace(',', ''))
        if 'k' in response_text[delta_match.start():delta_match.end()].lower():
            vol_delta *= 1000
        elif 'm' in response_text[delta_match.start():delta_match.end()].lower():
            vol_delta *= 1000000
        vol_delta_status = delta_match.group(2).upper()
    else:
        vol_delta = None
        vol_delta_status = None

    roc_match = re.search(r'Vol\s*ROC:\s*([+-]?[\d.]+)%?\s*\(?(ELEVATED|NORMAL)\)?', response_text, re.IGNORECASE)
    vol_roc = float(roc_match.group(1)) if roc_match else None
    vol_roc_status = roc_match.group(2).upper() if roc_match else None

    sma_match = re.search(r'SMA:\s*(B\+|B-|N)', response_text)
    sma = sma_match.group(1) if sma_match else None

    h1_match = re.search(r'H1\s*Struct(?:ure)?:\s*(B\+|B-|N)', response_text)
    h1_struct = h1_match.group(1) if h1_match else None

    # v2.0 uses REASONING instead of SNAPSHOT
    snapshot_match = re.search(r'(?:SNAPSHOT|REASONING):\s*(.+?)(?:\n\n|$)', response_text, re.IGNORECASE | re.DOTALL)
    snapshot = snapshot_match.group(1).strip() if snapshot_match else None

    # v2.0 specific: extract PASS/FAIL from analysis
    if is_v2:
        # Look for aligned/opposing in the analysis
        aligned_match = re.search(r'SMA:\s*\w+\s*\[(aligned|opposing|neutral)\]', response_text, re.IGNORECASE)
        h1_aligned_match = re.search(r'H1:\s*\w+\s*\[(aligned|opposing|neutral)\]', response_text, re.IGNORECASE)

        # Override status based on v2.0 analysis if found
        if aligned_match:
            alignment = aligned_match.group(1).upper()
            # Map v2.0 alignment to v1.x status for consistency in DB
            pass  # Keep original status parsing

    return {
        'prediction': prediction,
        'confidence': confidence,
        'candle_pct': candle_pct,
        'candle_status': candle_status,
        'vol_delta': vol_delta,
        'vol_delta_status': vol_delta_status,
        'vol_roc': vol_roc,
        'vol_roc_status': vol_roc_status,
        'sma': sma,
        'h1_struct': h1_struct,
        'snapshot': snapshot
    }


def save_prediction(trade, parsed, response_text, tokens_in, tokens_out, processing_ms):
    """Save prediction to database with upsert logic.

    Uses ON CONFLICT to update existing predictions when re-processing trades.
    """
    outcome = 'WIN' if trade['is_winner'] else 'LOSS'

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
    ON CONFLICT (trade_id) DO UPDATE SET
        prediction = EXCLUDED.prediction,
        confidence = EXCLUDED.confidence,
        reasoning = EXCLUDED.reasoning,
        candle_pct = EXCLUDED.candle_pct,
        candle_status = EXCLUDED.candle_status,
        vol_delta = EXCLUDED.vol_delta,
        vol_delta_status = EXCLUDED.vol_delta_status,
        vol_roc = EXCLUDED.vol_roc,
        vol_roc_status = EXCLUDED.vol_roc_status,
        sma = EXCLUDED.sma,
        h1_struct = EXCLUDED.h1_struct,
        snapshot = EXCLUDED.snapshot,
        model_used = EXCLUDED.model_used,
        prompt_version = EXCLUDED.prompt_version,
        tokens_input = EXCLUDED.tokens_input,
        tokens_output = EXCLUDED.tokens_output,
        processing_time_ms = EXCLUDED.processing_time_ms
    """

    params = (
        trade['trade_id'], trade['ticker'], trade['date'], trade['direction'],
        trade['model'], trade['zone_type'], trade['entry_price'], trade['entry_time'],
        parsed['prediction'], parsed['confidence'], response_text,
        parsed['candle_pct'], parsed['candle_status'],
        parsed['vol_delta'], parsed['vol_delta_status'],
        parsed['vol_roc'], parsed['vol_roc_status'],
        parsed['sma'], parsed['h1_struct'], parsed['snapshot'],
        outcome, float(trade['pnl_r']) if trade['pnl_r'] else None,
        'claude-sonnet-4-20250514', PROMPT_VERSION, tokens_in, tokens_out, processing_ms
    )

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(query, params)
    conn.commit()
    conn.close()


def main():
    args = parse_args()

    # Determine mode
    use_v2 = not args.legacy

    print("=" * 60)
    print(f"DOW AI BATCH ANALYZER - {args.limit} TRADES")
    if args.reprocess:
        print("MODE: RE-PROCESSING (updating existing predictions)")
    print(f"PROMPT VERSION: {PROMPT_VERSION}")
    print(f"ARCHITECTURE: {'v2.0 (Claude as Decision Engine)' if use_v2 else 'v1.x (Legacy - Pre-calculated Labels)'}")
    print("=" * 60)

    # Load AI context
    print("\nLoading AI context...")
    ai_context = load_ai_context()

    # Load trades
    print("Loading trades...")
    trades = load_trades(limit=args.limit, include_processed=args.reprocess)

    if not trades:
        print("No trades to process!")
        return

    print(f"Found {len(trades)} trades to process")

    # Dry run - just show trades
    if args.dry_run:
        print("\n" + "-" * 60)
        print("DRY RUN - Trades that would be processed:")
        print("-" * 60)
        for trade in trades:
            outcome = 'WIN' if trade['is_winner'] else 'LOSS'
            health = trade['health_score'] or 'N/A'
            print(f"  {trade['trade_id']}: {trade['ticker']} {trade['direction']} | Health: {health}/10 | {outcome}")
        print("\nDry run complete. No API calls made.")
        return

    # Initialize Claude client
    print(f"\nUsing API key: {ANTHROPIC_API_KEY[:20]}...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Process each trade
    print("\n" + "-" * 60)
    results = []
    total_tokens_in = 0
    total_tokens_out = 0

    for i, trade in enumerate(trades, 1):
        print(f"\n[{i}/{len(trades)}] {trade['trade_id']}: {trade['ticker']} {trade['direction']}")

        # Load M1 bars
        m1_bars = load_m1_bars(trade['ticker'], trade['date'], trade['entry_time'])
        print(f"  Loaded {len(m1_bars)} M1 bars")

        # Build prompt (v2.0 or legacy based on args)
        prompt = build_prompt(trade, m1_bars, ai_context, use_v2=use_v2)

        # Call Claude
        start_time = time.time()
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            processing_ms = int((time.time() - start_time) * 1000)

            response_text = response.content[0].text
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens

            print(f"  API response ({tokens_in} in, {tokens_out} out, {processing_ms}ms)")
            total_tokens_in += tokens_in
            total_tokens_out += tokens_out

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        # Parse response
        parsed = parse_response(response_text, is_v2=use_v2)

        # Determine if correct
        outcome = 'WIN' if trade['is_winner'] else 'LOSS'
        if parsed['prediction'] == 'TRADE':
            correct = outcome == 'WIN'
        else:
            correct = outcome == 'LOSS'

        status = "CORRECT" if correct else "WRONG"
        results.append(correct)

        print(f"  Prediction: {parsed['prediction']} ({parsed['confidence']}) vs {outcome} [{status}]")
        print(f"  Indicators: Candle={parsed['candle_pct']}% ({parsed['candle_status']}), "
              f"Vol Delta={parsed['vol_delta']} ({parsed['vol_delta_status']}), "
              f"Vol ROC={parsed['vol_roc']}% ({parsed['vol_roc_status']})")
        print(f"  Snapshot: {parsed['snapshot'][:80]}..." if parsed['snapshot'] and len(parsed['snapshot']) > 80 else f"  Snapshot: {parsed['snapshot']}")

        # Save to database
        try:
            save_prediction(trade, parsed, response_text, tokens_in, tokens_out, processing_ms)
            print(f"  Saved to database")
        except Exception as e:
            print(f"  ERROR saving: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    correct_count = sum(results)
    total = len(results)
    accuracy = (correct_count / total * 100) if total > 0 else 0

    print(f"Processed: {total}")
    print(f"Correct:   {correct_count} ({accuracy:.1f}%)")
    print(f"Wrong:     {total - correct_count}")

    # Cost estimate (Claude Sonnet pricing: $3/M input, $15/M output)
    input_cost = (total_tokens_in / 1_000_000) * 3.00
    output_cost = (total_tokens_out / 1_000_000) * 15.00
    total_cost = input_cost + output_cost

    print(f"\nAPI Usage:")
    print(f"  Input tokens:  {total_tokens_in:,}")
    print(f"  Output tokens: {total_tokens_out:,}")
    print(f"  Total cost:    ${total_cost:.4f}")


if __name__ == '__main__':
    main()
