"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS
Simple Runner Script (handles imports properly)
XIII Trading LLC
================================================================================

Run from anywhere:
    python C:/XIIITradingSystems/Epoch/02_zone_system/12_system_analysis/secondary_processor/ramp_up_analysis/run.py

Or from the ramp_up_analysis directory:
    python run.py

Options:
    python run.py --full          # Reprocess all trades
    python run.py --export        # Export CSV after processing
    python run.py --stop-type zone_buffer  # Use different stop type

================================================================================
"""

import sys
from pathlib import Path

# Set up paths for imports
SCRIPT_DIR = Path(__file__).parent
MODULE_DIR = SCRIPT_DIR.parent.parent  # 12_system_analysis

# Now import with absolute paths
import argparse
import logging
from datetime import datetime
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import numpy as np

# Import DB config from 12_system_analysis FIRST (before local config shadows it)
sys.path.insert(0, str(MODULE_DIR))
from config import DB_CONFIG

# Now import local ramp_up config with explicit path
import importlib.util
local_config_path = SCRIPT_DIR / 'config.py'
spec = importlib.util.spec_from_file_location("ramp_up_config", local_config_path)
ramp_up_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ramp_up_config)

# Extract values from local config
STOP_TYPE = ramp_up_config.STOP_TYPE
LOOKBACK_BARS = ramp_up_config.LOOKBACK_BARS
INDICATORS = ramp_up_config.INDICATORS
NUMERIC_INDICATORS = ramp_up_config.NUMERIC_INDICATORS
CATEGORICAL_INDICATORS = ramp_up_config.CATEGORICAL_INDICATORS
TREND_THRESHOLD = ramp_up_config.TREND_THRESHOLD
MOMENTUM_THRESHOLD = ramp_up_config.MOMENTUM_THRESHOLD
MOMENTUM_SPLIT_BAR = ramp_up_config.MOMENTUM_SPLIT_BAR
MIN_BARS_REQUIRED = ramp_up_config.MIN_BARS_REQUIRED
TREND_LABELS = ramp_up_config.TREND_LABELS
MOMENTUM_LABELS = ramp_up_config.MOMENTUM_LABELS
STRUCTURE_CONSISTENCY_LABELS = ramp_up_config.STRUCTURE_CONSISTENCY_LABELS
BATCH_SIZE = ramp_up_config.BATCH_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class RampUpMacro:
    """Summary metrics for a single trade's ramp-up period."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class RampUpProgression:
    """Single bar in the ramp-up progression."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def create_tables(conn):
    """Create tables if they don't exist."""
    schema_path = SCRIPT_DIR / 'schema' / 'ramp_up_tables.sql'

    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        logger.info("Tables created/verified")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
        return False


def fetch_all_trade_ids(conn) -> List[str]:
    """Fetch all trade IDs."""
    with conn.cursor() as cur:
        cur.execute("SELECT trade_id FROM trades ORDER BY date, entry_time")
        return [row[0] for row in cur.fetchall()]


def fetch_processed_trade_ids(conn, stop_type: str) -> List[str]:
    """Fetch already processed trade IDs."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT trade_id FROM ramp_up_macro WHERE stop_type = %s", [stop_type])
            return [row[0] for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []


def fetch_trades(conn, trade_ids: List[str]) -> List[dict]:
    """Fetch trade records."""
    query = """
        SELECT trade_id, date, ticker, model, direction, entry_time, entry_price
        FROM trades WHERE trade_id = ANY(%s)
        ORDER BY date, entry_time
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, [trade_ids])
        return [dict(row) for row in cur.fetchall()]


