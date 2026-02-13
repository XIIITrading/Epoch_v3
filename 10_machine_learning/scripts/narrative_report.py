"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Narrative Report Generator
XIII Trading LLC
================================================================================

Generates a human-readable, educational report from ML analysis results.
Written in plain language -- explains what the stats mean, why they matter,
and what actions to consider.

This is NOT a data dump. It's a report you can read front-to-back and
understand even without a statistics background.

Output:
  analysis/edge_audits/narrative_report_YYYYMMDD.md

Usage:
    Called automatically by run_ml_workflow.py after analyze/cycle
    Or standalone: python scripts/narrative_report.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_CONFIG, VALIDATED_EDGES, EDGE_CRITERIA,
    EDGE_AUDITS_DIR, SYSTEM_STATE_JSON, HYPOTHESIS_TRACKER_JSON,
    PENDING_EDGES_JSON, ensure_directories,
)


def _significance_explanation(p_value: float) -> str:
    """Translate p-value into plain English."""
    if p_value < 0.001:
        return "extremely strong evidence (less than 0.1% chance this is random noise)"
    elif p_value < 0.01:
        return "very strong evidence (less than 1% chance this is random)"
    elif p_value < 0.05:
        return "statistically significant (less than 5% chance this is random)"
    elif p_value < 0.10:
        return "borderline -- suggestive but not reliable enough to act on"
    elif p_value < 0.20:
        return "weak -- could easily be random variation"
    else:
        return "not significant -- likely just noise in the data"


def _confidence_explanation(confidence: str, trades: int) -> str:
    """Translate confidence level into plain English."""
    if confidence == "HIGH":
        return f"HIGH confidence ({trades} trades -- large enough sample to trust)"
    elif confidence == "MEDIUM":
        return f"MEDIUM confidence ({trades} trades -- usable but monitor closely)"
    else:
        return f"LOW confidence ({trades} trades -- too few to rely on, needs more data)"


def _effect_explanation(effect_pp: float) -> str:
    """Translate effect size into plain English."""
    abs_effect = abs(effect_pp)
    direction = "higher" if effect_pp > 0 else "lower"

    if abs_effect > 15:
        strength = "massive"
    elif abs_effect > 10:
        strength = "very large"
    elif abs_effect > 5:
        strength = "meaningful"
    elif abs_effect > 3:
        strength = "moderate"
    else:
        strength = "small"

    return f"{strength} -- win rate is {abs_effect:.1f} percentage points {direction} than your overall average"


def _health_icon(status: str) -> str:
    """Get status icon."""
    return {
        "HEALTHY": "OK",
        "WEAKENING": "WARNING",
        "DEGRADED": "FAILED",
        "INCONCLUSIVE": "UNKNOWN",
    }.get(status, "?")


