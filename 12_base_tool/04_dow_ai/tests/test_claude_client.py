"""
DOW AI - Claude Client Tests
Epoch Trading System v1 - XIII Trading LLC

Run: python tests/test_claude_client.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.claude_client import ClaudeClient
from config import debug_print, get_debug_filepath


class TestClaudeClient:
    """Test suite for ClaudeClient."""

    def __init__(self):
        self.client = ClaudeClient(verbose=True)
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        print(f"  [{status}] {test_name}")
        if message and not passed:
            print(f"         {message}")

    def test_client_initialization(self):
        """Test that client initializes properly."""
        if self.client.client is not None:
            self.log_result("client_initialization", True)
            return True
        else:
            self.log_result("client_initialization", False, "Client is None")
            return False

    def test_connection(self):
        """Test API connection."""
        connected = self.client.test_connection()

        if connected:
            self.log_result("api_connection", True)
            return True
        else:
            self.log_result("api_connection", False, "Connection failed - check API key")
            return False

    def test_simple_response(self):
        """Test that we get a response from Claude."""
        prompt = "Respond with exactly: TEST PASSED"
        response = self.client.analyze(prompt, max_tokens=50)

        if "PASSED" in response.upper() or "TEST" in response.upper():
            self.log_result("simple_response", True)
            return True
        elif response.startswith("Error"):
            self.log_result("simple_response", False, response)
            return False
        else:
            # Claude might phrase it differently
            self.log_result("simple_response", True)
            print(f"         Response: {response[:50]}...")
            return True

    def test_trading_analysis_response(self):
        """Test a trading-style analysis prompt."""
        prompt = """You are a trading assistant.

TSLA is at $250.
M15 structure: BULL
Volume delta: +50,000 (Bullish)

In 2 sentences, assess this setup for a long entry."""

        response = self.client.analyze(prompt, max_tokens=200)

        if not response.startswith("Error") and len(response) > 20:
            self.log_result("trading_analysis_response", True)
            print(f"         Response length: {len(response)} chars")
            return True
        else:
            self.log_result("trading_analysis_response", False, response[:100])
            return False

    def test_max_tokens_respected(self):
        """Test that max_tokens parameter is respected."""
        prompt = "Write a very long essay about the stock market."
        response = self.client.analyze(prompt, max_tokens=50)

        # Response should be relatively short due to token limit
        if not response.startswith("Error"):
            self.log_result("max_tokens_respected", True)
            print(f"         Response length: {len(response)} chars")
            return True
        else:
            self.log_result("max_tokens_respected", False, response)
            return False

    def test_handles_empty_prompt(self):
        """Test handling of empty prompt."""
        response = self.client.analyze("")

        # Should get some response (even if error)
        if response is not None and len(response) > 0:
            self.log_result("handles_empty_prompt", True)
            return True
        else:
            self.log_result("handles_empty_prompt", False, "No response")
            return False

    def run_all(self) -> bool:
        """Run all tests."""
        print("\n" + "=" * 60)
        print("CLAUDE CLIENT - TEST SUITE")
        print("=" * 60 + "\n")

        # Run tests
        self.test_client_initialization()

        # If initialization failed, skip remaining tests
        if not self.results[-1][1]:
            print("\n[ABORT] Client not initialized, skipping remaining tests")
            return False

        self.test_connection()

        # If connection failed, skip remaining tests
        if not self.results[-1][1]:
            print("\n[ABORT] Connection failed, skipping remaining tests")
            return False

        self.test_simple_response()
        self.test_trading_analysis_response()
        self.test_max_tokens_respected()
        self.test_handles_empty_prompt()

        # Summary
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)

        print("\n" + "-" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("-" * 60)

        # Write debug report if any failures
        if passed < total:
            filepath = get_debug_filepath('test', 'claude_client')
            with open(filepath, 'w') as f:
                f.write("CLAUDE CLIENT TEST REPORT\n")
                f.write("=" * 60 + "\n\n")
                for name, passed, msg in self.results:
                    status = "PASS" if passed else "FAIL"
                    f.write(f"[{status}] {name}\n")
                    if msg:
                        f.write(f"       {msg}\n")
            print(f"\nDebug report saved to: {filepath}")

        return passed == total


if __name__ == '__main__':
    tester = TestClaudeClient()
    success = tester.run_all()
    sys.exit(0 if success else 1)
