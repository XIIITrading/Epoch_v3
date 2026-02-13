"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Trade Lifecycle Pattern Analysis
XIII Trading LLC
================================================================================

Consumes pre-computed signals from the trade_lifecycle_signals table
(populated by 03_backtest processor step 16) and performs statistical
pattern analysis to identify which indicator behaviors correlate with
winning vs losing trades.

Produces:
  1. Pattern frequency report (signal -> win rate / edge)
  2. Combination pattern report (indicator pairs)
  3. Direction-specific breakdowns (LONG vs SHORT)
  4. Raw JSON for downstream consumption

Data source: trade_lifecycle_signals table
  - Rampup trend signals (INCREASING, DECREASING, FLAT, etc.)
  - Entry level signals (COMPRESSED, EXPANDING, etc.)
  - Flip signals (NO_FLIP, FLIP_TO_POSITIVE, etc.)
  - M5 progression data
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG, PATTERNS_DIR

# =============================================================================
# CONFIGURATION
# =============================================================================

MIN_TRADES_FOR_PATTERN = 20

# Signal columns organized by phase
RAMPUP_COLUMNS = [
    "rampup_candle_range_pct", "rampup_vol_delta", "rampup_vol_roc",
    "rampup_cvd_slope", "rampup_sma_spread", "rampup_sma_momentum_ratio",
    "rampup_health_score", "rampup_long_score", "rampup_short_score",
]

ENTRY_LEVEL_COLUMNS = [
    "entry_candle_range_pct", "entry_vol_delta", "entry_vol_roc",
    "entry_cvd_slope", "entry_sma_spread", "entry_sma_momentum_ratio",
    "entry_health_score", "entry_long_score", "entry_short_score",
]

ENTRY_CATEGORICAL_COLUMNS = [
    "entry_sma_momentum_label", "entry_m1_structure", "entry_m5_structure",
    "entry_m15_structure", "entry_h1_structure", "entry_h4_structure",
]

POST_ENTRY_COLUMNS = [
    "post_candle_range_pct", "post_vol_delta", "post_vol_roc",
    "post_cvd_slope", "post_sma_spread", "post_sma_momentum_ratio",
    "post_health_score", "post_long_score", "post_short_score",
]

FLIP_COLUMNS = [
    "flip_vol_delta", "flip_cvd_slope", "flip_sma_spread",
]

M5_COLUMNS = [
    "m5_health_trend",
]


# =============================================================================
# PATTERN STATS
# =============================================================================

class PatternStats:
    def __init__(self):
        self.total = 0
        self.wins = 0

    @property
    def win_rate(self) -> float:
        return (self.wins / self.total * 100) if self.total > 0 else 0


# =============================================================================
# DATA LOADING
# =============================================================================

