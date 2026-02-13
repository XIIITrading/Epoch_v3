"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Prompt Exporter - Generate Claude-readable analysis documents
XIII Trading LLC
================================================================================

Exports analysis results from Supabase tables to formatted markdown documents
optimized for Claude Code review.

Usage:
    # Export all analysis prompts
    python -m exporters.prompt_exporter

    # Export specific analysis
    python -m exporters.prompt_exporter --only direction model

    # Export to specific directory
    python -m exporters.prompt_exporter --output-dir ./my_outputs

================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging
import argparse
import sys

# Path structure: exporters/ -> ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
# Need to go up 4 levels from this file to reach 12_system_analysis
_system_analysis_dir = str(Path(__file__).parent.parent.parent.parent.resolve())
if _system_analysis_dir not in sys.path:
    sys.path.insert(0, _system_analysis_dir)

from config import DB_CONFIG, WIN_CONDITION_CONFIG

logger = logging.getLogger(__name__)

# Default output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'analysis'


class PromptExporter:
    """
    Exports analysis tables to Claude-readable markdown prompts.
    """

    def __init__(self, stop_type: Optional[str] = None, output_dir: Optional[Path] = None):
        self.stop_type = stop_type or WIN_CONDITION_CONFIG['default_stop_type']
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.conn = None

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _fetch_data(self, query: str, params: list = None) -> List[Dict[str, Any]]:
        """Fetch data from database."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or [])
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def _format_pct(self, val: float, decimals: int = 1) -> str:
        """Format a decimal as percentage."""
        if val is None:
            return "N/A"
        return f"{val * 100:.{decimals}f}%"

    def _format_lift(self, val: float) -> str:
        """Format lift with sign."""
        if val is None:
            return "N/A"
        sign = "+" if val >= 0 else ""
        return f"{sign}{val * 100:.1f}%"

    def _significance_marker(self, is_significant: bool, n: int) -> str:
        """Return marker for significance."""
        if is_significant:
            return ""
        return f" *(n={n}, insufficient)*"

    # =========================================================================
    # Export Functions
    # =========================================================================

    def export_direction_analysis(self) -> str:
        """Export direction analysis (Long vs Short)."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_direction
            WHERE stop_type = %s
            ORDER BY direction
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_trades = sum(r['total_trades'] for r in data)

        content = f"""# Direction Analysis (Long vs Short)

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}
- **Total Trades**: {total_trades}

## Summary
This analysis compares win rates between LONG and SHORT trades across all models.

## Data Table

| Direction | Total | Wins | Losses | Win Rate | Avg R |
|-----------|-------|------|--------|----------|-------|
"""
        for row in data:
            marker = self._significance_marker(row['is_significant'], row['total_trades'])
            content += f"| {row['direction']} | {row['total_trades']} | {row['wins']} | {row['losses']} | {self._format_pct(row['win_rate'])}{marker} | {row['avg_r_achieved']:.2f}R |\n"

        content += """
## Questions for Analysis
1. Is there a significant difference in win rate between Long and Short trades?
2. Does average R achieved differ meaningfully between directions?
3. Should different indicator thresholds be used for Long vs Short?

## Claude Analysis Instructions
Review the data above and provide:
1. Key observations about direction performance
2. Hypotheses for any differences observed
3. Recommendations for further investigation
"""
        filepath = self.output_dir / '01_direction_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_trade_type_analysis(self) -> str:
        """Export trade type analysis (Continuation vs Rejection)."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_trade_type
            WHERE stop_type = %s
            ORDER BY trade_type
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_trades = sum(r['total_trades'] for r in data)

        content = f"""# Trade Type Analysis (Continuation vs Rejection)

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}
- **Total Trades**: {total_trades}

## Model Groupings
- **CONTINUATION**: EPCH1 (Primary Zone) + EPCH3 (Secondary Zone) - Momentum through zone
- **REJECTION**: EPCH2 (Primary Zone) + EPCH4 (Secondary Zone) - Reversal at zone

## Data Table

