"""
================================================================================
EPOCH TRADING SYSTEM - OPTIONS CONTRACT SELECTOR
Modifiable Contract Selection Logic
XIII Trading LLC
================================================================================

This module contains the logic for selecting which options contract to use
for a given trade. The selection method can be modified directly in this file.

CURRENT STRATEGY: First In-The-Money (ITM)
- LONG trades: Buy ITM call (highest strike below entry price)
- SHORT trades: Buy ITM put (lowest strike above entry price)

TO MODIFY: Edit the select_contract() function or change SELECTION_METHOD.

================================================================================
"""

from datetime import date, timedelta
from typing import Optional, List
from dataclasses import dataclass

# Handle both relative and absolute imports
try:
    from .fetcher import OptionsChain, OptionsContract, build_options_ticker
    from .config import MIN_DAYS_TO_EXPIRY, DEFAULT_STRIKE_METHOD
except ImportError:
    from fetcher import OptionsChain, OptionsContract, build_options_ticker
    from config import MIN_DAYS_TO_EXPIRY, DEFAULT_STRIKE_METHOD


# =============================================================================
# SELECTION METHOD - MODIFY THIS TO CHANGE CONTRACT SELECTION STRATEGY
# =============================================================================
# Options: "FIRST_ITM", "ATM", "FIRST_OTM"
SELECTION_METHOD = DEFAULT_STRIKE_METHOD


@dataclass
class SelectedContract:
    """Result of contract selection."""
    contract: OptionsContract
    ticker: str
    selection_method: str
    selection_notes: str


def select_contract(
    chain: OptionsChain,
    entry_price: float,
    direction: str,
    trade_date: date,
    exit_date: date = None
) -> Optional[SelectedContract]:
    """
    Select an options contract for a trade.

    This is the main entry point for contract selection. Modify this function
    or the helper functions below to change selection logic.

    Args:
        chain: OptionsChain with available contracts
        entry_price: Entry price of the underlying
        direction: "LONG" or "SHORT"
        trade_date: Date of the trade
        exit_date: Exit date (defaults to trade_date if not provided)

    Returns:
        SelectedContract or None if no suitable contract found
    """
    if not chain or not chain.contracts:
        return None

    if exit_date is None:
        exit_date = trade_date

    # Determine contract type based on direction
    # LONG = Buy Call, SHORT = Buy Put
    contract_type = "call" if direction.upper() == "LONG" else "put"

    # Select expiration
    expiration = select_expiration(chain, exit_date)
    if not expiration:
        return None

    # Filter contracts by type and expiration
    valid_contracts = [
        c for c in chain.contracts
        if c.contract_type == contract_type and c.expiration == expiration
    ]

    if not valid_contracts:
        return None

    # Select strike based on method
    if SELECTION_METHOD == "FIRST_ITM":
        selected = select_first_itm(valid_contracts, entry_price, direction)
    elif SELECTION_METHOD == "ATM":
        selected = select_atm(valid_contracts, entry_price)
    elif SELECTION_METHOD == "FIRST_OTM":
        selected = select_first_otm(valid_contracts, entry_price, direction)
    else:
        # Default to ITM
        selected = select_first_itm(valid_contracts, entry_price, direction)

    if not selected:
        return None

    return SelectedContract(
        contract=selected,
        ticker=selected.ticker,
        selection_method=SELECTION_METHOD,
        selection_notes=f"Strike ${selected.strike} for {direction} at ${entry_price:.2f}"
    )


def select_expiration(chain: OptionsChain, exit_date: date) -> Optional[date]:
    """
    Select appropriate expiration date.

    Rules:
    1. Must expire AFTER exit_date
    2. Must have at least MIN_DAYS_TO_EXPIRY buffer

    Args:
        chain: OptionsChain with available expirations
        exit_date: Trade exit date

    Returns:
        Selected expiration date or None
    """
    min_expiry = exit_date + timedelta(days=MIN_DAYS_TO_EXPIRY)

    valid_expirations = [
        exp for exp in chain.get_expirations()
        if exp >= min_expiry
    ]

    if not valid_expirations:
        # Fallback: try any expiration after exit
        valid_expirations = [
            exp for exp in chain.get_expirations()
            if exp > exit_date
        ]

    if not valid_expirations:
        return None

    # Return closest valid expiration
    return min(valid_expirations)


