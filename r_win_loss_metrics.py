import psycopg2
import sys

DB_CONFIG = {
    'host': 'db.pdbmcskznoaiybdiobje.supabase.co',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'guid-saltation-covet',
    'sslmode': 'require',
}

SEP = '=' * 80

def ph(title):
    print()
    print(SEP)
    print('  ' + title)
    print(SEP)

def ptable(rows, cols):
    if not rows:
        print('  (no results)')
        return
    widths = [len(str(c)) for c in cols]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val is not None else 'NULL'))
    hdr = '  '.join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
    print('  ' + hdr)
    div = '  '.join('-' * w for w in widths)
    print('  ' + div)
    for row in rows:
        line = '  '.join(str(v if v is not None else 'NULL').ljust(widths[i]) for i, v in enumerate(row))
        print('  ' + line)

def main():
    print()
    print('#' * 80)
    print('  R_WIN_LOSS TABLE - COMPREHENSIVE METRICS')
    print('#' * 80)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    ph('1. OVERALL SUMMARY')
    cur.execute(chr(10).join([
        'SELECT',
        '    COUNT(*) as total_trades,',
        '    COUNT(*) FILTER (WHERE outcome = chr(39) + 'WIN' + chr(39)) as wins,'
    ]))
