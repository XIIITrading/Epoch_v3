"""
Output exporters for market scanner results.
"""

from .excel_exporter import ExcelExporter

# Import other exporters if they exist
try:
    from .csv_exporter import CSVExporter
except ImportError:
    CSVExporter = None

try:
    from .markdown_exporter import MarkdownExporter
except ImportError:
    MarkdownExporter = None

try:
    from .report_formatter import ReportFormatter
except ImportError:
    ReportFormatter = None

try:
    from .supabase_exporter import SupabaseExporter
except ImportError:
    SupabaseExporter = None

# Build __all__ dynamically based on what's available
__all__ = ['ExcelExporter']

if CSVExporter:
    __all__.append('CSVExporter')
if MarkdownExporter:
    __all__.append('MarkdownExporter')
if ReportFormatter:
    __all__.append('ReportFormatter')
if SupabaseExporter:
    __all__.append('SupabaseExporter')