def fetch_stop_analysis(conn, trade_ids: List[str], stop_type: str) -> dict:
    """Fetch stop analysis indexed by trade_id."""
    query = """
        SELECT trade_id, outcome, mfe_distance, r_achieved
        FROM stop_analysis
        WHERE stop_type = %s AND trade_id = ANY(%s) AND stop_price IS NOT NULL
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, [stop_type, trade_ids])
        return {row['trade_id']: dict(row) for row in cur.fetchall()}


def fetch_m1_bars(conn, ticker: str, bar_date, entry_time, num_bars: int) -> List[dict]:
    """Fetch M1 indicator bars before entry."""
    entry_time_str = entry_time.strftime('%H:%M:%S') if hasattr(entry_time, 'strftime') else str(entry_time)

    query = """
        SELECT bar_time, candle_range_pct, vol_delta, vol_roc, sma_spread,
               sma_momentum_ratio, m15_structure, h1_structure, long_score, short_score
        FROM m1_indicator_bars
        WHERE ticker = %s AND bar_date = %s AND bar_time <= %s
        ORDER BY bar_time DESC
        LIMIT %s
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, [ticker.upper(), bar_date, entry_time_str, num_bars])
        rows = cur.fetchall()

    return [dict(row) for row in reversed(rows)]


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def safe_float(val):
    """Safely convert to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    """Safely convert to int."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def calculate_trend(values: List[float]) -> str:
    """Calculate trend using linear regression slope."""
    if len(values) < 3:
        return TREND_LABELS['flat']

    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)

    value_range = max(values) - min(values)
    if value_range == 0:
        return TREND_LABELS['flat']

    normalized_slope = slope * len(values) / value_range

    if normalized_slope > TREND_THRESHOLD:
        return TREND_LABELS['rising']
    elif normalized_slope < -TREND_THRESHOLD:
        return TREND_LABELS['falling']
    return TREND_LABELS['flat']


def calculate_momentum(bars: List[dict], indicator: str) -> str:
    """Calculate momentum by comparing first-half vs second-half."""
    first_half = []
    second_half = []

    for bar in bars:
        val = bar.get(indicator)
        if val is None:
            continue
        try:
            val = float(val)
        except (ValueError, TypeError):
            continue

        if bar['bars_to_entry'] <= MOMENTUM_SPLIT_BAR:
            first_half.append(val)
        else:
            second_half.append(val)

    if not first_half or not second_half:
        return MOMENTUM_LABELS['stable']

    first_avg = np.mean(first_half)
    second_avg = np.mean(second_half)

    if first_avg == 0:
        if second_avg == 0:
            return MOMENTUM_LABELS['stable']
        return MOMENTUM_LABELS['building'] if second_avg > 0 else MOMENTUM_LABELS['fading']

    pct_change = (second_avg - first_avg) / abs(first_avg)

    if pct_change > MOMENTUM_THRESHOLD:
        return MOMENTUM_LABELS['building']
    elif pct_change < -MOMENTUM_THRESHOLD:
        return MOMENTUM_LABELS['fading']
    return MOMENTUM_LABELS['stable']


def calculate_structure_consistency(bars: List[dict], indicator: str) -> str:
    """Calculate structure consistency for categorical indicators."""
    values = [bar.get(indicator) for bar in bars if bar.get(indicator)]

    if not values:
        return STRUCTURE_CONSISTENCY_LABELS['mixed']

    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1

    total = len(values)
    dominant = max(counts, key=counts.get)
    dominant_pct = counts[dominant] / total

    if dominant_pct >= 0.8:
        if dominant == 'BULL':
            return STRUCTURE_CONSISTENCY_LABELS['consistent_bull']
        elif dominant == 'BEAR':
            return STRUCTURE_CONSISTENCY_LABELS['consistent_bear']
        return STRUCTURE_CONSISTENCY_LABELS['consistent_neutral']

    if len(values) >= 3:
        start_val = values[0]
        end_val = values[-1]
        if start_val != end_val:
            if end_val == 'BULL':
                return STRUCTURE_CONSISTENCY_LABELS['flip_to_bull']
            elif end_val == 'BEAR':
                return STRUCTURE_CONSISTENCY_LABELS['flip_to_bear']

    return STRUCTURE_CONSISTENCY_LABELS['mixed']


