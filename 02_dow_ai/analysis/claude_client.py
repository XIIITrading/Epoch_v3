"""
DOW AI - Claude API Client
Epoch Trading System v2.0 - XIII Trading LLC

Wrapper for Anthropic API interactions.
"""
import anthropic
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, VERBOSE, debug_print


class ClaudeClient:
    """
    Client for Claude API interactions.

    Handles sending prompts to Claude and receiving analysis responses.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        verbose: bool = None
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (uses config if not provided)
            model: Claude model ID (uses config if not provided)
            verbose: Enable verbose output
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or CLAUDE_MODEL
        self.verbose = verbose if verbose is not None else VERBOSE

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            if self.verbose:
                debug_print(f"ClaudeClient initialized with model: {self.model}")
        except Exception as e:
            if self.verbose:
                debug_print(f"Error initializing Claude client: {e}")
            self.client = None

    def analyze(self, prompt: str, max_tokens: int = None) -> str:
        """
        Send prompt to Claude and get response.

        Args:
            prompt: The analysis prompt to send
            max_tokens: Max response tokens (default from config)

        Returns:
            Claude's response text, or error message if failed
        """
        if self.client is None:
            return "Error: Claude client not initialized. Check API key."

        max_tokens = max_tokens or CLAUDE_MAX_TOKENS

        if self.verbose:
            debug_print(f"Sending prompt to Claude ({len(prompt)} chars)")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response = message.content[0].text

            if self.verbose:
                debug_print(f"Received response ({len(response)} chars)")

            return response

        except anthropic.APIError as e:
            error_msg = f"API Error: {e}"
            if self.verbose:
                debug_print(error_msg)
            return error_msg

        except anthropic.AuthenticationError as e:
            error_msg = f"Authentication Error: Check your API key. {e}"
            if self.verbose:
                debug_print(error_msg)
            return error_msg

        except anthropic.RateLimitError as e:
            error_msg = f"Rate Limit Error: Too many requests. {e}"
            if self.verbose:
                debug_print(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Error: {e}"
            if self.verbose:
                debug_print(error_msg)
            return error_msg

    def test_connection(self) -> bool:
        """
        Test the API connection with a simple prompt.

        Returns:
            True if connection successful, False otherwise
        """
        if self.client is None:
            return False

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Respond with only: CONNECTION OK"}
                ]
            )
            response = message.content[0].text
            return "OK" in response.upper()

        except Exception as e:
            if self.verbose:
                debug_print(f"Connection test failed: {e}")
            return False


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("CLAUDE CLIENT - STANDALONE TEST")
    print("=" * 60)

    client = ClaudeClient(verbose=True)

    # Test 1: Connection test
    print("\n[TEST 1] Testing API connection...")
    if client.test_connection():
        print("  SUCCESS: API connection working")
    else:
        print("  FAILED: Could not connect to API")
        print("  Check your ANTHROPIC_API_KEY in config.py")
        sys.exit(1)

    # Test 2: Simple analysis
    print("\n[TEST 2] Testing simple analysis...")
    test_prompt = """You are a trading assistant.

Given: TSLA is at $250, showing bullish M15 structure with rising volume.

Provide a brief (2-3 sentence) assessment of the setup."""

    response = client.analyze(test_prompt, max_tokens=200)

    if not response.startswith("Error"):
        print("  SUCCESS: Received response from Claude")
        print("\n  Response:")
        print("  " + "-" * 50)
        for line in response.split('\n'):
            print(f"  {line}")
        print("  " + "-" * 50)
    else:
        print(f"  FAILED: {response}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
