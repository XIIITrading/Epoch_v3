"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Report 1: Core Snapshot Report
XIII Trading LLC
================================================================================

System-wide "snapshot at entry" report. No ramp-up analysis.
Pulls from entry_indicators + trades_m5_r_win for the full trade population.

Sections:
  1. Overall Baseline
  2. Each indicator's values and win rates
  3. Direction breakdown (LONG / SHORT)
  4. Model breakdown (EPCH1-4)
  5. Top composite profiles (multi-indicator combinations)

This is the "what did the system look like at the moment of entry?" report.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

import psycopg2
import psycopg2.extras

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG, ANALYSIS_DIR

OUTPUT_DIR = ANALYSIS_DIR / "reports"

# Indicators to analyze from entry_indicators
ENTRY_INDICATORS = [
    ("h4_structure", "H4 Structure"),
    ("h1_structure", "H1 Structure"),
    ("m15_structure", "M15 Structure"),
    ("m5_structure", "M5 Structure"),
    ("sma_alignment", "SMA Alignment"),
    ("sma_momentum_label", "SMA Momentum"),
    ("vwap_position", "VWAP Position"),
]

# Bucketed indicators
BUCKETED_INDICATORS = [
    {
        "name": "health_tier",
        "label": "Continuation Score Tier",
        "query_expr": """
            CASE
                WHEN ei.health_score >= 8 THEN 'STRONG (8-10)'
                WHEN ei.health_score >= 6 THEN 'MODERATE (6-7)'
                WHEN ei.health_score >= 4 THEN 'WEAK (4-5)'
                ELSE 'CRITICAL (0-3)'
            END
        """,
    },
    {
        "name": "stop_distance_bucket",
        "label": "Stop Distance",
        "query_expr": """
            CASE
                WHEN m.stop_distance_pct < 0.12 THEN 'TIGHT (<0.12%%)'
                WHEN m.stop_distance_pct < 0.25 THEN 'NORMAL (0.12-0.25%%)'
                WHEN m.stop_distance_pct < 0.50 THEN 'WIDE (0.25-0.50%%)'
                ELSE 'VERY WIDE (>=0.50%%)'
            END
        """,
    },
]

# Fields from trades_m5_r_win
TRADE_FIELDS = [
    ("direction", "Direction"),
    ("model", "Entry Model"),
    ("zone_type", "Zone Type"),
]

