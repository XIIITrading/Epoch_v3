"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Export for Claude
XIII Trading LLC
================================================================================

Generates Claude-readable exports from the EPOCH database.
ALL outcomes sourced from trades_m5_r_win (sole source of truth).

Usage:
    python export_for_claude.py                    # Export today's data
    python export_for_claude.py --date 2026-01-31  # Export specific date
    python export_for_claude.py --all              # Export last 30 available dates
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_CONFIG, DAILY_EXPORTS_DIR, EXPORT_CONFIG, CANONICAL_OUTCOME,
    VALIDATED_EDGES, EDGE_CRITERIA, ensure_directories
)


class ClaudeExporter:
    """Exports EPOCH data in Claude-readable format.

    All trade data and outcomes sourced exclusively from trades_m5_r_win.
    The legacy trades table is NOT used.
    """

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        print(f"  Connected to Supabase")

    def _execute(self, query: str, params: list = None) -> List[Dict]:
        """Execute query and return results as list of dicts."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def export_trades(self, date: datetime) -> Dict[str, Any]:
        """
        Export trades with canonical outcomes for a specific date.

        Returns a Claude-optimized structure with:
        - Summary statistics
        - Trade list with key fields
        - Model breakdown
        - Direction breakdown

        Source: trades_m5_r_win (sole source of truth)
        """
        date_str = date.strftime("%Y-%m-%d")

        query = """
        SELECT
            m.trade_id,
            m.date,
            m.ticker,
            m.model,
            m.direction,
            m.entry_price,
            m.entry_time::text,
            m.zone_high,
            m.zone_low,
            m.zone_type,
            -- Canonical outcome
            m.is_winner,
            m.outcome,
            m.pnl_r,
            m.exit_reason,
            m.stop_price,
            m.stop_distance,
            m.max_r_achieved,
            m.reached_2r,
            m.reached_3r,
            m.outcome_method,
            -- R-level tracking
            m.r1_hit,
            m.r1_time::text,
            m.r2_hit,
            m.r3_hit,
            m.stop_hit,
            m.stop_hit_time::text,
            m.minutes_to_r1,
            -- Entry indicators
            ei.health_score,
            ei.h1_structure,
            ei.m15_structure,
            ei.m5_structure,
            ei.vol_roc,
            ei.vol_delta,
            ei.sma_spread,
            ei.sma_momentum_label
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE m.date = %s
        ORDER BY m.entry_time
        """

        trades = self._execute(query, [date_str])

        if not trades:
            return {
                "date": date_str,
                "total_trades": 0,
                "message": "No trades found for this date"
            }

        # Calculate summary statistics
        winners = [t for t in trades if t["is_winner"]]
        losers = [t for t in trades if not t["is_winner"]]
        total_r = sum(t["pnl_r"] or 0 for t in trades)

        summary = {
            "date": date_str,
            "total_trades": len(trades),
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": round(len(winners) / len(trades) * 100, 1) if trades else 0,
            "total_r": round(total_r, 2),
            "expectancy_r": round(total_r / len(trades), 3) if trades else 0,
            "canonical_win_condition": (
                f"{CANONICAL_OUTCOME['stop_type']} "
                f"(ATR({CANONICAL_OUTCOME['atr_period']}) x {CANONICAL_OUTCOME['atr_multiplier']}, "
                f"{CANONICAL_OUTCOME['trigger']}-based)"
            ),
            "data_source": "trades_m5_r_win (sole source of truth)",
        }

        # Model breakdown
        model_stats = {}
        for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
            model_trades = [t for t in trades if t["model"] == model]
            model_winners = [t for t in model_trades if t["is_winner"]]
            if model_trades:
                model_stats[model] = {
                    "trades": len(model_trades),
                    "winners": len(model_winners),
                    "win_rate": round(len(model_winners) / len(model_trades) * 100, 1),
                    "total_r": round(sum(t["pnl_r"] or 0 for t in model_trades), 2),
                }

        # Direction breakdown
        direction_stats = {}
        for direction in ["LONG", "SHORT"]:
            dir_trades = [t for t in trades if t["direction"] == direction]
            dir_winners = [t for t in dir_trades if t["is_winner"]]
            if dir_trades:
                direction_stats[direction] = {
                    "trades": len(dir_trades),
                    "winners": len(dir_winners),
                    "win_rate": round(len(dir_winners) / len(dir_trades) * 100, 1),
                    "total_r": round(sum(t["pnl_r"] or 0 for t in dir_trades), 2),
                }

        # Clean trades for export (convert dates, handle None values)
        clean_trades = []
        for t in trades:
            clean_trade = {}
            for k, v in t.items():
                if v is None:
                    clean_trade[k] = None
                elif hasattr(v, 'isoformat'):
                    clean_trade[k] = v.isoformat()
                elif isinstance(v, (int, float, str, bool)):
                    clean_trade[k] = v
                else:
                    clean_trade[k] = str(v)
            clean_trades.append(clean_trade)

        return {
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "trades_m5_r_win",
            "summary": summary,
            "model_breakdown": model_stats,
            "direction_breakdown": direction_stats,
            "trades": clean_trades,
        }

    def export_edge_analysis(self, date: datetime) -> str:
        """
        Export edge analysis results as markdown for Claude.

        Source: trades_m5_r_win (sole source of truth)
        """
        date_str = date.strftime("%Y-%m-%d")

        # Get trade data for the date range (last 30 days for context)
        start_date = (date - timedelta(days=30)).strftime("%Y-%m-%d")

        query = """
        SELECT
            COUNT(*) as total_trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
        FROM trades_m5_r_win m
        WHERE m.date BETWEEN %s AND %s
        """

        stats = self._execute(query, [start_date, date_str])
        baseline = stats[0] if stats else {"total_trades": 0, "winners": 0, "avg_r": 0}

        baseline_wr = (
            (baseline["winners"] / baseline["total_trades"] * 100)
            if baseline["total_trades"]
            else 0
        )

        # Build markdown report
        md = f"""# Edge Analysis Report

