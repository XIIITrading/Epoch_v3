# check_analysis.py
import openpyxl
from pathlib import Path

wb = openpyxl.load_workbook(Path(r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"), data_only=True)
sheet = wb["analysis"]

print("Primary Zone Tickers (B31:B40):")
for row in range(31, 41):
    val = sheet[f"B{row}"].value
    if val:
        print(f"  Row {row}: {val}")

print("\nSecondary Zone Tickers (N31:N40):")
for row in range(31, 41):
    val = sheet[f"N{row}"].value
    if val:
        print(f"  Row {row}: {val}")

wb.close()