def _run_cont_score_deep_dive(health_min: int, health_max: int, label: str) -> str:
    """
    Query the database for sub-group breakdowns of a continuation score tier.
    Returns markdown text with Direction, Zone Type, and Model sub-sections.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception:
        return "\n*Could not connect to database for deep-dive.*\n"

    date_filter = "m.date >= CURRENT_DATE - INTERVAL '30 days'"
    health_filter = f"ei.health_score >= {health_min} AND ei.health_score <= {health_max}"

    md = ""

    try:
        # ----- Direction breakdown -----
        cur.execute(f"""
            SELECT m.direction,
                COUNT(*) as total,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
                ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE {health_filter} AND {date_filter}
            GROUP BY m.direction ORDER BY m.direction
        """)
        dir_rows = cur.fetchall()

        cur.execute(f"""
            SELECT m.direction,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
            FROM trades_m5_r_win m WHERE {date_filter}
            GROUP BY m.direction
        """)
        base_dir = {r["direction"]: float(r["baseline_wr"]) for r in cur.fetchall()}

        md += f"\n**By Direction** (Is the {label} edge biased toward LONGs or SHORTs?)\n\n"
        md += "| Direction | Trades | WR | Baseline | Effect | Avg R |\n"
        md += "|-----------|--------|----|---------:|-------:|------:|\n"
        for r in dir_rows:
            d = r["direction"]
            wr = float(r["win_rate"])
            bwr = base_dir.get(d, 0)
            effect = round(wr - bwr, 1)
            md += f"| {d} | {r['total']} | {wr:.1f}% | {bwr:.1f}% | {effect:+.1f}pp | {float(r['avg_r']):+.3f} |\n"
        md += "\n"

        # ----- Zone Type breakdown -----
        cur.execute(f"""
            SELECT m.zone_type,
                COUNT(*) as total,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
                ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE {health_filter} AND {date_filter}
            GROUP BY m.zone_type ORDER BY m.zone_type
        """)
        zone_rows = cur.fetchall()

        cur.execute(f"""
            SELECT m.zone_type,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
            FROM trades_m5_r_win m WHERE {date_filter}
            GROUP BY m.zone_type
        """)
        base_zone = {r["zone_type"]: float(r["baseline_wr"]) for r in cur.fetchall()}

        md += f"**By Zone Type** (Primary vs Secondary)\n\n"
        md += "| Zone Type | Trades | WR | Baseline | Effect | Avg R |\n"
        md += "|-----------|--------|----|---------:|-------:|------:|\n"
        for r in zone_rows:
            zt = r["zone_type"] or "NULL"
            wr = float(r["win_rate"])
            bwr = base_zone.get(r["zone_type"], 0)
            effect = round(wr - bwr, 1)
            md += f"| {zt} | {r['total']} | {wr:.1f}% | {bwr:.1f}% | {effect:+.1f}pp | {float(r['avg_r']):+.3f} |\n"
        md += "\n"

        # ----- Model breakdown -----
        cur.execute(f"""
            SELECT
                CASE WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'CONTINUATION'
                     ELSE 'REJECTION' END as model_type,
                COUNT(*) as total,
                SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
                ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
            FROM trades_m5_r_win m
            LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
            WHERE {health_filter} AND {date_filter}
            GROUP BY model_type ORDER BY model_type
        """)
        model_rows = cur.fetchall()

        cur.execute(f"""
            SELECT
                CASE WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'CONTINUATION'
                     ELSE 'REJECTION' END as model_type,
                ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
            FROM trades_m5_r_win m WHERE {date_filter}
            GROUP BY model_type
        """)
        base_model = {r["model_type"]: float(r["baseline_wr"]) for r in cur.fetchall()}

        md += f"**By Entry Model** (Continuation vs Rejection -- is the score biased?)\n\n"
        md += "| Model Type | Trades | WR | Baseline | Effect | Avg R |\n"
        md += "|------------|--------|----|---------:|-------:|------:|\n"
        for r in model_rows:
            mt = r["model_type"]
            wr = float(r["win_rate"])
            bwr = base_model.get(mt, 0)
            effect = round(wr - bwr, 1)
            md += f"| {mt} | {r['total']} | {wr:.1f}% | {bwr:.1f}% | {effect:+.1f}pp | {float(r['avg_r']):+.3f} |\n"
        md += "\n"

    except Exception as e:
        md += f"\n*Deep-dive query error: {e}*\n"
    finally:
        conn.close()

    return md


def generate_narrative_report(
    analysis_result: Dict = None,
    validation_result: List[Dict] = None,
    hypothesis_result: Dict = None,
) -> str:
    """
    Generate the full narrative report from analysis results.

    Can be called with any combination of results -- it will include
    sections for whatever data is provided.
    """
    now = datetime.now()

    # Load state files for context
    system_state = {}
    if SYSTEM_STATE_JSON.exists():
        with open(SYSTEM_STATE_JSON, "r") as f:
            system_state = json.load(f)

    hypothesis_data = {"hypotheses": []}
    if HYPOTHESIS_TRACKER_JSON.exists():
        with open(HYPOTHESIS_TRACKER_JSON, "r") as f:
            hypothesis_data = json.load(f)

    pending_edges = []
    if PENDING_EDGES_JSON.exists():
        with open(PENDING_EDGES_JSON, "r") as f:
            pending_edges = json.load(f)

    # =====================================================================
    # BUILD REPORT
    # =====================================================================

    sections = []

    # ----- HEADER -----
    sections.append(f"""# EPOCH ML Analysis Report
