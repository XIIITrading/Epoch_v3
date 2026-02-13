"""
================================================================================
EPOCH TRADING SYSTEM - OPTIONS ANALYSIS CALCULATOR
R-Multiple and Net Returns Calculations
XIII Trading LLC
================================================================================

Calculates options trade performance metrics:
- R-Multiple: Options P&L expressed as R (risk unit)
- Net Returns: Percentage return on options premium

================================================================================
"""

from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List

# Handle both relative and absolute imports
try:
    from .config import CALCULATION_VERSION
except ImportError:
    from config import CALCULATION_VERSION


@dataclass
class OptionsAnalysisResult:
    """
    Complete options analysis result for database storage.

    Maps to the options_analysis table schema.
    """
    # Primary Key
    trade_id: str

    # Trade Identification
    ticker: str
    direction: str
    entry_date: date
    entry_time: Optional[time]
    entry_price: float

    # Options Contract Details
    options_ticker: str
    strike: float
    expiration: date
    contract_type: str  # CALL, PUT

    # Options Entry/Exit
    option_entry_price: Optional[float]
    option_entry_time: Optional[str]
    option_exit_price: Optional[float]
    option_exit_time: Optional[str]

    # P&L Metrics
    pnl_dollars: Optional[float]
    pnl_percent: Optional[float]
    option_r: Optional[float]
    net_return: Optional[float]

    # Comparison to Underlying
    underlying_r: Optional[float]
    r_multiplier: Optional[float]

    # Outcome
    win: Optional[int]  # 1 = win, 0 = loss

    # Processing Status
    status: str  # SUCCESS, NO_CHAIN, NO_CONTRACT, NO_BARS, etc.

    # Metadata
    calculation_version: str = CALCULATION_VERSION


@dataclass
class OptionsTradeResult:
    """
    Complete options trade result with R and Net Returns.

    Used for P&L calculations before creating OptionsAnalysisResult.
    """
    # Entry data
    option_entry_price: float
    option_entry_time: str

    # Exit data
    option_exit_price: float
    option_exit_time: str

    # P&L metrics
    pnl_dollars: float          # Dollar P&L per contract (exit - entry) * 100
    pnl_percent: float          # Percentage return on premium
    option_r: float             # R-multiple for options trade
    net_return: float           # Net return percentage

    # Comparison to underlying
    underlying_pnl_r: float     # Underlying trade R-multiple
    r_multiplier: float         # How much better/worse options did vs underlying

    # Win/Loss
    win: bool


