"""
DOW AI - Pydantic Data Models
Epoch Trading System v1 - XIII Trading LLC

Structured data models for type safety throughout the application.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime


class BarData(BaseModel):
    """Single OHLCV bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketStructureResult(BaseModel):
    """Market structure calculation result for a single timeframe."""
    timeframe: str
    direction: Literal['BULL', 'BEAR', 'NEUTRAL']
    strong_level: Optional[float] = None
    weak_level: Optional[float] = None
    last_break: Optional[Literal['BOS', 'ChoCH']] = None
    last_break_price: Optional[float] = None


class VolumeAnalysis(BaseModel):
    """Volume analysis results."""
    delta_5bar: float
    delta_signal: Literal['Bullish', 'Bearish', 'Neutral']
    roc_percent: float
    roc_signal: Literal['Above Avg', 'Below Avg', 'Average']
    cvd_trend: Literal['Rising', 'Falling', 'Flat']
    cvd_values: List[float] = Field(default_factory=list)


class CandlestickPattern(BaseModel):
    """Detected candlestick pattern."""
    timeframe: str
    pattern: str
    price: float
    bars_ago: int
    direction: Literal['bullish', 'bearish', 'neutral']


class ZoneContext(BaseModel):
    """Zone information from Excel."""
    zone_id: str
    rank: str
    zone_high: float
    zone_low: float
    hvn_poc: float
    score: float
    confluences: str
    tier: Optional[str] = None
    target: Optional[float] = None
    target_id: Optional[str] = None
    r_r: Optional[float] = None
    direction: Optional[str] = None


class CamarillaLevels(BaseModel):
    """Camarilla pivot levels."""
    # Daily
    d1_s6: Optional[float] = None
    d1_s4: Optional[float] = None
    d1_s3: Optional[float] = None
    d1_r3: Optional[float] = None
    d1_r4: Optional[float] = None
    d1_r6: Optional[float] = None
    # Weekly
    w1_s6: Optional[float] = None
    w1_s4: Optional[float] = None
    w1_s3: Optional[float] = None
    w1_r3: Optional[float] = None
    w1_r4: Optional[float] = None
    w1_r6: Optional[float] = None
    # Monthly
    m1_s6: Optional[float] = None
    m1_s4: Optional[float] = None
    m1_s3: Optional[float] = None
    m1_r3: Optional[float] = None
    m1_r4: Optional[float] = None
    m1_r6: Optional[float] = None


class AnalysisRequest(BaseModel):
    """Request for entry/exit analysis."""
    ticker: str
    mode: Literal['entry', 'exit']
    direction: Literal['long', 'short', 'sell', 'cover']
    model: str
    analysis_datetime: Optional[datetime] = None  # None = live


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    request: AnalysisRequest
    current_price: float
    zone_context: Optional[ZoneContext] = None
    market_structure: Dict[str, MarketStructureResult] = Field(default_factory=dict)
    volume_analysis: Optional[VolumeAnalysis] = None
    patterns: Dict[str, List[CandlestickPattern]] = Field(default_factory=dict)
    atr: Optional[float] = None
    hvn_pocs: List[float] = Field(default_factory=list)
    camarilla: Optional[CamarillaLevels] = None
    claude_response: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    prompt: str = ""  # For debugging
    error: Optional[str] = None
