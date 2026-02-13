"""
DOW AI - Export Indicator Edges
Epoch Trading System v1 - XIII Trading LLC

Parses indicator edge test results from 03_indicators markdown files and exports:
1. JSON file to ai_context/indicator_edges.json
2. Upsert to ai_indicator_edges Supabase table

Run: python export_indicator_edges.py [--json-only] [--db-only] [--verbose]
"""

import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras

# =============================================================================
# Supabase Configuration
# =============================================================================
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
AI_CONTEXT_DIR = SCRIPT_DIR / "ai_context"
OUTPUT_FILE = AI_CONTEXT_DIR / "indicator_edges.json"
INDICATORS_DIR = Path("C:/XIIITradingSystems/Epoch/03_indicators/python")

# Indicator result directories
INDICATOR_FOLDERS = {
    'candle_range': 'candle_range',
    'volume_delta': 'volume_delta',
    'volume_roc': 'volume_roc',
    'cvd_slope': 'cvd_slope',
    'sma_edge': 'sma_edge',
    'structure_edge': 'structure_edge',
    'vwap_simple': 'vwap_simple'
}


def get_db_connection():
    """Get PostgreSQL connection to Supabase."""
    return psycopg2.connect(**DB_CONFIG)


def find_latest_result_file(indicator_folder: str) -> Optional[Path]:
    """Find the most recent result markdown file for an indicator."""
    results_dir = INDICATORS_DIR / indicator_folder / "results"
    if not results_dir.exists():
        return None

    md_files = list(results_dir.glob("*.md"))
    if not md_files:
        return None

    # Sort by modification time, newest first
    md_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return md_files[0]


def parse_edge_table(content: str) -> List[Dict]:
    """
    Parse edge summary tables from markdown content.

    Looks for tables with format:
    | Test | Segment | Edge? | Conf | Effect | p-value |
    """
    edges = []

    # Pattern to match table rows with edge data
    # Format: | Test Name | Segment | **YES**/NO | HIGH/MEDIUM/LOW | Xpp | 0.XXXX |
    table_row_pattern = re.compile(
        r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\*\*YES\*\*|NO)\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|\s*([\d.]+)pp\s*\|\s*([\d.]+)\s*\|'
    )

    for match in table_row_pattern.finditer(content):
        test_name = match.group(1).strip()
        segment = match.group(2).strip()
        has_edge = match.group(3) == '**YES**'
        confidence = match.group(4)
        effect_size = float(match.group(5))
        p_value = float(match.group(6))

        edges.append({
            'test_name': test_name,
            'segment': segment,
            'has_edge': has_edge,
            'confidence': confidence,
            'effect_size_pp': effect_size,
            'p_value': p_value
        })

    return edges


def parse_key_findings(content: str) -> List[str]:
    """Extract key findings (edges detected) section."""
    findings = []

    # Look for "Key Findings" section
    key_findings_match = re.search(
        r'## Key Findings.*?\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )

    if key_findings_match:
        findings_text = key_findings_match.group(1)
        # Parse bullet points
        for line in findings_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                findings.append(line[2:])

    return findings


def parse_indicator_report(indicator: str, file_path: Path, verbose: bool = False) -> Dict:
    """Parse a single indicator's edge report."""
    content = file_path.read_text(encoding='utf-8')

    # Extract metadata
    metadata = {}

    # Generated date
    gen_match = re.search(r'\*\*Generated:\*\*\s*(.+)', content)
    if gen_match:
        metadata['generated'] = gen_match.group(1).strip()

    # Data range
    range_match = re.search(r'\*\*Data Range:\*\*\s*(.+)', content)
    if range_match:
        metadata['data_range'] = range_match.group(1).strip()

    # Total trades
    trades_match = re.search(r'\*\*Total Trades:\*\*\s*([\d,]+)', content)
    if trades_match:
        metadata['total_trades'] = int(trades_match.group(1).replace(',', ''))

    # Baseline win rate
    baseline_match = re.search(r'\*\*Baseline Win Rate:\*\*\s*([\d.]+)%', content)
    if baseline_match:
        metadata['baseline_win_rate'] = float(baseline_match.group(1))

    # Parse edge tables
    edges = parse_edge_table(content)

    # Parse key findings
    key_findings = parse_key_findings(content)

    if verbose:
        print(f"    {indicator}: {len(edges)} edge tests, {sum(1 for e in edges if e['has_edge'])} with edge")

    return {
        'indicator': indicator,
        'file': file_path.name,
        'metadata': metadata,
        'edges': edges,
        'key_findings': key_findings
    }


def summarize_edges_for_json(all_reports: List[Dict]) -> Dict:
    """
    Create a simplified JSON structure optimized for DOW AI prompts.

    Groups edges by indicator with favorable/unfavorable conditions.
    """
    summary = {
        "generated_at": datetime.now().isoformat(),
        "edges": {}
    }

    for report in all_reports:
        indicator = report['indicator']
        edges = report['edges']

        # Find edges with has_edge=True and HIGH/MEDIUM confidence
        significant_edges = [e for e in edges if e['has_edge'] and e['confidence'] in ['HIGH', 'MEDIUM']]

        if not significant_edges:
            continue

        # Group by segment (ALL, LONG, SHORT)
        by_segment = {}
        for edge in significant_edges:
            segment = edge['segment']
            if segment not in by_segment:
                by_segment[segment] = []
            by_segment[segment].append(edge)

        # Determine favorable/unfavorable conditions
        favorable = []
        unfavorable = []
        best_for = "ALL"
        max_effect = 0
        max_effect_segment = "ALL"

        for segment, seg_edges in by_segment.items():
            for edge in seg_edges:
                effect = edge['effect_size_pp']

                # Track best segment
                if effect > max_effect:
                    max_effect = effect
                    max_effect_segment = segment

                # Create condition string
                test_name = edge['test_name']
                condition = f"{test_name}: +{effect:.1f}pp ({segment})"

                # Categorize based on test name patterns
                if 'absorption' in test_name.lower() or '<' in test_name:
                    unfavorable.append(f"SKIP if {test_name}")
                else:
                    favorable.append(condition)

        # Limit to top 3 each
        favorable = favorable[:3]
        unfavorable = unfavorable[:2]

        summary['edges'][indicator] = {
            'favorable': favorable,
            'unfavorable': unfavorable,
            'best_for': max_effect_segment,
            'max_effect_pp': max_effect,
            'total_tests': len(edges),
            'significant_edges': len(significant_edges)
        }

    return summary


def export_to_json(summary: Dict, verbose: bool = False) -> bool:
    """Export indicator edges to JSON file."""
    try:
        AI_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_FILE, 'w') as f:
            json.dump(summary, f, indent=2)

        if verbose:
            print(f"  Exported to {OUTPUT_FILE}")

        return True
    except Exception as e:
        print(f"  ERROR exporting JSON: {e}")
        return False


