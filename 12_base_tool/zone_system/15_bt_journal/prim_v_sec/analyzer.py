"""
Epoch Backtest Journal - Primary vs Secondary Zone Analyzer
Calculates performance metrics for EPCH1-4 models and zone types.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.connection import EpochDatabase
from config.settings import PRIMARY_MODELS, SECONDARY_MODELS, MODEL_ZONE_MAPPING


@dataclass
class ModelStats:
    """Statistics for a single model."""
    model: str
    zone_type: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    gross_wins_r: float
    gross_losses_r: float
    net_r: float
    expectancy_r: float
    largest_win_r: float
    largest_loss_r: float
    avg_win_r: float
    avg_loss_r: float


@dataclass
class ZoneTypeStats:
    """Statistics for a zone type (PRIMARY or SECONDARY)."""
    zone_type: str
    models: List[str]
    trades: int
    wins: int
    losses: int
    win_rate: float
    gross_wins_r: float
    gross_losses_r: float
    net_r: float
    expectancy_r: float


@dataclass
class AnalysisView:
    """Statistics for a single view (all trades or winners only)."""
    view_name: str  # "All Trades" or "Winners Only"
    trade_count: int
    model_stats: List[ModelStats]
    zone_stats: List[ZoneTypeStats]
    overall_stats: Dict


@dataclass
class AnalysisResult:
    """Complete analysis result with multiple views."""
    start_date: Optional[date]
    end_date: Optional[date]
    total_days: int
    all_trades: AnalysisView  # Monte Carlo raw data
    winners_only: AnalysisView  # Filtered to winners
    raw_trades: List[Dict] = None  # Raw trade data for export

    # Backwards compatibility properties
    @property
    def model_stats(self) -> List[ModelStats]:
        return self.all_trades.model_stats

    @property
    def zone_stats(self) -> List[ZoneTypeStats]:
        return self.all_trades.zone_stats

    @property
    def overall_stats(self) -> Dict:
        return self.all_trades.overall_stats


class PrimarySecondaryAnalyzer:
    """
    Analyzes trade performance by model (EPCH1-4) and zone type (PRIMARY/SECONDARY).
    """

    def __init__(self, db: EpochDatabase = None):
        """
        Initialize analyzer.

        Args:
            db: Database connection. Creates new if not provided.
        """
        self.db = db or EpochDatabase()

    def analyze(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> AnalysisResult:
        """
        Run primary vs secondary analysis.

        Args:
            start_date: Start of date range (inclusive). None for all data.
            end_date: End of date range (inclusive). None for all data.

        Returns:
            AnalysisResult with model and zone statistics for both views
        """
        # Load trades
        trades = self.db.get_trades(start_date=start_date, end_date=end_date)

        if not trades:
            empty_view = AnalysisView(
                view_name="All Trades",
                trade_count=0,
                model_stats=[],
                zone_stats=[],
                overall_stats={}
            )
            return AnalysisResult(
                start_date=start_date,
                end_date=end_date,
                total_days=0,
                all_trades=empty_view,
                winners_only=AnalysisView(
                    view_name="Winners Only",
                    trade_count=0,
                    model_stats=[],
                    zone_stats=[],
                    overall_stats={}
                ),
                raw_trades=[]
            )

        # Determine actual date range
        dates = sorted(set(t["date"] for t in trades))
        actual_start = dates[0] if dates else start_date
        actual_end = dates[-1] if dates else end_date
        total_days = len(dates)

        # Calculate ALL TRADES view
        all_model_stats = self._calculate_model_stats(trades)
        all_zone_stats = self._calculate_zone_stats(trades, all_model_stats)
        all_overall_stats = self._calculate_overall_stats(trades)

        all_trades_view = AnalysisView(
            view_name="All Trades",
            trade_count=len(trades),
            model_stats=all_model_stats,
            zone_stats=all_zone_stats,
            overall_stats=all_overall_stats
        )

        # Calculate WINNERS ONLY view
        winners = [t for t in trades if t["is_winner"]]
        winners_model_stats = self._calculate_model_stats(winners)
        winners_zone_stats = self._calculate_zone_stats(winners, winners_model_stats)
        winners_overall_stats = self._calculate_overall_stats(winners)

        winners_only_view = AnalysisView(
            view_name="Winners Only",
            trade_count=len(winners),
            model_stats=winners_model_stats,
            zone_stats=winners_zone_stats,
            overall_stats=winners_overall_stats
        )

        return AnalysisResult(
            start_date=actual_start,
            end_date=actual_end,
            total_days=total_days,
            all_trades=all_trades_view,
            winners_only=winners_only_view,
            raw_trades=trades
        )

    def _calculate_model_stats(self, trades: List[Dict]) -> List[ModelStats]:
        """Calculate statistics for each model."""
        stats = []

        for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
            model_trades = [t for t in trades if t["model"] == model]

            if not model_trades:
                continue

            wins = [t for t in model_trades if t["is_winner"]]
            losses = [t for t in model_trades if not t["is_winner"]]

            win_pnls = [float(t["pnl_r"]) for t in wins]
            loss_pnls = [float(t["pnl_r"]) for t in losses]

            gross_wins = sum(win_pnls) if win_pnls else 0
            gross_losses = sum(loss_pnls) if loss_pnls else 0
            net_r = gross_wins + gross_losses

            stats.append(ModelStats(
                model=model,
                zone_type=MODEL_ZONE_MAPPING[model],
                trades=len(model_trades),
                wins=len(wins),
                losses=len(losses),
                win_rate=len(wins) / len(model_trades) if model_trades else 0,
                gross_wins_r=gross_wins,
                gross_losses_r=gross_losses,
                net_r=net_r,
                expectancy_r=net_r / len(model_trades) if model_trades else 0,
                largest_win_r=max(win_pnls) if win_pnls else 0,
                largest_loss_r=min(loss_pnls) if loss_pnls else 0,
                avg_win_r=sum(win_pnls) / len(win_pnls) if win_pnls else 0,
                avg_loss_r=sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0,
            ))

        return stats

    def _calculate_zone_stats(
        self,
        trades: List[Dict],
        model_stats: List[ModelStats]
    ) -> List[ZoneTypeStats]:
        """Calculate statistics for PRIMARY and SECONDARY zones."""
        stats = []

        for zone_type, models in [("PRIMARY", PRIMARY_MODELS), ("SECONDARY", SECONDARY_MODELS)]:
            zone_model_stats = [s for s in model_stats if s.zone_type == zone_type]

            if not zone_model_stats:
                continue

            trades_count = sum(s.trades for s in zone_model_stats)
            wins_count = sum(s.wins for s in zone_model_stats)
            losses_count = sum(s.losses for s in zone_model_stats)
            gross_wins = sum(s.gross_wins_r for s in zone_model_stats)
            gross_losses = sum(s.gross_losses_r for s in zone_model_stats)
            net_r = gross_wins + gross_losses

            stats.append(ZoneTypeStats(
                zone_type=zone_type,
                models=models,
                trades=trades_count,
                wins=wins_count,
                losses=losses_count,
                win_rate=wins_count / trades_count if trades_count else 0,
                gross_wins_r=gross_wins,
                gross_losses_r=gross_losses,
                net_r=net_r,
                expectancy_r=net_r / trades_count if trades_count else 0,
            ))

        return stats

    def _calculate_overall_stats(self, trades: List[Dict]) -> Dict:
        """Calculate overall statistics."""
        if not trades:
            return {}

        wins = [t for t in trades if t["is_winner"]]
        losses = [t for t in trades if not t["is_winner"]]

        win_pnls = [float(t["pnl_r"]) for t in wins]
        loss_pnls = [float(t["pnl_r"]) for t in losses]

        gross_wins = sum(win_pnls) if win_pnls else 0
        gross_losses = sum(loss_pnls) if loss_pnls else 0
        net_r = gross_wins + gross_losses

        return {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(trades) if trades else 0,
            "gross_wins_r": gross_wins,
            "gross_losses_r": gross_losses,
            "net_r": net_r,
            "expectancy_r": net_r / len(trades) if trades else 0,
            "largest_win_r": max(win_pnls) if win_pnls else 0,
            "largest_loss_r": min(loss_pnls) if loss_pnls else 0,
            "avg_win_r": sum(win_pnls) / len(win_pnls) if win_pnls else 0,
            "avg_loss_r": sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0,
        }
