"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 04: INDICATOR ANALYSIS v2.0
Scorecard Exporter - Writes scorecard markdown + JSON files
XIII Trading LLC
================================================================================

Exports scorecard analysis results to structured files:
  results/YYYYMMDD/scorecards/
    CLAUDE.md               - Instructions for Claude Code
    tier_ranking.md          - All 11 indicators × 4 trade types
    long_continuation.md     - Trade type scorecard
    short_continuation.md    - Trade type scorecard
    long_rejection.md        - Trade type scorecard
    short_rejection.md       - Trade type scorecard
    rubric_summary.md        - Cross-type patterns
    _prior.json              - Machine-readable for degradation tracking
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from analysis.scorecard_analyzer import (
    DegradationFlag,
    ScorecardResult,
    TradeTypeResult,
)
from analysis.tier_ranker import IndicatorScore
from config import MODULE_ROOT, TRADE_TYPES, SCORECARD_TOP_N


class ScorecardExporter:
    """Writes scorecard .md files to results directory."""

    def __init__(self, results_dir: Optional[Path] = None):
        self._results_dir = results_dir or MODULE_ROOT / "results"

    def export(self, result: ScorecardResult) -> Path:
        """
        Export full scorecard analysis to dated scorecards folder.

        Returns path to the export folder.
        """
        date_str = datetime.now().strftime("%Y%m%d")
        export_dir = self._results_dir / date_str / "scorecards"
        export_dir.mkdir(parents=True, exist_ok=True)

        self._export_claude_md(export_dir, result)
        self._export_tier_ranking(export_dir, result)

        for tt_key, tt_result in result.trade_type_results.items():
            self._export_trade_type_scorecard(export_dir, tt_key, tt_result, result)

        self._export_rubric_summary(export_dir, result)
        self._export_prior_json(export_dir, result)

        return export_dir

    # ==================================================================
    # CLAUDE.md - Instructions for Claude Code
    # ==================================================================
    def _export_claude_md(self, export_dir: Path, result: ScorecardResult):
        content = """# Scorecard Analysis - Claude Code Instructions

## What These Files Are
Scorecards rank the top 5 indicators for each of 4 trade types based on
statistical edge (effect size + significance). They tell you which indicators
to check BEFORE taking a specific type of trade.

## File Index
- `tier_ranking.md` -- Full ranking of all 11 indicators across all 4 trade types
- `long_continuation.md` -- Scorecard for LONG + EPCH1/EPCH3 trades
- `short_continuation.md` -- Scorecard for SHORT + EPCH1/EPCH3 trades
- `long_rejection.md` -- Scorecard for LONG + EPCH2/EPCH4 trades
- `short_rejection.md` -- Scorecard for SHORT + EPCH2/EPCH4 trades
- `rubric_summary.md` -- Master overview with cross-type patterns

## How to Read a Scorecard
Each scorecard has:
1. **Trade Type Context** -- direction, models, sample size, baseline win rate
2. **Top 5 Indicators** -- ranked by tier (S/A/B/C), each with:
   - Binary signal: a YES/NO rule (e.g., "TAKE when h1_structure = BEAR")
   - Effect size: how many percentage points this signal adds/removes
   - Ramp-up pattern: what to watch in the 10 bars before entry
3. **Pre-Entry Checklist** -- the 5 signals as a decision tree

## Tier Definitions
| Tier | Effect Size | P-Value | Meaning |
|------|------------|---------|---------|
| S | >= 15pp | < 0.01 | Elite -- always check this indicator |
| A | >= 8pp | < 0.05 | Strong -- high-confidence filter |
| B | >= 4pp | < 0.05 | Moderate -- useful confirmation |
| C | >= 2pp | < 0.10 | Weak -- marginal edge, use as tiebreaker |
| Rejected | below thresholds | -- | Not actionable for this trade type |

## How to Interpret Effect Size
Effect size is the spread (in percentage points) between the best and worst
states/quintiles of an indicator. Example: if h1_structure BEAR = 68% WR
and BULL = 45% WR, effect size = 23pp.

## How to Interpret Ramp-Up Divergence
For continuous indicators, the ramp-up divergence shows how differently
winners and losers behave in the 10 minutes before entry. Positive means
winners have higher values. Larger magnitude = stronger pre-entry signal.

## Degradation Flags
Lines marked with [DEGRADED] indicate the indicator's edge has weakened
compared to the prior analysis run. Possible causes:
- Market regime change
- Sample size change
- Random variation

When you see degradation, DO NOT automatically remove the indicator.
Instead, flag it for the user to review.

## Workflow: Updating Scorecards
1. User runs: `python 04_indicators/runner.py --compare <prior_dir>`
2. Claude Code reads the new scorecards
3. If degradation flags exist, summarize them for the user
4. User decides whether to adjust trading rules
5. Claude Code NEVER changes scorecard files directly -- only the runner does

## The 5-Indicator Limit
Each scorecard includes exactly the top 5 (or fewer if insufficient data).
This is intentional -- a trader cannot realistically check more than 5
indicators in real-time. If an indicator is not in the top 5, it is either
redundant with a stronger indicator or not statistically significant for
that trade type.

## Trade Type Definitions
- **Long Continuation**: LONG direction + EPCH1 (Primary) or EPCH3 (Secondary)
- **Short Continuation**: SHORT direction + EPCH1 (Primary) or EPCH3 (Secondary)
- **Long Rejection**: LONG direction + EPCH2 (Primary) or EPCH4 (Secondary)
- **Short Rejection**: SHORT direction + EPCH2 (Primary) or EPCH4 (Secondary)

## Binary Signal Format
Signals use this pattern:
- `TAKE when <indicator> = <state>` -- favorable condition, look for this
- `SKIP when <indicator> = <state>` -- unfavorable condition, avoid this
- For continuous indicators, signals reference quintile ranges
- Ramp-up context describes what the indicator should be DOING (building,
  accelerating, compressing) not just its value at one point

## CRITICAL: Relative vs Absolute Benchmarks

### Indicators that are already relative (safe to compare across tickers):
- `candle_range_pct` -- ATR-normalized percentage ✅
- `sma_spread_pct` -- percentage spread between SMAs ✅
- `vol_roc` -- percentage rate of change ✅
- All categorical indicators (sma_config, m5_structure, etc.) ✅

### Indicators that are ABSOLUTE (ticker-dependent, NOT portable):
- `vol_delta_roll` -- raw volume delta in contracts/shares ❌
- `cvd_slope` -- raw CVD slope in absolute units ❌

**Rules for absolute indicators:**
1. The quintile ranges shown in scorecards (e.g., Q1 = -812,397 to -338,684)
   are fitted to the CURRENT dataset and ticker(s). They are NOT universal
   thresholds.
2. When evaluating a new trade, use the **quintile rank** (Q1/Q2/Q3/Q4/Q5)
   as the signal -- not the raw boundary values.
3. "Q1" means "bottom 20% of this indicator's own recent distribution."
   The actual numbers will differ across tickers due to liquidity differences.
4. To apply these signals to a different ticker, re-run the scorecard analysis
   on that ticker's data. Never carry raw vol_delta_roll or cvd_slope
   boundaries from one ticker to another.
5. When Claude Code references these indicators in trade evaluation, say
   "Volume Delta is in the lowest quintile of its recent range" -- NOT
   "Volume Delta is below -338,684."
"""
        (export_dir / "CLAUDE.md").write_text(content, encoding="utf-8")

    # ==================================================================
    # tier_ranking.md - Full indicator ranking table
    # ==================================================================
    def _export_tier_ranking(self, export_dir: Path, result: ScorecardResult):
        lines = [
            "# Indicator Tier Ranking - All Trade Types",
            "",
            f"**Generated:** {result.run_date}",
            f"**Total Trades:** {result.total_trades:,}",
        ]
        if result.date_from or result.date_to:
            lines.append(
                f"**Date Range:** {result.date_from or 'earliest'} to "
                f"{result.date_to or 'latest'}"
            )
        lines.append("")

        # Build the tier table
        lines.append("## Overall Tier Table")
        lines.append("")

        # Collect all indicator names (from first trade type that has scores)
        all_indicators = []
        for tt_result in result.trade_type_results.values():
            if tt_result.all_scores:
                all_indicators = [
                    (s.indicator_col, s.indicator_label, s.indicator_type)
                    for s in tt_result.all_scores
                ]
                break

        if all_indicators:
            header = "| Indicator | Type | " + " | ".join(
                TRADE_TYPES[k]["label"] for k in TRADE_TYPES
            ) + " |"
            separator = "|-----------|------|" + "|".join(
                "-----------" for _ in TRADE_TYPES
            ) + "|"
            lines.append(header)
            lines.append(separator)

            for col, label, ind_type in all_indicators:
                row = f"| {label} | {ind_type[:4]} |"
                for tt_key in TRADE_TYPES:
                    tt_result = result.trade_type_results.get(tt_key)
                    if tt_result:
                        score = next(
                            (s for s in tt_result.all_scores if s.indicator_col == col),
                            None,
                        )
                        if score and score.effect_size > 0:
                            cell = f" {score.tier} ({score.effect_size:.1f}pp)"
                            if score.confidence == "LOW_DATA":
                                cell += " *"
                            # Check degradation
                            degraded = any(
                                d.indicator_col == col and d.trade_type_key == tt_key
                                for d in result.degradation_flags
                            )
                            if degraded:
                                cell += " [DEGRADED]"
                            row += cell + " |"
                        else:
                            row += " - |"
                    else:
                        row += " - |"
                lines.append(row)

        lines.append("")
        lines.append("*\\* = LOW_DATA (insufficient sample size for full statistical validation)*")
        lines.append("")

        # Degradation flags section
        if result.degradation_flags:
            lines.append("## Degradation Flags")
            lines.append("")
            for flag in result.degradation_flags:
                lines.append(f"- [DEGRADED] {flag.message}")
            lines.append("")

        # Trade type summary
        lines.append("## Trade Type Summary")
        lines.append("")
        lines.append("| Trade Type | Trades | Win Rate | Avg R | Top Tier | Top Indicator |")
        lines.append("|------------|--------|----------|-------|----------|---------------|")
        for tt_key, tt_config in TRADE_TYPES.items():
            tt_result = result.trade_type_results.get(tt_key)
            if tt_result and tt_result.total_trades > 0:
                top = tt_result.top_scores[0] if tt_result.top_scores else None
                lines.append(
                    f"| {tt_config['label']} | {tt_result.total_trades} | "
                    f"{tt_result.win_rate:.1f}% | {tt_result.avg_r:.2f} | "
                    f"{top.tier if top else 'N/A'} | "
                    f"{top.indicator_label if top else 'N/A'} |"
                )
            else:
                lines.append(
                    f"| {tt_config['label']} | 0 | - | - | N/A | N/A |"
                )

        lines.append("")
        (export_dir / "tier_ranking.md").write_text("\n".join(lines), encoding="utf-8")

    # ==================================================================
    # Individual trade type scorecard
    # ==================================================================
    def _export_trade_type_scorecard(
        self,
        export_dir: Path,
        tt_key: str,
        tr: TradeTypeResult,
        result: ScorecardResult,
    ):
        """
        Write a single trade type scorecard. Always uses the same
        template structure regardless of sample size or tier results.
        """
        # Determine overall data confidence for this trade type
        low_data_scores = [s for s in tr.top_scores if s.confidence == "LOW_DATA"]
        has_low_data = len(low_data_scores) > 0
        data_note = ""
        if has_low_data:
            data_note = (
                f"\n> **LOW DATA WARNING:** This trade type has {tr.total_trades} trades. "
                f"Results are directional but not yet statistically validated. "
                f"Indicators marked [LOW_DATA] need more trades to confirm.\n"
            )

        lines = [
            f"# Scorecard: {tr.label}",
            "",
            f"**Direction:** {tr.direction} | **Models:** {', '.join(tr.models)}",
            f"**Trades:** {tr.total_trades:,} | **Win Rate:** {tr.win_rate:.1f}% | "
            f"**Avg R:** {tr.avg_r:.2f}",
            f"**Generated:** {result.run_date}",
        ]
        if data_note:
            lines.append(data_note)

        lines.extend(["", "---", ""])

        # Always show Top 5 Indicators section
        lines.append("## Top 5 Indicators")
        lines.append("")

        for i, score in enumerate(tr.top_scores, 1):
            degraded = any(
                d.indicator_col == score.indicator_col and d.trade_type_key == tt_key
                for d in result.degradation_flags
            )
            # Build tags
            tags = []
            if score.confidence == "LOW_DATA":
                tags.append("[LOW_DATA]")
            if degraded:
                tags.append("[DEGRADED]")
            tag_str = "  " + " ".join(tags) if tags else ""

            lines.append(
                f"### #{i}: {score.indicator_label} "
                f"(Tier {score.tier} -- {score.effect_size:.1f}pp effect){tag_str}"
            )

            lines.append(f"- **Confidence:** {score.confidence}")
            lines.append(f"- **Signal:** {score.binary_signal}")
            lines.append(f"- **Avoid:** {score.binary_avoid}")
            lines.append(
                f"- **Best state:** {score.best_state} = "
                f"{score.best_state_win_rate:.1f}% WR "
                f"({score.best_state_trades} trades)"
            )
            lines.append(
                f"- **Worst state:** {score.worst_state} = "
                f"{score.worst_state_win_rate:.1f}% WR "
                f"({score.worst_state_trades} trades)"
            )
            lines.append(f"- **P-value:** {score.p_value:.6f}")

            # Ramp-up pattern for continuous indicators
            if score.indicator_type == "continuous":
                if abs(score.ramp_divergence) > 0.0001:
                    div_sign = "higher" if score.ramp_divergence > 0 else "lower"
                    accel_desc = ""
                    if abs(score.ramp_acceleration) > 0.0001:
                        accel_dir = "accelerating" if score.ramp_acceleration > 0 else "decelerating"
                        accel_desc = f" {accel_dir} ({score.ramp_acceleration:+.6f}/bar)"
                    lines.append(
                        f"- **Ramp-up pattern:** Winners show {div_sign} values "
                        f"in last 10 bars. "
                        f"Divergence: {score.ramp_divergence:+.6f}.{accel_desc}"
                    )
                else:
                    lines.append("- **Ramp-up pattern:** No significant divergence detected.")
            else:
                lines.append("- **Ramp-up pattern:** N/A (categorical indicator)")

            lines.append("")

        # Pre-entry checklist (always present)
        lines.append("---")
        lines.append("")
        lines.append("## Pre-Entry Checklist")
        lines.append("")
        lines.append(f"Before entering a **{tr.label}** trade:")
        lines.append("")

        for i, score in enumerate(tr.top_scores, 1):
            degraded = any(
                d.indicator_col == score.indicator_col and d.trade_type_key == tt_key
                for d in result.degradation_flags
            )
            tags = []
            if score.confidence == "LOW_DATA":
                tags.append("[LOW_DATA]")
            if degraded:
                tags.append("[DEGRADED]")
            tag_str = " " + " ".join(tags) if tags else ""
            lines.append(
                f"{i}. [ ] {score.binary_signal}  "
                f"({score.tier}-tier, +{score.effect_size:.0f}pp){tag_str}"
            )

        lines.append("")
        n = len(tr.top_scores)
        high_conf = max(n - 1, 1)
        mod_conf = max(n - 2, 1)
        lines.append(f"**Minimum:** Pass {high_conf} of {n} for HIGH confidence")
        lines.append(f"**Acceptable:** Pass {mod_conf} of {n} for MODERATE confidence")

        if len(tr.top_scores) >= 2:
            lines.append(
                f"**Skip trade if:** Fail #{1} ({tr.top_scores[0].indicator_label}) "
                f"AND #{2} ({tr.top_scores[1].indicator_label})"
            )

        lines.append("")

        # Remaining indicators (not in top 5)
        remaining = [s for s in tr.all_scores if s not in tr.top_scores]
        if remaining:
            lines.append("## Remaining Indicators (Not in Top 5)")
            lines.append("")
            lines.append("| Indicator | Tier | Confidence | Effect | P-Value | Reason |")
            lines.append("|-----------|------|------------|--------|---------|--------|")
            for score in remaining:
                if score.p_value > 0.10:
                    reason = f"Not significant (p={score.p_value:.4f})"
                elif score.effect_size < 2.0:
                    reason = f"Weak effect ({score.effect_size:.1f}pp)"
                else:
                    reason = "Outside top 5 by ranking"
                lines.append(
                    f"| {score.indicator_label} | {score.tier} | "
                    f"{score.confidence} | {score.effect_size:.1f}pp | "
                    f"{score.p_value:.6f} | {reason} |"
                )
            lines.append("")

        (export_dir / f"{tt_key}.md").write_text("\n".join(lines), encoding="utf-8")

    # ==================================================================
    # rubric_summary.md - Cross-type patterns
    # ==================================================================
    def _export_rubric_summary(self, export_dir: Path, result: ScorecardResult):
        lines = [
            "# Scorecard Rubric Summary",
            "",
            f"**Generated:** {result.run_date}",
            f"**Total Trades:** {result.total_trades:,}",
            "",
        ]

        # Find universal indicators (appear in 3+ scorecards)
        indicator_appearances: Dict[str, List] = {}
        for tt_key, tt_result in result.trade_type_results.items():
            for score in tt_result.top_scores:
                if score.indicator_col not in indicator_appearances:
                    indicator_appearances[score.indicator_col] = []
                indicator_appearances[score.indicator_col].append({
                    "trade_type": tt_key,
                    "label": score.indicator_label,
                    "tier": score.tier,
                    "effect": score.effect_size,
                    "signal": score.binary_signal,
                })

        # Universal indicators (3+ appearances)
        universal = {
            col: entries for col, entries in indicator_appearances.items()
            if len(entries) >= 3
        }

        if universal:
            lines.append("## Universal Indicators (Top-5 in 3+ Trade Types)")
            lines.append("")
            lines.append("| Indicator | Appears In | Avg Effect | Common Signal |")
            lines.append("|-----------|-----------|------------|---------------|")
            for col, entries in sorted(
                universal.items(), key=lambda x: -len(x[1])
            ):
                count = len(entries)
                avg_effect = sum(e["effect"] for e in entries) / count
                label = entries[0]["label"]
                # Most common signal
                signals = [e["signal"] for e in entries]
                common_signal = max(set(signals), key=signals.count)
                lines.append(
                    f"| {label} | {count}/4 | {avg_effect:.1f}pp | {common_signal} |"
                )
            lines.append("")

        # Direction-specific patterns
        lines.append("## Direction-Specific Patterns")
        lines.append("")

        for direction in ["LONG", "SHORT"]:
            dir_types = [
                k for k, v in TRADE_TYPES.items() if v["direction"] == direction
            ]
            top_indicators = []
            for tt_key in dir_types:
                tt_result = result.trade_type_results.get(tt_key)
                if tt_result and tt_result.top_scores:
                    top = tt_result.top_scores[0]
                    top_indicators.append(
                        f"{TRADE_TYPES[tt_key]['label']}: "
                        f"{top.indicator_label} ({top.tier}, {top.effect_size:.1f}pp)"
                    )
            if top_indicators:
                lines.append(f"**{direction} trades:**")
                for ind in top_indicators:
                    lines.append(f"- {ind}")
                lines.append("")

        # Continuation vs Rejection patterns
        lines.append("## Continuation vs Rejection Patterns")
        lines.append("")

        for trade_style, style_types in [
            ("Continuation", ["long_continuation", "short_continuation"]),
            ("Rejection", ["long_rejection", "short_rejection"]),
        ]:
            style_indicators = []
            for tt_key in style_types:
                tt_result = result.trade_type_results.get(tt_key)
                if tt_result:
                    for score in tt_result.top_scores[:3]:  # top 3 per type
                        style_indicators.append(score.indicator_label)

            if style_indicators:
                # Count frequency
                from collections import Counter
                freq = Counter(style_indicators)
                top_3 = freq.most_common(3)
                lines.append(f"**{trade_style} trades favor:** " + ", ".join(
                    f"{name} ({count}x)" for name, count in top_3
                ))
                lines.append("")

        # Degradation summary
        if result.degradation_flags:
            lines.append("## Degradation Summary")
            lines.append("")
            lines.append(
                f"- {len(result.degradation_flags)} degradation flag(s) "
                "detected in this run"
            )
            tier_drops = [
                f for f in result.degradation_flags if f.flag_type == "tier_drop"
            ]
            if tier_drops:
                lines.append(f"- {len(tier_drops)} tier drop(s)")
            top5_demotions = [
                f for f in result.degradation_flags if f.flag_type == "top5_demotion"
            ]
            if top5_demotions:
                lines.append(f"- {len(top5_demotions)} top-5 demotion(s)")
            lines.append("")
        else:
            lines.append("## Degradation Summary")
            lines.append("")
            lines.append("No degradation comparison available (no prior run specified).")
            lines.append("")

        # Links
        lines.append("## Scorecard Links")
        lines.append("")
        for tt_key, tt_config in TRADE_TYPES.items():
            lines.append(f"- [{tt_config['label']}]({tt_key}.md)")
        lines.append(f"- [Full Tier Ranking](tier_ranking.md)")
        lines.append("")

        (export_dir / "rubric_summary.md").write_text("\n".join(lines), encoding="utf-8")

    # ==================================================================
    # _prior.json - Machine-readable for degradation tracking
    # ==================================================================
    def _export_prior_json(self, export_dir: Path, result: ScorecardResult):
        """Write _prior.json for next run's degradation comparison."""
        data = {
            "run_date": result.run_date,
            "date_from": result.date_from,
            "date_to": result.date_to,
            "total_trades": result.total_trades,
            "trade_types": {},
        }

        for tt_key, tt_result in result.trade_type_results.items():
            top5_cols = {s.indicator_col for s in tt_result.top_scores}
            indicators = {}
            for score in tt_result.all_scores:
                indicators[score.indicator_col] = {
                    "tier": score.tier,
                    "confidence": score.confidence,
                    "effect_size": score.effect_size,
                    "p_value": score.p_value,
                    "top5": score.indicator_col in top5_cols,
                }
            data["trade_types"][tt_key] = {
                "total_trades": tt_result.total_trades,
                "win_rate": tt_result.win_rate,
                "indicators": indicators,
            }

        (export_dir / "_prior.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8",
        )
