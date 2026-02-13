"""
DOW AI v3.0 Trade Loader
Epoch Trading System - XIII Trading LLC

Loads trades with FULL M1 indicator bar data for dual-pass analysis.
This is the key difference from v2.0 - we load ALL columns from m1_indicator_bars,
not just a subset.
"""

import logging
from datetime import date, time
from typing import List, Optional, Set, Dict, Any
import json

import psycopg2
from psycopg2.extras import RealDictCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG, AI_CONTEXT_DIR, M1_RAMPUP_BARS

# Import v3 data structures
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ai_context'))
from prompt_v3 import M1BarFull, TradeForAnalysis


logger = logging.getLogger(__name__)


class TradeLoaderV3:
    """
    Loads trades with complete M1 indicator data for v3.0 dual-pass analysis.

    Key differences from v2.0 loader:
    - Loads ALL columns from m1_indicator_bars (not just a subset)
    - Returns M1BarFull objects with structure indicators per bar
    - Caches AI context for Pass 2 prompts
    """

    def __init__(self):
        """Initialize loader."""
        self._ai_context = None

    def load_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        direction: Optional[str] = None,
        exclude_analyzed: bool = True,
        limit: Optional[int] = None
    ) -> List[TradeForAnalysis]:
        """
        Load trades with full M1 bar data for dual-pass analysis.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            ticker: Filter by ticker symbol
            model: Filter by model (EPCH1-4)
            direction: Filter by direction (LONG/SHORT)
            exclude_analyzed: Skip trades already in dual_pass_analysis
            limit: Maximum trades to load

        Returns:
            List of TradeForAnalysis objects with full M1 bar data
        """
        # Build trade query - canonical outcome from trades_m5_r_win (M5 ATR 1.1x stop)
        query = """
        SELECT
            t.trade_id,
            t.date as trade_date,
            t.ticker,
            t.direction,
            t.model,
            t.zone_type,
            t.entry_price,
            t.entry_time,
            COALESCE(tu.is_winner, t.is_winner) as is_winner,
            COALESCE(tu.pnl_r, t.pnl_r) as pnl_r
        FROM trades t
        JOIN entry_indicators ei ON t.trade_id = ei.trade_id
        LEFT JOIN trades_m5_r_win tu ON t.trade_id = tu.trade_id
        WHERE ei.health_score IS NOT NULL
        """

        params = []

        if exclude_analyzed:
            query += """
            AND NOT EXISTS (
                SELECT 1 FROM dual_pass_analysis dpa
                WHERE dpa.trade_id = t.trade_id
            )
            """

        if start_date:
            query += " AND t.date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND t.date <= %s"
            params.append(end_date)

        if ticker:
            query += " AND t.ticker = %s"
            params.append(ticker.upper())

        if model:
            query += " AND t.model = %s"
            params.append(model.upper())

        if direction:
            query += " AND t.direction = %s"
            params.append(direction.upper())

        query += " ORDER BY t.date DESC, t.entry_time DESC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        # Execute query
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        conn.close()

        logger.info(f"Found {len(rows)} trades matching criteria")

        # Convert to TradeForAnalysis objects
        trades = []
        for row in rows:
            # Load M1 bars with FULL indicators
            m1_bars = self._load_m1_bars_full(
                ticker=row['ticker'],
                bar_date=row['trade_date'],
                entry_time=row['entry_time'],
                num_bars=M1_RAMPUP_BARS
            )

            if len(m1_bars) < 5:
                logger.warning(f"Insufficient M1 bars for {row['trade_id']}: {len(m1_bars)} bars")
                continue

            trade = TradeForAnalysis(
                trade_id=row['trade_id'],
                ticker=row['ticker'],
                trade_date=str(row['trade_date']),
                entry_time=str(row['entry_time']),
                direction=row['direction'],
                entry_price=float(row['entry_price']),
                model=row['model'],
                zone_type=row['zone_type'],
                m1_bars=m1_bars,
                is_winner=row['is_winner'],
                pnl_r=float(row['pnl_r']) if row['pnl_r'] else None
            )
            trades.append(trade)

        logger.info(f"Loaded {len(trades)} trades with M1 bar data")
        return trades

    def _load_m1_bars_full(
        self,
        ticker: str,
        bar_date: date,
        entry_time: time,
        num_bars: int = 15
    ) -> List[M1BarFull]:
        """
        Load M1 bars with ALL indicator fields from m1_indicator_bars.

        This is the key v3.0 change - we load everything the table has,
        so Claude sees exactly what a human trader would see.
        """
        query = """
        SELECT
            bar_time,
            open, high, low, close, volume,
            vwap,
            sma9, sma21, sma_spread, sma_momentum_label,
            vol_roc, vol_delta, cvd_slope,
            h1_structure, m15_structure, m5_structure, m1_structure,
            candle_range_pct,
            long_score, short_score
        FROM m1_indicator_bars
        WHERE ticker = %s
          AND bar_date = %s
          AND bar_time < %s
        ORDER BY bar_time DESC
        LIMIT %s
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker, bar_date, entry_time, num_bars))
            rows = cur.fetchall()
        conn.close()

        # Convert to M1BarFull objects (reverse to chronological order)
        bars = []
        for i, row in enumerate(reversed(rows)):
            bar_index = -(num_bars - i)  # -15 to -1

            bar = M1BarFull(
                bar_index=bar_index,
                bar_time=row['bar_time'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                vol_delta=float(row['vol_delta']) if row['vol_delta'] else 0,
                vol_roc=float(row['vol_roc']) if row['vol_roc'] else 0,
                cvd_slope=float(row['cvd_slope']) if row['cvd_slope'] else 0,
                candle_range_pct=float(row['candle_range_pct']) if row['candle_range_pct'] else 0,
                vwap=float(row['vwap']) if row['vwap'] else 0,
                sma9=float(row['sma9']) if row['sma9'] else 0,
                sma21=float(row['sma21']) if row['sma21'] else 0,
                sma_spread=float(row['sma_spread']) if row['sma_spread'] else 0,
                sma_momentum_label=row['sma_momentum_label'] or 'N/A',
                h1_structure=row['h1_structure'] or 'N/A',
                m15_structure=row['m15_structure'] or 'N/A',
                m5_structure=row['m5_structure'] or 'N/A',
                m1_structure=row['m1_structure'] or 'N/A',
                long_score=int(row['long_score']) if row['long_score'] else 0,
                short_score=int(row['short_score']) if row['short_score'] else 0
            )
            bars.append(bar)

        return bars

    def load_ai_context(self) -> Dict[str, Any]:
        """
        Load AI context files for Pass 2 prompts.

        Returns cached context on subsequent calls.
        """
        if self._ai_context is not None:
            return self._ai_context

        context = {}

        # Indicator edges
        edges_file = AI_CONTEXT_DIR / "indicator_edges.json"
        if edges_file.exists():
            with open(edges_file, 'r') as f:
                context['indicator_edges'] = json.load(f)
            logger.debug(f"Loaded indicator edges from {edges_file}")

        # Zone performance
        zone_file = AI_CONTEXT_DIR / "zone_performance.json"
        if zone_file.exists():
            with open(zone_file, 'r') as f:
                context['zone_performance'] = json.load(f)
            logger.debug(f"Loaded zone performance from {zone_file}")

        # Model stats
        stats_file = AI_CONTEXT_DIR / "model_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                context['model_stats'] = json.load(f)
            logger.debug(f"Loaded model stats from {stats_file}")

        self._ai_context = context
        return context

    def get_trade_count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        direction: Optional[str] = None,
        exclude_analyzed: bool = True
    ) -> int:
        """Get count of trades matching criteria."""
        query = """
        SELECT COUNT(*)
        FROM trades t
        JOIN entry_indicators ei ON t.trade_id = ei.trade_id
        WHERE ei.health_score IS NOT NULL
        """

        params = []

        if exclude_analyzed:
            query += """
            AND NOT EXISTS (
                SELECT 1 FROM dual_pass_analysis dpa
                WHERE dpa.trade_id = t.trade_id
            )
            """

        if start_date:
            query += " AND t.date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND t.date <= %s"
            params.append(end_date)

        if ticker:
            query += " AND t.ticker = %s"
            params.append(ticker.upper())

        if model:
            query += " AND t.model = %s"
            params.append(model.upper())

        if direction:
            query += " AND t.direction = %s"
            params.append(direction.upper())

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(query, params)
            count = cur.fetchone()[0]
        conn.close()

        return count
