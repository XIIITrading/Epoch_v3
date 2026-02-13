"""
Epoch Backtest Journal - Confluence Analyzer
Calculates direction-relative factor alignment and confluence scoring.
XIII Trading LLC
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
    factor_name: str                    # e.g., "M5_Structure", "VWAP", "SMA_Stack"
    
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
    
    # Neutral cases (structure = NEUTRAL, VWAP = AT, etc.)
    neutral_trades: int
    neutral_wins: int
    neutral_win_rate: float
    
    # Edge calculation
    alignment_edge: float               # aligned_win_rate - misaligned_win_rate
    edge_rank: int = 0                  # Rank by edge (1 = highest edge)


@dataclass
class ConfluenceBucket:
    """Stats for one confluence score level."""
    score: int                          # 0-7
    score_label: str                    # "0-1", "2", "3", etc.
    trade_count: int
    wins: int
    losses: int
    win_rate: float
    avg_pnl_r: float
    total_pnl_r: float


@dataclass
class AnalysisResult:
    """Complete confluence analysis output."""
    start_date: Optional[date]
    end_date: Optional[date]
    total_trades: int
    trades_with_entry_data: int
    baseline_win_rate: float
    baseline_expectancy: float
    
    # Individual factor analysis (sorted by edge_rank)
    factor_alignments: List[FactorAlignment]
    
    # Confluence curve (the key output)
    confluence_buckets: List[ConfluenceBucket]
    
    # Summary metrics for headlines
    min_score_for_positive_expectancy: Optional[int]  # e.g., 5
    score_6_plus_win_rate: float
    score_6_plus_trades: int
    score_5_plus_win_rate: float
    score_5_plus_trades: int
    
    # Raw data with calculated alignments for Excel export
    raw_data: List[Dict] = field(default_factory=list)


class ConfluenceAnalyzer:
    """
    Analyzes direction-relative factor alignment and confluence scoring.
    
    For each factor, determines if it was ALIGNED or MISALIGNED with trade direction.
    Calculates confluence score (0-8) as sum of aligned factors.
    
    ALIGNMENT LOGIC:
    - For LONG trades: BULL structure, ABOVE VWAP, BULLISH SMA, BULL delta = aligned
    - For SHORT trades: BEAR structure, BELOW VWAP, BEARISH SMA, BEAR delta = aligned
    - Volume Trend: INCREASING or FLAT = aligned for both directions
    """
    
    # The 8 factors for confluence scoring
    FACTORS = [
        'm5_structure',
        'm15_structure', 
        'h1_structure',
        'h4_structure',
        'vwap',
        'sma_stack',
        'volume',
        'volume_delta'
    ]
    
    # Display names for factors
    FACTOR_DISPLAY_NAMES = {
        'm5_structure': 'M5 Structure',
        'm15_structure': 'M15 Structure',
        'h1_structure': 'H1 Structure',
        'h4_structure': 'H4 Structure',
        'vwap': 'VWAP Position',
        'sma_stack': 'SMA Stack',
        'volume': 'Volume Trend',
        'volume_delta': 'Volume Delta'
    }
    
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
        
        # Filter trades with entry data (m5_structure as indicator)
        trades_with_data = [t for t in trades if t.get('m5_structure') is not None]
        
        if not trades_with_data:
            return self._empty_result(actual_start, actual_end, total_trades=len(trades))
        
        # Calculate baseline statistics
        baseline_win_rate = self._calculate_win_rate(trades_with_data)
        baseline_expectancy = self._calculate_expectancy(trades_with_data)
        
        # For each trade, calculate alignments and confluence score
        enriched_trades = []
        for trade in trades_with_data:
            alignments = self._calculate_alignments(trade)
            confluence_score = self._calculate_confluence_score(alignments)
            
            # Store alignment results in trade dict for later use
            enriched_trade = {
                **trade,
                '_alignments': alignments,
                '_confluence_score': confluence_score
            }
            enriched_trades.append(enriched_trade)
        
        # Aggregate factor alignment stats
        factor_alignments = self._aggregate_factor_stats(enriched_trades)
        
        # Aggregate confluence buckets
        confluence_buckets = self._aggregate_confluence_buckets(enriched_trades)
        
        # Calculate summary metrics
        min_score_positive = self._find_min_positive_expectancy_score(confluence_buckets)
        score_6_plus = self._calculate_score_threshold_stats(enriched_trades, threshold=6)
        score_5_plus = self._calculate_score_threshold_stats(enriched_trades, threshold=5)
        
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
            raw_data=enriched_trades
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
            min_score_for_positive_expectancy=None,
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
    
    def _calculate_alignments(self, trade: Dict) -> Dict[str, Dict]:
        """
        Calculate alignment status for each factor based on trade direction.
        
        Returns dict: factor_name -> {'aligned': bool, 'neutral': bool}
        """
        direction = (trade.get('direction') or '').upper()
        is_long = direction == 'LONG'
        
        alignments = {}
        
        # Structure factors: BULL aligned for LONG, BEAR aligned for SHORT
        for tf in ['m5_structure', 'm15_structure', 'h1_structure', 'h4_structure']:
            value = (trade.get(tf) or '').upper()
            if value == 'NEUTRAL' or value == '':
                alignments[tf] = {'aligned': False, 'neutral': True}
            elif is_long:
                alignments[tf] = {'aligned': value == 'BULL', 'neutral': False}
            else:  # SHORT
                alignments[tf] = {'aligned': value == 'BEAR', 'neutral': False}
        
        # VWAP: ABOVE aligned for LONG, BELOW aligned for SHORT
        vwap = (trade.get('entry_vs_vwap') or '').upper()
        if vwap == 'AT' or vwap == '':
            alignments['vwap'] = {'aligned': False, 'neutral': True}
        elif is_long:
            alignments['vwap'] = {'aligned': vwap == 'ABOVE', 'neutral': False}
        else:
            alignments['vwap'] = {'aligned': vwap == 'BELOW', 'neutral': False}
        
        # SMA Stack: BULLISH aligned for LONG, BEARISH aligned for SHORT
        sma = (trade.get('sma9_vs_sma21') or '').upper()
        if sma == '':
            alignments['sma_stack'] = {'aligned': False, 'neutral': True}
        elif is_long:
            alignments['sma_stack'] = {'aligned': sma == 'BULLISH', 'neutral': False}
        else:
            alignments['sma_stack'] = {'aligned': sma == 'BEARISH', 'neutral': False}
        
        # Volume Trend: INCREASING or FLAT is aligned for both directions
        vol = (trade.get('volume_trend') or '').upper()
        if vol == '':
            alignments['volume'] = {'aligned': False, 'neutral': True}
        else:
            alignments['volume'] = {'aligned': vol in ['INCREASING', 'FLAT'], 'neutral': False}
        
        # Volume Delta: BULL aligned for LONG, BEAR aligned for SHORT
        vol_delta = (trade.get('volume_delta_class') or '').upper()
        if vol_delta == 'NEUTRAL' or vol_delta == '':
            alignments['volume_delta'] = {'aligned': False, 'neutral': True}
        elif is_long:
            alignments['volume_delta'] = {'aligned': vol_delta == 'BULL', 'neutral': False}
        else:
            alignments['volume_delta'] = {'aligned': vol_delta == 'BEAR', 'neutral': False}
        
        return alignments
    
    def _calculate_confluence_score(self, alignments: Dict[str, Dict]) -> int:
        """Sum of ALIGNED factors (0-7)."""
        return sum(1 for a in alignments.values() if a.get('aligned'))
    
    def _aggregate_factor_stats(self, trades: List[Dict]) -> List[FactorAlignment]:
        """Calculate aligned/misaligned win rates for each factor."""
        factor_stats = []
        
        for factor in self.FACTORS:
            aligned = [t for t in trades if t['_alignments'].get(factor, {}).get('aligned')]
            misaligned = [t for t in trades 
                         if not t['_alignments'].get(factor, {}).get('aligned') 
                         and not t['_alignments'].get(factor, {}).get('neutral')]
            neutral = [t for t in trades if t['_alignments'].get(factor, {}).get('neutral')]
            
            aligned_wins = sum(1 for t in aligned if t.get('is_winner'))
            misaligned_wins = sum(1 for t in misaligned if t.get('is_winner'))
            neutral_wins = sum(1 for t in neutral if t.get('is_winner'))
            
            aligned_wr = aligned_wins / len(aligned) if aligned else 0
            misaligned_wr = misaligned_wins / len(misaligned) if misaligned else 0
            neutral_wr = neutral_wins / len(neutral) if neutral else 0
            
            aligned_pnl = [float(t.get('pnl_r', 0) or 0) for t in aligned]
            misaligned_pnl = [float(t.get('pnl_r', 0) or 0) for t in misaligned]
            
            display_name = self.FACTOR_DISPLAY_NAMES.get(factor, factor)
            
            factor_stats.append(FactorAlignment(
                factor_name=display_name,
                aligned_trades=len(aligned),
                aligned_wins=aligned_wins,
                aligned_win_rate=aligned_wr,
                aligned_avg_pnl_r=sum(aligned_pnl) / len(aligned_pnl) if aligned_pnl else 0,
                misaligned_trades=len(misaligned),
                misaligned_wins=misaligned_wins,
                misaligned_win_rate=misaligned_wr,
                misaligned_avg_pnl_r=sum(misaligned_pnl) / len(misaligned_pnl) if misaligned_pnl else 0,
                neutral_trades=len(neutral),
                neutral_wins=neutral_wins,
                neutral_win_rate=neutral_wr,
                alignment_edge=aligned_wr - misaligned_wr
            ))
        
        # Sort by edge and assign ranks
        factor_stats.sort(key=lambda x: x.alignment_edge, reverse=True)
        for rank, f in enumerate(factor_stats, 1):
            f.edge_rank = rank
        
        return factor_stats
    
    def _aggregate_confluence_buckets(self, trades: List[Dict]) -> List[ConfluenceBucket]:
        """Aggregate stats by confluence score."""
        buckets = []
        
        # Group scores: 0-1 together (usually small sample), 2-8 individual
        score_groups = [
            (0, 1, '0-1'),
            (2, 2, '2'),
            (3, 3, '3'),
            (4, 4, '4'),
            (5, 5, '5'),
            (6, 6, '6'),
            (7, 7, '7'),
            (8, 8, '8'),
        ]
        
        for low, high, label in score_groups:
            bucket_trades = [t for t in trades if low <= t.get('_confluence_score', 0) <= high]
            if not bucket_trades:
                continue
            
            wins = sum(1 for t in bucket_trades if t.get('is_winner'))
            pnls = [float(t.get('pnl_r', 0) or 0) for t in bucket_trades]
            
            buckets.append(ConfluenceBucket(
                score=low if low == high else low,
                score_label=label,
                trade_count=len(bucket_trades),
                wins=wins,
                losses=len(bucket_trades) - wins,
                win_rate=wins / len(bucket_trades),
                avg_pnl_r=sum(pnls) / len(pnls),
                total_pnl_r=sum(pnls)
            ))
        
        return buckets
    
    def _find_min_positive_expectancy_score(self, buckets: List[ConfluenceBucket]) -> Optional[int]:
        """Find minimum score with positive expectancy."""
        for bucket in sorted(buckets, key=lambda x: x.score):
            if bucket.avg_pnl_r > 0:
                return bucket.score
        return None
    
    def _calculate_score_threshold_stats(self, trades: List[Dict], threshold: int = 6) -> Tuple[float, int]:
        """Calculate stats for trades with score >= threshold."""
        high_score_trades = [t for t in trades if t.get('_confluence_score', 0) >= threshold]
        
        if not high_score_trades:
            return (0.0, 0)
        
        wins = sum(1 for t in high_score_trades if t.get('is_winner'))
        win_rate = wins / len(high_score_trades)
        
        return (win_rate, len(high_score_trades))


if __name__ == "__main__":
    print("Confluence Analyzer module")
    print("\nUsage:")
    print("  from confluence_analysis.analyzer import ConfluenceAnalyzer")
    print("  analyzer = ConfluenceAnalyzer()")
    print("  result = analyzer.analyze()")