# DOW AI v3.0 Workflow Guide
## Epoch Trading System - XIII Trading LLC

---

## Overview

DOW AI v3.0 uses Claude AI to predict trade outcomes by analyzing M1 bar data with backtested context. The system has two operational modes:

1. **Production Mode** (Weekly): Single-pass analysis using Pass 2 logic
2. **Validation Mode** (Monthly): Dual-pass analysis to validate and refine

---

## Architecture

```
02_dow_ai/
├── ai_context/                  # Backtested knowledge files
│   ├── indicator_edges.json     # +/- impact by indicator
│   ├── zone_performance.json    # Win rates by zone type
│   ├── model_stats.json         # Performance by model
│   └── prompt_v3.py            # Prompt builder
│
├── batch_analyzer/              # Batch processing
│   ├── scripts/
│   │   ├── batch_analyze_production.py  # Weekly production runs
│   │   ├── batch_analyze_v3.py          # Validation dual-pass runs
│   │   ├── run_monthly_validation.py    # Monthly validation wrapper
│   │   └── analyze_pass2_errors.py      # Error pattern analysis
│   └── data/
│       ├── trade_loader_v3.py
│       ├── prediction_storage.py        # -> ai_predictions table
│       └── dual_pass_storage.py         # -> dual_pass_analysis table
│
├── dow_analysis/                # PyQt6 GUI
│   └── main_window.py          # Supports Production/Validation modes
│
├── entry_qualifier/             # Live trading assistant
│   └── ai/
│       └── dual_pass_worker.py # Live dual-pass with user notes
│
└── docs/                        # This documentation
```

---

## Data Flow

### Production Mode (Weekly)

```
trades (Supabase)
       |
       v
+------------------+
| Production       |
| Analyzer         |
| (Pass 2 Only)    |
+------------------+
       |
       v
ai_predictions (Supabase)
       |
       v
Training Module (06_training)
```

**Purpose**: Generate AI predictions for the Training Module to study.

**Frequency**: Weekly (every Sunday or when new trades accumulate)

**Table**: `ai_predictions`

---

### Validation Mode (Monthly)

```
trades (Supabase)
       |
       v
+------------------+
| Validation       |
| Analyzer         |
| (Pass 1 + 2)     |
+------------------+
       |
       v
dual_pass_analysis (Supabase)
       |
       v
+------------------+
| Error Analysis   |
| Script           |
+------------------+
       |
       v
ai_context updates
```

**Purpose**: Validate Pass 2 accuracy and identify improvement areas.

**Frequency**: Monthly (after updating instructions)

**Table**: `dual_pass_analysis`

---

## Weekly Production Cycle

### Step 1: Run Production Analysis

Via GUI (dow_analysis):
1. Open DOW AI Analysis Tool
2. Select **Production (Pass 2 -> ai_predictions)**
3. Set batch size (50-100 recommended)
4. Click **Run Batch Analysis**

Via Command Line:
```bash
cd 02_dow_ai/batch_analyzer/scripts
python batch_analyze_production.py --limit 100 --save-results
```

### Step 2: Review Results

The console/output file shows:
- Trades processed
- Pass 2 accuracy
- API cost

Example output:
```
PASS 2 PERFORMANCE:
  TRADE Calls: 45 (45.0%)
  Correct Predictions: 66
  Accuracy: 66.0%

API USAGE:
  Input tokens: 450,000
  Output tokens: 15,000
  Estimated cost: $1.58
```

### Step 3: Update Training Module

The `ai_predictions` table now contains fresh predictions for flashcard review.

---

## Monthly Validation Cycle

### Step 1: Update Instructions (if needed)

Edit `ai_context/prompt_v3.py` to refine Pass 2 behavior based on:
- Error analysis from previous month
- New market insights
- Indicator edge updates

### Step 2: Run Validation

Via GUI:
1. Select **Validation (Dual-Pass -> dual_pass_analysis)**
2. Set batch to **500**
3. Click **Run Batch Analysis**

Via Command Line:
```bash
cd 02_dow_ai/batch_analyzer/scripts
python run_monthly_validation.py --trades 500
```

### Step 3: Analyze Errors

```bash
python analyze_pass2_errors.py --output monthly_errors.txt
```

