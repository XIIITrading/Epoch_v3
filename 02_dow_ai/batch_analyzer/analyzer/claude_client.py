"""
Claude Batch Client
Handles Claude API calls with rate limiting for batch processing.
"""

import time
import anthropic
from typing import Optional, Tuple
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    REQUESTS_PER_MINUTE,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    MAX_OUTPUT_TOKENS
)
from models.trade_context import TradeContext
from models.prediction import AIPrediction
from prompts.batch_prompt import BatchPromptBuilder
from analyzer.response_parser import ResponseParser


class ClaudeBatchClient:
    """
    Claude API client with rate limiting for batch processing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = CLAUDE_MODEL,
        requests_per_minute: int = REQUESTS_PER_MINUTE
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to config)
            model: Claude model to use
            requests_per_minute: Rate limit
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model
        self.requests_per_minute = requests_per_minute

        # Initialize client
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Rate limiting
        self._request_times = []
        self._min_interval = 60.0 / requests_per_minute

        # Helpers
        self.prompt_builder = BatchPromptBuilder()
        self.response_parser = ResponseParser()

        # Stats
        self.total_requests = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_errors = 0

    def analyze_trade(self, trade: TradeContext) -> AIPrediction:
        """
        Analyze a single trade and return prediction.

        Args:
            trade: TradeContext with all indicators

        Returns:
            AIPrediction object
        """
        # Rate limiting
        self._wait_for_rate_limit()

        # Build prompt
        prompt = self.prompt_builder.build_prompt(trade)

        # Track timing
        start_time = time.time()

        # Make API call with retries
        response_text = None
        tokens_input = 0
        tokens_output = 0

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = response.content[0].text
                tokens_input = response.usage.input_tokens
                tokens_output = response.usage.output_tokens

                # Update stats
                self.total_requests += 1
                self.total_tokens_input += tokens_input
                self.total_tokens_output += tokens_output

                break

            except anthropic.RateLimitError:
                print(f"  Rate limited, waiting {RETRY_DELAY_SECONDS * (attempt + 1)}s...")
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))

            except anthropic.APIError as e:
                print(f"  API error: {e}")
                self.total_errors += 1
                if attempt == MAX_RETRIES - 1:
                    # Use rule-based fallback
                    return self.response_parser.create_rule_based_prediction(trade)
                time.sleep(RETRY_DELAY_SECONDS)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Parse response
        if response_text:
            prediction = self.response_parser.parse_response(
                response_text=response_text,
                trade=trade,
                model_used=self.model,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                processing_time_ms=processing_time_ms
            )
        else:
            prediction = self.response_parser.create_rule_based_prediction(trade)

        return prediction

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        now = time.time()

        # Remove old request times (older than 60 seconds)
        self._request_times = [t for t in self._request_times if now - t < 60]

        # If at limit, wait
        if len(self._request_times) >= self.requests_per_minute:
            oldest = self._request_times[0]
            wait_time = 60 - (now - oldest) + 0.1  # Small buffer
            if wait_time > 0:
                print(f"  Rate limit reached, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

        # Also ensure minimum interval between requests
        if self._request_times:
            last_request = self._request_times[-1]
            elapsed = now - last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)

        # Record this request time
        self._request_times.append(time.time())

    def get_stats(self) -> dict:
        """Get client statistics."""
        return {
            'total_requests': self.total_requests,
            'total_tokens_input': self.total_tokens_input,
            'total_tokens_output': self.total_tokens_output,
            'total_errors': self.total_errors,
            'model': self.model,
        }

    def estimate_cost(self) -> dict:
        """Estimate cost based on tokens used."""
        # Pricing as of Jan 2026 (per 1M tokens)
        pricing = {
            'claude-sonnet-4-20250514': {'input': 3.0, 'output': 15.0},
            'claude-opus-4-5-20251101': {'input': 15.0, 'output': 75.0},
            'claude-3-5-haiku-20241022': {'input': 0.25, 'output': 1.25},
        }

        model_pricing = pricing.get(self.model, pricing['claude-sonnet-4-20250514'])

        input_cost = (self.total_tokens_input / 1_000_000) * model_pricing['input']
        output_cost = (self.total_tokens_output / 1_000_000) * model_pricing['output']

        return {
            'input_tokens': self.total_tokens_input,
            'output_tokens': self.total_tokens_output,
            'input_cost': round(input_cost, 4),
            'output_cost': round(output_cost, 4),
            'total_cost': round(input_cost + output_cost, 4),
        }
