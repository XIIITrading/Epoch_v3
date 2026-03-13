"""
Data Journal Analysis Runner
==============================
Runs objective analysis steps (zone quality, structure, bar data) and
outputs results to data_journal_results/.

Usage:
    python run_all.py          # Run all steps
    python run_all.py 2        # Run step 2 only
    python run_all.py 2 3 4    # Run steps 2, 3, and 4

Steps:
    2 - Zone Quality vs Outcomes
    3 - Market Structure vs Outcomes
    4 - Bar Data Characteristics vs Outcomes
"""
import sys
import time

STEPS = {
    2: ('Zone Quality vs Outcomes', 'step2_zone_quality'),
    3: ('Market Structure vs Outcomes', 'step3_market_structure'),
    4: ('Bar Data Characteristics vs Outcomes', 'step4_bar_data'),
}


def run_step(step_num: int):
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

    print('Data Journal Analysis Suite')
    print(f'Running steps: {steps}')

    total_start = time.time()
    for step in steps:
        run_step(step)
    total_elapsed = time.time() - total_start

    print(f'\n{"=" * 80}')
    print(f'ALL STEPS COMPLETE ({total_elapsed:.1f}s total)')
    print(f'Results written to: data_journal_results/')
    print(f'{"=" * 80}')


if __name__ == '__main__':
    main()
