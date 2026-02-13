"""
Dual Pass Query Worker
Epoch Trading System v3.0 - XIII Trading LLC

QThread worker for executing DOW AI dual-pass queries:
- Pass 1: User's perspective/notes (replaces automated analysis)
- Pass 2: System analysis with backtested context

This allows the user to input their read of the market, then
have the system provide its recommendation based on learned edges.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, time as dt_time

from PyQt6.QtCore import QThread, pyqtSignal

# Add parent paths for imports
_dow_ai_dir = Path(__file__).parent.parent.parent.resolve()
if str(_dow_ai_dir) not in sys.path:
    sys.path.insert(0, str(_dow_ai_dir))

# Import v3.0 prompt components
from ai_context.prompt_v3 import (
    M1BarFull,
    PROMPT_VERSION,
    format_m1_bars_table,
    format_indicator_edges,
    format_zone_performance,
    estimate_tokens
)

from .context_loader import AIContextLoader

# Import Claude client
ClaudeClient = None

try:
    from analysis.claude_client import ClaudeClient
except ImportError as e:
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


# =============================================================================
# LIVE DUAL-PASS PROMPT TEMPLATE
# =============================================================================

LIVE_PASS2_TEMPLATE = """You are DOW, the AI trading analyst for the EPOCH system.

TRADER'S PERSPECTIVE (Pass 1):
================================================================================
{user_notes}
================================================================================

The trader above has shared their read of this {direction} setup.
Your job: Combine their observations with the backtested edges below to provide
a system recommendation.

CRITICAL CONTEXT:
- This trade is PRE-QUALIFIED by the EPOCH system
- System baseline: ~47% win rate on 1.5R trades = positive expectancy
- Backtested edges below show what IMPROVES our win rate further
- Default is TRADE. Only say NO_TRADE if indicators are CLEARLY unfavorable.

================================================================================
TRADE SETUP
================================================================================

Ticker: {ticker}
Direction: {direction}
Entry Price: ${entry_price:.2f}
Entry Time: {entry_time}

================================================================================
LIVE M1 PRICE ACTION - LAST {bar_count} BARS
================================================================================

{m1_bars_table}

================================================================================
BACKTESTED EDGES (from historical trades)
================================================================================

H1 STRUCTURE EDGE (+36pp when aligned - THIS IS THE STRONGEST EDGE):
{structure_edges}

SMA SPREAD EDGE:
{sma_edges}

CANDLE RANGE EDGE:
{candle_range_edges}

VOLUME DELTA EDGE:
{vol_delta_edges}

================================================================================
ZONE PERFORMANCE
================================================================================

{zone_performance}

================================================================================
DECISION RULES
================================================================================

CHECK THE STRONGEST EDGE FIRST: H1 Structure
- H1 ALIGNED with {direction} (BULL for LONG, BEAR for SHORT): Strong TRADE signal (+36pp edge)
- H1 NEUTRAL: Trade is acceptable (neutral edge)
- H1 OPPOSED (BEAR for LONG, BULL for SHORT): Caution - consider NO_TRADE only if MULTIPLE other factors also unfavorable

Compare the trader's perspective with the data:
- Do they see what the indicators show?
- Are they being too aggressive or too conservative?
- Does the backtested evidence support their read?

REMEMBER: We need ~33% win rate to break even on 1.5R. Our baseline is 47%.
Even a "mediocre" setup has positive expectancy. Only reject CLEARLY BAD setups.

================================================================================
YOUR RESPONSE
================================================================================

