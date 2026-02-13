"""
Pydantic data models for the Epoch Trading Journal.

Data flow: CSV row → Fill → TradeLeg → Trade → DailyTradeLog

Key design decisions:
- One Trade per symbol per session (all fills blended at VWAP)
- Position state machine determines entry vs exit fills
- S and SS are equivalent (both represent selling)
- All trades assumed closed by end of session
- Adds (scaling back in) are blended into the entry leg
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, List, Dict
from datetime import date, time, datetime
from decimal import Decimal
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class TradeDirection(str, Enum):
    """Direction of a completed trade. Matches existing DB convention."""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeSide(str, Enum):
    """Which side of a trade a leg belongs to."""
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class TradeOutcome(str, Enum):
    """Outcome classification of a completed trade."""
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"  # Defensive — all trades should be closed in practice


class FillSide(str, Enum):
    """
    Raw side code from DAS Trader CSV.
    S and SS are both 'sell' — context determines if it's a short entry
    or a long exit. The position state machine handles this.
    """
    BUY = "B"
    SHORT_SELL = "SS"
    SELL = "S"

    @property
    def is_sell_side(self) -> bool:
        """True for both S and SS — they are equivalent."""
        return self in (FillSide.SHORT_SELL, FillSide.SELL)

    @property
    def is_buy_side(self) -> bool:
        return self == FillSide.BUY


# =============================================================================
# Fill — Single parsed row from DAS Trader CSV
# =============================================================================

class Fill(BaseModel):
    """
    A single parsed fill row from DAS Trader CSV (Format 2).

    One row = one execution. The position state machine in trade_processor.py
    uses sequential fills to determine which are entries vs exits.
    """
    time: time                    # Fill execution time (HH:MM:SS)
    symbol: str                   # Ticker symbol (e.g., "AMD")
    side: FillSide                # B, SS, or S
    price: float                  # Execution price
    qty: int                      # Share quantity
    route: str = ""               # Order route (e.g., "SMAT")
    account: str = ""             # Account identifier
    fill_type: str = ""           # "Margin", "Short", etc. (CSV column "Type")
    cloid: str = ""               # Client order ID

    @computed_field
    @property
    def notional(self) -> float:
        """Dollar value of this fill (price * qty)."""
        return self.price * self.qty


# =============================================================================
# TradeLeg — Aggregated fills on one side of a trade
# =============================================================================

class TradeLeg(BaseModel):
    """
    Aggregated fills on one side (entry or exit).
    Multiple fills combined into VWAP.

    Example: Short 500 @ $100 + Short 500 @ $101 = TradeLeg(avg_price=100.50, total_qty=1000)
    Adds are included in the entry leg — all entry-side fills blend together.
    """
    side: TradeSide
    fills: List[Fill] = Field(default_factory=list)

    @computed_field
    @property
    def avg_price(self) -> float:
        """Volume-weighted average price across all fills."""
        if not self.fills:
            return 0.0
        total_notional = sum(f.price * f.qty for f in self.fills)
        total_qty = sum(f.qty for f in self.fills)
        return total_notional / total_qty if total_qty else 0.0

    @computed_field
    @property
    def total_qty(self) -> int:
        """Total shares across all fills in this leg."""
        return sum(f.qty for f in self.fills)

    @computed_field
    @property
    def first_fill_time(self) -> Optional[time]:
        """Earliest fill time in this leg."""
        if not self.fills:
            return None
        return min(f.time for f in self.fills)

    @computed_field
    @property
    def last_fill_time(self) -> Optional[time]:
        """Latest fill time in this leg."""
        if not self.fills:
            return None
        return max(f.time for f in self.fills)

    @computed_field
    @property
    def fill_count(self) -> int:
        """Number of individual fills in this leg."""
        return len(self.fills)


# =============================================================================
# Trade — Complete round-trip trade
# =============================================================================

class Trade(BaseModel):
    """
    A complete round-trip trade: entry leg + exit leg.

    One Trade per symbol per session. All entry-side fills (including adds)
    are blended into the entry leg at VWAP. All exit-side fills are blended
    into the exit leg at VWAP.

    trade_id format: {SYMBOL}_{MMDDYY}_JRNL_{HHMM}
    Uses JRNL to distinguish from backtest trades (EPCH1-4).
    """

    # === Identification ===
    trade_id: str
    trade_date: date
    symbol: str
    direction: TradeDirection
    account: str = ""                     # Account ID — distinguishes SIM vs LIVE

    # === Trade Legs ===
    entry_leg: TradeLeg
    exit_leg: Optional[TradeLeg] = None

    # === Review Fields (populated later in review page — Sprint 3) ===
    zone_id: Optional[str] = None
    model: Optional[str] = None           # EPCH_01 through EPCH_04
    stop_price: Optional[float] = None    # Needed for R-multiple calc
    notes: Optional[str] = None

    # === Computed: Price Accessors ===

    @computed_field
    @property
    def entry_price(self) -> float:
        """VWAP entry price across all entry fills (including adds)."""
        return self.entry_leg.avg_price

    @computed_field
    @property
    def exit_price(self) -> Optional[float]:
        """VWAP exit price across all exit fills. None if trade still open."""
        return self.exit_leg.avg_price if self.exit_leg else None

    @computed_field
    @property
    def entry_time(self) -> Optional[time]:
        """Time of first entry fill."""
        return self.entry_leg.first_fill_time

    @computed_field
    @property
    def exit_time(self) -> Optional[time]:
        """Time of last exit fill."""
        return self.exit_leg.last_fill_time if self.exit_leg else None

    @computed_field
    @property
    def total_qty(self) -> int:
        """Total entry shares (the position size, including adds)."""
        return self.entry_leg.total_qty

    @computed_field
    @property
    def is_closed(self) -> bool:
        """True if trade has an exit leg."""
        return self.exit_leg is not None

    # === Computed: P&L ===

    @computed_field
    @property
    def pnl_dollars(self) -> Optional[float]:
        """Per-share P&L. Matches existing trades table convention."""
        if self.exit_price is None:
            return None
        if self.direction == TradeDirection.LONG:
            return self.exit_price - self.entry_price
        else:
            return self.entry_price - self.exit_price

    @computed_field
    @property
    def pnl_total(self) -> Optional[float]:
        """Total dollar P&L (per-share P&L * total entry qty)."""
        if self.pnl_dollars is None:
            return None
        return self.pnl_dollars * self.total_qty

    @computed_field
    @property
    def pnl_r(self) -> Optional[float]:
        """P&L in R-multiples. Requires stop_price to be set."""
        if self.pnl_dollars is None or self.stop_price is None:
            return None
        risk = abs(self.entry_price - self.stop_price)
        return self.pnl_dollars / risk if risk != 0 else None

    @computed_field
    @property
    def outcome(self) -> TradeOutcome:
        """Win/Loss/Breakeven classification."""
        if not self.is_closed or self.pnl_dollars is None:
            return TradeOutcome.OPEN
        if self.pnl_dollars > 0:
            return TradeOutcome.WIN
        elif self.pnl_dollars < 0:
            return TradeOutcome.LOSS
        return TradeOutcome.BREAKEVEN

    # === Computed: Duration ===

    @computed_field
    @property
    def duration_seconds(self) -> Optional[int]:
        """Trade duration from first entry fill to last exit fill."""
        if self.entry_time is None or self.exit_time is None:
            return None
        entry_dt = datetime.combine(self.trade_date, self.entry_time)
        exit_dt = datetime.combine(self.trade_date, self.exit_time)
        return int((exit_dt - entry_dt).total_seconds())

    @computed_field
    @property
    def duration_display(self) -> Optional[str]:
        """Human-readable duration string (e.g., '1m 50s')."""
        if self.duration_seconds is None:
            return None
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    # === Serialization ===

    def to_db_row(self, source_file: str = "") -> Dict:
        """
        Serialize Trade to flat dict for DB insert into journal_trades.
        Fills are ephemeral — only aggregated leg data persists.
        """
        return {
            "trade_id": self.trade_id,
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "account": self.account,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "entry_qty": self.entry_leg.total_qty,
            "entry_fills": self.entry_leg.fill_count,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time,
            "exit_qty": self.exit_leg.total_qty if self.exit_leg else None,
            "exit_fills": self.exit_leg.fill_count if self.exit_leg else None,
            "pnl_dollars": self.pnl_dollars,
            "pnl_total": self.pnl_total,
            "pnl_r": self.pnl_r,
            "outcome": self.outcome.value,
            "duration_seconds": self.duration_seconds,
            "zone_id": self.zone_id,
            "model": self.model,
            "stop_price": self.stop_price,
            "notes": self.notes,
            "source_file": source_file,
            "is_closed": self.is_closed,
        }

    @classmethod
    def from_db_row(cls, row: Dict) -> "Trade":
        """
        Reconstruct Trade from a journal_trades DB row.
        Creates synthetic TradeLeg objects without individual fills
        (fills are ephemeral and not stored in DB).
        """
        direction = TradeDirection(row["direction"])

        # Build synthetic entry leg (no individual fills — just the aggregate)
        entry_fill = Fill(
            time=row["entry_time"],
            symbol=row["symbol"],
            side=FillSide.SHORT_SELL if direction == TradeDirection.SHORT else FillSide.BUY,
            price=float(row["entry_price"]),
            qty=int(row["entry_qty"]),
        )
        entry_leg = TradeLeg(side=TradeSide.ENTRY, fills=[entry_fill])

        # Build synthetic exit leg if trade is closed
        exit_leg = None
        if row.get("exit_price") is not None and row.get("exit_time") is not None:
            exit_fill = Fill(
                time=row["exit_time"],
                symbol=row["symbol"],
                side=FillSide.BUY if direction == TradeDirection.SHORT else FillSide.SELL,
                price=float(row["exit_price"]),
                qty=int(row.get("exit_qty", row["entry_qty"])),
            )
            exit_leg = TradeLeg(side=TradeSide.EXIT, fills=[exit_fill])

        return cls(
            trade_id=row["trade_id"],
            trade_date=row["trade_date"],
            symbol=row["symbol"],
            direction=direction,
            account=row.get("account", ""),
            entry_leg=entry_leg,
            exit_leg=exit_leg,
            zone_id=row.get("zone_id"),
            model=row.get("model"),
            stop_price=float(row["stop_price"]) if row.get("stop_price") is not None else None,
            notes=row.get("notes"),
        )


# =============================================================================
# DailyTradeLog — All trades from one CSV session
# =============================================================================

class DailyTradeLog(BaseModel):
    """
    All trades from a single trading session (one CSV file).
    Contains parsed trades plus any errors encountered during processing.
    """
    trade_date: date
    source_file: str
    trades: List[Trade] = Field(default_factory=list)
    parse_errors: List[str] = Field(default_factory=list)

    @computed_field
    @property
    def trade_count(self) -> int:
        """Total number of trades in this session."""
        return len(self.trades)

    @computed_field
    @property
    def closed_count(self) -> int:
        """Number of fully closed trades."""
        return sum(1 for t in self.trades if t.is_closed)

    @computed_field
    @property
    def open_count(self) -> int:
        """Number of trades still open (should be 0 in practice)."""
        return sum(1 for t in self.trades if not t.is_closed)

    @computed_field
    @property
    def symbols_traded(self) -> List[str]:
        """Sorted list of unique symbols traded."""
        return sorted(set(t.symbol for t in self.trades))

    @computed_field
    @property
    def total_pnl(self) -> float:
        """Total P&L across all closed trades."""
        return sum(t.pnl_total or 0.0 for t in self.trades if t.is_closed)

    @computed_field
    @property
    def win_count(self) -> int:
        return sum(1 for t in self.trades if t.outcome == TradeOutcome.WIN)

    @computed_field
    @property
    def loss_count(self) -> int:
        return sum(1 for t in self.trades if t.outcome == TradeOutcome.LOSS)

    @computed_field
    @property
    def win_rate(self) -> Optional[float]:
        """Win rate as a decimal (0.0-1.0). None if no closed trades."""
        closed = self.closed_count
        return self.win_count / closed if closed > 0 else None