# =============================================================================
# STRIKE SELECTION METHODS - Modify these to change behavior
# =============================================================================

def select_first_itm(
    contracts: List[OptionsContract],
    entry_price: float,
    direction: str
) -> Optional[OptionsContract]:
    """
    Select the first in-the-money contract (closest to ATM while still ITM).

    For LONG (calls): ITM = strike < entry_price
        Select highest strike that is still below entry price

    For SHORT (puts): ITM = strike > entry_price
        Select lowest strike that is still above entry price

    Args:
        contracts: List of contracts (already filtered by type/expiration)
        entry_price: Entry price of underlying
        direction: "LONG" or "SHORT"

    Returns:
        Selected contract or None
    """
    if direction.upper() == "LONG":
        # For calls: ITM means strike < price
        itm_contracts = [c for c in contracts if c.strike < entry_price]
        if not itm_contracts:
            return None
        # First ITM = highest strike (closest to ATM)
        return max(itm_contracts, key=lambda c: c.strike)
    else:
        # For puts: ITM means strike > price
        itm_contracts = [c for c in contracts if c.strike > entry_price]
        if not itm_contracts:
            return None
        # First ITM = lowest strike (closest to ATM)
        return min(itm_contracts, key=lambda c: c.strike)


def select_atm(
    contracts: List[OptionsContract],
    entry_price: float
) -> Optional[OptionsContract]:
    """
    Select the at-the-money contract (strike closest to entry price).

    Args:
        contracts: List of contracts
        entry_price: Entry price of underlying

    Returns:
        Contract with strike closest to entry price
    """
    if not contracts:
        return None

    return min(contracts, key=lambda c: abs(c.strike - entry_price))


def select_first_otm(
    contracts: List[OptionsContract],
    entry_price: float,
    direction: str
) -> Optional[OptionsContract]:
    """
    Select the first out-of-the-money contract (closest to ATM while still OTM).

    For LONG (calls): OTM = strike > entry_price
        Select lowest strike that is still above entry price

    For SHORT (puts): OTM = strike < entry_price
        Select highest strike that is still below entry price

    Args:
        contracts: List of contracts
        entry_price: Entry price of underlying
        direction: "LONG" or "SHORT"

    Returns:
        Selected contract or None
    """
    if direction.upper() == "LONG":
        # For calls: OTM means strike > price
        otm_contracts = [c for c in contracts if c.strike > entry_price]
        if not otm_contracts:
            return None
        # First OTM = lowest strike (closest to ATM)
        return min(otm_contracts, key=lambda c: c.strike)
    else:
        # For puts: OTM means strike < price
        otm_contracts = [c for c in contracts if c.strike < entry_price]
        if not otm_contracts:
            return None
        # First OTM = highest strike (closest to ATM)
        return max(otm_contracts, key=lambda c: c.strike)


# =============================================================================
# ALTERNATIVE SELECTION METHODS - Uncomment and use as needed
# =============================================================================

def select_by_delta(
    contracts: List[OptionsContract],
    target_delta: float
) -> Optional[OptionsContract]:
    """
    Select contract closest to target delta.

    Example: select_by_delta(contracts, 0.70) for 70-delta option

    Args:
        contracts: List of contracts with delta values
        target_delta: Target delta (e.g., 0.70 for 70-delta)

    Returns:
        Contract with delta closest to target
    """
    # Filter contracts that have delta data
    contracts_with_delta = [c for c in contracts if c.delta is not None]
    if not contracts_with_delta:
        return None

    return min(contracts_with_delta, key=lambda c: abs(abs(c.delta) - target_delta))


def select_by_strike(
    contracts: List[OptionsContract],
    target_strike: float
) -> Optional[OptionsContract]:
    """
    Select contract with specific strike price.

    Args:
        contracts: List of contracts
        target_strike: Target strike price

    Returns:
        Contract with matching or closest strike
    """
    if not contracts:
        return None

    # Try exact match first
    exact = [c for c in contracts if c.strike == target_strike]
    if exact:
        return exact[0]

    # Otherwise closest
    return min(contracts, key=lambda c: abs(c.strike - target_strike))
