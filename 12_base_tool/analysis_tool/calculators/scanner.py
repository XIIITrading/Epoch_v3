"""
Two-Phase Market Scanner - Ported from 01_market_scanner.

This module provides stock scanning functionality with:
- Phase 1: Hard filters (ATR, price, gap)
- Phase 2: Ranking by multiple metrics
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np

from data.polygon_client import get_polygon_client, PolygonClient

logger = logging.getLogger(__name__)


@dataclass
class FilterPhase:
    """Hard filters that remove tickers from consideration."""
    min_atr: float = 2.00      # $2.00 minimum ATR
    min_price: float = 10.00   # $10 minimum price
    min_gap_percent: float = 2.0  # 2% minimum gap (absolute value)


@dataclass
class RankingWeights:
    """Weights for ranking metrics (all set to 1 initially)."""
    overnight_volume: float = 1.0
    relative_overnight_volume: float = 1.0
    relative_volume: float = 1.0
    gap_magnitude: float = 1.0
    short_interest: float = 1.0


@dataclass
class ScanResult:
    """Result from a single ticker scan."""
    rank: int
    ticker: str
    ticker_id: str
    current_price: float
    prior_close: float
    gap_percent: float
    atr: float
    current_overnight_volume: int
    prior_overnight_volume: int
    relative_overnight_volume: float
    relative_volume: float
    ranking_score: float
    scan_date: date
    scan_time: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame."""
        return {
            'rank': self.rank,
            'ticker': self.ticker,
            'ticker_id': self.ticker_id,
            'current_price': self.current_price,
            'prior_close': self.prior_close,
            'gap_percent': self.gap_percent,
            'atr': self.atr,
            'current_overnight_volume': self.current_overnight_volume,
            'prior_overnight_volume': self.prior_overnight_volume,
            'relative_overnight_volume': self.relative_overnight_volume,
            'relative_volume': self.relative_volume,
            'ranking_score': self.ranking_score,
            'scan_date': self.scan_date,
            'scan_time': self.scan_time,
        }


class OvernightVolumeFetcher:
    """Fetches and calculates overnight volume metrics."""

    def __init__(self, polygon_client: PolygonClient):
        self.client = polygon_client

    def fetch_overnight_volumes(self, ticker: str, scan_date: datetime) -> Dict:
        """
        Fetch overnight volumes for current and prior day.

        Time windows (all in UTC):
        - Current overnight: Prior day 20:01 to current day 12:00
        - Prior overnight: 2 days ago 20:01 to 1 day ago 12:00
        - Prior regular hours: 1 day ago 13:30 to 20:00

        Returns:
            Dict with:
            - current_overnight_volume
            - prior_overnight_volume
            - prior_regular_volume
            - current_price
        """
        # Ensure timezone aware
        if scan_date.tzinfo is None:
            scan_date = scan_date.replace(tzinfo=timezone.utc)

        # Define time windows (all in UTC)
        current_overnight_start = datetime.combine(
            scan_date.date() - timedelta(days=1),
            time(20, 1, 0),
            tzinfo=timezone.utc
        )
        current_overnight_end = datetime.combine(
            scan_date.date(),
            time(12, 0, 0),
            tzinfo=timezone.utc
        )

        # Prior overnight: 2 days ago 20:01 to 1 day ago 12:00
        prior_overnight_start = current_overnight_start - timedelta(days=1)
        prior_overnight_end = current_overnight_end - timedelta(days=1)

        # Prior regular hours: 1 day ago 13:30 to 20:00
        prior_regular_start = datetime.combine(
            scan_date.date() - timedelta(days=1),
            time(13, 30, 0),
            tzinfo=timezone.utc
        )
        prior_regular_end = datetime.combine(
            scan_date.date() - timedelta(days=1),
            time(20, 0, 0),
            tzinfo=timezone.utc
        )

        try:
            # Fetch current overnight volume
            current_overnight_df = self.client.fetch_minute_bars(
                ticker,
                current_overnight_start.date(),
                current_overnight_end.date(),
                multiplier=1
            )

            # Filter to correct time range
            if not current_overnight_df.empty:
                mask = (
                    (current_overnight_df['timestamp'] >= current_overnight_start) &
                    (current_overnight_df['timestamp'] <= current_overnight_end)
                )
                current_overnight_df = current_overnight_df[mask]

            current_overnight_vol = int(current_overnight_df['volume'].sum()) if not current_overnight_df.empty else 0

            # Fetch prior overnight volume
            prior_overnight_df = self.client.fetch_minute_bars(
                ticker,
                prior_overnight_start.date(),
                prior_overnight_end.date(),
                multiplier=1
            )

            if not prior_overnight_df.empty:
                mask = (
                    (prior_overnight_df['timestamp'] >= prior_overnight_start) &
                    (prior_overnight_df['timestamp'] <= prior_overnight_end)
                )
                prior_overnight_df = prior_overnight_df[mask]

            prior_overnight_vol = int(prior_overnight_df['volume'].sum()) if not prior_overnight_df.empty else 0

            # Fetch prior regular hours volume
            prior_regular_df = self.client.fetch_minute_bars(
                ticker,
                prior_regular_start.date(),
                prior_regular_end.date(),
                multiplier=1
            )

            if not prior_regular_df.empty:
                mask = (
                    (prior_regular_df['timestamp'] >= prior_regular_start) &
                    (prior_regular_df['timestamp'] <= prior_regular_end)
                )
                prior_regular_df = prior_regular_df[mask]

            prior_regular_vol = int(prior_regular_df['volume'].sum()) if not prior_regular_df.empty else 0

            # Get current price (last price at 12:00 UTC)
            if not current_overnight_df.empty:
                current_price = float(current_overnight_df['close'].iloc[-1])
            else:
                current_price = 0.0

            return {
                'current_overnight_volume': current_overnight_vol,
                'prior_overnight_volume': prior_overnight_vol,
                'prior_regular_volume': prior_regular_vol,
                'current_price': current_price
            }

        except Exception as e:
            logger.error(f"Failed to fetch overnight volumes for {ticker}: {e}")
            return {
                'current_overnight_volume': 0,
                'prior_overnight_volume': 0,
                'prior_regular_volume': 0,
                'current_price': 0.0
            }