TRADER ASSESSMENT: [Brief comment on the trader's perspective - are they reading the setup correctly?]

INDICATORS (from last 5 bars):
- H1 Structure: [value] -> [ALIGNED/NEUTRAL/OPPOSED]
- {direction_score} Score: [value] -> [HIGH >=6 / MED 4-5 / LOW <4]
- Avg Range%: [value] -> [GOOD >=0.12% / LOW <0.12%]
- SMA Spread: [value] -> [ALIGNED/NEUTRAL/OPPOSED]

DECISION: [TRADE or NO_TRADE]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [2-3 sentences connecting the trader's perspective to backtested edges. If you agree with the trader, explain why. If you disagree, explain what they might be missing.]
"""


class DualPassQueryWorker(QThread):
    """
    Worker thread for executing dual-pass DOW AI queries.

    Pass 1: User enters their perspective/notes in the UI
    Pass 2: System runs analysis combining user notes + backtested context

    Signals:
        response_ready: Emitted when AI response is received
                       (ticker, direction, user_notes, response)
        error_occurred: Emitted when an error occurs (error_message)
        status_update: Emitted with progress messages during execution
    """

    response_ready = pyqtSignal(str, str, str, str)  # ticker, direction, user_notes, response
    error_occurred = pyqtSignal(str)  # error message
    status_update = pyqtSignal(str)  # progress message

    def __init__(
        self,
        ticker: str,
        direction: str,
        user_notes: str,
        bars_data: List[Dict],
        parent=None
    ):
        """
        Initialize the dual-pass query worker.

        Args:
            ticker: Stock symbol to analyze
            direction: Trade direction (LONG/SHORT)
            user_notes: User's perspective/notes (Pass 1 input)
            bars_data: Processed bar data from Entry Qualifier
            parent: Parent QObject
        """
        super().__init__(parent)
        self.ticker = ticker
        self.direction = direction
        self.user_notes = user_notes
        self.bars_data = bars_data

        # Components (initialized in run() for thread safety)
        self._context_loader = None
        self._claude_client = None

    def run(self):
        """
        Execute the dual-pass AI query workflow.

        1. Load cached AI context from JSON files
        2. Convert bar data to M1BarFull format
        3. Build Pass 2 prompt with user notes + backtested context
        4. Call Claude API
        5. Emit response or error
        """
        try:
            self.status_update.emit("Loading AI context...")

            # Initialize context loader
            self._context_loader = AIContextLoader()

            # Load cached context (fast - local JSON)
            ai_context = self._context_loader.load_all()

            # Check for context errors
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

            # Convert bars to M1BarFull format
            self.status_update.emit("Processing bar data...")
            m1_bars = self._convert_to_m1_bars(self.bars_data)

            # Build Pass 2 prompt
            self.status_update.emit("Building dual-pass prompt...")
            prompt = self._build_live_pass2_prompt(
                ticker=self.ticker,
                direction=self.direction,
                entry_price=current_price,
                user_notes=self.user_notes,
                m1_bars=m1_bars,
                ai_context=ai_context
            )

            # Log token estimate
            tokens = estimate_tokens(prompt)
            self.status_update.emit(f"Prompt: ~{tokens} tokens")

            # Call Claude API
            self.status_update.emit("Calling Claude API (Pass 2)...")
            response = self._query_claude(prompt)

            if response.startswith("Error"):
                self.error_occurred.emit(response)
            else:
                self.status_update.emit("Response received")
                self.response_ready.emit(
                    self.ticker,
                    self.direction,
                    self.user_notes,
                    response
                )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.error_occurred.emit(f"Query failed: {str(e)}\n\nDetails:\n{error_details}")

    def _convert_to_m1_bars(self, bars_data: List[Dict]) -> List[M1BarFull]:
        """
        Convert Entry Qualifier bar data to M1BarFull format.

        Args:
            bars_data: List of processed bar dicts from Entry Qualifier

        Returns:
            List of M1BarFull objects
        """
        m1_bars = []

        for i, bar in enumerate(bars_data):
            # Calculate bar index relative to entry (last bar is -1)
            bar_index = i - len(bars_data)

            # Parse time
            bar_time = bar.get('timestamp')
            if isinstance(bar_time, str):
                try:
                    bar_time = datetime.fromisoformat(bar_time.replace('Z', '+00:00')).time()
                except Exception:
                    bar_time = dt_time(0, 0)
            elif isinstance(bar_time, datetime):
                bar_time = bar_time.time()
            elif not isinstance(bar_time, dt_time):
                bar_time = dt_time(0, 0)

            m1_bar = M1BarFull(
                bar_index=bar_index,
                bar_time=bar_time,
                open=bar.get('open', 0),
                high=bar.get('high', 0),
                low=bar.get('low', 0),
                close=bar.get('close', 0),
                volume=int(bar.get('volume', 0)),
                vol_delta=bar.get('roll_delta', 0),
                vol_roc=bar.get('volume_roc', 0),
                cvd_slope=bar.get('cvd_slope', 0),
                candle_range_pct=bar.get('candle_range_pct', 0),
                vwap=bar.get('vwap', 0),
                sma9=bar.get('sma9', 0),
                sma21=bar.get('sma21', 0),
                sma_spread=bar.get('sma_spread', 0),
                sma_momentum_label=bar.get('sma_momentum', 'N/A'),
                h1_structure=bar.get('h1_display', 'N/A'),
                m15_structure=bar.get('m15_display', 'N/A'),
                m5_structure=bar.get('m5_display', 'N/A'),
                m1_structure=bar.get('m1_structure', 'N/A'),
                long_score=0,
                short_score=0
            )
            m1_bars.append(m1_bar)

        return m1_bars

    def _build_live_pass2_prompt(
        self,
        ticker: str,
        direction: str,
        entry_price: float,
        user_notes: str,
        m1_bars: List[M1BarFull],
        ai_context: Dict[str, Any]
    ) -> str:
        """
        Build the live Pass 2 prompt with user notes and backtested context.

        Args:
            ticker: Stock symbol
            direction: LONG or SHORT
            entry_price: Current price
            user_notes: User's perspective (Pass 1)
            m1_bars: M1 bar data
            ai_context: Loaded AI context

        Returns:
            Formatted prompt string
        """
        # Get context data
        indicator_edges = ai_context.get('indicator_edges', {})
        zone_performance = ai_context.get('zone_performance', {})

        # Format edges
        formatted_edges = format_indicator_edges(indicator_edges, direction)

        # Format zone performance
        formatted_zones = format_zone_performance(zone_performance, direction)

        # Format M1 bars table
        m1_table = format_m1_bars_table(m1_bars)

        # Direction-specific parameters
        direction_score = "Long" if direction == "LONG" else "Short"

        # Current time
        entry_time = datetime.now().strftime("%H:%M:%S ET")

        return LIVE_PASS2_TEMPLATE.format(
            ticker=ticker,
            direction=direction,
            entry_price=entry_price,
            entry_time=entry_time,
            user_notes=user_notes if user_notes.strip() else "(No notes provided - trader did not share their perspective)",
            bar_count=len(m1_bars),
            m1_bars_table=m1_table,
            structure_edges=formatted_edges.get('structure', '  - No data'),
            sma_edges=formatted_edges.get('sma', '  - No data'),
            candle_range_edges=formatted_edges.get('candle_range', '  - No data'),
            vol_delta_edges=formatted_edges.get('vol_delta', '  - No data'),
            zone_performance=formatted_zones,
            direction_score=direction_score
        )

    def _query_claude(self, prompt: str) -> str:
        """
        Send prompt to Claude API and get response.

        Args:
            prompt: The formatted prompt string

        Returns:
            Claude's response text or error message
        """
        if ClaudeClient is None:
            claude_path = _dow_ai_dir / "analysis" / "claude_client.py"
            error_msg = "Error: Claude client not available\n\n"
            error_msg += "Diagnostics:\n"
            error_msg += f"  - DOW AI dir: {_dow_ai_dir}\n"
            error_msg += f"  - Claude client path: {claude_path}\n"
            error_msg += f"  - Path exists: {claude_path.exists()}\n"
            return error_msg

        try:
            self.status_update.emit("Initializing Claude client...")
            self._claude_client = ClaudeClient()

            if self._claude_client.client is None:
                return "Error: Claude client initialized but API connection failed\n\nCheck ANTHROPIC_API_KEY in config.py"

            self.status_update.emit("Sending request to Claude...")
            # Use appropriate max_tokens for dual-pass response
            response = self._claude_client.analyze(prompt, max_tokens=600)

            if response is None:
                return "Error: Claude returned empty response"

            return response

        except Exception as e:
            import traceback
            return f"Error calling Claude API: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
