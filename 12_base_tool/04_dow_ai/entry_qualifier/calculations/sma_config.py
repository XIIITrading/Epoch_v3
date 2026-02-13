"""
SMA Configuration Calculations
Epoch Trading System v1 - XIII Trading LLC

Calculates SMA9, SMA21, configuration (BULLISH/BEARISH),
spread percentage, and price position.
"""
from typing import List, Optional, Tuple
from enum import Enum


class SMAConfig(Enum):
    """SMA configuration states."""
    BULLISH = "BULL"   # SMA9 > SMA21
    BEARISH = "BEAR"   # SMA9 < SMA21
    NEUTRAL = "FLAT"   # SMA9 == SMA21 (rare)


class PricePosition(Enum):
    """Price position relative to SMAs."""
    ABOVE_BOTH = "ABOVE"
    BETWEEN = "BTWN"
    BELOW_BOTH = "BELOW"


# Threshold for wide spread (indicates strong trend)
WIDE_SPREAD_THRESHOLD = 0.15  # 0.15%


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average.

    Args:
        prices: List of close prices
        period: SMA period

    Returns:
        SMA value, or None if insufficient data
    """
    if len(prices) < period:
        return None

    return sum(prices[-period:]) / period


def calculate_sma_spread_pct(sma9: float, sma21: float, price: float) -> float:
    """
    Calculate spread between SMA9 and SMA21 as percentage of price.

    Args:
        sma9: SMA9 value
        sma21: SMA21 value
        price: Reference price for percentage calculation

    Returns:
        Spread as percentage (e.g., 0.15 for 0.15%)
    """
    if price <= 0:
        return 0.0

    spread = abs(sma9 - sma21)
    return (spread / price) * 100


def get_sma_config(sma9: float, sma21: float) -> SMAConfig:
    """
    Determine SMA configuration.

    Args:
        sma9: SMA9 value
        sma21: SMA21 value

    Returns:
        SMAConfig enum value
    """
    if sma9 > sma21:
        return SMAConfig.BULLISH
    elif sma9 < sma21:
        return SMAConfig.BEARISH
    else:
        return SMAConfig.NEUTRAL


def get_price_position(price: float, sma9: float, sma21: float) -> PricePosition:
    """
    Determine price position relative to SMAs.

    Args:
        price: Current price
        sma9: SMA9 value
        sma21: SMA21 value

    Returns:
        PricePosition enum value
    """
    higher_sma = max(sma9, sma21)
    lower_sma = min(sma9, sma21)

    if price > higher_sma:
        return PricePosition.ABOVE_BOTH
    elif price < lower_sma:
        return PricePosition.BELOW_BOTH
    else:
        return PricePosition.BETWEEN


def is_wide_spread(spread_pct: float) -> bool:
    """
    Check if SMA spread indicates strong trend.

    Args:
        spread_pct: Spread as percentage

    Returns:
        True if spread >= 0.15%
    """
    return spread_pct >= WIDE_SPREAD_THRESHOLD


def format_sma_display(config: SMAConfig, spread_pct: float) -> str:
    """
    Format SMA config and spread for display.

    Args:
        config: SMA configuration
        spread_pct: Spread as percentage

    Returns:
        Formatted string like "BULL 0.15%"
    """
    return f"{config.value} {spread_pct:.2f}%"


def calculate_all_sma_configs(
    bars: List[dict],
    sma_short: int = 9,
    sma_long: int = 21
) -> List[dict]:
    """
    Calculate SMA configuration for all bars.

    Args:
        bars: List of bar dictionaries with 'close' or 'c' key
        sma_short: Short SMA period (default 9)
        sma_long: Long SMA period (default 21)

    Returns:
        List of dicts with SMA-related values
    """
    results = []
    closes = []

    for i, bar in enumerate(bars):
        close = bar.get('close', bar.get('c', 0))
        closes.append(close)

        # Need at least sma_long bars to calculate
        if i < sma_long - 1:
            results.append({
                'sma9': None,
                'sma21': None,
                'sma_config': None,
                'sma_spread_pct': None,
                'price_position': None,
                'sma_display': None
            })
        else:
            # Calculate SMAs
            sma9 = calculate_sma(closes, sma_short)
            sma21 = calculate_sma(closes, sma_long)

            if sma9 is not None and sma21 is not None:
                config = get_sma_config(sma9, sma21)
                spread_pct = calculate_sma_spread_pct(sma9, sma21, close)
                position = get_price_position(close, sma9, sma21)
                display = format_sma_display(config, spread_pct)

                results.append({
                    'sma9': sma9,
                    'sma21': sma21,
                    'sma_config': config,
                    'sma_spread_pct': spread_pct,
                    'price_position': position,
                    'sma_display': display
                })
            else:
                results.append({
                    'sma9': None,
                    'sma21': None,
                    'sma_config': None,
                    'sma_spread_pct': None,
                    'price_position': None,
                    'sma_display': None
                })

    return results
