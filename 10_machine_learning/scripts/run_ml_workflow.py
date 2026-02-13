"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Master ML Workflow Orchestrator
XIII Trading LLC
================================================================================

Orchestrates the full ML closed-loop pipeline.
Claude Code runs this as the analysis engine -- no copy-paste needed.

CLOSED LOOP:
  EXPORT -> VALIDATE-EDGES -> ANALYZE -> HYPOTHESIZE -> TEST -> UPDATE STATE
    ^                                                              |
    +--------------------------------------------------------------+

AUTONOMY MODEL:
  Autonomous:       export, analyze, hypothesize, test, validate, status, cycle
  Flag + Pause:     New validated edges, degraded edges -> pending_edges.json
  Human Required:   approve-edge, remove-edge (modifies config.py VALIDATED_EDGES)

Usage:
    python run_ml_workflow.py daily                      # Daily export pipeline
    python run_ml_workflow.py weekly                     # Weekly audit prep
    python run_ml_workflow.py full                       # Full pipeline (daily + weekly)
    python run_ml_workflow.py validate-edges             # Check all validated edges
    python run_ml_workflow.py analyze                    # Full system analysis
    python run_ml_workflow.py hypothesize                # Scan + test new hypotheses
    python run_ml_workflow.py test-hypothesis H001       # Test specific hypothesis
    python run_ml_workflow.py cycle                      # Full closed-loop cycle
    python run_ml_workflow.py status                     # Print system status
    python run_ml_workflow.py approve-edge H001          # Promote pending edge
    python run_ml_workflow.py remove-edge "Edge Name"    # Remove degraded edge
    python run_ml_workflow.py report-core                # Core snapshot report (entry indicators)
    python run_ml_workflow.py report-lifecycle            # Lifecycle ramp-up report (M1 bars)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add parent to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    STATE_DIR, CHANGELOG_DIR, DAILY_EXPORTS_DIR, WEEKLY_EXPORTS_DIR,
    VALIDATED_EDGES, MODULE_ROOT, ensure_directories,
)


# =========================================================================
# EXISTING MODES: daily, weekly, full
# =========================================================================

def run_daily_pipeline(date: datetime = None):
    """Run the daily export pipeline."""
    from export_for_claude import ClaudeExporter

    if date is None:
        date = datetime.now()

    print("\n" + "-" * 50)
    print("  PHASE: Daily Export")
    print("-" * 50)

    exporter = ClaudeExporter()
    try:
        result = exporter.run_daily_export(date)

        print("\n  Verification:")
        for f in result.get("files", []):
            p = Path(f)
            if p.exists():
                size_kb = p.stat().st_size / 1024
                print(f"    [OK] {p.name} ({size_kb:.1f} KB)")
            else:
                print(f"    [MISSING] {p.name}")

        summary = result.get("summary", {})
        if summary.get("total_trades", 0) > 0:
            print(f"\n  Trades: {summary['total_trades']}")
            print(f"  Win Rate: {summary.get('win_rate', 0)}%")
            print(f"  Total R: {summary.get('total_r', 0):+.2f}")
        else:
            print(f"\n  No trades found for {date.strftime('%Y-%m-%d')}")

        return result
    finally:
        exporter.close()


def run_weekly_pipeline(date: datetime = None, weeks: int = 1):
    """Run the weekly aggregation pipeline."""
    from weekly_aggregation import WeeklyAggregator

    if date is None:
        date = datetime.now()

    print("\n" + "-" * 50)
    print("  PHASE: Weekly Aggregation")
    print("-" * 50)

    aggregator = WeeklyAggregator()
    try:
        aggregator.run_weekly_aggregation(end_date=date, weeks=weeks)

        print("\n  Weekly exports:")
        for f in sorted(WEEKLY_EXPORTS_DIR.glob("*.md")):
            size_kb = f.stat().st_size / 1024
            print(f"    {f.name} ({size_kb:.1f} KB)")
    finally:
        aggregator.close()


def run_full_pipeline(date: datetime = None):
    """Run the complete export pipeline: daily + weekly."""
    if date is None:
        date = datetime.now()

    print("\n  Running full export pipeline...")
    print(f"  Date: {date.strftime('%Y-%m-%d')}")

    daily_result = run_daily_pipeline(date)
    run_weekly_pipeline(date)

    summary = daily_result.get("summary", {}) if daily_result else {}
    if summary.get("total_trades", 0) > 0:
        print(f"\n  Export complete: {summary['total_trades']} trades | "
              f"WR: {summary.get('win_rate', 0)}% | R: {summary.get('total_r', 0):+.2f}")

    return daily_result


