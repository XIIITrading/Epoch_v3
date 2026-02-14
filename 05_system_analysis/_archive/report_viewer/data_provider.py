"""
================================================================================
EPOCH TRADING SYSTEM - System Analysis Data Provider
XIII Trading LLC
================================================================================

PURPOSE:
    Centralized data access for the report viewer dashboard.
    Fetches from Supabase, runs existing calculation functions,
    returns DataFrames ready for display in QTableWidget.

    No new calculations - reuses existing modules only.

================================================================================
"""

import sys
import pandas as pd
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal

# Add module root for imports
MODULE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MODULE_ROOT))

from data.supabase_client import get_client
from calculations.stop_analysis.results_aggregator import (
    aggregate_by_stop_type,
    aggregate_by_model_direction
)
from calculations.stop_analysis.ui_components import (
    _safe_float,
    _convert_supabase_to_results_format
)
from calculations.model.win_rate_by_model import calculate_win_rate_by_model
from calculations.trade_management.mfe_mae_sequence import (
    calculate_sequence_summary,
    calculate_sequence_by_model
)


# Stop type display names
STOP_TYPE_NAMES = {
    'zone_buffer': 'Zone + 5% Buffer',
    'prior_m1': 'Prior M1 H/L',
    'prior_m5': 'Prior M5 H/L',
    'm5_atr': 'M5 ATR (Close)',
    'm15_atr': 'M15 ATR (Close)',
    'fractal': 'M5 Fractal H/L'
}