# Composite profile indicators (for multi-indicator combinations)
COMPOSITE_INDICATORS = [
    "m15_structure", "sma_alignment", "health_tier",
]


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def run_indicator_query(conn, indicator_col: str, source: str = "ei") -> List[Dict]:
    """Query win rates for each value of an indicator."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if source == "ei":
        cur.execute(f"""
            SELECT
                ei.{indicator_col} as value,
                COUNT(*) as total,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE ei.{indicator_col} IS NOT NULL
            GROUP BY ei.{indicator_col}
            ORDER BY total DESC
        """)
    else:
        cur.execute(f"""
            SELECT
                m.{indicator_col} as value,
                COUNT(*) as total,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
            FROM trades_m5_r_win m
            WHERE m.{indicator_col} IS NOT NULL
            GROUP BY m.{indicator_col}
            ORDER BY total DESC
        """)

    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def run_bucketed_query(conn, query_expr: str) -> List[Dict]:
    """Query win rates for a computed bucket expression."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT
            {query_expr} as value,
            COUNT(*) as total,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        GROUP BY value
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def run_direction_indicator_query(conn, indicator_col: str, direction: str) -> List[Dict]:
    """Query indicator win rates filtered by direction."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT
            ei.{indicator_col} as value,
            COUNT(*) as total,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE ei.{indicator_col} IS NOT NULL
        AND m.direction = %s
        GROUP BY ei.{indicator_col}
        ORDER BY total DESC
    """, (direction,))
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def run_model_indicator_query(conn, indicator_col: str, model: str) -> List[Dict]:
    """Query indicator win rates filtered by model."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT
            ei.{indicator_col} as value,
            COUNT(*) as total,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE ei.{indicator_col} IS NOT NULL
        AND m.model = %s
        GROUP BY ei.{indicator_col}
        ORDER BY total DESC
    """, (model,))
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def run_composite_query(conn) -> List[Dict]:
    """Query win rates for multi-indicator composite profiles."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            ei.m15_structure,
            ei.sma_alignment,
            CASE
                WHEN ei.health_score >= 8 THEN 'STRONG'
                WHEN ei.health_score >= 6 THEN 'MODERATE'
                WHEN ei.health_score >= 4 THEN 'WEAK'
                ELSE 'CRITICAL'
            END as health_tier,
            COUNT(*) as total,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE ei.m15_structure IS NOT NULL
        AND ei.sma_alignment IS NOT NULL
        AND ei.health_score IS NOT NULL
        GROUP BY ei.m15_structure, ei.sma_alignment, health_tier
        HAVING COUNT(*) >= 20
        ORDER BY (SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::float / COUNT(*)) DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def format_indicator_table(rows: List[Dict], baseline_wr: float) -> List[str]:
    """Format indicator rows into a report table."""
    lines = []
    lines.append(f"  {'Value':<25s} {'N':>6s} {'Wins':>6s} {'WR':>7s} {'Edge':>8s}")
    lines.append(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7} {'-'*8}")

    # Sort by edge descending
    sorted_rows = sorted(rows, key=lambda r: (r["wins"] / r["total"] * 100 if r["total"] > 0 else 0) - baseline_wr, reverse=True)

    for row in sorted_rows:
        if row["total"] == 0 or row["value"] is None:
            continue
        wr = row["wins"] / row["total"] * 100
        edge = wr - baseline_wr
        marker = ""
        if row["total"] >= 30:
            if abs(edge) >= 10.0:
                marker = " !!!"
            elif abs(edge) >= 5.0:
                marker = " ***"
        val_str = str(row["value"])[:25]
        lines.append(
            f"  {val_str:<25s} {row['total']:>6d} {row['wins']:>6d} "
            f"{wr:>6.1f}% {edge:>+7.1f}pp{marker}"
        )

    return lines


def generate_core_report():
    """Generate the full core snapshot report."""
    print("=" * 60)
    print("EPOCH ML - Core Snapshot Report")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Baseline
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins
        FROM trades_m5_r_win
    """)
    baseline = cur.fetchone()
    total_trades = baseline["total"]
    total_wins = baseline["wins"]
    baseline_wr = total_wins / total_trades * 100
    cur.close()

    lines = []
    lines.append("=" * 80)
    lines.append("EPOCH ML - CORE SNAPSHOT REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Source: entry_indicators + trades_m5_r_win")
    lines.append(f"Win Condition: trades_m5_r_win.is_winner (M5 ATR(14) x 1.1, close-based)")
    lines.append("=" * 80)

    # Section 1: Baseline
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 1: BASELINE")
    lines.append("-" * 80)
    lines.append(f"  Total Trades: {total_trades}")
    lines.append(f"  Total Wins:   {total_wins}")
    lines.append(f"  Baseline WR:  {baseline_wr:.1f}%")

    # Section 2: Individual Indicators
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 2: ENTRY INDICATOR VALUES (snapshot at entry)")
    lines.append("-" * 80)

    print("\n  Querying entry indicators...")
    for col, label in ENTRY_INDICATORS:
        rows = run_indicator_query(conn, col, source="ei")
        lines.append(f"\n  {label} ({col}):")
        lines.extend(format_indicator_table(rows, baseline_wr))

    for bucket in BUCKETED_INDICATORS:
        rows = run_bucketed_query(conn, bucket["query_expr"])
        lines.append(f"\n  {bucket['label']}:")
        lines.extend(format_indicator_table(rows, baseline_wr))

    for col, label in TRADE_FIELDS:
        rows = run_indicator_query(conn, col, source="trade")
        lines.append(f"\n  {label} ({col}):")
        lines.extend(format_indicator_table(rows, baseline_wr))

    # Section 3: Direction Breakdown
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 3: DIRECTION BREAKDOWN")
    lines.append("-" * 80)

    print("  Querying direction breakdowns...")
    for direction in ["LONG", "SHORT"]:
        lines.append(f"\n  === {direction} TRADES ===")
        for col, label in ENTRY_INDICATORS:
            rows = run_direction_indicator_query(conn, col, direction)
            lines.append(f"\n  {label} ({col}):")
            lines.extend(format_indicator_table(rows, baseline_wr))

    # Section 4: Model Breakdown
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 4: MODEL BREAKDOWN (EPCH1-4)")
    lines.append("-" * 80)

    print("  Querying model breakdowns...")
    for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
        lines.append(f"\n  === {model} ===")
        for col, label in ENTRY_INDICATORS:
            rows = run_model_indicator_query(conn, col, model)
            if rows:
                lines.append(f"\n  {label} ({col}):")
                lines.extend(format_indicator_table(rows, baseline_wr))

    # Section 5: Composite Profiles
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 5: TOP COMPOSITE PROFILES (M15 + SMA Alignment + Health Tier)")
    lines.append("-" * 80)

    print("  Querying composite profiles...")
    composites = run_composite_query(conn)

    lines.append(f"\n  {'M15':<10s} {'SMA Align':<12s} {'Health':<10s} {'N':>6s} {'Wins':>6s} {'WR':>7s} {'Edge':>8s}")
    lines.append(f"  {'-'*10} {'-'*12} {'-'*10} {'-'*6} {'-'*6} {'-'*7} {'-'*8}")

    for row in composites:
        wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
        edge = wr - baseline_wr
        marker = ""
        if row["total"] >= 30:
            if abs(edge) >= 10.0:
                marker = " !!!"
            elif abs(edge) >= 5.0:
                marker = " ***"
        lines.append(
            f"  {str(row['m15_structure']):<10s} {str(row['sma_alignment']):<12s} "
            f"{str(row['health_tier']):<10s} {row['total']:>6d} {row['wins']:>6d} "
            f"{wr:>6.1f}% {edge:>+7.1f}pp{marker}"
        )

    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF CORE SNAPSHOT REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("*** = edge >= 5pp with N >= 30")
    lines.append("!!! = edge >= 10pp with N >= 30")
    lines.append(f"Baseline WR: {baseline_wr:.1f}%")
    lines.append(f"Win Condition: trades_m5_r_win.is_winner")

    conn.close()

    # Write report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = OUTPUT_DIR / f"core_snapshot_{date_str}.md"

    report_text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n  Report saved to {report_path}")
    return report_path


if __name__ == "__main__":
    generate_core_report()
