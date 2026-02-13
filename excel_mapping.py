import xlwings as xw
import yaml
from pathlib import Path

# Configuration
EXCEL_PATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
OUTPUT_PATH = r"C:\XIIITradingSystems\Epoch\epoch_cell_map.yaml"

# Define ranges to scan - easily expandable
scan_config = [
    # {'sheet': 'market_overview', 'range': 'B4:P24', 'segment': 'market_screener'},
    # {'sheet': 'market_overview', 'range': 'B29:R31', 'segment': 'market_structure'},
    # {'sheet': 'market_overview', 'range': 'B36:R45', 'segment': 'ticker_structure'},
    {'sheet': 'bar_data', 'range': 'B4:M13', 'segment': 'ticker_structure'},
    {'sheet': 'bar_data', 'range': 'B17:L26', 'segment': 'monthly_metrics'},
    {'sheet': 'bar_data', 'range': 'B31:L40', 'segment': 'weekly_metrics'},
    {'sheet': 'bar_data', 'range': 'B45:L54', 'segment': 'daily_metrics'},
    {'sheet': 'bar_data', 'range': 'B59:O68', 'segment': 'time_hvn'},
    {'sheet': 'bar_data', 'range': 'B73:T82', 'segment': 'on_options_metrics'},
    {'sheet': 'bar_data', 'range': 'B86:V95', 'segment': 'add_metrics'},
]

def scan_excel_ranges():
    """
    Scans Excel ranges and creates a cell map based on cell contents.
    Cell values become keys, cell addresses become values.
    """
    
    # Load existing map if it exists
    if Path(OUTPUT_PATH).exists():
        with open(OUTPUT_PATH, 'r') as f:
            cell_map = yaml.safe_load(f)
        print(f"✓ Loading existing map from {OUTPUT_PATH}\n")
    else:
        cell_map = {'excel_path': EXCEL_PATH}
        print("Creating new map\n")
    
    # Open workbook (read-only for safety)
    wb = xw.Book(EXCEL_PATH)
    
    try:
        for config in scan_config:
            sheet_name = config['sheet']
            range_addr = config['range']
            segment_name = config['segment']
            
            print(f"Scanning {sheet_name}!{range_addr} for segment '{segment_name}'...")
            
            # Get the sheet
            sht = wb.sheets[sheet_name]
            
            # Get the range
            range_obj = sht.range(range_addr)
            
            # Initialize nested structure if needed
            if sheet_name not in cell_map:
                cell_map[sheet_name] = {}
            
            if segment_name not in cell_map[sheet_name]:
                cell_map[sheet_name][segment_name] = {}
            
            # Scan each cell in the range
            for cell in range_obj:
                cell_value = cell.value
                
                # Only process non-empty cells
                if cell_value is not None and str(cell_value).strip() != '':
                    cell_name = str(cell_value).strip()
                    cell_address = cell.get_address(False, False)  # Returns 'B4' format
                    
                    # Store in the map
                    cell_map[sheet_name][segment_name][cell_name] = cell_address
                    print(f"  Found: {cell_name} -> {cell_address}")
        
        # Write to YAML file
        with open(OUTPUT_PATH, 'w') as f:
            yaml.dump(cell_map, f, default_flow_style=False, sort_keys=False)
        
        print(f"\n✓ Cell map created successfully: {OUTPUT_PATH}")
        print(f"  Total sheets: {len([k for k in cell_map.keys() if k != 'excel_path'])}")
        
        # Display summary
        for sheet_name in cell_map:
            if sheet_name == 'excel_path':
                continue
            print(f"\n  {sheet_name}:")
            for segment_name in cell_map[sheet_name]:
                cell_count = len(cell_map[sheet_name][segment_name])
                print(f"    {segment_name}: {cell_count} cells")
    
    finally:
        # Close workbook without saving
        wb.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Epoch v1 Cell Map Generator")
    print("=" * 60)
    print()
    
    scan_excel_ranges()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)