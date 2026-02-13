"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Analysis Calculators
XIII Trading LLC
================================================================================

Individual analyzer classes for each analysis table.

================================================================================
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging
import sys
from pathlib import Path

# Path structure: analysis/ -> ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
# Need to go up 4 levels from this file to reach 12_system_analysis
_system_analysis_dir = str(Path(__file__).parent.parent.parent.parent.resolve())
if _system_analysis_dir not in sys.path:
    sys.path.insert(0, _system_analysis_dir)

from config import CONTINUATION_MODELS, REJECTION_MODELS

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


# =============================================================================
# TABLE 1: Direction Analyzer
# =============================================================================
class DirectionAnalyzer(BaseAnalyzer):
    """Analyze win rates by direction (LONG vs SHORT)."""

    def get_table_name(self) -> str:
        return 'ramp_analysis_direction'

    def get_upsert_columns(self) -> List[str]:
        return [
            'direction', 'total_trades', 'wins', 'losses', 'win_rate',
            'avg_r_achieved', 'avg_mfe_distance', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['direction', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by direction."""
        data = self.fetch_macro_data()
        if not data:
            return []

        # Group by direction
        by_direction = defaultdict(list)
        for row in data:
            by_direction[row['direction']].append(row)

        results = []
        for direction, trades in by_direction.items():
            stats = self.calculate_win_rate(trades)
            results.append({
                'direction': direction,
                'total_trades': stats['total_trades'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': stats['win_rate'],
                'avg_r_achieved': stats['avg_r_achieved'],
                'avg_mfe_distance': stats['avg_mfe_distance'],
                'is_significant': stats['is_significant'],
                'stop_type': self.stop_type,
            })

        return results


# =============================================================================
# TABLE 2: Trade Type Analyzer
# =============================================================================
class TradeTypeAnalyzer(BaseAnalyzer):
    """Analyze win rates by trade type (CONTINUATION vs REJECTION)."""

    def get_table_name(self) -> str:
        return 'ramp_analysis_trade_type'

    def get_upsert_columns(self) -> List[str]:
        return [
            'trade_type', 'models', 'total_trades', 'wins', 'losses', 'win_rate',
            'avg_r_achieved', 'avg_mfe_distance', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['trade_type', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by trade type."""
        data = self.fetch_macro_data()
        if not data:
            return []

        # Group by trade type
        continuation_trades = [r for r in data if r['model'] in CONTINUATION_MODELS]
        rejection_trades = [r for r in data if r['model'] in REJECTION_MODELS]

        results = []

        # Continuation
        stats = self.calculate_win_rate(continuation_trades)
        results.append({
            'trade_type': 'CONTINUATION',
            'models': ','.join(CONTINUATION_MODELS),
            'total_trades': stats['total_trades'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'win_rate': stats['win_rate'],
            'avg_r_achieved': stats['avg_r_achieved'],
            'avg_mfe_distance': stats['avg_mfe_distance'],
            'is_significant': stats['is_significant'],
            'stop_type': self.stop_type,
        })

        # Rejection
        stats = self.calculate_win_rate(rejection_trades)
        results.append({
            'trade_type': 'REJECTION',
            'models': ','.join(REJECTION_MODELS),
            'total_trades': stats['total_trades'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'win_rate': stats['win_rate'],
            'avg_r_achieved': stats['avg_r_achieved'],
            'avg_mfe_distance': stats['avg_mfe_distance'],
            'is_significant': stats['is_significant'],
            'stop_type': self.stop_type,
        })

        return results


# =============================================================================
# TABLE 3: Model Analyzer
# =============================================================================
class ModelAnalyzer(BaseAnalyzer):
    """Analyze win rates by individual model."""

    def get_table_name(self) -> str:
        return 'ramp_analysis_model'

    def get_upsert_columns(self) -> List[str]:
        return [
            'model', 'trade_type', 'zone_type', 'total_trades', 'wins', 'losses',
            'win_rate', 'avg_r_achieved', 'avg_mfe_distance', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['model', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by model."""
        data = self.fetch_macro_data()
        if not data:
            return []

        # Group by model
        by_model = defaultdict(list)
        for row in data:
            by_model[row['model']].append(row)

        results = []
        for model, trades in by_model.items():
            stats = self.calculate_win_rate(trades)
            results.append({
                'model': model,
                'trade_type': self.get_trade_type(model),
                'zone_type': self.get_zone_type(model),
                'total_trades': stats['total_trades'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': stats['win_rate'],
                'avg_r_achieved': stats['avg_r_achieved'],
                'avg_mfe_distance': stats['avg_mfe_distance'],
                'is_significant': stats['is_significant'],
                'stop_type': self.stop_type,
            })

        return results


# =============================================================================
# TABLE 4: Model + Direction Analyzer
# =============================================================================
class ModelDirectionAnalyzer(BaseAnalyzer):
    """Analyze win rates by model + direction combination."""

    def get_table_name(self) -> str:
        return 'ramp_analysis_model_direction'

    def get_upsert_columns(self) -> List[str]:
        return [
            'model', 'direction', 'trade_type', 'zone_type', 'total_trades',
            'wins', 'losses', 'win_rate', 'avg_r_achieved', 'avg_mfe_distance',
            'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['model', 'direction', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by model + direction."""
        data = self.fetch_macro_data()
        if not data:
            return []

        # Group by model + direction
        by_combo = defaultdict(list)
        for row in data:
            key = (row['model'], row['direction'])
            by_combo[key].append(row)

        results = []
        for (model, direction), trades in by_combo.items():
            stats = self.calculate_win_rate(trades)
            results.append({
                'model': model,
                'direction': direction,
                'trade_type': self.get_trade_type(model),
                'zone_type': self.get_zone_type(model),
                'total_trades': stats['total_trades'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': stats['win_rate'],
                'avg_r_achieved': stats['avg_r_achieved'],
                'avg_mfe_distance': stats['avg_mfe_distance'],
                'is_significant': stats['is_significant'],
                'stop_type': self.stop_type,
            })

        return results


# =============================================================================
# TABLE 5: Indicator Trend Analyzer
# =============================================================================
class IndicatorTrendAnalyzer(BaseAnalyzer):
    """Analyze win rates by indicator trend state (RISING/FALLING/FLAT)."""

    # Indicators with trend columns
    TREND_INDICATORS = [
        'candle_range_pct',
        'vol_delta',
        'vol_roc',
        'sma_spread',
        'sma_momentum_ratio',
        'long_score',
        'short_score',
    ]

    # Groupings to analyze
    GROUPINGS = [
        ('direction', lambda r: r['direction']),
        ('trade_type', lambda r: 'CONTINUATION' if r['model'] in CONTINUATION_MODELS else 'REJECTION'),
        ('model', lambda r: r['model']),
        ('model_direction', lambda r: f"{r['model']}_{r['direction']}"),
    ]

    def get_table_name(self) -> str:
        return 'ramp_analysis_indicator_trend'

    def get_upsert_columns(self) -> List[str]:
        return [
            'grouping_type', 'grouping_value', 'indicator', 'trend_state',
            'total_trades', 'wins', 'losses', 'win_rate', 'baseline_win_rate',
            'lift_vs_baseline', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['grouping_type', 'grouping_value', 'indicator', 'trend_state', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by indicator trend state for each grouping."""
        data = self.fetch_macro_data()
        if not data:
            return []

        results = []

        for grouping_type, grouping_fn in self.GROUPINGS:
            # Group data
            by_group = defaultdict(list)
            for row in data:
                group_val = grouping_fn(row)
                by_group[group_val].append(row)

            # For each group, calculate baseline and indicator stats
            for group_val, trades in by_group.items():
                baseline_stats = self.calculate_win_rate(trades)
                baseline_wr = baseline_stats['win_rate']

                # For each indicator
                for indicator in self.TREND_INDICATORS:
                    trend_col = f'ramp_trend_{indicator}'

                    # Group by trend state
                    by_state = defaultdict(list)
                    for t in trades:
                        state = t.get(trend_col)
                        if state:
                            by_state[state].append(t)

                    # Calculate stats for each state
                    for state, state_trades in by_state.items():
                        stats = self.calculate_win_rate(state_trades)
                        lift = self.calculate_lift(stats['win_rate'], baseline_wr)

                        results.append({
                            'grouping_type': grouping_type,
                            'grouping_value': group_val,
                            'indicator': indicator,
                            'trend_state': state,
                            'total_trades': stats['total_trades'],
                            'wins': stats['wins'],
                            'losses': stats['losses'],
                            'win_rate': stats['win_rate'],
                            'baseline_win_rate': baseline_wr,
                            'lift_vs_baseline': lift,
                            'is_significant': stats['is_significant'],
                            'stop_type': self.stop_type,
                        })

        return results


# =============================================================================
# TABLE 6: Indicator Momentum Analyzer
# =============================================================================
class IndicatorMomentumAnalyzer(BaseAnalyzer):
    """Analyze win rates by indicator momentum state (BUILDING/FADING/STABLE)."""

    # Indicators with momentum columns
    MOMENTUM_INDICATORS = [
        'candle_range_pct',
        'vol_delta',
        'vol_roc',
        'sma_spread',
        'sma_momentum_ratio',
        'long_score',
        'short_score',
    ]

    # Same groupings as trend analyzer
    GROUPINGS = IndicatorTrendAnalyzer.GROUPINGS

    def get_table_name(self) -> str:
        return 'ramp_analysis_indicator_momentum'

    def get_upsert_columns(self) -> List[str]:
        return [
            'grouping_type', 'grouping_value', 'indicator', 'momentum_state',
            'total_trades', 'wins', 'losses', 'win_rate', 'baseline_win_rate',
            'lift_vs_baseline', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['grouping_type', 'grouping_value', 'indicator', 'momentum_state', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by indicator momentum state for each grouping."""
        data = self.fetch_macro_data()
        if not data:
            return []

        results = []

        for grouping_type, grouping_fn in self.GROUPINGS:
            by_group = defaultdict(list)
            for row in data:
                group_val = grouping_fn(row)
                by_group[group_val].append(row)

            for group_val, trades in by_group.items():
                baseline_stats = self.calculate_win_rate(trades)
                baseline_wr = baseline_stats['win_rate']

                for indicator in self.MOMENTUM_INDICATORS:
                    momentum_col = f'ramp_momentum_{indicator}'

                    by_state = defaultdict(list)
                    for t in trades:
                        state = t.get(momentum_col)
                        if state:
                            by_state[state].append(t)

                    for state, state_trades in by_state.items():
                        stats = self.calculate_win_rate(state_trades)
                        lift = self.calculate_lift(stats['win_rate'], baseline_wr)

                        results.append({
                            'grouping_type': grouping_type,
                            'grouping_value': group_val,
                            'indicator': indicator,
                            'momentum_state': state,
                            'total_trades': stats['total_trades'],
                            'wins': stats['wins'],
                            'losses': stats['losses'],
                            'win_rate': stats['win_rate'],
                            'baseline_win_rate': baseline_wr,
                            'lift_vs_baseline': lift,
                            'is_significant': stats['is_significant'],
                            'stop_type': self.stop_type,
                        })

        return results


# =============================================================================
# TABLE 7: Structure Consistency Analyzer
# =============================================================================
class StructureConsistencyAnalyzer(BaseAnalyzer):
    """Analyze win rates by structure consistency state."""

    STRUCTURE_INDICATORS = ['m15', 'h1']
    GROUPINGS = IndicatorTrendAnalyzer.GROUPINGS

    def get_table_name(self) -> str:
        return 'ramp_analysis_structure_consistency'

    def get_upsert_columns(self) -> List[str]:
        return [
            'grouping_type', 'grouping_value', 'indicator', 'consistency_state',
            'total_trades', 'wins', 'losses', 'win_rate', 'baseline_win_rate',
            'lift_vs_baseline', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['grouping_type', 'grouping_value', 'indicator', 'consistency_state', 'stop_type']

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by structure consistency state."""
        data = self.fetch_macro_data()
        if not data:
            return []

        results = []

        for grouping_type, grouping_fn in self.GROUPINGS:
            by_group = defaultdict(list)
            for row in data:
                group_val = grouping_fn(row)
                by_group[group_val].append(row)

            for group_val, trades in by_group.items():
                baseline_stats = self.calculate_win_rate(trades)
                baseline_wr = baseline_stats['win_rate']

                for indicator in self.STRUCTURE_INDICATORS:
                    structure_col = f'ramp_structure_{indicator}'

                    by_state = defaultdict(list)
                    for t in trades:
                        state = t.get(structure_col)
                        if state:
                            by_state[state].append(t)

                    for state, state_trades in by_state.items():
                        stats = self.calculate_win_rate(state_trades)
                        lift = self.calculate_lift(stats['win_rate'], baseline_wr)

                        results.append({
                            'grouping_type': grouping_type,
                            'grouping_value': group_val,
                            'indicator': indicator,
                            'consistency_state': state,
                            'total_trades': stats['total_trades'],
                            'wins': stats['wins'],
                            'losses': stats['losses'],
                            'win_rate': stats['win_rate'],
                            'baseline_win_rate': baseline_wr,
                            'lift_vs_baseline': lift,
                            'is_significant': stats['is_significant'],
                            'stop_type': self.stop_type,
                        })

        return results


# =============================================================================
# TABLE 8: Entry Snapshot Analyzer
# =============================================================================
class EntrySnapshotAnalyzer(BaseAnalyzer):
    """Analyze win rates by entry bar indicator values (bucketed)."""

    # Define buckets for each indicator
    INDICATOR_BUCKETS = {
        'long_score': [
            ('LOW (0-2)', 0, 2),
            ('MID (3-4)', 3, 4),
            ('HIGH (5-7)', 5, 7),
        ],
        'short_score': [
            ('LOW (0-2)', 0, 2),
            ('MID (3-4)', 3, 4),
            ('HIGH (5-7)', 5, 7),
        ],
        'vol_roc': [
            ('NEGATIVE', -999999, 0),
            ('LOW (0-30)', 0, 30),
            ('HIGH (30+)', 30, 999999),
        ],
        'vol_delta': [
            ('STRONG NEG', -999999999, -100000),
            ('WEAK NEG', -100000, 0),
            ('WEAK POS', 0, 100000),
            ('STRONG POS', 100000, 999999999),
        ],
        'candle_range_pct': [
            ('LOW (<0.10)', 0, 0.10),
            ('MID (0.10-0.20)', 0.10, 0.20),
            ('HIGH (0.20+)', 0.20, 999),
        ],
    }

    GROUPINGS = IndicatorTrendAnalyzer.GROUPINGS

    def get_table_name(self) -> str:
        return 'ramp_analysis_entry_snapshot'

    def get_upsert_columns(self) -> List[str]:
        return [
            'grouping_type', 'grouping_value', 'indicator', 'bucket',
            'bucket_min', 'bucket_max', 'total_trades', 'wins', 'losses',
            'win_rate', 'baseline_win_rate', 'lift_vs_baseline',
            'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['grouping_type', 'grouping_value', 'indicator', 'bucket', 'stop_type']

    def _get_bucket(self, value: float, buckets: List[tuple]) -> Optional[tuple]:
        """Find the bucket for a value."""
        if value is None:
            return None
        for bucket_name, min_val, max_val in buckets:
            if min_val <= value <= max_val:
                return (bucket_name, min_val, max_val)
        return None

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate win rates by entry bar indicator buckets."""
        data = self.fetch_macro_data()
        if not data:
            return []

        results = []

        for grouping_type, grouping_fn in self.GROUPINGS:
            by_group = defaultdict(list)
            for row in data:
                group_val = grouping_fn(row)
                by_group[group_val].append(row)

            for group_val, trades in by_group.items():
                baseline_stats = self.calculate_win_rate(trades)
                baseline_wr = baseline_stats['win_rate']

                for indicator, buckets in self.INDICATOR_BUCKETS.items():
                    entry_col = f'entry_{indicator}'

                    # Group by bucket
                    by_bucket = defaultdict(list)
                    for t in trades:
                        val = t.get(entry_col)
                        bucket_info = self._get_bucket(val, buckets)
                        if bucket_info:
                            by_bucket[bucket_info].append(t)

                    for bucket_info, bucket_trades in by_bucket.items():
                        bucket_name, bucket_min, bucket_max = bucket_info
                        stats = self.calculate_win_rate(bucket_trades)
                        lift = self.calculate_lift(stats['win_rate'], baseline_wr)

                        results.append({
                            'grouping_type': grouping_type,
                            'grouping_value': group_val,
                            'indicator': indicator,
                            'bucket': bucket_name,
                            'bucket_min': bucket_min,
                            'bucket_max': bucket_max,
                            'total_trades': stats['total_trades'],
                            'wins': stats['wins'],
                            'losses': stats['losses'],
                            'win_rate': stats['win_rate'],
                            'baseline_win_rate': baseline_wr,
                            'lift_vs_baseline': lift,
                            'is_significant': stats['is_significant'],
                            'stop_type': self.stop_type,
                        })

        return results


# =============================================================================
# TABLE 9: Progression Average Analyzer
# =============================================================================
class ProgressionAvgAnalyzer(BaseAnalyzer):
    """Calculate average indicator values at each bar position by outcome."""

    GROUPINGS = IndicatorTrendAnalyzer.GROUPINGS

    def get_table_name(self) -> str:
        return 'ramp_analysis_progression_avg'

    def get_upsert_columns(self) -> List[str]:
        return [
            'grouping_type', 'grouping_value', 'outcome', 'bars_to_entry',
            'avg_candle_range_pct', 'avg_vol_delta', 'avg_vol_roc',
            'avg_sma_spread', 'avg_sma_momentum_ratio', 'avg_long_score',
            'avg_short_score', 'sample_size', 'is_significant', 'stop_type'
        ]

    def get_conflict_columns(self) -> List[str]:
        return ['grouping_type', 'grouping_value', 'outcome', 'bars_to_entry', 'stop_type']

    def _safe_avg(self, values: List) -> Optional[float]:
        """Calculate average, handling None values."""
        valid = [v for v in values if v is not None]
        return sum(valid) / len(valid) if valid else None

    def calculate(self) -> List[Dict[str, Any]]:
        """Calculate average indicator values at each bar position."""
        # Get macro data for grouping info
        macro_data = self.fetch_macro_data()
        if not macro_data:
            return []

        # Build trade_id -> (group_val, outcome) mapping for each grouping
        trade_info = {}
        for row in macro_data:
            trade_info[row['trade_id']] = {
                'direction': row['direction'],
                'trade_type': 'CONTINUATION' if row['model'] in CONTINUATION_MODELS else 'REJECTION',
                'model': row['model'],
                'model_direction': f"{row['model']}_{row['direction']}",
                'outcome': row['outcome'],
            }

        # Fetch progression data
        prog_data = self.fetch_progression_data()
        if not prog_data:
            return []

        results = []

        for grouping_type, _ in self.GROUPINGS:
            # Group progression data
            # Key: (grouping_value, outcome, bars_to_entry)
            grouped = defaultdict(list)

            for p in prog_data:
                tid = p['trade_id']
                if tid not in trade_info:
                    continue

                info = trade_info[tid]
                group_val = info[grouping_type]
                outcome = info['outcome']
                bars = p['bars_to_entry']

                grouped[(group_val, outcome, bars)].append(p)

            # Calculate averages
            for (group_val, outcome, bars), rows in grouped.items():
                sample_size = len(rows)

                results.append({
                    'grouping_type': grouping_type,
                    'grouping_value': group_val,
                    'outcome': outcome,
                    'bars_to_entry': bars,
                    'avg_candle_range_pct': self._safe_avg([r.get('candle_range_pct') for r in rows]),
                    'avg_vol_delta': self._safe_avg([r.get('vol_delta') for r in rows]),
                    'avg_vol_roc': self._safe_avg([r.get('vol_roc') for r in rows]),
                    'avg_sma_spread': self._safe_avg([r.get('sma_spread') for r in rows]),
                    'avg_sma_momentum_ratio': self._safe_avg([r.get('sma_momentum_ratio') for r in rows]),
                    'avg_long_score': self._safe_avg([r.get('long_score') for r in rows]),
                    'avg_short_score': self._safe_avg([r.get('short_score') for r in rows]),
                    'sample_size': sample_size,
                    'is_significant': sample_size >= 30,
                    'stop_type': self.stop_type,
                })

        return results