## {now.strftime('%B %d, %Y')}

> This report explains your trading system's statistical edges in plain language.
> Every claim is backed by data from your actual trades in `trades_m5_r_win`.
> Read it front-to-back -- it's designed to teach as it goes.

---
""")

    # ----- QUICK GLOSSARY -----
    sections.append("""## How to Read This Report

Before diving in, here are the key terms you'll see throughout:

| Term | What It Means |
|------|---------------|
| **Win Rate** | Percentage of trades that hit 1R profit before the stop was triggered |
| **Baseline** | Your overall win rate across ALL trades -- the number to beat |
| **Effect (pp)** | "Percentage points" -- how much better or worse than baseline. +5pp means the win rate is 5 points higher than average |
| **p-value** | The probability this result happened by pure chance. Below 0.05 = statistically significant. Think of it as a confidence meter -- lower is better |
| **Chi-squared** | The statistical test used to compare two groups. You don't need to understand the math -- just look at the p-value it produces |
| **Sample Size (N)** | How many trades are in the group. More trades = more trustworthy. We require at least 30 for any conclusion |
| **Significant** | Passes ALL three tests: p < 0.05, effect > 3pp, and N >= 30 |

---
""")

    # ----- BASELINE SECTION -----
    baseline = system_state.get("baseline", {})
    if analysis_result:
        baseline = analysis_result.get("baseline", baseline)

    if baseline.get("total_trades"):
        sections.append(f"""## Your Baseline Performance

This is your system's overall performance -- the benchmark everything else is measured against.

| Metric | Value | What It Means |
|--------|-------|---------------|
| **Total Trades** | {baseline['total_trades']:,} | Number of trades in this analysis window |
| **Win Rate** | {baseline.get('win_rate', 0):.1f}% | {baseline['total_trades']:,} trades, {round(baseline['total_trades'] * baseline.get('win_rate', 0) / 100):,} winners |
| **Average R** | {baseline.get('avg_r', 0):+.3f} | Each trade averages {baseline.get('avg_r', 0):+.3f}R profit. Positive = profitable system |
| **Std Dev R** | {baseline.get('std_r', 0):.3f} | How much individual trades vary. Higher = more volatile results |
| **Period** | {baseline.get('period_start', '?')} to {baseline.get('period_end', '?')} | Date range of trades analyzed |

**Bottom line**: Your system wins {baseline.get('win_rate', 0):.1f}% of the time with an average return of {baseline.get('avg_r', 0):+.3f}R per trade. Every edge below is compared against this {baseline.get('win_rate', 0):.1f}% baseline.

---
""")

    # ----- EXISTING EDGE HEALTH -----
    edge_health = system_state.get("edge_health", {})
    if validation_result or edge_health:
        results_to_use = validation_result if validation_result else []

        sections.append("""## Health Check: Your Existing Validated Edges

These are the edges you previously identified and built into your trading rules.
This section checks whether they still hold up against fresh data.

""")

        if results_to_use:
            for r in results_to_use:
                if r.get("status") == "NO_DEFINITION":
                    continue

                status = r.get("status", "UNKNOWN")
                icon = _health_icon(status)
                name = r["edge"]
                stored = r.get("stored_effect_pp", 0)
                current = r.get("current_effect_pp", 0)
                p_val = r.get("p_value", 1.0)
                group_wr = r.get("group_win_rate", 0)
                base_wr = r.get("baseline_win_rate", 0)
                n = r.get("group_trades", 0)

                sections.append(f"""### {name} -- [{icon}]

**What this edge claims**: """)

                # Find the original edge definition for context
                original = next((e for e in VALIDATED_EDGES if e["name"] == name), None)
                if original:
                    sections.append(f"""{original.get('action', 'N/A')}
**Original effect**: {stored:+.1f} percentage points
""")

                sections.append(f"""**Current measurement**:
