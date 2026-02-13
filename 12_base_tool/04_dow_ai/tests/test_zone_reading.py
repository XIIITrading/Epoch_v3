"""Test zone reading from Analysis worksheet."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.epoch_reader import EpochReader

def test_zone_reading():
    """Test reading zones from Analysis worksheet."""
    reader = EpochReader()

    if not reader.connect():
        print("FAIL - Could not connect to Excel")
        return False

    ticker = "NVDA"  # Or whichever ticker you have

    # Test primary zone
    print(f"\nTesting PRIMARY zone for {ticker}...")
    primary = reader.get_primary_zone(ticker)
    if primary:
        print(f"  PASS - Primary zone found:")
        print(f"    Zone ID: {primary['zone_id']}")
        print(f"    Direction: {primary['direction']}")
        print(f"    Range: ${primary['zone_low']:.2f} - ${primary['zone_high']:.2f}")
        print(f"    POC: ${primary['hvn_poc']:.2f}")
        print(f"    Target: ${primary['target']:.2f}" if primary['target'] else "    Target: N/A")
    else:
        print(f"  WARNING - No primary zone found for {ticker}")

    # Test secondary zone
    print(f"\nTesting SECONDARY zone for {ticker}...")
    secondary = reader.get_secondary_zone(ticker)
    if secondary:
        print(f"  PASS - Secondary zone found:")
        print(f"    Zone ID: {secondary['zone_id']}")
        print(f"    Direction: {secondary['direction']}")
        print(f"    Range: ${secondary['zone_low']:.2f} - ${secondary['zone_high']:.2f}")
        print(f"    POC: ${secondary['hvn_poc']:.2f}")
        print(f"    Target: ${secondary['target']:.2f}" if secondary['target'] else "    Target: N/A")
    else:
        print(f"  WARNING - No secondary zone found for {ticker}")

    # Verify they're different
    if primary and secondary:
        if primary['zone_id'] != secondary['zone_id']:
            print(f"\n  PASS - Primary and Secondary are different zones")
        else:
            print(f"\n  FAIL - Primary and Secondary have same zone_id!")

    # Test model-based selection
    print(f"\nTesting get_zone_for_model()...")
    for model in ['EPCH_01', 'EPCH_02', 'EPCH_03', 'EPCH_04']:
        zone = reader.get_zone_for_model(ticker, model)
        zone_id = zone['zone_id'] if zone else 'None'
        zone_type = zone['zone_type'] if zone else 'N/A'
        print(f"  {model} → {zone_type.upper()} zone: {zone_id}")

    return True

if __name__ == '__main__':
    test_zone_reading()
