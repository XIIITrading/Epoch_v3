"""
POC Line Filter Diagnostic
==========================
Compares raw HVN POCs vs filtered zones to verify only L3+ POCs
are drawn on the pre-market report chart.

Outputs:
  - Console text diagnostic
  - Side-by-side PNG: CURRENT (bug) vs FIXED (L3+ filter)

Usage:
    python test_poc_filter.py                   # defaults to TSLA, today
    python test_poc_filter.py TSLA              # specific ticker, today
    python test_poc_filter.py TSLA 2026-03-12   # specific ticker + date
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Set, Tuple

import psycopg2
import psycopg2.extras
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Setup path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shared.config.credentials import SUPABASE_DB_CONFIG

# ── Constants ────────────────────────────────────────────────────────────────

RANKING_SCORE_THRESHOLDS = {
    "L5": 12.0, "L4": 9.0, "L3": 6.0, "L2": 3.0, "L1": 0.0,
}
MIN_ZONE_SCORE = 6.0

# Colors (match EPOCH_DARK from shared/charts/colors.py)
C_BG          = "#1C1C1C"
C_TEXT        = "#e0e0e0"
C_TEXT_MUTED  = "#888888"
C_TEXT_DIM    = "#666666"
C_BORDER      = "#444444"
C_CANDLE_UP   = "#26a69a"
C_CANDLE_DOWN = "#ef5350"
C_ZONE_PRI    = "#90bff9"
C_ZONE_SEC    = "#faa1a4"
C_POC_LINE    = "#FFFFFF"
C_POC_ALPHA   = 0.3
C_ZONE_ALPHA  = 0.15
C_SKIP_LINE   = "#FF6B6B"  # Red for "should not be drawn" indicator
C_PD_VP_POC   = "#FF9800"  # Orange for Prior Day VP POC
C_PD_VP_VA    = "#00BCD4"  # Cyan for Prior Day VP VAH/VAL


# ── Helpers ──────────────────────────────────────────────────────────────────

def score_to_rank(score: float) -> str:
    for rank, threshold in RANKING_SCORE_THRESHOLDS.items():
        if score >= threshold:
            return rank
    return "L1"


def header(text: str, width: int = 72) -> str:
    return f"\n{'=' * width}\n  {text}\n{'=' * width}"


def divider(width: int = 72) -> str:
    return "-" * width


# ── Direct DB Queries ────────────────────────────────────────────────────────

def query_db(conn, sql: str, params: tuple) -> List[Dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_raw_pocs(conn, ticker: str, session_date: date) -> List[float]:
    rows = query_db(conn, """
        SELECT poc_1, poc_2, poc_3, poc_4, poc_5,
               poc_6, poc_7, poc_8, poc_9, poc_10
        FROM hvn_pocs
        WHERE date = %s AND UPPER(ticker) = UPPER(%s)
    """, (session_date, ticker))
    if not rows:
        return []
    row = rows[0]
    pocs = []
    for i in range(1, 11):
        val = row.get(f"poc_{i}")
        if val is not None:
            pocs.append(float(val))
    return pocs


def fetch_filtered_zones(conn, ticker: str, session_date: date) -> List[Dict]:
    return query_db(conn, """
        SELECT zone_id, hvn_poc, zone_high, zone_low,
               score, rank, overlap_count as overlaps, confluences
        FROM zones
        WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        ORDER BY score DESC
    """, (session_date, ticker))


def fetch_setups(conn, ticker: str, session_date: date) -> Tuple[Optional[Dict], Optional[Dict]]:
    rows = query_db(conn, """
        SELECT setup_type, direction, zone_id, hvn_poc,
               zone_high, zone_low, target_price as target, risk_reward as r_r
        FROM setups
        WHERE date = %s AND UPPER(ticker) = UPPER(%s)
    """, (session_date, ticker))
    primary = next((r for r in rows if r.get("setup_type") == "PRIMARY"), None)
    secondary = next((r for r in rows if r.get("setup_type") == "SECONDARY"), None)
    return primary, secondary


def fetch_bar_data(conn, ticker: str, session_date: date) -> Optional[Dict]:
    rows = query_db(conn, """
        SELECT price, d1_atr, pd_vp_poc, pd_vp_vah, pd_vp_val
        FROM bar_data
        WHERE date = %s AND UPPER(ticker) = UPPER(%s)
    """, (session_date, ticker))
    return rows[0] if rows else None


# ── Build POC Lists ──────────────────────────────────────────────────────────

def build_skip_prices(primary: Optional[Dict], secondary: Optional[Dict]) -> Set[float]:
    skip = set()
    for setup in [primary, secondary]:
        if setup:
            poc = float(setup.get("hvn_poc", 0) or 0)
            target = float(setup.get("target", 0) or 0)
            if poc > 0:
                skip.add(round(poc, 2))
            if target > 0:
                skip.add(round(target, 2))
    return skip


def build_filtered_poc_set(filtered_zones: List[Dict]) -> Set[float]:
    return {
        round(float(z.get("hvn_poc", 0)), 2)
        for z in filtered_zones
        if isinstance(z, dict) and float(z.get("hvn_poc", 0) or 0) > 0
    }


def classify_pocs(
    raw_pocs: List[float],
    filtered_poc_set: Set[float],
    skip_prices: Set[float],
) -> List[Dict]:
    """Classify each raw POC into: DRAW, SETUP, SKIP."""
    results = []
    for i, price in enumerate(raw_pocs, 1):
        rounded = round(price, 2)
        in_filtered = rounded in filtered_poc_set
        in_skip = any(abs(rounded - sp) < 0.01 for sp in skip_prices)

        if in_filtered and not in_skip:
            verdict = "DRAW"
        elif in_filtered and in_skip:
            verdict = "SETUP"
        else:
            verdict = "SKIP"

        results.append({
            "rank": i, "price": price, "in_filtered": in_filtered,
            "in_skip": in_skip, "verdict": verdict,
        })
    return results


# ── Chart Rendering ──────────────────────────────────────────────────────────

def draw_panel(
    ax: plt.Axes,
    title: str,
    raw_pocs: List[float],
    primary: Optional[Dict],
    secondary: Optional[Dict],
    skip_prices: Set[float],
    pocs_to_draw: List[Dict],
    bar_data: Optional[Dict],
    show_violations: bool = False,
):
    """Draw a single price-level panel showing which POC lines appear."""
    ax.set_facecolor(C_BG)

    # Determine y-range from all POC prices with padding
    all_prices = [p["price"] for p in pocs_to_draw]
    for setup in [primary, secondary]:
        if setup:
            all_prices.append(float(setup.get("hvn_poc", 0) or 0))
            all_prices.append(float(setup.get("target", 0) or 0))
            all_prices.append(float(setup.get("zone_high", 0) or 0))
            all_prices.append(float(setup.get("zone_low", 0) or 0))
    # Include PD VP levels in y-range
    if bar_data:
        for key in ("pd_vp_poc", "pd_vp_vah", "pd_vp_val"):
            val = float(bar_data.get(key, 0) or 0)
            if val > 0:
                all_prices.append(val)
    all_prices = [p for p in all_prices if p > 0]

    if not all_prices:
        ax.text(0.5, 0.5, "No data", color=C_TEXT, fontsize=14, ha="center", va="center")
        return

    y_min = min(all_prices) - 2
    y_max = max(all_prices) + 2

    # Current price marker
    if bar_data:
        cur_price = float(bar_data.get("price", 0) or 0)
        if cur_price > 0:
            ax.axhline(cur_price, color="#FFD700", linewidth=1.5, alpha=0.6, linestyle=":")
            ax.text(0.98, cur_price, f"Current ${cur_price:.2f}",
                    color="#FFD700", fontsize=7, va="bottom", ha="right",
                    transform=ax.get_yaxis_transform())

    # Prior Day Volume Profile levels
    if bar_data:
        pd_poc = float(bar_data.get("pd_vp_poc", 0) or 0)
        pd_vah = float(bar_data.get("pd_vp_vah", 0) or 0)
        pd_val = float(bar_data.get("pd_vp_val", 0) or 0)
        if pd_poc > 0:
            ax.axhline(pd_poc, color=C_PD_VP_POC, linewidth=1.5, alpha=0.7, linestyle="-")
            ax.text(0.50, pd_poc, f"PD POC ${pd_poc:.2f}", color=C_PD_VP_POC,
                    fontsize=7, va="center", ha="center", fontweight="bold",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_PD_VP_POC, alpha=0.8, linewidth=0.5))
        if pd_vah > 0:
            ax.axhline(pd_vah, color=C_PD_VP_VA, linewidth=1.0, alpha=0.6, linestyle="--")
            ax.text(0.50, pd_vah, f"PD VAH ${pd_vah:.2f}", color=C_PD_VP_VA,
                    fontsize=7, va="center", ha="center",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_PD_VP_VA, alpha=0.8, linewidth=0.5))
        if pd_val > 0:
            ax.axhline(pd_val, color=C_PD_VP_VA, linewidth=1.0, alpha=0.6, linestyle="--")
            ax.text(0.50, pd_val, f"PD VAL ${pd_val:.2f}", color=C_PD_VP_VA,
                    fontsize=7, va="center", ha="center",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_PD_VP_VA, alpha=0.8, linewidth=0.5))

    # Primary zone fill + lines
    if primary:
        zh = float(primary.get("zone_high", 0) or 0)
        zl = float(primary.get("zone_low", 0) or 0)
        poc = float(primary.get("hvn_poc", 0) or 0)
        target = float(primary.get("target", 0) or 0)
        if zh > 0 and zl > 0:
            ax.axhspan(zl, zh, alpha=C_ZONE_ALPHA, color=C_ZONE_PRI, zorder=1)
        if poc > 0:
            ax.axhline(poc, color=C_ZONE_PRI, linewidth=1.5, alpha=0.8)
            ax.text(0.02, poc, f"PRI ${poc:.2f}", color=C_ZONE_PRI, fontsize=7,
                    va="center", ha="left", fontweight="bold",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_ZONE_PRI, alpha=0.8, linewidth=0.5))
        if target > 0:
            ax.axhline(target, color=C_ZONE_PRI, linestyle="-", linewidth=2, alpha=0.9)
            ax.text(0.02, target, f"TGT ${target:.2f}", color=C_ZONE_PRI, fontsize=7,
                    va="center", ha="left", fontweight="bold",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_ZONE_PRI, alpha=0.8, linewidth=0.5))

    # Secondary zone fill + lines
    if secondary:
        zh = float(secondary.get("zone_high", 0) or 0)
        zl = float(secondary.get("zone_low", 0) or 0)
        poc = float(secondary.get("hvn_poc", 0) or 0)
        target = float(secondary.get("target", 0) or 0)
        if zh > 0 and zl > 0:
            ax.axhspan(zl, zh, alpha=C_ZONE_ALPHA, color=C_ZONE_SEC, zorder=1)
        if poc > 0:
            ax.axhline(poc, color=C_ZONE_SEC, linewidth=1.5, alpha=0.8)
            ax.text(0.02, poc, f"SEC ${poc:.2f}", color=C_ZONE_SEC, fontsize=7,
                    va="center", ha="left",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_ZONE_SEC, alpha=0.8, linewidth=0.5))
        if target > 0:
            ax.axhline(target, color=C_ZONE_SEC, linestyle="-", linewidth=2, alpha=0.9)
            ax.text(0.02, target, f"TGT ${target:.2f}", color=C_ZONE_SEC, fontsize=7,
                    va="center", ha="left", fontweight="bold",
                    transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_ZONE_SEC, alpha=0.8, linewidth=0.5))

    # POC lines
    for p in pocs_to_draw:
        price = p["price"]
        rank = p["rank"]
        verdict = p["verdict"]

        if verdict == "DRAW":
            # Normal grey dashed POC line
            ax.axhline(price, color=C_POC_LINE, linestyle="--", linewidth=1.0,
                       alpha=C_POC_ALPHA, zorder=2)
            ax.text(0.98, price, f"POC{rank}: ${price:.2f}",
                    color=C_POC_LINE, fontsize=7, va="center", ha="right",
                    alpha=0.8, transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_POC_LINE, alpha=0.5, linewidth=0.5))
        elif verdict == "SKIP" and show_violations:
            # Show what SHOULDN'T be drawn (red dashed = violation)
            ax.axhline(price, color=C_SKIP_LINE, linestyle="--", linewidth=1.0,
                       alpha=0.4, zorder=2)
            ax.text(0.98, price, f"POC{rank}: ${price:.2f}  SHOULD NOT DRAW",
                    color=C_SKIP_LINE, fontsize=7, va="center", ha="right",
                    alpha=0.7, transform=ax.get_yaxis_transform(),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=C_BG,
                              edgecolor=C_SKIP_LINE, alpha=0.5, linewidth=0.5))

    # Styling
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_ylabel("Price ($)", color=C_TEXT, fontsize=9)
    ax.tick_params(colors=C_TEXT, labelsize=8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color(C_BORDER)

    ax.set_title(title, color=C_TEXT, fontsize=11, fontweight="bold", pad=10)


def render_comparison_png(
    ticker: str,
    session_date: date,
    raw_pocs: List[float],
    filtered_zones: List[Dict],
    primary: Optional[Dict],
    secondary: Optional[Dict],
    bar_data: Optional[Dict],
    output_path: str,
):
    """Render side-by-side comparison PNG: CURRENT (bug) vs FIXED."""
    skip_prices = build_skip_prices(primary, secondary)
    filtered_poc_set = build_filtered_poc_set(filtered_zones)

    # ── Left panel: CURRENT behavior (all raw POCs, no L3+ filter) ────
    current_pocs = []
    for i, price in enumerate(raw_pocs, 1):
        rounded = round(price, 2)
        in_skip = any(abs(rounded - sp) < 0.01 for sp in skip_prices)
        if not in_skip:
            current_pocs.append({"rank": i, "price": price, "verdict": "DRAW",
                                 "in_filtered": rounded in filtered_poc_set,
                                 "in_skip": False})

    # ── Right panel: FIXED behavior (only L3+ POCs) ──────────────────
    fixed_pocs = []
    for i, price in enumerate(raw_pocs, 1):
        rounded = round(price, 2)
        in_filtered = rounded in filtered_poc_set
        in_skip = any(abs(rounded - sp) < 0.01 for sp in skip_prices)
        if in_filtered and not in_skip:
            fixed_pocs.append({"rank": i, "price": price, "verdict": "DRAW",
                               "in_filtered": True, "in_skip": False})

    # ── Build figure ─────────────────────────────────────────────────
    fig, (ax_current, ax_fixed) = plt.subplots(
        1, 2, figsize=(16, 9), facecolor=C_BG,
        gridspec_kw={"wspace": 0.15}
    )

    # Count lines for titles
    current_grey = len(current_pocs)
    fixed_grey = len(fixed_pocs)

    draw_panel(
        ax_current,
        f"CURRENT (No Filter)\n{current_grey} grey POC lines drawn",
        raw_pocs, primary, secondary, skip_prices, current_pocs, bar_data,
        show_violations=False,
    )
    draw_panel(
        ax_fixed,
        f"FIXED (L3+ Filter)\n{fixed_grey} grey POC lines drawn",
        raw_pocs, primary, secondary, skip_prices, fixed_pocs, bar_data,
        show_violations=True,
    )

    # Suptitle
    fig.suptitle(
        f"{ticker} | POC Filter Diagnostic | {session_date}",
        color=C_TEXT, fontsize=14, fontweight="bold", y=0.97,
    )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=C_ZONE_PRI, alpha=0.4, label="Primary Zone"),
        mpatches.Patch(facecolor=C_ZONE_SEC, alpha=0.4, label="Secondary Zone"),
        plt.Line2D([0], [0], color=C_POC_LINE, linestyle="--", alpha=C_POC_ALPHA,
                    linewidth=1.0, label="Grey POC (drawn)"),
        plt.Line2D([0], [0], color=C_SKIP_LINE, linestyle="--", alpha=0.4,
                    linewidth=1.0, label="Should NOT draw (sub-L3)"),
        plt.Line2D([0], [0], color="#FFD700", linestyle=":", alpha=0.6,
                    linewidth=1.5, label="Current Price"),
        plt.Line2D([0], [0], color=C_PD_VP_POC, linestyle="-", alpha=0.7,
                    linewidth=1.5, label="PD VP POC"),
        plt.Line2D([0], [0], color=C_PD_VP_VA, linestyle="--", alpha=0.6,
                    linewidth=1.0, label="PD VP VAH/VAL"),
    ]
    fig.legend(
        handles=legend_elements, loc="lower center", ncol=4,
        fontsize=8, facecolor=C_BG, edgecolor=C_BORDER,
        labelcolor=C_TEXT, framealpha=0.9,
    )

    plt.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.08)
    fig.savefig(output_path, dpi=100, facecolor=C_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  PNG saved: {output_path}")


# ── Console Diagnostic ───────────────────────────────────────────────────────

def print_diagnostic(
    raw_pocs: List[float],
    filtered_zones: List[Dict],
    primary: Optional[Dict],
    secondary: Optional[Dict],
) -> None:
    """Print text diagnostic to console."""
    skip_prices = build_skip_prices(primary, secondary)
    filtered_poc_set = build_filtered_poc_set(filtered_zones)

    # ── 1. Raw HVN POCs ──────────────────────────────────────────────
    print(header("RAW HVN POCs (hvn_pocs table - all 10)"))
    if not raw_pocs:
        print("  (none found)")
    else:
        for i, price in enumerate(raw_pocs, 1):
            print(f"  POC{i:>2}: ${price:>10.2f}")
    print(f"\n  Total: {len(raw_pocs)}")

    # ── 2. Filtered Zones ────────────────────────────────────────────
    print(header("FILTERED ZONES (zones table - should all be L3+)"))
    violations: List[Dict] = []
    if not filtered_zones:
        print("  (none found)")
    else:
        fmt = "  {zone_id:>12s} | POC: ${poc:>8.2f} | Range: ${low:>8.2f}-${high:>8.2f} | Score: {score:>5.1f} | Rank: {rank:<3s} | {flag}"
        for z in filtered_zones:
            score = float(z.get("score", 0) or 0)
            is_violation = score < MIN_ZONE_SCORE
            if is_violation:
                violations.append(z)
            print(fmt.format(
                zone_id=z.get("zone_id", "?"),
                poc=float(z.get("hvn_poc", 0) or 0),
                low=float(z.get("zone_low", 0) or 0),
                high=float(z.get("zone_high", 0) or 0),
                score=score,
                rank=z.get("rank", score_to_rank(score)),
                flag="!! BELOW L3 !!" if is_violation else "",
            ))
    print(f"\n  Total zones: {len(filtered_zones)}")
    print(f"  Unique POC prices: {len(filtered_poc_set)}")

    # ── 3. Setups ────────────────────────────────────────────────────
    print(header("SETUPS (drawn separately - skipped from POC loop)"))
    if primary:
        print(f"  PRIMARY  : POC ${float(primary.get('hvn_poc', 0) or 0):.2f}  |  Target ${float(primary.get('target', 0) or 0):.2f}")
    else:
        print("  PRIMARY  : (none)")
    if secondary:
        print(f"  SECONDARY: POC ${float(secondary.get('hvn_poc', 0) or 0):.2f}  |  Target ${float(secondary.get('target', 0) or 0):.2f}")
    else:
        print("  SECONDARY: (none)")
    if skip_prices:
        print(f"\n  Skip-list prices: {', '.join(f'${p:.2f}' for p in sorted(skip_prices))}")

    # ── 4. POC-by-POC Verdict ────────────────────────────────────────
    classified = classify_pocs(raw_pocs, filtered_poc_set, skip_prices)
    print(header("POC LINE VERDICT (what the chart should draw)"))
    print(f"  {'POC#':<6} {'Price':>10}  {'In Zones?':>10}  {'Skipped?':>10}  {'Verdict':>10}")
    print(f"  {divider(52)}")
    drawn_count = 0
    for p in classified:
        if p["verdict"] == "DRAW":
            drawn_count += 1
        print(f"  POC{p['rank']:<2}  ${p['price']:>9.2f}  "
              f"{'YES' if p['in_filtered'] else 'NO':>10}  "
              f"{'YES' if p['in_skip'] else 'NO':>10}  "
              f"{p['verdict']:>10}")

    # ── 5. Summary ───────────────────────────────────────────────────
    print(header("SUMMARY"))
    print(f"  Raw HVN POCs:           {len(raw_pocs)}")
    print(f"  Filtered zones (L3+):   {len(filtered_zones)}")
    print(f"  Setup lines (separate): {len(skip_prices)}")
    print(f"  Grey POC lines drawn:   {drawn_count}")
    print(f"  POCs correctly skipped:  {len(raw_pocs) - drawn_count}")

    if violations:
        print(f"\n  !! VIOLATIONS: {len(violations)} zone(s) below L3 stored in DB:")
        for v in violations:
            print(f"     {v.get('zone_id', '?')}  score={float(v.get('score', 0)):.1f}  rank={v.get('rank', '?')}")

    # ── 6. Prior Day Volume Profile ─────────────────────────────
    print(header("PRIOR DAY VOLUME PROFILE"))
    print("  (Fetched from bar_data table - independent of zone scoring)")
    # Note: bar_data is not passed to this function; printed in main()

    # Bug scenario count
    bug_drawn = sum(1 for p in raw_pocs
                    if not any(abs(round(p, 2) - sp) < 0.01 for sp in skip_prices))
    print(f"\n  CURRENT (no filter): {bug_drawn} grey lines (matches screenshot)")
    print(f"  FIXED   (L3+ only):  {drawn_count} grey lines")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
    if len(sys.argv) > 2:
        session_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    else:
        session_date = date.today()

    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, f"poc_filter_{ticker}_{session_date}.png")

    print(f"\n  POC Filter Diagnostic")
    print(f"  Ticker: {ticker}  |  Date: {session_date}")
    print(f"  L3 Score Floor: {MIN_ZONE_SCORE}")

    try:
        conn = psycopg2.connect(**SUPABASE_DB_CONFIG)
        conn.autocommit = True
    except Exception as e:
        print(f"\n  ERROR: Could not connect to Supabase: {e}")
        sys.exit(1)

    try:
        raw_pocs = fetch_raw_pocs(conn, ticker, session_date)
        filtered_zones = fetch_filtered_zones(conn, ticker, session_date)
        primary, secondary = fetch_setups(conn, ticker, session_date)
        bar_data = fetch_bar_data(conn, ticker, session_date)

        if not raw_pocs:
            print(f"\n  No HVN POC data found for {ticker} on {session_date}")
            sys.exit(1)

        # Console output
        print_diagnostic(raw_pocs, filtered_zones, primary, secondary)

        # Print PD VP levels
        if bar_data:
            pd_poc = float(bar_data.get("pd_vp_poc", 0) or 0)
            pd_vah = float(bar_data.get("pd_vp_vah", 0) or 0)
            pd_val = float(bar_data.get("pd_vp_val", 0) or 0)
            if pd_poc > 0:
                print(f"  PD VP POC: ${pd_poc:.2f}")
                print(f"  PD VP VAH: ${pd_vah:.2f}")
                print(f"  PD VP VAL: ${pd_val:.2f}")
            else:
                print("  PD VP levels: (not calculated)")

        # PNG output
        render_comparison_png(
            ticker, session_date,
            raw_pocs, filtered_zones, primary, secondary, bar_data,
            output_path,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
