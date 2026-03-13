# 01_Application Improvement Plan v2.0
## Mapped to Method System 1.0 (XIII.METHOD)

> **Generated**: 2026-03-11
> **Source Spec**: Epoch v3 Technical Reference v1.0
> **Method System**: XIII.METHOD 1.0
> **Current State**: 11 tabs, 6-stage pipeline, 51 Python files, ~16K lines

---

## Mapping Overview

The 01_application module currently serves **5 of the 15** Method System sections directly, with partial coverage of 2 more. This document maps every current tab to its Method bucket, identifies gaps, and defines improvements.

| Method Section | Code | Current Coverage | 01_App Tab(s) |
|---|---|---|---|
| Market Screener | .01 | **Full** | Pre-Market Scanner, Structure Screener |
| In-Play Identification | .02 | **Partial** | Dashboard (daily ticker selection) |
| Setup Analysis | .03 | **Full** | Market Screener, Bar Data, Raw Zones, Zone Results, Zone Analysis |
| Discord Posting | .04 | **Partial** | Dashboard (Discord export), discord_post.py |
| Social Media Posting | .05 | None | — |
| Entry Identifier | .06 | None | — |
| TradingView Tooling | .07 | **Partial** | TradingView Export tab |
| Entry Rules & Execution | .08 | None | — |
| Exit Strategy | .09 | None | — |
| Backtesting | .10 | None (lives in 03_backtest) | — |
| Indicator Analysis | .11 | None (lives in 04_indicators) | — |
| Trade Journal | .12 | None (lives in 08_journal) | — |
| Education Automation | .13 | None | — |
| Social Media Automation | .14 | None | — |
| System Improvement | .15 | None | — |

---

## Section 1: Market Screener | XIII.METHOD.01

### Current Tabs
- **Tab 1 — Pre-Market Scanner**: Two-phase scan (ATR/price/gap filter → overnight volume ranking)
- **Tab 2 — Structure Screener**: D1 market structure classification with composite scoring

### What Works
- Two-phase scanning with configurable universe (S&P 500, NASDAQ 100, DOW 30, Russell 2000, All US)
- 7-state structure classification (Bull, Bull Low, Bear, Bear High, Out Strong, Out Weak, Neutral)
- Composite scoring: Structure(30) + Alignment(20) + Gap(20) + RVOL(25) + Zone(10) = ~105 max
- Top 10 Bull/Bear shortlists
- Parallel processing with worker threads

### Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 1.1 | Improvement | High | **Scanner → Structure Pipeline** | Auto-feed scanner results into Structure Screener (currently manual re-entry) |
| 1.2 | Feature | High | **Sector/Industry Grouping** | Add sector rotation view — group scanner results by GICS sector to identify hot/cold sectors |
| 1.3 | Improvement | Normal | **Historical Scanner Persistence** | Save daily scan results to Supabase for trend analysis (which tickers appear repeatedly) |
| 1.4 | Improvement | Normal | **Structure Trend Tracking** | Track structure state changes over time — alert when tickers flip from Bear to Bull |
| 1.5 | Feature | Normal | **Custom Filter Profiles** | Save/load filter presets (e.g., "Momentum Play", "Reversal Candidates") |
| 1.6 | Bug | High | **Scanner Timeout Handling** | Improve error handling when Polygon rate limits hit during large universe scans |
| 1.7 | Improvement | Normal | **Relative Volume Baseline** | Make RVOL lookback period configurable (currently hardcoded) |

---

## Section 2: In-Play Ticker Identification | XIII.METHOD.02

### Current Coverage
- **Tab 4 — Dashboard**: Daily ticker selection form with Supabase persistence
- No formal in-play qualification rules beyond manual selection

### What's Missing
- No systematic "in-play" criteria — currently relies on user judgment from scanner output
- No scoring system for in-play qualification
- No session context (pre-market levels, expected catalysts)

### Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 2.1 | Feature | High | **In-Play Qualification Engine** | Define method-specific criteria: minimum gap %, minimum RVOL, structure alignment, proximity to key level. Auto-score each candidate. |
| 2.2 | Feature | High | **In-Play Dashboard Panel** | New panel in Dashboard showing qualified tickers with pass/fail criteria breakdown |
| 2.3 | Feature | Normal | **Session Context Builder** | For each in-play ticker: prior day close, overnight range, key level proximity, expected move (ATR), catalyst flag |
| 2.4 | Feature | Normal | **In-Play History** | Track daily in-play lists in Supabase — analyze which in-play criteria correlate with profitable days |
| 2.5 | Improvement | Normal | **Scanner → In-Play Flow** | One-click promote from scanner/structure results to in-play list with auto-population of context |

