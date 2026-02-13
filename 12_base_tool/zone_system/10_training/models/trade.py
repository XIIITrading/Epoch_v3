"""
Epoch Trading System - Trade Data Models
Dataclasses for trade records from Supabase.
"""

from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional, List


@dataclass
class Trade:
    """
    Core trade record from trades table.
    Matches schema from 11_database_export/schema/07_trades.sql
    """
    trade_id: str
    date: date
    ticker: str
    model: str  # EPCH1, EPCH2, EPCH3, EPCH4
    zone_type: Optional[str]  # PRIMARY, SECONDARY
    direction: Optional[str]  # LONG, SHORT

    # Zone boundaries
    zone_high: Optional[float]
    zone_low: Optional[float]

    # Entry
    entry_price: Optional[float]
    entry_time: Optional[time]

    # Stop
    stop_price: Optional[float]

    # Targets
    target_3r: Optional[float]
    target_calc: Optional[float]
    target_used: Optional[float]

    # Exit
    exit_price: Optional[float]
    exit_time: Optional[time]
    exit_reason: Optional[str]  # STOP, TARGET_3R, TARGET_CALC, CHOCH, EOD

    # P&L
    pnl_dollars: Optional[float]
    pnl_r: Optional[float]
    risk: Optional[float]

    # Outcome
    is_winner: bool = False

    @classmethod
    def from_db_row(cls, row: dict) -> 'Trade':
        """Create Trade from database row dict."""
        return cls(
            trade_id=row['trade_id'],
            date=row['date'],
            ticker=row['ticker'],
            model=row.get('model'),
            zone_type=row.get('zone_type'),
            direction=row.get('direction'),
            zone_high=row.get('zone_high'),
            zone_low=row.get('zone_low'),
            entry_price=row.get('entry_price'),
            entry_time=row.get('entry_time'),
            stop_price=row.get('stop_price'),
            target_3r=row.get('target_3r'),
            target_calc=row.get('target_calc'),
            target_used=row.get('target_used'),
            exit_price=row.get('exit_price'),
            exit_time=row.get('exit_time'),
            exit_reason=row.get('exit_reason'),
            pnl_dollars=row.get('pnl_dollars'),
            pnl_r=row.get('pnl_r'),
            risk=row.get('risk'),
            is_winner=row.get('is_winner', False),
        )

    @property
    def zone_mid(self) -> Optional[float]:
        """Get zone midpoint (POC approximation)."""
        if self.zone_high and self.zone_low:
            return (self.zone_high + self.zone_low) / 2
        return None

    @property
    def entry_datetime(self) -> Optional[datetime]:
        """Combine date and entry_time into datetime."""
        if self.entry_time:
            return datetime.combine(self.date, self.entry_time)
        return None

    @property
    def exit_datetime(self) -> Optional[datetime]:
        """Combine date and exit_time into datetime."""
        if self.exit_time:
            return datetime.combine(self.date, self.exit_time)
        return None

    @property
    def duration_minutes(self) -> Optional[int]:
        """Trade duration in minutes."""
        if self.entry_datetime and self.exit_datetime:
            delta = self.exit_datetime - self.entry_datetime
            return int(delta.total_seconds() / 60)
        return None


