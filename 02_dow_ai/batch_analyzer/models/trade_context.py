"""
Trade Context Model
Contains all data needed to generate a DOW AI prompt for a trade.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional, List, Dict, Any


@dataclass
class M1Bar:
    """Single M1 bar with indicators."""
    bar_time: time
    open: float
    high: float
    low: float
    close: float
    volume: int
    candle_range_pct: Optional[float] = None
    vol_delta: Optional[float] = None
    vol_roc: Optional[float] = None
    sma_spread: Optional[float] = None
    h1_structure: Optional[str] = None
    long_score: Optional[int] = None
    short_score: Optional[int] = None


@dataclass
class EntryIndicators:
    """Entry indicator snapshot for a trade."""
    # Health scores
    health_score: Optional[int] = None
    health_label: Optional[str] = None
    structure_score: Optional[int] = None
    volume_score: Optional[int] = None
    price_score: Optional[int] = None

    # Structure factors
    h4_structure: Optional[str] = None
    h4_structure_healthy: Optional[bool] = None
    h1_structure: Optional[str] = None
    h1_structure_healthy: Optional[bool] = None
    m15_structure: Optional[str] = None
    m15_structure_healthy: Optional[bool] = None
    m5_structure: Optional[str] = None
    m5_structure_healthy: Optional[bool] = None

    # Volume factors
    vol_roc: Optional[float] = None
    vol_roc_healthy: Optional[bool] = None
    vol_delta: Optional[float] = None
    vol_delta_healthy: Optional[bool] = None
    cvd_slope: Optional[float] = None
    cvd_slope_healthy: Optional[bool] = None

    # Price/SMA factors
    sma9: Optional[float] = None
    sma21: Optional[float] = None
    sma_spread: Optional[float] = None
    sma_alignment: Optional[str] = None
    sma_alignment_healthy: Optional[bool] = None
    sma_momentum_label: Optional[str] = None
    sma_momentum_healthy: Optional[bool] = None
    vwap: Optional[float] = None
    vwap_position: Optional[str] = None
    vwap_healthy: Optional[bool] = None

    @property
    def structure_healthy_count(self) -> int:
        """Count of healthy structure factors."""
        return sum([
            self.h4_structure_healthy or False,
            self.h1_structure_healthy or False,
            self.m15_structure_healthy or False,
            self.m5_structure_healthy or False,
        ])

    @property
    def volume_healthy_count(self) -> int:
        """Count of healthy volume factors."""
        return sum([
            self.vol_roc_healthy or False,
            self.vol_delta_healthy or False,
            self.cvd_slope_healthy or False,
        ])

    @property
    def price_healthy_count(self) -> int:
        """Count of healthy price/SMA factors."""
        return sum([
            self.sma_alignment_healthy or False,
            self.sma_momentum_healthy or False,
            self.vwap_healthy or False,
        ])

    @property
    def total_healthy_count(self) -> int:
        """Total count of healthy factors (0-10)."""
        return (
            self.structure_healthy_count +
            self.volume_healthy_count +
            self.price_healthy_count
        )


@dataclass
class TradeContext:
    """Complete context for a trade needed for DOW AI analysis."""
    # Trade identification
    trade_id: str
    ticker: str
    direction: str
    model: str
    zone_type: str

    # Trade details
    trade_date: date
    entry_time: time
    entry_price: float

    # Actual outcome (for accuracy tracking)
    is_winner: bool
    pnl_r: Optional[float] = None

    # Entry indicators
    indicators: Optional[EntryIndicators] = None

    # M1 ramp-up bars
    m1_bars: List[M1Bar] = field(default_factory=list)

    # AI context (edges, zone performance)
    ai_context: Optional[Dict[str, Any]] = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'TradeContext':
        """Create TradeContext from database row."""
        indicators = EntryIndicators(
            health_score=row.get('health_score'),
            health_label=row.get('health_label'),
            structure_score=row.get('structure_score'),
            volume_score=row.get('volume_score'),
            price_score=row.get('price_score'),
            h4_structure=row.get('h4_structure'),
            h4_structure_healthy=row.get('h4_structure_healthy'),
            h1_structure=row.get('h1_structure'),
            h1_structure_healthy=row.get('h1_structure_healthy'),
            m15_structure=row.get('m15_structure'),
            m15_structure_healthy=row.get('m15_structure_healthy'),
            m5_structure=row.get('m5_structure'),
            m5_structure_healthy=row.get('m5_structure_healthy'),
            vol_roc=float(row['vol_roc']) if row.get('vol_roc') else None,
            vol_roc_healthy=row.get('vol_roc_healthy'),
            vol_delta=float(row['vol_delta']) if row.get('vol_delta') else None,
            vol_delta_healthy=row.get('vol_delta_healthy'),
            cvd_slope=float(row['cvd_slope']) if row.get('cvd_slope') else None,
            cvd_slope_healthy=row.get('cvd_slope_healthy'),
            sma9=float(row['sma9']) if row.get('sma9') else None,
            sma21=float(row['sma21']) if row.get('sma21') else None,
            sma_spread=float(row['sma_spread']) if row.get('sma_spread') else None,
            sma_alignment=row.get('sma_alignment'),
            sma_alignment_healthy=row.get('sma_alignment_healthy'),
            sma_momentum_label=row.get('sma_momentum_label'),
            sma_momentum_healthy=row.get('sma_momentum_healthy'),
            vwap=float(row['vwap']) if row.get('vwap') else None,
            vwap_position=row.get('vwap_position'),
            vwap_healthy=row.get('vwap_healthy'),
        )

        return cls(
            trade_id=row['trade_id'],
            ticker=row['ticker'],
            direction=row['direction'],
            model=row['model'],
            zone_type=row['zone_type'],
            trade_date=row['date'],
            entry_time=row['entry_time'],
            entry_price=float(row['entry_price']),
            is_winner=row['is_winner'],
            pnl_r=float(row['pnl_r']) if row.get('pnl_r') else None,
            indicators=indicators,
        )