def calculate_for_trade(trade: dict, stop_type: str) -> tuple:
    """Calculate ramp-up metrics for a single trade."""
    bars = trade.get('m1_bars', [])

    if len(bars) < MIN_BARS_REQUIRED:
        return None, []

    # Calculate bars_to_entry
    num_bars = len(bars)
    for i, bar in enumerate(bars):
        bar['bars_to_entry'] = i - (num_bars - 1)

    entry_bar = bars[-1]
    ramp_bars = bars[:-1]

    # Build progression records
    progressions = []
    for bar in bars:
        prog = RampUpProgression(
            trade_id=trade['trade_id'],
            bars_to_entry=bar['bars_to_entry'],
            bar_time=bar['bar_time'],
            candle_range_pct=safe_float(bar.get('candle_range_pct')),
            vol_delta=safe_float(bar.get('vol_delta')),
            vol_roc=safe_float(bar.get('vol_roc')),
            sma_spread=safe_float(bar.get('sma_spread')),
            sma_momentum_ratio=safe_float(bar.get('sma_momentum_ratio')),
            m15_structure=bar.get('m15_structure'),
            h1_structure=bar.get('h1_structure'),
            long_score=safe_int(bar.get('long_score')),
            short_score=safe_int(bar.get('short_score')),
        )
        progressions.append(prog)

    # Build macro record
    macro = RampUpMacro(
        trade_id=trade['trade_id'],
        date=trade['date'],
        ticker=trade['ticker'],
        model=trade['model'],
        direction=trade['direction'],
        entry_time=trade['entry_time'],
        stop_type=stop_type,
        lookback_bars=LOOKBACK_BARS,
        outcome=trade['outcome'],
        mfe_distance=safe_float(trade.get('mfe_distance')),
        r_achieved=safe_float(trade.get('r_achieved')),
        bars_analyzed=len(bars),
    )

    # Entry bar snapshot
    macro.entry_candle_range_pct = safe_float(entry_bar.get('candle_range_pct'))
    macro.entry_vol_delta = safe_float(entry_bar.get('vol_delta'))
    macro.entry_vol_roc = safe_float(entry_bar.get('vol_roc'))
    macro.entry_sma_spread = safe_float(entry_bar.get('sma_spread'))
    macro.entry_sma_momentum_ratio = safe_float(entry_bar.get('sma_momentum_ratio'))
    macro.entry_m15_structure = entry_bar.get('m15_structure')
    macro.entry_h1_structure = entry_bar.get('h1_structure')
    macro.entry_long_score = safe_int(entry_bar.get('long_score'))
    macro.entry_short_score = safe_int(entry_bar.get('short_score'))

    # Calculate metrics for numeric indicators
    for indicator in NUMERIC_INDICATORS:
        values = [safe_float(bar.get(indicator)) for bar in ramp_bars if bar.get(indicator) is not None]
        values = [v for v in values if v is not None]

        if values:
            setattr(macro, f'ramp_avg_{indicator}', float(np.mean(values)))
            setattr(macro, f'ramp_trend_{indicator}', calculate_trend(values))
            setattr(macro, f'ramp_momentum_{indicator}', calculate_momentum(ramp_bars, indicator))
        else:
            setattr(macro, f'ramp_avg_{indicator}', None)
            setattr(macro, f'ramp_trend_{indicator}', None)
            setattr(macro, f'ramp_momentum_{indicator}', None)

    # Structure consistency
    macro.ramp_structure_m15 = calculate_structure_consistency(ramp_bars, 'm15_structure')
    macro.ramp_structure_h1 = calculate_structure_consistency(ramp_bars, 'h1_structure')

    return macro, progressions


# =============================================================================
# INSERT FUNCTIONS
# =============================================================================

