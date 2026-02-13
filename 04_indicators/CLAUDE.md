# 04_indicators - Indicator Edge Testing v1.0

## Module Overview

PyQt6-based edge testing framework for validating indicator effectiveness using M1 bar data. Tests statistical significance of various indicators against trade outcomes to identify actionable trading edges.

## Architecture

```
04_indicators/
├── app.py                       # Module launcher entry point
├── config.py                    # Module configuration
├── CLAUDE.md                    # AI context documentation
├── indicator_gui/
│   ├── __init__.py
│   ├── main.py                  # PyQt6 app entry point
│   ├── main_window.py           # Main window with terminal output
│   └── styles.py                # Dark theme stylesheet
├── scripts/
│   ├── __init__.py
│   └── run_edge_tests.py        # CLI edge test runner
├── edge_testing/
│   ├── __init__.py
│   ├── base_tester.py           # Database access, statistical tests
│   └── edge_tests.py            # Individual indicator test functions
└── results/                     # Generated markdown reports
```

## Entry Points

```bash
# Launch GUI (primary usage)
python 04_indicators/app.py

# CLI mode (for automation)
python 04_indicators/scripts/run_edge_tests.py
python 04_indicators/scripts/run_edge_tests.py --indicators candle_range,volume_delta
python 04_indicators/scripts/run_edge_tests.py --date-from 2026-01-01 --verbose
python 04_indicators/scripts/run_edge_tests.py --export results.md
```

## Indicators Tested

| Indicator | Tests | Data Source |
|-----------|-------|-------------|
| **Candle Range** | Threshold, Quintile, Absorption | M1 bar OHLC |
| **Volume Delta** | Sign, Alignment, Magnitude | m1_indicator_bars.vol_delta |
| **Volume ROC** | Category, Quintile | m1_indicator_bars.vol_roc |
| **CVD Slope** | Direction, Alignment | m1_indicator_bars.cvd_slope |
| **SMA Analysis** | Spread Direction, Price Position | m1_indicator_bars.sma9, sma21 |
| **Market Structure** | H1/M15/M5 Direction, MTF Alignment | entry_indicators |

## Data Flow

1. **Load Data**: Fetch trades joined with M1 indicator bars (prior bar to avoid look-ahead bias)
2. **Calculate Metrics**: Derive indicator-specific metrics (quintiles, alignment, categories)
3. **Run Statistical Tests**: Chi-square for categorical, Spearman for ordinal
4. **Evaluate Edges**: Check p-value < 0.05 AND effect size > 3pp
5. **Generate Reports**: Output to terminal and optional markdown export

## Statistical Test Criteria

An edge is validated when ALL conditions are met:
- **p-value < 0.05**: Statistically significant
- **Effect size > 3pp**: Practically significant (percentage point difference)
- **Confidence >= MEDIUM**: Minimum 30 trades per group (100+ for HIGH)

## Segments Tested

Each indicator is tested across multiple segments:
- **ALL**: All trades combined
- **LONG / SHORT**: By trade direction
- **CONTINUATION / REJECTION**: By trade type (EPCH1+3 vs EPCH2+4)
- **EPCH1, EPCH2, EPCH3, EPCH4**: Individual entry models

## Key Findings from V1 Testing

### Validated Edges (Strongest First)

| Indicator | Test | Segment | Effect Size |
|-----------|------|---------|-------------|
| Candle Range | Quintile | ALL | 28.7pp |
| H1 Structure | Direction | ALL | 39.7pp |
| CVD Slope | Category | SHORT | 27pp |
| Volume Delta | Magnitude | LONG | 20pp |
| SMA | Spread Direction | SHORT | 25pp |

### Universal Skip Filter
- **Absorption Zone**: Candle range < 0.12% = 33% WR (skip all trades)

### Paradoxical Findings
- MISALIGNED volume delta beats ALIGNED (5-21pp edge)
- NEUTRAL H1 structure beats BULL/BEAR
- Trading against order flow captures exhaustion/reversals

## Database Tables Used

### Input Tables
- `trades`: Trade records with entry times
- `m1_indicator_bars`: M1 bar snapshots with indicator values
- `entry_indicators`: Entry-time structure snapshots
- `stop_analysis`: Win/loss outcomes by stop type

### Join Logic
Entry at S15 uses PRIOR M1 bar to avoid look-ahead bias:
```sql
-- Entry at 09:35:15 -> use M1 bar at 09:34:00
(date_trunc('minute', entry_time) - INTERVAL '1 minute')::time AS prior_bar_time
```

## GUI Features

- **Indicator Selection**: Multi-select list with all 7 indicators
- **Filters**: Stop type, optional date range
- **Terminal Output**: Real-time progress with color coding
- **Progress Bar**: Tracks completion via `[X/N]` pattern
- **Export Option**: Generate markdown report

### Terminal Color Coding
- **GREEN** (#26a69a): Edge detected, success
- **RED** (#ef5350): Errors, failures
- **ORANGE** (#ff9800): Warnings, no edge, low data
- **GRAY** (#808080): Section dividers
- **WHITE** (#e8e8e8): Default output

## Configuration (config.py)

Key settings:
- `DB_CONFIG`: Supabase connection
- `P_VALUE_THRESHOLD`: 0.05 (statistical significance)
- `EFFECT_SIZE_THRESHOLD`: 3.0 (practical significance in pp)
- `MIN_SAMPLE_SIZE_HIGH`: 100 (HIGH confidence)
- `MIN_SAMPLE_SIZE_MEDIUM`: 30 (MEDIUM confidence)
- `INDICATORS`: Registry of all indicator tests
- `DEFAULT_INDICATOR_ORDER`: Strongest edges first

## Dependencies

- PyQt6 (GUI framework)
- psycopg2 (PostgreSQL)
- pandas (data manipulation)
- numpy (numerical operations)
- scipy (statistical tests)

## Development Notes

- Based on DOW AI / 03_backtest UI pattern
- Core logic from 08_base_tool/03_indicators
- Uses QProcess for subprocess management
- Progress tracking via stdout parsing
- Chi-square test for categorical variables
- Spearman correlation for ordinal quintiles