def load_lifecycle_signals(conn) -> List[Dict]:
    """Load all records from trade_lifecycle_signals."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM trade_lifecycle_signals ORDER BY date, ticker")
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# =============================================================================
# PATTERN AGGREGATION
# =============================================================================

def aggregate_single_patterns(rows: List[Dict]) -> Dict[str, PatternStats]:
    """Aggregate single-column signal patterns."""
    patterns = defaultdict(PatternStats)

    all_columns = (
        RAMPUP_COLUMNS + ENTRY_LEVEL_COLUMNS + ENTRY_CATEGORICAL_COLUMNS
        + POST_ENTRY_COLUMNS + FLIP_COLUMNS + M5_COLUMNS
    )

    for row in rows:
        is_win = 1 if row["is_winner"] else 0

        for col in all_columns:
            val = row.get(col)
            if val is not None and val != "INSUFFICIENT" and val != "NULL":
                key = f"{col}|{val}"
                patterns[key].total += 1
                patterns[key].wins += is_win

        # Direction-specific rampup patterns
        direction = row.get("direction", "")
        for col in RAMPUP_COLUMNS:
            val = row.get(col)
            if val is not None and val != "INSUFFICIENT":
                key = f"{direction}_{col}|{val}"
                patterns[key].total += 1
                patterns[key].wins += is_win

    return dict(patterns)


def aggregate_combo_patterns(rows: List[Dict]) -> Dict[str, PatternStats]:
    """Aggregate multi-column combination patterns."""
    combos = defaultdict(PatternStats)

    pairs = [
        ("rampup_candle_range_pct", "rampup_vol_delta"),
        ("rampup_candle_range_pct", "rampup_vol_roc"),
        ("rampup_vol_delta", "rampup_cvd_slope"),
        ("rampup_vol_delta", "rampup_vol_roc"),
        ("entry_health_score", "entry_candle_range_pct"),
        ("rampup_sma_spread", "rampup_vol_delta"),
        ("flip_vol_delta", "rampup_candle_range_pct"),
        ("flip_vol_delta", "entry_health_score"),
        ("flip_cvd_slope", "rampup_vol_delta"),
        ("entry_candle_range_pct", "entry_vol_delta"),
    ]

    for row in rows:
        is_win = 1 if row["is_winner"] else 0

        for col1, col2 in pairs:
            v1 = row.get(col1)
            v2 = row.get(col2)
            if (v1 and v1 not in ("INSUFFICIENT", "NULL")
                    and v2 and v2 not in ("INSUFFICIENT", "NULL")):
                key = f"combo|{col1}={v1}+{col2}={v2}"
                combos[key].total += 1
                combos[key].wins += is_win

    return dict(combos)


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(
    patterns: Dict[str, PatternStats],
    combo_patterns: Dict[str, PatternStats],
    total_trades: int,
    total_wins: int,
    output_path: Path,
) -> str:
    """Generate the lifecycle analysis report."""
    baseline_wr = total_wins / total_trades * 100 if total_trades > 0 else 0

    lines = []
    lines.append("=" * 80)
    lines.append("EPOCH ML - TRADE LIFECYCLE PATTERN ANALYSIS")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Source: trade_lifecycle_signals table")
    lines.append(f"Baseline: {total_trades} trades, {baseline_wr:.1f}% WR")
    lines.append("=" * 80)

    # Organize by phase prefix
    phase_groups = {
        "rampup_": "RAMP-UP TRENDS (30 M1 bars before entry)",
        "entry_": "AT ENTRY (snapshot)",
        "post_": "POST-ENTRY TRENDS (30 M1 bars after entry)",
        "flip_": "FLIP DETECTION (sign changes in ramp-up)",
        "m5_": "M5 TRADE PROGRESSION",
    }

    for prefix, label in phase_groups.items():
        phase_items = {
            k: v for k, v in patterns.items()
            if k.startswith(prefix) and not k.startswith("LONG_") and not k.startswith("SHORT_")
            and v.total >= MIN_TRADES_FOR_PATTERN
        }

        if not phase_items:
            continue

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"PHASE: {label}")
        lines.append("-" * 80)

        by_col = defaultdict(list)
        for key, stats in phase_items.items():
            col_part, signal = key.split("|", 1)
            edge_pp = stats.win_rate - baseline_wr
            by_col[col_part].append((signal, stats, edge_pp))

        for col in sorted(by_col.keys()):
            items = by_col[col]
            items.sort(key=lambda x: abs(x[2]), reverse=True)

            # Clean column name for display
            display_col = col.replace("rampup_", "").replace("entry_", "").replace("post_", "").replace("flip_", "").replace("m5_", "")
            lines.append(f"\n  {display_col}:")
            lines.append(f"  {'Signal':<25s} {'N':>6s} {'Wins':>6s} {'WR':>7s} {'Edge':>8s}")
            lines.append(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7} {'-'*8}")

            for signal, stats, edge_pp in items:
                marker = ""
                if stats.total >= 30:
                    if abs(edge_pp) >= 10.0:
                        marker = " !!!"
                    elif abs(edge_pp) >= 5.0:
                        marker = " ***"
                lines.append(
                    f"  {signal:<25s} {stats.total:>6d} {stats.wins:>6d} "
                    f"{stats.win_rate:>6.1f}% {edge_pp:>+7.1f}pp{marker}"
                )

    # Direction-specific
    for direction in ["LONG", "SHORT"]:
        dir_items = {
            k: v for k, v in patterns.items()
            if k.startswith(f"{direction}_rampup_") and v.total >= MIN_TRADES_FOR_PATTERN
        }

        if not dir_items:
            continue

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"{direction} TRADE RAMP-UP PATTERNS")
        lines.append("-" * 80)

        by_col = defaultdict(list)
        for key, stats in dir_items.items():
            col_part, signal = key.split("|", 1)
            display_col = col_part.replace(f"{direction}_rampup_", "")
            edge_pp = stats.win_rate - baseline_wr
            by_col[display_col].append((signal, stats, edge_pp))

        for col in sorted(by_col.keys()):
            items = by_col[col]
            items.sort(key=lambda x: abs(x[2]), reverse=True)

            lines.append(f"\n  {col}:")
            lines.append(f"  {'Signal':<25s} {'N':>6s} {'Wins':>6s} {'WR':>7s} {'Edge':>8s}")
            lines.append(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7} {'-'*8}")

            for signal, stats, edge_pp in items:
                marker = ""
                if stats.total >= 30:
                    if abs(edge_pp) >= 10.0:
                        marker = " !!!"
                    elif abs(edge_pp) >= 5.0:
                        marker = " ***"
                lines.append(
                    f"  {signal:<25s} {stats.total:>6d} {stats.wins:>6d} "
                    f"{stats.win_rate:>6.1f}% {edge_pp:>+7.1f}pp{marker}"
                )

    # Combinations
    significant_combos = {
        k: v for k, v in combo_patterns.items()
        if v.total >= MIN_TRADES_FOR_PATTERN and abs(v.win_rate - baseline_wr) >= 5.0
    }

    if significant_combos:
        lines.append("")
        lines.append("-" * 80)
        lines.append("COMBINATION PATTERNS (indicator pairs, edge >= 5pp)")
        lines.append("-" * 80)

        sorted_combos = sorted(
            significant_combos.items(),
            key=lambda x: abs(x[1].win_rate - baseline_wr),
            reverse=True,
        )

        lines.append(f"\n  {'Pattern':<65s} {'N':>5s} {'WR':>7s} {'Edge':>8s}")
        lines.append(f"  {'-'*65} {'-'*5} {'-'*7} {'-'*8}")

        for key, stats in sorted_combos[:50]:
            label = key.replace("combo|", "")
            edge_pp = stats.win_rate - baseline_wr
            marker = " !!!" if abs(edge_pp) >= 10.0 else " ***"
            lines.append(
                f"  {label:<65s} {stats.total:>5d} {stats.win_rate:>6.1f}% {edge_pp:>+7.1f}pp{marker}"
            )

    # Top findings summary
    lines.append("")
    lines.append("=" * 80)
    lines.append("KEY FINDINGS SUMMARY")
    lines.append("=" * 80)

    all_items = [(k, v) for k, v in patterns.items() if v.total >= MIN_TRADES_FOR_PATTERN]
    all_items.sort(key=lambda x: x[1].win_rate - baseline_wr, reverse=True)

    lines.append(f"\n  TOP 15 POSITIVE EDGES (highest WR above {baseline_wr:.1f}% baseline):")
    lines.append(f"  {'Pattern':<60s} {'N':>5s} {'WR':>7s} {'Edge':>8s}")
    lines.append(f"  {'-'*60} {'-'*5} {'-'*7} {'-'*8}")
    for key, stats in all_items[:15]:
        edge_pp = stats.win_rate - baseline_wr
        label = key.replace("|", " -> ")
        lines.append(f"  {label:<60s} {stats.total:>5d} {stats.win_rate:>6.1f}% {edge_pp:>+7.1f}pp")

    lines.append(f"\n  TOP 15 NEGATIVE EDGES (lowest WR below {baseline_wr:.1f}% baseline):")
    lines.append(f"  {'Pattern':<60s} {'N':>5s} {'WR':>7s} {'Edge':>8s}")
    lines.append(f"  {'-'*60} {'-'*5} {'-'*7} {'-'*8}")
    for key, stats in all_items[-15:]:
        edge_pp = stats.win_rate - baseline_wr
        label = key.replace("|", " -> ")
        lines.append(f"  {label:<60s} {stats.total:>5d} {stats.win_rate:>6.1f}% {edge_pp:>+7.1f}pp")

    lines.append("")
    lines.append("*** = edge >= 5pp with N >= 30")
    lines.append("!!! = edge >= 10pp with N >= 30")
    lines.append(f"Baseline WR: {baseline_wr:.1f}%")

    report_text = "\n".join(lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text


def save_raw_patterns(patterns: Dict, combos: Dict, output_path: Path):
    """Save raw pattern data as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "patterns": {},
        "combo_patterns": {},
    }
    for key, stats in patterns.items():
        data["patterns"][key] = {
            "total": stats.total,
            "wins": stats.wins,
            "win_rate": round(stats.win_rate, 2),
        }
    for key, stats in combos.items():
        data["combo_patterns"][key] = {
            "total": stats.total,
            "wins": stats.wins,
            "win_rate": round(stats.win_rate, 2),
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_lifecycle_analysis():
    """Main entry point."""
    print("=" * 60)
    print("EPOCH ML - Trade Lifecycle Pattern Analysis")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)

    print("\n[1/4] Loading lifecycle signals from database...")
    rows = load_lifecycle_signals(conn)
    total_trades = len(rows)
    total_wins = sum(1 for r in rows if r["is_winner"])
    baseline_wr = total_wins / total_trades * 100 if total_trades > 0 else 0
    print(f"  -> {total_trades} trades loaded ({baseline_wr:.1f}% baseline WR)")

    conn.close()

    print("\n[2/4] Aggregating single-indicator patterns...")
    patterns = aggregate_single_patterns(rows)
    print(f"  -> {len(patterns)} unique pattern keys")

    combo_patterns = aggregate_combo_patterns(rows)
    print(f"  -> {len(combo_patterns)} combination pattern keys")

    print("\n[3/4] Generating report...")
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = PATTERNS_DIR / f"lifecycle_analysis_{date_str}.md"
    report = generate_report(patterns, combo_patterns, total_trades, total_wins, report_path)
    print(f"  -> Report saved to {report_path}")

    print("\n[4/4] Saving raw pattern data...")
    json_path = PATTERNS_DIR / f"lifecycle_patterns_{date_str}.json"
    save_raw_patterns(patterns, combo_patterns, json_path)
    print(f"  -> JSON saved to {json_path}")

    # Quick top findings
    all_items = [(k, v) for k, v in patterns.items() if v.total >= MIN_TRADES_FOR_PATTERN]
    all_items.sort(key=lambda x: abs(x[1].win_rate - baseline_wr), reverse=True)

    print(f"\nTop 10 strongest signals (by absolute edge):")
    for key, stats in all_items[:10]:
        edge_pp = stats.win_rate - baseline_wr
        label = key.replace("|", " -> ")
        print(f"  {label:<55s} N={stats.total:>4d} WR={stats.win_rate:.1f}% edge={edge_pp:+.1f}pp")

    return report_path, json_path


if __name__ == "__main__":
    run_lifecycle_analysis()
