"""
Epoch Backtest Journal - Confluence Analyzer
Calculates direction-relative confluence scoring to determine how stacked
alignment of entry factors impacts win rate.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.connection import EpochDatabase


@dataclass
class FactorAlignment:
    """Results for a single factor's directional alignment."""
    factor_name: str  # e.g., "M5_Structure"

    # When aligned with trade direction
    aligned_trades: int
    aligned_wins: int
    aligned_win_rate: float
    aligned_avg_pnl_r: float

    # When misaligned with trade direction
    misaligned_trades: int
    misaligned_wins: int
    misaligned_win_rate: float
    misaligned_avg_pnl_r: float

    # Neutral (structure = NEUTRAL, or VWAP = AT)
    neutral_trades: int
    neutral_wins: int
    neutral_win_rate: float

    # Edge calculation
    alignment_edge: float  # aligned_win_rate - misaligned_win_rate
    edge_rank: int = 0  # Rank by edge (1 = highest edge)


@dataclass
class ConfluenceBucket:
    """Stats for one confluence score level."""
    score: int  # 0-7
    score_label: str  # "0-1", "2", "3", etc.
    trade_count: int
    wins: int
    losses: int
    win_rate: float
    avg_pnl_r: float
    total_pnl_r: float


@dataclass
class AnalysisResult:
    """Complete analysis output."""
    start_date: Optional[date]
    end_date: Optional[date]
    total_trades: int
    trades_with_entry_data: int
    baseline_win_rate: float
    baseline_expectancy: float

    # Individual factor analysis
    factor_alignments: List[FactorAlignment]  # Sorted by edge_rank

    # Confluence curve (the key output)
    confluence_buckets: List[ConfluenceBucket]  # Scores 0-7

    # Summary metrics for headlines
    min_score_for_positive_expectancy: Optional[int]  # e.g., 5
    score_6_plus_win_rate: float
    score_6_plus_trades: int
    score_5_plus_win_rate: float
    score_5_plus_trades: int

    # Raw data for Excel
    raw_data: List[Dict] = field(default_factory=list)