**Date**: {date_str}
**Analysis Period**: {start_date} to {date_str}
**Total Trades**: {baseline['total_trades']}
**Baseline Win Rate**: {baseline_wr:.1f}%
**Average R**: {baseline['avg_r']}
**Data Source**: trades_m5_r_win (sole source of truth)

---

## Validated Edges

| Edge | Effect Size | Confidence | Action |
|------|-------------|------------|--------|
"""

        for edge in VALIDATED_EDGES:
            md += (
                f"| {edge['name']} | {edge['effect_size_pp']:+.1f}pp "
                f"| {edge['confidence']} | {edge['action']} |\n"
            )

        md += f"""

---

## Edge Criteria

- **Statistical Significance**: p-value < {EDGE_CRITERIA['p_value_threshold']}
- **Practical Significance**: Effect size > {EDGE_CRITERIA['effect_size_threshold']}pp
- **Minimum Sample (MEDIUM)**: {EDGE_CRITERIA['min_sample_medium']} trades
- **Minimum Sample (HIGH)**: {EDGE_CRITERIA['min_sample_high']} trades

---

## Notes

- Win condition: {CANONICAL_OUTCOME['stop_type']} stop (ATR({CANONICAL_OUTCOME['atr_period']}) x {CANONICAL_OUTCOME['atr_multiplier']}, {CANONICAL_OUTCOME['trigger']}-based)
- All outcomes from `trades_m5_r_win.is_winner` (sole source)
- Effect sizes measured in percentage points (pp) above baseline

---