def insert_macros(conn, macros: list) -> int:
    """Insert macro records."""
    if not macros:
        return 0

    sql = """
        INSERT INTO ramp_up_macro (
            trade_id, stop_type, lookback_bars, date, ticker, model, direction, entry_time,
            outcome, mfe_distance, r_achieved,
            entry_candle_range_pct, entry_vol_delta, entry_vol_roc,
            entry_sma_spread, entry_sma_momentum_ratio,
            entry_m15_structure, entry_h1_structure, entry_long_score, entry_short_score,
            ramp_avg_candle_range_pct, ramp_avg_vol_delta, ramp_avg_vol_roc,
            ramp_avg_sma_spread, ramp_avg_sma_momentum_ratio,
            ramp_avg_long_score, ramp_avg_short_score,
            ramp_trend_candle_range_pct, ramp_trend_vol_delta, ramp_trend_vol_roc,
            ramp_trend_sma_spread, ramp_trend_sma_momentum_ratio,
            ramp_trend_long_score, ramp_trend_short_score,
            ramp_momentum_candle_range_pct, ramp_momentum_vol_delta, ramp_momentum_vol_roc,
            ramp_momentum_sma_spread, ramp_momentum_sma_momentum_ratio,
            ramp_momentum_long_score, ramp_momentum_short_score,
            ramp_structure_m15, ramp_structure_h1, bars_analyzed
        ) VALUES %s
        ON CONFLICT (trade_id) DO UPDATE SET
            stop_type = EXCLUDED.stop_type,
            outcome = EXCLUDED.outcome,
            mfe_distance = EXCLUDED.mfe_distance,
            r_achieved = EXCLUDED.r_achieved,
            calculated_at = CURRENT_TIMESTAMP
    """

    values = []
    for m in macros:
        values.append((
            m.trade_id, m.stop_type, m.lookback_bars, m.date, m.ticker, m.model, m.direction, m.entry_time,
            m.outcome, m.mfe_distance, m.r_achieved,
            m.entry_candle_range_pct, m.entry_vol_delta, m.entry_vol_roc,
            m.entry_sma_spread, m.entry_sma_momentum_ratio,
            m.entry_m15_structure, m.entry_h1_structure, m.entry_long_score, m.entry_short_score,
            getattr(m, 'ramp_avg_candle_range_pct', None), getattr(m, 'ramp_avg_vol_delta', None),
            getattr(m, 'ramp_avg_vol_roc', None), getattr(m, 'ramp_avg_sma_spread', None),
            getattr(m, 'ramp_avg_sma_momentum_ratio', None), getattr(m, 'ramp_avg_long_score', None),
            getattr(m, 'ramp_avg_short_score', None),
            getattr(m, 'ramp_trend_candle_range_pct', None), getattr(m, 'ramp_trend_vol_delta', None),
            getattr(m, 'ramp_trend_vol_roc', None), getattr(m, 'ramp_trend_sma_spread', None),
            getattr(m, 'ramp_trend_sma_momentum_ratio', None), getattr(m, 'ramp_trend_long_score', None),
            getattr(m, 'ramp_trend_short_score', None),
            getattr(m, 'ramp_momentum_candle_range_pct', None), getattr(m, 'ramp_momentum_vol_delta', None),
            getattr(m, 'ramp_momentum_vol_roc', None), getattr(m, 'ramp_momentum_sma_spread', None),
            getattr(m, 'ramp_momentum_sma_momentum_ratio', None), getattr(m, 'ramp_momentum_long_score', None),
            getattr(m, 'ramp_momentum_short_score', None),
            m.ramp_structure_m15, m.ramp_structure_h1, m.bars_analyzed,
        ))

    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    return len(values)


