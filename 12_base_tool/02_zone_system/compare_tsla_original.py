"""
TSLA Comparison Script - Run analysis using ORIGINAL 02_zone_system calculators.

This script compares two modes:
1. Without D1 ATR (uses internally calculated ATR from minute data)
2. With D1 ATR (simulating production mode where ATR comes from bar_data worksheet)
"""
import sys
sys.path.insert(0, r'C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier')
sys.path.insert(0, r'C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier\calculations')

from datetime import date
from calculations.epoch_hvn_identifier import EpochHVNIdentifier

ticker = 'TSLA'
anchor_date = '2025-11-21'
analysis_date = date.today().isoformat()

print('='*80)
print(f'ORIGINAL SYSTEM (02_zone_system) - TSLA Analysis')
print(f'Anchor Date: {anchor_date}')
print(f'Analysis Date: {analysis_date}')
print('='*80)

# HVN POCs - Mode 1: Internal ATR calculation (fallback mode)
print('\n--- HVN POCs (Mode 1: Internal ATR) ---')
identifier = EpochHVNIdentifier()
result = identifier.analyze(ticker=ticker, start_date=anchor_date)

print(f'Date Range: {result.start_date} to {result.end_date}')
print(f'Bars Analyzed: {result.bars_analyzed}')
print(f'ATR Used: ${result.atr_used:.4f}' if result.atr_used else 'ATR Used: N/A')

for poc in sorted(result.pocs, key=lambda x: x.rank):
    print(f'  POC{poc.rank:2d}: ${poc.price:.2f} (vol: {poc.volume:,.0f})')

# HVN POCs - Mode 2: With D1 ATR from bar_data (production mode)
# Using same ATR value that the new Streamlit tool calculates: $13.80
print('\n--- HVN POCs (Mode 2: D1 ATR = $13.80) ---')
result2 = identifier.analyze(ticker=ticker, start_date=anchor_date, atr_value=13.80)

print(f'Date Range: {result2.start_date} to {result2.end_date}')
print(f'Bars Analyzed: {result2.bars_analyzed}')
print(f'ATR Used: ${result2.atr_used:.4f}' if result2.atr_used else 'ATR Used: N/A')

for poc in sorted(result2.pocs, key=lambda x: x.rank):
    print(f'  POC{poc.rank:2d}: ${poc.price:.2f} (vol: {poc.volume:,.0f})')

print('\n' + '='*80)