| Trade Type | Models | Total | Wins | Losses | Win Rate | Avg R |
|------------|--------|-------|------|--------|----------|-------|
"""
        for row in data:
            marker = self._significance_marker(row['is_significant'], row['total_trades'])
            content += f"| {row['trade_type']} | {row['models']} | {row['total_trades']} | {row['wins']} | {row['losses']} | {self._format_pct(row['win_rate'])}{marker} | {row['avg_r_achieved']:.2f}R |\n"

        content += """
## Questions for Analysis
1. Do Continuation trades perform differently than Rejection trades?
2. Should indicator expectations differ between these trade types?
3. Is one trade type more suited to current market conditions?

## Claude Analysis Instructions
Review the data and provide insights on:
1. Performance comparison between trade types
2. Implications for indicator analysis (momentum vs absorption patterns)
3. Recommendations for separating analysis by trade type
"""
        filepath = self.output_dir / '02_trade_type_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_model_analysis(self) -> str:
        """Export model analysis (EPCH1/2/3/4)."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_model
            WHERE stop_type = %s
            ORDER BY model
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_trades = sum(r['total_trades'] for r in data)

        content = f"""# Model Analysis (EPCH1/2/3/4)

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}
- **Total Trades**: {total_trades}

## Model Definitions
| Model | Zone Type | Trade Type | Description |
|-------|-----------|------------|-------------|
| EPCH1 | PRIMARY | CONTINUATION | Momentum continuation with macro trend |
| EPCH2 | PRIMARY | REJECTION | Counter-trend rejection at primary zone |
| EPCH3 | SECONDARY | CONTINUATION | Counter-trend continuation through secondary zone |
| EPCH4 | SECONDARY | REJECTION | Rejection back toward macro trend |

## Performance Data

| Model | Zone | Trade Type | Total | Wins | Losses | Win Rate | Avg R |
|-------|------|------------|-------|------|--------|----------|-------|
"""
        for row in data:
            marker = self._significance_marker(row['is_significant'], row['total_trades'])
            content += f"| {row['model']} | {row['zone_type']} | {row['trade_type']} | {row['total_trades']} | {row['wins']} | {row['losses']} | {self._format_pct(row['win_rate'])}{marker} | {row['avg_r_achieved']:.2f}R |\n"

        content += """
## Questions for Analysis
1. Which model has the highest win rate?
2. Do Primary Zone trades perform better than Secondary Zone trades?
3. Are there models that should be prioritized or avoided?

## Claude Analysis Instructions
Analyze the model performance data and provide:
1. Ranking of models by risk-adjusted performance
2. Observations about Zone Type impact
3. Recommendations for model-specific indicator thresholds
"""
        filepath = self.output_dir / '03_model_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_model_direction_analysis(self) -> str:
        """Export model + direction analysis (8 combinations)."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_model_direction
            WHERE stop_type = %s
            ORDER BY model, direction
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_trades = sum(r['total_trades'] for r in data)

        content = f"""# Model + Direction Analysis

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}
- **Total Trades**: {total_trades}

## Overview
This analysis breaks down performance by all 8 combinations of Model (4) x Direction (2).

## Performance Data

| Model | Direction | Zone | Trade Type | Total | Wins | Losses | Win Rate | Avg R |
|-------|-----------|------|------------|-------|------|--------|----------|-------|
"""
        for row in data:
            marker = self._significance_marker(row['is_significant'], row['total_trades'])
            content += f"| {row['model']} | {row['direction']} | {row['zone_type']} | {row['trade_type']} | {row['total_trades']} | {row['wins']} | {row['losses']} | {self._format_pct(row['win_rate'])}{marker} | {row['avg_r_achieved']:.2f}R |\n"

        content += """
## Questions for Analysis
1. Which Model + Direction combinations have the highest win rates?
2. Are there combinations that should be avoided entirely?
3. Do Long and Short trades perform differently within the same model?

## Claude Analysis Instructions
Provide detailed analysis of:
1. Top 3 and Bottom 3 performing combinations
2. Patterns in direction performance by model type
3. Specific recommendations for each combination
"""
        filepath = self.output_dir / '04_model_direction_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_indicator_trend_analysis(self) -> str:
        """Export indicator trend analysis."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_indicator_trend
            WHERE stop_type = %s
              AND grouping_type = 'model_direction'
            ORDER BY grouping_value, indicator, trend_state
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Indicator Trend Analysis

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}

