# End-of-Week Epoch Analysis Protocol

> **Version**: 1.0
> **Created**: 2026-02-27
> **Purpose**: Generate weekly human-readable and AI-readable system snapshots for Epoch v3
> **Trigger**: `"Run eow_epoch_analysis.md"`

---

## How to Run

Tell Claude Code:
```
Run eow_epoch_analysis.md
```

Claude Code will read this file and execute the full protocol below.

---

## Execution Overview

This protocol produces **two documents** from a full traversal of `C:\XIIITradingSystems\Epoch_v3\`:

| Output | Local Path | Notion Properties |
|--------|-----------|-------------------|
| Executive Summary | `12_system_architecture/epoch_system_summary.md` | Business: XIII, Type: System Summary |
| Technical Reference | `12_system_architecture/epoch_technical_reference.md` | Business: XIII, Type: Technical Spec |

Both are published to the **Documents database** in Notion and saved locally. Each run overwrites the prior version. Git history provides the audit trail.

---

## Notion Configuration

### Documents Database
- **Database ID**: `2e7f98ca-811d-8081-aecc-d6bc56e9862c`
- **Data Source ID**: `2e7f98ca-811d-8034-88a8-000b125acc95`

### Page IDs (updated after each run)
- **Executive Summary Page**: `314f98ca-811d-8191-a989-ee8883aebbfb`
- **Technical Reference Page**: `314f98ca-811d-812d-8d68-de4622efcc3d`

> After the first run, Claude Code MUST update these Page IDs in this file so that subsequent runs overwrite the same Notion pages instead of creating duplicates.

### Property Values
```
Executive Summary:
  Title: "Epoch v3 — System Summary (v{VERSION})"
  Business: "XIII"
  Type: "System Summary"
  Version: {VERSION}

Technical Reference:
  Title: "Epoch v3 — Technical Reference (v{VERSION})"
  Business: "XIII"
  Type: "Technical Spec"
  Version: {VERSION}
```

---

## Versioning

- **Current Version**: 1.1
- Each weekly run increments by 0.1 (1.0 → 1.1 → 1.2 ...)
- Read the current version from this file's `Current Version` field
- After generating both documents, increment the version here
- Both output files include the version in their metadata header

---

## Context Window Management

### Codebase Scale
- **563 Python files** across **144,456 lines of code**
- This EXCEEDS a single context window — the analysis MUST be phased

### Conversation Phases

The full analysis is split into **3 conversation phases** based on module size and complexity:

| Phase | Modules | Est. Files | Est. Lines |
|-------|---------|-----------|------------|
| **Phase 1** | 00_shared, 01_application, 02_dow_ai, 03_backtest | 208 | 48,667 |
| **Phase 2** | 04_indicators, 05_system_analysis, 06_training | 220 | 63,192 |
| **Phase 3** | 08_journal, 09_results, 10_machine_learning, 11_trade_reel + Assembly & Publish | 115 | 29,854 |

> **07_market_analysis** has 0 Python files and is skipped (noted as empty in output).

### Handoff Protocol

At the END of each Phase (1 and 2), Claude Code MUST:

1. **Save progress** — Write a handoff file to `12_system_architecture/_analysis_handoff.md`
2. **Notify the user** with the following message:

---

> **CONVERSATION BREAK NEEDED**
>
> Phase {N} of 3 is complete. The analysis so far has been saved to:
> `12_system_architecture/_analysis_handoff.md`
>
> **Summary of what was completed:**
> {2-3 bullet points describing modules analyzed and key findings}
>
> **To continue, start a new conversation and say:**
> ```
> Continue eow_epoch_analysis.md — Phase {N+1}
> ```
>
> Claude Code will read the handoff file and pick up where we left off.

---

### Handoff File Format

The file `12_system_architecture/_analysis_handoff.md` is structured as:

```markdown
# EOW Analysis Handoff

