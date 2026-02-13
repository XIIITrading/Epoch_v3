"""
Excel output via xlwings for Epoch v1 integration using named ranges.
DATA ONLY - No formatting changes. MAX 20 ROWS.
"""
import xlwings as xw
import pandas as pd
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Export scan results to Excel via xlwings using named ranges."""
    
    # Named range configuration
    HEADERS_RANGE_NAME = "scanner_results_headers"
    DATA_RANGE_NAME = "scanner_results"
    WORKSHEET_NAME = "market_overview"
    MAX_ROWS = 20  # Maximum rows to export to Excel
    
    # Column mapping (must match named range layout B3:Q3)
    COLUMNS = [
        'rank', 'ticker', 'ticker_id', 'current_price', 'gap_percent',
        'current_overnight_volume', 'prior_overnight_volume',
        'relative_overnight_volume', 'relative_volume',
        'short_interest', 'days_to_cover', 'ranking_score',
        'atr', 'prior_close', 'scan_date', 'scan_time'
    ]
    
    HEADERS = [
        'Rank', 'Ticker', 'Ticker ID', 'Price', 'Gap %',
        'Curr O/N Vol', 'Prior O/N Vol', 'Rel O/N Vol', 'Rel Vol',
        'Short %', 'DTC', 'Score', 'ATR', 'Prior Close',
        'Scan Date', 'Scan Time'
    ]
    
    @classmethod
    def export_to_epoch(cls, 
                        scan_results: pd.DataFrame, 
                        workbook_path: str,
                        clear_existing: bool = True,
                        max_rows: int = None) -> bool:
        """
        Export scan results to Epoch v1 using named ranges.
        DATA ONLY - Does not modify formatting, column widths, or row heights.
        LIMITED TO TOP 20 ROWS by default.
        
        Args:
            scan_results: DataFrame with scan results (assumed pre-sorted by rank)
            workbook_path: Path to epoch_v1.xlsm
            clear_existing: Clear existing data before writing
            max_rows: Maximum rows to export (default: 20)
            
        Returns:
            bool: Success status
        """
        try:
            # Open workbook
            wb = xw.Book(workbook_path)
            ws = wb.sheets[cls.WORKSHEET_NAME]
            
            logger.info(f"Opened workbook: {workbook_path}")
            
            # Check if named ranges exist, create if not
            cls._ensure_named_ranges(wb, ws)
            
            # Clear existing data if requested (always clear full range to remove old data)
            if clear_existing:
                cls._clear_data_range(ws)
            
            # Prepare data
            export_df = cls._prepare_data(scan_results, max_rows or cls.MAX_ROWS)
            
            if export_df.empty:
                logger.warning("No data to export")
                return False
            
            # Write headers (only if they don't exist)
            cls._write_headers_if_missing(ws)
            
            # Write data using named range
            cls._write_data(ws, export_df)
            
            # Save workbook
            wb.save()
            
            logger.info(f"Successfully exported {len(export_df)} rows to {workbook_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Excel file not found: {workbook_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    @classmethod
    def _ensure_named_ranges(cls, wb: xw.Book, ws: xw.sheets) -> None:
        """Ensure named ranges exist, create if missing."""
        try:
            # Check for headers range
            try:
                _ = wb.names[cls.HEADERS_RANGE_NAME]
                logger.debug(f"Found existing named range: {cls.HEADERS_RANGE_NAME}")
            except KeyError:
                # Create headers range B3:Q3
                ws.range('B3:Q3').name = cls.HEADERS_RANGE_NAME
                logger.info(f"Created named range: {cls.HEADERS_RANGE_NAME} at B3:Q3")
            
            # Check for data range
            try:
                _ = wb.names[cls.DATA_RANGE_NAME]
                logger.debug(f"Found existing named range: {cls.DATA_RANGE_NAME}")
            except KeyError:
                # Create data range starting at B4:Q4
                ws.range('B4:Q4').name = cls.DATA_RANGE_NAME
                logger.info(f"Created named range: {cls.DATA_RANGE_NAME} at B4:Q4")
                
        except Exception as e:
            logger.warning(f"Could not verify named ranges: {e}")
    
    @classmethod
    def _clear_data_range(cls, ws: xw.sheets) -> None:
        """Clear existing data in the scanner_results range."""
        try:
            # Always clear up to row 23 (headers at 3, data 4-23 = 20 rows)
            # This ensures old data beyond top 20 is removed
            clear_range = ws.range('B4:Q23')
            clear_range.clear_contents()
            logger.debug(f"Cleared data range B4:Q23")
        except Exception as e:
            logger.warning(f"Could not clear data range: {e}")
    
    @classmethod
    def _prepare_data(cls, scan_results: pd.DataFrame, max_rows: int) -> pd.DataFrame:
        """
        Prepare data for export with proper column order.
        LIMITS TO TOP N ROWS based on max_rows parameter.
        """
        # Limit to top N rows (already sorted by rank from scanner)
        if len(scan_results) > max_rows:
            logger.info(f"Limiting export from {len(scan_results)} to top {max_rows} rows")
            scan_results = scan_results.head(max_rows).copy()
        
        # Add scan metadata if missing
        if 'scan_date' not in scan_results.columns:
            scan_results['scan_date'] = datetime.now().strftime('%Y-%m-%d')
        if 'scan_time' not in scan_results.columns:
            scan_results['scan_time'] = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        
        # Select columns in the correct order
        available_columns = [col for col in cls.COLUMNS if col in scan_results.columns]
        
        if not available_columns:
            logger.error("No matching columns found in scan results")
            return pd.DataFrame()
        
        export_df = scan_results[available_columns].copy()
        
        # Convert percentages to decimal form (Excel will format them)
        if 'gap_percent' in export_df.columns:
            export_df['gap_percent'] = export_df['gap_percent'] / 100
        
        if 'short_interest' in export_df.columns:
            export_df['short_interest'] = export_df['short_interest'] / 100
        
        logger.info(f"Prepared {len(export_df)} rows for export")
        
        return export_df
    
    @classmethod
    def _write_headers_if_missing(cls, ws: xw.sheets) -> None:
        """Write column headers only if B3 is empty."""
        try:
            # Check if headers already exist
            if ws.range('B3').value is None or ws.range('B3').value == '':
                # Write headers
                ws.range('B3').value = cls.HEADERS
                logger.debug("Headers written to B3:Q3")
            else:
                logger.debug("Headers already exist, skipping")
            
        except Exception as e:
            logger.warning(f"Could not write headers: {e}")
    
    @classmethod
    def _write_data(cls, ws: xw.sheets, export_df: pd.DataFrame) -> None:
        """Write data starting at B4. NO FORMATTING."""
        try:
            # Write data starting at B4 - raw values only
            ws.range('B4').options(index=False, header=False).value = export_df.values
            
            logger.info(f"Wrote {len(export_df)} rows of data starting at B4")
            
        except Exception as e:
            logger.error(f"Failed to write data: {e}")
            raise
    
    @classmethod
    def get_scan_summary(cls, workbook_path: str) -> dict:
        """
        Read summary information from the scanner_results range.
        
        Returns:
            dict: Summary with count, date, top tickers, etc.
        """
        try:
            wb = xw.Book(workbook_path)
            ws = wb.sheets[cls.WORKSHEET_NAME]
            
            # Read data from named range area (B4:Q23 for max 20 rows)
            last_row = ws.range('B' + str(ws.cells.last_cell.row)).end('up').row
            
            if last_row <= 3:
                return {'count': 0, 'message': 'No scan data found'}
            
            # Limit to max 23 (headers at 3, max 20 data rows)
            last_row = min(last_row, 23)
            
            # Read the data
            data_range = ws.range(f'B4:Q{last_row}')
            data = data_range.value
            
            # Handle single row case
            if not isinstance(data[0], (list, tuple)):
                data = [data]
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data, columns=cls.HEADERS)
            
            summary = {
                'count': len(df),
                'scan_date': df['Scan Date'].iloc[0] if len(df) > 0 else None,
                'scan_time': df['Scan Time'].iloc[0] if len(df) > 0 else None,
                'top_5_tickers': df['Ticker'].head(5).tolist() if len(df) >= 5 else df['Ticker'].tolist(),
                'avg_gap': df['Gap %'].mean() if 'Gap %' in df.columns else None,
                'avg_score': df['Score'].mean() if 'Score' in df.columns else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to read scan summary: {e}")
            return {'error': str(e)}