## Overview
This analysis shows win rates when each indicator's **trend** (linear regression over ramp period) is RISING, FALLING, or FLAT.

A positive **Lift** means the win rate is higher than the baseline for that grouping.

## Key Indicators
- **vol_delta**: Volume buy/sell differential trend
- **vol_roc**: Volume rate of change trend
- **long_score**: Composite long score trend
- **short_score**: Composite short score trend
- **sma_spread**: SMA spread trend
- **candle_range_pct**: Candle range trend

## Data by Model + Direction

"""
        # Group by model_direction
        by_group = {}
        for row in data:
            gv = row['grouping_value']
            if gv not in by_group:
                by_group[gv] = []
            by_group[gv].append(row)

        for group_val, rows in sorted(by_group.items()):
            baseline = rows[0]['baseline_win_rate'] if rows else None
            content += f"### {group_val} (Baseline: {self._format_pct(baseline)})\n\n"
            content += "| Indicator | Trend | N | Win Rate | Lift |\n"
            content += "|-----------|-------|---|----------|------|\n"

            for row in rows:
                marker = "" if row['is_significant'] else "*"
                content += f"| {row['indicator']} | {row['trend_state']} | {row['total_trades']}{marker} | {self._format_pct(row['win_rate'])} | {self._format_lift(row['lift_vs_baseline'])} |\n"

            content += "\n"

        content += """
## Claude Analysis Instructions
Analyze the trend data and identify:
1. Which indicators have the most predictive trend patterns per model+direction?
2. Are there "universal" patterns (e.g., RISING vol_delta always good)?
3. Specific trend combinations that significantly outperform baseline
4. Patterns that differ between Continuation and Rejection models

*Note: Rows marked with * have fewer than 30 trades and may not be statistically significant.*
"""
        filepath = self.output_dir / '05_indicator_trend_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_indicator_momentum_analysis(self) -> str:
        """Export indicator momentum analysis."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_indicator_momentum
            WHERE stop_type = %s
              AND grouping_type = 'model_direction'
            ORDER BY grouping_value, indicator, momentum_state
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Indicator Momentum Analysis

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}

## Overview
This analysis shows win rates when each indicator's **momentum** (first-half vs second-half of ramp period) is BUILDING, FADING, or STABLE.

- **BUILDING**: Second half average > First half average (indicator accelerating toward entry)
- **FADING**: Second half average < First half average (indicator decelerating toward entry)
- **STABLE**: Minimal change between halves

## Data by Model + Direction

"""
        by_group = {}
        for row in data:
            gv = row['grouping_value']
            if gv not in by_group:
                by_group[gv] = []
            by_group[gv].append(row)

        for group_val, rows in sorted(by_group.items()):
            baseline = rows[0]['baseline_win_rate'] if rows else None
            content += f"### {group_val} (Baseline: {self._format_pct(baseline)})\n\n"
            content += "| Indicator | Momentum | N | Win Rate | Lift |\n"
            content += "|-----------|----------|---|----------|------|\n"

            for row in rows:
                marker = "" if row['is_significant'] else "*"
                content += f"| {row['indicator']} | {row['momentum_state']} | {row['total_trades']}{marker} | {self._format_pct(row['win_rate'])} | {self._format_lift(row['lift_vs_baseline'])} |\n"

            content += "\n"

        content += """
## Claude Analysis Instructions
Analyze the momentum data to identify:
1. Which momentum patterns are most predictive of wins?
2. Does BUILDING momentum in long_score predict Long wins?
3. Does FADING vol_delta predict Rejection trade wins (absorption pattern)?
4. Differences between Continuation and Rejection models

*Note: Rows marked with * have fewer than 30 trades.*
"""
        filepath = self.output_dir / '06_indicator_momentum_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_structure_consistency_analysis(self) -> str:
        """Export structure consistency analysis."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_structure_consistency
            WHERE stop_type = %s
              AND grouping_type = 'model_direction'
            ORDER BY grouping_value, indicator, consistency_state
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Structure Consistency Analysis

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}

