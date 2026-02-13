"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 03: SHARED INDICATORS
Input Adapters
XIII Trading LLC
================================================================================

Adapters for converting between different input formats:
- pandas DataFrame
- List of dicts
- List of objects with attributes

================================================================================
"""

from typing import List, Dict, Union, Any, Optional
import sys

# Try to import pandas, but don't require it
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


def normalize_bars(data: Any) -> List[Dict]:
    """
    Normalize bar data to a consistent List[Dict] format.

    Accepts:
    - pandas DataFrame with columns: open, high, low, close, volume
    - List of dicts with keys: open/open_price, high/high_price, etc.
    - List of objects with attributes

    Returns:
        List of dicts with normalized keys: open, high, low, close, volume
    """
    if data is None:
        return []

    # Handle pandas DataFrame
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        return _dataframe_to_bars(data)

    # Handle list
    if isinstance(data, list):
        if len(data) == 0:
            return []

        # Check first element to determine format
        first = data[0]

        if isinstance(first, dict):
            return _normalize_dict_bars(data)
        else:
            # Assume objects with attributes
            return _objects_to_bars(data)

    return []


def _dataframe_to_bars(df: 'pd.DataFrame') -> List[Dict]:
    """Convert pandas DataFrame to List[Dict]."""
    bars = []

    # Determine column names
    open_col = 'open' if 'open' in df.columns else 'open_price'
    high_col = 'high' if 'high' in df.columns else 'high_price'
    low_col = 'low' if 'low' in df.columns else 'low_price'
    close_col = 'close' if 'close' in df.columns else 'close_price'
    volume_col = 'volume'

    for idx, row in df.iterrows():
        bars.append({
            'open': float(row.get(open_col, 0)),
            'high': float(row.get(high_col, 0)),
            'low': float(row.get(low_col, 0)),
            'close': float(row.get(close_col, 0)),
            'volume': int(row.get(volume_col, 0)),
        })

    return bars


def _normalize_dict_bars(bars: List[Dict]) -> List[Dict]:
    """Normalize dict-based bars to consistent keys."""
    result = []

    for bar in bars:
        result.append({
            'open': _get_value(bar, 'open_price', 'open'),
            'high': _get_value(bar, 'high_price', 'high'),
            'low': _get_value(bar, 'low_price', 'low'),
            'close': _get_value(bar, 'close_price', 'close'),
            'volume': int(_get_value(bar, 'volume', default=0)),
        })

    return result


def _objects_to_bars(objects: List[Any]) -> List[Dict]:
    """Convert list of objects to List[Dict]."""
    bars = []

    for obj in objects:
        bars.append({
            'open': float(getattr(obj, 'open', getattr(obj, 'open_price', 0))),
            'high': float(getattr(obj, 'high', getattr(obj, 'high_price', 0))),
            'low': float(getattr(obj, 'low', getattr(obj, 'low_price', 0))),
            'close': float(getattr(obj, 'close', getattr(obj, 'close_price', 0))),
            'volume': int(getattr(obj, 'volume', 0)),
        })

    return bars


def _get_value(d: Dict, *keys: str, default: float = 0.0) -> float:
    """Get value from dict trying multiple keys."""
    for key in keys:
        if key in d and d[key] is not None:
            try:
                return float(d[key])
            except (ValueError, TypeError):
                continue
    return default


def bars_to_dataframe(bars: List[Dict]) -> Optional['pd.DataFrame']:
    """
    Convert List[Dict] bars to pandas DataFrame.

    Returns None if pandas is not available.
    """
    if not HAS_PANDAS:
        return None

    return pd.DataFrame(bars)
