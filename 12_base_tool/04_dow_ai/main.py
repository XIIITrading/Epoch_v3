"""
DOW AI Trading Assistant - Main Entry Point
Epoch Trading System v1 - XIII Trading LLC

Run: python main.py [command] [args]

Examples:
    python main.py entry NVDA long secondary
    python main.py exit TSLA sell primary
    python main.py models
"""
import sys
from pathlib import Path

# Ensure we're in the correct directory for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cli import cli
except Exception as e:
    print(f"[ERROR] Failed to import CLI: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
