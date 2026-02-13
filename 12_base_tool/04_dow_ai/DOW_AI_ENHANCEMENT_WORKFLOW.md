# DOW AI Enhancement Workflow
## Systematic Approach to Building Smarter Trading Prompts

**Version:** 1.0
**Created:** January 20, 2026
**Status:** Implementation Ready

---

## Executive Summary

This document provides a systematic workflow for continuously enhancing DOW AI prompts using validated data from the Epoch trading system. The workflow connects three primary data sources:

1. **Validated Indicator Edges** (`03_indicators/python`) - Statistical edge testing results
2. **Historical Trade Performance** (Supabase) - Win rates, MFE/MAE, health scores
3. **Real-Time Analysis Data** (Polygon + Supabase) - Current market conditions

---

## Part 1: Current State Analysis

### What DOW AI Currently Receives

```
ENTRY PROMPT (130 lines, 24+ parameters)
├── Trade Request (ticker, direction, zone type)
├── Zone Data (from Supabase: zones, setups tables)
├── Price-to-Zone Relationship (calculated)
├── Model Classification (EPCH_01-04, auto-calculated)
├── Market Structure (H4, H1, M15, M5 from Polygon)
├── Volume Analysis (M1/M5/M15 delta, ROC, CVD)
├── Candlestick Patterns (detected)
├── Supporting Levels (ATR, HVN POCs, Camarilla)
├── SMA Analysis (M5/M15 alignment, spread)
└── VWAP Analysis (session VWAP vs price)
```

### What DOW AI is Missing

| Category | Missing Data | Source Available |
|----------|-------------|------------------|
| **Historical Context** | Model win rates, typical MFE/MAE | `trades`, `mfe_mae_potential` |
| **Indicator Edges** | Validated thresholds, paradoxical findings | `03_indicators/python/results/` |
| **Zone Quality** | Historical success rate, test count | `zones`, `trades` (joined) |
| **Stop Optimization** | Best stop type for this model | `stop_analysis` |
| **Health Baseline** | What health score typically wins | `entry_indicators` |
| **Time-to-Target** | Expected duration by model | `optimal_trade` |

---

## Part 2: Supabase Integration Architecture

### New AI Context Tables

Create these tables to aggregate validated data for prompt injection:

