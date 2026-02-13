# Progression Analysis (Bar-by-Bar)

## Metadata
- **Generated**: 2026-01-19 17:38:38
- **Stop Type**: m5_atr

## Overview
This analysis shows **average indicator values at each bar position** from bar -15 (earliest) to bar 0 (entry), segmented by WIN vs LOSS outcomes.

The detailed data is in `09_progression_analysis.json`. This summary highlights key patterns.

## How to Interpret
Compare the WIN progression to the LOSS progression for each model+direction:
- Where do they diverge?
- What indicator behavior separates winners from losers?

## Claude Analysis Instructions
Review the JSON data and identify:
1. At which bar position do WIN and LOSS trades begin to diverge?
2. What indicator patterns are present in winning trades but absent in losing trades?
3. Are there "early warning" signs at bar -10 or -5 that predict outcome?
4. Create a narrative description of "what a winning trade looks like" for each model+direction

## Key Questions for Each Model+Direction
For Continuation trades (EPCH1, EPCH3):
- Does vol_delta build in the trade direction as entry approaches?
- Does momentum accelerate (vol_roc increasing)?

For Rejection trades (EPCH2, EPCH4):
- Does vol_delta show absorption (shrinking) before flipping?
- Does vol_roc decrease (exhaustion) before entry?
