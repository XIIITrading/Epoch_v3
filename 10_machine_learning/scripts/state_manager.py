"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
State Manager
XIII Trading LLC
================================================================================

Manages dual-format state: JSON (machine-readable) + MD (human-readable).
The JSON files are the source of truth; MD files are auto-generated summaries.

State files:
  state/system_state.json       → Baseline metrics, edge health, drift alerts
  state/hypothesis_tracker.json → All hypotheses with lifecycle status
  state/pending_edges.json      → Edges awaiting human approval
  state/changelog/              → Dated changelog entries
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    STATE_DIR, CHANGELOG_DIR, SYSTEM_STATE_JSON,
    HYPOTHESIS_TRACKER_JSON, PENDING_EDGES_JSON,
    ensure_directories,
)


class StateManager:
    """Manages all JSON state files with MD auto-generation."""

    def __init__(self):
        ensure_directories()

    # =========================================================================
    # SYSTEM STATE
    # =========================================================================

    def load_system_state(self) -> Dict:
        """Load system_state.json, return empty structure if missing."""
        if SYSTEM_STATE_JSON.exists():
            with open(SYSTEM_STATE_JSON, "r") as f:
                return json.load(f)
        return self._default_system_state()

    def save_system_state(self, data: Dict) -> None:
        """Save system_state.json and regenerate system_state.md."""
        data["last_updated"] = datetime.now().isoformat()
        with open(SYSTEM_STATE_JSON, "w") as f:
            json.dump(data, f, indent=2, default=str)
        self._generate_system_state_md(data)
        print(f"  State saved: {SYSTEM_STATE_JSON.name}")

    def _default_system_state(self) -> Dict:
        return {
            "last_updated": None,
            "baseline": {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_r": 0.0,
                "std_r": 0.0,
                "period_start": None,
                "period_end": None,
            },
            "edge_health": {},
            "drift_alerts": [],
            "last_cycle": None,
        }

    def _generate_system_state_md(self, data: Dict) -> None:
        """Auto-generate system_state.md from JSON."""
        md_path = STATE_DIR / "system_state.md"
        b = data.get("baseline", {})
        eh = data.get("edge_health", {})
        alerts = data.get("drift_alerts", [])

        md = f"""# System State

**Last Updated**: {data.get('last_updated', 'N/A')}
**Last Cycle**: {data.get('last_cycle', 'Never')}

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| Total Trades | {b.get('total_trades', 0)} |
| Win Rate | {b.get('win_rate', 0):.1f}% |
| Avg R | {b.get('avg_r', 0):.3f} |
| Std R | {b.get('std_r', 0):.3f} |
| Period | {b.get('period_start', 'N/A')} to {b.get('period_end', 'N/A')} |

---

## Edge Health

| Edge | Status | Current Effect | Stored Effect | p-value |
|------|--------|---------------|--------------|---------|
"""
        for name, health in eh.items():
            md += (
                f"| {name} | {health.get('status', 'UNKNOWN')} "
                f"| {health.get('current_effect_pp', 0):+.1f}pp "
                f"| {health.get('stored_effect_pp', 0):+.1f}pp "
                f"| {health.get('p_value', 'N/A')} |\n"
            )

        if alerts:
            md += "\n---\n\n## Drift Alerts\n\n"
            for alert in alerts:
                md += f"- **{alert.get('type', 'ALERT')}**: {alert.get('message', '')}\n"

        md += f"\n---\n\n*Auto-generated from system_state.json — {datetime.now().isoformat()}*\n"

        with open(md_path, "w") as f:
            f.write(md)

    # =========================================================================
    # HYPOTHESIS TRACKER
    # =========================================================================

    def load_hypotheses(self) -> Dict:
        """Load hypothesis_tracker.json, return empty structure if missing."""
        if HYPOTHESIS_TRACKER_JSON.exists():
            with open(HYPOTHESIS_TRACKER_JSON, "r") as f:
                return json.load(f)
        return self._default_hypotheses()

    def save_hypotheses(self, data: Dict) -> None:
        """Save hypothesis_tracker.json and regenerate hypothesis_tracker.md."""
        data["last_updated"] = datetime.now().isoformat()
        with open(HYPOTHESIS_TRACKER_JSON, "w") as f:
            json.dump(data, f, indent=2, default=str)
        self._generate_hypotheses_md(data)
        print(f"  Hypotheses saved: {HYPOTHESIS_TRACKER_JSON.name}")

    def _default_hypotheses(self) -> Dict:
        return {
            "last_updated": None,
            "next_id": 1,
            "hypotheses": [],
        }

    def get_next_hypothesis_id(self) -> str:
        """Get next hypothesis ID (H001, H002, etc.)."""
        data = self.load_hypotheses()
        next_id = data.get("next_id", 1)
        return f"H{next_id:03d}"

    def add_hypothesis(self, hypothesis: Dict) -> str:
        """Add a new hypothesis and return its ID."""
        data = self.load_hypotheses()
        hyp_id = f"H{data['next_id']:03d}"
        hypothesis["id"] = hyp_id
        hypothesis["created"] = datetime.now().isoformat()
        hypothesis["status"] = hypothesis.get("status", "PROPOSED")
        data["hypotheses"].append(hypothesis)
        data["next_id"] += 1
        self.save_hypotheses(data)
        return hyp_id

    def update_hypothesis(self, hyp_id: str, updates: Dict) -> bool:
        """Update an existing hypothesis by ID."""
        data = self.load_hypotheses()
        for h in data["hypotheses"]:
            if h["id"] == hyp_id:
                h.update(updates)
                h["last_tested"] = datetime.now().isoformat()
                self.save_hypotheses(data)
                return True
        print(f"  WARNING: Hypothesis {hyp_id} not found")
        return False

    def _generate_hypotheses_md(self, data: Dict) -> None:
        """Auto-generate hypothesis_tracker.md from JSON."""
        md_path = STATE_DIR / "hypothesis_tracker.md"
        hypotheses = data.get("hypotheses", [])

        md = f"""# Hypothesis Tracker

**Last Updated**: {data.get('last_updated', 'N/A')}
**Total Hypotheses**: {len(hypotheses)}

---

## Active Hypotheses

| ID | Name | Status | Effect | p-value | Confidence |
|----|------|--------|--------|---------|------------|
"""
        for h in hypotheses:
            if h.get("status") in ("PROPOSED", "TESTING"):
                result = h.get("test_result") or {}
                md += (
                    f"| {h['id']} | {h.get('name', 'Unnamed')} "
                    f"| {h['status']} "
                    f"| {result.get('effect_size_pp', h.get('initial_effect_pp', '--'))} "
                    f"| {result.get('p_value', h.get('initial_p_value', '--'))} "
                    f"| {result.get('confidence', h.get('initial_confidence', '--'))} |\n"
                )

        md += "\n---\n\n## Validated Hypotheses\n\n"
        md += "| ID | Name | Effect | p-value | Validated Date |\n"
        md += "|----|------|--------|---------|----------------|\n"
        for h in hypotheses:
            if h.get("status") == "VALIDATED":
                result = h.get("test_result") or {}
                md += (
                    f"| {h['id']} | {h.get('name', 'Unnamed')} "
                    f"| {result.get('effect_size_pp', '--')}pp "
                    f"| {result.get('p_value', '--')} "
                    f"| {h.get('last_tested', '--')} |\n"
                )

        md += "\n---\n\n## Rejected Hypotheses\n\n"
        md += "| ID | Name | Reason | Tested Date |\n"
        md += "|----|------|--------|-------------|\n"
        for h in hypotheses:
            if h.get("status") == "REJECTED":
                result = h.get("test_result", {})
                md += (
                    f"| {h['id']} | {h.get('name', 'Unnamed')} "
                    f"| {h.get('rejection_reason', 'Did not meet criteria')} "
                    f"| {h.get('last_tested', '—')} |\n"
                )

        md += f"\n---\n\n*Auto-generated from hypothesis_tracker.json — {datetime.now().isoformat()}*\n"

        with open(md_path, "w") as f:
            f.write(md)

    # =========================================================================
    # PENDING EDGES
    # =========================================================================

    def load_pending_edges(self) -> List[Dict]:
        """Load pending_edges.json, return empty list if missing."""
        if PENDING_EDGES_JSON.exists():
            with open(PENDING_EDGES_JSON, "r") as f:
                return json.load(f)
        return []

    def save_pending_edges(self, data: List[Dict]) -> None:
        """Save pending_edges.json."""
        with open(PENDING_EDGES_JSON, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Pending edges saved: {PENDING_EDGES_JSON.name}")

    def add_pending_edge(self, edge: Dict) -> None:
        """Add an edge to the pending review queue."""
        pending = self.load_pending_edges()

        # Check for duplicate by hypothesis_id or name
        for existing in pending:
            if (
                existing.get("hypothesis_id") == edge.get("hypothesis_id")
                or existing.get("name") == edge.get("name")
            ):
                # Update existing
                existing.update(edge)
                existing["updated"] = datetime.now().isoformat()
                self.save_pending_edges(pending)
                print(f"  Updated pending edge: {edge.get('name', 'Unknown')}")
                return

        edge["added"] = datetime.now().isoformat()
        pending.append(edge)
        self.save_pending_edges(pending)
        print(f"  Added pending edge: {edge.get('name', 'Unknown')}")

    def remove_pending_edge(self, name: str) -> bool:
        """Remove an edge from the pending queue by name."""
        pending = self.load_pending_edges()
        new_pending = [e for e in pending if e.get("name") != name]
        if len(new_pending) < len(pending):
            self.save_pending_edges(new_pending)
            return True
        return False

    # =========================================================================
    # CHANGELOG
    # =========================================================================

    def append_changelog(self, entry_type: str, message: str, details: Dict = None) -> None:
        """
        Write a dated changelog entry.

        Args:
            entry_type: Type of change (EDGE_VALIDATED, EDGE_DEGRADED, HYPOTHESIS_TESTED, etc.)
            message: Human-readable summary
            details: Optional structured data
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = CHANGELOG_DIR / f"changelog_{today}.json"

        # Load existing entries for today
        entries = []
        if log_path.exists():
            with open(log_path, "r") as f:
                entries = json.load(f)

        entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "message": message,
            "details": details or {},
        })

        with open(log_path, "w") as f:
            json.dump(entries, f, indent=2, default=str)

    # =========================================================================
    # UTILITY
    # =========================================================================

    def print_status_banner(self) -> None:
        """Print a concise status summary with any pending actions."""
        state = self.load_system_state()
        pending = self.load_pending_edges()
        hypotheses = self.load_hypotheses()

        baseline = state.get("baseline", {})
        edge_health = state.get("edge_health", {})
        alerts = state.get("drift_alerts", [])

        active_hypotheses = [
            h for h in hypotheses.get("hypotheses", [])
            if h.get("status") in ("PROPOSED", "TESTING")
        ]

        print("\n" + "=" * 60)
        print("  EPOCH ML - System Status")
        print("=" * 60)

        # Baseline
        if baseline.get("total_trades"):
            print(f"\n  Baseline: {baseline['total_trades']} trades | "
                  f"WR {baseline.get('win_rate', 0):.1f}% | "
                  f"Avg R {baseline.get('avg_r', 0):.3f}")

        # Edge health
        if edge_health:
            print(f"\n  Validated Edges:")
            for name, health in edge_health.items():
                status = health.get("status", "UNKNOWN")
                icon = {"HEALTHY": "[OK]", "WEAKENING": "[!!]", "DEGRADED": "[XX]"}.get(status, "[??]")
                print(f"    {icon} {name}: {health.get('current_effect_pp', 0):+.1f}pp "
                      f"(stored: {health.get('stored_effect_pp', 0):+.1f}pp)")

        # Pending edges
        if pending:
            print(f"\n  *** PENDING REVIEW ({len(pending)} edges) ***")
            for e in pending:
                reason = e.get("reason", "")
                print(f"    > {e.get('name', 'Unknown')}: {reason}")

        # Active hypotheses
        if active_hypotheses:
            print(f"\n  Active Hypotheses: {len(active_hypotheses)}")
            for h in active_hypotheses[:5]:
                print(f"    {h['id']}: {h.get('name', 'Unnamed')} [{h['status']}]")

        # Drift alerts
        if alerts:
            print(f"\n  *** DRIFT ALERTS ({len(alerts)}) ***")
            for a in alerts:
                print(f"    ⚠ {a.get('message', '')}")

        last_cycle = state.get("last_cycle")
        if last_cycle:
            print(f"\n  Last cycle: {last_cycle}")

        print("=" * 60)


if __name__ == "__main__":
    # Quick self-test
    print("=" * 60)
    print("  State Manager - Self Test")
    print("=" * 60)

    sm = StateManager()

    # Test system state
    state = sm.load_system_state()
    print(f"\n  System state loaded: {bool(state)}")
    print(f"  Keys: {list(state.keys())}")

    # Test hypotheses
    hyp = sm.load_hypotheses()
    print(f"\n  Hypotheses loaded: {len(hyp.get('hypotheses', []))} hypotheses")
    print(f"  Next ID: {sm.get_next_hypothesis_id()}")

    # Test pending edges
    pending = sm.load_pending_edges()
    print(f"\n  Pending edges: {len(pending)}")

    # Test status banner
    sm.print_status_banner()

    print("\n  Self-test complete")