---

## Section 3: Setup Analysis | XIII.METHOD.03

### Current Tabs
- **Tab 3 — Market Screener**: Pipeline control (ticker input, anchor dates, market mode)
- **Tab 5 — Bar Data**: All technical data display (structure, OHLC, HVN, options, Camarilla)
- **Tab 6 — Raw Zones**: All zone candidates pre-filtering
- **Tab 7 — Zone Results**: Filtered zones with tier classification (T3/T2/T1)
- **Tab 8 — Zone Analysis**: Primary + Secondary setups with R:R

### Current Pipeline (6 Stages)
1. Market Structure (D1/H4/H1/M15)
2. Bar Data (OHLC, ATR, Camarilla)
3. HVN POC Identification (10 ranked by volume)
4. Zone Confluence Calculation
5. Zone Filtering & Tier Classification
6. Setup Analysis (Primary + Secondary)

### What Works
- Full 6-stage pipeline with well-defined zone scoring weights
- Multi-timeframe structure analysis with composite weighting
- ATR-based zone width calculation (ATR/2)
- Confluence scoring: Monthly(3.0), Weekly(2.0), Daily(1.0), Options(2.5), Cam Monthly(3.0), Cam Weekly(2.0), Structure D1(1.5), Structure H1(1.0)
- Tier system: T3 (L4/L5, institutional), T2 (L3), T1 (L1/L2)

### Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 3.1 | Improvement | Urgent | **Prior Day Value Area Integration** | Add prior day VAH/VAL/POC from volume profile to zone confluence calculation — this is a core method concept not yet in the pipeline |
| 3.2 | Improvement | High | **Zone Scoring Weight Tuning** | Current weights are static. Allow configuration via weights.py and track which weight configs produce highest backtest win rate |
| 3.3 | Feature | High | **Supply/Demand Zone Identification** | Distinct from HVN zones — identify classic supply/demand zones from impulsive moves with unfilled orders. Layer these as additional confluence |
| 3.4 | Improvement | High | **Anchor Date Intelligence** | Max Volume anchor resolver needs refinement — currently picks single highest volume day. Consider: rolling volume clusters, significant gap days, earnings dates |
| 3.5 | Improvement | Normal | **Zone Freshness Scoring** | Zones that have been tested (price touched) should be penalized vs untouched zones — requires tracking zone touch history |
| 3.6 | Feature | Normal | **Multi-Anchor Analysis** | Run pipeline with multiple anchor dates simultaneously and compare/merge zone outputs to find most persistent levels |
| 3.7 | Improvement | Normal | **Options Level Enhancement** | Currently top 10 by OI. Add: put/call ratio per level, gamma exposure estimation, expiry clustering |
| 3.8 | Bug | High | **End Timestamp Edge Cases** | Market mode cutoffs (Pre-Market: 09:00 ET, Post-Market: 15:00 ET) need validation for holidays and half-days |
| 3.9 | Improvement | Normal | **Bar Data Tab Usability** | Tab 5 is data-dense but lacks visual hierarchy. Add collapsible sections, highlight key levels, color-code by timeframe |
| 3.10 | Feature | Normal | **Zone Visualization Overlay** | Add inline mini-charts in Raw Zones and Zone Results tabs showing zone placement relative to price |
| 3.11 | Improvement | Normal | **Setup Target Logic** | Current target = next major level. Improve with: ATR-projected targets, prior session high/low, Fibonacci extensions |

---

## Section 4: Discord Posting | XIII.METHOD.04

### Current Coverage
- **Dashboard Tab**: Daily ticker selection with Discord export
- **generators/discord_post.py**: Discord formatting utilities

### Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 4.1 | Feature | High | **Structured Post Templates** | Define standard Discord post formats: Morning Watchlist, Trade Setup, In-Play Alert, End-of-Day Recap |
| 4.2 | Feature | High | **One-Click Discord Export** | From Zone Analysis tab, export formatted setup post (ticker, direction, zone, target, R:R, chart) directly to Discord |
| 4.3 | Improvement | Normal | **Webhook Integration** | Direct Discord webhook posting from app instead of clipboard copy |
| 4.4 | Feature | Normal | **Chart Attachment** | Auto-attach Pre-Market Report chart PNG to Discord posts |

