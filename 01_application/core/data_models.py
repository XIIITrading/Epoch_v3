"""
Pydantic data models for the Epoch Analysis Tool.
These replace the Excel cell structures with typed Python objects.
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class Direction(str, Enum):
    """Market direction enumeration."""
    BULL_PLUS = "Bull+"
    BULL = "Bull"
    NEUTRAL = "Neutral"
    BEAR = "Bear"
    BEAR_PLUS = "Bear+"
    ERROR = "ERROR"


class Rank(str, Enum):
    """Zone rank enumeration (L1=worst, L5=best)."""
    L5 = "L5"
    L4 = "L4"
    L3 = "L3"
    L2 = "L2"
    L1 = "L1"


class Tier(str, Enum):
    """Zone tier enumeration (T3=best, T1=worst)."""
    T3 = "T3"  # High Quality (L4, L5)
    T2 = "T2"  # Medium Quality (L3)
    T1 = "T1"  # Lower Quality (L1, L2)


class AnchorPreset(str, Enum):
    """Anchor date preset options."""
    CUSTOM = "custom"
    PRIOR_DAY = "prior_day"
    PRIOR_WEEK = "prior_week"
    PRIOR_MONTH = "prior_month"
    YTD = "ytd"


# =============================================================================
# INPUT MODELS
# =============================================================================

class TickerInput(BaseModel):
    """Input for a single ticker analysis."""
    ticker: str
    analysis_date: date
    anchor_date: date  # Epoch start date for HVN calculation
    price: Optional[float] = None

    @computed_field
    @property
    def ticker_id(self) -> str:
        """Generate ticker ID in format TICKER_MMDDYY."""
        return f"{self.ticker}_{self.analysis_date.strftime('%m%d%y')}"


# =============================================================================
# MARKET STRUCTURE MODELS
# =============================================================================

class TimeframeStructure(BaseModel):
    """Market structure for a single timeframe."""
    direction: Direction = Direction.NEUTRAL
    strong: Optional[float] = None
    weak: Optional[float] = None


class MarketStructure(BaseModel):
    """Complete market structure analysis for a ticker."""
    ticker: str
    datetime: datetime
    price: float

    # Timeframe structures
    d1: TimeframeStructure = Field(default_factory=TimeframeStructure)
    h4: TimeframeStructure = Field(default_factory=TimeframeStructure)
    h1: TimeframeStructure = Field(default_factory=TimeframeStructure)
    m15: TimeframeStructure = Field(default_factory=TimeframeStructure)

    # Composite direction
    composite: Direction = Direction.NEUTRAL

    def calculate_composite(self) -> Direction:
        """
        Calculate composite direction from all timeframes.

        Weights: D1=1.5, H4=1.5, H1=1.0, M15=0.5
        """
        weights = {'d1': 1.5, 'h4': 1.5, 'h1': 1.0, 'm15': 0.5}
        score = 0.0

        for tf, weight in weights.items():
            tf_struct = getattr(self, tf)
            if tf_struct.direction in [Direction.BULL, Direction.BULL_PLUS]:
                score += weight
            elif tf_struct.direction in [Direction.BEAR, Direction.BEAR_PLUS]:
                score -= weight

        max_score = sum(weights.values())  # 4.5

        if score >= 3.5:
            return Direction.BULL_PLUS
        elif score > 0:
            return Direction.BULL
        elif score <= -3.5:
            return Direction.BEAR_PLUS
        elif score < 0:
            return Direction.BEAR
        else:
            return Direction.NEUTRAL


# =============================================================================
# BAR DATA MODELS
# =============================================================================

class OHLCData(BaseModel):
    """OHLC data for a period."""
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None

    def is_complete(self) -> bool:
        """Check if all OHLC values are present."""
        return all([
            self.open is not None,
            self.high is not None,
            self.low is not None,
            self.close is not None
        ])


class CamarillaLevels(BaseModel):
    """Camarilla pivot levels for a timeframe."""
    s6: Optional[float] = None
    s4: Optional[float] = None
    s3: Optional[float] = None
    r3: Optional[float] = None
    r4: Optional[float] = None
    r6: Optional[float] = None

    def to_dict(self, prefix: str) -> Dict[str, float]:
        """Convert to dictionary with prefixed keys."""
        result = {}
        if self.s6 is not None:
            result[f'{prefix}_s6'] = self.s6
        if self.s4 is not None:
            result[f'{prefix}_s4'] = self.s4
        if self.s3 is not None:
            result[f'{prefix}_s3'] = self.s3
        if self.r3 is not None:
            result[f'{prefix}_r3'] = self.r3
        if self.r4 is not None:
            result[f'{prefix}_r4'] = self.r4
        if self.r6 is not None:
            result[f'{prefix}_r6'] = self.r6
        return result


class BarData(BaseModel):
    """Complete bar data for a ticker (replaces bar_data sheet)."""
    ticker: str
    ticker_id: str
    analysis_date: date

    # Current price
    price: float

    # Monthly OHLC
    m1_current: OHLCData = Field(default_factory=OHLCData)
    m1_prior: OHLCData = Field(default_factory=OHLCData)

    # Weekly OHLC
    w1_current: OHLCData = Field(default_factory=OHLCData)
    w1_prior: OHLCData = Field(default_factory=OHLCData)

    # Daily OHLC
    d1_current: OHLCData = Field(default_factory=OHLCData)
    d1_prior: OHLCData = Field(default_factory=OHLCData)

    # Overnight
    overnight_high: Optional[float] = None
    overnight_low: Optional[float] = None

    # Options levels (top 10 by OI)
    options_levels: List[float] = Field(default_factory=list)

    # ATR values
    m1_atr: Optional[float] = None
    m5_atr: Optional[float] = None
    m15_atr: Optional[float] = None
    h1_atr: Optional[float] = None
    d1_atr: Optional[float] = None

    # Camarilla levels
    camarilla_daily: CamarillaLevels = Field(default_factory=CamarillaLevels)
    camarilla_weekly: CamarillaLevels = Field(default_factory=CamarillaLevels)
    camarilla_monthly: CamarillaLevels = Field(default_factory=CamarillaLevels)

    # Market structure levels
    d1_strong: Optional[float] = None
    d1_weak: Optional[float] = None
    h4_strong: Optional[float] = None
    h4_weak: Optional[float] = None
    h1_strong: Optional[float] = None
    h1_weak: Optional[float] = None
    m15_strong: Optional[float] = None
    m15_weak: Optional[float] = None

    def get_all_levels(self) -> Dict[str, float]:
        """
        Get all technical levels as a flat dictionary.
        Used for confluence zone calculation.
        """
        levels = {}

        # Monthly OHLC
        if self.m1_current.open is not None:
            levels['m1_01'] = self.m1_current.open
        if self.m1_current.high is not None:
            levels['m1_02'] = self.m1_current.high
        if self.m1_current.low is not None:
            levels['m1_03'] = self.m1_current.low
        if self.m1_current.close is not None:
            levels['m1_04'] = self.m1_current.close
        if self.m1_prior.open is not None:
            levels['m1_po'] = self.m1_prior.open
        if self.m1_prior.high is not None:
            levels['m1_ph'] = self.m1_prior.high
        if self.m1_prior.low is not None:
            levels['m1_pl'] = self.m1_prior.low
        if self.m1_prior.close is not None:
            levels['m1_pc'] = self.m1_prior.close

        # Weekly OHLC
        if self.w1_current.open is not None:
            levels['w1_01'] = self.w1_current.open
        if self.w1_current.high is not None:
            levels['w1_02'] = self.w1_current.high
        if self.w1_current.low is not None:
            levels['w1_03'] = self.w1_current.low
        if self.w1_current.close is not None:
            levels['w1_04'] = self.w1_current.close
        if self.w1_prior.open is not None:
            levels['w1_po'] = self.w1_prior.open
        if self.w1_prior.high is not None:
            levels['w1_ph'] = self.w1_prior.high
        if self.w1_prior.low is not None:
            levels['w1_pl'] = self.w1_prior.low
        if self.w1_prior.close is not None:
            levels['w1_pc'] = self.w1_prior.close

        # Daily OHLC
        if self.d1_current.open is not None:
            levels['d1_01'] = self.d1_current.open
        if self.d1_current.high is not None:
            levels['d1_02'] = self.d1_current.high
        if self.d1_current.low is not None:
            levels['d1_03'] = self.d1_current.low
        if self.d1_current.close is not None:
            levels['d1_04'] = self.d1_current.close
        if self.d1_prior.open is not None:
            levels['d1_po'] = self.d1_prior.open
        if self.d1_prior.high is not None:
            levels['d1_ph'] = self.d1_prior.high
        if self.d1_prior.low is not None:
            levels['d1_pl'] = self.d1_prior.low
        if self.d1_prior.close is not None:
            levels['d1_pc'] = self.d1_prior.close

        # Overnight
        if self.overnight_high is not None:
            levels['d1_onh'] = self.overnight_high
        if self.overnight_low is not None:
            levels['d1_onl'] = self.overnight_low

        # Options
        for i, level in enumerate(self.options_levels, 1):
            if level is not None:
                levels[f'op_{i:02d}'] = level

        # Camarilla
        levels.update(self.camarilla_daily.to_dict('d1'))
        levels.update(self.camarilla_weekly.to_dict('w1'))
        levels.update(self.camarilla_monthly.to_dict('m1'))

        # Market structure
        if self.d1_strong is not None:
            levels['d1_s'] = self.d1_strong
        if self.d1_weak is not None:
            levels['d1_w'] = self.d1_weak
        if self.h4_strong is not None:
            levels['h4_s'] = self.h4_strong
        if self.h4_weak is not None:
            levels['h4_w'] = self.h4_weak
        if self.h1_strong is not None:
            levels['h1_s'] = self.h1_strong
        if self.h1_weak is not None:
            levels['h1_w'] = self.h1_weak
        if self.m15_strong is not None:
            levels['m15_s'] = self.m15_strong
        if self.m15_weak is not None:
            levels['m15_w'] = self.m15_weak

        return levels


# =============================================================================
# HVN MODELS
# =============================================================================

class POCResult(BaseModel):
    """Single Point of Control result."""
    price: float
    volume: float
    rank: int  # 1 = highest volume


class HVNResult(BaseModel):
    """HVN POC calculation result."""
    ticker: str
    start_date: date
    end_date: date
    bars_analyzed: int = 0
    total_volume: float = 0.0
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    atr_used: Optional[float] = None

    # 10 POCs ranked by volume (poc1 = highest volume)
    pocs: List[POCResult] = Field(default_factory=list)

    def get_poc(self, rank: int) -> Optional[float]:
        """Get POC price by rank (1-10)."""
        for poc in self.pocs:
            if poc.rank == rank:
                return poc.price
        return None

    def get_poc_prices(self) -> List[float]:
        """Get all POC prices in rank order."""
        sorted_pocs = sorted(self.pocs, key=lambda x: x.rank)
        return [poc.price for poc in sorted_pocs]

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary with hvn_poc1 through hvn_poc10 keys."""
        result = {}
        for poc in self.pocs:
            result[f'hvn_poc{poc.rank}'] = poc.price
        return result