## Overview
This analysis shows win rates based on M15 and H1 **structure consistency** during the ramp period.

### Consistency States
- **CONSISTENT_BULL**: Structure bullish for 80%+ of ramp bars
- **CONSISTENT_BEAR**: Structure bearish for 80%+ of ramp bars
- **FLIP_TO_BULL**: Structure changed from bearish to bullish during ramp
- **FLIP_TO_BEAR**: Structure changed from bullish to bearish during ramp
- **MIXED**: No clear pattern

## Data by Model + Direction

"""
        by_group = {}
        for row in data:
            gv = row['grouping_value']
            if gv not in by_group:
                by_group[gv] = []
            by_group[gv].append(row)

        for group_val, rows in sorted(by_group.items()):
            baseline = rows[0]['baseline_win_rate'] if rows else None
            content += f"### {group_val} (Baseline: {self._format_pct(baseline)})\n\n"
            content += "| Timeframe | Consistency | N | Win Rate | Lift |\n"
            content += "|-----------|-------------|---|----------|------|\n"

            for row in rows:
                marker = "" if row['is_significant'] else "*"
                content += f"| {row['indicator'].upper()} | {row['consistency_state']} | {row['total_trades']}{marker} | {self._format_pct(row['win_rate'])} | {self._format_lift(row['lift_vs_baseline'])} |\n"

            content += "\n"

        content += """
## Claude Analysis Instructions
Analyze structure consistency patterns:
1. Does consistent structure alignment with trade direction improve win rates?
2. Are FLIP patterns (structure changing) predictive for any model?
3. Which timeframe (M15 vs H1) is more predictive?
4. Do Rejection trades benefit from counter-structure setups?

*Note: Rows marked with * have fewer than 30 trades.*
"""
        filepath = self.output_dir / '07_structure_consistency_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_entry_snapshot_analysis(self) -> str:
        """Export entry snapshot analysis."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_entry_snapshot
            WHERE stop_type = %s
              AND grouping_type = 'model_direction'
            ORDER BY grouping_value, indicator, bucket
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Entry Bar Snapshot Analysis

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}

## Overview
This analysis shows win rates based on indicator values **at the entry bar** (bar 0), bucketed into ranges.

This answers: "Given the indicator value at the moment of entry, what is the win probability?"

## Data by Model + Direction

"""
        by_group = {}
        for row in data:
            gv = row['grouping_value']
            if gv not in by_group:
                by_group[gv] = []
            by_group[gv].append(row)

        for group_val, rows in sorted(by_group.items()):
            baseline = rows[0]['baseline_win_rate'] if rows else None
            content += f"### {group_val} (Baseline: {self._format_pct(baseline)})\n\n"
            content += "| Indicator | Bucket | N | Win Rate | Lift |\n"
            content += "|-----------|--------|---|----------|------|\n"

            for row in rows:
                marker = "" if row['is_significant'] else "*"
                content += f"| {row['indicator']} | {row['bucket']} | {row['total_trades']}{marker} | {self._format_pct(row['win_rate'])} | {self._format_lift(row['lift_vs_baseline'])} |\n"

            content += "\n"

        content += """
## Claude Analysis Instructions
Analyze entry bar values to identify:
1. Optimal score ranges for entry (e.g., long_score 5-7 for Long trades)
2. Vol_delta magnitude thresholds that improve win rates
3. Entry bar "red flags" that should prevent entry
4. Model-specific entry criteria

