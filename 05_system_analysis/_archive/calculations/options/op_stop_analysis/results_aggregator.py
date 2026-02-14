"""
Options Stop Analysis Results Aggregator

Aggregates simulation results by stop type, model, contract type.
"""

import pandas as pd
from typing import Dict, List, Any

from .stop_types import OPTIONS_STOP_TYPES, STOP_TYPE_ORDER


def aggregate_by_stop_type(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results by stop type.

    Returns DataFrame with columns:
    - Stop Type: Display name
    - n: Trade count
    - Wins: Win count
    - Losses: Loss count
    - Win Rate %: Win percentage
    - Avg R (Win): Average R on winners
    - Avg R (All): Average R overall (expectancy)
    - Stop Hit %: Percentage of trades where stop was hit
    """
    rows = []

    for stop_type in STOP_TYPE_ORDER:
        type_results = results.get(stop_type, [])

        if not type_results:
            continue

        n = len(type_results)

        # Count outcomes
        wins = sum(1 for r in type_results if r['outcome'] == 'WIN')
        losses = sum(1 for r in type_results if r['outcome'] == 'LOSS')
        stop_hits = sum(1 for r in type_results if r['stop_hit'])

        # Calculate averages
        r_values = [r['r_achieved'] for r in type_results]
        avg_r_all = sum(r_values) / len(r_values) if r_values else 0

        win_r_values = [r['r_achieved'] for r in type_results if r['outcome'] == 'WIN']
        avg_r_win = sum(win_r_values) / len(win_r_values) if win_r_values else 0

        rows.append({
            'Stop Type': OPTIONS_STOP_TYPES[stop_type]['display_name'],
            'stop_type_key': stop_type,
            'Stop %': OPTIONS_STOP_TYPES[stop_type]['loss_pct'],
            'n': n,
            'Wins': wins,
            'Losses': losses,
            'Win Rate %': (wins / n) * 100 if n > 0 else 0,
            'Stop Hit %': (stop_hits / n) * 100 if n > 0 else 0,
            'Avg R (Win)': avg_r_win,
            'Avg R (All)': avg_r_all,
            'Expectancy': avg_r_all
        })

    return pd.DataFrame(rows)


def aggregate_by_model_contract(
    results: Dict[str, List[Dict[str, Any]]]
) -> pd.DataFrame:
    """
    Aggregate results by model and contract type for each stop type.
    """
    rows = []

    for stop_type in STOP_TYPE_ORDER:
        type_results = results.get(stop_type, [])

        if not type_results:
            continue

        # Group by model and contract_type
        df = pd.DataFrame(type_results)

        if 'model' not in df.columns or 'contract_type' not in df.columns:
            continue

        for (model, contract), group in df.groupby(['model', 'contract_type']):
            n = len(group)
            wins = sum(1 for _, r in group.iterrows() if r['outcome'] == 'WIN')

            r_values = group['r_achieved'].tolist()
            avg_r = sum(r_values) / len(r_values) if r_values else 0

            rows.append({
                'Stop Type': OPTIONS_STOP_TYPES[stop_type]['short_name'],
                'stop_type_key': stop_type,
                'Model': model,
                'Contract': contract,
                'n': n,
                'Win Rate %': (wins / n) * 100 if n > 0 else 0,
                'Expectancy': avg_r
            })

    return pd.DataFrame(rows)


def find_best_stop_type(
    summary_df: pd.DataFrame,
    metric: str = 'Expectancy'
) -> Dict[str, Any]:
    """
    Find the best performing stop type based on specified metric.

    Uses all available data (no minimum sample size filter).
    """
    if summary_df.empty:
        return {'stop_type': 'N/A', 'expectancy': 0}

    best_idx = summary_df[metric].idxmax()
    best_row = summary_df.loc[best_idx]

    return {
        'stop_type': best_row['Stop Type'],
        'stop_type_key': best_row['stop_type_key'],
        'expectancy': best_row['Expectancy'],
        'win_rate': best_row['Win Rate %'],
        'n': best_row['n']
    }
