# raw_zones_writer.py - Epoch Raw Zones Writer
# Writes all calculated zones to raw_zones worksheet
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
Adapted from Meridian raw_zones_writer.py
Writes to raw_zones worksheet with columns A-M:
A: Ticker_ID, B: Ticker, C: Date, D: Price, E: Direction
F: Zone_ID, G: HVN_POC, H: Zone_High, I: Zone_Low
J: Overlaps, K: Score, L: Rank, M: Confluences
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


class EpochRawZonesWriter:
    """Writes all unfiltered zone results to raw_zones worksheet"""

    def __init__(self, excel_connection):
        """
        Initialize writer
        
        Args:
            excel_connection: Excel connection object with get_sheet() method
        """
        self.conn = excel_connection
        self.raw_zones_sheet = excel_connection.get_sheet('raw_zones')
        
        # Column mapping (A-M)
        self.columns = {
            'ticker_id': 'A',
            'ticker': 'B',
            'date': 'C',
            'price': 'D',
            'direction': 'E',
            'zone_id': 'F',
            'hvn_poc': 'G',
            'zone_high': 'H',
            'zone_low': 'I',
            'overlaps': 'J',
            'score': 'K',
            'rank': 'L',
            'confluences': 'M'
        }

    def write_all_zones(self, all_zones_df: pd.DataFrame):
        """
        Write ALL calculated zones to raw_zones worksheet
        Data starts at row 2 (row 1 has headers)
        
        Args:
            all_zones_df: DataFrame with ALL zones (already sorted by ticker_id, score)
        """
        print("\n" + "=" * 60)
        print(f"WRITING {len(all_zones_df)} RAW ZONES TO RAW_ZONES WORKSHEET")
        print("=" * 60)
        
        # Write data rows starting at row 2
        if all_zones_df is not None and not all_zones_df.empty:
            self._write_data(all_zones_df)
        else:
            print("  No zones to write")
            return
        
        print("\n✓ Raw zones written successfully")

    def _clear_data_only(self):
        """Clear only data rows (preserve headers in row 1 and formatting)"""
        print("\nClearing data rows (preserving headers and formatting)...")
        
        try:
            # Try clearing from row 2 onwards, columns A-M
            self.raw_zones_sheet.range('A2:M1000').clear_contents()
        except Exception as e:
            print(f"  ⚠ Could not clear range (will overwrite): {e}")
            # If clear fails, we'll just overwrite - not a critical error

    def _write_data(self, all_zones_df: pd.DataFrame):
        """
        Write zone data starting from row 2
        
        Args:
            all_zones_df: DataFrame with ALL zone results
        """
        start_row = 2
        zones_written = 0
        prev_ticker = None
        
        print(f"\n  Writing {len(all_zones_df)} zones starting at row {start_row}...")
        print(f"  (Grouped by ticker, sorted by score within each ticker)")
        
        # Track zones per rank for summary
        rank_counts = {'L5': 0, 'L4': 0, 'L3': 0, 'L2': 0, 'L1': 0}
        
        for idx, zone in all_zones_df.iterrows():
            row_num = start_row + zones_written
            
            try:
                # Write each column
                self.raw_zones_sheet.range(f'A{row_num}').value = zone['ticker_id']
                self.raw_zones_sheet.range(f'B{row_num}').value = zone['ticker']
                self.raw_zones_sheet.range(f'C{row_num}').value = zone['date']
                self.raw_zones_sheet.range(f'D{row_num}').value = zone['price']
                self.raw_zones_sheet.range(f'E{row_num}').value = zone['direction']
                self.raw_zones_sheet.range(f'F{row_num}').value = zone['zone_id']
                self.raw_zones_sheet.range(f'G{row_num}').value = zone['hvn_poc']
                self.raw_zones_sheet.range(f'H{row_num}').value = zone['zone_high']
                self.raw_zones_sheet.range(f'I{row_num}').value = zone['zone_low']
                self.raw_zones_sheet.range(f'J{row_num}').value = zone['overlaps']
                self.raw_zones_sheet.range(f'K{row_num}').value = zone['score']
                self.raw_zones_sheet.range(f'L{row_num}').value = zone['rank']
                self.raw_zones_sheet.range(f'M{row_num}').value = zone['confluences']
            except Exception as e:
                print(f"  ❌ Error writing row {row_num}: {e}")
                continue
            
            # Track rank counts
            rank = zone['rank']
            if rank in rank_counts:
                rank_counts[rank] += 1
            
            # Print progress on ticker change
            if zone['ticker_id'] != prev_ticker:
                print(f"    Row {row_num}: {zone['ticker']} | {zone['zone_id']} | {zone['rank']} | Score: {zone['score']:.2f}")
            
            prev_ticker = zone['ticker_id']
            zones_written += 1
        
        print(f"\n  ✓ {zones_written} zones written to rows {start_row}-{start_row + zones_written - 1}")
        print(f"\n  Rank breakdown:")
        print(f"    L5: {rank_counts['L5']}")
        print(f"    L4: {rank_counts['L4']}")
        print(f"    L3: {rank_counts['L3']}")
        print(f"    L2: {rank_counts['L2']}")
        print(f"    L1: {rank_counts['L1']}")

    def write_summary(self, stats: dict, start_row: int = None):
        """
        Write summary statistics below the zone data
        
        Args:
            stats: Dictionary with summary statistics
            start_row: Row to start writing summary (auto-calculated if None)
        """
        if start_row is None:
            # Find first empty row after data
            start_row = stats.get('total_zones', 0) + 5
            start_row = max(start_row, 50)  # Minimum row 50
        
        print(f"\n  Writing summary at row {start_row}...")
        
        # Summary header
        self.raw_zones_sheet.range(f'A{start_row}').value = "EPOCH RAW ZONES SUMMARY"
        self.raw_zones_sheet.range(f'A{start_row}').api.Font.Bold = True
        
        # Stats
        stats_row = start_row + 1
        summary_items = [
            ("Tickers Processed:", stats.get('total_tickers', 0)),
            ("Total Zones Found:", stats.get('total_zones', 0)),
            ("L5 Zones:", stats.get('l5_count', 0)),
            ("L4 Zones:", stats.get('l4_count', 0)),
            ("L3 Zones:", stats.get('l3_count', 0)),
            ("L2 Zones:", stats.get('l2_count', 0)),
            ("L1 Zones:", stats.get('l1_count', 0)),
            ("Avg Score:", stats.get('avg_score', 0)),
            ("Max Score:", stats.get('max_score', 0)),
        ]
        
        for i, (label, value) in enumerate(summary_items):
            self.raw_zones_sheet.range(f'A{stats_row + i}').value = label
            self.raw_zones_sheet.range(f'B{stats_row + i}').value = value
        
        print("  ✓ Summary written")