@dataclass
class OptimalTradeEvent:
    """
    Event row from optimal_trade table (v2.0.0 - Points-Based).
    Each trade has 4 events: ENTRY, MFE, MAE, EXIT

    Win condition: mfe_time < mae_time (temporal, not P&L based)
    P&L: Points (absolute $) instead of R-multiples
    Exit: Fixed 15:30 ET
    """
    trade_id: str
    event_type: str  # ENTRY, MFE, MAE, EXIT
    date: date
    ticker: str
    direction: Optional[str]
    model: Optional[str]
    win: Optional[int]  # 1 if mfe_time < mae_time, else 0

    event_time: Optional[time]
    bars_from_entry: Optional[int]

    # Points-based pricing (v2.0.0)
    entry_price: Optional[float]
    price_at_event: Optional[float]
    points_at_event: Optional[float]  # Replaces r_at_event
    actual_points: Optional[float]    # Replaces actual_r

    # Health metrics
    health_score: Optional[int]
    health_label: Optional[str]
    health_delta: Optional[int]
    health_summary: Optional[str]

    # Component scores
    structure_score: Optional[int]
    volume_score: Optional[int]
    price_score: Optional[int]

    # Price indicators
    vwap: Optional[float]
    sma9: Optional[float]
    sma21: Optional[float]
    sma_spread: Optional[float]
    sma_momentum_ratio: Optional[float]
    sma_momentum_label: Optional[str]

    # Volume indicators
    vol_roc: Optional[float]
    vol_delta: Optional[float]
    cvd_slope: Optional[float]

    # Structure
    m5_structure: Optional[str]
    m15_structure: Optional[str]
    h1_structure: Optional[str]
    h4_structure: Optional[str]

    @classmethod
    def from_db_row(cls, row: dict) -> 'OptimalTradeEvent':
        """Create OptimalTradeEvent from database row dict."""
        return cls(
            trade_id=row['trade_id'],
            event_type=row['event_type'],
            date=row['date'],
            ticker=row['ticker'],
            direction=row.get('direction'),
            model=row.get('model'),
            win=row.get('win'),
            event_time=row.get('event_time'),
            bars_from_entry=row.get('bars_from_entry'),
            entry_price=row.get('entry_price'),
            price_at_event=row.get('price_at_event'),
            points_at_event=row.get('points_at_event'),
            actual_points=row.get('actual_points'),
            health_score=row.get('health_score'),
            health_label=row.get('health_label'),
            health_delta=row.get('health_delta'),
            health_summary=row.get('health_summary'),
            structure_score=row.get('structure_score'),
            volume_score=row.get('volume_score'),
            price_score=row.get('price_score'),
            vwap=row.get('vwap'),
            sma9=row.get('sma9'),
            sma21=row.get('sma21'),
            sma_spread=row.get('sma_spread'),
            sma_momentum_ratio=row.get('sma_momentum_ratio'),
            sma_momentum_label=row.get('sma_momentum_label'),
            vol_roc=row.get('vol_roc'),
            vol_delta=row.get('vol_delta'),
            cvd_slope=row.get('cvd_slope'),
            m5_structure=row.get('m5_structure'),
            m15_structure=row.get('m15_structure'),
            h1_structure=row.get('h1_structure'),
            h4_structure=row.get('h4_structure'),
        )