# =========================================================================
# NEW MODES: validate-edges, analyze, hypothesize, test-hypothesis
# =========================================================================

def run_validate_edges(days: int = 30, start_date: str = None, end_date: str = None):
    """Validate all edges in config.VALIDATED_EDGES."""
    from edge_validator import run_edge_validation
    return run_edge_validation(days=days, start_date=start_date, end_date=end_date)


def run_analyze(days: int = 30, start_date: str = None, end_date: str = None):
    """Run full system analysis with narrative report."""
    from analysis_engine import run_analysis
    result = run_analysis(days=days, start_date=start_date, end_date=end_date)

    # Also generate narrative report
    try:
        from narrative_report import build_and_save_report
        report_path = build_and_save_report(analysis_result=result)
        print(f"\n  >> READ THIS FILE: {report_path}")
    except Exception as e:
        print(f"\n  [WARN] Narrative report failed: {e}")

    return result


def run_hypothesize(days: int = 30, start_date: str = None, end_date: str = None):
    """Scan for new hypothesis candidates and auto-test them."""
    from hypothesis_engine import run_hypothesis_scan
    return run_hypothesis_scan(days=days, start_date=start_date, end_date=end_date)


def run_test_hypothesis(hyp_id: str, days: int = 30, start_date: str = None, end_date: str = None):
    """Test a specific hypothesis by ID."""
    from hypothesis_engine import run_test_hypothesis as _run_test
    return _run_test(hyp_id, days=days, start_date=start_date, end_date=end_date)


# =========================================================================
# REPORT MODES: Core Snapshot + Lifecycle Ramp-Up
# =========================================================================

def run_report_core():
    """Generate Report 1: Core Snapshot (entry-time indicators, no ramp-up)."""
    from report_core_snapshot import generate_core_report

    print("\n" + "-" * 50)
    print("  REPORT: Core Snapshot")
    print("-" * 50)

    report_path = generate_core_report()
    print(f"\n  >> READ THIS FILE: {report_path}")
    return report_path


def run_report_lifecycle():
    """Generate Report 2: Lifecycle Ramp-Up (M1 bar analysis across trade phases)."""
    from report_lifecycle import generate_lifecycle_report

    print("\n" + "-" * 50)
    print("  REPORT: Lifecycle Ramp-Up")
    print("-" * 50)

    report_path = generate_lifecycle_report()
    print(f"\n  >> READ THIS FILE: {report_path}")
    return report_path


# =========================================================================
# CYCLE MODE: Full closed-loop
# =========================================================================

