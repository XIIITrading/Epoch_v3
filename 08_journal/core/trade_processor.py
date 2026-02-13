"""
CSV processing pipeline for the Epoch Trading Journal.

Pipeline:
    process_session(filepath)          <- Main entry point
        ├── extract_date_from_filename(filepath)
        ├── parse_csv(filepath)
        ├── group_fills(fills)
        └── pair_trades(symbol, fills, date)   <- Per symbol
                ├── determine_direction(fills)  <- First fill (chronological)
                ├── classify_fills_by_position(fills, direction)  <- State machine
                └── build_trade_id(symbol, date, time)

Position State Machine:
    Walks fills in chronological order, tracking running position.
    First fill determines direction (SHORT if sell-side, LONG if buy-side).
    Same-side fills as initial direction = entry/add (increase position).
    Opposite-side fills = exit/cover (reduce position).

Key decisions:
    - One Trade per symbol per session (all fills blended at VWAP)
    - S and SS are equivalent (both are sell-side)
    - CSV rows may NOT be in chronological order — always sort by time
    - All trades assumed closed by end of session
    - Adds (scaling back in after partial exit) blend into entry leg
"""

import re
from pathlib import Path
from datetime import date, time
from typing import List, Dict, Tuple

from .models import (
    Fill, FillSide, TradeLeg, TradeSide, Trade, TradeDirection,
    DailyTradeLog,
)


# =============================================================================
# Date extraction
# =============================================================================

def extract_date_from_filename(filepath: Path) -> date:
    """
    Extract trading date from CSV filename.
    Last 6 digits of stem = MMDDYY.

    Examples:
        test_012826.csv     -> date(2026, 1, 28)
        test_02_012826.csv  -> date(2026, 1, 28)
        tl_012926.csv       -> date(2026, 1, 29)

    Raises ValueError if no 6-digit date pattern found.
    """
    stem = filepath.stem

    # Try last 6 digits first (most reliable)
    match = re.search(r'(\d{6})$', stem)
    if not match:
        # Fallback: any 6-digit sequence
        match = re.search(r'(\d{6})', stem)
    if not match:
        raise ValueError(f"Cannot extract date from '{filepath.name}'. Expected MMDDYY in filename.")

    d = match.group(1)
    month = int(d[0:2])
    day = int(d[2:4])
    year = int(d[4:6]) + 2000
    return date(year, month, day)


# =============================================================================
# CSV parsing
# =============================================================================

SIDE_MAP = {
    "B": FillSide.BUY,
    "SS": FillSide.SHORT_SELL,
    "S": FillSide.SELL,
}


def parse_csv(filepath: Path) -> Tuple[List[Fill], List[str]]:
    """
    Parse DAS Trader Format 2 CSV (tab-delimited) into Fill objects.

    Columns: Time, Symbol, Side, Price, Qty, Route, Account, Type, Cloid

    Returns:
        (fills, errors) — successfully parsed fills and any error messages.
        Errors are non-fatal; one bad row doesn't stop processing.
    """
    fills: List[Fill] = []
    errors: List[str] = []

    text = filepath.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        errors.append(f"Empty CSV file: {filepath.name}")
        return fills, errors

    # Skip header row
    data_lines = lines[1:]

    for line_num, line in enumerate(data_lines, start=2):
        try:
            cols = line.split("\t")
            if len(cols) < 5:
                errors.append(f"Row {line_num}: insufficient columns ({len(cols)})")
                continue

            # Parse time (HH:MM:SS)
            time_parts = cols[0].split(":")
            fill_time = time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]))

            # Parse side
            raw_side = cols[2].strip().upper()
            if raw_side not in SIDE_MAP:
                errors.append(f"Row {line_num}: unknown side '{raw_side}'")
                continue
            side = SIDE_MAP[raw_side]

            fill = Fill(
                time=fill_time,
                symbol=cols[1].strip().upper(),
                side=side,
                price=float(cols[3]),
                qty=int(cols[4]),
                route=cols[5].strip() if len(cols) > 5 else "",
                account=cols[6].strip() if len(cols) > 6 else "",
                fill_type=cols[7].strip() if len(cols) > 7 else "",
                cloid=cols[8].strip() if len(cols) > 8 else "",
            )
            fills.append(fill)

        except (ValueError, IndexError) as e:
            errors.append(f"Row {line_num}: {e}")

    return fills, errors


# =============================================================================
# Grouping
# =============================================================================

def group_fills(fills: List[Fill]) -> Dict[str, List[Fill]]:
    """
    Group fills by symbol, sort by time within each group.
    Chronological order is critical for the position state machine.
    """
    groups: Dict[str, List[Fill]] = {}
    for fill in fills:
        groups.setdefault(fill.symbol, []).append(fill)

    # Sort each group chronologically
    for symbol in groups:
        groups[symbol].sort(key=lambda f: f.time)

    return groups


# =============================================================================
# Direction and fill classification via position state machine
# =============================================================================