# =============================================================================
# ZONE MODELS
# =============================================================================

class RawZone(BaseModel):
    """A single confluence zone before filtering."""
    ticker: str
    ticker_id: str
    analysis_date: date
    price: float
    direction: Direction

    zone_id: str
    poc_rank: int  # 1-10 (which HVN POC this zone is based on)
    hvn_poc: float
    zone_high: float
    zone_low: float

    overlaps: int = 0
    score: float = 0.0
    rank: Rank = Rank.L1
    confluences: List[str] = Field(default_factory=list)

    @computed_field
    @property
    def confluences_str(self) -> str:
        """Get confluences as comma-separated string."""
        return ", ".join(self.confluences)

    @computed_field
    @property
    def zone_mid(self) -> float:
        """Get zone midpoint."""
        return (self.zone_high + self.zone_low) / 2


class FilteredZone(RawZone):
    """A zone after filtering with tier and setup flags."""
    tier: Tier = Tier.T1

    # Distance from current price
    atr_distance: Optional[float] = None
    proximity_group: Optional[str] = None

    # Setup flags
    is_bull_poc: bool = False
    is_bear_poc: bool = False

    # Target info (populated in setup analysis)
    bull_target: Optional[float] = None
    bear_target: Optional[float] = None


# =============================================================================
# SETUP MODELS
# =============================================================================

