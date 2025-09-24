-- DeFi Sample Dataset: Processed Data Layer
-- These tables represent the "silver" layer - cleaned and enriched data

CREATE SCHEMA IF NOT EXISTS DEFI_SAMPLE_DB.PROCESSED;

-- Cryptocurrency metadata (dynamic table)
CREATE OR REPLACE DYNAMIC TABLE DEFI_SAMPLE_DB.PROCESSED.COIN_INFO(
    type,
    coin_type,
    coin_decimals,
    coin_name,
    coin_symbol
)
TARGET_LAG = '1 hour'
REFRESH_MODE = INCREMENTAL
INITIALIZE = ON_CREATE
WAREHOUSE = COMPUTE_WH
COMMENT = 'Dynamic table containing cryptocurrency metadata, refreshes hourly from object changes'
AS
SELECT
    type,
    SPLIT_PART(SPLIT_PART(type, '<', 2), '>', 1) AS coin_type,
    object_json:decimals::INTEGER AS coin_decimals,
    object_json:name::STRING AS coin_name,
    object_json:symbol::STRING AS coin_symbol
FROM DEFI_SAMPLE_DB.RAW.OBJECT_CHANGES
WHERE
    type LIKE '0x2::coin::CoinMetadata%'
    AND object_json:decimals IS NOT NULL
QUALIFY RANK() OVER (PARTITION BY type ORDER BY version DESC) = 1;

-- Main fact table: processed DEX trades
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE
CLUSTER BY (timestamp_ms, protocol) (
    protocol VARCHAR(50) COMMENT 'DEX protocol name',
    timestamp_ms NUMBER(38,0) COMMENT 'Trade execution timestamp in milliseconds',
    transaction_digest VARCHAR(66) COMMENT 'Unique transaction identifier',
    event_index NUMBER(38,0) COMMENT 'Event position within transaction',
    epoch NUMBER(38,0) COMMENT 'Blockchain epoch when trade occurred',
    checkpoint NUMBER(38,0) COMMENT 'Blockchain checkpoint reference',
    pool_id VARCHAR(66) COMMENT 'Trading pool identifier',
    sender VARCHAR(66) COMMENT 'Address that initiated the trade',

    -- Input token details
    coin_in VARCHAR(200) COMMENT 'Input token type identifier',
    amount_in NUMBER(38,0) COMMENT 'Raw input amount (before decimal adjustment)',
    coin_in_name VARCHAR(100) COMMENT 'Input token name',
    coin_in_symbol VARCHAR(20) COMMENT 'Input token symbol',
    coin_in_decimals NUMBER(38,0) COMMENT 'Input token decimal places',
    adjusted_amount_in FLOAT COMMENT 'Decimal-adjusted input amount',

    -- Output token details
    coin_out VARCHAR(200) COMMENT 'Output token type identifier',
    amount_out NUMBER(38,0) COMMENT 'Raw output amount (before decimal adjustment)',
    coin_out_name VARCHAR(100) COMMENT 'Output token name',
    coin_out_symbol VARCHAR(20) COMMENT 'Output token symbol',
    coin_out_decimals NUMBER(38,0) COMMENT 'Output token decimal places',
    adjusted_amount_out FLOAT COMMENT 'Decimal-adjusted output amount',

    -- Trade metadata
    a_to_b BOOLEAN COMMENT 'Trade direction: true=A→B, false=B→A',
    fee_amount NUMBER(38,0) COMMENT 'Protocol fee charged for the trade',
    price_impact FLOAT COMMENT 'Price impact of the trade (calculated)',

    -- Data lineage
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    -- Add tags for metadata management
    CONSTRAINT pk_dex_trades PRIMARY KEY (transaction_digest, event_index)
)
WITH TAG (
    DATA_OWNER = 'defi_team',
    PROJECT = 'trading_analytics',
    SUB_PROJECT = 'dex_trades'
)
COMMENT = 'Processed DEX trade data with token metadata and decimal adjustments';

-- Daily price aggregations
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.PROCESSED.DAILY_PRICES (
    day_window DATE COMMENT 'Trading day (UTC)',
    token_type VARCHAR(200) COMMENT 'Token type identifier',
    token_symbol VARCHAR(20) COMMENT 'Token symbol',

    -- Price metrics
    open_price_usd FLOAT COMMENT 'Opening price in USD',
    high_price_usd FLOAT COMMENT 'Highest price in USD',
    low_price_usd FLOAT COMMENT 'Lowest price in USD',
    close_price_usd FLOAT COMMENT 'Closing price in USD',
    avg_price_usd FLOAT COMMENT 'Volume-weighted average price',

    -- Volume metrics
    volume_usd FLOAT COMMENT 'Total trading volume in USD',
    trade_count INTEGER COMMENT 'Number of trades',
    unique_traders INTEGER COMMENT 'Number of unique trader addresses',

    -- Data quality metrics
    price_data_points INTEGER COMMENT 'Number of price observations',
    price_volatility FLOAT COMMENT 'Price volatility (std dev / mean)',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT pk_daily_prices PRIMARY KEY (day_window, token_type)
)
CLUSTER BY (day_window, token_type)
COMMENT = 'Daily aggregated price and volume data for all tokens';