- This group's win rate: **{group_wr:.1f}%** across {n:,} trades
- Overall baseline win rate: **{base_wr:.1f}%**
- Current effect: **{current:+.1f}pp** (originally stored as {stored:+.1f}pp)
- Statistical significance: p = {p_val:.4f} -- {_significance_explanation(p_val)}

""")

                if status == "HEALTHY":
                    sections.append(f"""**Verdict: HEALTHY** -- This edge is performing as expected. The current effect ({current:+.1f}pp) is close to the stored value ({stored:+.1f}pp). Continue using this rule.

""")
                elif status == "WEAKENING":
                    sections.append(f"""**Verdict: WEAKENING** -- This edge still points in the right direction, but it's weaker than originally measured. The current effect ({current:+.1f}pp) is noticeably lower than the stored value ({stored:+.1f}pp). Keep using it but watch closely -- if it continues to fade, it may need to be retired.

""")
                elif status == "DEGRADED":
                    if (stored > 0 and current <= 0) or (stored < 0 and current >= 0):
                        sections.append(f"""**Verdict: DEGRADED -- SIGN REVERSED** -- This is a serious finding. The edge has flipped direction entirely. It was stored as {stored:+.1f}pp but now measures at {current:+.1f}pp. This means the condition that was supposed to help (or hurt) your trading is doing the opposite.

**Recommendation**: This edge should be removed from your validated rules. The original measurement may have been based on different win criteria (the old `trades` table) or a different time period. With `trades_m5_r_win` as the sole source, this pattern does not hold.

""")
                    else:
                        sections.append(f"""**Verdict: DEGRADED** -- This edge has weakened significantly. The stored effect was {stored:+.1f}pp but it now shows {current:+.1f}pp with p={p_val:.4f}.

**Recommendation**: Consider removing this edge from your validated rules and re-evaluating with more data.

""")
                elif status == "INCONCLUSIVE":
                    sections.append(f"""**Verdict: INCONCLUSIVE** -- We cannot confirm or deny this edge with the current data. The p-value of {p_val:.4f} means there's a {p_val*100:.1f}% chance the observed difference is just random noise. This doesn't mean the edge is dead -- it means we need more data or a longer analysis window to draw conclusions.

**What to do**: Don't remove it yet, but don't rely on it heavily either. Re-test with a larger date range (--days 60 or --days 90).

""")

        sections.append("---\n")

    # ----- NEWLY DISCOVERED EDGES -----
    significant_edges = []
    if analysis_result:
        significant_edges = analysis_result.get("significant_edges", [])

    if significant_edges:
        sections.append(f"""## Newly Discovered Edges

The system scanned {len(analysis_result.get('scans', {}))} indicator columns across all {baseline.get('total_trades', 0):,} trades. Below are the groups that showed a statistically significant difference from your baseline.

**What "significant" means**: Each of these passed three tests:
1. The effect is large enough to matter (> {EDGE_CRITERIA['effect_size_threshold']}pp)
2. The result is unlikely to be random chance (p < {EDGE_CRITERIA['p_value_threshold']})
3. There are enough trades to trust the result (N >= {EDGE_CRITERIA['min_sample_medium']})

""")

        # Sort by absolute effect
        sorted_edges = sorted(significant_edges, key=lambda x: abs(x["effect_pp"]), reverse=True)

        # Display name overrides (overlay -- DB fields unchanged)
        display_names = {
            "health_tier": "cont_score",
        }

        for i, edge in enumerate(sorted_edges, 1):
            direction = "POSITIVE (trade)" if edge["effect_pp"] > 0 else "NEGATIVE (skip/avoid)"
            conf = _confidence_explanation(edge["confidence"], edge["trades"])
            sig = _significance_explanation(edge["p_value"])
            effect_desc = _effect_explanation(edge["effect_pp"])

            display_ind = display_names.get(edge["indicator"], edge["indicator"])

            sections.append(f"""### {i}. {display_ind} = {edge['value']} [{direction}]

- **Win Rate**: {edge['win_rate']:.1f}% vs {baseline.get('win_rate', 0):.1f}% baseline
- **Effect**: {edge['effect_pp']:+.1f}pp -- {effect_desc}
- **Evidence**: p = {edge['p_value']:.4f} -- {sig}
- **Sample**: {conf}

