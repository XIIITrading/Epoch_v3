# Edge Analysis

This command has been upgraded to a Skill. Use `/edge-analysis` to trigger it.

The skill auto-executes the Python analysis scripts and feeds the output to Claude for interpretation.

## Manual Run (if needed)
```bash
cd C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\edge_analysis_test
python run_all.py        # All steps
python run_all.py 1      # Step 1 only
```

## Results Location
`C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\edge_analysis_test\edge_analysis_results\`

## Skill Location
`.claude/skills/edge-analysis/SKILL.md`
