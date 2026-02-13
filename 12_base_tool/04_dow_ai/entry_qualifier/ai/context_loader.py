"""
AI Context Loader
Epoch Trading System v1 - XIII Trading LLC

Loads cached AI context data from local JSON files.
Fast local read for real-time trading queries.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class AIContextLoader:
    """
    Loads AI context data from local JSON files.

    Context files are generated weekly by the refresh_ai_context.py workflow
    and stored in the ai_context/ directory.

    Files:
        - model_stats.json: EPCH model performance by direction
        - indicator_edges.json: Validated indicator edge conditions
        - zone_performance.json: Win rates by zone type and score
    """

    # Default context directory (relative to this file)
    DEFAULT_CONTEXT_DIR = Path(__file__).parent.parent.parent / "ai_context"

    def __init__(self, context_dir: Path = None):
        """
        Initialize the context loader.

        Args:
            context_dir: Path to ai_context directory (uses default if not provided)
        """
        self.context_dir = context_dir or self.DEFAULT_CONTEXT_DIR
        self._cache = {}
        self._cache_time = None

    def load_model_stats(self, force_reload: bool = False) -> Dict:
        """
        Load model statistics from model_stats.json.

        Returns:
            Dict with structure:
            {
                "generated_at": "2026-01-22T10:00:00",
                "date_range": {"from": "...", "to": "..."},
                "models": {
                    "EPCH1": {
                        "LONG": {"trades": N, "win_rate": X, ...},
                        "SHORT": {...}
                    },
                    ...
                }
            }
        """
        return self._load_json_file("model_stats.json", force_reload)

    def load_indicator_edges(self, force_reload: bool = False) -> Dict:
        """
        Load indicator edges from indicator_edges.json.

        Returns:
            Dict with structure:
            {
                "generated_at": "2026-01-22T10:00:00",
                "edges": {
                    "candle_range": {
                        "favorable": [...],
                        "unfavorable": [...],
                        "best_for": "ALL"
                    },
                    ...
                }
            }
        """
        return self._load_json_file("indicator_edges.json", force_reload)

    def load_zone_performance(self, force_reload: bool = False) -> Dict:
        """
        Load zone performance from zone_performance.json.

        Returns:
            Dict with structure:
            {
                "generated_at": "2026-01-22T10:00:00",
                "primary": {
                    "LONG": {"high": X, "mid": Y, "low": Z},
                    "SHORT": {...}
                },
                "secondary": {...}
            }
        """
        return self._load_json_file("zone_performance.json", force_reload)

    def load_all(self, force_reload: bool = False) -> Dict:
        """
        Load all context files into a single dict.

        Returns:
            Dict with keys: model_stats, indicator_edges, zone_performance
        """
        return {
            "model_stats": self.load_model_stats(force_reload),
            "indicator_edges": self.load_indicator_edges(force_reload),
            "zone_performance": self.load_zone_performance(force_reload)
        }

    def _load_json_file(self, filename: str, force_reload: bool = False) -> Dict:
        """
        Load a JSON file from the context directory.

        Uses simple caching - reloads if force_reload or if not cached.
        """
        cache_key = filename

        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]

        filepath = self.context_dir / filename

        if not filepath.exists():
            # Return empty dict with warning info
            return {
                "_error": f"File not found: {filepath}",
                "_hint": "Run 'python scripts/refresh_ai_context.py' to generate context files"
            }

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._cache[cache_key] = data
            return data
        except json.JSONDecodeError as e:
            return {
                "_error": f"Invalid JSON in {filename}: {e}",
                "_hint": "Check file format or regenerate with refresh_ai_context.py"
            }
        except Exception as e:
            return {
                "_error": f"Error loading {filename}: {e}"
            }

    def get_model_stats_for_query(self, model: str, direction: str) -> Dict:
        """
        Get model statistics for a specific model/direction combination.

        Args:
            model: EPCH1, EPCH2, EPCH3, or EPCH4
            direction: LONG or SHORT

        Returns:
            Dict with trades, win_rate, avg_mfe_r, avg_mae_r, etc.
            or empty dict if not found
        """
        stats = self.load_model_stats()
        models = stats.get("models", {})
        model_data = models.get(model, {})
        return model_data.get(direction, {})

    def get_relevant_edges(self, direction: str, limit: int = 5) -> str:
        """
        Get relevant indicator edges formatted for prompt inclusion.

        Args:
            direction: LONG or SHORT
            limit: Maximum number of edges to include

        Returns:
            Formatted string of edge conditions
        """
        edges_data = self.load_indicator_edges()
        edges = edges_data.get("edges", {})

        lines = []
        count = 0

        for indicator, edge_info in edges.items():
            if count >= limit:
                break

            favorable = edge_info.get("favorable", [])
            best_for = edge_info.get("best_for", "ALL")

            # Include if edge applies to this direction or ALL
            if best_for in [direction, "ALL"]:
                for condition in favorable[:1]:  # Just top condition per indicator
                    lines.append(f"- {indicator}: {condition}")
                    count += 1

        if not lines:
            return "- No validated edges for current context"

        return "\n".join(lines)

    def get_zone_win_rate(self, zone_type: str, direction: str, score_bucket: str) -> float:
        """
        Get historical win rate for a zone type/direction/score combination.

        Args:
            zone_type: "primary" or "secondary"
            direction: LONG or SHORT
            score_bucket: "low", "mid", or "high"

        Returns:
            Win rate as percentage, or 0 if not found
        """
        zone_data = self.load_zone_performance()
        type_data = zone_data.get(zone_type, {})
        dir_data = type_data.get(direction, {})
        return dir_data.get(score_bucket, 0)

    def get_context_age_hours(self) -> Optional[float]:
        """
        Get the age of the context data in hours.

        Returns:
            Hours since context was generated, or None if unavailable
        """
        stats = self.load_model_stats()
        generated_at = stats.get("generated_at")

        if not generated_at:
            return None

        try:
            gen_time = datetime.fromisoformat(generated_at)
            age = datetime.now() - gen_time
            return age.total_seconds() / 3600
        except:
            return None

    def is_context_stale(self, max_age_hours: float = 168) -> bool:
        """
        Check if context data is older than threshold.

        Args:
            max_age_hours: Maximum acceptable age in hours (default 168 = 1 week)

        Returns:
            True if context is stale or unavailable
        """
        age = self.get_context_age_hours()
        if age is None:
            return True
        return age > max_age_hours

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self._cache_time = None
