"""
Journal Trade With Metrics — Data model for the flashcard training UI.

Wraps the existing Trade model from core/models.py and adds calculated metrics
from the 5 journal training tables. Provides property accessors that match
the 06_training.TradeWithMetrics interface so UI components work with the
same field names.

Usage:
    from core.training_models import JournalTradeWithMetrics

    trade_with_metrics = JournalTradeWithMetrics.from_db_rows(
        trade_row=trade_dict,
        mfe_mae_row=mfe_dict,
        r_levels_row=r_levels_dict,
        entry_indicators_row=ei_dict,
        optimal_events=events_dict,
        zone_row=zone_dict,
    )
"""

from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional, Dict, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import Trade, TradeDirection


@dataclass
class JournalTradeWithMetrics:
    """
    Journal trade with MFE/MAE metrics, R-levels, events, and zone info.
    Adapted from 06_training TradeWithMetrics for journal data.
    """
    trade: Trade

    # --- MFE/MAE (from journal_mfe_mae_potential) ---
    mfe_r: Optional[float] = None
    mfe_price: Optional[float] = None
    mfe_time: Optional[time] = None
    mfe_bar_index: Optional[int] = None
    mae_r: Optional[float] = None
    mae_price: Optional[float] = None
    mae_time: Optional[time] = None
    mae_bar_index: Optional[int] = None
    temporal_win: Optional[bool] = None

    # --- R-Levels (from journal_r_levels) ---
    stop_distance: Optional[float] = None
    r1_price: Optional[float] = None
    r2_price: Optional[float] = None
    r3_price: Optional[float] = None
    r1_hit: bool = False
    r1_hit_time: Optional[time] = None
    r1_hit_bar_index: Optional[int] = None
    r2_hit: bool = False
    r2_hit_time: Optional[time] = None
    r2_hit_bar_index: Optional[int] = None
    r3_hit: bool = False
    r3_hit_time: Optional[time] = None
    r3_hit_bar_index: Optional[int] = None
    stop_hit: bool = False
    stop_hit_time: Optional[time] = None
    max_r_achieved: Optional[float] = None
    r_levels_pnl_r: Optional[float] = None
    r_levels_outcome: Optional[str] = None
    r_levels_is_winner: Optional[bool] = None

    # --- Entry Health (from journal_entry_indicators) ---
    entry_health: Optional[int] = None
    entry_vwap: Optional[float] = None
    entry_sma9: Optional[float] = None
    entry_sma21: Optional[float] = None

    # --- Event Healths (from journal_optimal_trade events) ---
    exit_health: Optional[int] = None
    mfe_health: Optional[int] = None
    mae_health: Optional[int] = None

    # R-crossing health (from journal_optimal_trade R_CROSS events)
    r1_crossed: bool = False
    r1_cross_time: Optional[time] = None
    r1_cross_bars: Optional[int] = None
    r1_health: Optional[int] = None
    r1_health_delta: Optional[int] = None
    r1_health_summary: Optional[str] = None

    r2_crossed: bool = False
    r2_cross_time: Optional[time] = None
    r2_cross_bars: Optional[int] = None
    r2_health: Optional[int] = None
    r2_health_delta: Optional[int] = None
    r2_health_summary: Optional[str] = None

    r3_crossed: bool = False
    r3_cross_time: Optional[time] = None
    r3_cross_bars: Optional[int] = None
    r3_health: Optional[int] = None
    r3_health_delta: Optional[int] = None
    r3_health_summary: Optional[str] = None

    # --- Zone Info (from zones table via JournalDB) ---
    zone_high: Optional[float] = None
    zone_low: Optional[float] = None
    zone_rank: Optional[str] = None
    zone_tier: Optional[str] = None
    zone_score: Optional[float] = None
    zone_setup_type: Optional[str] = None

    # =========================================================================
    # CONVENIENCE PROPERTIES — Match 06_training TradeWithMetrics interface
    # =========================================================================

    @property
    def trade_id(self) -> str:
        return self.trade.trade_id

    @property
    def ticker(self) -> str:
        return self.trade.symbol

    @property
    def date(self) -> date:
        return self.trade.trade_date

    @property
    def direction(self) -> str:
        return self.trade.direction.value

    @property
    def model(self) -> Optional[str]:
        return self.trade.model

    @property
    def zone_type(self) -> Optional[str]:
        return self.zone_setup_type

    @property
    def entry_price(self) -> float:
        return self.trade.entry_price

    @property
    def exit_price(self) -> Optional[float]:
        return self.trade.exit_price

    @property
    def entry_time(self) -> Optional[time]:
        return self.trade.entry_time

    @property
    def exit_time(self) -> Optional[time]:
        return self.trade.exit_time

    @property
    def entry_datetime(self) -> Optional[datetime]:
        if self.trade.entry_time:
            return datetime.combine(self.trade.trade_date, self.trade.entry_time)
        return None

    @property
    def exit_datetime(self) -> Optional[datetime]:
        if self.trade.exit_time:
            return datetime.combine(self.trade.trade_date, self.trade.exit_time)
        return None

    @property
    def stop_price(self) -> Optional[float]:
        return self.trade.stop_price

    @property
    def default_stop_price(self) -> Optional[float]:
        return self.trade.stop_price

    @property
    def risk_per_share(self) -> Optional[float]:
        return self.stop_distance

    @property
    def pnl_r(self) -> Optional[float]:
        """P&L in R-multiples. Prefer r_levels calculation, fallback to trade."""
        if self.r_levels_pnl_r is not None:
            return self.r_levels_pnl_r
        return self.trade.pnl_r

    @property
    def pnl_points(self) -> Optional[float]:
        """P&L in dollars per share (points)."""
        return self.trade.pnl_dollars

    @property
    def pnl_total(self) -> Optional[float]:
        """Total dollar P&L."""
        return self.trade.pnl_total

    @property
    def is_winner(self) -> bool:
        return self.trade.outcome.value == 'WIN'

    @property
    def is_winner_r(self) -> bool:
        """Win condition based on R-multiples."""
        if self.r_levels_is_winner is not None:
            return self.r_levels_is_winner
        r = self.pnl_r
        return r is not None and r > 0

    @property
    def outcome_r(self) -> str:
        """Classify trade outcome."""
        if self.r_levels_outcome:
            return self.r_levels_outcome
        r = self.pnl_r
        if r is None:
            return "UNKNOWN"
        if r > 0:
            return "WIN"
        elif r < 0:
            return "LOSS"
        return "BREAKEVEN"

    @property
    def mfe_bars(self) -> Optional[int]:
        return self.mfe_bar_index

    @property
    def mae_bars(self) -> Optional[int]:
        return self.mae_bar_index

    @property
    def mfe_points(self) -> Optional[float]:
        """MFE in points (dollars per share)."""
        if self.mfe_price is None:
            return None
        if self.direction == 'LONG':
            return self.mfe_price - self.entry_price
        else:
            return self.entry_price - self.mfe_price

    @property
    def mae_points(self) -> Optional[float]:
        """MAE in points (dollars per share)."""
        if self.mae_price is None:
            return None
        if self.direction == 'LONG':
            return self.mae_price - self.entry_price  # negative for LONG
        else:
            return self.entry_price - self.mae_price  # negative for SHORT

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.trade.duration_seconds is not None:
            return self.trade.duration_seconds // 60
        return None

    @property
    def duration_display(self) -> Optional[str]:
        return self.trade.duration_display

    @property
    def exit_reason(self) -> Optional[str]:
        """Exit reason — journal uses manual exit, not system-generated."""
        return None  # Journal trades don't have system exit reasons

    @property
    def zone_mid(self) -> Optional[float]:
        if self.zone_high and self.zone_low:
            return (self.zone_high + self.zone_low) / 2
        return None

    def calculate_r_multiple(self, price: float) -> Optional[float]:
        """Calculate R-multiple for any price."""
        if not self.risk_per_share or self.risk_per_share == 0:
            return None
        if self.direction == 'LONG':
            return (price - self.entry_price) / self.risk_per_share
        else:
            return (self.entry_price - price) / self.risk_per_share

    # =========================================================================
    # FACTORY
    # =========================================================================

    @classmethod
    def from_db_rows(
        cls,
        trade_row: Dict,
        mfe_mae_row: Optional[Dict] = None,
        r_levels_row: Optional[Dict] = None,
        entry_indicators_row: Optional[Dict] = None,
        optimal_events: Optional[Dict[str, Dict]] = None,
        zone_row: Optional[Dict] = None,
    ) -> 'JournalTradeWithMetrics':
        """
        Build JournalTradeWithMetrics from database row dicts.

        Args:
            trade_row: Dict from journal_trades
            mfe_mae_row: Dict from journal_mfe_mae_potential
            r_levels_row: Dict from journal_r_levels
            entry_indicators_row: Dict from journal_entry_indicators
            optimal_events: Dict[event_type → Dict] from journal_optimal_trade
            zone_row: Dict from zones table
        """
        trade = Trade.from_db_row(trade_row)

        kwargs = {'trade': trade}

        # MFE/MAE
        if mfe_mae_row:
            kwargs.update({
                'mfe_r': _sf(mfe_mae_row.get('mfe_r')),
                'mfe_price': _sf(mfe_mae_row.get('mfe_price')),
                'mfe_time': mfe_mae_row.get('mfe_time'),
                'mfe_bar_index': _si(mfe_mae_row.get('mfe_bar_index')),
                'mae_r': _sf(mfe_mae_row.get('mae_r')),
                'mae_price': _sf(mfe_mae_row.get('mae_price')),
                'mae_time': mfe_mae_row.get('mae_time'),
                'mae_bar_index': _si(mfe_mae_row.get('mae_bar_index')),
                'temporal_win': mfe_mae_row.get('temporal_win'),
            })

        # R-Levels
        if r_levels_row:
            kwargs.update({
                'stop_distance': _sf(r_levels_row.get('stop_distance')),
                'r1_price': _sf(r_levels_row.get('r1_price')),
                'r2_price': _sf(r_levels_row.get('r2_price')),
                'r3_price': _sf(r_levels_row.get('r3_price')),
                'r1_hit': bool(r_levels_row.get('r1_hit')),
                'r1_hit_time': r_levels_row.get('r1_hit_time'),
                'r1_hit_bar_index': _si(r_levels_row.get('r1_hit_bar_index')),
                'r2_hit': bool(r_levels_row.get('r2_hit')),
                'r2_hit_time': r_levels_row.get('r2_hit_time'),
                'r2_hit_bar_index': _si(r_levels_row.get('r2_hit_bar_index')),
                'r3_hit': bool(r_levels_row.get('r3_hit')),
                'r3_hit_time': r_levels_row.get('r3_hit_time'),
                'r3_hit_bar_index': _si(r_levels_row.get('r3_hit_bar_index')),
                'stop_hit': bool(r_levels_row.get('stop_hit')),
                'stop_hit_time': r_levels_row.get('stop_hit_time'),
                'max_r_achieved': _sf(r_levels_row.get('max_r_achieved')),
                'r_levels_pnl_r': _sf(r_levels_row.get('pnl_r')),
                'r_levels_outcome': r_levels_row.get('outcome'),
                'r_levels_is_winner': r_levels_row.get('is_winner'),
            })

        # Entry Indicators
        if entry_indicators_row:
            kwargs.update({
                'entry_health': _si(entry_indicators_row.get('health_score')),
                'entry_vwap': _sf(entry_indicators_row.get('vwap')),
                'entry_sma9': _sf(entry_indicators_row.get('sma9')),
                'entry_sma21': _sf(entry_indicators_row.get('sma21')),
            })

        # Optimal Trade Events (health at each event)
        if optimal_events:
            # MFE health
            mfe_event = optimal_events.get('MFE')
            if mfe_event:
                kwargs['mfe_health'] = _si(mfe_event.get('health_score'))

            # MAE health
            mae_event = optimal_events.get('MAE')
            if mae_event:
                kwargs['mae_health'] = _si(mae_event.get('health_score'))

            # EXIT health
            exit_event = optimal_events.get('EXIT')
            if exit_event:
                kwargs['exit_health'] = _si(exit_event.get('health_score'))

            # R1 crossing
            r1_event = optimal_events.get('R1_CROSS')
            if r1_event:
                kwargs.update({
                    'r1_crossed': True,
                    'r1_cross_time': r1_event.get('event_time'),
                    'r1_cross_bars': _si(r1_event.get('bars_from_entry')),
                    'r1_health': _si(r1_event.get('health_score')),
                    'r1_health_delta': _si(r1_event.get('health_delta')),
                    'r1_health_summary': r1_event.get('health_summary'),
                })

            # R2 crossing
            r2_event = optimal_events.get('R2_CROSS')
            if r2_event:
                kwargs.update({
                    'r2_crossed': True,
                    'r2_cross_time': r2_event.get('event_time'),
                    'r2_cross_bars': _si(r2_event.get('bars_from_entry')),
                    'r2_health': _si(r2_event.get('health_score')),
                    'r2_health_delta': _si(r2_event.get('health_delta')),
                    'r2_health_summary': r2_event.get('health_summary'),
                })

            # R3 crossing
            r3_event = optimal_events.get('R3_CROSS')
            if r3_event:
                kwargs.update({
                    'r3_crossed': True,
                    'r3_cross_time': r3_event.get('event_time'),
                    'r3_cross_bars': _si(r3_event.get('bars_from_entry')),
                    'r3_health': _si(r3_event.get('health_score')),
                    'r3_health_delta': _si(r3_event.get('health_delta')),
                    'r3_health_summary': r3_event.get('health_summary'),
                })

        # Zone info
        if zone_row:
            kwargs.update({
                'zone_high': _sf(zone_row.get('zone_high')),
                'zone_low': _sf(zone_row.get('zone_low')),
                'zone_rank': zone_row.get('rank'),
                'zone_tier': zone_row.get('tier'),
                'zone_score': _sf(zone_row.get('score')),
                'zone_setup_type': zone_row.get('setup_type'),
            })

        return cls(**kwargs)


# =============================================================================
# HELPERS
# =============================================================================

def _sf(val) -> Optional[float]:
    """Safe float conversion."""
    if val is None:
        return None
    try:
        f = float(val)
        import math
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _si(val) -> Optional[int]:
    """Safe int conversion."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