def determine_direction(fills: List[Fill]) -> TradeDirection:
    """
    First fill chronologically determines trade direction.
    Sell-side first (SS or S) → SHORT. Buy-side first (B) → LONG.

    Fills must be sorted by time before calling this.
    """
    first = fills[0]
    if first.side.is_sell_side:
        return TradeDirection.SHORT
    return TradeDirection.LONG


def classify_fills_by_position(
    fills: List[Fill],
    direction: TradeDirection,
) -> Tuple[List[Fill], List[Fill]]:
    """
    Position state machine: walk fills chronologically and classify each
    as entry or exit based on running position.

    For a SHORT trade:
        - Sell-side fills (SS/S) increase short position → entry/add
        - Buy-side fills (B) reduce short position → exit/cover

    For a LONG trade:
        - Buy-side fills (B) increase long position → entry/add
        - Sell-side fills (SS/S) reduce long position → exit/sell

    All entry-side fills (initial + adds) go into the entry leg.
    All exit-side fills go into the exit leg.
    Both legs are blended at VWAP.

    Fills must be sorted by time before calling this.
    """
    entry_fills: List[Fill] = []
    exit_fills: List[Fill] = []

    for fill in fills:
        if direction == TradeDirection.SHORT:
            if fill.side.is_sell_side:
                entry_fills.append(fill)    # Short entry or add
            else:
                exit_fills.append(fill)     # Cover (buy to close)
        else:  # LONG
            if fill.side.is_buy_side:
                entry_fills.append(fill)    # Long entry or add
            else:
                exit_fills.append(fill)     # Sell to close

    return entry_fills, exit_fills


# =============================================================================
# Trade ID generation
# =============================================================================

def build_trade_id(symbol: str, trade_date: date, entry_time: time) -> str:
    """
    Format: {SYMBOL}_{MMDDYY}_JRNL_{HHMM}
    Example: AMD_012826_JRNL_1417

    Uses JRNL to distinguish journal trades from backtest trades (EPCH1-4).
    """
    date_str = trade_date.strftime("%m%d%y")
    time_str = f"{entry_time.hour:02d}{entry_time.minute:02d}"
    return f"{symbol}_{date_str}_JRNL_{time_str}"


# =============================================================================
# Trade pairing
# =============================================================================

def pair_trades(
    symbol: str,
    fills: List[Fill],
    trade_date: date,
) -> Trade:
    """
    Build a single Trade from all fills for one symbol.

    Algorithm:
    1. determine_direction() from first fill (chronological)
    2. classify_fills_by_position() via state machine
    3. Build entry TradeLeg (all entry fills → VWAP)
    4. Build exit TradeLeg if exit fills exist
    5. Create Trade with both legs

    Returns a single Trade (one per symbol per session).
    Fills must be sorted by time before calling this.
    """
    direction = determine_direction(fills)
    entry_fills, exit_fills = classify_fills_by_position(fills, direction)

    entry_leg = TradeLeg(side=TradeSide.ENTRY, fills=entry_fills)

    exit_leg = None
    if exit_fills:
        exit_leg = TradeLeg(side=TradeSide.EXIT, fills=exit_fills)

    # Use first entry fill time for the trade ID
    entry_time = entry_leg.first_fill_time
    trade_id = build_trade_id(symbol, trade_date, entry_time)

    # Account from first entry fill (distinguishes SIM vs LIVE)
    account = entry_fills[0].account if entry_fills else ""

    return Trade(
        trade_id=trade_id,
        trade_date=trade_date,
        symbol=symbol,
        direction=direction,
        account=account,
        entry_leg=entry_leg,
        exit_leg=exit_leg,
    )


# =============================================================================
# Main entry point
# =============================================================================

def process_session(filepath: Path) -> DailyTradeLog:
    """
    Main entry point: DAS Trader CSV → DailyTradeLog.

    Pipeline:
    1. Extract date from filename
    2. Parse CSV into Fill objects
    3. Group fills by symbol
    4. Pair each symbol's fills into a Trade

    Errors in one symbol do not prevent processing other symbols.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    # Step 1: Extract date
    try:
        trade_date = extract_date_from_filename(filepath)
    except ValueError as e:
        return DailyTradeLog(
            trade_date=date.today(),
            source_file=filepath.name,
            parse_errors=[str(e)],
        )

    # Step 2: Parse CSV
    fills, parse_errors = parse_csv(filepath)
    errors.extend(parse_errors)

    if not fills:
        return DailyTradeLog(
            trade_date=trade_date,
            source_file=filepath.name,
            parse_errors=errors or ["No fills found in CSV"],
        )

    # Step 3: Group by symbol
    groups = group_fills(fills)

    # Step 4: Pair each symbol into a Trade
    trades: List[Trade] = []
    for symbol, symbol_fills in sorted(groups.items()):
        try:
            trade = pair_trades(symbol, symbol_fills, trade_date)
            trades.append(trade)
        except Exception as e:
            errors.append(f"{symbol}: {e}")

    return DailyTradeLog(
        trade_date=trade_date,
        source_file=filepath.name,
        trades=trades,
        parse_errors=errors,
    )