## Status
- **Protocol**: eow_epoch_analysis.md
- **Version Being Generated**: {VERSION}
- **Current Phase**: {COMPLETED_PHASE} of 3
- **Next Phase**: {NEXT_PHASE}
- **Timestamp**: {ISO-8601}

## Completed Analysis

### Phase 1 Results (if complete)
{Raw analysis content for 00_shared, 01_application, 02_dow_ai, 03_backtest}

### Phase 2 Results (if complete)
{Raw analysis content for 04_indicators, 05_system_analysis, 06_training}

## Remaining Work
- Modules still to analyze: {list}
- After all phases: Assemble into final documents, publish to Notion
```

### Continuation Protocol

When Claude Code sees `"Continue eow_epoch_analysis.md — Phase {N}"`:
1. Read this instruction file (`eow_epoch_analysis.md`)
2. Read the handoff file (`_analysis_handoff.md`)
3. Continue from the specified phase
4. On Phase 3 completion: assemble both final documents and publish

---

## Phase 1: Core Infrastructure & Primary Modules

### Traversal Order

#### 1.1 — 00_shared (Core Infrastructure)
Analyze in this order:
1. `config/` — All configuration files, credential patterns, EpochConfig settings
2. `data/` — Polygon client (API patterns, timeframes, rate limiting), Supabase client (connection, query patterns)
3. `indicators/` — Every indicator: name, algorithm, parameters, output type, what trading question it answers
4. `ui/` — BaseWindow class, COLORS dict, DARK_STYLESHEET, common widget patterns
5. `models/` — All Pydantic models and their relationships
6. `utils/` — Utility functions

**Capture for each indicator:**
- Name and file path
- What it measures (plain English)
- Algorithm (pseudocode or formula)
- Parameters and defaults
- Output type (from `types.py`)
- What trading question it answers

#### 1.2 — 01_application (Main Trading App)
Analyze in this order:
1. `app.py` + `config.py` — Entry point, module configuration
2. `calculators/` — All 8 pipeline stages in sequence:
   - bar_data → hvn_identifier → anchor_resolver → market_structure
   - setup_analyzer → zone_calculator → zone_filter → scanner
3. `core/` — Data models, core calculations
4. `data/` — Data fetching layer
5. `generators/` — Analysis generators
6. `ui/` — UI components and layouts
7. `visualization_config.py` + `weights.py` — Chart config, zone scoring

**Capture**: Pipeline flow, zone calculation logic, scanner criteria, UI layout

#### 1.3 — 02_dow_ai (Claude Trading Assistant)
Analyze:
1. `app.py` — Entry point
2. Core AI integration (prompts, Claude API usage)
3. UI components
4. What questions it answers, how it processes context

#### 1.4 — 03_backtest (Trade Simulation)
Analyze:
1. `app.py` + `config.py`
2. Engine architecture (how trades are simulated)
3. All secondary processors (the 13 mentioned in CLAUDE.md)
4. Output tables and schema
5. Performance metrics calculated

**Save Phase 1 results to handoff file. Notify user of conversation break.**

---

## Phase 2: Analysis & Testing Modules

#### 2.1 — 04_indicators (Edge Testing Framework)
Analyze:
1. Which 7 indicators are tested
2. Testing methodology (how "edge" is measured)
3. Statistical methods used
4. Output format and reporting

#### 2.2 — 05_system_analysis (Statistical Analysis)
This is the largest module (140 files, 41K lines). Analyze:
1. `app.py` + `config.py` — Entry point, configuration
2. `data/provider.py` — DataProvider class, all queries
3. `questions/_base.py` — BaseQuestion interface
4. `questions/` — Every `q_*.py` file: question text, SQL query, visualization, export format
5. `ui/main_window.py` — Layout and interaction flow
6. Categorize all questions by category

#### 2.3 — 06_training (Interactive Training)
Analyze:
1. Training modes and flashcard system
2. What trading concepts are covered
3. UI and interaction patterns

**Save Phase 2 results to handoff file. Notify user of conversation break.**

---

## Phase 3: Remaining Modules + Assembly + Publish

#### 3.1 — 08_journal (Trade Review)
Analyze: Entry point, journaling workflow, data captured per trade

#### 3.2 — 09_results (Analysis Results Storage)
Analyze: Storage patterns, result formats (small module — 2 files)

#### 3.3 — 10_machine_learning (ML Analysis)
Analyze: ML models used, lifecycle tracking, feature engineering

#### 3.4 — 11_trade_reel (Video/Image Generation)
Analyze: Reel generation pipeline, output formats

#### 3.5 — 07_market_analysis (Historical Journals)
Note: Currently 0 Python files. Document as empty/pending module.

#### 3.6 — Assembly
Combine all phase results into the two final documents using the templates below.

#### 3.7 — Delta Detection
Compare the newly generated documents against the prior versions:
- If prior `epoch_system_summary.md` exists: diff for the "Recent Changes" section
- If no prior version: write "Initial baseline — no prior version to compare"
- Use git diff or content comparison to identify additions, removals, and modifications

#### 3.8 — Publish
1. Write `epoch_system_summary.md` to `12_system_architecture/`
2. Write `epoch_technical_reference.md` to `12_system_architecture/`
3. Create or update Notion pages (see Notion Configuration section)
4. Update this file: increment version, update Page IDs if first run
5. Delete `_analysis_handoff.md` (no longer needed)

---

## Output 1: Executive Summary Template

```markdown
# Epoch v3 — System Summary

