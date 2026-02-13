"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Report 2: Lifecycle Ramp-Up Report
XIII Trading LLC
================================================================================

Analyzes M1 indicator bar ramp-up sequences, MFE paths, and exit paths.
Reads from trade_lifecycle_signals (pre-entry) and computes MFE/exit signals
on the fly from m1_indicator_bars + trades_m5_r_win.

Sections:
  1. Pre-Entry: LONG vs SHORT
  2. Pre-Entry: Continuation vs Rejection (M5 structure aligned)
  3. Pre-Entry: Model Specific (EPCH1-4)
  4. Path to MFE (15-bar ramp-up + snapshot at MFE time)
  5. Path to Exit (15-bar ramp-up + snapshot at max-R time)

Each section shows:
  A) Best composite profile (multi-indicator ideal state)
  B) Individual indicators with ideal state and hit rate
"""

import sys
import json
from datetime import datetime, time as dtime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG, ANALYSIS_DIR


# =============================================================================
# SIGNAL CLASSIFIERS (inline from 03_backtest lifecycle calculator)
# =============================================================================

TREND_WINDOW = 5

LEVEL_THRESHOLDS = {
    "candle_range_pct": [("COMPRESSED", None, 0.08), ("NORMAL", 0.08, 0.15),
                          ("EXPANDING", 0.15, 0.25), ("EXPLOSIVE", 0.25, None)],
    "vol_roc": [("LOW", None, 10), ("MODERATE", 10, 50),
                ("ELEVATED", 50, 100), ("EXTREME", 100, None)],
    "vol_delta": [("STRONG_SELL", None, -50000), ("MILD_SELL", -50000, 0),
                  ("MILD_BUY", 0, 50000), ("STRONG_BUY", 50000, None)],
    "cvd_slope": [("STRONG_FALLING", None, -0.2), ("MILD_FALLING", -0.2, 0),
                  ("MILD_RISING", 0, 0.2), ("STRONG_RISING", 0.2, None)],
    "health_score": [("CRITICAL", None, 4), ("WEAK", 4, 6),
                     ("MODERATE", 6, 8), ("STRONG", 8, None)],
    "long_score": [("MINIMAL", None, 2), ("LOW", 2, 5),
                   ("MODERATE", 5, 8), ("HIGH", 8, None)],
    "short_score": [("MINIMAL", None, 2), ("LOW", 2, 5),
                    ("MODERATE", 5, 8), ("HIGH", 8, None)],
    "sma_spread": [("WIDE_BEAR", None, -0.15), ("NARROW_BEAR", -0.15, 0),
                   ("NARROW_BULL", 0, 0.15), ("WIDE_BULL", 0.15, None)],
    "sma_momentum_ratio": [("NARROWING", None, -1), ("FLAT", -1, 1),
                           ("WIDENING", 1, 5), ("STRONG_WIDENING", 5, None)],
}


def classify_trend(values, window=TREND_WINDOW):
    clean = [v for v in values if v is not None]
    if len(clean) < window:
        return "INSUFFICIENT"
    recent = clean[-window:]
    deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
    if not deltas:
        return "FLAT"
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    total = len(deltas)
    if pos >= total * 0.75:
        return "INCREASING"
    if neg >= total * 0.75:
        return "DECREASING"
    mid = len(deltas) // 2
    if mid == 0:
        return "FLAT"
    first = sum(deltas[:mid]) / mid
    second = sum(deltas[mid:]) / (len(deltas) - mid)
    if first > 0 and second < 0:
        return "INC_THEN_DEC"
    if first < 0 and second > 0:
        return "DEC_THEN_INC"
    changes = sum(1 for i in range(len(deltas)-1) if (deltas[i] > 0) != (deltas[i+1] > 0))
    if changes >= total * 0.6:
        return "VOLATILE"
    return "FLAT"


def classify_level(value, indicator):
    if value is None:
        return "NULL"
    thresholds = LEVEL_THRESHOLDS.get(indicator)
    if not thresholds:
        return "UNKNOWN"
    for label, low, high in thresholds:
        if low is None and high is not None and value < high:
            return label
        if low is not None and high is None and value >= low:
            return label
        if low is not None and high is not None and low <= value < high:
            return label
    return "UNKNOWN"

OUTPUT_DIR = ANALYSIS_DIR / "reports"

# =============================================================================
# CONFIGURATION
# =============================================================================

MFE_EXIT_RAMPUP_BARS = 15  # 15 M1 bars before MFE/exit event

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

FLIP_COLUMNS = [
    "flip_vol_delta", "flip_cvd_slope", "flip_sma_spread",
]

# M1 numeric indicators for MFE/exit analysis
M1_NUMERIC = [
    "candle_range_pct", "vol_delta", "vol_roc", "cvd_slope",
    "sma_spread", "sma_momentum_ratio", "health_score",
    "long_score", "short_score",
]

# Key ramp-up columns for composite profiles (top contributors)
COMPOSITE_RAMPUP = [
    "rampup_candle_range_pct", "rampup_vol_delta", "rampup_sma_spread",
]


# =============================================================================
# HELPERS
# =============================================================================

class Stats:
    __slots__ = ("total", "wins")
    def __init__(self):
        self.total = 0
        self.wins = 0

    @property
    def wr(self):
        return (self.wins / self.total * 100) if self.total > 0 else 0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def format_table(rows: List[Tuple[str, Stats]], baseline_wr: float, min_n: int = 20) -> List[str]:
    """Format signal -> Stats into a table, sorted by edge."""
    filtered = [(s, st) for s, st in rows if st.total >= min_n]
    filtered.sort(key=lambda x: x[1].wr - baseline_wr, reverse=True)

    lines = []
    lines.append(f"  {'Signal':<25s} {'N':>6s} {'Wins':>6s} {'WR':>7s} {'Edge':>8s}")
    lines.append(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7} {'-'*8}")

    for signal, st in filtered:
        edge = st.wr - baseline_wr
        marker = ""
        if st.total >= 30:
            if abs(edge) >= 10.0:
                marker = " !!!"
            elif abs(edge) >= 5.0:
                marker = " ***"
        lines.append(
            f"  {signal:<25s} {st.total:>6d} {st.wins:>6d} "
            f"{st.wr:>6.1f}% {edge:>+7.1f}pp{marker}"
        )

    return lines


def aggregate_column(rows: List[Dict], col: str) -> Dict[str, Stats]:
    """Aggregate win/loss stats by signal value for a column."""
    agg = defaultdict(Stats)
    for r in rows:
        val = r.get(col)
        if val and val not in ("INSUFFICIENT", "NULL", "N/A"):
            agg[val].total += 1
            agg[val].wins += (1 if r["is_winner"] else 0)
    return dict(agg)


def find_best_composite(rows: List[Dict], cols: List[str], min_n: int = 20) -> List[Tuple]:
    """Find multi-indicator composite profiles with highest win rates."""
    combos = defaultdict(Stats)
    for r in rows:
        vals = []
        skip = False
        for c in cols:
            v = r.get(c)
            if not v or v in ("INSUFFICIENT", "NULL"):
                skip = True
                break
            vals.append(v)
        if skip:
            continue
        key = tuple(vals)
        combos[key].total += 1
        combos[key].wins += (1 if r["is_winner"] else 0)

    # Filter and sort
    results = [(k, st) for k, st in combos.items() if st.total >= min_n]
    results.sort(key=lambda x: x[1].wr, reverse=True)
    return results[:15]  # Top 15


def format_composite_table(composites: List[Tuple], cols: List[str], baseline_wr: float) -> List[str]:
    """Format composite profile results."""
    lines = []
    col_headers = [c.replace("rampup_", "").replace("entry_", "")[:15] for c in cols]
    header = "  " + "  ".join(f"{h:<17s}" for h in col_headers) + f" {'N':>5s} {'WR':>7s} {'Edge':>8s}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for combo_vals, st in composites:
        edge = st.wr - baseline_wr
        marker = " !!!" if abs(edge) >= 10 and st.total >= 30 else (" ***" if abs(edge) >= 5 and st.total >= 30 else "")
        row = "  " + "  ".join(f"{str(v):<17s}" for v in combo_vals)
        row += f" {st.total:>5d} {st.wr:>6.1f}% {edge:>+7.1f}pp{marker}"
        lines.append(row)

    return lines


# =============================================================================
# SECTION BUILDERS
# =============================================================================

def build_section(rows: List[Dict], title: str, baseline_wr: float,
                  rampup_cols: List[str], level_cols: List[str],
                  flip_cols: List[str], composite_cols: List[str]) -> List[str]:
    """Build a complete section with individual indicators + composite profiles."""
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append(title)
    n_trades = len(rows)
    n_wins = sum(1 for r in rows if r["is_winner"])
    section_wr = n_wins / n_trades * 100 if n_trades > 0 else 0
    lines.append(f"  Trades: {n_trades}, Wins: {n_wins}, WR: {section_wr:.1f}% (baseline: {baseline_wr:.1f}%)")
    lines.append("=" * 80)

    if n_trades < 20:
        lines.append("  Insufficient trades for analysis (< 20)")
        return lines

    # A) Best composite profile
    lines.append("")
    lines.append("  --- BEST COMPOSITE PROFILES ---")
    composites = find_best_composite(rows, composite_cols)
    if composites:
        lines.extend(format_composite_table(composites, composite_cols, baseline_wr))
    else:
        lines.append("  No composite profiles with N >= 20")

    # B) Individual ramp-up indicators
    lines.append("")
    lines.append("  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---")
    for col in rampup_cols:
        agg = aggregate_column(rows, col)
        if agg:
            display = col.replace("rampup_", "")
            lines.append(f"\n  {display}:")
            lines.extend(format_table(list(agg.items()), baseline_wr))

    # C) Entry level signals
    lines.append("")
    lines.append("  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---")
    for col in level_cols:
        agg = aggregate_column(rows, col)
        if agg:
            display = col.replace("entry_", "")
            lines.append(f"\n  {display}:")
            lines.extend(format_table(list(agg.items()), baseline_wr))

    # D) Flip signals
    if flip_cols:
        lines.append("")
        lines.append("  --- FLIP SIGNALS (sign changes in ramp-up) ---")
        for col in flip_cols:
            agg = aggregate_column(rows, col)
            if agg:
                display = col.replace("flip_", "")
                lines.append(f"\n  {display}:")
                lines.extend(format_table(list(agg.items()), baseline_wr))

    return lines


# =============================================================================
# MFE / EXIT SIGNAL COMPUTATION
# =============================================================================

def compute_event_signals(conn, event_type: str = "MFE") -> List[Dict]:
    """Compute M1 indicator signals at a trade event (MFE or max-R exit).

    For each trade:
      1. Get the event time (MFE from m5_trade_bars, or max-R from trades_m5_r_win)
      2. Load M1 bars for that ticker/date
      3. Compute 15-bar ramp-up trend + snapshot at event time
      4. Return enriched rows

    Returns list of dicts with trade context + event signals.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if event_type == "MFE":
        # Get MFE time from m5_trade_bars
        cur.execute("""
            SELECT tb.trade_id, tb.ticker, tb.date, tb.bar_time as event_time,
                   t.direction, t.model, t.is_winner, t.max_r_achieved
            FROM m5_trade_bars tb
            JOIN trades_m5_r_win t ON tb.trade_id = t.trade_id
            WHERE tb.event_type IN ('MFE', 'MFE_MAE')
            ORDER BY tb.date, tb.ticker
        """)
    else:
        # Get exit time for ALL trades:
        #   Winners: time of max R achieved
        #   Losers: stop_hit_time, or last M5 bar time as fallback
        cur.execute("""
            SELECT t.trade_id, t.ticker, t.date,
                   CASE
                       WHEN t.max_r_achieved >= 5 THEN t.r5_time
                       WHEN t.max_r_achieved >= 4 THEN t.r4_time
                       WHEN t.max_r_achieved >= 3 THEN t.r3_time
                       WHEN t.max_r_achieved >= 2 THEN t.r2_time
                       WHEN t.max_r_achieved >= 1 THEN t.r1_time
                       WHEN t.stop_hit_time IS NOT NULL THEN t.stop_hit_time
                       ELSE t.zb_exit_time
                   END as event_time,
                   t.direction, t.model, t.is_winner, t.max_r_achieved
            FROM trades_m5_r_win t
            WHERE (t.max_r_achieved >= 1 OR t.stop_hit_time IS NOT NULL OR t.zb_exit_time IS NOT NULL)
            ORDER BY t.date, t.ticker
        """)

    trades = [dict(r) for r in cur.fetchall()]
    cur.close()

    if not trades:
        return []

    # Group by ticker/date
    by_td = defaultdict(list)
    for t in trades:
        if t["event_time"] is not None:
            by_td[(t["ticker"], t["date"])].append(t)

    results = []
    processed = 0

    for (ticker, date), group in by_td.items():
        # Load M1 bars
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM m1_indicator_bars
            WHERE ticker = %s AND bar_date = %s
            ORDER BY bar_time
        """, (ticker, date))
        m1_bars = [dict(r) for r in cur.fetchall()]
        cur.close()

        for trade in group:
            event_time = trade["event_time"]
            if event_time is None:
                continue

            # Find ramp-up bars (15 bars before event)
            before_bars = [b for b in m1_bars if b["bar_time"] < event_time]
            rampup = before_bars[-MFE_EXIT_RAMPUP_BARS:]

            # Find snapshot bar (at or closest before event)
            snapshot = None
            for b in m1_bars:
                if b["bar_time"] <= event_time:
                    snapshot = b
                elif b["bar_time"] > event_time:
                    break

            # Compute signals
            row = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "date": str(date),
                "direction": trade["direction"],
                "model": trade["model"],
                "is_winner": trade["is_winner"],
                "max_r_achieved": trade["max_r_achieved"],
                "event_time": str(event_time),
                "rampup_bars_found": len(rampup),
            }

            for ind in M1_NUMERIC:
                # Ramp-up trend
                vals = [b.get(ind) for b in rampup]
                row[f"rampup_{ind}"] = classify_trend(vals)

                # Snapshot level
                val = snapshot.get(ind) if snapshot else None
                row[f"snapshot_{ind}"] = classify_level(val, ind)

            results.append(row)

        processed += 1
        if processed % 50 == 0:
            print(f"    {event_type}: {processed}/{len(by_td)} groups, {len(results)} trades")

    return results


def build_event_section(rows: List[Dict], title: str, baseline_wr: float) -> List[str]:
    """Build an MFE or exit section from computed event signals."""
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append(title)
    n_trades = len(rows)
    n_wins = sum(1 for r in rows if r["is_winner"])
    section_wr = n_wins / n_trades * 100 if n_trades > 0 else 0
    lines.append(f"  Trades: {n_trades}, Wins: {n_wins}, WR: {section_wr:.1f}% (baseline: {baseline_wr:.1f}%)")
    lines.append("=" * 80)

    if n_trades < 20:
        lines.append("  Insufficient trades for analysis (< 20)")
        return lines

    rampup_cols = [f"rampup_{ind}" for ind in M1_NUMERIC]
    snapshot_cols = [f"snapshot_{ind}" for ind in M1_NUMERIC]
    composite_cols = [f"rampup_{ind}" for ind in ["candle_range_pct", "vol_delta", "sma_spread"]]

    # Composite profiles
    lines.append("")
    lines.append("  --- BEST COMPOSITE PROFILES (ramp-up to event) ---")
    composites = find_best_composite(rows, composite_cols)
    if composites:
        lines.extend(format_composite_table(composites, composite_cols, baseline_wr))

    # Ramp-up trends
    lines.append("")
    lines.append(f"  --- RAMP-UP TRENDS ({MFE_EXIT_RAMPUP_BARS} M1 bars before event) ---")
    for col in rampup_cols:
        agg = aggregate_column(rows, col)
        if agg:
            display = col.replace("rampup_", "")
            lines.append(f"\n  {display}:")
            lines.extend(format_table(list(agg.items()), baseline_wr))

    # Snapshot levels
    lines.append("")
    lines.append("  --- SNAPSHOT AT EVENT ---")
    for col in snapshot_cols:
        agg = aggregate_column(rows, col)
        if agg:
            display = col.replace("snapshot_", "")
            lines.append(f"\n  {display}:")
            lines.extend(format_table(list(agg.items()), baseline_wr))

    return lines


# =============================================================================
# MAIN
# =============================================================================

def generate_lifecycle_report():
    """Generate the full lifecycle ramp-up report."""
    print("=" * 60)
    print("EPOCH ML - Lifecycle Ramp-Up Report")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Load all lifecycle signals
    print("\n[1/7] Loading lifecycle signals...")
    cur.execute("SELECT * FROM trade_lifecycle_signals ORDER BY date, ticker")
    all_rows = [dict(r) for r in cur.fetchall()]
    total_trades = len(all_rows)
    total_wins = sum(1 for r in all_rows if r["is_winner"])
    baseline_wr = total_wins / total_trades * 100
    print(f"  -> {total_trades} trades, {baseline_wr:.1f}% baseline WR")
    cur.close()

    lines = []
    lines.append("=" * 80)
    lines.append("EPOCH ML - LIFECYCLE RAMP-UP REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Source: trade_lifecycle_signals + m1_indicator_bars")
    lines.append(f"Win Condition: trades_m5_r_win.is_winner (M5 ATR(14) x 1.1, close-based)")
    lines.append(f"Baseline: {total_trades} trades, {baseline_wr:.1f}% WR")
    lines.append("=" * 80)

    # ------------------------------------------------------------------
    # SECTION 1: Pre-Entry LONG vs SHORT
    # ------------------------------------------------------------------
    print("\n[2/7] Building Section 1: LONG vs SHORT...")
    for direction in ["LONG", "SHORT"]:
        filtered = [r for r in all_rows if r["direction"] == direction]
        lines.extend(build_section(
            filtered,
            f"SECTION 1: PRE-ENTRY - {direction} TRADES",
            baseline_wr,
            RAMPUP_COLUMNS, ENTRY_LEVEL_COLUMNS, FLIP_COLUMNS, COMPOSITE_RAMPUP,
        ))

    # ------------------------------------------------------------------
    # SECTION 2: Pre-Entry Continuation vs Rejection
    # M5 structure BULL + LONG = continuation; BEAR + SHORT = continuation
    # M5 structure BULL + SHORT = rejection; BEAR + LONG = rejection
    # ------------------------------------------------------------------
    print("[3/7] Building Section 2: Continuation vs Rejection...")

    cont_rows = [r for r in all_rows
                 if (r["direction"] == "LONG" and r.get("entry_m5_structure") == "BULL")
                 or (r["direction"] == "SHORT" and r.get("entry_m5_structure") == "BEAR")]
    reject_rows = [r for r in all_rows
                   if (r["direction"] == "LONG" and r.get("entry_m5_structure") == "BEAR")
                   or (r["direction"] == "SHORT" and r.get("entry_m5_structure") == "BULL")]
    neutral_rows = [r for r in all_rows if r.get("entry_m5_structure") == "NEUTRAL"]

    lines.extend(build_section(
        cont_rows,
        "SECTION 2A: PRE-ENTRY - CONTINUATION TRADES (M5 aligned with direction)",
        baseline_wr,
        RAMPUP_COLUMNS, ENTRY_LEVEL_COLUMNS, FLIP_COLUMNS, COMPOSITE_RAMPUP,
    ))
    lines.extend(build_section(
        reject_rows,
        "SECTION 2B: PRE-ENTRY - REJECTION TRADES (M5 opposing direction)",
        baseline_wr,
        RAMPUP_COLUMNS, ENTRY_LEVEL_COLUMNS, FLIP_COLUMNS, COMPOSITE_RAMPUP,
    ))
    lines.extend(build_section(
        neutral_rows,
        "SECTION 2C: PRE-ENTRY - NEUTRAL TRADES (M5 structure = NEUTRAL)",
        baseline_wr,
        RAMPUP_COLUMNS, ENTRY_LEVEL_COLUMNS, FLIP_COLUMNS, COMPOSITE_RAMPUP,
    ))

    # ------------------------------------------------------------------
    # SECTION 3: Model Specific (EPCH1-4)
    # ------------------------------------------------------------------
    print("[4/7] Building Section 3: Model Specific...")
    for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
        filtered = [r for r in all_rows if r["model"] == model]
        lines.extend(build_section(
            filtered,
            f"SECTION 3: PRE-ENTRY - MODEL {model}",
            baseline_wr,
            RAMPUP_COLUMNS, ENTRY_LEVEL_COLUMNS, FLIP_COLUMNS, COMPOSITE_RAMPUP,
        ))

    # ------------------------------------------------------------------
    # SECTION 4: Path to MFE
    # ------------------------------------------------------------------
    print("[5/7] Building Section 4: Path to MFE...")
    mfe_rows = compute_event_signals(conn, event_type="MFE")
    print(f"  -> {len(mfe_rows)} MFE events processed")
    lines.extend(build_event_section(
        mfe_rows,
        "SECTION 4: PATH TO MFE (15-bar M1 ramp-up + snapshot at MFE)",
        baseline_wr,
    ))

    # Direction split for MFE
    for direction in ["LONG", "SHORT"]:
        filtered = [r for r in mfe_rows if r["direction"] == direction]
        lines.extend(build_event_section(
            filtered,
            f"SECTION 4{direction[0]}: PATH TO MFE - {direction} TRADES",
            baseline_wr,
        ))

    # ------------------------------------------------------------------
    # SECTION 5: Path to Exit (max R)
    # ------------------------------------------------------------------
    print("[6/7] Building Section 5: Path to Exit (max R)...")
    exit_rows = compute_event_signals(conn, event_type="EXIT")
    print(f"  -> {len(exit_rows)} exit events processed")
    lines.extend(build_event_section(
        exit_rows,
        "SECTION 5: PATH TO EXIT / MAX-R (15-bar M1 ramp-up + snapshot at max R time)",
        baseline_wr,
    ))

    # R-level split
    for r_level in [1, 2, 3]:
        filtered = [r for r in exit_rows if r.get("max_r_achieved", 0) >= r_level
                    and r.get("max_r_achieved", 0) < r_level + 1]
        if len(filtered) >= 20:
            lines.extend(build_event_section(
                filtered,
                f"SECTION 5.{r_level}: PATH TO EXIT - TRADES REACHING EXACTLY R{r_level}",
                baseline_wr,
            ))

    # R3+ group
    r3plus = [r for r in exit_rows if r.get("max_r_achieved", 0) >= 3]
    if len(r3plus) >= 20:
        lines.extend(build_event_section(
            r3plus,
            "SECTION 5.3+: PATH TO EXIT - TRADES REACHING R3 OR HIGHER",
            baseline_wr,
        ))

    conn.close()

    # Footer
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF LIFECYCLE RAMP-UP REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("*** = edge >= 5pp with N >= 30")
    lines.append("!!! = edge >= 10pp with N >= 30")
    lines.append(f"Baseline WR: {baseline_wr:.1f}%")
    lines.append(f"Win Condition: trades_m5_r_win.is_winner")

    # Write
    print("\n[7/7] Saving report...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = OUTPUT_DIR / f"lifecycle_rampup_{date_str}.md"

    report_text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"  -> Report saved to {report_path}")
    print(f"  -> {len(lines)} lines")

    return report_path


if __name__ == "__main__":
    generate_lifecycle_report()