""")

            # Add contextual interpretation
            if edge["indicator"] == "health_tier":
                if "STRONG" in edge["value"]:
                    sections.append("""**Interpretation**: When the Continuation Score (the composite of all 10 indicators, formerly called "health score") is 8 or above, your system dramatically outperforms. This makes intuitive sense -- when everything is aligned in one direction, continuation trades work especially well. The sample is small (MEDIUM confidence) so this needs monitoring, but the effect size is huge.

""")
                    # Deep-dive sub-sections
                    sections.append(_run_cont_score_deep_dive(8, 10, "STRONG"))

                elif "MODERATE" in edge["value"]:
                    sections.append("""**Interpretation**: Continuation Scores of 6-7 also show a clear advantage. With nearly 1,000 trades, this is a reliable finding. It suggests your indicator framework genuinely captures something meaningful about trade quality -- specifically, how well conditions support a continuation move.

""")
                    sections.append(_run_cont_score_deep_dive(6, 7, "MODERATE"))

                elif "WEAK" in edge["value"]:
                    sections.append("""**Interpretation**: When the Continuation Score drops to 4-5, performance falls below average. This is the mirror image of the STRONG/MODERATE findings -- fewer indicators aligned means weaker continuation conditions. These setups may actually be better suited for rejection plays.

""")
                    sections.append(_run_cont_score_deep_dive(4, 5, "WEAK"))

            elif edge["indicator"] == "m15_structure":
                if edge["value"] == "BEAR":
                    sections.append("""**Interpretation**: When the M15 timeframe shows bearish structure, your trades underperform significantly. This is a strong skip signal -- regardless of other factors, M15 BEAR structure is a headwind.

""")
                elif edge["value"] == "BULL":
                    sections.append("""**Interpretation**: M15 bullish structure is a tailwind for your trades. This makes sense -- when the 15-minute chart agrees with your trade direction, you have structural support. Combined with the BEAR finding, M15 structure is clearly an important filter.

""")

            elif edge["indicator"] == "h1_structure" and edge["value"] == "BEAR":
                sections.append("""**Interpretation**: This is counterintuitive. Your original validated edge claimed H1 NEUTRAL was the sweet spot (+36pp). But with `trades_m5_r_win` as sole source, H1 BEAR actually shows a positive edge while NEUTRAL is flat. This suggests the original H1 NEUTRAL finding may have been an artifact of the old win calculation.

""")

            elif edge["indicator"] == "sma_alignment":
                if edge["value"] == "BULL":
                    sections.append("""**Interpretation**: This is counterintuitive -- when SMA9 is above SMA21 (bullish alignment), your trades actually perform *worse* than average. This could mean your system works better in mean-reversion contexts rather than trend-following ones, or that "obvious" bullish alignment attracts crowded trades.

""")
                elif edge["value"] == "BEAR":
                    sections.append("""**Interpretation**: Bearish SMA alignment (SMA9 below SMA21) shows better performance. Combined with the BULL alignment finding, this suggests your zone-based entries work better when going against the short-term SMA trend -- a contrarian signal.

""")

            elif edge["indicator"] == "stop_distance_bucket" and "TIGHT" in edge["value"]:
                sections.append("""**Interpretation**: Tight zones (very small stop distance) perform well. This may be because tight zones represent precise, high-conviction levels where price respects the zone boundary cleanly. Note: this contradicts the original "Absorption Zone Skip" edge which claimed small zones should be skipped. The difference is likely due to the switch from `trades` to `trades_m5_r_win` win classification.

""")

        sections.append("---\n")

    # ----- NON-SIGNIFICANT INDICATORS -----
    if analysis_result:
        scans = analysis_result.get("scans", {})
        non_sig_indicators = []

        for ind_name, scan_data in scans.items():
            has_sig = any(b["is_significant"] for b in scan_data.get("buckets", []))
            if not has_sig:
                non_sig_indicators.append(ind_name)

        if non_sig_indicators:
            sections.append(f"""## What Showed No Edge