*Generated: {datetime.now().isoformat()}*
"""

        return md

    def export_system_metrics(self, date: datetime) -> Dict[str, Any]:
        """
        Export system-wide metrics for Claude analysis.

        Source: trades_m5_r_win (sole source of truth)
        """
        date_str = date.strftime("%Y-%m-%d")

        # Overall stats query - trades_m5_r_win only
        query = """
        SELECT
            COUNT(*) as total_trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(SUM(m.pnl_r)::numeric, 2) as total_r,
            ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r,
            ROUND(STDDEV(m.pnl_r)::numeric, 3) as std_r
        FROM trades_m5_r_win m
        WHERE m.date BETWEEN %s AND %s
        """

        # Last 30 days
        start_30 = (date - timedelta(days=30)).strftime("%Y-%m-%d")
        stats_30 = self._execute(query, [start_30, date_str])

        # Last 7 days
        start_7 = (date - timedelta(days=7)).strftime("%Y-%m-%d")
        stats_7 = self._execute(query, [start_7, date_str])

        def calc_metrics(stats):
            if not stats or not stats[0]["total_trades"]:
                return {"trades": 0, "win_rate": 0, "total_r": 0, "avg_r": 0, "std_r": 0}
            s = stats[0]
            return {
                "trades": s["total_trades"],
                "win_rate": round(s["winners"] / s["total_trades"] * 100, 1),
                "total_r": float(s["total_r"] or 0),
                "avg_r": float(s["avg_r"] or 0),
                "std_r": float(s["std_r"] or 0),
            }

        return {
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "trades_m5_r_win",
            "report_date": date_str,
            "last_30_days": calc_metrics(stats_30),
            "last_7_days": calc_metrics(stats_7),
            "canonical_win_condition": CANONICAL_OUTCOME,
            "validated_edges_count": len(VALIDATED_EDGES),
        }

    def run_daily_export(self, date: datetime = None) -> Dict[str, Any]:
        """Run full daily export and save to files."""
        if date is None:
            date = datetime.now()

        date_str = date.strftime(EXPORT_CONFIG["date_format"])
        ensure_directories()

        print(f"\n  Exporting data for {date.strftime('%Y-%m-%d')}...")

        # Export trades
        trades_data = self.export_trades(date)
        trades_path = DAILY_EXPORTS_DIR / f"trades_{date_str}.json"
        with open(trades_path, "w") as f:
            json.dump(trades_data, f, indent=EXPORT_CONFIG["json_indent"], default=str)
        print(f"    Trades: {trades_path}")

        # Export edge analysis
        edge_md = self.export_edge_analysis(date)
        edge_path = DAILY_EXPORTS_DIR / f"edge_analysis_{date_str}.md"
        with open(edge_path, "w") as f:
            f.write(edge_md)
        print(f"    Edge Analysis: {edge_path}")

        # Export system metrics
        metrics_data = self.export_system_metrics(date)
        metrics_path = DAILY_EXPORTS_DIR / f"system_metrics_{date_str}.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics_data, f, indent=EXPORT_CONFIG["json_indent"], default=str)
        print(f"    System Metrics: {metrics_path}")

        print(f"\n  Daily export complete for {date.strftime('%Y-%m-%d')}")

        return {
            "date": date_str,
            "files": [str(trades_path), str(edge_path), str(metrics_path)],
            "summary": trades_data.get("summary", {}),
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Export EPOCH data for Claude analysis")
    parser.add_argument("--date", type=str, help="Export date (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Export all available dates (last 30)")
    args = parser.parse_args()

    print("=" * 70)
    print("  EPOCH ML EXPORT - Claude Data Pipeline")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 70)

    exporter = ClaudeExporter()

    try:
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d")
            result = exporter.run_daily_export(date)
            print(f"\n  Summary: {result.get('summary', {})}")
        elif args.all:
            # Get all available dates from canonical table
            dates = exporter._execute(
                "SELECT DISTINCT date FROM trades_m5_r_win ORDER BY date DESC LIMIT 30"
            )
            print(f"\n  Found {len(dates)} dates to export")
            for i, d in enumerate(dates):
                print(f"\n  [{i + 1}/{len(dates)}]")
                exporter.run_daily_export(d["date"])
        else:
            # Default: today
            result = exporter.run_daily_export()
            print(f"\n  Summary: {result.get('summary', {})}")
    finally:
        exporter.close()

    print("\n" + "=" * 70)
    print("  Export complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
