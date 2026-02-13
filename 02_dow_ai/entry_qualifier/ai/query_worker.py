"""
AI Query Worker
Epoch Trading System v1 - XIII Trading LLC

QThread worker for executing DOW AI queries without blocking the UI.
Combines live data, cached context, and zone data into a prompt for Claude.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

# Add parent paths for imports
# entry_qualifier/ai/query_worker.py -> 04_dow_ai
_dow_ai_dir = Path(__file__).parent.parent.parent.resolve()
if str(_dow_ai_dir) not in sys.path:
    sys.path.insert(0, str(_dow_ai_dir))

from .context_loader import AIContextLoader
from .compact_prompt import build_compact_prompt

# Import Claude client from 04_dow_ai/analysis/
ClaudeClient = None
SupabaseReader = None

try:
    from analysis.claude_client import ClaudeClient
except ImportError as e:
    # Try alternative import path
    try:
        import importlib.util
        claude_path = _dow_ai_dir / "analysis" / "claude_client.py"
        if claude_path.exists():
            spec = importlib.util.spec_from_file_location("claude_client", claude_path)
            claude_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(claude_module)
            ClaudeClient = claude_module.ClaudeClient
    except Exception as e2:
        print(f"Warning: Could not import ClaudeClient: {e} / {e2}")

try:
    from data.supabase_reader import SupabaseReader
except ImportError as e:
    # Try alternative import path
    try:
        import importlib.util
        reader_path = _dow_ai_dir / "data" / "supabase_reader.py"
        if reader_path.exists():
            spec = importlib.util.spec_from_file_location("supabase_reader", reader_path)
            reader_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(reader_module)
            SupabaseReader = reader_module.SupabaseReader
    except Exception as e2:
        print(f"Warning: Could not import SupabaseReader: {e} / {e2}")


class AIQueryWorker(QThread):
    """
    Worker thread for executing DOW AI queries.

    Loads context, builds prompt, calls Claude API, and emits response.
    Runs in a separate thread to prevent UI blocking.

    Signals:
        response_ready: Emitted when AI response is received
                       (ticker, direction, response)
        error_occurred: Emitted when an error occurs (error_message)
        status_update: Emitted with progress messages during execution
    """

    response_ready = pyqtSignal(str, str, str)  # ticker, direction, response
    error_occurred = pyqtSignal(str)  # error message
    status_update = pyqtSignal(str)  # progress message

    def __init__(
        self,
        ticker: str,
        direction: str,
        bars_data: List[Dict],
        parent=None
    ):
        """
        Initialize the query worker.

        Args:
            ticker: Stock symbol to analyze
            direction: Trade direction (LONG/SHORT)
            bars_data: Processed bar data from Entry Qualifier
            parent: Parent QObject
        """
        super().__init__(parent)
        self.ticker = ticker
        self.direction = direction
        self.bars_data = bars_data

        # Initialize components (will be created in run() to ensure thread safety)
        self._context_loader = None
        self._claude_client = None
        self._supabase_reader = None

    def run(self):
        """
        Execute the AI query workflow.

        1. Load cached AI context from JSON files
        2. Fetch zone data from Supabase (optional)
        3. Build compact prompt
        4. Call Claude API
        5. Emit response or error
        """
        try:
            self.status_update.emit("Loading AI context...")

            # Initialize components in worker thread
            self._context_loader = AIContextLoader()

            # Load cached context (fast - local JSON)
            ai_context = self._context_loader.load_all()

            # Check if context has errors and report them
            context_warnings = []
            for key, value in ai_context.items():
                if isinstance(value, dict) and '_error' in value:
                    context_warnings.append(f"{key}: {value['_error']}")

            if context_warnings:
                self.status_update.emit(f"Context warnings: {'; '.join(context_warnings)}")

            # Get current price from bars
            current_price = 0.0
            if self.bars_data:
                current_price = self.bars_data[-1].get('close', 0)
                self.status_update.emit(f"Current price: ${current_price:.2f}")
            else:
                self.status_update.emit("Warning: No bar data available")

            # Try to fetch zone data from Supabase
            self.status_update.emit("Fetching zone data...")
            zone_data = self._fetch_zone_data()
            if zone_data:
                self.status_update.emit(f"Zone loaded: {zone_data.get('zone_id', 'unknown')}")
            else:
                self.status_update.emit("Zone data not available (optional)")

            # Build compact prompt
            self.status_update.emit("Building prompt...")
            prompt = build_compact_prompt(
                ticker=self.ticker,
                direction=self.direction,
                current_price=current_price,
                bars_data=self.bars_data,
                ai_context=ai_context,
                zone_data=zone_data
            )

            # Call Claude API
            self.status_update.emit("Calling Claude API...")
            response = self._query_claude(prompt)

            if response.startswith("Error"):
                self.error_occurred.emit(response)
            else:
                self.status_update.emit("Response received")
                self.response_ready.emit(
                    self.ticker,
                    self.direction,
                    response
                )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.error_occurred.emit(f"Query failed: {str(e)}\n\nDetails:\n{error_details}")

        finally:
            # Cleanup
            if self._supabase_reader:
                try:
                    self._supabase_reader.close()
                except:
                    pass

    def _fetch_zone_data(self) -> Optional[Dict]:
        """
        Fetch zone data from Supabase for the current ticker.

        Returns:
            Zone data dict or None if unavailable
        """
        if SupabaseReader is None:
            return None

        try:
            self._supabase_reader = SupabaseReader()
            if not self._supabase_reader.connect():
                return None

            # Get zone data for ticker (simplified - no model dependency)
            zone_data = self._supabase_reader.get_zone_for_ticker(self.ticker)
            return zone_data

        except Exception as e:
            # Zone data is optional - don't fail query
            return None

    def _query_claude(self, prompt: str) -> str:
        """
        Send prompt to Claude API and get response.

        Args:
            prompt: The formatted prompt string

        Returns:
            Claude's response text or error message
        """
        if ClaudeClient is None:
            # Provide detailed diagnostics
            claude_path = _dow_ai_dir / "analysis" / "claude_client.py"
            error_msg = "Error: Claude client not available\n\n"
            error_msg += "Diagnostics:\n"
            error_msg += f"  - DOW AI dir: {_dow_ai_dir}\n"
            error_msg += f"  - Claude client path: {claude_path}\n"
            error_msg += f"  - Path exists: {claude_path.exists()}\n"
            error_msg += f"  - sys.path[0]: {sys.path[0] if sys.path else 'empty'}\n"
            return error_msg

        try:
            self.status_update.emit("Initializing Claude client...")
            self._claude_client = ClaudeClient()

            if self._claude_client.client is None:
                return "Error: Claude client initialized but API connection failed\n\nCheck ANTHROPIC_API_KEY in config.py"

            self.status_update.emit("Sending request to Claude...")
            # Use reduced max_tokens for compact responses
            response = self._claude_client.analyze(prompt, max_tokens=400)

            if response is None:
                return "Error: Claude returned empty response"

            return response

        except Exception as e:
            import traceback
            return f"Error calling Claude API: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


class MockAIQueryWorker(QThread):
    """
    Mock worker for testing UI without actual API calls.
    """

    response_ready = pyqtSignal(str, str, str)  # ticker, direction, response
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        ticker: str,
        direction: str,
        bars_data: List[Dict],
        parent=None
    ):
        super().__init__(parent)
        self.ticker = ticker
        self.direction = direction
        self.bars_data = bars_data

    def run(self):
        """Generate mock response after short delay."""
        import time
        time.sleep(1.5)  # Simulate API latency

        # Generate mock response
        mock_response = f"""TRADE | Confidence: MEDIUM

INDICATORS:
- Candle %: 0.18% (GOOD)
- Vol Delta: +45k (FAVORABLE)
- Vol ROC: +65% (ELEVATED)
- SMA: BULL
- H1 Struct: NEUT

SNAPSHOT: {self.ticker} shows solid {self.direction} setup. Range exceeds threshold, volume confirms direction. H1 neutral allows entry flexibility. Enter on break with stop below zone."""

        self.response_ready.emit(
            self.ticker,
            self.direction,
            mock_response
        )