class Setup(BaseModel):
    """A trading setup (primary or secondary)."""
    ticker: str
    ticker_id: str
    direction: Direction
    setup_type: str = "Primary"  # "Primary" or "Secondary"

    zone_id: str
    hvn_poc: float
    zone_high: float
    zone_low: float
    tier: Tier

    # Target information
    target_id: Optional[str] = None
    target: Optional[float] = None
    risk_reward: Optional[float] = None

    @computed_field
    @property
    def setup_string(self) -> str:
        """
        Generate setup string for display.

        Note: For PineScript export, use the pinescript_values property
        or combine primary+secondary using generate_pinescript_6/16.
        """
        target_str = f"{self.target:.2f}" if self.target else "0"
        return f"{self.zone_high:.2f},{self.zone_low:.2f},{target_str}"

    @property
    def pinescript_values(self) -> List[float]:
        """Get values for PineScript export: [zone_high, zone_low, target]."""
        return [
            self.zone_high,
            self.zone_low,
            self.target if self.target else 0.0
        ]


def generate_pinescript_6(primary: Optional[Setup], secondary: Optional[Setup]) -> str:
    """
    Generate PineScript_6 string from primary and secondary setups.

    Format: pri_high,pri_low,pri_target,sec_high,sec_low,sec_target

    Args:
        primary: Primary setup (or None)
        secondary: Secondary setup (or None)

    Returns:
        Comma-separated string of 6 values
    """
    pri_high = primary.zone_high if primary else 0.0
    pri_low = primary.zone_low if primary else 0.0
    pri_target = primary.target if primary and primary.target else 0.0

    sec_high = secondary.zone_high if secondary else 0.0
    sec_low = secondary.zone_low if secondary else 0.0
    sec_target = secondary.target if secondary and secondary.target else 0.0

    values = [pri_high, pri_low, pri_target, sec_high, sec_low, sec_target]
    return ",".join(f"{v:.2f}" if v != 0 else "0" for v in values)


