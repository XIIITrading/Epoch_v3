"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 10: MACHINE LEARNING
Prompt Template Builders
XIII Trading LLC
================================================================================

Python functions that build context-rich prompts for Claude analysis sessions.
These inject live data into prompt templates for more targeted analysis.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add parent to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CANONICAL_OUTCOME, VALIDATED_EDGES, EDGE_CRITERIA,
    DAILY_EXPORTS_DIR, WEEKLY_EXPORTS_DIR, STATE_DIR,
    PROMPTS_DIR
)


def build_edge_audit_prompt(date: datetime = None) -> str:
    """
    Build a complete edge audit prompt with embedded data.

    Loads the edge_audit.md template and appends the latest daily exports
    so the entire prompt can be pasted into a Claude session.
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y%m%d")

    # Load template
    template_path = PROMPTS_DIR / "edge_audit.md"
    template = template_path.read_text() if template_path.exists() else "# Edge Audit\n\n"

    # Load daily exports
    trades_path = DAILY_EXPORTS_DIR / f"trades_{date_str}.json"
    edge_path = DAILY_EXPORTS_DIR / f"edge_analysis_{date_str}.md"
    metrics_path = DAILY_EXPORTS_DIR / f"system_metrics_{date_str}.json"

    prompt = template + "\n\n---\n\n# Attached Data\n\n"

    if trades_path.exists():
        trades_data = json.loads(trades_path.read_text())
        # Include summary and model breakdown (not full trade list for token efficiency)
        summary_data = {
            "summary": trades_data.get("summary", {}),
            "model_breakdown": trades_data.get("model_breakdown", {}),
            "direction_breakdown": trades_data.get("direction_breakdown", {}),
            "trade_count": len(trades_data.get("trades", [])),
        }
        prompt += f"## Trade Summary ({date_str})\n\n```json\n{json.dumps(summary_data, indent=2)}\n```\n\n"
    else:
        prompt += f"## Trade Summary\n\n*No export found for {date_str}*\n\n"

    if edge_path.exists():
        prompt += f"## Edge Analysis\n\n{edge_path.read_text()}\n\n"

    if metrics_path.exists():
        prompt += f"## System Metrics\n\n```json\n{metrics_path.read_text()}\n```\n\n"

    return prompt


def build_hypothesis_prompt(
    observation: str,
    indicator: str,
    proposed_condition: str,
    date: datetime = None
) -> str:
    """
    Build a hypothesis testing prompt with context.

    Args:
        observation: What pattern was observed
        indicator: Which indicator to test
        proposed_condition: The condition to evaluate
        date: Date for loading current data
    """
    if date is None:
        date = datetime.now()

    # Load hypothesis generator template
    template_path = PROMPTS_DIR / "hypothesis_generator.md"
    template = template_path.read_text() if template_path.exists() else ""

    prompt = template + f"""

---

# Specific Hypothesis to Evaluate

## Observation
{observation}

## Proposed Hypothesis
- **Indicator**: `{indicator}`
- **Condition**: {proposed_condition}
- **Expected Effect**: To be determined from analysis

## Current Validated Edges (for comparison)
"""

    for edge in VALIDATED_EDGES:
        prompt += f"- {edge['name']}: {edge['effect_size_pp']:+.1f}pp ({edge['confidence']})\n"

    prompt += f"""

## Statistical Requirements
- p-value < {EDGE_CRITERIA['p_value_threshold']}
- Effect size > {EDGE_CRITERIA['effect_size_threshold']}pp
- Minimum sample: {EDGE_CRITERIA['min_sample_medium']} trades (MEDIUM) / {EDGE_CRITERIA['min_sample_high']} trades (HIGH)

## Questions
1. Is this hypothesis independent from existing validated edges?
2. What SQL query would test this?
3. What sample size do we need?
4. What are the risks of a false positive?
"""

    return prompt


def build_pattern_mining_prompt(
    trades_data: Dict[str, Any],
    focus_area: str = "general"
) -> str:
    """
    Build a pattern mining prompt with embedded trade data.

    Args:
        trades_data: Trade export data (from export_for_claude.py)
        focus_area: Focus area - 'general', 'winners', 'losers', 'model', 'time'
    """
    template_path = PROMPTS_DIR / "trade_pattern_mining.md"
    template = template_path.read_text() if template_path.exists() else ""

    focus_instructions = {
        "general": "Perform a broad pattern analysis across all dimensions.",
        "winners": "Focus specifically on what winning trades have in common.",
        "losers": "Focus specifically on what losing trades share - looking for avoidable patterns.",
        "model": "Focus on model-specific patterns (EPCH1-4 differences).",
        "time": "Focus on time-based patterns (time of day, day of week).",
    }

    prompt = template + f"""

---

# Analysis Focus: {focus_area.upper()}

{focus_instructions.get(focus_area, focus_instructions['general'])}

# Trade Data

```json
{json.dumps(trades_data, indent=2, default=str)}
```
"""

    return prompt


def build_session_context() -> str:
    """
    Build the standard session context to load at the start of any Claude session.

    Combines CLAUDE.md + current system state + latest metrics.
    """
    parts = []

    # CLAUDE.md
    claude_md = Path(__file__).parent.parent / "CLAUDE.md"
    if claude_md.exists():
        parts.append(claude_md.read_text())

    # System state
    state_path = STATE_DIR / "system_state.md"
    if state_path.exists():
        parts.append("\n\n---\n\n# Current System State\n\n" + state_path.read_text())

    # Latest metrics (find most recent)
    metrics_files = sorted(DAILY_EXPORTS_DIR.glob("system_metrics_*.json"), reverse=True)
    if metrics_files:
        latest_metrics = json.loads(metrics_files[0].read_text())
        parts.append(
            "\n\n---\n\n# Latest Metrics\n\n```json\n"
            + json.dumps(latest_metrics, indent=2)
            + "\n```"
        )

    return "\n".join(parts)
