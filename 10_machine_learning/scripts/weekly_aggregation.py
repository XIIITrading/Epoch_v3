"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Weekly Aggregation
XIII Trading LLC
================================================================================

Generates weekly summary reports from daily exports for Claude edge audits.
ALL outcomes sourced from trades_m5_r_win (sole source of truth).

Usage:
    python weekly_aggregation.py                     # Current week
    python weekly_aggregation.py --weeks 4           # Last 4 weeks
    python weekly_aggregation.py --date 2026-01-31   # Week containing date
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
    DB_CONFIG, WEEKLY_EXPORTS_DIR, DAILY_EXPORTS_DIR, EXPORT_CONFIG,
    CANONICAL_OUTCOME, VALIDATED_EDGES, EDGE_CRITERIA, ensure_directories
)


class WeeklyAggregator:
    """Generates weekly summary reports for Claude analysis.

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

    def get_week_bounds(self, date: datetime) -> tuple:
        """Get Monday-Friday bounds for the week containing date."""
        # Find Monday of that week
        monday = date - timedelta(days=date.weekday())
        friday = monday + timedelta(days=4)
        return monday, friday

    def generate_weekly_report(self, end_date: datetime = None) -> str:
        """
        Generate a weekly aggregation report in markdown format.

        Source: trades_m5_r_win (sole source of truth)
        """
        if end_date is None:
            end_date = datetime.now()

        monday, friday = self.get_week_bounds(end_date)
        start_str = monday.strftime("%Y-%m-%d")
        end_str = friday.strftime("%Y-%m-%d")

        # Weekly trade summary
        query = """
        SELECT
            m.date,
            COUNT(*) as trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(SUM(m.pnl_r)::numeric, 2) as total_r,
            ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
        FROM trades_m5_r_win m
        WHERE m.date BETWEEN %s AND %s
        GROUP BY m.date
        ORDER BY m.date
        """
        daily_stats = self._execute(query, [start_str, end_str])

        # Model breakdown for the week
        model_query = """
        SELECT
            m.model,
            COUNT(*) as trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(SUM(m.pnl_r)::numeric, 2) as total_r
        FROM trades_m5_r_win m
        WHERE m.date BETWEEN %s AND %s
        GROUP BY m.model
        ORDER BY m.model
        """
        model_stats = self._execute(model_query, [start_str, end_str])

        # Edge analysis: H1 Structure breakdown
        h1_query = """
        SELECT
            ei.h1_structure,
            COUNT(*) as trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE m.date BETWEEN %s AND %s
        AND ei.h1_structure IS NOT NULL
        GROUP BY ei.h1_structure
        ORDER BY ei.h1_structure
        """
        h1_stats = self._execute(h1_query, [start_str, end_str])

        # Health score distribution: winners vs losers
        health_query = """
        SELECT
            CASE
                WHEN ei.health_score >= 8 THEN 'STRONG (8-10)'
                WHEN ei.health_score >= 6 THEN 'MODERATE (6-7)'
                WHEN ei.health_score >= 4 THEN 'WEAK (4-5)'
                ELSE 'CRITICAL (0-3)'
            END as health_tier,
            COUNT(*) as trades,
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as winners,
            ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
        FROM trades_m5_r_win m
        LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
        WHERE m.date BETWEEN %s AND %s
        AND ei.health_score IS NOT NULL
        GROUP BY health_tier
        ORDER BY health_tier
        """
        health_stats = self._execute(health_query, [start_str, end_str])

        # Build totals
        total_trades = sum(d["trades"] for d in daily_stats)
        total_winners = sum(d["winners"] for d in daily_stats)
        total_r = sum(float(d["total_r"] or 0) for d in daily_stats)
        week_wr = round(total_winners / total_trades * 100, 1) if total_trades else 0

        # Build markdown report
        md = f"""# Weekly Aggregation Report

**Week**: {start_str} to {end_str}
**Generated**: {datetime.now().isoformat()}
**Win Condition**: {CANONICAL_OUTCOME['stop_type']} (ATR({CANONICAL_OUTCOME['atr_period']}) x {CANONICAL_OUTCOME['atr_multiplier']}, {CANONICAL_OUTCOME['trigger']}-based)
**Data Source**: trades_m5_r_win (sole source of truth)

---

## Weekly Summary

