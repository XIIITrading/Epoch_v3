---
name: data-journal
description: Run objective data journal analysis — zone quality, market structure, and bar data characteristics vs trade outcomes. Use when asked to run data journal, zone analysis, structure analysis, or bar data analysis.
allowed-tools: Bash(python *), Bash(cd *), Read
---

# Data Journal — Objective Performance Analysis

## Auto-Run Analysis

Execute the data journal analysis scripts:

!`cd C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\data_journal_test && python run_all.py`

## Your Task

You just ran the data journal analysis suite (Steps 2-4). Now:

1. **Read the results files** from `C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\data_journal_test\data_journal_results\` — read each `.md` file produced

2. **Summarize key findings per step:**

   **Step 2 — Zone Quality:**
   - Do T3 zones win more than T1? What's the pp difference?
   - Is there a score/overlap threshold below which zones should be filtered?
   - Do options or Camarilla confluences add measurable edge?

   **Step 3 — Market Structure:**
   - Does ALIGNED vs COUNTER show significant WR difference?
   - Which direction + model combination is the sweet spot?
   - Does setup R:R predict actual R achieved?
   - Primary vs Secondary — which adds more value?

   **Step 4 — Bar Data:**
   - Is there an ATR sweet spot for ticker selection?
   - Does overnight gap size help or hurt?
   - Price range performance differences?
   - Which characteristics should become screener filters?

3. **Cross-reference with edge analysis** (Step 1 results if available):
   - Were your winning picks in better zones (higher tier, more confluence)?
   - Were your winning picks structurally aligned?
   - Do your picks have a distinct bar data profile vs skipped tickers?

4. **Produce actionable screening criteria:**
   - List specific thresholds that predict edge (e.g., "T3 zones + ALIGNED = +8pp")
   - Flag metrics worth adding to the screener persistence layer
   - Identify filters that would have caught bad picks (like HIMS)

5. **Recommend next steps** and follow-up Actions for the Kairos board

## Available Steps

| Step | Script | Question |
|------|--------|----------|
| 2 | `step2_zone_quality.py` | Do T3 zones outperform T1? |
| 3 | `step3_market_structure.py` | Does structure alignment predict outcomes? |
| 4 | `step4_bar_data.py` | Do ATR/price/gap characteristics matter? |

Run individual steps: `python run_all.py 2` or `python run_all.py 3 4`