@dataclass
class TradeWithMetrics:
    """
    Trade with MFE/MAE metrics from optimal_trade table (v2.1.0 - R-Multiple Based).
    This is the main data structure used in the flashcard UI.

    Win condition: pnl_r > 0 (R-multiple based, aligned with System Analysis)
    Stop: Zone edge + 5% buffer (default)
    P&L: R-multiples (risk-adjusted) as primary, points as secondary
    Exit: Fixed 15:30 ET (EOD)
    """
    trade: Trade

    # Win condition (temporal: mfe_time < mae_time) - kept for reference
    temporal_win: Optional[int] = None  # 1 if mfe_time < mae_time, else 0

    # MFE metrics (points-based)
    mfe_points: Optional[float] = None
    mfe_bars: Optional[int] = None
    mfe_time: Optional[time] = None
    mfe_price: Optional[float] = None
    mfe_health: Optional[int] = None

    # MAE metrics (points-based)
    mae_points: Optional[float] = None
    mae_bars: Optional[int] = None
    mae_time: Optional[time] = None
    mae_price: Optional[float] = None
    mae_health: Optional[int] = None

    # Exit metrics (fixed 15:30)
    exit_points: Optional[float] = None  # Final P&L in points
    exit_time_actual: Optional[time] = None  # Should be 15:30

    # Entry health
    entry_health: Optional[int] = None

    # Exit health
    exit_health: Optional[int] = None

    # Zone info (from zones table)
    zone_rank: Optional[str] = None
    zone_tier: Optional[str] = None
    zone_score: Optional[float] = None

    # Bookmap image URL (from trade_images table)
    bookmap_url: Optional[str] = None

    # ==========================================================================
    # R-Multiple Calculations (v2.1.0 - Aligned with System Analysis)
    # Stop: Zone edge + 5% buffer (from stop_analysis table or calculated)
    # ==========================================================================

    # Stop analysis data (from stop_analysis table, stop_type='zone_buffer')
    stop_analysis_price: Optional[float] = None  # Pre-calculated stop from DB
    stop_analysis_r_achieved: Optional[float] = None  # R achieved from DB
    stop_analysis_outcome: Optional[str] = None  # WIN/LOSS/PARTIAL from DB
    stop_analysis_mfe_price: Optional[float] = None  # MFE price from stop analysis

    # ==========================================================================
    # R-Level Crossing Events (v2.2.0 - Health score tracking at R-levels)
    # Captures indicator snapshots when price crosses 1R, 2R, 3R thresholds
    # ==========================================================================

    # R1 crossing event (1R target)
    r1_crossed: bool = False
    r1_time: Optional[time] = None
    r1_bars: Optional[int] = None
    r1_health: Optional[int] = None
    r1_health_delta: Optional[int] = None  # Change from entry health
    r1_health_summary: Optional[str] = None  # IMPROVING, DEGRADING, STABLE

    # R2 crossing event (2R target)
    r2_crossed: bool = False
    r2_time: Optional[time] = None
    r2_bars: Optional[int] = None
    r2_health: Optional[int] = None
    r2_health_delta: Optional[int] = None
    r2_health_summary: Optional[str] = None

    # R3 crossing event (3R target)
    r3_crossed: bool = False
    r3_time: Optional[time] = None
    r3_bars: Optional[int] = None
    r3_health: Optional[int] = None
    r3_health_delta: Optional[int] = None
    r3_health_summary: Optional[str] = None

    @property
    def default_stop_price(self) -> Optional[float]:
        """
        Get stop price: prefer stop_analysis table, fallback to calculation.
        Zone edge + 5% buffer.
        For LONG: zone_low - (zone_height * 0.05)
        For SHORT: zone_high + (zone_height * 0.05)
        """
        # Prefer pre-calculated stop from stop_analysis table
        if self.stop_analysis_price is not None:
            return float(self.stop_analysis_price)

        # Fallback to calculation
        if not self.zone_high or not self.zone_low or not self.direction:
            return None

        # Convert Decimal to float for calculation
        zone_high = float(self.zone_high)
        zone_low = float(self.zone_low)
        zone_height = zone_high - zone_low
        buffer = zone_height * 0.05

        if self.direction == 'LONG':
            return zone_low - buffer
        else:  # SHORT
            return zone_high + buffer

    @property
    def risk_per_share(self) -> Optional[float]:
        """Calculate risk per share (distance from entry to stop)."""
        if not self.entry_price or not self.default_stop_price:
            return None
        return abs(float(self.entry_price) - float(self.default_stop_price))

    @property
    def r1_price(self) -> Optional[float]:
        """Calculate 1R target price."""
        if not self.entry_price or not self.risk_per_share or not self.direction:
            return None
        entry = float(self.entry_price)
        if self.direction == 'LONG':
            return entry + self.risk_per_share
        else:  # SHORT
            return entry - self.risk_per_share

    @property
    def r2_price(self) -> Optional[float]:
        """Calculate 2R target price."""
        if not self.entry_price or not self.risk_per_share or not self.direction:
            return None
        entry = float(self.entry_price)
        if self.direction == 'LONG':
            return entry + (2 * self.risk_per_share)
        else:  # SHORT
            return entry - (2 * self.risk_per_share)

    @property
    def r3_price(self) -> Optional[float]:
        """Calculate 3R target price."""
        if not self.entry_price or not self.risk_per_share or not self.direction:
            return None
        entry = float(self.entry_price)
        if self.direction == 'LONG':
            return entry + (3 * self.risk_per_share)
        else:  # SHORT
            return entry - (3 * self.risk_per_share)

    def calculate_r_multiple(self, price: float) -> Optional[float]:
        """
        Calculate R-multiple for any price relative to entry.
        Aligned with System Analysis logic.

        Args:
            price: The price to calculate R-multiple for

        Returns:
            R-multiple (positive = favorable, negative = adverse)
        """
        if not self.entry_price or not self.risk_per_share or self.risk_per_share == 0:
            return None

        entry = float(self.entry_price)
        price = float(price)

        if self.direction == 'LONG':
            pnl = price - entry
        else:  # SHORT
            pnl = entry - price

        return pnl / self.risk_per_share

    @property
    def mfe_r(self) -> Optional[float]:
        """MFE in R-multiples."""
        if self.mfe_price:
            return self.calculate_r_multiple(self.mfe_price)
        return None

    @property
    def mae_r(self) -> Optional[float]:
        """MAE in R-multiples (will be negative)."""
        if self.mae_price:
            return self.calculate_r_multiple(self.mae_price)
        return None

    @property
    def pnl_r(self) -> Optional[float]:
        """Final P&L in R-multiples (EOD exit)."""
        if self.trade.exit_price:
            return self.calculate_r_multiple(self.trade.exit_price)
        return None

    @property
    def is_winner_r(self) -> bool:
        """
        Win condition based on R-multiple (aligned with System Analysis).
        A trade is a winner if pnl_r > 0.
        """
        r = self.pnl_r
        return r is not None and r > 0

    @property
    def outcome_r(self) -> str:
        """Classify trade outcome based on R-multiple."""
        r = self.pnl_r
        if r is None:
            return "UNKNOWN"
        if r > 0:
            return "WIN"
        elif r < 0:
            return "LOSS"
        return "BREAKEVEN"

    @classmethod
    def from_trade_and_events(
        cls,
        trade: Trade,
        events: List[OptimalTradeEvent],
        zone_info: Optional[dict] = None,
        bookmap_url: Optional[str] = None,
        stop_analysis: Optional[dict] = None
    ) -> 'TradeWithMetrics':
        """Create TradeWithMetrics from Trade and list of OptimalTradeEvents.

        Args:
            trade: Core trade data
            events: List of OptimalTradeEvent (ENTRY, MFE, MAE, EXIT)
            zone_info: Optional zone metadata (rank, tier, score)
            bookmap_url: Optional URL to bookmap image
            stop_analysis: Optional stop analysis data for zone_buffer stop type
        """

        # Initialize with trade
        result = cls(trade=trade, bookmap_url=bookmap_url)

        # Extract metrics from events
        for event in events:
            # Get win condition from any event (same for all 4)
            if result.temporal_win is None and event.win is not None:
                result.temporal_win = event.win

            if event.event_type == 'ENTRY':
                result.entry_health = event.health_score
            elif event.event_type == 'MFE':
                result.mfe_points = event.points_at_event
                result.mfe_bars = event.bars_from_entry
                result.mfe_time = event.event_time
                result.mfe_price = event.price_at_event
                result.mfe_health = event.health_score
            elif event.event_type == 'MAE':
                result.mae_points = event.points_at_event
                result.mae_bars = event.bars_from_entry
                result.mae_time = event.event_time
                result.mae_price = event.price_at_event
                result.mae_health = event.health_score
            elif event.event_type == 'EXIT':
                result.exit_health = event.health_score
                result.exit_points = event.points_at_event
                result.exit_time_actual = event.event_time
            # R-level crossing events (v2.2.0)
            elif event.event_type == 'R1_CROSS':
                result.r1_crossed = True
                result.r1_time = event.event_time
                result.r1_bars = event.bars_from_entry
                result.r1_health = event.health_score
                result.r1_health_delta = event.health_delta
                result.r1_health_summary = event.health_summary
            elif event.event_type == 'R2_CROSS':
                result.r2_crossed = True
                result.r2_time = event.event_time
                result.r2_bars = event.bars_from_entry
                result.r2_health = event.health_score
                result.r2_health_delta = event.health_delta
                result.r2_health_summary = event.health_summary
            elif event.event_type == 'R3_CROSS':
                result.r3_crossed = True
                result.r3_time = event.event_time
                result.r3_bars = event.bars_from_entry
                result.r3_health = event.health_score
                result.r3_health_delta = event.health_delta
                result.r3_health_summary = event.health_summary

        # Add zone info if provided
        if zone_info:
            result.zone_rank = zone_info.get('rank')
            result.zone_tier = zone_info.get('tier')
            result.zone_score = zone_info.get('score')

        # Add stop analysis data (zone_buffer) if provided
        if stop_analysis:
            result.stop_analysis_price = stop_analysis.get('stop_price')
            result.stop_analysis_r_achieved = stop_analysis.get('r_achieved')
            result.stop_analysis_outcome = stop_analysis.get('outcome')
            result.stop_analysis_mfe_price = stop_analysis.get('mfe_price')

        return result

    # Convenience properties
    @property
    def trade_id(self) -> str:
        return self.trade.trade_id

    @property
    def ticker(self) -> str:
        return self.trade.ticker

    @property
    def date(self) -> date:
        return self.trade.date

    @property
    def direction(self) -> Optional[str]:
        return self.trade.direction

    @property
    def pnl_points(self) -> Optional[float]:
        """Final P&L in points (absolute $)."""
        return self.exit_points

    @property
    def is_winner(self) -> bool:
        """Win condition: mfe_time < mae_time (temporal)."""
        return self.temporal_win == 1

    @property
    def entry_time(self) -> Optional[time]:
        return self.trade.entry_time

    @property
    def exit_time(self) -> Optional[time]:
        """Exit time (fixed 15:30 ET for v2.0.0)."""
        return self.exit_time_actual or self.trade.exit_time

    @property
    def entry_price(self) -> Optional[float]:
        return self.trade.entry_price

    @property
    def exit_price(self) -> Optional[float]:
        return self.trade.exit_price

    @property
    def zone_high(self) -> Optional[float]:
        return self.trade.zone_high

    @property
    def zone_low(self) -> Optional[float]:
        return self.trade.zone_low

    @property
    def duration_minutes(self) -> Optional[int]:
        return self.trade.duration_minutes

    @property
    def exit_reason(self) -> Optional[str]:
        return self.trade.exit_reason

    @property
    def model(self) -> Optional[str]:
        return self.trade.model

    @property
    def zone_type(self) -> Optional[str]:
        return self.trade.zone_type


