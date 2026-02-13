# Streamlit Archive - Training Module

This directory contains the original Streamlit version of the training module,
preserved as a functional fallback before the PyQt6 migration.

## Usage
```bash
cd C:\XIIITradingSystems\Epoch\06_training
streamlit run _archive_streamlit/streamlit_app.py
```

## Files
- `streamlit_app.py` - Main Streamlit entry point
- `app_streamlit.py` - Original launcher (subprocess)
- `components/` - Streamlit UI components
- `data/cache_manager.py` - Original cache with st.session_state

## Note
The data layer (`data/supabase_client.py`, `data/polygon_client.py`),
models (`models/trade.py`), chart builders (`components/charts.py`,
`components/rampup_chart.py`), and config (`config.py`) are shared
with the PyQt6 version and remain in their original locations.