class ConfluenceAnalyzer:
    """
    Analyzes direction-relative confluence scoring.
    Calculates how stacked alignment of entry factors impacts win rate.
    """

    # Factor definitions for alignment calculation
    STRUCTURE_FACTORS = ['m5_structure', 'm15_structure', 'h1_structure', 'h4_structure']
    ALL_FACTORS = STRUCTURE_FACTORS + ['vwap', 'sma_stack', 'volume']

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
        Run confluence analysis.

        Args:
            start_date: Start of date range (inclusive). None for all data.
            end_date: End of date range (inclusive). None for all data.

        Returns:
            AnalysisResult with factor alignments and confluence curve
        """
        # Load trades with entry events
        trades = self.db.get_trades_with_entry_events(start_date=start_date, end_date=end_date)

        if not trades:
            return self._empty_result(start_date, end_date)

        # Determine actual date range
        dates = sorted(set(t["date"] for t in trades))
        actual_start = dates[0] if dates else start_date
        actual_end = dates[-1] if dates else end_date

        # Filter trades with entry data (using m5_structure as indicator)
        trades_with_data = [t for t in trades if t.get('m5_structure') is not None]

        if not trades_with_data:
            return self._empty_result(actual_start, actual_end, total_trades=len(trades))

        # Calculate baseline statistics
        baseline_win_rate = self._calculate_win_rate(trades_with_data)
        baseline_expectancy = self._calculate_expectancy(trades_with_data)

        # Calculate alignments for each trade and add to trade dict
        for trade in trades_with_data:
            alignments = self._calculate_alignment(trade)
            trade['_alignments'] = alignments
            trade['_confluence_score'] = self._calculate_confluence_score(alignments)

        # Analyze individual factors
        factor_alignments = self._analyze_factor_alignments(trades_with_data)

        # Rank factors by edge
        factor_alignments.sort(key=lambda x: x.alignment_edge, reverse=True)
        for rank, fa in enumerate(factor_alignments, 1):
            fa.edge_rank = rank

        # Build confluence buckets
        confluence_buckets = self._build_confluence_buckets(trades_with_data)

        # Calculate summary metrics
        min_score_positive = self._find_min_positive_expectancy_score(confluence_buckets)
        score_6_plus = self._calculate_score_threshold_stats(trades_with_data, threshold=6)
        score_5_plus = self._calculate_score_threshold_stats(trades_with_data, threshold=5)

        return AnalysisResult(
            start_date=actual_start,
            end_date=actual_end,
            total_trades=len(trades),
            trades_with_entry_data=len(trades_with_data),
            baseline_win_rate=baseline_win_rate,
            baseline_expectancy=baseline_expectancy,
            factor_alignments=factor_alignments,
            confluence_buckets=confluence_buckets,
            min_score_for_positive_expectancy=min_score_positive,
            score_6_plus_win_rate=score_6_plus[0],
            score_6_plus_trades=score_6_plus[1],
            score_5_plus_win_rate=score_5_plus[0],
            score_5_plus_trades=score_5_plus[1],
            raw_data=trades_with_data
        )

    def _empty_result(
        self,
        start_date: date = None,
        end_date: date = None,
        total_trades: int = 0
    ) -> AnalysisResult:
        """Create empty result for no data case."""
        return AnalysisResult(
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            trades_with_entry_data=0,
            baseline_win_rate=0.0,
            baseline_expectancy=0.0,
            factor_alignments=[],
            confluence_buckets=[],
            min_score_for_positive_expectancy=7,
            score_6_plus_win_rate=0.0,
            score_6_plus_trades=0,
            score_5_plus_win_rate=0.0,
            score_5_plus_trades=0,
            raw_data=[]
        )

    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate for a set of trades."""
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t.get('is_winner'))
        return wins / len(trades)

    def _calculate_expectancy(self, trades: List[Dict]) -> float:
        """Calculate average PnL (expectancy) in R."""
        if not trades:
            return 0.0
        pnls = [float(t.get('pnl_r', 0) or 0) for t in trades]
        return sum(pnls) / len(pnls)

    def _calculate_alignment(self, trade: Dict) -> Dict:
        """
        Calculate alignment for each factor based on trade direction.
        Returns dict with factor_name -> {'aligned': bool, 'neutral': bool}
        """
        direction = trade.get('direction', '')
        is_long = direction == 'LONG'

        alignments = {}

        # Structure factors - BULL aligned for LONG, BEAR aligned for SHORT
        for tf in self.STRUCTURE_FACTORS:
            value = trade.get(tf)
            if value is None or str(value).upper() == 'NEUTRAL':
                alignments[tf] = {'aligned': False, 'neutral': True}
            elif is_long:
                alignments[tf] = {'aligned': str(value).upper() == 'BULL', 'neutral': False}
            else:  # SHORT
                alignments[tf] = {'aligned': str(value).upper() == 'BEAR', 'neutral': False}

        # VWAP - ABOVE aligned for LONG, BELOW aligned for SHORT
        vwap = trade.get('entry_vs_vwap')
        if vwap is None or str(vwap).upper() == 'AT':
            alignments['vwap'] = {'aligned': False, 'neutral': True}
        elif is_long:
            alignments['vwap'] = {'aligned': str(vwap).upper() == 'ABOVE', 'neutral': False}
        else:
            alignments['vwap'] = {'aligned': str(vwap).upper() == 'BELOW', 'neutral': False}

        # SMA Stack - BULLISH aligned for LONG, BEARISH aligned for SHORT
        sma = trade.get('sma9_vs_sma21')
        if sma is None:
            alignments['sma_stack'] = {'aligned': False, 'neutral': True}
        elif is_long:
            alignments['sma_stack'] = {'aligned': str(sma).upper() == 'BULLISH', 'neutral': False}
        else:
            alignments['sma_stack'] = {'aligned': str(sma).upper() == 'BEARISH', 'neutral': False}

        # Volume - INCREASING or FLAT is aligned for both directions
        vol = trade.get('volume_trend')
        if vol is None:
            alignments['volume'] = {'aligned': False, 'neutral': True}
        else:
            alignments['volume'] = {'aligned': str(vol).upper() in ['INCREASING', 'FLAT'], 'neutral': False}

        return alignments

    def _calculate_confluence_score(self, alignments: Dict) -> int:
        """Sum of aligned factors (0-7)."""
        return sum(1 for a in alignments.values() if a['aligned'])

    def _analyze_factor_alignments(self, trades: List[Dict]) -> List[FactorAlignment]:
        """Analyze alignment statistics for each factor."""
        factor_stats = {}

        for factor in self.ALL_FACTORS:
            factor_stats[factor] = {
                'aligned': {'trades': [], 'wins': 0},
                'misaligned': {'trades': [], 'wins': 0},
                'neutral': {'trades': [], 'wins': 0}
            }

        # Aggregate by factor
        for trade in trades:
            alignments = trade.get('_alignments', {})
            is_winner = trade.get('is_winner', False)
            pnl_r = float(trade.get('pnl_r', 0) or 0)

            for factor in self.ALL_FACTORS:
                alignment = alignments.get(factor, {'aligned': False, 'neutral': True})

                if alignment['neutral']:
                    factor_stats[factor]['neutral']['trades'].append(pnl_r)
                    if is_winner:
                        factor_stats[factor]['neutral']['wins'] += 1
                elif alignment['aligned']:
                    factor_stats[factor]['aligned']['trades'].append(pnl_r)
                    if is_winner:
                        factor_stats[factor]['aligned']['wins'] += 1
                else:
                    factor_stats[factor]['misaligned']['trades'].append(pnl_r)
                    if is_winner:
                        factor_stats[factor]['misaligned']['wins'] += 1

        # Build FactorAlignment objects
        results = []
        for factor in self.ALL_FACTORS:
            stats = factor_stats[factor]

            aligned_trades = len(stats['aligned']['trades'])
            aligned_wins = stats['aligned']['wins']
            aligned_pnls = stats['aligned']['trades']
            aligned_win_rate = aligned_wins / aligned_trades if aligned_trades > 0 else 0
            aligned_avg_pnl = sum(aligned_pnls) / len(aligned_pnls) if aligned_pnls else 0

            misaligned_trades = len(stats['misaligned']['trades'])
            misaligned_wins = stats['misaligned']['wins']
            misaligned_pnls = stats['misaligned']['trades']
            misaligned_win_rate = misaligned_wins / misaligned_trades if misaligned_trades > 0 else 0
            misaligned_avg_pnl = sum(misaligned_pnls) / len(misaligned_pnls) if misaligned_pnls else 0

            neutral_trades = len(stats['neutral']['trades'])
            neutral_wins = stats['neutral']['wins']
            neutral_win_rate = neutral_wins / neutral_trades if neutral_trades > 0 else 0

            alignment_edge = aligned_win_rate - misaligned_win_rate

            # Format factor name for display
            display_name = factor.replace('_', ' ').title()
            if factor in self.STRUCTURE_FACTORS:
                display_name = factor.upper().replace('_STRUCTURE', '')

            results.append(FactorAlignment(
                factor_name=display_name,
                aligned_trades=aligned_trades,
                aligned_wins=aligned_wins,
                aligned_win_rate=aligned_win_rate,
                aligned_avg_pnl_r=aligned_avg_pnl,
                misaligned_trades=misaligned_trades,
                misaligned_wins=misaligned_wins,
                misaligned_win_rate=misaligned_win_rate,
                misaligned_avg_pnl_r=misaligned_avg_pnl,
                neutral_trades=neutral_trades,
                neutral_wins=neutral_wins,
                neutral_win_rate=neutral_win_rate,
                alignment_edge=alignment_edge
            ))

        return results

    def _build_confluence_buckets(self, trades: List[Dict]) -> List[ConfluenceBucket]:
        """Build confluence score buckets with stats."""
        # Group trades by score
        score_groups = {i: [] for i in range(8)}  # 0-7

        for trade in trades:
            score = trade.get('_confluence_score', 0)
            score_groups[score].append(trade)

        # Build buckets
        buckets = []

        # Combine 0 and 1 due to typically low sample sizes
        combined_01 = score_groups[0] + score_groups[1]
        if combined_01:
            wins = sum(1 for t in combined_01 if t.get('is_winner'))
            pnls = [float(t.get('pnl_r', 0) or 0) for t in combined_01]
            buckets.append(ConfluenceBucket(
                score=0,  # Representative score
                score_label="0-1",
                trade_count=len(combined_01),
                wins=wins,
                losses=len(combined_01) - wins,
                win_rate=wins / len(combined_01) if combined_01 else 0,
                avg_pnl_r=sum(pnls) / len(pnls) if pnls else 0,
                total_pnl_r=sum(pnls)
            ))

        # Individual buckets for 2-7
        for score in range(2, 8):
            group = score_groups[score]
            if group:
                wins = sum(1 for t in group if t.get('is_winner'))
                pnls = [float(t.get('pnl_r', 0) or 0) for t in group]
                buckets.append(ConfluenceBucket(
                    score=score,
                    score_label=str(score),
                    trade_count=len(group),
                    wins=wins,
                    losses=len(group) - wins,
                    win_rate=wins / len(group) if group else 0,
                    avg_pnl_r=sum(pnls) / len(pnls) if pnls else 0,
                    total_pnl_r=sum(pnls)
                ))

        return buckets

    def _find_min_positive_expectancy_score(self, buckets: List[ConfluenceBucket]) -> int:
        """Find minimum score that has positive expectancy."""
        for bucket in buckets:
            if bucket.avg_pnl_r > 0:
                return bucket.score
        return 7  # Default to max if none found

    def _calculate_score_threshold_stats(self, trades: List[Dict], threshold: int = 6) -> Tuple[float, int]:
        """Calculate stats for trades with score >= threshold."""
        high_score_trades = [t for t in trades if t.get('_confluence_score', 0) >= threshold]

        if not high_score_trades:
            return (0.0, 0)

        wins = sum(1 for t in high_score_trades if t.get('is_winner'))
        win_rate = wins / len(high_score_trades)

        return (win_rate, len(high_score_trades))
