"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: BACKTEST RUNNER v4.0
Entry Collector - Entry Detection Only (S15 Bars)
XIII Trading LLC
================================================================================

Collects entry signals from EPCH1-4 models on S15 bars and produces
EntryRecord objects for export to trades_2 table.

No exit management, no position tracking, no P&L calculation.
Those are handled by secondary processors downstream.

TRADE_ID FORMAT: {ticker}_{MMDDYY}_{model}_{HHMM}
================================================================================
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import VERBOSE
from engine.entry_models import EntrySignal, EntryDetector


@dataclass
class EntryRecord:
    """A detected entry for export to trades_2 table."""
    trade_id: str
    date: str
    ticker: str
    model: str          # "EPCH1", "EPCH2", "EPCH3", "EPCH4"
    zone_type: str      # "PRIMARY" or "SECONDARY"
    direction: str      # "LONG" or "SHORT"
    zone_high: float
    zone_low: float
    entry_price: float
    entry_time: datetime


def generate_trade_id(ticker: str, entry_time: datetime, model_name: str) -> str:
    """Generate formatted trade_id string."""
    date_str = entry_time.strftime('%m%d%y')
    time_str = entry_time.strftime('%H%M')
    return f"{ticker}_{date_str}_{model_name}_{time_str}"


class TradeSimulator:
    """
    Detects and collects entry signals from S15 bars.
    """

    def __init__(self, ticker: str, trade_date: str):
        self.ticker = ticker
        self.trade_date = trade_date

        self.entries: List[EntryRecord] = []

        self.primary_zone: Optional[dict] = None
        self.secondary_zone: Optional[dict] = None

        self.entry_detector = EntryDetector()

    def set_zones(self, primary_zone: Optional[dict] = None,
                  secondary_zone: Optional[dict] = None):
        """Set zone data for entry detection"""
        self.primary_zone = primary_zone
        self.secondary_zone = secondary_zone

    def process_bar_entries_only(self, bar_idx: int, bar_time: datetime,
                                 bar_open: float, bar_high: float,
                                 bar_low: float, bar_close: float) -> List[EntryRecord]:
        """Process an S15 bar for entry detection. Returns new entries found."""
        new_entries = []

        signals = self.entry_detector.check_all_entries(
            bar_idx, bar_time, bar_open, bar_high, bar_low, bar_close,
            self.primary_zone, self.secondary_zone
        )

        for signal in signals:
            trade_id = generate_trade_id(self.ticker, signal.entry_time, signal.model_name)

            record = EntryRecord(
                trade_id=trade_id,
                date=self.trade_date,
                ticker=self.ticker,
                model=signal.model_name,
                zone_type=signal.zone_type,
                direction=signal.direction,
                zone_high=signal.zone_high,
                zone_low=signal.zone_low,
                entry_price=signal.entry_price,
                entry_time=signal.entry_time
            )

            self.entries.append(record)
            new_entries.append(record)

            if VERBOSE:
                print(f"  [{bar_time.strftime('%H:%M:%S')}] ENTRY {signal.direction} {signal.model_name} "
                      f"@ ${signal.entry_price:.2f}")

        self.entry_detector.update_prior_bar(bar_open, bar_high, bar_low, bar_close)

        return new_entries

    def get_entries(self) -> List[EntryRecord]:
        """Get all detected entries."""
        return self.entries

    def reset(self):
        """Reset simulator state"""
        self.entries.clear()
        self.entry_detector.reset()
