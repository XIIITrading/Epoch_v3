# EPOCH Code Review Prompt

## Context

You are reviewing code from the EPOCH 2.0 Trading System. The system is built with:
- Python 3.10+
- PyQt6 for desktop GUI
- PostgreSQL (Supabase) for data storage
- Polygon.io for market data
- psycopg2 for database access
- pandas for data manipulation

## System Architecture

- **00_shared/**: Centralized infrastructure (credentials, data clients, indicators, UI)
- **01_application/**: Zone analysis (pre-market)
- **02_dow_ai/**: AI trading assistant
- **03_backtest/**: Trade simulation with secondary processors
- **04_indicators/**: Statistical edge testing
- **05_system_analysis/**: Analytics dashboard
- **10_machine_learning/**: Claude integration hub (this module)

## Review Criteria

### 1. Correctness
- Does the code use `trades_m5_r_win.is_winner` for outcomes (not `trades.is_winner`)?
- Are indicator calculations using the correct thresholds from config?
- Are SQL queries parameterized (not string-formatted)?
- Are edge cases handled (empty results, None values, division by zero)?

### 2. Architecture
- Does it follow the shared import pattern (`from shared.xxx import ...`)?
- Is configuration centralized (not hardcoded values)?
- Does it maintain module independence?
- Are there unnecessary dependencies between modules?

### 3. Performance
- Are database queries efficient (proper JOINs, WHERE clauses)?
- Is data loaded once and reused (not re-queried)?
- Are there N+1 query patterns?
- Could any operations be batched?

### 4. Data Integrity
- Is the canonical win condition used consistently?
- Are date ranges handled correctly?
- Are timezone issues addressed?
- Is data validated before processing?

### 5. Error Handling
- Are database connections properly closed (try/finally)?
- Are file operations wrapped in error handlers?
- Are meaningful error messages provided?
- Is there graceful degradation?

## Output Format

1. **Summary**: Overall assessment (1-2 sentences)
2. **Critical Issues**: Must-fix items (correctness, data integrity)
3. **Improvements**: Recommended changes (performance, architecture)
4. **Style Notes**: Minor suggestions (naming, formatting)
5. **Positive Observations**: What the code does well

---

*Paste code for review below this line*