> **Version**: {VERSION}
> **Generated**: {DATE}
> **Files Analyzed**: {COUNT}
> **Lines of Code**: {LOC}
> **Modules**: {MODULE_COUNT} active

---

## System Overview
{2-3 paragraphs: What Epoch v3 is, its purpose, who uses it, what problem it solves.
Written for a non-technical stakeholder who understands trading but not code.}

## Module Map

### 00_shared — Core Infrastructure
{2-3 sentences: What it provides, why it exists, what depends on it}

### 01_application — Trading Analysis
{2-3 sentences: What it does, the 8-stage pipeline concept, zone identification}

### 02_dow_ai — AI Trading Assistant
{2-3 sentences}

{... repeat for each module ...}

## Indicator Summary

| Indicator | What It Measures | Trading Question It Answers |
|-----------|-----------------|---------------------------|
| Volume Delta | ... | ... |
| Volume ROC | ... | ... |
| CVD | ... | ... |
| ATR | ... | ... |
| SMA | ... | ... |
| VWAP | ... | ... |
| Candle Range | ... | ... |
| Market Structure | ... | ... |

## Scanner Logic
{For each scanner: What it filters for, how candidates are ranked, what surfaces to the user}

## Data Flow
{How data moves through the system:
Sources (Polygon.io, Supabase) → Processing (indicators, pipeline) → Display (PyQt6) → Storage (Supabase export)}

## Recent Changes
{Delta from prior version. First run: "Initial baseline — no prior version."}

## Decision Log
{Key architectural decisions discovered in the codebase:
- Why centralized shared infrastructure
- Why PyQt6 over Streamlit
- Why module independence
- Any other decisions evident from code comments or structure}
```

---

## Output 2: Technical Reference Template

```markdown
# Epoch v3 — Technical Reference

> **Version**: {VERSION}
> **Generated**: {DATE}
> **Files Analyzed**: {COUNT}
> **Lines of Code**: {LOC}
> **Python Version**: {VERSION}
> **Key Dependencies**: PyQt6, pandas, numpy, plotly, kaleido, psycopg2, polygon-api-client, anthropic

---