def insert_progressions(conn, progressions: list) -> int:
    """Insert progression records."""
    if not progressions:
        return 0

    sql = """
        INSERT INTO ramp_up_progression (
            trade_id, bars_to_entry, bar_time,
            candle_range_pct, vol_delta, vol_roc, sma_spread, sma_momentum_ratio,
            m15_structure, h1_structure, long_score, short_score
        ) VALUES %s
        ON CONFLICT (trade_id, bars_to_entry) DO UPDATE SET
            bar_time = EXCLUDED.bar_time,
            candle_range_pct = EXCLUDED.candle_range_pct,
            calculated_at = CURRENT_TIMESTAMP
    """

    values = [(
        p.trade_id, p.bars_to_entry, p.bar_time,
        p.candle_range_pct, p.vol_delta, p.vol_roc, p.sma_spread, p.sma_momentum_ratio,
        p.m15_structure, p.h1_structure, p.long_score, p.short_score,
    ) for p in progressions]

    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    return len(values)


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def run_analysis(
    stop_type: str = STOP_TYPE,
    full_reprocess: bool = False,
    export_csv: bool = False
):
    """Run ramp-up analysis."""
    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("RAMP-UP ANALYSIS")
    logger.info(f"Stop Type: {stop_type}")
    logger.info(f"Lookback Bars: {LOOKBACK_BARS}")
    logger.info("=" * 60)

    conn = get_connection()

    try:
        # Create tables
        logger.info("Creating tables if needed...")
        create_tables(conn)

        # Determine trades to process
        all_trades = set(fetch_all_trade_ids(conn))

        if full_reprocess:
            logger.info("Full reprocess - clearing existing data...")
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE ramp_up_progression")
                cur.execute("TRUNCATE TABLE ramp_up_macro")
            conn.commit()
            trades_to_process = list(all_trades)
        else:
            processed = set(fetch_processed_trade_ids(conn, stop_type))
            trades_to_process = list(all_trades - processed)
            logger.info(f"Incremental: {len(trades_to_process)} new trades ({len(processed)} already done)")

        if not trades_to_process:
            logger.info("No trades to process")
            return

        # Fetch trade data
        logger.info(f"Fetching data for {len(trades_to_process)} trades...")
        trades = fetch_trades(conn, trades_to_process)
        stop_data = fetch_stop_analysis(conn, trades_to_process, stop_type)

        # Process each trade
        all_macros = []
        all_progressions = []
        skipped = 0

        for i, trade in enumerate(trades):
            trade_id = trade['trade_id']

            # Skip if no stop analysis
            if trade_id not in stop_data:
                skipped += 1
                continue

            # Merge stop analysis
            stop = stop_data[trade_id]
            trade['outcome'] = stop['outcome']
            trade['mfe_distance'] = stop['mfe_distance']
            trade['r_achieved'] = stop['r_achieved']

            # Fetch M1 bars
            bars = fetch_m1_bars(
                conn, trade['ticker'], trade['date'],
                trade['entry_time'], LOOKBACK_BARS + 1
            )
            trade['m1_bars'] = bars

            # Calculate
            macro, progressions = calculate_for_trade(trade, stop_type)
            if macro:
                all_macros.append(macro)
                all_progressions.extend(progressions)
            else:
                skipped += 1

            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(trades)} trades...")

        # Insert results
        logger.info(f"Inserting {len(all_macros)} macros, {len(all_progressions)} progressions...")
        macros_inserted = insert_macros(conn, all_macros)
        progs_inserted = insert_progressions(conn, all_progressions)

        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("COMPLETE")
        logger.info(f"Trades processed: {len(all_macros)}")
        logger.info(f"Trades skipped: {skipped}")
        logger.info(f"Macro records: {macros_inserted}")
        logger.info(f"Progression records: {progs_inserted}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 60)

    finally:
        conn.close()


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ramp-up analysis')
    parser.add_argument('--stop-type', default=STOP_TYPE,
                        choices=['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal'])
    parser.add_argument('--full', action='store_true', help='Reprocess all trades')
    parser.add_argument('--export', action='store_true', help='Export to CSV after')

    args = parser.parse_args()

    run_analysis(
        stop_type=args.stop_type,
        full_reprocess=args.full,
        export_csv=args.export
    )
