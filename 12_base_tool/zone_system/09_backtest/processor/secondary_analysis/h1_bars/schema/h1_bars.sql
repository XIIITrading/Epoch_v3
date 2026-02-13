-- H1 Bars Schema
-- 1-hour bars for market structure analysis in training module
-- Stores 30+ H1 bars before market open for each ticker-date

CREATE TABLE IF NOT EXISTS h1_bars (
    ticker VARCHAR(10) NOT NULL,
    bar_date DATE NOT NULL,
    bar_time TIME WITHOUT TIME ZONE NOT NULL,
    bar_timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap NUMERIC(12, 4),
    transactions INTEGER,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT h1_bars_pkey PRIMARY KEY (ticker, bar_timestamp)
) TABLESPACE pg_default;

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_h1_bars_ticker_date
    ON h1_bars USING btree (ticker, bar_date) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_h1_bars_date
    ON h1_bars USING btree (bar_date) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_h1_bars_ticker
    ON h1_bars USING btree (ticker) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_h1_bars_ticker_date_time
    ON h1_bars USING btree (ticker, bar_date, bar_time) TABLESPACE pg_default;

-- Comment
COMMENT ON TABLE h1_bars IS 'Pre-fetched 1-hour bars for H1 market structure analysis in training module. Stores ~30 H1 bars before market open plus trading day bars.';
