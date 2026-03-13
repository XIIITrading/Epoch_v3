"""
Shared fixtures and helpers for the System Analysis Test Suite.
"""
import sys
import json
import os
from pathlib import Path
from datetime import date
from typing import Any, Dict, List, Optional

import pytest
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Path setup - ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # Epoch_v3/
SHARED_ROOT = PROJECT_ROOT / "00_shared"

# Add paths so we can import shared.*, 01_application.*, 03_backtest.*
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

# Results directory
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Result writer fixture
# ---------------------------------------------------------------------------
class ResultWriter:
    """Writes JSON result files matching the Notion spec."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir

    def write_validation(
        self,
        test_id: str,
        question: str,
        checks: List[Dict[str, Any]],
    ) -> Dict:
        """Write a Part 1 (pass/fail validation) result."""
        all_passed = all(c["passed"] for c in checks)
        passed_count = sum(1 for c in checks if c["passed"])
        total = len(checks)

        result = {
            "test_id": test_id,
            "question": question,
            "answer": f"{'Yes' if all_passed else 'No'} - {passed_count}/{total} checks passed",
            "passed": all_passed,
            "checks": checks,
        }

        path = self.results_dir / f"{test_id}.json"
        path.write_text(json.dumps(result, indent=2, default=str))
        return result

    def write_analysis(
        self,
        test_id: str,
        question: str,
        answer: str,
        sample_size: int,
        metrics: Dict[str, Any],
    ) -> Dict:
        """Write a Part 2 (statistical analysis) result."""
        result = {
            "test_id": test_id,
            "question": question,
            "answer": answer,
            "sample_size": sample_size,
            "metrics": metrics,
        }

        path = self.results_dir / f"{test_id}.json"
        path.write_text(json.dumps(result, indent=2, default=str))
        return result


@pytest.fixture(scope="session")
def result_writer():
    """Provide a ResultWriter instance for the entire test session."""
    return ResultWriter(RESULTS_DIR)


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------
def make_ohlcv_df(
    n: int = 50,
    start_price: float = 100.0,
    volatility: float = 0.5,
    base_volume: int = 10000,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a realistic synthetic OHLCV DataFrame."""
    rng = np.random.RandomState(seed)
    closes = [start_price]
    for _ in range(n - 1):
        change = rng.normal(0, volatility)
        closes.append(closes[-1] + change)

    closes = np.array(closes)
    highs = closes + rng.uniform(0.1, 1.0, n)
    lows = closes - rng.uniform(0.1, 1.0, n)
    opens = lows + rng.uniform(0, 1, n) * (highs - lows)
    volumes = rng.randint(base_volume // 2, base_volume * 2, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def make_check(name: str, expected: Any, actual: Any, tol: float = 1e-6) -> Dict:
    """Create a check dict for ResultWriter. Supports numeric tolerance."""
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        passed = abs(expected - actual) < tol
    else:
        passed = expected == actual
    return {
        "name": name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
    }
