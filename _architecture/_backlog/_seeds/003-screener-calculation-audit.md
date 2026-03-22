# Screener Data Bucket Audit & Workflow Definition

**Seed ID**: 003
**Created**: 2026-03-21
**Status**: Seed — Not Yet Analyzed

---

## The Idea (What + Why)

Perform a full read-only audit of every calculation the system currently produces across
`bar_data`, `hvn_pocs`, `market_structure`, `zones`, and `setups`. Map each confirmed field
to one of four time-based execution buckets (Weekly, Nightly, Morning Session, Real-Time).
Identify gaps where desired data points do not yet have an implementation. The output becomes
the authoritative data contract and bucket workflow document that all screener pipeline work
depends on.

## Trigger (What Made You Think of This)

Designing the 50-ticker intelligent screener requires knowing exactly what is already computed
before anything new can be specced. The architecture docs (`DATA_FLOW.md`) describe `bar_data`
as "~70 fields" by category only — the actual column list, calculation logic, and bucket
assignments are only knowable by reading the codebase and querying the live schema directly.
Without this audit, any screener spec would be guesswork.

## System Area

- `01_application/` — primary source of all zone pipeline calculations
- `00_shared/indicators/` — shared indicator calculation library
- `bar_data` Supabase table — ~70-field schema to be enumerated
- `hvn_pocs`, `market_structure`, `zones`, `setups` Supabase tables
- `_architecture/DATA_FLOW.md` — to be updated with confirmed field list on completion

## Desired Outcome

A single completed markdown document (`003_screener-bucket-audit.md` in `_backlog/_analysis/`)
that contains:

1. **Full field inventory** — every column in `bar_data`, `hvn_pocs`, `market_structure`,
   `zones`, and `setups`, confirmed from both the codebase and live Supabase schema
2. **Bucket assignment** for each field across the four execution windows:

   | Bucket | Window | Trigger |
   |--------|--------|---------|
   | A — Weekly | Saturday / Sunday | Friday close universe refresh |
   | B — Nightly | After 20:00 ET | Post-session, prior to next trading day |
   | C — Morning Session | 07:00 – 08:00 ET | Pre-market data available |
   | D — Real-Time | 09:30 – 16:00 ET | Live session polling |

3. **Gap list** — every data point discussed in the screener ideation session
   (see session context below) that has no existing implementation, with a plain-English
   description of what would need to be built
4. **Confirmed existing fields** mapped to their source file/function in the codebase

When this document exists, Seed 004 (screener pipeline build) can be written and specced
without ambiguity.

## Session Context (Desired Data Points Discussed)

The following were identified during the screener ideation session as desired inputs.
Claude Code should confirm status (EXISTS / PARTIAL / NEW) for each during the audit:

### Bucket A — Weekly
- Monthly (M1) OHLC levels — prior and current period
- Weekly (W1) OHLC levels — prior and current period
- W1 and M1 market structure direction (BOS/CHoCH on weekly/monthly bars)
- ATR across all timeframes (M1 through D1)
- SMA 9 / SMA 21
- 50-ticker universe selection (new — no current batch logic)
- Epoch anchor auto-detection: nearest high volume day ≥ 20% above all others
  within prior 6 months (currently manual — needs automation rule)

### Bucket B — Nightly
- Daily (D1) OHLC — prior day H/L/O/C
- Camarilla Pivots next day (S3/S4/S6, R3/R4/R6)
- Options OI levels (op_01 through op_10)
- PDV POC / VAH / VAL (prior day volume profile)
- HVN POC calculations (Top 10, anchored from high volume epoch date)
- VbP Profile anchored from auto-detected high volume date
- Current D1 High / Low / Open (live trading day)
- Current W1 High / Open / Low
- Zone confluence scoring (60+ levels, bucket-max, L1–L5, T1–T3)
- Primary / Secondary zone setup generation (direction, targets, R:R)

### Bucket C — Morning Session (07:00–08:00 ET)
- Pre-Market High (PMH)
- Pre-Market Low (PML)
- Pre-Market Value Area High (PMVAH)
- Pre-Market Value Area Low (PMVAL)
- Pre-Market Point of Control (PMPOC)
- Current Price at 07:30 ET
- HVN POCs (query from prior night batch)
- Primary / Secondary zone levels (query from prior night batch)
- Market structure levels (query from prior night batch)
- Camarilla pivots (query from prior night batch)

### Bucket D — Real-Time
- Candle Range %
- Volume Delta (5-bar rolling)
- Volume Rate of Change (vs 20-bar trailing average)
- SMA Configuration (SMA9 vs SMA21 spread, momentum direction)
- H1 Market Structure (cached, refreshed hourly)
- LONG / SHORT composite scores (0–7)

## Priority Signal

**HIGH** — This audit directly blocks Seed 004 (screener pipeline build) and the broader
50-ticker intelligent screener. Nothing downstream can be specced without it.

## Constraints

- **Read-only**: No code changes, no schema modifications, no new tables during this task
- **Two source checks required**: Codebase AND live Supabase schema query
  (`information_schema.columns WHERE table_name = 'bar_data'`) — both must be confirmed
  before any field is marked EXISTS
- **Must not assume**: If a field is not found in both sources, mark as UNCLEAR and flag
  for Silva to resolve — do not infer from category descriptions in DATA_FLOW.md
- **Output format**: Single markdown file only — no PLAN.md, no DECISIONS.md, no code
- **Depends on**: Access to `C:\XIIITradingSystems\Method_v1\` codebase and live Supabase

## Monday.com Item

*(Leave blank — to be added when seed is approved and item is created)*

---

*Seed template per `_architecture/IDEA_INTAKE_WORKFLOW.md` — Phase 1 (20% seed only).*
*Phase 2 analysis to be generated by Claude Code when directed.*