def upsert_to_supabase(conn, all_reports: List[Dict], verbose: bool = False) -> bool:
    """Upsert indicator edges to ai_indicator_edges table."""
    upsert_query = """
    INSERT INTO ai_indicator_edges (
        indicator, segment, test_name, has_edge, p_value,
        effect_size_pp, confidence, baseline_win_rate,
        favorable_condition, validation_date, updated_at
    ) VALUES (
        %(indicator)s, %(segment)s, %(test_name)s, %(has_edge)s, %(p_value)s,
        %(effect_size_pp)s, %(confidence)s, %(baseline_win_rate)s,
        %(favorable_condition)s, %(validation_date)s, NOW()
    )
    ON CONFLICT (indicator, segment, test_name) DO UPDATE SET
        has_edge = EXCLUDED.has_edge,
        p_value = EXCLUDED.p_value,
        effect_size_pp = EXCLUDED.effect_size_pp,
        confidence = EXCLUDED.confidence,
        baseline_win_rate = EXCLUDED.baseline_win_rate,
        favorable_condition = EXCLUDED.favorable_condition,
        validation_date = EXCLUDED.validation_date,
        updated_at = NOW();
    """

    try:
        with conn.cursor() as cur:
            rows_affected = 0

            for report in all_reports:
                indicator = report['indicator']
                metadata = report['metadata']
                baseline_wr = metadata.get('baseline_win_rate', 44.0)

                # Parse validation date from metadata
                gen_str = metadata.get('generated', '')
                try:
                    validation_date = datetime.strptime(gen_str.split()[0], '%Y-%m-%d').date()
                except:
                    validation_date = datetime.now().date()

                for edge in report['edges']:
                    # Create favorable condition description
                    if edge['has_edge']:
                        favorable = f"{edge['test_name']}: +{edge['effect_size_pp']:.1f}pp edge"
                    else:
                        favorable = None

                    params = {
                        'indicator': indicator,
                        'segment': edge['segment'],
                        'test_name': edge['test_name'],
                        'has_edge': edge['has_edge'],
                        'p_value': edge['p_value'],
                        'effect_size_pp': edge['effect_size_pp'],
                        'confidence': edge['confidence'],
                        'baseline_win_rate': baseline_wr,
                        'favorable_condition': favorable,
                        'validation_date': validation_date
                    }
                    cur.execute(upsert_query, params)
                    rows_affected += 1

            conn.commit()

        if verbose:
            print(f"  Upserted {rows_affected} rows to ai_indicator_edges")

        return True
    except Exception as e:
        print(f"  ERROR upserting to Supabase: {e}")
        conn.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description='Export indicator edges to JSON and Supabase')
    parser.add_argument('--json-only', action='store_true', help='Only export to JSON, skip Supabase')
    parser.add_argument('--db-only', action='store_true', help='Only upsert to Supabase, skip JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    print("=" * 60)
    print("DOW AI - Export Indicator Edges")
    print("=" * 60)

    # Parse all indicator reports
    print("\n[1] Parsing indicator edge reports...")
    all_reports = []

    for indicator, folder in INDICATOR_FOLDERS.items():
        result_file = find_latest_result_file(folder)
        if result_file:
            if args.verbose:
                print(f"  Found: {result_file.name}")
            report = parse_indicator_report(indicator, result_file, args.verbose)
            all_reports.append(report)
        else:
            if args.verbose:
                print(f"  No results found for {indicator}")

    if not all_reports:
        print("  WARNING: No indicator reports found")
        sys.exit(1)

    print(f"  Parsed {len(all_reports)} indicator reports")

    # Calculate totals
    total_edges = sum(len(r['edges']) for r in all_reports)
    total_significant = sum(sum(1 for e in r['edges'] if e['has_edge']) for r in all_reports)
    print(f"  Total edge tests: {total_edges}")
    print(f"  Significant edges: {total_significant}")

    # Create summary for JSON
    summary = summarize_edges_for_json(all_reports)

    # Export to JSON
    if not args.db_only:
        print("\n[2] Exporting to JSON...")
        if export_to_json(summary, args.verbose):
            print("  JSON export complete")
        else:
            print("  JSON export failed")

    # Upsert to Supabase
    if not args.json_only:
        print("\n[3] Upserting to Supabase...")
        try:
            conn = get_db_connection()
            if upsert_to_supabase(conn, all_reports, args.verbose):
                print("  Supabase upsert complete")
            else:
                print("  Supabase upsert failed")
            conn.close()
        except Exception as e:
            print(f"  ERROR connecting to Supabase: {e}")

    print("\n" + "=" * 60)
    print("Export complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
