"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Edge Validator
XIII Trading LLC
================================================================================

Validates all edges in config.VALIDATED_EDGES against current data.
Runs statistical tests, classifies health, flags degraded edges for review.

Output:
  - Console summary with health status
  - Audit report in analysis/edge_audits/edge_validation_YYYYMMDD.md
  - Updates system_state.json edge_health
  - Adds degraded edges to pending_edges.json

Usage:
    python run_ml_workflow.py validate-edges
    python run_ml_workflow.py validate-edges --days 30
    python run_ml_workflow.py validate-edges --start 2026-01-01 --end 2026-01-31
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_CONFIG, VALIDATED_EDGES, EDGE_DEFINITIONS,
    EDGE_AUDITS_DIR, ensure_directories,
)
from scripts.statistical_tests import run_full_test, classify_edge_health
from scripts.state_manager import StateManager


class EdgeValidator:
    """
    Validates all VALIDATED_EDGES against current database data.

    For each edge:
    1. Run group query (trades matching edge condition)
    2. Run baseline query (all trades for comparison)
    3. Run chi-squared test
    4. Classify health: HEALTHY / WEAKENING / DEGRADED / INCONCLUSIVE
    5. Flag degraded edges for review
    """

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.state = StateManager()
        print("  Connected to Supabase")

    def _execute_single(self, query: str, params: list = None) -> Dict:
        """Execute query expecting a single row result."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else {"wins": 0, "total": 0}

    def validate_edge(
        self,
        edge: Dict,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """
        Validate a single edge against current data.

        Args:
            edge: Edge definition from VALIDATED_EDGES
            start_date: Start of validation window (YYYY-MM-DD)
            end_date: End of validation window (YYYY-MM-DD)

        Returns:
            Dict with test results and health classification
        """
        edge_name = edge["name"]
        definition = EDGE_DEFINITIONS.get(edge_name)

        if not definition:
            return {
                "edge": edge_name,
                "status": "NO_DEFINITION",
                "message": f"No SQL definition found for '{edge_name}' in config.EDGE_DEFINITIONS",
            }

        # Run group query
        group = self._execute_single(
            definition["group_query"],
            [start_date, end_date],
        )

        # Run baseline query
        baseline = self._execute_single(
            definition["baseline_query"],
            [start_date, end_date],
        )

        group_wins = int(group.get("wins", 0) or 0)
        group_total = int(group.get("total", 0) or 0)
        baseline_wins = int(baseline.get("wins", 0) or 0)
        baseline_total = int(baseline.get("total", 0) or 0)

        # Run statistical test
        test_result = run_full_test(group_wins, group_total, baseline_wins, baseline_total)

        # Classify health vs stored value
        stored_effect = edge.get("effect_size_pp", 0)
        health_status = classify_edge_health(
            current_effect_pp=test_result.effect_size_pp,
            stored_effect_pp=stored_effect,
            p_value=test_result.p_value,
        )

        return {
            "edge": edge_name,
            "status": health_status,
            "stored_effect_pp": stored_effect,
            "current_effect_pp": test_result.effect_size_pp,
            "group_win_rate": test_result.group_win_rate,
            "baseline_win_rate": test_result.baseline_win_rate,
            "group_trades": test_result.group_trades,
            "baseline_trades": test_result.baseline_trades,
            "chi2": test_result.chi2,
            "p_value": test_result.p_value,
            "confidence": test_result.confidence,
            "is_significant": test_result.is_significant,
            "period": f"{start_date} to {end_date}",
        }

    def validate_all_edges(
        self,
        days: int = 30,
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """
        Validate all VALIDATED_EDGES.

        Args:
            days: Number of days to look back (default 30)
            start_date: Override start date (YYYY-MM-DD)
            end_date: Override end date (YYYY-MM-DD)

        Returns:
            List of validation results
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
            start_date = start_dt.strftime("%Y-%m-%d")

        print(f"\n  Validation period: {start_date} to {end_date}")
        print(f"  Edges to validate: {len(VALIDATED_EDGES)}")

        results = []
        for edge in VALIDATED_EDGES:
            print(f"\n  Validating: {edge['name']}...")
            result = self.validate_edge(edge, start_date, end_date)
            results.append(result)

            # Print inline summary
            status = result.get("status", "UNKNOWN")
            icon = {
                "HEALTHY": "[OK]",
                "WEAKENING": "[!!]",
                "DEGRADED": "[XX]",
                "INCONCLUSIVE": "[??]",
                "NO_DEFINITION": "[--]",
            }.get(status, "[??]")

            if status == "NO_DEFINITION":
                print(f"    {icon} {result['message']}")
            else:
                print(f"    {icon} {status}")
                print(f"    Current: {result['current_effect_pp']:+.1f}pp "
                      f"(stored: {result['stored_effect_pp']:+.1f}pp)")
                print(f"    Group WR: {result['group_win_rate']:.1f}% "
                      f"({result['group_trades']} trades) | "
                      f"Baseline WR: {result['baseline_win_rate']:.1f}% "
                      f"({result['baseline_trades']} trades)")
                print(f"    p={result['p_value']:.4f} | {result['confidence']} confidence")

        return results

    def process_results(self, results: List[Dict]) -> None:
        """
        Process validation results: update state, flag degraded edges, write report.
        """
        ensure_directories()

        # Update system state with edge health
        state = self.state.load_system_state()
        edge_health = {}
        degraded = []
        weakening = []

        for r in results:
            if r.get("status") == "NO_DEFINITION":
                continue

            edge_health[r["edge"]] = {
                "status": r["status"],
                "current_effect_pp": r["current_effect_pp"],
                "stored_effect_pp": r["stored_effect_pp"],
                "p_value": round(r["p_value"], 4),
                "group_trades": r["group_trades"],
                "confidence": r["confidence"],
                "validated": datetime.now().isoformat(),
            }

            if r["status"] == "DEGRADED":
                degraded.append(r)
            elif r["status"] == "WEAKENING":
                weakening.append(r)

        state["edge_health"] = edge_health
        self.state.save_system_state(state)

        # Flag degraded edges for review
        for d in degraded:
            self.state.add_pending_edge({
                "name": d["edge"],
                "reason": f"DEGRADED: stored {d['stored_effect_pp']:+.1f}pp -> current {d['current_effect_pp']:+.1f}pp (p={d['p_value']:.4f})",
                "action": "REVIEW_FOR_REMOVAL",
                "test_result": {
                    "current_effect_pp": d["current_effect_pp"],
                    "stored_effect_pp": d["stored_effect_pp"],
                    "p_value": d["p_value"],
                    "group_trades": d["group_trades"],
                    "period": d["period"],
                },
            })
            self.state.append_changelog(
                "EDGE_DEGRADED",
                f"Edge '{d['edge']}' degraded: {d['stored_effect_pp']:+.1f}pp -> {d['current_effect_pp']:+.1f}pp",
                d,
            )

        # Write audit report
        report = self._generate_report(results)
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = EDGE_AUDITS_DIR / f"edge_validation_{date_str}.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n  Report: {report_path}")

        # Print summary banner
        print("\n" + "=" * 60)
        print("  EDGE VALIDATION SUMMARY")
        print("=" * 60)

        healthy = [r for r in results if r.get("status") == "HEALTHY"]
        inconclusive = [r for r in results if r.get("status") == "INCONCLUSIVE"]

        print(f"  HEALTHY:      {len(healthy)}")
        print(f"  WEAKENING:    {len(weakening)}")
        print(f"  DEGRADED:     {len(degraded)}")
        print(f"  INCONCLUSIVE: {len(inconclusive)}")

        if degraded:
            print("\n  *** DEGRADED EDGES FLAGGED FOR REVIEW ***")
            for d in degraded:
                print(f"    > {d['edge']}: {d['stored_effect_pp']:+.1f}pp -> {d['current_effect_pp']:+.1f}pp")
            print("  Run 'python run_ml_workflow.py status' to see pending actions")

        if weakening:
            print("\n  *** WEAKENING EDGES (monitor) ***")
            for w in weakening:
                print(f"    > {w['edge']}: {w['stored_effect_pp']:+.1f}pp -> {w['current_effect_pp']:+.1f}pp")

        print("=" * 60)

    def _generate_report(self, results: List[Dict]) -> str:
        """Generate markdown validation report."""
        now = datetime.now()

        md = f"""# Edge Validation Report

**Generated**: {now.isoformat()}
**Source**: trades_m5_r_win (sole source of truth)

---

## Validation Results

| Edge | Status | Stored | Current | p-value | Trades | Confidence |
|------|--------|--------|---------|---------|--------|------------|
"""
        for r in results:
            if r.get("status") == "NO_DEFINITION":
                md += f"| {r['edge']} | NO_DEFINITION | — | — | — | — | — |\n"
            else:
                md += (
                    f"| {r['edge']} | {r['status']} "
                    f"| {r['stored_effect_pp']:+.1f}pp "
                    f"| {r['current_effect_pp']:+.1f}pp "
                    f"| {r['p_value']:.4f} "
                    f"| {r['group_trades']} "
                    f"| {r['confidence']} |\n"
                )

        md += "\n---\n\n## Detailed Results\n\n"

        for r in results:
            if r.get("status") == "NO_DEFINITION":
                continue

            md += f"""### {r['edge']}

- **Status**: {r['status']}
- **Period**: {r.get('period', 'N/A')}
- **Group**: {r['group_win_rate']:.1f}% WR ({r['group_trades']} trades)
- **Baseline**: {r['baseline_win_rate']:.1f}% WR ({r['baseline_trades']} trades)
- **Effect**: {r['current_effect_pp']:+.1f}pp (stored: {r['stored_effect_pp']:+.1f}pp)
- **Chi²**: {r.get('chi2', 0):.4f} | p-value: {r['p_value']:.6f}
- **Significant**: {r['is_significant']}

"""

        md += f"\n---\n\n*Auto-generated by edge_validator.py — {now.isoformat()}*\n"
        return md

    def close(self):
        if self.conn:
            self.conn.close()


def run_edge_validation(days: int = 30, start_date: str = None, end_date: str = None):
    """Entry point for edge validation."""
    print("\n" + "=" * 60)
    print("  EPOCH ML - Edge Validation")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 60)

    validator = EdgeValidator()
    try:
        results = validator.validate_all_edges(
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
        validator.process_results(results)
        return results
    finally:
        validator.close()


if __name__ == "__main__":
    run_edge_validation()
