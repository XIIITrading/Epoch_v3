"""
DOW AI Data Fetcher - Retrieves supplemental data from Supabase for prompt generation.

Fetches HVN POCs, Camarilla pivots, bar data, and market structure
to provide full context for Claude Desktop analysis.
"""

from datetime import date, datetime, time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BarDataContext:
    """Bar data context including ATR and Camarilla pivots."""
    ticker: str
    trade_date: date
    price: Optional[float] = None

    # ATR values
    m5_atr: Optional[float] = None
    m15_atr: Optional[float] = None
    h1_atr: Optional[float] = None
    d1_atr: Optional[float] = None

    # Daily Camarilla
    d1_cam_s6: Optional[float] = None
    d1_cam_s4: Optional[float] = None
    d1_cam_s3: Optional[float] = None
    d1_cam_r3: Optional[float] = None
    d1_cam_r4: Optional[float] = None
    d1_cam_r6: Optional[float] = None

    # Weekly Camarilla
    w1_cam_s3: Optional[float] = None
    w1_cam_r3: Optional[float] = None

    # Options levels
    options_levels: List[float] = None

    def __post_init__(self):
        if self.options_levels is None:
            self.options_levels = []


@dataclass
class HVNPOCContext:
    """HVN POC levels for the ticker."""
    ticker: str
    trade_date: date
    epoch_start_date: Optional[date] = None
    pocs: List[float] = None  # poc_1 through poc_10

    def __post_init__(self):
        if self.pocs is None:
            self.pocs = []


@dataclass
class MarketStructureContext:
    """Multi-timeframe market structure."""
    ticker: str
    trade_date: date

    # Timeframe directions
    d1_direction: Optional[str] = None
    h4_direction: Optional[str] = None
    h1_direction: Optional[str] = None
    m15_direction: Optional[str] = None
    composite_direction: Optional[str] = None

    # Strong/Weak levels
    d1_strong: Optional[float] = None
    d1_weak: Optional[float] = None
    h4_strong: Optional[float] = None
    h4_weak: Optional[float] = None
    h1_strong: Optional[float] = None
    h1_weak: Optional[float] = None
    m15_strong: Optional[float] = None
    m15_weak: Optional[float] = None


@dataclass
class SetupContext:
    """Primary/Secondary setup information."""
    ticker: str
    trade_date: date
    setup_type: str  # PRIMARY or SECONDARY
    direction: Optional[str] = None
    zone_id: Optional[str] = None
    hvn_poc: Optional[float] = None
    zone_high: Optional[float] = None
    zone_low: Optional[float] = None
    target_id: Optional[str] = None
    target_price: Optional[float] = None
    risk_reward: Optional[float] = None