#### Table 1: `ai_model_stats`
```sql
-- Aggregated performance metrics by EPCH model
CREATE TABLE ai_model_stats (
    model VARCHAR(10) PRIMARY KEY,  -- EPCH1, EPCH2, EPCH3, EPCH4
    total_trades INTEGER,
    win_rate DECIMAL(5,2),
    avg_mfe_r DECIMAL(5,2),
    avg_mae_r DECIMAL(5,2),
    avg_time_to_mfe_minutes INTEGER,
    avg_time_to_target_minutes INTEGER,
    best_stop_type VARCHAR(20),
    best_stop_win_rate DECIMAL(5,2),
    avg_health_score_winners DECIMAL(3,1),
    avg_health_score_losers DECIMAL(3,1),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table 2: `ai_indicator_edges`
```sql
-- Validated indicator thresholds from weekly testing
CREATE TABLE ai_indicator_edges (
    indicator VARCHAR(30) PRIMARY KEY,
    direction VARCHAR(10),           -- LONG, SHORT, ALL
    trade_type VARCHAR(15),          -- CONTINUATION, REJECTION, ALL
    threshold_value VARCHAR(50),     -- e.g., ">= 0.15%", "POSITIVE"
    baseline_win_rate DECIMAL(5,2),
    edge_win_rate DECIMAL(5,2),
    effect_size_pp DECIMAL(5,2),     -- percentage points
    confidence VARCHAR(10),          -- HIGH, MEDIUM, LOW
    p_value DECIMAL(8,6),
    sample_size INTEGER,
    validation_date DATE,
    notes TEXT
);
```

#### Table 3: `ai_zone_performance`
```sql
-- Historical zone performance for quality assessment
CREATE TABLE ai_zone_performance (
    zone_rank VARCHAR(5),            -- L1-L5
    total_trades INTEGER,
    win_rate DECIMAL(5,2),
    avg_mfe_r DECIMAL(5,2),
    avg_bounce_pct DECIMAL(5,2),     -- Average price bounce from zone
    avg_hold_duration_minutes INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table 4: `ai_prompt_history`
```sql
-- Track prompt versions and their effectiveness
CREATE TABLE ai_prompt_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_version VARCHAR(20),
    prompt_type VARCHAR(20),         -- entry, exit
    prompt_hash VARCHAR(64),         -- SHA256 of prompt template
    deployed_at TIMESTAMPTZ,
    trades_analyzed INTEGER,
    recommendation_accuracy DECIMAL(5,2),
    avg_confidence_score DECIMAL(3,1),
    notes TEXT
);
```

#### Table 5: `ai_recommendations`
```sql
-- Log all DOW AI recommendations for feedback loop
CREATE TABLE ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id VARCHAR(50),            -- Link to trades table if trade taken
    analysis_time TIMESTAMPTZ,
    ticker VARCHAR(10),
    direction VARCHAR(10),
    zone_type VARCHAR(15),
    model_code VARCHAR(10),
    confidence VARCHAR(10),          -- HIGH, MEDIUM, LOW
    recommendation VARCHAR(50),      -- TAKE_TRADE, WAIT, SKIP
    entry_triggers TEXT,
    invalidation_levels TEXT,
    user_action VARCHAR(20),         -- TAKEN, SKIPPED, MODIFIED
    outcome VARCHAR(20),             -- WIN, LOSS, BREAKEVEN, PENDING
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Part 3: Data Population Scripts

### Script 1: Populate Model Stats (Weekly)

```python
# File: 04_dow_ai/scripts/populate_model_stats.py
"""
Run weekly after backtest completion.
Aggregates trade performance by EPCH model.
"""

QUERY = """
INSERT INTO ai_model_stats (
    model, total_trades, win_rate, avg_mfe_r, avg_mae_r,
    avg_time_to_mfe_minutes, best_stop_type, best_stop_win_rate,
    avg_health_score_winners, avg_health_score_losers
)
SELECT
    t.model,
    COUNT(*) as total_trades,
    AVG(CASE WHEN t.is_winner THEN 1 ELSE 0 END) * 100 as win_rate,
    AVG(m.mfe_r_potential) as avg_mfe_r,
    AVG(m.mae_r_potential) as avg_mae_r,
    AVG(EXTRACT(EPOCH FROM (m.mfe_potential_time - t.entry_time))/60) as avg_time_to_mfe_minutes,
    (SELECT stop_type FROM stop_analysis sa
     WHERE sa.model = t.model
     GROUP BY stop_type
     ORDER BY AVG(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) DESC
     LIMIT 1) as best_stop_type,
    (SELECT MAX(avg_wr) FROM (
        SELECT AVG(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as avg_wr
        FROM stop_analysis sa WHERE sa.model = t.model GROUP BY stop_type
    ) x) as best_stop_win_rate,
    AVG(CASE WHEN t.is_winner THEN e.health_score END) as avg_health_score_winners,
    AVG(CASE WHEN NOT t.is_winner THEN e.health_score END) as avg_health_score_losers
FROM trades t
LEFT JOIN mfe_mae_potential m ON t.trade_id = m.trade_id
LEFT JOIN entry_indicators e ON t.trade_id = e.trade_id
GROUP BY t.model
ON CONFLICT (model) DO UPDATE SET
    total_trades = EXCLUDED.total_trades,
    win_rate = EXCLUDED.win_rate,
    avg_mfe_r = EXCLUDED.avg_mfe_r,
    avg_mae_r = EXCLUDED.avg_mae_r,
    avg_time_to_mfe_minutes = EXCLUDED.avg_time_to_mfe_minutes,
    best_stop_type = EXCLUDED.best_stop_type,
    best_stop_win_rate = EXCLUDED.best_stop_win_rate,
    avg_health_score_winners = EXCLUDED.avg_health_score_winners,
    avg_health_score_losers = EXCLUDED.avg_health_score_losers,
    updated_at = NOW();
"""
```

### Script 2: Populate Indicator Edges (After Validation)

```python
# File: 04_dow_ai/scripts/populate_indicator_edges.py
"""
Run after each indicator validation session.
Parses edge test results and inserts into database.
"""

INDICATOR_EDGES = [
    # From candle_range_edge_20260117.md
    {
        "indicator": "candle_range_absorption",
        "direction": "ALL",
        "trade_type": "ALL",
        "threshold_value": "< 0.12%",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 33.3,
        "effect_size_pp": -11.1,
        "confidence": "HIGH",
        "sample_size": 2788,
        "notes": "SKIP FILTER - Always skip entries with absorption bars"
    },
    {
        "indicator": "candle_range_minimum",
        "direction": "ALL",
        "trade_type": "ALL",
        "threshold_value": ">= 0.15%",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 54.2,
        "effect_size_pp": 9.8,
        "confidence": "HIGH",
        "sample_size": 2788,
        "notes": "Primary entry threshold"
    },
    # From vol_delta_edge_20260116.md
    {
        "indicator": "vol_delta_short",
        "direction": "SHORT",
        "trade_type": "ALL",
        "threshold_value": "POSITIVE",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 50.7,
        "effect_size_pp": 10.7,
        "confidence": "HIGH",
        "sample_size": 1200,
        "notes": "PARADOX: Positive delta wins for SHORT (exhausted buyers)"
    },
    {
        "indicator": "vol_delta_long_magnitude",
        "direction": "LONG",
        "trade_type": "ALL",
        "threshold_value": "Q4-Q5 (top 40%)",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 57.0,
        "effect_size_pp": 20.0,
        "confidence": "HIGH",
        "sample_size": 1100,
        "notes": "Magnitude matters for LONG"
    },
    # From structure_edge_20260117.md
    {
        "indicator": "h1_structure",
        "direction": "ALL",
        "trade_type": "ALL",
        "threshold_value": "NEUTRAL",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 52.9,
        "effect_size_pp": 39.7,
        "confidence": "HIGH",
        "sample_size": 2757,
        "notes": "PARADOX: NEUTRAL H1 beats ALIGNED (53% vs 20%)"
    },
    {
        "indicator": "cvd_slope_short",
        "direction": "SHORT",
        "trade_type": "ALL",
        "threshold_value": "POSITIVE/EXTREME_POS",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 62.0,
        "effect_size_pp": 21.0,
        "confidence": "HIGH",
        "sample_size": 600,
        "notes": "PARADOX: Positive CVD wins for SHORT"
    },
    {
        "indicator": "sma_config_short",
        "direction": "SHORT",
        "trade_type": "ALL",
        "threshold_value": "BULLISH",
        "baseline_win_rate": 44.4,
        "edge_win_rate": 53.0,
        "effect_size_pp": 14.1,
        "confidence": "HIGH",
        "sample_size": 800,
        "notes": "PARADOX: Bullish SMA config wins for SHORT (failed rally)"
    },
]
```

---

## Part 4: Enhanced Prompt Templates

### New Prompt Sections to Add

#### Section A: Historical Model Performance
```python
HISTORICAL_PERFORMANCE_SECTION = """
## HISTORICAL MODEL PERFORMANCE ({model_code})

Based on {total_trades} historical trades:
- Win Rate: {win_rate}%
- Average MFE: {avg_mfe_r}R (in your favor before stop)
- Average MAE: {avg_mae_r}R (against you before recovery)
- Time to MFE: ~{avg_time_to_mfe} minutes
- Best Stop Type: {best_stop_type} ({best_stop_win_rate}% win rate)
- Health Score: Winners avg {health_winners}, Losers avg {health_losers}

⚠️ If current health score < {health_threshold}, PROCEED WITH CAUTION
"""
```

#### Section B: Validated Indicator Edges
```python
INDICATOR_EDGES_SECTION = """
## VALIDATED INDICATOR EDGES (2,788 trades, HIGH confidence)

CRITICAL FILTERS:
✗ Candle Range < 0.12% → SKIP (33% WR, -11pp penalty)
✓ Candle Range ≥ 0.15% → PROCEED (54% WR, +10pp edge)

{direction}-SPECIFIC SIGNALS:
{direction_specific_edges}

PARADOXICAL FINDINGS (Validated):
{paradox_list}

CURRENT ALIGNMENT:
{current_alignment_status}
"""
```

#### Section C: Zone Quality Assessment
```python
ZONE_QUALITY_SECTION = """
## ZONE QUALITY ASSESSMENT

This zone is ranked {zone_rank}:
- Historical win rate for {zone_rank} zones: {rank_win_rate}%
- Average bounce: {avg_bounce}%
- Zone score: {zone_score} (confluences: {confluences})

{quality_recommendation}
"""
```

### Modified `build_entry_prompt()` Function

```python
def build_entry_prompt(
    # ... existing parameters ...
    # NEW PARAMETERS:
    model_stats: dict = None,        # From ai_model_stats
    indicator_edges: list = None,    # From ai_indicator_edges
    zone_quality: dict = None,       # From ai_zone_performance
) -> str:
    """
    Enhanced entry prompt with historical context and validated edges.
    """

    # Build existing sections...

    # NEW: Add historical performance section
    if model_stats:
        historical_section = HISTORICAL_PERFORMANCE_SECTION.format(
            model_code=model_code,
            total_trades=model_stats['total_trades'],
            win_rate=model_stats['win_rate'],
            avg_mfe_r=model_stats['avg_mfe_r'],
            avg_mae_r=model_stats['avg_mae_r'],
            avg_time_to_mfe=model_stats['avg_time_to_mfe_minutes'],
            best_stop_type=model_stats['best_stop_type'],
            best_stop_win_rate=model_stats['best_stop_win_rate'],
            health_winners=model_stats['avg_health_score_winners'],
            health_losers=model_stats['avg_health_score_losers'],
            health_threshold=model_stats['avg_health_score_losers'] + 1
        )

    # NEW: Add indicator edges section
    if indicator_edges:
        edges_section = build_indicator_edges_section(
            direction=direction,
            trade_type=trade_type,
            indicator_edges=indicator_edges,
            current_indicators=current_indicators
        )

    # NEW: Add zone quality section
    if zone_quality:
        zone_section = ZONE_QUALITY_SECTION.format(
            zone_rank=zone['rank'],
            rank_win_rate=zone_quality['win_rate'],
            avg_bounce=zone_quality['avg_bounce_pct'],
            zone_score=zone['score'],
            confluences=zone['confluences'],
            quality_recommendation=get_quality_recommendation(zone_quality)
        )

    # Combine all sections into final prompt
    return final_prompt
```

---

## Part 5: Systematic Enhancement Workflow

### Daily Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MORNING (Before Market Open)                               │
│  ├── 1. Run zone system pipeline (02_zone_system)           │
│  ├── 2. Export zones to Supabase (13_database_export)       │
│  └── 3. DOW AI reads zones from Supabase (already active)   │
│                                                             │
│  DURING TRADING                                             │
│  ├── 4. Use DOW AI for entry/exit analysis                  │
│  ├── 5. Log recommendations to ai_recommendations table     │
│  └── 6. Track user_action (TAKEN/SKIPPED)                   │
│                                                             │
│  AFTER MARKET CLOSE                                         │
│  ├── 7. Run backtest on day's trades (09_backtest)          │
│  ├── 8. Run secondary processor (09_backtest/processor)     │
│  └── 9. Update ai_recommendations with outcomes             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Weekly Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    WEEKLY WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FRIDAY EVENING / SATURDAY                                  │
│  ├── 1. Run indicator edge validation (03_indicators/python)│
│  │   └── python candle_range/candle_range_edge.py           │
│  │   └── python volume_delta/vol_delta_edge.py              │
│  │   └── python structure_edge/structure_edge.py            │
│  │   └── ... (all 7 indicator modules)                      │
│  │                                                          │
│  ├── 2. Review edge test results in results/ folders        │
│  │                                                          │
│  ├── 3. Update ai_indicator_edges table                     │
│  │   └── python scripts/populate_indicator_edges.py         │
│  │                                                          │
│  ├── 4. Update ai_model_stats table                         │
│  │   └── python scripts/populate_model_stats.py             │
│  │                                                          │
│  ├── 5. Review recommendation accuracy                      │
│  │   └── Compare ai_recommendations to trade outcomes       │
│  │                                                          │
│  └── 6. Identify prompt improvements                        │
│      └── Adjust thresholds based on new edge data           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Monthly Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                   MONTHLY WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  END OF MONTH                                               │
│  ├── 1. Run full system analysis (12_system_analysis)       │
│  │   └── Review CALC-001 through CALC-011 metrics           │
│  │                                                          │
│  ├── 2. Compare prompt versions in ai_prompt_history        │
│  │   └── Measure recommendation_accuracy by version         │
│  │                                                          │
│  ├── 3. Update zone performance metrics                     │
│  │   └── python scripts/populate_zone_performance.py        │
│  │                                                          │
│  ├── 4. Review HOLD indicators (e.g., VWAP)                 │
│  │   └── Determine if enough data to VALIDATE or REJECT     │
│  │                                                          │
│  └── 5. Version and deploy prompt improvements              │
│      └── Update entry_prompt.py with new sections           │
│      └── Log to ai_prompt_history                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 6: Claude Desktop Integration

### Framework for Claude Desktop

Create a structured context document that Claude Desktop can reference:

```markdown
# EPOCH TRADING SYSTEM - Claude Desktop Reference

## System Overview
Epoch is an institutional-grade trading system that identifies high-probability
zones based on volume profile analysis and multi-timeframe confluence scoring.

## Entry Models (4 Types)
- **EPCH1**: Primary Zone Continuation (WITH zone direction)
- **EPCH2**: Primary Zone Rejection (AGAINST zone direction)
- **EPCH3**: Secondary Zone Continuation (WITH zone direction)
- **EPCH4**: Secondary Zone Rejection (AGAINST zone direction)

## Validated Indicator Edges

### Universal Filters (Apply to ALL trades)
| Filter | Threshold | Action | Effect |
|--------|-----------|--------|--------|
| Candle Range | < 0.12% | SKIP | -11pp |
| Candle Range | ≥ 0.15% | PROCEED | +10pp |

### LONG-Specific Edges
| Indicator | Condition | Win Rate | Edge |
|-----------|-----------|----------|------|
| Vol Delta Magnitude | Q4-Q5 | 57% | +20pp |
| H1 Structure | NEUTRAL | 53% | +40pp |
| Volume ROC | ≥ 30% | 52% | +8pp |

### SHORT-Specific Edges (Note Paradoxes)
| Indicator | Condition | Win Rate | Edge | Notes |
|-----------|-----------|----------|------|-------|
| Vol Delta Sign | POSITIVE | 51% | +11pp | Exhausted buyers |
| CVD Slope | POSITIVE | 62% | +21pp | Exhausted buying |
| SMA Config | BULLISH | 53% | +14pp | Failed rally setup |
| H1 Structure | NEUTRAL | 53% | +40pp | Transition zone |

## 10-Factor Health Score

| Factor | Points | Healthy Condition |
|--------|--------|-------------------|
| H4 Structure | 1 | Aligned with direction |
| H1 Structure | 1 | Aligned with direction |
| M15 Structure | 1 | Aligned with direction |
| M5 Structure | 1 | Aligned with direction |
| Volume ROC | 1 | > +20% vs 20-bar avg |
| Volume Delta | 1 | Positive (LONG) / Negative (SHORT) |
| CVD Direction | 1 | Rising (LONG) / Falling (SHORT) |
| SMA Alignment | 1 | SMA9 > SMA21 (LONG) / inverse |
| SMA Spread | 1 | WIDENING |
| VWAP Location | 1 | Above (LONG) / Below (SHORT) |

**Health Score Interpretation:**
- 8-10: STRONG (high probability)
- 6-7: MODERATE (proceed with confirmation)
- 4-5: WEAK (additional confirmation required)
- 0-3: CRITICAL (likely skip)

## Zone Ranking System

| Rank | Score | Win Rate | Recommendation |
|------|-------|----------|----------------|
| L5 | ≥ 12.0 | ~55% | BEST - High priority |
| L4 | ≥ 9.0 | ~50% | GOOD - Standard entry |
| L3 | ≥ 6.0 | ~45% | MODERATE - Needs confirmation |
| L2 | ≥ 3.0 | ~40% | LOW - Extra caution |
| L1 | < 3.0 | ~35% | WORST - Often skip |

## Stop Type Performance

| Stop Type | Win Rate | Best For |
|-----------|----------|----------|
| Zone Buffer (+5%) | 45% | All models |
| Prior M5 H/L | 48% | EPCH1/EPCH3 |
| M5 ATR (1.1x) | 46% | Volatile tickers |
| Fractal | 44% | EPCH2/EPCH4 |

## Key Paradoxes to Remember

1. **NEUTRAL H1 > ALIGNED H1**: Counter-intuitive but validated
   - NEUTRAL = transition zone, less crowded
   - ALIGNED = often at extended levels

2. **SHORT + POSITIVE signals**: Exhaustion setup
   - Positive volume delta = buyers exhausted
   - Positive CVD slope = buying exhausted
   - Bullish SMA = failed rally opportunity

3. **MISALIGNED often wins**: Entering against recent flow
   - Captures reversal/exhaustion points
   - Works for both LONG and SHORT

## Analysis Workflow

When analyzing a trade setup:

1. **Check Universal Filters**
   - Candle range ≥ 0.15%? If not, SKIP

2. **Apply Direction-Specific Edges**
   - LONG: Check vol delta magnitude (Q4-Q5)
   - SHORT: Check vol delta sign (want POSITIVE)

3. **Evaluate Structure**
   - NEUTRAL H1 is optimal
   - ALIGNED with trend is actually worse

4. **Calculate Health Score**
   - Score 8+ = Strong
   - Score 6-7 = Moderate
   - Score < 6 = Caution

5. **Consider Zone Quality**
   - L5/L4 = Proceed
   - L3 = Need extra confirmation
   - L1/L2 = Often skip

6. **Formulate Recommendation**
   - Include confidence level
   - Specify entry triggers
   - Define invalidation levels
```

### How to Use with Claude Desktop

1. **Save the above as a Project file** in Claude Desktop
2. **Reference it in conversations** about trading setups
3. **Ask Claude to apply the framework** when analyzing:
   - "Given this setup, apply the Epoch edge filters..."
   - "What paradoxes should I watch for on this SHORT?"
   - "Calculate the health score for this entry..."

---

## Part 7: Implementation Roadmap

### Phase 1: Database Setup (Week 1)

- [ ] Create `ai_model_stats` table in Supabase
- [ ] Create `ai_indicator_edges` table in Supabase
- [ ] Create `ai_zone_performance` table in Supabase
- [ ] Create `ai_recommendations` table in Supabase
- [ ] Create `ai_prompt_history` table in Supabase

### Phase 2: Population Scripts (Week 2)

- [ ] Write `populate_model_stats.py`
- [ ] Write `populate_indicator_edges.py`
- [ ] Write `populate_zone_performance.py`
- [ ] Initial data population from existing trades

### Phase 3: Prompt Enhancement (Week 3)

- [ ] Add historical performance section to entry prompt
- [ ] Add indicator edges section to entry prompt
- [ ] Add zone quality section to entry prompt
- [ ] Create helper function `fetch_ai_context()`

### Phase 4: Aggregator Integration (Week 4)

- [ ] Modify `AnalysisAggregator` to fetch from AI context tables
- [ ] Add AI context parameters to `build_entry_prompt()`
- [ ] Test enhanced prompts with sample trades
- [ ] Deploy to production

### Phase 5: Feedback Loop (Ongoing)

- [ ] Implement recommendation logging
- [ ] Create weekly review dashboard
- [ ] Track prompt version performance
- [ ] Continuous edge refinement

---

## Part 8: File Locations Reference

### DOW AI Core Files
```
C:\XIIITradingSystems\Epoch\04_dow_ai\
├── analysis/
│   ├── aggregator.py        # Main orchestrator - MODIFY
│   ├── prompts/
│   │   ├── entry_prompt.py  # Entry template - MODIFY
│   │   └── exit_prompt.py   # Exit template - MODIFY
│   └── claude_client.py     # Claude API client
├── data/
│   ├── supabase_reader.py   # Database reader - ACTIVE
│   └── polygon_fetcher.py   # Market data
├── scripts/                 # NEW DIRECTORY
│   ├── populate_model_stats.py
│   ├── populate_indicator_edges.py
│   └── populate_zone_performance.py
└── config.py                # Configuration
```

### Indicator Validation Files
```
C:\XIIITradingSystems\Epoch\03_indicators\python\
├── config.py                # All thresholds
├── combined_signal_summary.md  # Aggregated findings
├── Indicator_Validation_Pipeline.md  # Full methodology
├── candle_range/results/    # Edge test results
├── volume_delta/results/    # Edge test results
├── volume_roc/results/      # Edge test results
├── cvd_slope/results/       # Edge test results
├── sma_edge/results/        # Edge test results
├── structure_edge/results/  # Edge test results
└── vwap_simple/results/     # Edge test results
```

### Database Schemas
```
C:\XIIITradingSystems\Epoch\02_zone_system\
├── 13_database_export\schema\  # Core tables
└── 09_backtest\processor\secondary_analysis\
    ├── entry_indicators\schema\
    ├── mfe_mae\schema\
    ├── stop_analysis\schema\
    └── indicator_refinement\schema\
```

---

## Summary

This workflow provides a systematic approach to continuously enhance DOW AI:

1. **Connect to validated data** through new AI context tables
2. **Inject historical context** into prompts (model performance, edges, quality)
3. **Track recommendations** for feedback loop optimization
4. **Weekly refinement** based on new edge testing results
5. **Monthly reviews** of prompt effectiveness

The key insight is that DOW AI becomes smarter not by changing the AI, but by giving it better context. The validated edges from 2,788 trades represent real statistical advantages that Claude can apply to new setups.

**Next Steps:**
1. Create the AI context tables in Supabase
2. Write the population scripts
3. Modify `entry_prompt.py` with new sections
4. Test with sample trades
5. Deploy and monitor
