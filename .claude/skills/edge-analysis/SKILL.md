---
name: edge-analysis
description: Run the Screener Performance Audit — analyzes backtest data to determine if ticker screening and selection criteria predict trade outcomes. Use when asked to run edge analysis, check screener performance, or analyze selection edge.
allowed-tools: Bash(python *), Bash(cd *), Read
---

# Edge Analysis — Screener Performance Audit

## Auto-Run Analysis

Execute the analysis scripts and capture the output:

!`cd C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\edge_analysis_test && python run_all.py`

## Your Task

You just ran the edge analysis suite. Now:

1. **Read the results files** from `C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\edge_analysis_test\edge_analysis_results\` — read each `.md` file produced

2. **Summarize key findings** for the user in a clear, concise format:
   - Lead with the headline number: overall win rate and the Tier A → B → C edge progression
   - Highlight the same-day tier comparison (Section 6) — this is the apples-to-apples answer
   - Call out "Your Picks vs What You Skipped" (Section 7) — this shows selection judgment quality

3. **Flag actionable insights**, for example:
   - Entry hours with dramatically different win rates (15:00 is historically terrible)
   - Models that consistently outperform (EPCH1 vs EPCH4)
   - Zone types that show edge (SECONDARY vs PRIMARY)
   - Index vs Custom performance gap
   - Specific tickers that are consistent winners or losers

4. **Flag data quality issues**:
   - How many overlapping days exist between Tier C selections and backtest data?
   - Are there tickers with very few trades (low confidence)?
   - Any dates with anomalous results?

5. **Recommend next steps**:
   - If Tier C data is thin, recommend the user keep saving daily selections to build the dataset
   - Suggest which Step 2-6 analysis to run next based on findings
   - Identify follow-up Actions for the Kairos board

## Context

### Three-Tier Comparison
- **Tier A** — Full Universe: all trades in `trades_m5_r_win_2` (the system running on everything)
- **Tier B** — Your 10 Custom Picks: non-index tickers (SPY/QQQ/DIA excluded) that went through the zone pipeline
- **Tier C** — Your Final 4: tickers saved via Dashboard export to `ticker_analysis` table
- **Index** — SPY/QQQ/DIA (automatic, always included)

### Key Question
Does A → B show edge (does your screening add value)? Does B → C show MORE edge (does your down-selection improve results)? Or are you over-filtering?

### Notion Action Page
If the user wants findings written to Notion: https://www.notion.so/320f98ca811d81a6a3aec7cd4b3f8848

### Available Steps
| Step | Script | Location | Question |
|------|--------|----------|----------|
| 1 | `step1_selection_edge.py` | `edge_analysis_test/` | Do your selected tickers show edge? |
| 2 | `step2_zone_quality.py` | `data_journal_test/` | Do T3 zones outperform T1? |
| 3 | `step3_market_structure.py` | `data_journal_test/` | Does structure alignment predict outcomes? |
| 4 | `step4_bar_data.py` | `data_journal_test/` | Do ATR/price/gap characteristics matter? |

### Related Skills
- `/data-journal` — Run Steps 2-4 (objective zone/structure/bar data analysis)
- `/user-journal` — Daily selection Q&A + aggregate subjective analysis
