"""
Epoch Trading System - Trading Journal Launcher

Usage:
    python app.py

Author: XIII Trading LLC
"""

import subprocess
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).parent


def main():
    """Launch the Streamlit journal application."""
    streamlit_app = MODULE_DIR / "streamlit_app.py"

    if not streamlit_app.exists():
        print(f"Error: Streamlit app not found at {streamlit_app}")
        sys.exit(1)

    print("=" * 60)
    print("  EPOCH TRADING JOURNAL")
    print("  Trade Logging, Review & Analytics")
    print("  XIII Trading LLC")
    print("=" * 60)
    print()
    print("Launching Streamlit application...")
    print("Press Ctrl+C to stop the server")
    print()

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(streamlit_app),
             "--server.port", "8502",
             "--server.headless", "true"],
            cwd=str(MODULE_DIR),
            check=True
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