## Directory Structure
{Full tree with purpose annotations — every folder, key files annotated}
```
Epoch_v3/
├── 00_shared/              # Centralized infrastructure
│   ├── config/             # Credentials, EpochConfig, market hours
│   ├── data/               # Polygon + Supabase clients
│   ├── indicators/         # 7 indicators + market structure
│   │   ├── config.py       # Indicator parameters
│   │   ├── types.py        # Result dataclasses
│   │   ├── core/           # Individual indicator implementations
│   │   └── structure/      # Market structure detection
│   ├── ui/                 # BaseWindow, COLORS, stylesheets
│   ├── models/             # Pydantic data models
│   └── utils/              # Common utilities
├── 01_application/         # Main trading app
│   ├── calculators/        # 8-stage zone pipeline
│   ...
{... complete tree ...}
```

## Module Deep-Dives

### 00_shared
**Entry Points**: N/A (library module)
**Dependencies**: polygon-api-client, psycopg2, pandas, numpy, PyQt6
**Config Keys**: POLYGON_API_KEY, SUPABASE_DB_CONFIG, ANTHROPIC_API_KEY
**Database Tables**: N/A (clients only)

#### Class Inventory
| Class/Function | File | Purpose |
|---------------|------|---------|
| PolygonClient | data/polygon/client.py | OHLCV data fetching |
| ... | ... | ... |

{... repeat for each module ...}

## Calculation Logic

### Volume Delta
**File**: `00_shared/indicators/core/volume_delta.py`
**Formula**: `delta = volume * (bar_position - 0.5)` where `bar_position = (close - low) / (high - low)`
**Parameters**: None
**Output**: `VolumeDeltaResult(delta, normalized_delta)`
**Edge Cases**: {any guards or special handling}

{... repeat for each indicator with exact formulas ...}

## Scanner Specifications
{For each scanner:
- Filter chain (step by step)
- Sort logic
- RVOL calculations
- Session comparisons
- Thresholds and cutoffs}

## Data Schema

### Supabase Tables
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| trades_m5_r_win_2 | Primary trade data | model, direction, is_winner, pnl_r, date |
| m1_indicator_bars_2 | Minute-level indicators | ticker, timestamp, {indicator columns} |
| ... | ... | ... |

### Query Patterns
{Common queries used across modules}

## Config Reference
| Parameter | Default | Valid Range | Affects |
|-----------|---------|-------------|---------|
| {key} | {value} | {range} | {what it changes} |
| ... | ... | ... | ... |

## Integration Points
{How modules call each other:
- Shared imports from 00_shared
- Data flow between backtest → system_analysis
- UI event flows
- Supabase as shared state layer}

## UI Component Map
| Widget | Module | Data Displayed | Refresh Trigger |
|--------|--------|---------------|-----------------|
| ... | ... | ... | ... |

## Recent Changes
{Delta from prior version. First run: "Initial baseline — no prior version."}
```

---

## Quality Checks

Before publishing, verify:
- [ ] Every module with Python files is covered
- [ ] Every indicator has a formula and plain-English description
- [ ] All Supabase tables discovered are documented
- [ ] The executive summary is readable by someone who understands trading but not code
- [ ] The technical reference has enough detail that Claude can answer "How does X work?" without reading source
- [ ] Version number is incremented from prior run
- [ ] Delta section reflects actual changes (or notes first run)
- [ ] Metadata header (file count, LOC) is accurate for this run

---

## Appendix: Quick Reference

### Run Commands
```
# Full run (starts Phase 1)
"Run eow_epoch_analysis.md"

# Continue from a specific phase
"Continue eow_epoch_analysis.md — Phase 2"
"Continue eow_epoch_analysis.md — Phase 3"
```

### File Locations
| File | Path |
|------|------|
| This protocol | `12_system_architecture/eow_epoch_analysis.md` |
| Executive Summary | `12_system_architecture/epoch_system_summary.md` |
| Technical Reference | `12_system_architecture/epoch_technical_reference.md` |
| Phase Handoff | `12_system_architecture/_analysis_handoff.md` |

### Notion Targets
| Document | Database | Data Source |
|----------|----------|-------------|
| Both outputs | `2e7f98ca-811d-8081-aecc-d6bc56e9862c` | `2e7f98ca-811d-8034-88a8-000b125acc95` |