def generate_pinescript_16(primary: Optional[Setup], secondary: Optional[Setup],
                           pocs: List[float]) -> str:
    """
    Generate PineScript_16 string from setups and POCs.

    Format: pri_high,pri_low,pri_target,sec_high,sec_low,sec_target,poc1,...,poc10

    Args:
        primary: Primary setup (or None)
        secondary: Secondary setup (or None)
        pocs: List of 10 POC prices (can be shorter, will be padded with 0s)

    Returns:
        Comma-separated string of 16 values
    """
    pine_6 = generate_pinescript_6(primary, secondary)

    # Ensure we have exactly 10 POCs
    poc_values = list(pocs[:10]) if pocs else []
    while len(poc_values) < 10:
        poc_values.append(0.0)

    poc_str = ",".join(f"{v:.2f}" if v != 0 else "0" for v in poc_values)
    return f"{pine_6},{poc_str}"


# =============================================================================
# ANALYSIS RESULT MODELS
# =============================================================================

class AnalysisResult(BaseModel):
    """Complete analysis result for a single ticker and anchor date."""
    ticker_input: TickerInput
    anchor_preset: AnchorPreset = AnchorPreset.CUSTOM

    # Analysis components
    market_structure: Optional[MarketStructure] = None
    bar_data: Optional[BarData] = None
    hvn_result: Optional[HVNResult] = None
    raw_zones: List[RawZone] = Field(default_factory=list)
    filtered_zones: List[FilteredZone] = Field(default_factory=list)

    # Setups
    primary_setup: Optional[Setup] = None
    secondary_setup: Optional[Setup] = None

    # Metadata
    calculation_time_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)

    def is_successful(self) -> bool:
        """Check if analysis completed successfully."""
        return len(self.errors) == 0 and self.bar_data is not None


class BatchAnalysisResult(BaseModel):
    """Results for a batch of tickers across multiple anchor dates."""
    analysis_date: date
    anchor_results: Dict[str, List[AnalysisResult]] = Field(default_factory=dict)
    # Key: anchor_preset (e.g., "custom", "prior_day")
    # Value: List of AnalysisResult for each ticker

    total_tickers: int = 0
    successful_tickers: int = 0
    total_time_seconds: Optional[float] = None


# =============================================================================
# SCANNER MODELS
# =============================================================================

class ScanResult(BaseModel):
    """Market scanner result row."""
    rank: int
    ticker: str
    ticker_id: str
    price: float
    gap_percent: float

    overnight_volume: int = 0
    prior_overnight_volume: int = 0
    relative_overnight_volume: float = 0.0
    relative_volume: float = 0.0

    short_interest: Optional[float] = None
    days_to_cover: Optional[float] = None

    ranking_score: float = 0.0
    atr: float = 0.0
    prior_close: float = 0.0

    scan_date: date
    scan_time: str = ""