| Metric | Value |
|--------|-------|
| Total Trades | {total_trades} |
| Winners | {total_winners} |
| Win Rate | {week_wr}% |
| Total R | {total_r:+.2f} |
| Expectancy | {total_r / total_trades:.3f}R | {'' if not total_trades else ''}

---

## Daily Breakdown

| Date | Trades | Winners | Win Rate | Total R | Avg R |
|------|--------|---------|----------|---------|-------|
"""

        for d in daily_stats:
            wr = round(d["winners"] / d["trades"] * 100, 1) if d["trades"] else 0
            md += (
                f"| {d['date']} | {d['trades']} | {d['winners']} "
                f"| {wr}% | {float(d['total_r'] or 0):+.2f} | {float(d['avg_r'] or 0):+.3f} |\n"
            )

        md += """
---

## Model Performance

| Model | Trades | Winners | Win Rate | Total R |
|-------|--------|---------|----------|---------|
"""

        for ms in model_stats:
            wr = round(ms["winners"] / ms["trades"] * 100, 1) if ms["trades"] else 0
            md += (
                f"| {ms['model']} | {ms['trades']} | {ms['winners']} "
                f"| {wr}% | {float(ms['total_r'] or 0):+.2f} |\n"
            )

        md += """
---

## Edge Effectiveness: H1 Structure

| H1 Structure | Trades | Winners | Win Rate | Avg R |
|-------------|--------|---------|----------|-------|
"""

        for h in h1_stats:
            wr = round(h["winners"] / h["trades"] * 100, 1) if h["trades"] else 0
            md += (
                f"| {h['h1_structure']} | {h['trades']} | {h['winners']} "
                f"| {wr}% | {float(h['avg_r'] or 0):+.3f} |\n"
            )

        md += """
---

## Health Score Distribution

| Health Tier | Trades | Winners | Win Rate | Avg R |
|-------------|--------|---------|----------|-------|
"""

        for hs in health_stats:
            wr = round(hs["winners"] / hs["trades"] * 100, 1) if hs["trades"] else 0
            md += (
                f"| {hs['health_tier']} | {hs['trades']} | {hs['winners']} "
                f"| {wr}% | {float(hs['avg_r'] or 0):+.3f} |\n"
            )

        md += f"""
---

## Validated Edges Status

| Edge | Expected Effect | This Week Status |
|------|----------------|------------------|
"""

        for edge in VALIDATED_EDGES:
            md += f"| {edge['name']} | {edge['effect_size_pp']:+.1f}pp | Review in audit |\n"

        md += f"""
---

## Notes

- All outcomes from `trades_m5_r_win.is_winner` (sole source)
- Edge criteria: p < {EDGE_CRITERIA['p_value_threshold']}, effect > {EDGE_CRITERIA['effect_size_threshold']}pp
- Use this report with `/prompts/edge_audit.md` for weekly Claude analysis

---

*Generated: {datetime.now().isoformat()}*
"""

        return md

    def run_weekly_aggregation(self, end_date: datetime = None, weeks: int = 1):
        """Run weekly aggregation and save to files."""
        if end_date is None:
            end_date = datetime.now()

        ensure_directories()

        for i in range(weeks):
            target_date = end_date - timedelta(weeks=i)
            monday, friday = self.get_week_bounds(target_date)
            week_label = monday.strftime("%Y%m%d")

            print(f"\n  Generating week of {monday.strftime('%Y-%m-%d')}...")

            report = self.generate_weekly_report(target_date)
            report_path = WEEKLY_EXPORTS_DIR / f"weekly_report_{week_label}.md"
            with open(report_path, "w") as f:
                f.write(report)
            print(f"    Report: {report_path}")

        print(f"\n  Weekly aggregation complete ({weeks} week(s))")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Generate weekly aggregation reports")
    parser.add_argument("--date", type=str, help="Date within target week (YYYY-MM-DD)")
    parser.add_argument("--weeks", type=int, default=1, help="Number of weeks to generate (default: 1)")
    args = parser.parse_args()

    print("=" * 70)
    print("  EPOCH ML - Weekly Aggregation")
    print("  Source: trades_m5_r_win (canonical)")
    print("=" * 70)

    aggregator = WeeklyAggregator()

    try:
        end_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
        aggregator.run_weekly_aggregation(end_date=end_date, weeks=args.weeks)
    finally:
        aggregator.close()

    print("\n" + "=" * 70)
    print("  Aggregation complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