class DataProvider:
    """
    Provides DataFrames for all report viewer tabs.

    All methods return pandas DataFrames ready for table display.
    Caches raw data after first fetch to avoid repeated DB calls.
    """

    def __init__(self):
        self._stop_data: Optional[List] = None
        self._stop_count: int = 0
        self._mfe_mae_data: Optional[List] = None
        self._results: Optional[Dict] = None
        self._summary_df: Optional[pd.DataFrame] = None

    def refresh(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Refresh all data from Supabase with optional date filtering.

        Args:
            date_from: Start date filter (inclusive). None = no lower bound.
            date_to: End date filter (inclusive). None = no upper bound.

        Returns dict with status info:
            {
                'stop_records': int,
                'unique_trades': int,
                'mfe_mae_records': int,
                'success': bool,
                'error': str or None
            }
        """
        try:
            client = get_client()

            # Fetch stop analysis data (with optional date filter)
            self._stop_data = client.fetch_stop_analysis(
                date_from=date_from, date_to=date_to
            )

            # Compute record count from data when filtered,
            # or from server count when unfiltered
            if date_from or date_to:
                self._stop_count = len(self._stop_data) if self._stop_data else 0
            else:
                self._stop_count = client.get_stop_analysis_count()

            # Fetch MFE/MAE potential data (with optional date filter)
            self._mfe_mae_data = client.fetch_mfe_mae_potential(
                date_from=date_from, date_to=date_to
            )

            # Pre-compute results dict (used by multiple tables)
            if self._stop_data:
                self._results = _convert_supabase_to_results_format(self._stop_data)
                self._summary_df = aggregate_by_stop_type(self._results)
                self._summary_df = self._summary_df.sort_values(
                    'Win Rate %', ascending=False
                ).reset_index(drop=True)
            else:
                self._results = None
                self._summary_df = None

            unique_trades = len(set(
                r.get('trade_id') for r in (self._stop_data or [])
            ))

            return {
                'stop_records': self._stop_count,
                'unique_trades': unique_trades,
                'mfe_mae_records': len(self._mfe_mae_data) if self._mfe_mae_data else 0,
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'stop_records': 0,
                'unique_trades': 0,
                'mfe_mae_records': 0,
                'success': False,
                'error': str(e)
            }

    @property
    def is_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._stop_data is not None

    @property
    def trade_count(self) -> int:
        """Number of unique trades."""
        if not self._stop_data:
            return 0
        return len(set(r.get('trade_id') for r in self._stop_data))

    @property
    def record_count(self) -> int:
        """Total stop analysis records."""
        return self._stop_count

    # =========================================================================
    # SECTION 1: Stop Type Comparison
    # =========================================================================

    def get_stop_type_comparison(self) -> Optional[pd.DataFrame]:
        """
        Get Stop Type Comparison table, ranked by Win Rate %.

        Returns DataFrame with columns:
            Stop Type, n, Avg Stop %, Stop Hit %, Win Rate %,
            Avg R (Win), Avg R (All), Net R (MFE), Expectancy
        """
        if self._summary_df is None:
            return None
        return self._summary_df.copy()

    def get_stop_type_order(self) -> List[str]:
        """Get stop type keys ordered by Win Rate % (from comparison table)."""
        if self._summary_df is None:
            return list(STOP_TYPE_NAMES.keys())
        return self._summary_df['stop_type_key'].tolist()

    # =========================================================================
    # SECTION 2: Win Rate by Model (per stop type)
    # =========================================================================

    def get_win_rate_by_model(self, stop_key: str) -> Optional[pd.DataFrame]:
        """
        Get Win Rate by Model for a specific stop type.

        Returns DataFrame with columns:
            Model, Wins, Losses, Total, Win%, Avg R (Win), Avg R (All), Expectancy
        """
        if self._results is None:
            return None

        outcomes = self._results.get(stop_key, [])
        if not outcomes:
            return None

        stop_name = STOP_TYPE_NAMES.get(stop_key, stop_key)
        model_df = calculate_win_rate_by_model(outcomes, stop_name)

        if model_df.empty or model_df['Total'].sum() == 0:
            return None

        return model_df

    def get_all_win_rate_by_model(self) -> Dict[str, pd.DataFrame]:
        """
        Get Win Rate by Model for all stop types, ordered by Win Rate %.

        Returns dict: {stop_key: DataFrame}
        """
        result = {}
        for stop_key in self.get_stop_type_order():
            df = self.get_win_rate_by_model(stop_key)
            if df is not None:
                result[stop_key] = df
        return result

    # =========================================================================
    # SECTION 3: Model-Direction Grid
    # =========================================================================

    def get_model_direction_grid(self) -> Optional[pd.DataFrame]:
        """
        Get Model-Direction win rate grid.

        Returns DataFrame with columns:
            Stop Type, EPCH01-L, EPCH01-S, EPCH02-L, EPCH02-S,
            EPCH03-L, EPCH03-S, EPCH04-L, EPCH04-S

        Rows ordered by Win Rate % from Stop Type Comparison.
        """
        if self._results is None:
            return None

        grid_df = aggregate_by_model_direction(self._results)
        if grid_df.empty:
            return None

        # Reorder rows to match stop type comparison ranking
        ordered_names = [
            STOP_TYPE_NAMES.get(k, k) for k in self.get_stop_type_order()
        ]
        grid_df['_sort'] = grid_df['Stop Type'].apply(
            lambda x: ordered_names.index(x) if x in ordered_names else 99
        )
        grid_df = grid_df.sort_values('_sort').drop(columns='_sort').reset_index(drop=True)

        return grid_df

    # =========================================================================
    # SECTION 4: MFE/MAE Sequence Analysis
    # =========================================================================

    def get_mfe_mae_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get MFE/MAE sequence overall summary.

        Returns dict with keys:
            total_trades, mfe_first_rate, mfe_first_count, mae_first_count,
            median_time_to_mfe, median_time_to_mae,
            pct_mfe_under_30min, pct_mfe_under_60min
        """
        if not self._mfe_mae_data:
            return None
        summary = calculate_sequence_summary(self._mfe_mae_data)
        if summary.get('total_trades', 0) == 0:
            return None
        return summary

    def get_mfe_mae_by_model(self) -> Optional[pd.DataFrame]:
        """
        Get MFE/MAE sequence breakdown by model-direction.

        Returns DataFrame with columns:
            model, direction, n_trades, p_mfe_first, median_time_mfe,
            median_time_mae, median_time_delta, mc_confidence
        """
        if not self._mfe_mae_data:
            return None
        model_df = calculate_sequence_by_model(self._mfe_mae_data)
        if model_df.empty:
            return None
        return model_df