class DOWAIDataFetcher:
    """
    Fetches supplemental data from Supabase for DOW AI prompt generation.

    Data sources:
    - bar_data: ATR, Camarilla pivots, options levels
    - hvn_pocs: 10 ranked POC levels
    - market_structure: Multi-timeframe direction analysis
    - setups: Primary/Secondary zone setups
    """

    def __init__(self, supabase_client):
        """
        Initialize with existing Supabase client.

        Args:
            supabase_client: SupabaseClient instance from training module
        """
        self.client = supabase_client

    def fetch_bar_data(self, ticker: str, trade_date: date) -> Optional[BarDataContext]:
        """
        Fetch bar data including ATR and Camarilla pivots.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            BarDataContext or None if not found
        """
        self.client._ensure_connected()

        # Need to find the ticker_id (t1-t10) for this ticker on this date
        query = """
            SELECT
                ticker, price,
                m5_atr, m15_atr, h1_atr, d1_atr,
                d1_cam_s6, d1_cam_s4, d1_cam_s3,
                d1_cam_r3, d1_cam_r4, d1_cam_r6,
                w1_cam_s3, w1_cam_r3,
                op_01, op_02, op_03, op_04, op_05,
                op_06, op_07, op_08, op_09, op_10
            FROM bar_data
            WHERE date = %s AND ticker = %s
            LIMIT 1
        """

        try:
            from psycopg2.extras import RealDictCursor
            with self.client.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date, ticker.upper()))
                row = cur.fetchone()

                if not row:
                    logger.warning(f"No bar_data found for {ticker} on {trade_date}")
                    return None

                # Extract options levels
                options = []
                for i in range(1, 11):
                    op = row.get(f'op_{i:02d}')
                    if op is not None:
                        options.append(float(op))

                return BarDataContext(
                    ticker=ticker,
                    trade_date=trade_date,
                    price=row.get('price'),
                    m5_atr=row.get('m5_atr'),
                    m15_atr=row.get('m15_atr'),
                    h1_atr=row.get('h1_atr'),
                    d1_atr=row.get('d1_atr'),
                    d1_cam_s6=row.get('d1_cam_s6'),
                    d1_cam_s4=row.get('d1_cam_s4'),
                    d1_cam_s3=row.get('d1_cam_s3'),
                    d1_cam_r3=row.get('d1_cam_r3'),
                    d1_cam_r4=row.get('d1_cam_r4'),
                    d1_cam_r6=row.get('d1_cam_r6'),
                    w1_cam_s3=row.get('w1_cam_s3'),
                    w1_cam_r3=row.get('w1_cam_r3'),
                    options_levels=options
                )

        except Exception as e:
            logger.error(f"Error fetching bar_data: {e}")
            self.client.conn.rollback()
            return None

    def fetch_hvn_pocs(self, ticker: str, trade_date: date) -> Optional[HVNPOCContext]:
        """
        Fetch HVN POC levels (10 ranked).

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            HVNPOCContext or None if not found
        """
        self.client._ensure_connected()

        query = """
            SELECT
                ticker, epoch_start_date,
                poc_1, poc_2, poc_3, poc_4, poc_5,
                poc_6, poc_7, poc_8, poc_9, poc_10
            FROM hvn_pocs
            WHERE date = %s AND ticker = %s
            LIMIT 1
        """

        try:
            from psycopg2.extras import RealDictCursor
            with self.client.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date, ticker.upper()))
                row = cur.fetchone()

                if not row:
                    logger.warning(f"No hvn_pocs found for {ticker} on {trade_date}")
                    return None

                # Extract POC levels
                pocs = []
                for i in range(1, 11):
                    poc = row.get(f'poc_{i}')
                    if poc is not None:
                        pocs.append(float(poc))

                return HVNPOCContext(
                    ticker=ticker,
                    trade_date=trade_date,
                    epoch_start_date=row.get('epoch_start_date'),
                    pocs=pocs
                )

        except Exception as e:
            logger.error(f"Error fetching hvn_pocs: {e}")
            self.client.conn.rollback()
            return None

    def fetch_market_structure(self, ticker: str, trade_date: date) -> Optional[MarketStructureContext]:
        """
        Fetch multi-timeframe market structure.

        Args:
            ticker: Stock symbol
            trade_date: Trading date

        Returns:
            MarketStructureContext or None if not found
        """
        self.client._ensure_connected()

        query = """
            SELECT
                ticker,
                d1_direction, h4_direction, h1_direction, m15_direction,
                composite_direction,
                d1_strong, d1_weak,
                h4_strong, h4_weak,
                h1_strong, h1_weak,
                m15_strong, m15_weak
            FROM market_structure
            WHERE date = %s AND ticker = %s
            LIMIT 1
        """

        try:
            from psycopg2.extras import RealDictCursor
            with self.client.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date, ticker.upper()))
                row = cur.fetchone()

                if not row:
                    logger.warning(f"No market_structure found for {ticker} on {trade_date}")
                    return None

                return MarketStructureContext(
                    ticker=ticker,
                    trade_date=trade_date,
                    d1_direction=row.get('d1_direction'),
                    h4_direction=row.get('h4_direction'),
                    h1_direction=row.get('h1_direction'),
                    m15_direction=row.get('m15_direction'),
                    composite_direction=row.get('composite_direction'),
                    d1_strong=row.get('d1_strong'),
                    d1_weak=row.get('d1_weak'),
                    h4_strong=row.get('h4_strong'),
                    h4_weak=row.get('h4_weak'),
                    h1_strong=row.get('h1_strong'),
                    h1_weak=row.get('h1_weak'),
                    m15_strong=row.get('m15_strong'),
                    m15_weak=row.get('m15_weak')
                )

        except Exception as e:
            logger.error(f"Error fetching market_structure: {e}")
            self.client.conn.rollback()
            return None

    def fetch_setup(self, ticker: str, trade_date: date, zone_type: str) -> Optional[SetupContext]:
        """
        Fetch setup information for a zone type.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            zone_type: 'PRIMARY' or 'SECONDARY'

        Returns:
            SetupContext or None if not found
        """
        self.client._ensure_connected()

        query = """
            SELECT
                ticker, setup_type, direction,
                zone_id, hvn_poc, zone_high, zone_low,
                target_id, target_price, risk_reward
            FROM setups
            WHERE date = %s AND ticker = %s AND setup_type = %s
            LIMIT 1
        """

        try:
            from psycopg2.extras import RealDictCursor
            with self.client.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (trade_date, ticker.upper(), zone_type.upper()))
                row = cur.fetchone()

                if not row:
                    logger.warning(f"No setup found for {ticker} {zone_type} on {trade_date}")
                    return None

                return SetupContext(
                    ticker=ticker,
                    trade_date=trade_date,
                    setup_type=row.get('setup_type'),
                    direction=row.get('direction'),
                    zone_id=row.get('zone_id'),
                    hvn_poc=row.get('hvn_poc'),
                    zone_high=row.get('zone_high'),
                    zone_low=row.get('zone_low'),
                    target_id=row.get('target_id'),
                    target_price=row.get('target_price'),
                    risk_reward=row.get('risk_reward')
                )

        except Exception as e:
            logger.error(f"Error fetching setup: {e}")
            self.client.conn.rollback()
            return None

    def fetch_all_context(
        self,
        ticker: str,
        trade_date: date,
        zone_type: str = 'PRIMARY'
    ) -> Dict[str, Any]:
        """
        Fetch all context data for a trade.

        Args:
            ticker: Stock symbol
            trade_date: Trading date
            zone_type: 'PRIMARY' or 'SECONDARY'

        Returns:
            Dict with bar_data, hvn_pocs, market_structure, setup
            Values are None if data not available
        """
        return {
            'bar_data': self.fetch_bar_data(ticker, trade_date),
            'hvn_pocs': self.fetch_hvn_pocs(ticker, trade_date),
            'market_structure': self.fetch_market_structure(ticker, trade_date),
            'setup': self.fetch_setup(ticker, trade_date, zone_type),
        }