class TwoPhaseScanner:
    """
    Two-phase market scanner.

    Phase 1: Apply hard filters (ATR, price, gap)
    Phase 2: Calculate ranking metrics and sort
    """

    def __init__(
        self,
        tickers: List[str],
        filter_phase: FilterPhase = None,
        ranking_weights: RankingWeights = None,
        parallel_workers: int = 10
    ):
        """
        Initialize scanner.

        Args:
            tickers: List of ticker symbols to scan
            filter_phase: Hard filter thresholds
            ranking_weights: Weights for ranking metrics
            parallel_workers: Number of parallel threads
        """
        self.tickers = tickers
        self.filter_phase = filter_phase or FilterPhase()
        self.ranking_weights = ranking_weights or RankingWeights()
        self.parallel_workers = parallel_workers

        # Initialize data fetchers
        self.polygon_client = get_polygon_client()
        self.overnight_fetcher = OvernightVolumeFetcher(self.polygon_client)

        logger.info(f"Scanner initialized with {len(tickers)} tickers")

    def run_scan(
        self,
        scan_date: datetime = None,
        progress_callback=None
    ) -> pd.DataFrame:
        """
        Run the two-phase scan.

        Args:
            scan_date: Date/time for scan (defaults to today 12:00 UTC)
            progress_callback: Optional callback(completed, total, ticker)

        Returns:
            DataFrame with ranked scan results
        """
        if scan_date is None:
            scan_date = datetime.now(timezone.utc).replace(
                hour=12, minute=0, second=0, microsecond=0
            )
        else:
            # Ensure we're using 12:00 UTC on the specified date
            if isinstance(scan_date, date) and not isinstance(scan_date, datetime):
                scan_date = datetime.combine(scan_date, time(12, 0, 0))
            scan_date = scan_date.replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )

        logger.info(f"Starting two-phase scan for {scan_date.strftime('%Y-%m-%d')} at 12:00 UTC")

        # Phase 1: Fetch data and apply filters
        filtered_data = self._phase1_filter(scan_date, progress_callback)

        if filtered_data.empty:
            logger.warning("No tickers passed Phase 1 filters")
            return pd.DataFrame()

        logger.info(f"Phase 1 complete: {len(filtered_data)} tickers passed filters")

        # Phase 2: Calculate ranking metrics and sort
        ranked_data = self._phase2_rank(filtered_data)

        # Add metadata
        ranked_data['scan_date'] = scan_date.date()
        ranked_data['scan_time'] = scan_date.strftime('%H:%M UTC')

        # Add ticker_id
        date_str = scan_date.strftime('%m%d%y')
        ranked_data['ticker_id'] = ranked_data['ticker'] + '.' + date_str

        logger.info(f"Phase 2 complete: Ranked {len(ranked_data)} tickers")

        return ranked_data

    def _phase1_filter(
        self,
        scan_date: datetime,
        progress_callback=None
    ) -> pd.DataFrame:
        """
        Phase 1: Apply hard filters.

        Filters:
        - ATR >= min_atr
        - Price >= min_price
        - |Gap%| >= min_gap_percent
        """
        passed_tickers = []

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {
                executor.submit(self._process_ticker, ticker, scan_date): ticker
                for ticker in self.tickers
            }

            completed = 0
            for future in as_completed(futures):
                ticker = futures[future]
                completed += 1

                if progress_callback:
                    progress_callback(completed, len(self.tickers), ticker)

                try:
                    ticker_data = future.result()
                    if ticker_data is not None:
                        passed_tickers.append(ticker_data)
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")

                if completed % 50 == 0:
                    logger.info(f"Processed {completed}/{len(self.tickers)} tickers...")

        return pd.DataFrame(passed_tickers)

    def _process_ticker(self, ticker: str, scan_date: datetime) -> Optional[Dict]:
        """Process a single ticker through Phase 1 filters."""
        try:
            # Get prior day's daily data for ATR and closing price
            history_end = scan_date.date() - timedelta(days=1)
            history_start = history_end - timedelta(days=20)

            historical_df = self.polygon_client.fetch_daily_bars(
                ticker,
                history_start,
                history_end
            )

            if historical_df.empty or len(historical_df) < 2:
                return None

            # Calculate ATR
            atr = self._calculate_atr(historical_df)

            # Apply ATR filter early
            if atr < self.filter_phase.min_atr:
                return None

            prior_close = float(historical_df['close'].iloc[-1])

            # Get overnight volumes and current price
            overnight_data = self.overnight_fetcher.fetch_overnight_volumes(ticker, scan_date)
            current_price = overnight_data['current_price']

            if current_price == 0:
                return None

            # Apply price filter
            if current_price < self.filter_phase.min_price:
                return None

            # Calculate gap
            gap_percent = ((current_price - prior_close) / prior_close * 100) if prior_close > 0 else 0

            # Apply gap filter
            if abs(gap_percent) < self.filter_phase.min_gap_percent:
                return None

            # Ticker passed all filters, return data
            return {
                'ticker': ticker,
                'current_price': current_price,
                'prior_close': prior_close,
                'gap_percent': gap_percent,
                'atr': atr,
                'current_overnight_volume': overnight_data['current_overnight_volume'],
                'prior_overnight_volume': overnight_data['prior_overnight_volume'],
                'prior_regular_volume': overnight_data['prior_regular_volume'],
            }

        except Exception as e:
            logger.debug(f"Error processing {ticker}: {e}")
            return None

    def _phase2_rank(self, filtered_df: pd.DataFrame) -> pd.DataFrame:
        """
        Phase 2: Calculate ranking metrics and sort.

        Metrics:
        - Relative overnight volume (current/prior)
        - Relative volume (current overnight/prior regular)
        - Gap magnitude (absolute)
        """
        df = filtered_df.copy()

        # Calculate relative volume metrics
        df['relative_overnight_volume'] = np.where(
            df['prior_overnight_volume'] > 0,
            df['current_overnight_volume'] / df['prior_overnight_volume'],
            0
        )

        df['relative_volume'] = np.where(
            df['prior_regular_volume'] > 0,
            df['current_overnight_volume'] / df['prior_regular_volume'],
            0
        )

        df['gap_magnitude'] = df['gap_percent'].abs()

        # Normalize each metric to 0-100 scale for fair comparison
        def normalize_column(col):
            if col.max() > col.min():
                return 100 * (col - col.min()) / (col.max() - col.min())
            return pd.Series([50] * len(col), index=col.index)

        # Create normalized scores
        df['norm_overnight_vol'] = normalize_column(df['current_overnight_volume'])
        df['norm_rel_overnight'] = normalize_column(df['relative_overnight_volume'])
        df['norm_rel_volume'] = normalize_column(df['relative_volume'])
        df['norm_gap'] = normalize_column(df['gap_magnitude'])

        # Calculate composite score with normalized values (without short interest)
        df['ranking_score'] = (
            self.ranking_weights.overnight_volume * df['norm_overnight_vol'] +
            self.ranking_weights.relative_overnight_volume * df['norm_rel_overnight'] +
            self.ranking_weights.relative_volume * df['norm_rel_volume'] +
            self.ranking_weights.gap_magnitude * df['norm_gap']
        )

        # Primary sort by overnight volume, then by composite score
        df = df.sort_values(
            by=['current_overnight_volume', 'ranking_score'],
            ascending=[False, False]
        )

        # Add rank
        df['rank'] = range(1, len(df) + 1)

        # Clean up intermediate columns
        df = df.drop(columns=[
            'prior_regular_volume',
            'norm_overnight_vol', 'norm_rel_overnight',
            'norm_rel_volume', 'norm_gap', 'gap_magnitude'
        ], errors='ignore')

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range using EMA.

        Formula: 14-period EMA of True Range
        True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
        """
        if len(df) < 2:
            return 0.0

        df = df.copy()
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))

        df['true_range'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        atr = df['true_range'].ewm(span=period, adjust=False).mean()

        return float(atr.iloc[-1]) if not atr.empty else 0.0


# Default ticker lists for common indices
SP500_TICKERS = [
    'A', 'AAL', 'AAP', 'AAPL', 'ABBV', 'ABC', 'ABMD', 'ABT', 'ACGL', 'ACN',
    'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AEE', 'AEP', 'AES', 'AFL', 'AIG',
    'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK', 'ALL', 'ALLE', 'AMAT', 'AMCR',
    'AMD', 'AME', 'AMGN', 'AMP', 'AMT', 'AMTM', 'AMZN', 'ANET', 'ANSS', 'AON',
    'AOS', 'APA', 'APD', 'APH', 'APO', 'APTV', 'ARE', 'ATO', 'AVB', 'AVGO',
    'AVY', 'AWK', 'AXON', 'AXP', 'AZO', 'BA', 'BAC', 'BALL', 'BAX', 'BBWI',
    'BBY', 'BDX', 'BEN', 'BF-B', 'BG', 'BIIB', 'BIO', 'BK', 'BKNG', 'BKR',
    'BLDR', 'BLK', 'BMY', 'BR', 'BRK-B', 'BRO', 'BSX', 'BWA', 'BX', 'BXP',
    'C', 'CAG', 'CAH', 'CARR', 'CAT', 'CB', 'CBOE', 'CBRE', 'CCI', 'CCL',
    'CDAY', 'CDNS', 'CDW', 'CE', 'CEG', 'CF', 'CFG', 'CHD', 'CHRW', 'CHTR',
    'CI', 'CINF', 'CL', 'CLX', 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS',
    'CNC', 'CNP', 'COF', 'COO', 'COP', 'COR', 'COST', 'CPAY', 'CPB', 'CPRT',
    'CPT', 'CRL', 'CRM', 'CRWD', 'CSCO', 'CSGP', 'CSX', 'CTAS', 'CTLT', 'CTRA',
    'CTSH', 'CTVA', 'CVS', 'CVX', 'CZR', 'D', 'DAL', 'DD', 'DE', 'DECK',
    'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DISH', 'DLR', 'DLTR', 'DOC',
    'DOV', 'DOW', 'DPZ', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'DXCM', 'EA',
    'EBAY', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL', 'ELV', 'EMN', 'EMR',
    'ENPH', 'EOG', 'EPAM', 'EQIX', 'EQR', 'EQT', 'ERIE', 'ES', 'ESS', 'ETN',
    'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'F', 'FANG',
    'FAST', 'FCX', 'FDS', 'FDX', 'FE', 'FFIV', 'FI', 'FICO', 'FIS', 'FITB',
    'FLT', 'FMC', 'FOX', 'FOXA', 'FRT', 'FSLR', 'FTNT', 'FTV', 'GD', 'GDDY',
    'GE', 'GEHC', 'GEN', 'GEV', 'GILD', 'GIS', 'GL', 'GLW', 'GM', 'GNRC',
    'GOOG', 'GOOGL', 'GPC', 'GPN', 'GRMN', 'GS', 'GWW', 'HAL', 'HAS', 'HBAN',
    'HCA', 'HD', 'HES', 'HIG', 'HII', 'HLT', 'HOLX', 'HON', 'HPE', 'HPQ',
    'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HUM', 'HWM', 'IBM', 'ICE', 'IDXX',
    'IEX', 'IFF', 'ILMN', 'INCY', 'INTC', 'INTU', 'INVH', 'IP', 'IPG', 'IQV',
    'IR', 'IRM', 'ISRG', 'IT', 'ITW', 'IVZ', 'J', 'JBHT', 'JBL', 'JCI',
    'JKHY', 'JNJ', 'JNPR', 'JPM', 'K', 'KDP', 'KEY', 'KEYS', 'KHC', 'KIM',
    'KKR', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 'KR', 'KVUE', 'L', 'LDOS',
    'LEN', 'LH', 'LHX', 'LII', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNT', 'LOW',
    'LRCX', 'LULU', 'LUV', 'LVS', 'LW', 'LYB', 'LYV', 'MA', 'MAA', 'MAR',
    'MAS', 'MBC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'META',
    'MGM', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MMM', 'MNST', 'MO', 'MOH',
    'MOS', 'MPC', 'MPWR', 'MRK', 'MRNA', 'MRO', 'MS', 'MSCI', 'MSFT', 'MSI',
    'MTB', 'MTCH', 'MTD', 'MU', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX',
    'NI', 'NKE', 'NOC', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA',
    'NVR', 'NWS', 'NWSA', 'NXPI', 'O', 'ODFL', 'OKE', 'OMC', 'ON', 'ORCL',
    'ORLY', 'OTIS', 'OXY', 'PANW', 'PARA', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEAK',
    'PEG', 'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKG', 'PLD',
    'PLTR', 'PM', 'PNC', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU',
    'PSA', 'PSX', 'PTC', 'PWR', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'RCL', 'REG',
    'REGN', 'RF', 'RHI', 'RJF', 'RL', 'RMD', 'ROK', 'ROL', 'ROP', 'ROST',
    'RSG', 'RTX', 'RVTY', 'SBAC', 'SBUX', 'SCHW', 'SHW', 'SJM', 'SLB', 'SMCI',
    'SNA', 'SNPS', 'SO', 'SOLV', 'SPG', 'SPGI', 'SRE', 'STE', 'STLD', 'STT',
    'STX', 'STZ', 'SWK', 'SWKS', 'SYF', 'SYK', 'SYY', 'T', 'TAP', 'TDG',
    'TDY', 'TECH', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 'TJX', 'TMO', 'TMUS',
    'TPL', 'TPR', 'TRGP', 'TRMB', 'TROW', 'TRV', 'TSCO', 'TSLA', 'TSN', 'TT',
    'TTWO', 'TXN', 'TXT', 'TYL', 'UAL', 'UBER', 'UDR', 'UHS', 'ULTA', 'UNH',
    'UNP', 'UPS', 'URI', 'USB', 'V', 'VICI', 'VLO', 'VLTO', 'VMC', 'VRSK',
    'VRSN', 'VRTX', 'VST', 'VTR', 'VTRS', 'VZ', 'WAB', 'WAT', 'WBA', 'WBD',
    'WDC', 'WDAY', 'WEC', 'WELL', 'WFC', 'WM', 'WMB', 'WMT', 'WRB', 'WRK',
    'WST', 'WTW', 'WY', 'WYNN', 'XEL', 'XOM', 'XRAY', 'XYL', 'YUM', 'ZBH',
    'ZBRA', 'ZION', 'ZTS'
]

NASDAQ100_TICKERS = [
    'AAPL', 'ABNB', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AMAT', 'AMD', 'AMGN',
    'AMZN', 'ANSS', 'ARM', 'ASML', 'AVGO', 'AZN', 'BIIB', 'BKNG', 'BKR', 'CDNS',
    'CDW', 'CEG', 'CHTR', 'CMCSA', 'COST', 'CPRT', 'CRWD', 'CSCO', 'CSGP', 'CSX',
    'CTAS', 'CTSH', 'DASH', 'DDOG', 'DLTR', 'DXCM', 'EA', 'EXC', 'FANG', 'FAST',
    'FTNT', 'GEHC', 'GFS', 'GILD', 'GOOG', 'GOOGL', 'HON', 'IDXX', 'ILMN', 'INTC',
    'INTU', 'ISRG', 'KDP', 'KHC', 'KLAC', 'LIN', 'LRCX', 'LULU', 'MAR', 'MCHP',
    'MDB', 'MDLZ', 'MELI', 'META', 'MNST', 'MRNA', 'MRVL', 'MSFT', 'MU', 'NFLX',
    'NVDA', 'NXPI', 'ODFL', 'ON', 'ORLY', 'PANW', 'PAYX', 'PCAR', 'PDD', 'PEP',
    'PYPL', 'QCOM', 'REGN', 'ROP', 'ROST', 'SBUX', 'SMCI', 'SNPS', 'TEAM', 'TMUS',
    'TSLA', 'TTD', 'TTWO', 'TXN', 'VRSK', 'VRTX', 'WBD', 'WDAY', 'XEL', 'ZS'
]

# Ticker list mapping
TICKER_LISTS = {
    'sp500': SP500_TICKERS,
    'nasdaq100': NASDAQ100_TICKERS,
}


def get_ticker_list(list_name: str) -> List[str]:
    """
    Get ticker list by name.

    Args:
        list_name: 'sp500' or 'nasdaq100'

    Returns:
        List of ticker symbols
    """
    if list_name.lower() not in TICKER_LISTS:
        raise ValueError(f"Unknown ticker list: {list_name}. Available: {list(TICKER_LISTS.keys())}")
    return TICKER_LISTS[list_name.lower()].copy()
