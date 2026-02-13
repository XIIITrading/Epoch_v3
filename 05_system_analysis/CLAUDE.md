# 05_system_analysis - AI Context

## Module Purpose
Comprehensive Streamlit dashboard for analyzing trading indicator performance across EPCH1-4 entry models. Provides statistical analysis, Monte Carlo simulations, and AI-powered insights for system refinement.

## Running the Application
```bash
cd C:\XIIITradingSystems\Epoch\05_system_analysis
streamlit run app.py --server.port 8502
```

## Architecture

### Main Entry Point
- `app.py` - Streamlit application with 5 major analysis tabs

### Data Layer
- `data/supabase_client.py` - PostgreSQL client for all database queries
- `credentials.py` - Database and API credentials
- `config.py` - Module configuration and constants

### UI Components (`components/`)
- `filters.py` - Date range, model, ticker, direction filters
- `summary_cards.py` - Metric display cards
- `charts.py` - Plotly chart rendering (MFE/MAE, win rates, etc.)
- `indicator_charts.py` - Indicator-specific visualizations
- `options_charts.py` - Options analysis charts
- `prompt_generator.py` - Claude prompt generation for analysis

### Analysis Modules (`analysis/`)
- `trade_stats.py` - Trade statistics calculations
- `indicator_stats.py` - Indicator performance metrics
- `model_comparison.py` - EPCH1-4 model comparisons

### Calculations (`calculations/`)
Organized by calculation type (CALC-001 through CALC-010):

- `model/` - Win rate by model (CALC-001)
- `trade_management/` - MFE/MAE stats and sequences (CALC-002, CALC-003)
- `indicators/` - Individual indicator calculations (VWAP, SMA, Volume)
- `structure/` - Market structure analysis (M5, M15, H1, H4)
- `health/` - Health score calculations
- `stop_analysis/` - Stop type analysis (CALC-009)
- `indicator_analysis/` - Health correlation, factor importance
- `indicator_refinement/` - Continuation/rejection scores (CALC-010)
- `indicator_edge/` - Edge testing framework
- `epch_indicators/` - EPCH-specific indicator tests
- `options/` - Options analysis calculations

### Monte AI (`monte_ai/`)
Claude-powered analysis and prompt generation:
- `prompts.py` - Base prompt templates
- `indicator_prompts.py` - Indicator-specific prompts
- `options_prompts.py` - Options analysis prompts
- `refinement_prompts.py` - System refinement prompts
- `data_collector.py` - Data aggregation for AI analysis
- `ui.py` - Monte AI UI components

### Secondary Processors (`secondary_processor/`)
Batch analysis tools:
- `ramp_up_analysis/` - Ramp-up pattern analysis
- Additional batch processors for extended analysis

## Key Data Tables (Supabase)
- `trades` - Base trade records
- `mfe_mae_potential` - MFE/MAE from entry to 15:30 ET
- `optimal_trade` - Trade events (ENTRY, MFE, MAE, EXIT, R-level crossings)
- `entry_indicators` - Indicator snapshots at entry
- `m5_trade_bars` - 5-minute bar progression
- `stop_analysis` - Pre-calculated stop outcomes by type
- `indicator_refinement` - Continuation/rejection scores
- `op_mfe_mae_potential` - Options MFE/MAE data

## Analysis Tabs
1. **Metrics Overview** - Win rates, model comparison, MFE/MAE distributions
2. **Options Analysis** - Options vs underlying performance
3. **Indicator Analysis** - Individual indicator edge testing
4. **EPCH Indicators** - Entry model specific analysis
5. **Archive** - Historical analysis reports

## Configuration
All configuration in `config.py`:
- `ENTRY_MODELS` - EPCH1-4 definitions
- `HEALTH_CONFIG` - Health score weights and thresholds
- `CHART_CONFIG` - Dark theme colors
- `WIN_CONDITION_CONFIG` - Stop type definitions

## Dependencies
- streamlit
- pandas
- plotly
- psycopg2
- python-dotenv
