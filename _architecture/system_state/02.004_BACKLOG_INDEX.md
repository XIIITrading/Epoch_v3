# Backlog Index

**System**: XIII Trading LLC — All Business Systems
**Document Version**: 002
**Last Updated**: 2026-03-22

---

## Active (Currently Being Built)

| ID | Name | Module(s) | Complexity | Started |
|----|------|-----------|-----------|---------|
| 002 | Architecture Baseline Audit | All modules (00–15), _architecture/ | High (19 files, 4 batches) — Batch 1 DONE, Batches 2-4 remaining | 2026-03-21 |

## Ready (Spec'd, Awaiting Build)

| ID | Name | Module(s) | Complexity | Priority |
|----|------|-----------|-----------|----------|
| — | — | — | — | — |

## In Analysis (Claude Code Expanding)

| ID | Name | Module(s) | Status |
|----|------|-----------|--------|
| — | — | — | — |

## Seeds (Not Yet Analyzed)

| ID | Name | System Area | Priority Signal |
|----|------|-------------|-----------------|
| 001 | Base Ticker Universe | 01_application, 13_market_data | SUBSUMED — replaced by Seed 004 (infrastructure) + Seed 005 (ticker list) |
| 006 | Pre-Market Analysis Tool (Beta) | 01_application/pre_market_analysis_beta/ | HIGH — PyQt6 morning workflow app. Consumes Seed 004 data. Screener table + chart viewer + bucket monitor. Seed file: `_seeds/006-pre-market-analysis-beta.md`. **APPROVED** — ready for analysis. |

## Parked (Deliberately Deferred)

| ID | Name | Reason | Revisit Date |
|----|------|--------|--------------|
| — | — | — | — |

## Complete (2026 Q1)

| ID | Name | Completed | Outcome |
|----|------|-----------|---------|
| 003 | Screener Data Bucket Audit | 2026-03-22 | 45 calculations mapped to 4 buckets (35 EXISTS, 10 NEW). All 5 Supabase tables confirmed. Bucket assignments approved. Data contract for Seed 004. |
| 004 | Screener Pipeline Build — Phase 1 (Bucket Runners) | 2026-03-22 | 9 new files, 2 modified, 3 schema changes. Bucket A/B/C runners built and tested. 48 tickers processed successfully. Parallel options (4 workers). Exporter fixed (savepoints + dict format). 372 records in Supabase. |
| 005 | Universe Ticker List | 2026-03-22 | 48 tickers populated in `config/universe_tickers.txt`. Bucket runners use this as fallback. Supabase `screener_universe` table created. Formal criteria deferred — current list is Silva's daily click-through tickers. |
