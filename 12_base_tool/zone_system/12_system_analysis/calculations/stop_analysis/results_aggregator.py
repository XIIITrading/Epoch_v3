"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 12: INDICATOR ANALYSIS
Calculation: Results Aggregator for Stop Analysis (CALC-009)
XIII Trading LLC
================================================================================

PURPOSE:
    Aggregate individual trade results into summary statistics for each stop type.

OUTPUT METRICS:
    - n: Sample size
    - Avg Stop: Average stop distance as % of entry
    - Stop Hit %: How often the stop is triggered
    - Win Rate: % of trades reaching 1R before stop
    - Avg R (Win): Average R on winning trades
    - Avg R (All): Net R per trade
    - Expectancy: (win_rate * avg_win_r) - (loss_rate * 1R)

================================================================================
"""

import pandas as pd
from typing import List, Dict, Any, Optional


# Model type mapping
CONTINUATION_MODELS = ['EPCH01', 'EPCH1', 'EPCH03', 'EPCH3']
REJECTION_MODELS = ['EPCH02', 'EPCH2', 'EPCH04', 'EPCH4']


def _normalize_model(model: str) -> str:
    """Normalize model name to EPCHXX format."""
    if model is None:
        return 'UNKNOWN'
    model_map = {
        'EPCH1': 'EPCH01', 'EPCH2': 'EPCH02',
        'EPCH3': 'EPCH03', 'EPCH4': 'EPCH04'
    }
    return model_map.get(model, model)


def _get_model_type(model: str) -> str:
    """Determine if model is continuation or rejection."""
    normalized = _normalize_model(model)
    if normalized in ['EPCH01', 'EPCH03']:
        return 'Continuation'
    elif normalized in ['EPCH02', 'EPCH04']:
        return 'Rejection'
    return 'Unknown'


def _calculate_expectancy(df: pd.DataFrame) -> float:
    """
    Calculate expectancy: E = (win% * avg_win) - (loss% * 1R)
    """
    if len(df) == 0:
        return 0.0

    wins = len(df[df['r_achieved'] >= 1.0])
    losses = len(df[df['outcome'] == 'LOSS'])
    total = len(df)

    win_rate = wins / total if total > 0 else 0
    loss_rate = losses / total if total > 0 else 0

    # Average R on winners
    winners_df = df[df['outcome'] == 'WIN']
    avg_r_winners = winners_df['r_achieved'].mean() if len(winners_df) > 0 else 0

    if pd.isna(avg_r_winners):
        avg_r_winners = 0

    expectancy = (win_rate * avg_r_winners) - (loss_rate * 1.0)
    return expectancy


def aggregate_by_stop_type(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results for each stop type into summary statistics.

    Parameters:
    -----------
    results : Dict[str, List[Dict]]
        Dictionary mapping stop_type to list of outcome records

    Returns:
    --------
    pd.DataFrame with columns:
        Stop Type, n, Avg Stop %, Stop Hit %, Win Rate %, Avg R (Win), Avg R (All), Expectancy
    """
    summary_rows = []

    stop_type_names = {
        'zone_buffer': 'Zone + 5% Buffer',
        'prior_m1': 'Prior M1 H/L',
        'prior_m5': 'Prior M5 H/L',
        'm5_atr': 'M5 ATR (Close)',
        'm15_atr': 'M15 ATR (Close)',
        'fractal': 'M5 Fractal H/L'
    }

    for stop_type in ['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal']:
        outcomes = results.get(stop_type, [])

        if not outcomes:
            summary_rows.append({
                'Stop Type': stop_type_names.get(stop_type, stop_type),
                'stop_type_key': stop_type,
                'n': 0,
                'Avg Stop %': 0.0,
                'Stop Hit %': 0.0,
                'Win Rate %': 0.0,
                'Avg R (Win)': 0.0,
                'Avg R (All)': 0.0,
                'Net R (MFE)': 0.0,
                'Expectancy': 0.0
            })
            continue

        df = pd.DataFrame(outcomes)
        total = len(df)

        # Basic stats
        stop_hit_count = df['stop_hit'].sum()
        stop_hit_pct = (stop_hit_count / total) * 100

        avg_stop_distance_pct = df['stop_distance_pct'].mean()

        # Win rate (1R+ achieved)
        wins = len(df[df['r_achieved'] >= 1.0])
        win_rate = (wins / total) * 100

        # R statistics
        winners_df = df[df['outcome'] == 'WIN']
        avg_r_winners = winners_df['r_achieved'].mean() if len(winners_df) > 0 else 0
        avg_r_all = df['r_achieved'].mean()

        # Handle NaN
        if pd.isna(avg_r_winners):
            avg_r_winners = 0
        if pd.isna(avg_r_all):
            avg_r_all = 0

        # Net R: Sum of r_achieved, with nulls imputed based on win/loss ratio
        # Nulls are distributed proportionally: wins get Avg R (Win), losses get -1.0R
        null_count = df['r_achieved'].isna().sum()
        non_null_sum = df['r_achieved'].dropna().sum()

        if null_count > 0 and total > 0:
            # Calculate win/loss ratio from non-null data
            win_rate_decimal = win_rate / 100  # Convert percentage to decimal
            loss_rate_decimal = stop_hit_pct / 100

            # Distribute nulls according to win/loss ratio
            null_wins = null_count * win_rate_decimal
            null_losses = null_count * loss_rate_decimal

            # Imputed R for nulls: wins at avg_r_winners, losses at -1.0R
            imputed_r = (null_wins * avg_r_winners) + (null_losses * -1.0)
            net_r = non_null_sum + imputed_r
        else:
            net_r = non_null_sum

        if pd.isna(net_r):
            net_r = 0

        # Expectancy
        expectancy = _calculate_expectancy(df)

        summary_rows.append({
            'Stop Type': stop_type_names.get(stop_type, stop_type),
            'stop_type_key': stop_type,
            'n': total,
            'Avg Stop %': round(avg_stop_distance_pct, 2),
            'Stop Hit %': round(stop_hit_pct, 1),
            'Win Rate %': round(win_rate, 1),
            'Avg R (Win)': round(avg_r_winners, 2),
            'Avg R (All)': round(avg_r_all, 2),
            'Net R (MFE)': round(net_r, 2),
            'Expectancy': round(expectancy, 3)
        })

    return pd.DataFrame(summary_rows)


