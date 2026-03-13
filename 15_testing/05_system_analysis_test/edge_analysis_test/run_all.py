"""
Edge Analysis Runner
====================
Runs all analysis steps in sequence and outputs results to edge_analysis_results/.

Usage:
    python run_all.py          # Run all steps
    python run_all.py 1        # Run step 1 only
    python run_all.py 1 2 3    # Run steps 1, 2, and 3

Steps:
    1 - Selection Edge Analysis (Tier A/B/C comparison)
    2 - Zone Quality vs Outcomes (TBD)
    3 - Market Structure vs Outcomes (TBD)
    4 - Bar Data Characteristics vs Outcomes (TBD)
    5 - Ticker Frequency Analysis (TBD)
    6 - Synthesis & Screening Criteria (TBD)
"""
import sys
import time

# Registry of available steps
STEPS = {
    1: ('Selection Edge Analysis', 'step1_selection_edge'),
    # 2: ('Zone Quality vs Outcomes', 'step2_zone_quality'),
    # 3: ('Market Structure vs Outcomes', 'step3_market_structure'),
    # 4: ('Bar Data Characteristics', 'step4_bar_data'),
    # 5: ('Ticker Frequency Analysis', 'step5_ticker_frequency'),
    # 6: ('Synthesis & Screening Criteria', 'step6_synthesis'),
}


def run_step(step_num: int):
    """Run a single analysis step."""
    if step_num not in STEPS:
        print(f'Step {step_num} not yet implemented.')
        return

    name, module_name = STEPS[step_num]
    print(f'\n{"=" * 80}')
    print(f'RUNNING STEP {step_num}: {name}')
    print(f'{"=" * 80}\n')

    start = time.time()
    module = __import__(module_name)
    module.run()
    elapsed = time.time() - start

    print(f'\n[Step {step_num} completed in {elapsed:.1f}s]')


def main():
    if len(sys.argv) > 1:
        steps = [int(s) for s in sys.argv[1:]]
    else:
        steps = sorted(STEPS.keys())

    print('Edge Analysis Suite')
    print(f'Running steps: {steps}')

    total_start = time.time()
    for step in steps:
        run_step(step)
    total_elapsed = time.time() - total_start

    print(f'\n{"=" * 80}')
    print(f'ALL STEPS COMPLETE ({total_elapsed:.1f}s total)')
    print(f'Results written to: edge_analysis_results/')
    print(f'{"=" * 80}')


if __name__ == '__main__':
    main()