These indicators were scanned but showed NO statistically significant difference from baseline. This is actually useful information -- it tells you what does NOT matter for your system.

| Indicator | What It Means |
|-----------|---------------|
""")
            explanations = {
                "direction": "LONG vs SHORT -- your system performs equally in both directions",
                "model": "EPCH1 vs EPCH2 vs EPCH3 vs EPCH4 -- no model is significantly better than another",
                "vwap_position": "Price above/below VWAP -- doesn't affect your win rate",
                "zone_type": "PRIMARY vs SECONDARY zones -- both perform similarly",
                "h4_structure": "H4 structure -- all trades were in NEUTRAL (only one value, can't compare)",
                "m5_structure": "M5 structure -- close to significant but didn't pass the threshold",
                "sma_momentum_label": "SMA momentum (WIDENING/NARROWING/STABLE) -- suggestive but not significant",
            }

            for ind in sorted(non_sig_indicators):
                desc = explanations.get(ind, "No significant difference between groups")
                sections.append(f"| {ind} | {desc} |\n")

            sections.append("""
**Why this matters**: You can stop worrying about these factors as trade filters. They don't meaningfully affect your outcomes. Focus your attention on the indicators that DO show edges (health score, M15 structure, SMA alignment).

---
""")

    # ----- DRIFT ALERTS -----
    drift_alerts = []
    if analysis_result:
        drift_alerts = analysis_result.get("drift_alerts", [])

    if drift_alerts:
        sections.append("""## Drift Alerts

Your system's baseline has shifted compared to the previous measurement:

""")
        for alert in drift_alerts:
            sections.append(f"- **{alert['type']}**: {alert['message']}\n")

        sections.append("""
**What drift means**: Trading edges can decay over time as market conditions change. If your baseline win rate or average R shifts significantly, it could mean the market environment has changed, or that recent trades are behaving differently than historical ones. This isn't necessarily bad -- just something to monitor.

---
""")

    # ----- PENDING ACTIONS -----
    if pending_edges:
        # Separate by action type
        removals = [e for e in pending_edges if e.get("action") == "REVIEW_FOR_REMOVAL"]
        approvals = [e for e in pending_edges if e.get("action") == "APPROVE_FOR_ADDITION"]

        sections.append(f"""## Pending Actions ({len(pending_edges)} items)

These items need your decision before the system will act on them.

""")

        if removals:
            sections.append("""### Edges to Consider Removing

These existing validated edges have degraded and may be doing more harm than good:

""")
            for r in removals:
                tr = r.get("test_result", {})
                sections.append(f"""- **{r['name']}**: Was stored as {tr.get('stored_effect_pp', '?'):+.1f}pp, now measures at {tr.get('current_effect_pp', '?'):+.1f}pp
  - To remove: `python scripts/run_ml_workflow.py remove-edge "{r['name']}"`

""")

        if approvals:
            sections.append("""### New Edges to Consider Adding

These were discovered by the hypothesis engine and passed all statistical tests:

""")
            for a in approvals:
                tr = a.get("test_result", {})
                ed = a.get("edge_definition", {})
                sections.append(f"""- **{a.get('name', 'Unknown')}** (Hypothesis {a.get('hypothesis_id', '?')})
  - Effect: {tr.get('effect_size_pp', ed.get('effect_size_pp', '?')):+.1f}pp | Win Rate: {tr.get('group_win_rate', '?')}% | N = {tr.get('group_trades', '?')} | p = {tr.get('p_value', '?')}
  - Action: {ed.get('action', 'TBD')}
  - To approve: `python scripts/run_ml_workflow.py approve-edge {a.get('hypothesis_id', '?')}`

""")

        sections.append("""**Important**: You don't have to act on all of these at once. Review the findings above, ask questions, and approve/remove edges when you're confident in the decision.

---
""")

    # ----- RECOMMENDATIONS -----
    sections.append("""## Summary & Recommendations

