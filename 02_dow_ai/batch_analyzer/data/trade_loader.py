"""
Trade Loader
Loads trades with entry indicators from Supabase for batch analysis.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import List, Optional, Dict, Any
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG, AI_CONTEXT_DIR, M1_RAMPUP_BARS
from models.trade_context import TradeContext, M1Bar, EntryIndicators


class TradeLoader:
    """Loads trades with indicators from Supabase."""

    def __init__(self):
        self._ai_context = None

    def load_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        direction: Optional[str] = None,
        exclude_processed: bool = True,
        limit: Optional[int] = None
    ) -> List[TradeContext]:
        """
        Load trades with entry indicators.

        Args:
            start_date: Start date filter
            end_date: End date filter
            ticker: Filter by ticker
            model: Filter by model (EPCH1-4)
            direction: Filter by direction (LONG/SHORT)
            exclude_processed: Exclude trades already in ai_predictions
            limit: Maximum number of trades to load

        Returns:
            List of TradeContext objects
        """
        query = """
        SELECT
            t.trade_id,
            t.date,
            t.ticker,
            t.direction,
            t.model,
            t.zone_type,
            t.entry_price,
            t.entry_time,
            -- Canonical outcome from trades_m5_r_win (M5 ATR 1.1x stop)
            COALESCE(tu.is_winner, t.is_winner) as is_winner,
            COALESCE(tu.pnl_r, t.pnl_r) as pnl_r,
            -- Entry indicators
            ei.health_score,
            ei.health_label,
            ei.structure_score,
            ei.volume_score,
            ei.price_score,
            ei.h4_structure,
            ei.h4_structure_healthy,
            ei.h1_structure,
            ei.h1_structure_healthy,
            ei.m15_structure,
            ei.m15_structure_healthy,
            ei.m5_structure,
            ei.m5_structure_healthy,
            ei.vol_roc,
            ei.vol_roc_healthy,
            ei.vol_delta,
            ei.vol_delta_healthy,
            ei.cvd_slope,
            ei.cvd_slope_healthy,
            ei.sma9,
            ei.sma21,
            ei.sma_spread,
            ei.sma_alignment,
            ei.sma_alignment_healthy,
            ei.sma_momentum_label,
            ei.sma_momentum_healthy,
            ei.vwap,
            ei.vwap_position,
            ei.vwap_healthy
        FROM trades t
        JOIN entry_indicators ei ON t.trade_id = ei.trade_id
        LEFT JOIN trades_m5_r_win tu ON t.trade_id = tu.trade_id
        WHERE ei.health_score IS NOT NULL
        """

        params = []

        if exclude_processed:
            query += """
            AND NOT EXISTS (
                SELECT 1 FROM ai_predictions ap
                WHERE ap.trade_id = t.trade_id
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

        query += " ORDER BY t.date, t.entry_time"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        conn.close()

        trades = []
        for row in rows:
            trade = TradeContext.from_db_row(dict(row))
            trade.ai_context = self.load_ai_context()
            trades.append(trade)

        return trades

    def load_m1_rampup(self, trade: TradeContext, num_bars: int = M1_RAMPUP_BARS) -> List[M1Bar]:
        """Load M1 bars before entry for ramp-up display."""
        query = """
        SELECT
            bar_time,
            open, high, low, close, volume,
            candle_range_pct,
            vol_delta,
            vol_roc,
            sma_spread,
            h1_structure,
            long_score,
            short_score
        FROM m1_indicator_bars
        WHERE ticker = %s
          AND bar_date = %s
          AND bar_time < %s
        ORDER BY bar_time DESC
        LIMIT %s
        """

        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                trade.ticker,
                trade.trade_date,
                trade.entry_time,
                num_bars
            ))
            rows = cur.fetchall()
        conn.close()

        # Convert to M1Bar objects (reverse to chronological order)
        bars = []
        for row in reversed(rows):
            bar = M1Bar(
                bar_time=row['bar_time'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                candle_range_pct=float(row['candle_range_pct']) if row['candle_range_pct'] else None,
                vol_delta=float(row['vol_delta']) if row['vol_delta'] else None,
                vol_roc=float(row['vol_roc']) if row['vol_roc'] else None,
                sma_spread=float(row['sma_spread']) if row['sma_spread'] else None,
                h1_structure=row['h1_structure'],
                long_score=int(row['long_score']) if row['long_score'] else None,
                short_score=int(row['short_score']) if row['short_score'] else None,
            )
            bars.append(bar)

        return bars

    def load_ai_context(self) -> Dict[str, Any]:
        """Load cached AI context (indicator edges, zone performance)."""
        if self._ai_context is not None:
            return self._ai_context

        context = {}

        # Load indicator edges
        edges_file = AI_CONTEXT_DIR / "indicator_edges.json"
        if edges_file.exists():
            with open(edges_file, 'r') as f:
                context['indicator_edges'] = json.load(f)

        # Load zone performance
        zone_file = AI_CONTEXT_DIR / "zone_performance.json"
        if zone_file.exists():
            with open(zone_file, 'r') as f:
                context['zone_performance'] = json.load(f)

        # Load model stats
        model_file = AI_CONTEXT_DIR / "model_stats.json"
        if model_file.exists():
            with open(model_file, 'r') as f:
                context['model_stats'] = json.load(f)

        self._ai_context = context
        return context

    def get_trade_count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ticker: Optional[str] = None,
        model: Optional[str] = None,
        direction: Optional[str] = None,
        exclude_processed: bool = True
    ) -> int:
        """Get count of trades matching criteria."""
        query = """
        SELECT COUNT(*)
        FROM trades t
        JOIN entry_indicators ei ON t.trade_id = ei.trade_id
        WHERE ei.health_score IS NOT NULL
        """

        params = []

        if exclude_processed:
            query += """
            AND NOT EXISTS (
                SELECT 1 FROM ai_predictions ap
                WHERE ap.trade_id = t.trade_id
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