class OptionsAnalysisCalculator:
    """
    Calculator for options analysis metrics.

    Takes trade data and fetcher, processes options data,
    and returns OptionsAnalysisResult for database storage.
    """

    def __init__(self, fetcher, verbose: bool = False):
        """
        Initialize the calculator.

        Args:
            fetcher: OptionsFetcher instance for API calls
            verbose: Enable verbose logging
        """
        self.fetcher = fetcher
        self.verbose = verbose

    def _log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"    {message}")

    def calculate(self, trade: Dict[str, Any]) -> Optional[OptionsAnalysisResult]:
        """
        Calculate options analysis for a single trade.

        Args:
            trade: Trade dictionary from database with keys:
                - trade_id, ticker, direction, date, entry_time, entry_price
                - exit_time, risk, pnl_r, is_winner

        Returns:
            OptionsAnalysisResult or None if calculation fails
        """
        # Handle both relative and absolute imports
        try:
            from .contract_selector import select_contract
        except ImportError:
            from contract_selector import select_contract

        trade_id = trade['trade_id']
        ticker = trade['ticker']
        direction = trade.get('direction', '')
        entry_date = trade['date']
        entry_time = trade.get('entry_time')
        entry_price = float(trade['entry_price']) if trade.get('entry_price') else 0
        exit_time = trade.get('exit_time')
        underlying_risk = float(trade['risk']) if trade.get('risk') else 0
        underlying_pnl_r = float(trade['pnl_r']) if trade.get('pnl_r') else 0
        underlying_win = trade.get('is_winner')

        self._log(f"Processing {trade_id}: {ticker} {direction} @ ${entry_price:.2f}")

        # Validate required data
        if not entry_price or not entry_date or not ticker:
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker='',
                strike=0,
                expiration=entry_date,
                contract_type='',
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='INVALID_DATA'
            )

        # Convert entry_date to proper format
        if isinstance(entry_date, datetime):
            entry_date_str = entry_date.strftime('%Y-%m-%d')
            entry_date = entry_date.date()
        elif isinstance(entry_date, date):
            entry_date_str = entry_date.strftime('%Y-%m-%d')
        else:
            entry_date_str = str(entry_date)

        # Step 1: Fetch options chain
        chain = self.fetcher.fetch_options_chain(
            underlying=ticker,
            trade_date=entry_date_str
        )

        if not chain or not chain.contracts:
            self._log(f"No options chain available for {ticker}")
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker='',
                strike=0,
                expiration=entry_date,
                contract_type='',
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='NO_CHAIN'
            )

        # Step 2: Select contract
        selected = select_contract(
            chain=chain,
            entry_price=entry_price,
            direction=direction,
            trade_date=entry_date,
            exit_date=entry_date  # Same day trades
        )

        if not selected:
            self._log(f"No suitable contract found for {ticker}")
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker='',
                strike=0,
                expiration=entry_date,
                contract_type='',
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='NO_CONTRACT'
            )

        contract = selected.contract
        self._log(f"Selected: {contract.ticker} (${contract.strike} {contract.contract_type})")

        # Step 3: Fetch entry bars (15-second)
        entry_bars = self.fetcher.fetch_entry_bars(
            options_ticker=contract.ticker,
            trade_date=entry_date_str
        )

        if not entry_bars:
            self._log(f"No 15-second bars available at entry")
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker=contract.ticker,
                strike=contract.strike,
                expiration=contract.expiration,
                contract_type=contract.contract_type.upper(),
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='NO_ENTRY_BARS'
            )

        # Step 4: Fetch exit bars (5-minute)
        exit_bars = self.fetcher.fetch_exit_bars(
            options_ticker=contract.ticker,
            trade_date=entry_date_str
        )

        if not exit_bars:
            self._log(f"No 5-minute bars available at exit")
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker=contract.ticker,
                strike=contract.strike,
                expiration=contract.expiration,
                contract_type=contract.contract_type.upper(),
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='NO_EXIT_BARS'
            )

        # Step 5: Find matching bars at entry and exit times
        entry_bar = self.fetcher.get_bar_at_time(entry_bars, entry_time, entry_date) if entry_time else None
        exit_bar = self.fetcher.get_bar_at_time(exit_bars, exit_time, entry_date) if exit_time else None

        # Fallback to first/last bar if time not provided
        if not entry_bar and not entry_time and entry_bars:
            entry_bar = entry_bars[0]
        if not exit_bar and not exit_time and exit_bars:
            exit_bar = exit_bars[-1]

        if not entry_bar or not exit_bar:
            self._log(f"Could not find matching bars")
            return OptionsAnalysisResult(
                trade_id=trade_id,
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                entry_time=entry_time,
                entry_price=entry_price,
                options_ticker=contract.ticker,
                strike=contract.strike,
                expiration=contract.expiration,
                contract_type=contract.contract_type.upper(),
                option_entry_price=None,
                option_entry_time=None,
                option_exit_price=None,
                option_exit_time=None,
                pnl_dollars=None,
                pnl_percent=None,
                option_r=None,
                net_return=None,
                underlying_r=underlying_pnl_r,
                r_multiplier=None,
                win=None,
                status='NO_MATCHING_BARS'
            )

        # Step 6: Calculate P&L
        trade_result = calculate_options_pnl(
            entry_price=entry_bar.open,
            exit_price=exit_bar.open,
            underlying_risk=underlying_risk,
            underlying_pnl_r=underlying_pnl_r,
            entry_time=entry_time.strftime('%H:%M:%S') if entry_time else '',
            exit_time=exit_time.strftime('%H:%M:%S') if exit_time else '',
            underlying_win=underlying_win
        )

        self._log(f"P&L: ${trade_result.pnl_dollars:.2f} ({trade_result.pnl_percent:.1f}%) = {trade_result.option_r:.2f}R")

        return OptionsAnalysisResult(
            trade_id=trade_id,
            ticker=ticker,
            direction=direction,
            entry_date=entry_date,
            entry_time=entry_time,
            entry_price=entry_price,
            options_ticker=contract.ticker,
            strike=contract.strike,
            expiration=contract.expiration,
            contract_type=contract.contract_type.upper(),
            option_entry_price=trade_result.option_entry_price,
            option_entry_time=trade_result.option_entry_time,
            option_exit_price=trade_result.option_exit_price,
            option_exit_time=trade_result.option_exit_time,
            pnl_dollars=trade_result.pnl_dollars,
            pnl_percent=trade_result.pnl_percent,
            option_r=trade_result.option_r,
            net_return=trade_result.net_return,
            underlying_r=trade_result.underlying_pnl_r,
            r_multiplier=trade_result.r_multiplier,
            win=1 if trade_result.win else 0,
            status='SUCCESS'
        )

    def close(self):
        """Cleanup resources."""
        if self.fetcher:
            self.fetcher.clear_cache()