def run_cycle(date: datetime = None, days: int = 30):
    """
    Run the full closed-loop cycle:
      1. Daily export (latest data)
      2. Validate existing edges
      3. Analyze system (baseline + indicator scan)
      4. Hypothesize (discover + test new candidates)
      5. Print summary with pending actions
    """
    from state_manager import StateManager

    if date is None:
        date = datetime.now()

    start_dt = date - timedelta(days=days)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = date.strftime("%Y-%m-%d")

    print("\n" + "=" * 70)
    print("  EPOCH ML - FULL CYCLE")
    print(f"  Date: {date.strftime('%Y-%m-%d')} | Lookback: {days} days")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 70)

    results = {}

    # Step 1: Daily export
    try:
        results["export"] = run_daily_pipeline(date)
    except Exception as e:
        print(f"\n  [WARN] Export failed: {e}")
        results["export"] = None

    # Step 2: Validate existing edges
    print("\n" + "-" * 50)
    print("  STEP 2: Edge Validation")
    print("-" * 50)
    try:
        results["validation"] = run_validate_edges(
            days=days, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        print(f"\n  [WARN] Validation failed: {e}")
        results["validation"] = None

    # Step 3: Analyze system
    print("\n" + "-" * 50)
    print("  STEP 3: System Analysis")
    print("-" * 50)
    try:
        results["analysis"] = run_analyze(
            days=days, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        print(f"\n  [WARN] Analysis failed: {e}")
        results["analysis"] = None

    # Step 4: Hypothesize
    print("\n" + "-" * 50)
    print("  STEP 4: Hypothesis Engine")
    print("-" * 50)
    try:
        results["hypotheses"] = run_hypothesize(
            days=days, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        print(f"\n  [WARN] Hypothesis engine failed: {e}")
        results["hypotheses"] = None

    # Step 5: Generate narrative report
    print("\n" + "-" * 50)
    print("  STEP 5: Narrative Report")
    print("-" * 50)
    try:
        from narrative_report import build_and_save_report
        report_path = build_and_save_report(
            analysis_result=results.get("analysis"),
            validation_result=results.get("validation"),
            hypothesis_result=results.get("hypotheses"),
        )
        print(f"  >> READ THIS FILE: {report_path}")
    except Exception as e:
        print(f"\n  [WARN] Narrative report failed: {e}")

    # Step 6: Core Snapshot Report
    print("\n" + "-" * 50)
    print("  STEP 6: Core Snapshot Report")
    print("-" * 50)
    try:
        core_path = run_report_core()
        results["report_core"] = str(core_path)
    except Exception as e:
        print(f"\n  [WARN] Core snapshot report failed: {e}")
        results["report_core"] = None

    # Step 7: Lifecycle Ramp-Up Report
    print("\n" + "-" * 50)
    print("  STEP 7: Lifecycle Ramp-Up Report")
    print("-" * 50)
    try:
        lifecycle_path = run_report_lifecycle()
        results["report_lifecycle"] = str(lifecycle_path)
    except Exception as e:
        print(f"\n  [WARN] Lifecycle ramp-up report failed: {e}")
        results["report_lifecycle"] = None

    # Step 8: Update cycle timestamp
    sm = StateManager()
    state = sm.load_system_state()
    state["last_cycle"] = datetime.now().isoformat()
    sm.save_system_state(state)

    # Step 9: Print final summary
    print("\n" + "=" * 70)
    print("  CYCLE COMPLETE - SUMMARY")
    print("=" * 70)

    # Export summary
    export_result = results.get("export")
    if export_result:
        summary = export_result.get("summary", {})
        print(f"\n  Export: {summary.get('total_trades', 0)} trades today")
    else:
        print("\n  Export: skipped/failed")

    # Validation summary
    validation = results.get("validation")
    if validation:
        degraded = [r for r in validation if r.get("status") == "DEGRADED"]
        healthy = [r for r in validation if r.get("status") == "HEALTHY"]
        print(f"  Validated Edges: {len(healthy)} healthy, {len(degraded)} degraded")
    else:
        print("  Validation: skipped/failed")

    # Analysis summary
    analysis = results.get("analysis")
    if analysis:
        baseline = analysis.get("baseline", {})
        print(f"  Baseline: {baseline.get('total_trades', 0)} trades | "
              f"WR {baseline.get('win_rate', 0):.1f}% | "
              f"Avg R {baseline.get('avg_r', 0):.3f}")
        print(f"  Significant edges: {len(analysis.get('significant_edges', []))}")
        print(f"  Drift alerts: {len(analysis.get('drift_alerts', []))}")

    # Hypothesis summary
    hyp_result = results.get("hypotheses")
    if hyp_result:
        print(f"  New candidates: {hyp_result.get('candidates', 0)}")
        print(f"  Validated: {len(hyp_result.get('validated', []))}")
        print(f"  Rejected: {len(hyp_result.get('rejected', []))}")

    # Reports summary
    if results.get("report_core"):
        print(f"  Core Snapshot: {results['report_core']}")
    if results.get("report_lifecycle"):
        print(f"  Lifecycle Ramp-Up: {results['report_lifecycle']}")

    # Pending actions
    pending = sm.load_pending_edges()
    if pending:
        print(f"\n  *** PENDING REVIEW: {len(pending)} edges ***")
        for e in pending:
            print(f"    > {e.get('name', 'Unknown')}: {e.get('reason', '')[:80]}")
        print("\n  Actions available:")
        print("    python run_ml_workflow.py approve-edge <H###>")
        print("    python run_ml_workflow.py remove-edge <name>")
        print("    python run_ml_workflow.py status")

    print("\n" + "=" * 70)

    return results


# =========================================================================
# STATUS MODE
# =========================================================================

def run_status():
    """Print current system status."""
    from state_manager import StateManager
    sm = StateManager()
    sm.print_status_banner()


# =========================================================================
# APPROVE / REMOVE EDGE MODES (Human-triggered)
# =========================================================================

def run_approve_edge(identifier: str):
    """
    Approve a pending edge and add it to config.py VALIDATED_EDGES.

    Args:
        identifier: Hypothesis ID (e.g., 'H001') or edge name
    """
    from state_manager import StateManager

    sm = StateManager()
    pending = sm.load_pending_edges()

    # Find matching pending edge
    target = None
    for e in pending:
        if (e.get("hypothesis_id") == identifier
                or e.get("name", "").startswith(identifier)):
            target = e
            break

    if target is None:
        print(f"\n  ERROR: No pending edge found matching '{identifier}'")
        print("  Available pending edges:")
        for e in pending:
            print(f"    {e.get('hypothesis_id', '---')}: {e.get('name', 'Unknown')}")
        return

    edge_def = target.get("edge_definition", {})
    test_result = target.get("test_result", {})

    print(f"\n  Approving edge: {target.get('name', 'Unknown')}")
    print(f"  Indicator: {edge_def.get('indicator', 'N/A')}")
    print(f"  Condition: {edge_def.get('condition', 'N/A')}")
    print(f"  Effect: {edge_def.get('effect_size_pp', test_result.get('effect_size_pp', 'N/A'))}pp")

    # Build new edge entry
    new_edge = {
        "name": target.get("name", f"{edge_def.get('indicator')}={edge_def.get('condition')}"),
        "indicator": edge_def.get("indicator", "unknown"),
        "condition": edge_def.get("condition", "unknown"),
        "effect_size_pp": edge_def.get("effect_size_pp", test_result.get("effect_size_pp", 0)),
        "confidence": edge_def.get("confidence", test_result.get("confidence", "MEDIUM")),
        "action": edge_def.get("action", "TRADE when active"),
        "validated_date": datetime.now().strftime("%Y-%m-%d"),
        "hypothesis_id": target.get("hypothesis_id", ""),
    }

    # Read config.py
    config_path = MODULE_ROOT / "config.py"
    with open(config_path, "r") as f:
        config_content = f.read()

    # Find VALIDATED_EDGES closing bracket position
    ve_start = config_content.find("VALIDATED_EDGES = [")
    if ve_start == -1:
        print("  ERROR: VALIDATED_EDGES not found in config.py")
        return

    # Find the closing ] for VALIDATED_EDGES
    bracket_depth = 0
    pos = ve_start + len("VALIDATED_EDGES = [")
    closing_bracket_pos = -1
    for i in range(pos, len(config_content)):
        if config_content[i] == '[':
            bracket_depth += 1
        elif config_content[i] == ']':
            if bracket_depth == 0:
                closing_bracket_pos = i
                break
            bracket_depth -= 1

    if closing_bracket_pos == -1:
        print("  ERROR: Could not find closing bracket of VALIDATED_EDGES")
        return

    # Build the new edge string
    new_edge_str = f"""    {{
        "name": "{new_edge['name']}",
        "indicator": "{new_edge['indicator']}",
        "condition": "{new_edge['condition']}",
        "effect_size_pp": {new_edge['effect_size_pp']},
        "confidence": "{new_edge['confidence']}",
        "action": "{new_edge['action']}",
        "validated_date": "{new_edge['validated_date']}",
    }},
"""

    # Insert before closing bracket
    config_content = (
        config_content[:closing_bracket_pos]
        + new_edge_str
        + config_content[closing_bracket_pos:]
    )

    with open(config_path, "w") as f:
        f.write(config_content)

    print(f"  [OK] Edge added to config.py VALIDATED_EDGES")

    # Remove from pending
    sm.remove_pending_edge(target.get("name"))
    print(f"  [OK] Removed from pending_edges.json")

    # Update hypothesis status if applicable
    hyp_id = target.get("hypothesis_id")
    if hyp_id:
        hyp_data = sm.load_hypotheses()
        for h in hyp_data.get("hypotheses", []):
            if h["id"] == hyp_id:
                h["status"] = "APPROVED"
                h["approved_date"] = datetime.now().isoformat()
                break
        sm.save_hypotheses(hyp_data)

    # Changelog
    sm.append_changelog(
        "EDGE_APPROVED",
        f"Edge approved: {new_edge['name']} ({new_edge['effect_size_pp']:+.1f}pp)",
        new_edge,
    )

    print(f"\n  Edge '{new_edge['name']}' is now in VALIDATED_EDGES")
    print("  It will be monitored in future validate-edges runs")


def run_remove_edge(edge_name: str):
    """
    Remove a degraded edge from config.py VALIDATED_EDGES.

    Args:
        edge_name: Name of the edge to remove
    """
    from state_manager import StateManager

    sm = StateManager()

    # Find the edge
    found = False
    for edge in VALIDATED_EDGES:
        if edge["name"] == edge_name:
            found = True
            break

    if not found:
        print(f"\n  ERROR: Edge '{edge_name}' not found in VALIDATED_EDGES")
        print("  Available edges:")
        for e in VALIDATED_EDGES:
            print(f"    - {e['name']}")
        return

    print(f"\n  Removing edge: {edge_name}")

    # Read config.py and remove the edge entry
    config_path = MODULE_ROOT / "config.py"
    with open(config_path, "r") as f:
        config_content = f.read()

    # Find the edge block in config.py
    name_marker = f'"name": "{edge_name}"'
    name_pos = config_content.find(name_marker)

    if name_pos == -1:
        print(f"  ERROR: Could not find '{edge_name}' in config.py")
        return

    # Find the opening { before this name
    open_brace = config_content.rfind("{", 0, name_pos)
    # Find the closing }, after this block
    close_brace = config_content.find("},", name_pos)

    if open_brace == -1 or close_brace == -1:
        print("  ERROR: Could not parse edge block in config.py")
        return

    # Remove the block including trailing comma/whitespace
    end_pos = close_brace + 2  # include },
    # Also remove leading whitespace
    while open_brace > 0 and config_content[open_brace - 1] in (' ', '\t'):
        open_brace -= 1
    # Remove trailing newline
    if end_pos < len(config_content) and config_content[end_pos] == '\n':
        end_pos += 1

    config_content = config_content[:open_brace] + config_content[end_pos:]

    with open(config_path, "w") as f:
        f.write(config_content)

    print(f"  [OK] Edge removed from config.py VALIDATED_EDGES")

    # Remove from pending if present
    sm.remove_pending_edge(edge_name)

    # Changelog
    sm.append_changelog(
        "EDGE_REMOVED",
        f"Edge removed: {edge_name}",
        {"name": edge_name, "removed_date": datetime.now().isoformat()},
    )

    print(f"\n  Edge '{edge_name}' has been removed")
    print("  EDGE_DEFINITIONS entry preserved for historical queries")


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EPOCH ML Workflow Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  daily             Daily export pipeline
  weekly            Weekly aggregation reports
  full              Full export (daily + weekly)
  validate-edges    Check health of all validated edges
  analyze           Full system analysis with indicator scan
  hypothesize       Discover and test new edge hypotheses
  test-hypothesis   Test a specific hypothesis by ID
  cycle             Full closed-loop cycle (all steps including reports)
  status            Print current system status
  approve-edge      Promote a pending edge into VALIDATED_EDGES
  remove-edge       Remove a degraded edge from VALIDATED_EDGES
  report-core       Generate core snapshot report (entry indicators)
  report-lifecycle  Generate lifecycle ramp-up report (M1 bar analysis)
""",
    )
    parser.add_argument(
        "mode",
        choices=[
            "daily", "weekly", "full",
            "validate-edges", "analyze", "hypothesize", "test-hypothesis",
            "cycle", "status", "approve-edge", "remove-edge",
            "report-core", "report-lifecycle",
        ],
        help="Workflow mode",
    )
    parser.add_argument("target", nargs="?", help="Hypothesis ID or edge name (for test-hypothesis, approve-edge, remove-edge)")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=30, help="Lookback days (default: 30)")
    parser.add_argument("--weeks", type=int, default=1, help="Weeks to aggregate (default: 1)")
    parser.add_argument("--start", type=str, help="Start date override (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date override (YYYY-MM-DD)")

    args = parser.parse_args()

    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else None

    print("=" * 70)
    print("  EPOCH ML WORKFLOW ORCHESTRATOR")
    print(f"  Mode: {args.mode.upper()}")
    print(f"  Date: {(date or datetime.now()).strftime('%Y-%m-%d')}")
    print("=" * 70)

    ensure_directories()

    if args.mode == "daily":
        run_daily_pipeline(date)
    elif args.mode == "weekly":
        run_weekly_pipeline(date, args.weeks)
    elif args.mode == "full":
        run_full_pipeline(date)
    elif args.mode == "validate-edges":
        run_validate_edges(days=args.days, start_date=args.start, end_date=args.end)
    elif args.mode == "analyze":
        run_analyze(days=args.days, start_date=args.start, end_date=args.end)
    elif args.mode == "hypothesize":
        run_hypothesize(days=args.days, start_date=args.start, end_date=args.end)
    elif args.mode == "test-hypothesis":
        if not args.target:
            print("  ERROR: Provide hypothesis ID, e.g.: test-hypothesis H001")
            sys.exit(1)
        run_test_hypothesis(args.target, days=args.days, start_date=args.start, end_date=args.end)
    elif args.mode == "cycle":
        run_cycle(date, days=args.days)
    elif args.mode == "status":
        run_status()
    elif args.mode == "approve-edge":
        if not args.target:
            print("  ERROR: Provide hypothesis ID or edge name")
            sys.exit(1)
        run_approve_edge(args.target)
    elif args.mode == "remove-edge":
        if not args.target:
            print("  ERROR: Provide edge name to remove")
            sys.exit(1)
        run_remove_edge(args.target)
    elif args.mode == "report-core":
        run_report_core()
    elif args.mode == "report-lifecycle":
        run_report_lifecycle()

    print("\n" + "=" * 70)
    print("  Workflow complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