-- Pool liquidity aggregations
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.PROCESSED.POOL_METRICS (
    pool_id VARCHAR(66) COMMENT 'Trading pool identifier',
    protocol VARCHAR(50) COMMENT 'DEX protocol name',
    day_window DATE COMMENT 'Metrics day (UTC)',

    -- Pool composition
    token_a_type VARCHAR(200) COMMENT 'Token A in the pool pair',
    token_b_type VARCHAR(200) COMMENT 'Token B in the pool pair',
    token_a_symbol VARCHAR(20) COMMENT 'Token A symbol',
    token_b_symbol VARCHAR(20) COMMENT 'Token B symbol',

    -- Liquidity metrics
    avg_liquidity_usd FLOAT COMMENT 'Average liquidity in USD',
    min_liquidity_usd FLOAT COMMENT 'Minimum liquidity in USD',
    max_liquidity_usd FLOAT COMMENT 'Maximum liquidity in USD',

    -- Trading metrics
    volume_usd FLOAT COMMENT 'Total trading volume in USD',
    fees_collected_usd FLOAT COMMENT 'Total fees collected in USD',
    trade_count INTEGER COMMENT 'Number of trades in the pool',
    unique_traders INTEGER COMMENT 'Number of unique traders',

    -- Performance metrics
    fee_apr FLOAT COMMENT 'Fee-based annual percentage rate',
    price_volatility FLOAT COMMENT 'Price volatility in the pool',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT pk_pool_metrics PRIMARY KEY (pool_id, day_window)
)
CLUSTER BY (day_window, protocol)
COMMENT = 'Daily aggregated metrics for trading pools';

-- Trader activity summary
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.PROCESSED.TRADER_ACTIVITY (
    trader_address VARCHAR(66) COMMENT 'Trader wallet address',
    day_window DATE COMMENT 'Activity day (UTC)',

    -- Trading metrics
    trade_count INTEGER COMMENT 'Number of trades executed',
    total_volume_usd FLOAT COMMENT 'Total trading volume in USD',
    avg_trade_size_usd FLOAT COMMENT 'Average trade size in USD',
    max_trade_size_usd FLOAT COMMENT 'Largest trade size in USD',

    -- Token diversity
    unique_tokens_traded INTEGER COMMENT 'Number of different tokens traded',
    unique_pools_used INTEGER COMMENT 'Number of different pools used',
    unique_protocols_used INTEGER COMMENT 'Number of different protocols used',

    -- Fee metrics
    total_fees_paid_usd FLOAT COMMENT 'Total fees paid in USD',
    avg_fee_per_trade_usd FLOAT COMMENT 'Average fee per trade in USD',

    -- Activity patterns
    first_trade_time TIME COMMENT 'Time of first trade',
    last_trade_time TIME COMMENT 'Time of last trade',
    trading_hours_active FLOAT COMMENT 'Hours with trading activity',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT pk_trader_activity PRIMARY KEY (trader_address, day_window)
)
CLUSTER BY (day_window, trader_address)
COMMENT = 'Daily trading activity summary for each trader address';

-- Create views for commonly used queries
CREATE OR REPLACE VIEW DEFI_SAMPLE_DB.PROCESSED.RECENT_TRADES_V AS
SELECT
    protocol,
    TO_TIMESTAMP(timestamp_ms/1000) AS trade_time,
    coin_in_symbol || '→' || coin_out_symbol AS trade_pair,
    adjusted_amount_in,
    adjusted_amount_out,
    sender,
    ROUND(adjusted_amount_in * 100.0, 2) AS estimated_usd_value  -- Placeholder calculation
FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE
WHERE timestamp_ms >= EXTRACT(EPOCH FROM CURRENT_TIMESTAMP() - INTERVAL '24 hours') * 1000
ORDER BY timestamp_ms DESC
LIMIT 1000;

CREATE OR REPLACE VIEW DEFI_SAMPLE_DB.PROCESSED.TOP_TOKENS_BY_VOLUME_V AS
SELECT
    coin_symbol,
    coin_name,
    COUNT(*) AS trade_count,
    SUM(adjusted_amount_in) AS total_volume,
    COUNT(DISTINCT sender) AS unique_traders,
    MIN(timestamp_ms) AS first_trade_ms,
    MAX(timestamp_ms) AS last_trade_ms
FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE
WHERE timestamp_ms >= EXTRACT(EPOCH FROM CURRENT_TIMESTAMP() - INTERVAL '7 days') * 1000
GROUP BY coin_symbol, coin_name
ORDER BY trade_count DESC;