---

## Section 5: Social Media Posting | XIII.METHOD.05

### Current Coverage
None in 01_application. Out of scope for core pipeline — covered by separate workflow.

---

## Section 6: Entry Identifier | XIII.METHOD.06

### Current Coverage
None in 01_application (lives conceptually in 03_backtest entry models EPCH1-4).

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 6.1 | Feature | High | **Real-Time Zone Alert** | When in Live mode, monitor price proximity to active zones and emit alerts (sound, desktop notification) when price enters a setup zone |
| 6.2 | Feature | Normal | **Entry Condition Checklist** | In Zone Analysis tab, add an interactive checklist for each setup: structure aligned?, volume confirming?, candle range OK?, indicator edges present? |
| 6.3 | Feature | Normal | **Signal Confidence Score** | Combine zone tier + structure alignment + indicator edge data into a single confidence % per setup |

---

## Section 7: TradingView Tooling | XIII.METHOD.07

### Current Tab
- **Tab 9 — TradingView Export**: PineScript_6 and PineScript_16 formatted data, click-to-copy

### What Works
- 21-column export table with all zone/setup data
- PineScript_6: `pri_high,pri_low,pri_target,sec_high,sec_low,sec_target`
- PineScript_16: Above + 10 POC levels
- Click-to-copy individual cells

### Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 7.1 | Improvement | High | **PineScript Indicator Sync** | Current export is copy-paste. Build direct TradingView webhook/API integration for auto-update |
| 7.2 | Feature | Normal | **Extended PineScript Format** | Add market structure levels (strong/weak per timeframe) to export for Pine overlay |
| 7.3 | Feature | Normal | **Multi-Ticker Batch Export** | Export all analyzed tickers in single clipboard action (currently per-ticker) |
| 7.4 | Improvement | Normal | **Export Validation** | Validate PineScript field formats before copy — catch NaN/None values that break Pine Script |

---

## Section 8: Entry Rules & Execution | XIII.METHOD.08

### Current Coverage
None in 01_application. Codified rules live in documentation only.

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 8.1 | Feature | Normal | **Position Size Calculator** | Dashboard has basic share sizing. Enhance with: account size input, risk % per trade, max sector exposure, correlation check |
| 8.2 | Feature | Normal | **Execution Checklist Tab** | Pre-trade checklist that gates trade execution: method criteria met, risk sized, stops placed, journal entry started |

---

## Section 9: Exit Strategy | XIII.METHOD.09

### Current Coverage
- Zone Analysis shows targets and R:R but no exit management.

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 9.1 | Feature | Normal | **Multi-Target Display** | Show R1 through R5 targets per setup (currently just single target) |
| 9.2 | Feature | Normal | **Partial Profit Levels** | Define scaling plan per setup: 50% at R1, 25% at R2, trail remaining |
| 9.3 | Feature | Low | **Dynamic Stop Visualization** | Show initial stop and ATR-trailing stop path on Pre-Market Report chart |

---

## Section 10: Backtesting | XIII.METHOD.10

### Current Coverage
None in 01_application (lives in 03_backtest).

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 10.1 | Feature | Normal | **Zone Performance Overlay** | In Zone Results tab, show historical win rate per zone tier from backtest data |
| 10.2 | Feature | Low | **Quick Backtest Trigger** | From Zone Analysis, trigger 03_backtest pipeline for selected ticker/setup |

---

## Section 11: Indicator Analysis | XIII.METHOD.11

### Current Coverage
None in 01_application (lives in 04_indicators).

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 11.1 | Feature | High | **Edge Indicators in Zone Analysis** | Pull indicator_edges.json into Zone Analysis tab. Show which indicator edges are active for each setup (e.g., "H1 Structure Aligned: +36pp") |
| 11.2 | Feature | Normal | **Indicator Overlay on Bar Data** | In Bar Data tab, show current indicator states per ticker (SMA alignment, CVD slope, volume delta, candle range) |

---

## Section 12: Trade Journal | XIII.METHOD.12

### Current Coverage
None in 01_application (lives in 08_journal).

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 12.1 | Feature | Normal | **Journal Quick-Entry** | From Zone Analysis, one-click create journal entry pre-populated with setup details (ticker, direction, zone, entry, stop, target) |

---

## Section 13: Education Automation | XIII.METHOD.13

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 13.1 | Feature | Normal | **Daily Analysis Export** | Auto-generate structured teaching document from pipeline results: "Here's what the system identified today and why" |