*Note: Rows marked with * have fewer than 30 trades.*
"""
        filepath = self.output_dir / '08_entry_snapshot_analysis.md'
        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {filepath}")
        return str(filepath)

    def export_progression_analysis(self) -> str:
        """Export progression average analysis as JSON for detailed review."""
        data = self._fetch_data("""
            SELECT * FROM ramp_analysis_progression_avg
            WHERE stop_type = %s
              AND grouping_type = 'model_direction'
            ORDER BY grouping_value, outcome, bars_to_entry
        """, [self.stop_type])

        if not data:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Structure for JSON output
        output = {
            'metadata': {
                'generated': timestamp,
                'stop_type': self.stop_type,
                'description': 'Average indicator values at each bar position (-15 to 0) by outcome'
            },
            'progressions': {}
        }

        # Group by model_direction and outcome
        for row in data:
            gv = row['grouping_value']
            outcome = row['outcome']

            if gv not in output['progressions']:
                output['progressions'][gv] = {'WIN': [], 'LOSS': []}

            bar_data = {
                'bars_to_entry': row['bars_to_entry'],
                'avg_candle_range_pct': float(row['avg_candle_range_pct']) if row['avg_candle_range_pct'] else None,
                'avg_vol_delta': float(row['avg_vol_delta']) if row['avg_vol_delta'] else None,
                'avg_vol_roc': float(row['avg_vol_roc']) if row['avg_vol_roc'] else None,
                'avg_sma_spread': float(row['avg_sma_spread']) if row['avg_sma_spread'] else None,
                'avg_long_score': float(row['avg_long_score']) if row['avg_long_score'] else None,
                'avg_short_score': float(row['avg_short_score']) if row['avg_short_score'] else None,
                'sample_size': row['sample_size'],
            }

            output['progressions'][gv][outcome].append(bar_data)

        # Write JSON
        json_path = self.output_dir / '09_progression_analysis.json'
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)

        # Also write a markdown summary
        content = f"""# Progression Analysis (Bar-by-Bar)

## Metadata
- **Generated**: {timestamp}
- **Stop Type**: {self.stop_type}

## Overview
This analysis shows **average indicator values at each bar position** from bar -15 (earliest) to bar 0 (entry), segmented by WIN vs LOSS outcomes.

The detailed data is in `09_progression_analysis.json`. This summary highlights key patterns.

## How to Interpret
Compare the WIN progression to the LOSS progression for each model+direction:
- Where do they diverge?
- What indicator behavior separates winners from losers?

## Claude Analysis Instructions
Review the JSON data and identify:
1. At which bar position do WIN and LOSS trades begin to diverge?
2. What indicator patterns are present in winning trades but absent in losing trades?
3. Are there "early warning" signs at bar -10 or -5 that predict outcome?
4. Create a narrative description of "what a winning trade looks like" for each model+direction

## Key Questions for Each Model+Direction
For Continuation trades (EPCH1, EPCH3):
- Does vol_delta build in the trade direction as entry approaches?
- Does momentum accelerate (vol_roc increasing)?

For Rejection trades (EPCH2, EPCH4):
- Does vol_delta show absorption (shrinking) before flipping?
- Does vol_roc decrease (exhaustion) before entry?
"""
        md_path = self.output_dir / '09_progression_summary.md'
        with open(md_path, 'w') as f:
            f.write(content)

        logger.info(f"Exported: {json_path}")
        logger.info(f"Exported: {md_path}")
        return str(json_path)


def export_all_prompts(
    stop_type: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> List[str]:
    """
    Export all analysis prompts.

    Returns:
        List of exported file paths
    """
    exporter = PromptExporter(stop_type=stop_type, output_dir=output_dir)

    if not exporter.connect():
        return []

    try:
        exported = []

        # Export each analysis
        exports = [
            exporter.export_direction_analysis,
            exporter.export_trade_type_analysis,
            exporter.export_model_analysis,
            exporter.export_model_direction_analysis,
            exporter.export_indicator_trend_analysis,
            exporter.export_indicator_momentum_analysis,
            exporter.export_structure_consistency_analysis,
            exporter.export_entry_snapshot_analysis,
            exporter.export_progression_analysis,
        ]

        for export_fn in exports:
            try:
                path = export_fn()
                if path:
                    exported.append(path)
            except Exception as e:
                logger.error(f"Error in {export_fn.__name__}: {e}")

        return exported

    finally:
        exporter.disconnect()


def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description='Export analysis results to Claude-readable prompts'
    )
    parser.add_argument(
        '--stop-type',
        default=None,
        help='Stop type for outcomes (default from config)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory for prompt files'
    )

    args = parser.parse_args()

    exported = export_all_prompts(
        stop_type=args.stop_type,
        output_dir=args.output_dir
    )

    print(f"\nExported {len(exported)} files:")
    for path in exported:
        print(f"  - {path}")


if __name__ == '__main__':
    main()
