"""
Pre-Market Query Layer
Screener Pipeline Build (Seed 004) — XIII Trading LLC

Reads all pre-computed data from Supabase for a given date and ticker list.
Used by the morning screener (Phase 2) and chart visualization (Phase 3).

This is a read-only module — it queries data written by Buckets A, B, and C.

Usage:
    from data.pre_market_query import load_pre_market_data

    data = load_pre_market_data(["AAPL", "MSFT"], date(2026, 3, 22))
    for ticker, d in data.items():
        print(d["bar_data"]["pm_high"])
        print(d["market_structure"]["d1_direction"])
        print(d["zones"])
"""
import logging
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def load_pre_market_data(
    tickers: List[str],
    analysis_date: date,
) -> Dict[str, Dict[str, Any]]:
    """
    Load all pre-computed data from Supabase for the morning screener.

    Queries 5 tables: bar_data, hvn_pocs, market_structure, zones, setups.
    Returns a dict keyed by ticker symbol.

    Args:
        tickers: List of ticker symbols to load
        analysis_date: The trading date

    Returns:
        Dict keyed by ticker → {
            "bar_data": Dict (all fields from bar_data table),
            "hvn_pocs": List[float] (poc_1..poc_10),
            "market_structure": Dict (all timeframe directions + levels),
            "zones": List[Dict] (filtered zones with scores),
            "setups": List[Dict] (primary + secondary setups),
        }
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from config import DB_CONFIG

    result = {}

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        # Load each table
        bar_data_map = _query_table(conn, "bar_data", "ticker", tickers, analysis_date)
        hvn_pocs_map = _query_table(conn, "hvn_pocs", "ticker", tickers, analysis_date)
        structure_map = _query_table(conn, "market_structure", "ticker", tickers, analysis_date)
        zones_map = _query_table_multi(conn, "zones", "ticker", tickers, analysis_date)
        setups_map = _query_table_multi(conn, "setups", "ticker", tickers, analysis_date)

        conn.close()

        # Assemble per-ticker
        for ticker in tickers:
            bar_data = bar_data_map.get(ticker)
            if not bar_data:
                logger.warning(f"No bar_data for {ticker} on {analysis_date}")
                continue

            # Extract HVN POC prices as a list
            hvn_row = hvn_pocs_map.get(ticker, {})
            hvn_list = []
            for i in range(1, 11):
                poc_val = hvn_row.get(f"poc_{i}")
                if poc_val is not None:
                    hvn_list.append(float(poc_val))

            result[ticker] = {
                "bar_data": dict(bar_data) if bar_data else {},
                "hvn_pocs": hvn_list,
                "market_structure": dict(structure_map.get(ticker, {})),
                "zones": [dict(z) for z in zones_map.get(ticker, [])],
                "setups": [dict(s) for s in setups_map.get(ticker, [])],
            }

    except Exception as e:
        logger.error(f"Pre-market query failed: {e}")
        raise

    return result


def check_nightly_status(
    tickers: List[str],
    analysis_date: date,
) -> Dict[str, bool]:
    """
    Quick check: did Bucket B (nightly) run for these tickers?

    Returns:
        Dict keyed by ticker → True if bar_data row exists for the date
    """
    import psycopg2
    from config import DB_CONFIG

    status = {t: False for t in tickers}

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        placeholders = ",".join(["%s"] * len(tickers))
        cur.execute(f"""
            SELECT ticker FROM bar_data
            WHERE date = %s AND ticker IN ({placeholders})
        """, (analysis_date, *tickers))

        for row in cur.fetchall():
            status[row[0]] = True

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Nightly status check failed: {e}")

    return status


def _query_table(
    conn,
    table: str,
    ticker_col: str,
    tickers: List[str],
    analysis_date: date,
) -> Dict[str, Dict]:
    """Query a single-row-per-ticker table. Returns dict keyed by ticker."""
    from psycopg2.extras import RealDictCursor

    placeholders = ",".join(["%s"] * len(tickers))
    query = f"""
        SELECT * FROM {table}
        WHERE date = %s AND {ticker_col} IN ({placeholders})
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (analysis_date, *tickers))
        rows = cur.fetchall()

    return {row[ticker_col]: row for row in rows}


def _query_table_multi(
    conn,
    table: str,
    ticker_col: str,
    tickers: List[str],
    analysis_date: date,
) -> Dict[str, List[Dict]]:
    """Query a multi-row-per-ticker table. Returns dict keyed by ticker → list of rows."""
    from psycopg2.extras import RealDictCursor

    placeholders = ",".join(["%s"] * len(tickers))
    query = f"""
        SELECT * FROM {table}
        WHERE date = %s AND {ticker_col} IN ({placeholders})
        ORDER BY {ticker_col}
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (analysis_date, *tickers))
        rows = cur.fetchall()

    result = {}
    for row in rows:
        ticker = row[ticker_col]
        if ticker not in result:
            result[ticker] = []
        result[ticker].append(row)

    return result