---

## Section 14: Social Media Automation | XIII.METHOD.14

Out of scope for 01_application.

---

## Section 15: System Improvement | XIII.METHOD.15

### Improvements (01_app touchpoints)

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| 15.1 | Feature | Normal | **Pipeline Performance Metrics** | Track pipeline run times per stage, API call counts, cache hit rates. Surface in Dashboard. |
| 15.2 | Feature | Normal | **Zone Accuracy Tracking** | After-the-fact: compare zone predictions to actual price action. Feed into weight tuning (3.2) |
| 15.3 | Improvement | Normal | **Error Reporting** | Centralized error logging with daily summary — currently errors are per-ticker in console |

---

## Cross-Cutting / Infrastructure Improvements

| # | Type | Priority | Improvement | Detail |
|---|---|---|---|---|
| X.1 | Improvement | Urgent | **Shared Infrastructure Migration** | Multiple imports still reference local `data/polygon_client.py` instead of `shared.data.polygon`. Complete migration to shared namespace. |
| X.2 | Improvement | High | **State Manager Cleanup** | `core/state_manager.py` appears to be Streamlit-era legacy. Remove or replace with proper PyQt state management. |
| X.3 | Improvement | High | **Cache Strategy** | `data/cache_manager.py` is file-based. Evaluate: TTL-based expiry, separate cache per analysis date, cache invalidation on market close. |
| X.4 | Improvement | Normal | **Tab Navigation** | 11 tabs is a lot. Consider: tab grouping (Scanning | Analysis | Export), or a sidebar navigation pattern. |
| X.5 | Improvement | Normal | **Keyboard Shortcuts** | Add hotkeys: Ctrl+R (run pipeline), Ctrl+1-9 (switch tabs), Ctrl+E (export), Ctrl+D (Discord post) |
| X.6 | Feature | Normal | **Session Persistence** | Save/restore last session: tickers, anchor dates, analysis date, market mode. Auto-load on startup. |
| X.7 | Improvement | Normal | **Dark Theme Polish** | Consistent styling across all tabs — some tables and widgets don't fully match the dark theme. |
| X.8 | Feature | Low | **Multi-Monitor Support** | Allow popping out individual tabs as separate windows for multi-monitor trading setups. |

---

## Priority Summary

| Priority | Count | Key Items |
|---|---|---|
| **Urgent** | 2 | Prior Day Value Area (3.1), Shared Import Migration (X.1) |
| **High** | 14 | Scanner→Structure flow (1.1), In-Play Engine (2.1/2.2), Zone weight tuning (3.2), Supply/Demand zones (3.3), Anchor intelligence (3.4), Discord templates (4.1/4.2), Zone alerts (6.1), PineScript sync (7.1), Edge indicators (11.1), Scanner errors (1.6), End timestamp bugs (3.8), State manager cleanup (X.2), Cache strategy (X.3) |
| **Normal** | 28 | Bulk of feature and improvement work |
| **Low** | 3 | Dynamic stop viz (9.3), Quick backtest (10.2), Multi-monitor (X.8) |

**Total Improvements: 47**

---

## Implementation Phases (Suggested)

### Phase 1 — Foundation (Week 1-2)
Fix infrastructure: X.1 (shared imports), X.2 (state manager), X.3 (cache), 3.8 (timestamp bugs), 1.6 (scanner errors)

### Phase 2 — Core Pipeline Enhancement (Week 3-4)
Upgrade the analytical engine: 3.1 (prior day value), 3.2 (weight tuning), 3.3 (supply/demand), 3.4 (anchor intelligence), 11.1 (edge indicators)

### Phase 3 — Workflow Automation (Week 5-6)
Streamline daily workflow: 1.1 (scanner→structure), 2.1/2.2 (in-play engine), 2.5 (scanner→in-play), 4.1/4.2 (Discord), 7.1 (PineScript sync)

### Phase 4 — Execution Support (Week 7-8)
Support live trading: 6.1 (zone alerts), 6.2 (entry checklist), 8.1 (position sizing), 9.1 (multi-target), 12.1 (journal quick-entry)

### Phase 5 — Polish & Measurement (Week 9-10)
Refine and track: 15.1 (metrics), 15.2 (accuracy tracking), X.4 (navigation), X.5 (shortcuts), X.6 (session persistence), X.7 (theme)

---

*This document should be reviewed section-by-section with the system operator to validate intent, adjust priorities, and add any missing improvements before Actions are created in Kairos.*