def aggregate_by_model_type(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results by continuation vs rejection model type.

    Parameters:
    -----------
    results : Dict[str, List[Dict]]
        Dictionary mapping stop_type to list of outcome records

    Returns:
    --------
    pd.DataFrame with columns:
        Stop Type, Model Type, n, Win Rate %, Expectancy
    """
    # Flatten all outcomes
    all_outcomes = []
    for stop_type, outcomes in results.items():
        for outcome in outcomes:
            outcome_copy = outcome.copy()
            outcome_copy['stop_type'] = stop_type
            outcome_copy['model_type'] = _get_model_type(outcome.get('model', ''))
            all_outcomes.append(outcome_copy)

    if not all_outcomes:
        return pd.DataFrame(columns=['Stop Type', 'Model Type', 'n', 'Win Rate %', 'Expectancy'])

    df = pd.DataFrame(all_outcomes)

    stop_type_names = {
        'zone_buffer': 'Zone + 5% Buffer',
        'prior_m1': 'Prior M1 H/L',
        'prior_m5': 'Prior M5 H/L',
        'm5_atr': 'M5 ATR (Close)',
        'm15_atr': 'M15 ATR (Close)',
        'fractal': 'M5 Fractal H/L'
    }

    rows = []
    for stop_type in ['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal']:
        for model_type in ['Continuation', 'Rejection']:
            subset = df[(df['stop_type'] == stop_type) & (df['model_type'] == model_type)]

            if len(subset) == 0:
                rows.append({
                    'Stop Type': stop_type_names.get(stop_type, stop_type),
                    'Model Type': model_type,
                    'n': 0,
                    'Win Rate %': 0.0,
                    'Expectancy': 0.0
                })
            else:
                wins = len(subset[subset['r_achieved'] >= 1.0])
                win_rate = (wins / len(subset)) * 100
                expectancy = _calculate_expectancy(subset)

                rows.append({
                    'Stop Type': stop_type_names.get(stop_type, stop_type),
                    'Model Type': model_type,
                    'n': len(subset),
                    'Win Rate %': round(win_rate, 1),
                    'Expectancy': round(expectancy, 3)
                })

    return pd.DataFrame(rows)


def aggregate_by_direction(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results by LONG vs SHORT direction.

    Parameters:
    -----------
    results : Dict[str, List[Dict]]
        Dictionary mapping stop_type to list of outcome records

    Returns:
    --------
    pd.DataFrame with columns:
        Stop Type, Direction, n, Win Rate %, Expectancy
    """
    # Flatten all outcomes
    all_outcomes = []
    for stop_type, outcomes in results.items():
        for outcome in outcomes:
            outcome_copy = outcome.copy()
            outcome_copy['stop_type'] = stop_type
            all_outcomes.append(outcome_copy)

    if not all_outcomes:
        return pd.DataFrame(columns=['Stop Type', 'Direction', 'n', 'Win Rate %', 'Expectancy'])

    df = pd.DataFrame(all_outcomes)

    stop_type_names = {
        'zone_buffer': 'Zone + 5% Buffer',
        'prior_m1': 'Prior M1 H/L',
        'prior_m5': 'Prior M5 H/L',
        'm5_atr': 'M5 ATR (Close)',
        'm15_atr': 'M15 ATR (Close)',
        'fractal': 'M5 Fractal H/L'
    }

    rows = []
    for stop_type in ['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal']:
        for direction in ['LONG', 'SHORT']:
            subset = df[(df['stop_type'] == stop_type) & (df['direction'] == direction)]

            if len(subset) == 0:
                rows.append({
                    'Stop Type': stop_type_names.get(stop_type, stop_type),
                    'Direction': direction,
                    'n': 0,
                    'Win Rate %': 0.0,
                    'Expectancy': 0.0
                })
            else:
                wins = len(subset[subset['r_achieved'] >= 1.0])
                win_rate = (wins / len(subset)) * 100
                expectancy = _calculate_expectancy(subset)

                rows.append({
                    'Stop Type': stop_type_names.get(stop_type, stop_type),
                    'Direction': direction,
                    'n': len(subset),
                    'Win Rate %': round(win_rate, 1),
                    'Expectancy': round(expectancy, 3)
                })

    return pd.DataFrame(rows)


def aggregate_by_model_direction(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results by 8 model-direction combinations.

    Parameters:
    -----------
    results : Dict[str, List[Dict]]
        Dictionary mapping stop_type to list of outcome records

    Returns:
    --------
    pd.DataFrame with columns:
        Stop Type, EPCH01-L, EPCH01-S, EPCH02-L, EPCH02-S, EPCH03-L, EPCH03-S, EPCH04-L, EPCH04-S
    """
    # Flatten all outcomes
    all_outcomes = []
    for stop_type, outcomes in results.items():
        for outcome in outcomes:
            outcome_copy = outcome.copy()
            outcome_copy['stop_type'] = stop_type
            outcome_copy['model_normalized'] = _normalize_model(outcome.get('model', ''))
            outcome_copy['model_direction'] = f"{outcome_copy['model_normalized']}-{outcome.get('direction', 'L')[0]}"
            all_outcomes.append(outcome_copy)

    if not all_outcomes:
        return pd.DataFrame()

    df = pd.DataFrame(all_outcomes)

    stop_type_names = {
        'zone_buffer': 'Zone + 5% Buffer',
        'prior_m1': 'Prior M1 H/L',
        'prior_m5': 'Prior M5 H/L',
        'm5_atr': 'M5 ATR (Close)',
        'm15_atr': 'M15 ATR (Close)',
        'fractal': 'M5 Fractal H/L'
    }

    model_dirs = ['EPCH01-L', 'EPCH01-S', 'EPCH02-L', 'EPCH02-S',
                  'EPCH03-L', 'EPCH03-S', 'EPCH04-L', 'EPCH04-S']

    rows = []
    for stop_type in ['zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal']:
        row = {'Stop Type': stop_type_names.get(stop_type, stop_type)}

        for md in model_dirs:
            subset = df[(df['stop_type'] == stop_type) & (df['model_direction'] == md)]

            if len(subset) == 0:
                row[md] = '-'
            else:
                wins = len(subset[subset['r_achieved'] >= 1.0])
                win_rate = (wins / len(subset)) * 100
                row[md] = f"{win_rate:.1f}%"

        rows.append(row)

    return pd.DataFrame(rows)


def find_best_stop_type(
    summary_df: pd.DataFrame,
    metric: str = 'Expectancy'
) -> Dict[str, Any]:
    """
    Identify the best performing stop type based on specified metric.

    Parameters:
    -----------
    summary_df : pd.DataFrame
        Output from aggregate_by_stop_type()
    metric : str
        Metric to use for ranking ('Expectancy', 'Win Rate %', 'Avg R (All)')

    Returns:
    --------
    Dict with best stop type details
    """
    if summary_df.empty or metric not in summary_df.columns:
        return {
            'stop_type': 'N/A',
            'stop_type_key': None,
            'value': 0,
            'metric': metric
        }

    # Filter to stop types with data
    valid_df = summary_df[summary_df['n'] > 0].copy()

    if valid_df.empty:
        return {
            'stop_type': 'N/A',
            'stop_type_key': None,
            'value': 0,
            'metric': metric
        }

    # Find best
    best_idx = valid_df[metric].idxmax()
    best_row = valid_df.loc[best_idx]

    return {
        'stop_type': best_row['Stop Type'],
        'stop_type_key': best_row.get('stop_type_key', None),
        'value': best_row[metric],
        'metric': metric,
        'n': best_row['n'],
        'win_rate': best_row['Win Rate %'],
        'expectancy': best_row['Expectancy']
    }


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test data
    test_results = {
        'zone_buffer': [
            {'trade_id': 'T1', 'model': 'EPCH01', 'direction': 'LONG', 'stop_distance_pct': 0.5,
             'stop_hit': False, 'r_achieved': 2.0, 'outcome': 'WIN'},
            {'trade_id': 'T2', 'model': 'EPCH02', 'direction': 'SHORT', 'stop_distance_pct': 0.6,
             'stop_hit': True, 'r_achieved': -1.0, 'outcome': 'LOSS'},
            {'trade_id': 'T3', 'model': 'EPCH01', 'direction': 'LONG', 'stop_distance_pct': 0.5,
             'stop_hit': False, 'r_achieved': 1.5, 'outcome': 'WIN'},
        ],
        'prior_m1': [
            {'trade_id': 'T1', 'model': 'EPCH01', 'direction': 'LONG', 'stop_distance_pct': 0.3,
             'stop_hit': True, 'r_achieved': -1.0, 'outcome': 'LOSS'},
            {'trade_id': 'T2', 'model': 'EPCH02', 'direction': 'SHORT', 'stop_distance_pct': 0.4,
             'stop_hit': False, 'r_achieved': 3.0, 'outcome': 'WIN'},
            {'trade_id': 'T3', 'model': 'EPCH01', 'direction': 'LONG', 'stop_distance_pct': 0.35,
             'stop_hit': True, 'r_achieved': -1.0, 'outcome': 'LOSS'},
        ],
        'prior_m5': [],
        'm5_atr': [],
        'm15_atr': [],
        'fractal': []
    }

    print("Results Aggregator Test")
    print("=" * 70)

    # Test aggregate_by_stop_type
    summary = aggregate_by_stop_type(test_results)
    print("\nSummary by Stop Type:")
    print(summary.to_string(index=False))

    # Test find_best_stop_type
    best = find_best_stop_type(summary)
    print(f"\nBest Stop Type: {best['stop_type']} ({best['metric']}: {best['value']:.3f})")

    # Test aggregate_by_model_type
    model_type_df = aggregate_by_model_type(test_results)
    print("\nBreakdown by Model Type:")
    print(model_type_df.to_string(index=False))