""")

    # Build dynamic recommendations
    recs = []

    # Check for degraded edges
    if validation_result:
        degraded = [r for r in validation_result if r.get("status") == "DEGRADED"]
        if degraded:
            names = ", ".join(d["edge"] for d in degraded)
            recs.append(f"**Clean house**: {len(degraded)} existing edge(s) have degraded ({names}). These were likely validated against the old `trades` table with different win logic. Consider removing them since they don't hold under the canonical `trades_m5_r_win` outcomes.")

    # Check for strong new edges
    if significant_edges:
        strong = [e for e in significant_edges if abs(e["effect_pp"]) > 5 and e["confidence"] == "HIGH"]
        if strong:
            recs.append(f"**Strong new edges found**: {len(strong)} indicator conditions show meaningful effects with HIGH confidence. The Continuation Score tiers and M15 structure are particularly promising -- both have large samples and strong effects.")

    # Continuation Score theme
    health_edges = [e for e in significant_edges if e.get("indicator") == "health_tier"]
    if len(health_edges) >= 2:
        recs.append("**Continuation Score is your best filter**: Multiple score tiers show significant edges. Higher score = better continuation performance. This validates that your 10-factor indicator framework captures real trading edge -- specifically how well conditions support a continuation move. Consider using CONT score >= 6 as a minimum threshold, and favor continuation entries (EPCH1/3) when score is 8+. See `docs/indicator_playbook.md` for the full CONT/REJECT signal mapping.")

    # M15 structure theme
    m15_edges = [e for e in significant_edges if e.get("indicator") == "m15_structure"]
    if len(m15_edges) >= 2:
        recs.append("**M15 structure matters**: Both BULL and BEAR M15 structure show significant effects in opposite directions. M15 BULL is a strong go signal, M15 BEAR is a strong skip signal. This is an actionable filter for your live trading.")

    # SMA contrarian theme
    sma_edges = [e for e in significant_edges if e.get("indicator") == "sma_alignment"]
    if len(sma_edges) >= 2:
        recs.append("**SMA alignment is contrarian**: Your system performs better when SMA alignment is BEAR (SMA9 < SMA21) and worse when it's BULL. This suggests your zone-based entries work better as mean-reversion plays rather than trend-following. Worth investigating further.")

    if not recs:
        recs.append("No urgent recommendations at this time. Continue monitoring edge health and running periodic analysis cycles.")

    for i, rec in enumerate(recs, 1):
        sections.append(f"{i}. {rec}\n\n")

    # ----- FOOTER -----
    sections.append(f"""---

## Next Steps

- **Ask questions**: This report is your starting point for discussion in Claude Code. Ask about anything that's unclear.
- **Deep dive**: Want more detail on a specific edge? Ask me to run `test-hypothesis` with different date ranges.
- **Approve edges**: When you're ready, use `approve-edge` to promote new edges into your validated set.
- **Remove edges**: Use `remove-edge` to clean out degraded edges.
- **Re-run**: After making changes, run `python scripts/run_ml_workflow.py cycle` to see the updated picture.

---

*Report generated {now.strftime('%Y-%m-%d %H:%M:%S')} by narrative_report.py*
*Data source: trades_m5_r_win (sole source of truth)*
*Statistical method: Chi-squared test with Yates correction (falls back to Fisher's exact for small samples)*
""")

    return "\n".join(sections)


def build_and_save_report(
    analysis_result: Dict = None,
    validation_result: List[Dict] = None,
    hypothesis_result: Dict = None,
) -> Path:
    """Generate the narrative report and save to disk."""
    ensure_directories()

    report = generate_narrative_report(
        analysis_result=analysis_result,
        validation_result=validation_result,
        hypothesis_result=hypothesis_result,
    )

    date_str = datetime.now().strftime("%Y%m%d")
    report_path = EDGE_AUDITS_DIR / f"narrative_report_{date_str}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"  Narrative report: {report_path}")
    return report_path


if __name__ == "__main__":
    # Standalone run -- loads latest state files and generates report
    print("=" * 60)
    print("  EPOCH ML - Narrative Report Generator")
    print("=" * 60)

    path = build_and_save_report()
    print(f"\n  Report saved to: {path}")
    print("  Open this file to read your analysis.")