This generates a report showing:
- Error rate by zone type, model, direction
- High-confidence errors (most concerning)
- Pass disagreement errors (where Pass 1 was right)
- Specific recommendations

### Step 4: Refine ai_context

Based on error analysis, update:

**indicator_edges.json** - Adjust edge values:
```json
{
  "H1_STRUCTURE": {
    "BULL": "+36pp when aligned with direction"
  }
}
```

**zone_performance.json** - Update zone expectations:
```json
{
  "ZONE_RECOVERY": {
    "win_rate": 0.58,
    "notes": "Best on M5 reversal patterns"
  }
}
```

### Step 5: Re-validate (Optional)

After updates, run a smaller validation (100 trades) to confirm improvement.

---

## Pass 1 vs Pass 2 Explained

### Pass 1: Trader's Eye

**What Claude sees**:
- Ticker, direction, entry price/time
- 15 M1 bars with all indicators
- No backtested context

**Purpose**: Baseline decision using only market data.

### Pass 2: System Decision

**What Claude sees**:
- Everything from Pass 1
- `indicator_edges.json` - Which indicators provide edge
- `zone_performance.json` - Historical zone win rates
- `model_stats.json` - Model-specific performance

**Purpose**: Authoritative recommendation using learned edges.

### Why Pass 2 Wins

From 390+ trades analyzed:
- Pass 1 accuracy: 56.4%
- Pass 2 accuracy: 64.1%
- When they disagree: Pass 2 correct 2:1

The backtested context consistently improves decisions.

---

## Cost Estimates

| Mode | Tokens/Trade | Cost/Trade | 100 Trades |
|------|--------------|------------|------------|
| Production | ~5,000 | ~$0.008 | ~$0.80 |
| Validation | ~10,000 | ~$0.016 | ~$1.60 |

Weekly production on 100 trades: ~$0.80
Monthly validation on 500 trades: ~$8.00

---

## Table Schemas

### ai_predictions

```sql
- trade_id (FK)
- prediction (TRADE/NO_TRADE)
- confidence (LOW/MEDIUM/HIGH)
- reasoning (text)
- candle_pct, candle_status
- vol_delta, vol_delta_status
- vol_roc, vol_roc_status
- sma, h1_struct
- model_used, prompt_version
- tokens_input, tokens_output
- processing_time_ms
- created_at
```

### dual_pass_analysis

```sql
- trade_id (PK)
- ticker, trade_date, direction, model, zone_type
- pass1_decision, pass1_confidence, pass1_reasoning
- pass1_tokens_input, pass1_tokens_output, pass1_latency_ms
- pass2_decision, pass2_confidence, pass2_reasoning
- pass2_tokens_input, pass2_tokens_output, pass2_latency_ms
- candle_pct, candle_status (from Pass 2)
- vol_delta, vol_delta_status
- vol_roc, vol_roc_status
- sma_spread, sma_status
- h1_structure, h1_status
- actual_outcome, actual_pnl_r
- pass1_correct, pass2_correct (computed)
- passes_agree, disagreement_winner (computed)
- prompt_version, model_used, analyzed_at
```

---

## Troubleshooting

### "No trades to process"

Check filters - may have already processed all trades. Use `--reprocess` to re-analyze.

### Rate limit errors

The scripts include automatic retry with 60-second wait. If persistent, reduce batch size.

### Low accuracy after updates

1. Run error analysis to identify specific patterns
2. Check if ai_context updates were too aggressive
3. Consider reverting to previous prompt version

### Database connection errors

Verify `batch_analyzer/config.py` has correct Supabase credentials.

---

## Quick Reference

### Production (Weekly)
```bash
python batch_analyze_production.py --limit 100 --save-results
```

### Validation (Monthly)
```bash
python run_monthly_validation.py --trades 500
```

### Error Analysis
```bash
python analyze_pass2_errors.py --output errors.txt
```

### Dry Run (Preview)
```bash
python batch_analyze_production.py --limit 50 --dry-run
```

---

## Version History

- **v3.0** (Jan 2026): Dual-pass architecture, production/validation split
- **v2.0**: Single-pass with backtested context
- **v1.0**: Basic AI predictions without learned edges

---

*Last Updated: January 27, 2026*