def calculate_options_pnl(
    entry_price: float,
    exit_price: float,
    underlying_risk: float,
    underlying_pnl_r: float,
    entry_time: str = "",
    exit_time: str = "",
    contracts: int = 1,
    underlying_win: bool = None
) -> OptionsTradeResult:
    """
    Calculate options trade P&L with R and Net Returns.

    Args:
        entry_price: Options entry price (premium paid)
        exit_price: Options exit price (premium received)
        underlying_risk: Dollar risk on underlying trade (stop distance)
        underlying_pnl_r: Underlying trade P&L in R-multiple
        entry_time: Entry time string for tracking
        exit_time: Exit time string for tracking
        contracts: Number of contracts (default 1)
        underlying_win: Win/loss from backtest (True=win, False=loss).
                        If provided, this is used instead of recalculating from options P&L.

    Returns:
        OptionsTradeResult with all metrics
    """
    # Basic P&L
    pnl_per_share = exit_price - entry_price
    pnl_dollars = pnl_per_share * 100 * contracts  # Options = 100 shares per contract

    # Percentage return on premium (Net Return)
    if entry_price > 0:
        pnl_percent = (pnl_per_share / entry_price) * 100
        net_return = pnl_percent
    else:
        pnl_percent = 0.0
        net_return = 0.0

    # R-Multiple calculation for options
    if underlying_risk > 0:
        # Risk per 100 shares (to match 1 contract)
        risk_per_contract = underlying_risk * 100
        option_r = pnl_dollars / risk_per_contract
    else:
        option_r = 0.0

    # R-Multiplier: How options R compares to underlying R
    if underlying_pnl_r != 0:
        r_multiplier = option_r / underlying_pnl_r
    else:
        r_multiplier = 0.0

    # Win/Loss - inherit from backtest if provided, otherwise calculate from options P&L
    if underlying_win is not None:
        win = underlying_win
    else:
        win = pnl_dollars > 0

    return OptionsTradeResult(
        option_entry_price=entry_price,
        option_entry_time=entry_time,
        option_exit_price=exit_price,
        option_exit_time=exit_time,
        pnl_dollars=pnl_dollars,
        pnl_percent=pnl_percent,
        option_r=option_r,
        net_return=net_return,
        underlying_pnl_r=underlying_pnl_r,
        r_multiplier=r_multiplier,
        win=win
    )


@dataclass
class OptionsSummaryStats:
    """Summary statistics for a batch of options trades."""
    total_trades: int
    successful_trades: int      # Trades with options data
    failed_trades: int          # Trades without options data

    # Win/Loss
    wins: int
    losses: int
    win_rate: float

    # P&L
    total_pnl_dollars: float
    avg_pnl_dollars: float
    avg_pnl_percent: float

    # R Stats
    total_r: float
    avg_r: float
    best_r: float
    worst_r: float

    # Comparison to underlying
    avg_r_multiplier: float     # Avg of options R / underlying R
    trades_outperformed: int    # Trades where options R > underlying R


def calculate_summary_stats(results: List[OptionsAnalysisResult]) -> OptionsSummaryStats:
    """
    Calculate summary statistics for a list of options analysis results.

    Args:
        results: List of OptionsAnalysisResult objects

    Returns:
        OptionsSummaryStats with aggregated metrics
    """
    # Filter successful trades
    successful = [r for r in results if r.status == 'SUCCESS' and r.pnl_dollars is not None]
    failed = len(results) - len(successful)

    if not successful:
        return OptionsSummaryStats(
            total_trades=len(results),
            successful_trades=0,
            failed_trades=failed,
            wins=0, losses=0, win_rate=0.0,
            total_pnl_dollars=0.0, avg_pnl_dollars=0.0, avg_pnl_percent=0.0,
            total_r=0.0, avg_r=0.0, best_r=0.0, worst_r=0.0,
            avg_r_multiplier=0.0, trades_outperformed=0
        )

    wins = sum(1 for r in successful if r.win == 1)
    losses = len(successful) - wins
    win_rate = wins / len(successful) * 100 if successful else 0

    total_pnl = sum(r.pnl_dollars for r in successful if r.pnl_dollars)
    avg_pnl = total_pnl / len(successful)
    avg_pnl_pct = sum(r.pnl_percent for r in successful if r.pnl_percent) / len(successful)

    r_values = [r.option_r for r in successful if r.option_r is not None]
    total_r = sum(r_values) if r_values else 0
    avg_r = total_r / len(r_values) if r_values else 0
    best_r = max(r_values) if r_values else 0
    worst_r = min(r_values) if r_values else 0

    # R multiplier
    valid_multipliers = [r.r_multiplier for r in successful if r.r_multiplier and r.r_multiplier != 0]
    avg_multiplier = sum(valid_multipliers) / len(valid_multipliers) if valid_multipliers else 0

    # Outperformance
    outperformed = sum(1 for r in successful if r.option_r and r.underlying_r and r.option_r > r.underlying_r)

    return OptionsSummaryStats(
        total_trades=len(results),
        successful_trades=len(successful),
        failed_trades=failed,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        total_pnl_dollars=total_pnl,
        avg_pnl_dollars=avg_pnl,
        avg_pnl_percent=avg_pnl_pct,
        total_r=total_r,
        avg_r=avg_r,
        best_r=best_r,
        worst_r=worst_r,
        avg_r_multiplier=avg_multiplier,
        trades_outperformed=outperformed
    )
