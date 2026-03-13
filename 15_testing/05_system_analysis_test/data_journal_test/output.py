"""
Output formatting utilities for data journal analysis.
Writes structured results to both console and markdown files.
"""
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'data_journal_results')


class ResultsWriter:
    """Writes analysis results to console and markdown file simultaneously."""

    def __init__(self, filename: str):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self.filepath = os.path.join(RESULTS_DIR, filename)
        self.lines = []
        self.filename = filename

    def header(self, title: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._write(f'# {title}')
        self._write(f'> Generated: {timestamp}')
        self._write('')

    def section(self, title: str):
        self._write(f'## {title}')
        self._write('')

    def subsection(self, title: str):
        self._write(f'### {title}')
        self._write('')

    def text(self, line: str = ''):
        self._write(line)

    def metric(self, label: str, value, unit: str = ''):
        display = f'{value}{unit}' if unit else str(value)
        self._write(f'- **{label}**: {display}')

    def table(self, headers: list, rows: list, alignments: list = None):
        if not rows:
            self._write('*No data*')
            self._write('')
            return

        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        header_line = '| ' + ' | '.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)) + ' |'
        self._write(header_line)

        if alignments:
            sep_parts = []
            for i, a in enumerate(alignments):
                w = col_widths[i]
                if a == 'right':
                    sep_parts.append('-' * (w - 1) + ':')
                elif a == 'center':
                    sep_parts.append(':' + '-' * (w - 2) + ':')
                else:
                    sep_parts.append('-' * w)
            sep_line = '| ' + ' | '.join(sep_parts) + ' |'
        else:
            sep_line = '| ' + ' | '.join('-' * w for w in col_widths) + ' |'
        self._write(sep_line)

        for row in rows:
            data_line = '| ' + ' | '.join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + ' |'
            self._write(data_line)
        self._write('')

    def divider(self):
        self._write('---')
        self._write('')

    def save(self):
        content = '\n'.join(self.lines)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'\n[SAVED] {self.filepath}')

    def _write(self, line: str):
        print(line)
        self.lines.append(line)
