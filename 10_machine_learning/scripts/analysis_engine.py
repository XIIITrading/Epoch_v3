"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Analysis Engine
XIII Trading LLC
================================================================================

Computes baseline metrics, per-indicator breakdowns, and detects drift.
Writes audit reports and updates system_state.json.

Output:
  - Audit report in analysis/edge_audits/audit_YYYYMMDD.md
  - Updated system_state.json with fresh baseline and drift alerts
  - Console summary with drift detection

Usage:
    python run_ml_workflow.py analyze
    python run_ml_workflow.py analyze --days 30
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_CONFIG, INDICATOR_SCAN_QUERIES, EDGE_CRITERIA,
    EDGE_AUDITS_DIR, ensure_directories,
)
from scripts.statistical_tests import run_full_test, confidence_level
from scripts.state_manager import StateManager


class AnalysisEngine:
    """
    Computes system-wide analysis: baseline metrics, indicator breakdowns, drift detection.

    All data sourced from trades_m5_r_win (sole source of truth).
    """

    DRIFT_THRESHOLD_PP = 2.0  # Movement > 2pp from prior state triggers alert

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.state = StateManager()
        print("  Connected to Supabase")

    def _execute(self, query: str, params: list = None) -> List[Dict]:
        """Execute query and return list of dicts."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def _execute_single(self, query: str, params: list = None) -> Dict:
        """Execute query expecting single row."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else {}

    def compute_baseline(self, start_date: str, end_date: str) -> Dict:
        """
        Compute overall baseline metrics from trades_m5_r_win.

        Returns dict with total_trades, win_rate, avg_r, std_r.
        """
        result = self._execute_single("""
            SELECT
                COUNT(*) as total_trades,
                ROUND(SUM(CASE WHEN is_winner THEN 1 ELSE 0 END)::numeric
                      / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
                ROUND(AVG(pnl_r)::numeric, 3) as avg_r,
                ROUND(STDDEV(pnl_r)::numeric, 3) as std_r,
                MIN(date)::text as period_start,
                MAX(date)::text as period_end
            FROM trades_m5_r_win
            WHERE date >= %s AND date <= %s
        """, [start_date, end_date])

        return {
            "total_trades": int(result.get("total_trades", 0) or 0),
            "win_rate": float(result.get("win_rate", 0) or 0),
            "avg_r": float(result.get("avg_r", 0) or 0),
            "std_r": float(result.get("std_r", 0) or 0),
            "period_start": result.get("period_start"),
            "period_end": result.get("period_end"),
        }

    def scan_indicators(self, start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """
        Scan all indicator columns for edge candidates.

        Returns dict mapping indicator_name -> list of {value, wins, total, win_rate, effect_pp, ...}
        """
        # Get baseline for comparison
        baseline = self.compute_baseline(start_date, end_date)
        baseline_wr = baseline["win_rate"]
        baseline_trades = baseline["total_trades"]
        baseline_wins = round(baseline_trades * baseline_wr / 100)

        scans = {}

        for indicator_name, scan_def in INDICATOR_SCAN_QUERIES.items():
            rows = self._execute(scan_def["query"], [start_date, end_date])

            buckets = []
            for row in rows:
                value = str(row.get("indicator_value", "NULL"))
                wins = int(row.get("wins", 0) or 0)
                total = int(row.get("total", 0) or 0)

                if total == 0:
                    continue

                wr = round(wins / total * 100, 1)
                effect_pp = round(wr - baseline_wr, 1)
                conf = confidence_level(total)

                # Run statistical test
                test = run_full_test(wins, total, baseline_wins, baseline_trades)

                buckets.append({
                    "value": value,
                    "wins": wins,
                    "total": total,
                    "win_rate": wr,
                    "effect_pp": effect_pp,
                    "p_value": round(test.p_value, 4),
                    "confidence": conf,
                    "is_significant": test.is_significant,
                })

            scans[indicator_name] = {
                "description": scan_def.get("description", ""),
                "buckets": sorted(buckets, key=lambda x: abs(x["effect_pp"]), reverse=True),
            }

        return scans

    def detect_drift(self, new_baseline: Dict) -> List[Dict]:
        """
        Compare new baseline against stored state to detect drift.

        Returns list of drift alerts.
        """
        state = self.state.load_system_state()
        old_baseline = state.get("baseline", {})
        alerts = []

        if not old_baseline.get("total_trades"):
            # No prior state, no drift to detect
            return alerts

        old_wr = old_baseline.get("win_rate", 0)
        new_wr = new_baseline.get("win_rate", 0)
        wr_drift = round(new_wr - old_wr, 1)

        if abs(wr_drift) > self.DRIFT_THRESHOLD_PP:
            direction = "UP" if wr_drift > 0 else "DOWN"
            alerts.append({
                "type": f"BASELINE_WR_{direction}",
                "message": f"Baseline win rate drifted {wr_drift:+.1f}pp: {old_wr:.1f}% -> {new_wr:.1f}%",
                "old_value": old_wr,
                "new_value": new_wr,
                "drift_pp": wr_drift,
            })

        old_avg_r = old_baseline.get("avg_r", 0)
        new_avg_r = new_baseline.get("avg_r", 0)
        r_drift = round(new_avg_r - old_avg_r, 3)

        if abs(r_drift) > 0.1:  # 0.1R threshold
            direction = "UP" if r_drift > 0 else "DOWN"
            alerts.append({
                "type": f"BASELINE_R_{direction}",
                "message": f"Baseline avg R drifted {r_drift:+.3f}: {old_avg_r:.3f} -> {new_avg_r:.3f}",
                "old_value": old_avg_r,
                "new_value": new_avg_r,
                "drift_r": r_drift,
            })

        return alerts

    def run_analysis(
        self,
        days: int = 30,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """
        Run full analysis cycle: baseline + indicator scan + drift detection.
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
            start_date = start_dt.strftime("%Y-%m-%d")

        print(f"\n  Analysis period: {start_date} to {end_date}")

        # Step 1: Compute baseline
        print("\n  Computing baseline...")
        baseline = self.compute_baseline(start_date, end_date)
        print(f"    Trades: {baseline['total_trades']}")
        print(f"    Win Rate: {baseline['win_rate']:.1f}%")
        print(f"    Avg R: {baseline['avg_r']:.3f}")
        print(f"    Std R: {baseline['std_r']:.3f}")

        # Step 2: Detect drift
        print("\n  Detecting drift...")
        drift_alerts = self.detect_drift(baseline)
        if drift_alerts:
            for alert in drift_alerts:
                print(f"    !! {alert['message']}")
        else:
            print("    No significant drift detected")

        # Step 3: Scan indicators
        print("\n  Scanning indicators...")
        scans = self.scan_indicators(start_date, end_date)

        significant_edges = []
        for ind_name, scan_data in scans.items():
            for bucket in scan_data["buckets"]:
                if bucket["is_significant"]:
                    significant_edges.append({
                        "indicator": ind_name,
                        "value": bucket["value"],
                        "effect_pp": bucket["effect_pp"],
                        "win_rate": bucket["win_rate"],
                        "trades": bucket["total"],
                        "p_value": bucket["p_value"],
                        "confidence": bucket["confidence"],
                    })

        print(f"    Indicators scanned: {len(scans)}")
        print(f"    Significant edges found: {len(significant_edges)}")

        if significant_edges:
            print("\n    Significant edges:")
            for se in sorted(significant_edges, key=lambda x: abs(x["effect_pp"]), reverse=True):
                print(f"      {se['indicator']}={se['value']}: {se['effect_pp']:+.1f}pp "
                      f"(WR {se['win_rate']:.1f}%, N={se['trades']}, p={se['p_value']:.4f})")

        # Step 4: Update state
        state = self.state.load_system_state()
        state["baseline"] = baseline
        state["drift_alerts"] = drift_alerts
        self.state.save_system_state(state)

        # Log drift alerts to changelog
        for alert in drift_alerts:
            self.state.append_changelog("DRIFT_ALERT", alert["message"], alert)

        # Step 5: Write audit report
        ensure_directories()
        report = self._generate_audit_report(baseline, scans, significant_edges, drift_alerts)
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = EDGE_AUDITS_DIR / f"audit_{date_str}.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n  Audit report: {report_path}")

        return {
            "baseline": baseline,
            "scans": scans,
            "significant_edges": significant_edges,
            "drift_alerts": drift_alerts,
        }

    def _generate_audit_report(
        self,
        baseline: Dict,
        scans: Dict,
        significant_edges: List[Dict],
        drift_alerts: List[Dict],
    ) -> str:
        """Generate comprehensive audit report in markdown."""
        now = datetime.now()

        md = f"""# System Analysis Audit

**Generated**: {now.isoformat()}
**Source**: trades_m5_r_win (sole source of truth)
**Period**: {baseline.get('period_start', 'N/A')} to {baseline.get('period_end', 'N/A')}

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| Total Trades | {baseline['total_trades']} |
| Win Rate | {baseline['win_rate']:.1f}% |
| Avg R | {baseline['avg_r']:.3f} |
| Std R | {baseline['std_r']:.3f} |

---

"""
        if drift_alerts:
            md += "## Drift Alerts\n\n"
            for alert in drift_alerts:
                md += f"- **{alert['type']}**: {alert['message']}\n"
            md += "\n---\n\n"

        md += "## Significant Edges (p < 0.05, effect > 3pp, N >= 30)\n\n"
        md += "| Indicator | Value | Effect | Win Rate | Trades | p-value | Confidence |\n"
        md += "|-----------|-------|--------|----------|--------|---------|------------|\n"

        for se in sorted(significant_edges, key=lambda x: abs(x["effect_pp"]), reverse=True):
            md += (
                f"| {se['indicator']} | {se['value']} "
                f"| {se['effect_pp']:+.1f}pp "
                f"| {se['win_rate']:.1f}% "
                f"| {se['trades']} "
                f"| {se['p_value']:.4f} "
                f"| {se['confidence']} |\n"
            )

        if not significant_edges:
            md += "| — | No significant edges found | — | — | — | — | — |\n"

        md += "\n---\n\n## Full Indicator Scan\n\n"

        for ind_name, scan_data in sorted(scans.items()):
            md += f"### {ind_name}\n"
            md += f"*{scan_data.get('description', '')}*\n\n"
            md += "| Value | Trades | Win Rate | Effect | p-value | Sig? |\n"
            md += "|-------|--------|----------|--------|---------|------|\n"

            for bucket in scan_data["buckets"]:
                sig_mark = "**YES**" if bucket["is_significant"] else "no"
                md += (
                    f"| {bucket['value']} "
                    f"| {bucket['total']} "
                    f"| {bucket['win_rate']:.1f}% "
                    f"| {bucket['effect_pp']:+.1f}pp "
                    f"| {bucket['p_value']:.4f} "
                    f"| {sig_mark} |\n"
                )
            md += "\n"

        md += f"\n---\n\n*Auto-generated by analysis_engine.py -- {now.isoformat()}*\n"
        return md

    def close(self):
        if self.conn:
            self.conn.close()


def run_analysis(days: int = 30, start_date: str = None, end_date: str = None):
    """Entry point for system analysis."""
    print("\n" + "=" * 60)
    print("  EPOCH ML - System Analysis")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 60)

    engine = AnalysisEngine()
    try:
        result = engine.run_analysis(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

        # Print summary
        print("\n" + "=" * 60)
        print("  ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"  Baseline: {result['baseline']['total_trades']} trades | "
              f"WR {result['baseline']['win_rate']:.1f}% | "
              f"Avg R {result['baseline']['avg_r']:.3f}")
        print(f"  Significant edges: {len(result['significant_edges'])}")
        print(f"  Drift alerts: {len(result['drift_alerts'])}")
        print("=" * 60)

        return result

    finally:
        engine.close()


if __name__ == "__main__":
    run_analysis()
