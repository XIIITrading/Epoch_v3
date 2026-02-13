"""
================================================================================
EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS
Full Analysis Pipeline
XIII Trading LLC
================================================================================

Master script that runs the complete analysis pipeline:
1. Creates analysis tables (if needed)
2. Calculates all analysis metrics
3. Exports Claude-readable prompt documents

Usage:
    # Run full pipeline with defaults
    python run_full_analysis.py

    # Specify stop type
    python run_full_analysis.py --stop-type zone_buffer

    # Skip table creation (tables already exist)
    python run_full_analysis.py --skip-create

    # Only export (skip calculations, use existing data)
    python run_full_analysis.py --export-only

================================================================================
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Get absolute paths
# Path structure: ramp_up_analysis/ -> secondary_processor/ -> 12_system_analysis/
_this_dir = Path(__file__).parent.resolve()
_system_analysis_dir = _this_dir.parent.parent  # 12_system_analysis (2 levels up)

# IMPORTANT: Both directories have an 'analysis/' folder, so path order matters!
# Python auto-adds script directory to sys.path[0], but we need to ensure:
# 1. _this_dir (ramp_up_analysis) is at position 0 for local analysis/exporters
# 2. _system_analysis_dir is in path for config/credentials imports

# First, add system_analysis dir if not present
if str(_system_analysis_dir) not in sys.path:
    sys.path.insert(1, str(_system_analysis_dir))  # Insert at position 1

# Ensure _this_dir is at position 0 (it may already be there due to Python's script behavior)
if sys.path[0] != str(_this_dir):
    # Remove it from current position if present
    if str(_this_dir) in sys.path:
        sys.path.remove(str(_this_dir))
    sys.path.insert(0, str(_this_dir))

# Import from parent config (WIN_CONDITION_CONFIG, DB_CONFIG)
# This works because we renamed local config.py to ramp_config.py
from config import WIN_CONDITION_CONFIG, DB_CONFIG

# Import from local modules (found in _this_dir/analysis/)
from analysis.run_analysis import run_all_analysis, create_tables
from exporters.prompt_exporter import export_all_prompts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_full_pipeline(
    stop_type: str = None,
    skip_create: bool = False,
    export_only: bool = False
) -> dict:
    """
    Run the complete analysis pipeline.

    Parameters:
        stop_type: Stop type for outcomes (default from config)
        skip_create: Skip table creation step
        export_only: Only run export, skip calculations

    Returns:
        Dict with pipeline results
    """
    if stop_type is None:
        stop_type = WIN_CONDITION_CONFIG['default_stop_type']

    start_time = datetime.now()
    results = {
        'stop_type': stop_type,
        'steps': {},
    }

    logger.info("=" * 70)
    logger.info("RAMP-UP INDICATOR ANALYSIS - FULL PIPELINE")
    logger.info(f"Stop Type: {stop_type}")
    logger.info("=" * 70)

    # Step 1: Create tables
    if not skip_create and not export_only:
        logger.info("\n[STEP 1] Creating analysis tables...")
        try:
            success = create_tables()
            results['steps']['create_tables'] = 'success' if success else 'failed'
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            results['steps']['create_tables'] = f'error: {e}'

    # Step 2: Run calculations
    if not export_only:
        logger.info("\n[STEP 2] Running analysis calculations...")
        try:
            calc_results = run_all_analysis(stop_type=stop_type)
            results['steps']['calculations'] = calc_results
        except Exception as e:
            logger.error(f"Calculations failed: {e}")
            results['steps']['calculations'] = f'error: {e}'

    # Step 3: Export prompts
    logger.info("\n[STEP 3] Exporting Claude-readable prompts...")
    try:
        exported = export_all_prompts(stop_type=stop_type)
        results['steps']['export'] = {
            'status': 'success',
            'files_exported': len(exported),
            'paths': exported,
        }
    except Exception as e:
        logger.error(f"Export failed: {e}")
        results['steps']['export'] = f'error: {e}'

    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    results['duration_seconds'] = duration

    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("=" * 70)

    # Print exported files
    if 'export' in results['steps'] and isinstance(results['steps']['export'], dict):
        logger.info("\nExported files for Claude review:")
        for path in results['steps']['export'].get('paths', []):
            logger.info(f"  - {path}")

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run full ramp-up indicator analysis pipeline'
    )
    parser.add_argument(
        '--stop-type',
        default=None,
        choices=list(WIN_CONDITION_CONFIG['stop_types'].keys()),
        help='Stop type for outcome data (default from config)'
    )
    parser.add_argument(
        '--skip-create',
        action='store_true',
        help='Skip table creation (tables already exist)'
    )
    parser.add_argument(
        '--export-only',
        action='store_true',
        help='Only export prompts (skip calculations)'
    )

    args = parser.parse_args()

    results = run_full_pipeline(
        stop_type=args.stop_type,
        skip_create=args.skip_create,
        export_only=args.export_only
    )

    # Check for errors
    has_errors = False
    for step, result in results.get('steps', {}).items():
        if isinstance(result, str) and result.startswith('error'):
            has_errors = True
        elif isinstance(result, dict) and result.get('status') == 'error':
            has_errors = True

    if has_errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