@dataclass
class Zone:
    """Zone data from zones table."""
    zone_id: str
    ticker: str
    date: date
    zone_high: float
    zone_low: float
    hvn_poc: Optional[float]
    rank: Optional[str]  # L1-L5
    tier: Optional[str]  # T1-T3
    score: Optional[float]
    is_filtered: bool = False  # True if in zone_results, False if raw only

    @classmethod
    def from_db_row(cls, row: dict) -> 'Zone':
        """Create Zone from database row dict."""
        return cls(
            zone_id=row['zone_id'],
            ticker=row['ticker'],
            date=row['date'],
            zone_high=row['zone_high'],
            zone_low=row['zone_low'],
            hvn_poc=row.get('hvn_poc'),
            rank=row.get('rank'),
            tier=row.get('tier'),
            score=row.get('score'),
            is_filtered=row.get('is_filtered', False),
        )

    @property
    def zone_mid(self) -> float:
        """Get zone midpoint."""
        return (self.zone_high + self.zone_low) / 2


@dataclass
class TradeReview:
    """
    Trade review record from trade_reviews table.
    Stores user notes and flags for trade analysis.
    """
    trade_id: str
    actual_outcome: str  # 'winner', 'loser', 'breakeven'
    notes: Optional[str] = None

    # Accuracy & Confirmation (EPCH v1.0)
    accuracy: bool = False  # Did trader predict correctly?
    tape_confirmation: bool = False  # Was tape confirmation present?

    # Trade Quality
    good_trade: bool = False
    signal_aligned: bool = False
    confirmation_required: bool = False

    # Stop Placement
    prior_candle_stop: bool = False
    two_candle_stop: bool = False
    atr_stop: bool = False
    zone_edge_stop: bool = False

    # Entry Attempt (1, 2, 3, or None)
    entry_attempt: Optional[int] = None

    # Trade Context
    with_trend: bool = False
    counter_trend: bool = False

    # Outcome Details
    stopped_by_wick: bool = False

    @classmethod
    def from_db_row(cls, row: dict) -> 'TradeReview':
        """Create TradeReview from database row dict."""
        return cls(
            trade_id=row['trade_id'],
            actual_outcome=row.get('actual_outcome', 'loser'),
            notes=row.get('notes'),
            # Accuracy & Confirmation
            accuracy=row.get('accuracy', False),
            tape_confirmation=row.get('tape_confirmation', False),
            # Trade Quality
            good_trade=row.get('good_trade', False),
            signal_aligned=row.get('signal_aligned', False),
            confirmation_required=row.get('confirmation_required', False),
            # Stop Placement
            prior_candle_stop=row.get('prior_candle_stop', False),
            two_candle_stop=row.get('two_candle_stop', False),
            atr_stop=row.get('atr_stop', False),
            zone_edge_stop=row.get('zone_edge_stop', False),
            # Entry Attempt
            entry_attempt=row.get('entry_attempt'),
            # Trade Context
            with_trend=row.get('with_trend', False),
            counter_trend=row.get('counter_trend', False),
            # Outcome Details
            stopped_by_wick=row.get('stopped_by_wick', False),
        )

    def to_dict(self) -> dict:
        """Convert to dict for database insert/update."""
        return {
            'trade_id': self.trade_id,
            'actual_outcome': self.actual_outcome,
            'notes': self.notes,
            'accuracy': self.accuracy,
            'tape_confirmation': self.tape_confirmation,
            'good_trade': self.good_trade,
            'signal_aligned': self.signal_aligned,
            'confirmation_required': self.confirmation_required,
            'prior_candle_stop': self.prior_candle_stop,
            'two_candle_stop': self.two_candle_stop,
            'atr_stop': self.atr_stop,
            'zone_edge_stop': self.zone_edge_stop,
            'entry_attempt': self.entry_attempt,
            'with_trend': self.with_trend,
            'counter_trend': self.counter_trend,
            'stopped_by_wick': self.stopped_by_wick,
        }


@dataclass
class TradeAnalysis:
    """
    Claude AI analysis record from trade_analysis table.
    Stores pre-trade and post-trade analysis responses.
    """
    trade_id: str
    analysis_type: str  # 'pre_trade' or 'post_trade'
    response_text: str
    prompt_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> 'TradeAnalysis':
        """Create TradeAnalysis from database row dict."""
        return cls(
            trade_id=row['trade_id'],
            analysis_type=row['analysis_type'],
            response_text=row['response_text'],
            prompt_text=row.get('prompt_text'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
