"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Hypothesis Engine
XIII Trading LLC
================================================================================

Discovers, proposes, tests, and classifies hypotheses about trading edges.
Works with the analysis engine's indicator scans to find new candidates.

Lifecycle: PROPOSED -> TESTING -> VALIDATED / REJECTED / INCONCLUSIVE

Output:
  - Hypotheses tracked in state/hypothesis_tracker.json
  - Test results archived in analysis/hypotheses/H###_result_YYYYMMDD.md
  - Validated hypotheses added to pending_edges.json for approval
  - Changelog entries for all state changes

Usage:
    python run_ml_workflow.py hypothesize
    python run_ml_workflow.py test-hypothesis H001
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_CONFIG, INDICATOR_SCAN_QUERIES, VALIDATED_EDGES,
    EDGE_CRITERIA, HYPOTHESES_DIR, ensure_directories,
)
from scripts.statistical_tests import run_full_test, confidence_level
from scripts.state_manager import StateManager


class HypothesisEngine:
    """
    Discovers and tests hypotheses about trading edges.

    Scan flow:
    1. Query each indicator column for distinct values with win/loss counts
    2. Compare each bucket against baseline
    3. If effect > threshold and N >= 30, propose as hypothesis
    4. Skip buckets already tracked (VALIDATED_EDGES or existing hypotheses)
    5. Test proposed hypotheses with chi-squared test
    6. Classify: VALIDATED (significant) / REJECTED (not significant) / INCONCLUSIVE (low N)
    """

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
            return dict(row) if row else {"wins": 0, "total": 0}

    def _get_tracked_edges(self) -> set:
        """Get set of already-tracked edge keys (indicator=value)."""
        tracked = set()

        # From VALIDATED_EDGES
        for edge in VALIDATED_EDGES:
            key = f"{edge.get('indicator', '')}={edge.get('condition', '')}"
            tracked.add(key)

        # From hypothesis tracker
        hyp_data = self.state.load_hypotheses()
        for h in hyp_data.get("hypotheses", []):
            key = f"{h.get('indicator', '')}={h.get('condition', '')}"
            tracked.add(key)

        return tracked

    def scan_for_candidates(
        self,
        days: int = 30,
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """
        Scan all indicator columns for new edge candidates.

        A candidate is a bucket with:
        - Effect > EDGE_CRITERIA['effect_size_threshold'] pp
        - Sample size >= EDGE_CRITERIA['min_sample_medium']
        - Not already tracked in VALIDATED_EDGES or hypothesis tracker

        Returns list of candidate dicts ready for hypothesis creation.
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
            start_date = start_dt.strftime("%Y-%m-%d")

        # Get baseline
        baseline = self._execute_single("""
            SELECT
                SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win
            WHERE date >= %s AND date <= %s
        """, [start_date, end_date])

        baseline_wins = int(baseline.get("wins", 0) or 0)
        baseline_total = int(baseline.get("total", 0) or 0)
        baseline_wr = baseline_wins / baseline_total * 100 if baseline_total else 0

        tracked = self._get_tracked_edges()
        candidates = []

        print(f"\n  Scanning for candidates ({start_date} to {end_date})...")
        print(f"  Baseline: {baseline_total} trades, {baseline_wr:.1f}% WR")
        print(f"  Already tracked: {len(tracked)} edges")

        for ind_name, scan_def in INDICATOR_SCAN_QUERIES.items():
            rows = self._execute(scan_def["query"], [start_date, end_date])

            for row in rows:
                value = str(row.get("indicator_value", "NULL"))
                wins = int(row.get("wins", 0) or 0)
                total = int(row.get("total", 0) or 0)

                if total < EDGE_CRITERIA["min_sample_medium"]:
                    continue

                wr = wins / total * 100
                effect_pp = round(wr - baseline_wr, 1)

                if abs(effect_pp) <= EDGE_CRITERIA["effect_size_threshold"]:
                    continue

                # Check if already tracked
                key = f"{ind_name}={value}"
                if key in tracked:
                    continue

                # Run quick test
                test = run_full_test(wins, total, baseline_wins, baseline_total)

                candidates.append({
                    "indicator": ind_name,
                    "condition": value,
                    "description": scan_def.get("description", ""),
                    "effect_pp": effect_pp,
                    "win_rate": round(wr, 1),
                    "baseline_wr": round(baseline_wr, 1),
                    "trades": total,
                    "wins": wins,
                    "p_value": round(test.p_value, 4),
                    "confidence": test.confidence,
                    "is_significant": test.is_significant,
                    "period": f"{start_date} to {end_date}",
                })

        # Sort by absolute effect size
        candidates.sort(key=lambda x: abs(x["effect_pp"]), reverse=True)

        print(f"  Candidates found: {len(candidates)}")
        for c in candidates:
            sig = "SIG" if c["is_significant"] else "---"
            print(f"    [{sig}] {c['indicator']}={c['condition']}: "
                  f"{c['effect_pp']:+.1f}pp (N={c['trades']}, p={c['p_value']:.4f})")

        return candidates

    def create_hypotheses(self, candidates: List[Dict]) -> List[str]:
        """
        Create hypothesis entries from candidates.

        Returns list of hypothesis IDs created.
        """
        created_ids = []

        for c in candidates:
            direction = "positive" if c["effect_pp"] > 0 else "negative"
            name = f"{c['indicator']}={c['condition']} ({direction} edge)"

            hyp_id = self.state.add_hypothesis({
                "name": name,
                "indicator": c["indicator"],
                "condition": c["condition"],
                "description": c["description"],
                "initial_effect_pp": c["effect_pp"],
                "initial_win_rate": c["win_rate"],
                "initial_trades": c["trades"],
                "initial_p_value": c["p_value"],
                "initial_confidence": c["confidence"],
                "initial_is_significant": c["is_significant"],
                "discovery_period": c["period"],
                "status": "PROPOSED",
                "test_result": None,
            })

            created_ids.append(hyp_id)
            print(f"  Created {hyp_id}: {name}")

            self.state.append_changelog(
                "HYPOTHESIS_PROPOSED",
                f"New hypothesis {hyp_id}: {name} ({c['effect_pp']:+.1f}pp, p={c['p_value']:.4f})",
                {"hypothesis_id": hyp_id, **c},
            )

        return created_ids

    def test_hypothesis(
        self,
        hyp_id: str,
        days: int = 30,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """
        Execute statistical test for a specific hypothesis.

        Args:
            hyp_id: Hypothesis ID (e.g., 'H001')
            days: Days to look back for test data
            start_date: Override start date
            end_date: Override end date

        Returns:
            Test result dict with classification
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
            start_date = start_dt.strftime("%Y-%m-%d")

        # Load hypothesis
        hyp_data = self.state.load_hypotheses()
        hypothesis = None
        for h in hyp_data.get("hypotheses", []):
            if h["id"] == hyp_id:
                hypothesis = h
                break

        if hypothesis is None:
            print(f"  ERROR: Hypothesis {hyp_id} not found")
            return {"error": f"Hypothesis {hyp_id} not found"}

        indicator = hypothesis["indicator"]
        condition = hypothesis["condition"]

        print(f"\n  Testing {hyp_id}: {hypothesis.get('name', 'Unnamed')}")
        print(f"  Indicator: {indicator} = {condition}")
        print(f"  Period: {start_date} to {end_date}")

        # Get the scan query for this indicator
        scan_def = INDICATOR_SCAN_QUERIES.get(indicator)
        if not scan_def:
            print(f"  ERROR: No scan query for indicator '{indicator}'")
            return {"error": f"No scan query for indicator '{indicator}'"}

        # Run indicator query and find matching bucket
        rows = self._execute(scan_def["query"], [start_date, end_date])
        group_wins = 0
        group_total = 0

        for row in rows:
            if str(row.get("indicator_value", "")) == condition:
                group_wins = int(row.get("wins", 0) or 0)
                group_total = int(row.get("total", 0) or 0)
                break

        # Get baseline
        baseline = self._execute_single("""
            SELECT
                SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM trades_m5_r_win
            WHERE date >= %s AND date <= %s
        """, [start_date, end_date])

        baseline_wins = int(baseline.get("wins", 0) or 0)
        baseline_total = int(baseline.get("total", 0) or 0)

        if group_total == 0:
            print(f"  No matching trades found for {indicator}={condition}")
            self.state.update_hypothesis(hyp_id, {
                "status": "INCONCLUSIVE",
                "test_result": {"error": "No matching trades", "period": f"{start_date} to {end_date}"},
            })
            return {"status": "INCONCLUSIVE", "reason": "No matching trades"}

        # Run full statistical test
        test = run_full_test(group_wins, group_total, baseline_wins, baseline_total)

        # Classify result
        if test.is_significant:
            status = "VALIDATED"
        elif test.group_trades < EDGE_CRITERIA["min_sample_medium"]:
            status = "INCONCLUSIVE"
        elif test.p_value > 0.20:
            status = "REJECTED"
        elif abs(test.effect_size_pp) <= EDGE_CRITERIA["effect_size_threshold"]:
            status = "REJECTED"
        else:
            status = "INCONCLUSIVE"

        result = {
            "status": status,
            "test_result": test.to_dict(),
            "test_period": f"{start_date} to {end_date}",
        }

        # Update hypothesis
        if status == "REJECTED":
            result["rejection_reason"] = self._get_rejection_reason(test)

        self.state.update_hypothesis(hyp_id, {
            "status": status,
            "test_result": test.to_dict(),
            "test_period": f"{start_date} to {end_date}",
            **({"rejection_reason": result.get("rejection_reason", "")} if status == "REJECTED" else {}),
        })

        # Print results
        print(f"\n  Result: {status}")
        print(f"  Group WR: {test.group_win_rate:.1f}% ({test.group_trades} trades)")
        print(f"  Baseline WR: {test.baseline_win_rate:.1f}% ({test.baseline_trades} trades)")
        print(f"  Effect: {test.effect_size_pp:+.1f}pp")
        print(f"  p-value: {test.p_value:.4f}")
        print(f"  Confidence: {test.confidence}")

        # Archive result
        self._archive_result(hyp_id, hypothesis, test, status)

        # Log to changelog
        self.state.append_changelog(
            f"HYPOTHESIS_{status}",
            f"{hyp_id} {status}: {hypothesis.get('name', 'Unnamed')} "
            f"(effect={test.effect_size_pp:+.1f}pp, p={test.p_value:.4f})",
            {"hypothesis_id": hyp_id, "test_result": test.to_dict()},
        )

        # If validated, add to pending edges
        if status == "VALIDATED":
            direction = "positive" if test.effect_size_pp > 0 else "negative"
            action = "TRADE when active" if test.effect_size_pp > 0 else "SKIP/AVOID"

            self.state.add_pending_edge({
                "name": hypothesis.get("name", f"{indicator}={condition}"),
                "hypothesis_id": hyp_id,
                "reason": f"VALIDATED: {test.effect_size_pp:+.1f}pp (p={test.p_value:.4f}, N={test.group_trades})",
                "action": "APPROVE_FOR_ADDITION",
                "edge_definition": {
                    "indicator": indicator,
                    "condition": condition,
                    "effect_size_pp": test.effect_size_pp,
                    "confidence": test.confidence,
                    "action": action,
                },
                "test_result": test.to_dict(),
            })

            print(f"\n  *** VALIDATED EDGE - PENDING APPROVAL ***")
            print(f"  Run 'python run_ml_workflow.py approve-edge {hyp_id}' to promote")

        return result

    def _get_rejection_reason(self, test) -> str:
        """Generate human-readable rejection reason."""
        reasons = []
        if test.p_value >= EDGE_CRITERIA["p_value_threshold"]:
            reasons.append(f"p={test.p_value:.4f} >= {EDGE_CRITERIA['p_value_threshold']}")
        if abs(test.effect_size_pp) <= EDGE_CRITERIA["effect_size_threshold"]:
            reasons.append(f"|effect|={abs(test.effect_size_pp):.1f}pp <= {EDGE_CRITERIA['effect_size_threshold']}pp")
        if test.group_trades < EDGE_CRITERIA["min_sample_medium"]:
            reasons.append(f"N={test.group_trades} < {EDGE_CRITERIA['min_sample_medium']}")
        return "; ".join(reasons) if reasons else "Did not meet significance criteria"

    def _archive_result(self, hyp_id: str, hypothesis: Dict, test, status: str) -> None:
        """Archive test result as markdown file."""
        ensure_directories()
        date_str = datetime.now().strftime("%Y%m%d")
        path = HYPOTHESES_DIR / f"{hyp_id}_result_{date_str}.md"

        md = f"""# Hypothesis Test Result: {hyp_id}

**Hypothesis**: {hypothesis.get('name', 'Unnamed')}
**Status**: {status}
**Tested**: {datetime.now().isoformat()}

---

## Hypothesis

- **Indicator**: {hypothesis.get('indicator', 'N/A')}
- **Condition**: {hypothesis.get('condition', 'N/A')}
- **Discovery Effect**: {hypothesis.get('initial_effect_pp', 'N/A')}pp
- **Discovery Period**: {hypothesis.get('discovery_period', 'N/A')}

---

## Test Results

| Metric | Value |
|--------|-------|
| Group Win Rate | {test.group_win_rate:.1f}% |
| Baseline Win Rate | {test.baseline_win_rate:.1f}% |
| Effect Size | {test.effect_size_pp:+.1f}pp |
| Chi-squared | {test.chi2:.4f} |
| p-value | {test.p_value:.6f} |
| Group Trades | {test.group_trades} |
| Baseline Trades | {test.baseline_trades} |
| Confidence | {test.confidence} |
| Significant | {test.is_significant} |

---

## Classification

**{status}**
"""
        if status == "VALIDATED":
            md += "\nThis hypothesis has been added to pending_edges.json for approval.\n"
        elif status == "REJECTED":
            md += f"\nReason: {self._get_rejection_reason(test)}\n"
        else:
            md += "\nInsufficient evidence to validate or reject. May retest with more data.\n"

        md += f"\n---\n\n*Generated by hypothesis_engine.py -- {datetime.now().isoformat()}*\n"

        with open(path, "w") as f:
            f.write(md)
        print(f"  Archived: {path}")

    def run_hypothesis_scan(
        self,
        days: int = 30,
        auto_test: bool = True,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """
        Full hypothesis pipeline: scan -> create -> optionally test.

        Args:
            days: Days to look back
            auto_test: If True, immediately test all proposed hypotheses
            start_date: Override start date
            end_date: Override end date

        Returns:
            Summary dict with candidates, created IDs, and test results
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
            start_date = start_dt.strftime("%Y-%m-%d")

        # Step 1: Scan for candidates
        candidates = self.scan_for_candidates(
            days=days, start_date=start_date, end_date=end_date
        )

        if not candidates:
            print("\n  No new candidates found")
            return {"candidates": 0, "created": [], "tested": []}

        # Step 2: Create hypotheses
        print(f"\n  Creating {len(candidates)} hypotheses...")
        created_ids = self.create_hypotheses(candidates)

        # Step 3: Auto-test if requested
        test_results = []
        if auto_test and created_ids:
            print(f"\n  Auto-testing {len(created_ids)} hypotheses...")
            for hyp_id in created_ids:
                result = self.test_hypothesis(
                    hyp_id, days=days,
                    start_date=start_date, end_date=end_date,
                )
                test_results.append({"id": hyp_id, **result})

        # Summary
        validated = [r for r in test_results if r.get("status") == "VALIDATED"]
        rejected = [r for r in test_results if r.get("status") == "REJECTED"]
        inconclusive = [r for r in test_results if r.get("status") == "INCONCLUSIVE"]

        print("\n" + "=" * 60)
        print("  HYPOTHESIS SCAN SUMMARY")
        print("=" * 60)
        print(f"  Candidates found: {len(candidates)}")
        print(f"  Hypotheses created: {len(created_ids)}")

        if auto_test:
            print(f"  Tested: {len(test_results)}")
            print(f"    VALIDATED:    {len(validated)}")
            print(f"    REJECTED:     {len(rejected)}")
            print(f"    INCONCLUSIVE: {len(inconclusive)}")

        if validated:
            print("\n  *** NEW VALIDATED EDGES - PENDING APPROVAL ***")
            for v in validated:
                tr = v.get("test_result", {})
                print(f"    > {v['id']}: {tr.get('effect_size_pp', '?'):+.1f}pp "
                      f"(p={tr.get('p_value', '?'):.4f})")

        print("=" * 60)

        return {
            "candidates": len(candidates),
            "created": created_ids,
            "tested": test_results,
            "validated": [v["id"] for v in validated],
            "rejected": [r["id"] for r in rejected],
        }

    def close(self):
        if self.conn:
            self.conn.close()


def run_hypothesis_scan(days: int = 30, start_date: str = None, end_date: str = None):
    """Entry point for hypothesis scanning."""
    print("\n" + "=" * 60)
    print("  EPOCH ML - Hypothesis Engine")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 60)

    engine = HypothesisEngine()
    try:
        return engine.run_hypothesis_scan(
            days=days, auto_test=True,
            start_date=start_date, end_date=end_date,
        )
    finally:
        engine.close()


def run_test_hypothesis(hyp_id: str, days: int = 30, start_date: str = None, end_date: str = None):
    """Entry point for testing a specific hypothesis."""
    print("\n" + "=" * 60)
    print(f"  EPOCH ML - Test Hypothesis {hyp_id}")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 60)

    engine = HypothesisEngine()
    try:
        return engine.test_hypothesis(
            hyp_id, days=days,
            start_date=start_date, end_date=end_date,
        )
    finally:
        engine.close()


if __name__ == "__main__":
    run_hypothesis_scan()
