-- DeFi Sample Dataset: Analytics Layer
-- These tables represent the "gold" layer - business-ready analytics

CREATE SCHEMA IF NOT EXISTS DEFI_SAMPLE_DB.ANALYTICS;

-- Business view: Only user-initiated trades (complex filtering logic)
CREATE OR REPLACE VIEW DEFI_SAMPLE_DB.ANALYTICS.FILTERED_DEX_TRADES_VIEW(
    protocol,
    timestamp_ms,
    transaction_digest,
    event_index,
    epoch,
    checkpoint,
    pool_id,
    sender,
    coin_in,
    coin_out,
    amount_in,
    amount_out,
    a_to_b,
    fee_amount,
    coin_in_name,
    coin_in_symbol,
    coin_in_decimals,
    coin_out_name,
    coin_out_symbol,
    coin_out_decimals,
    adjusted_amount_in,
    adjusted_amount_out
)
COMMENT = 'Filtered view showing only user-initiated DEX trades (excludes arbitrage and MEV)'
AS
WITH user_transaction_coins AS (
    -- Identify coins that were actually modified in user wallets
    SELECT DISTINCT
        previous_transaction AS transaction_digest,
        -- Normalize SUI address to canonical form
        CASE
            WHEN coin_type = '0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI'
            THEN '0x2::sui::SUI'
            ELSE coin_type
        END AS coin_type
    FROM DEFI_SAMPLE_DB.RAW.OBJECT_CHANGES
    WHERE
        coin_type IS NOT NULL
        AND previous_transaction IS NOT NULL
        AND owner_address NOT LIKE '0x%pool%'  -- Exclude pool addresses
        AND owner_address NOT LIKE '0x%router%'  -- Exclude router addresses
)
SELECT dts.*
FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE dts
WHERE EXISTS (
    SELECT 1
    FROM user_transaction_coins utc
    WHERE
        utc.transaction_digest = dts.transaction_digest
        AND utc.coin_type = (
            CASE
                WHEN dts.coin_in = '0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI'
                THEN '0x2::sui::SUI'
                ELSE dts.coin_in
            END
        )
);

-- Dynamic table: BTC-focused trades with USD pricing
CREATE OR REPLACE DYNAMIC TABLE DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT(
    protocol,
    timestamp_ms,
    timestamp_utc,
    transaction_digest,
    pool_id,
    pool_name,
    sender,
    coin_in,
    coin_out,
    a_to_b,
    coin_in_name,
    coin_in_symbol,
    coin_out_name,
    coin_out_symbol,
    coin_a_amount,
    coin_b_amount,
    amount_in_usd,
    amount_out_usd,
    coin_a_value_usd,
    coin_b_value_usd,
    avg_trade_value_usd,
    coin_in_price_usd,
    coin_out_price_usd
)
TARGET_LAG = '1 day'
REFRESH_MODE = FULL
INITIALIZE = ON_CREATE
WAREHOUSE = COMPUTE_WH
COMMENT = 'BTC-focused trading data with USD pricing - refreshes daily'
AS
WITH btc_tokens AS (
    -- Identify BTC-related tokens
    SELECT coin_type, coin_symbol, coin_name
    FROM DEFI_SAMPLE_DB.PROCESSED.COIN_INFO
    WHERE
        UPPER(coin_symbol) LIKE '%BTC%'
        OR UPPER(coin_name) LIKE '%BITCOIN%'
        OR UPPER(coin_symbol) LIKE '%WBTC%'
),
btc_pools AS (
    -- Find pools that contain BTC tokens
    SELECT DISTINCT
        pm.pool_id,
        pm.protocol
    FROM DEFI_SAMPLE_DB.PROCESSED.POOL_METRICS pm
    WHERE
        pm.token_a_symbol IN (SELECT coin_symbol FROM btc_tokens)
        OR pm.token_b_symbol IN (SELECT coin_symbol FROM btc_tokens)
),
price_data AS (
    -- Get recent price data
    SELECT
        token_type,
        token_symbol,
        avg_price_usd,
        day_window,
        ROW_NUMBER() OVER (
            PARTITION BY token_type, DATE_TRUNC('day', CURRENT_DATE())
            ORDER BY day_window DESC
        ) AS price_rank
    FROM DEFI_SAMPLE_DB.PROCESSED.DAILY_PRICES
    WHERE day_window >= CURRENT_DATE() - 7  -- Last week of prices
),
latest_prices AS (
    SELECT token_type, token_symbol, avg_price_usd
    FROM price_data
    WHERE price_rank = 1
),
pool_names AS (
    -- Get pool names (simplified - in real implementation would join with pool metadata)
    SELECT DISTINCT
        pool_id,
        FIRST_VALUE(
            token_a_symbol || '/' || token_b_symbol
        ) OVER (
            PARTITION BY pool_id
            ORDER BY day_window DESC
        ) AS pool_name
    FROM DEFI_SAMPLE_DB.PROCESSED.POOL_METRICS
)
SELECT
    dt.protocol,
    dt.timestamp_ms,
    TO_TIMESTAMP(dt.timestamp_ms/1000) AS timestamp_utc,
    dt.transaction_digest,
    dt.pool_id,
    pn.pool_name,
    dt.sender,
    dt.coin_in,
    dt.coin_out,
    dt.a_to_b,
    dt.coin_in_name,
    dt.coin_in_symbol,
    dt.coin_out_name,
    dt.coin_out_symbol,

    -- Directional amounts (A/B based on pool definition)
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_in
        ELSE dt.adjusted_amount_out
    END AS coin_a_amount,
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_out
        ELSE dt.adjusted_amount_in
    END AS coin_b_amount,

    -- USD calculations
    dt.adjusted_amount_in * COALESCE(p_in.avg_price_usd, 0) AS amount_in_usd,
    dt.adjusted_amount_out * COALESCE(p_out.avg_price_usd, 0) AS amount_out_usd,

    -- Directional USD values
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_in * COALESCE(p_in.avg_price_usd, 0)
        ELSE dt.adjusted_amount_out * COALESCE(p_out.avg_price_usd, 0)
    END AS coin_a_value_usd,
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_out * COALESCE(p_out.avg_price_usd, 0)
        ELSE dt.adjusted_amount_in * COALESCE(p_in.avg_price_usd, 0)
    END AS coin_b_value_usd,

    -- Average trade value
    (dt.adjusted_amount_in * COALESCE(p_in.avg_price_usd, 0) +
     dt.adjusted_amount_out * COALESCE(p_out.avg_price_usd, 0)) / 2 AS avg_trade_value_usd,

    -- Price references
    p_in.avg_price_usd AS coin_in_price_usd,
    p_out.avg_price_usd AS coin_out_price_usd

FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE dt
JOIN btc_pools bp ON dt.pool_id = bp.pool_id
LEFT JOIN latest_prices p_in ON dt.coin_in_symbol = p_in.token_symbol
LEFT JOIN latest_prices p_out ON dt.coin_out_symbol = p_out.token_symbol
LEFT JOIN pool_names pn ON dt.pool_id = pn.pool_id
ORDER BY dt.timestamp_ms DESC;

-- High-level trading metrics (materialized for performance)
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.ANALYTICS.TRADING_METRICS_DAILY (
    metric_date DATE COMMENT 'Date of the metrics',
    protocol VARCHAR(50) COMMENT 'DEX protocol name',

    -- Volume metrics
    total_trades INTEGER COMMENT 'Total number of trades',
    total_volume_usd FLOAT COMMENT 'Total trading volume in USD',
    avg_trade_size_usd FLOAT COMMENT 'Average trade size in USD',
    median_trade_size_usd FLOAT COMMENT 'Median trade size in USD',

    -- User metrics
    unique_traders INTEGER COMMENT 'Number of unique trader addresses',
    new_traders INTEGER COMMENT 'Number of first-time traders',
    returning_traders INTEGER COMMENT 'Number of returning traders',

    -- Pool metrics
    active_pools INTEGER COMMENT 'Number of pools with trades',
    avg_pool_volume_usd FLOAT COMMENT 'Average volume per pool',

    -- Token diversity
    unique_tokens_traded INTEGER COMMENT 'Number of different tokens traded',
    top_token_pair VARCHAR(50) COMMENT 'Most traded token pair',
    top_pair_volume_usd FLOAT COMMENT 'Volume of most traded pair',

    -- Fee metrics
    total_fees_usd FLOAT COMMENT 'Total fees collected in USD',
    avg_fee_per_trade_usd FLOAT COMMENT 'Average fee per trade in USD',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT pk_trading_metrics PRIMARY KEY (metric_date, protocol)
)
CLUSTER BY (metric_date, protocol)
COMMENT = 'Daily aggregated trading metrics by protocol - business KPIs';

-- User behavior analysis
CREATE OR REPLACE VIEW DEFI_SAMPLE_DB.ANALYTICS.USER_SEGMENTS_V AS
WITH user_stats AS (
    SELECT
        sender,
        COUNT(*) AS total_trades,
        SUM(adjusted_amount_in * 100) AS total_volume_approx_usd,  -- Rough approximation
        COUNT(DISTINCT DATE_TRUNC('day', TO_TIMESTAMP(timestamp_ms/1000))) AS active_days,
        COUNT(DISTINCT coin_in_symbol) AS unique_input_tokens,
        COUNT(DISTINCT coin_out_symbol) AS unique_output_tokens,
        COUNT(DISTINCT protocol) AS protocols_used,
        MIN(timestamp_ms) AS first_trade_ms,
        MAX(timestamp_ms) AS last_trade_ms
    FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE
    GROUP BY sender
),
user_classifications AS (
    SELECT
        sender,
        total_trades,
        total_volume_approx_usd,
        active_days,
        unique_input_tokens + unique_output_tokens AS token_diversity,
        protocols_used,
        DATEDIFF('day', TO_DATE(TO_TIMESTAMP(first_trade_ms/1000)), CURRENT_DATE()) AS days_since_first_trade,

        -- User segment classification
        CASE
            WHEN total_trades >= 100 AND total_volume_approx_usd >= 10000 THEN 'Whale'
            WHEN total_trades >= 50 AND total_volume_approx_usd >= 5000 THEN 'High Volume'
            WHEN total_trades >= 10 AND active_days >= 5 THEN 'Regular Trader'
            WHEN total_trades >= 5 THEN 'Casual Trader'
            ELSE 'New User'
        END AS user_segment,

        CASE
            WHEN unique_input_tokens + unique_output_tokens >= 10 THEN 'Token Explorer'
            WHEN protocols_used >= 3 THEN 'Multi-Protocol'
            WHEN active_days >= 10 THEN 'Consistent Trader'
            ELSE 'Focused Trader'
        END AS behavior_type

    FROM user_stats
)
SELECT
    user_segment,
    behavior_type,
    COUNT(*) AS user_count,
    AVG(total_trades) AS avg_trades_per_user,
    AVG(total_volume_approx_usd) AS avg_volume_per_user,
    AVG(active_days) AS avg_active_days,
    AVG(token_diversity) AS avg_token_diversity,
    SUM(total_volume_approx_usd) AS segment_total_volume
FROM user_classifications
GROUP BY user_segment, behavior_type
ORDER BY segment_total_volume DESC;

-- Cross-protocol arbitrage opportunities (advanced analytics)
CREATE OR REPLACE VIEW DEFI_SAMPLE_DB.ANALYTICS.PRICE_DISCREPANCIES_V AS
WITH same_token_trades AS (
    SELECT
        dt1.coin_in_symbol,
        dt1.coin_out_symbol,
        dt1.protocol AS protocol_1,
        dt2.protocol AS protocol_2,
        dt1.adjusted_amount_in / dt1.adjusted_amount_out AS rate_1,
        dt2.adjusted_amount_in / dt2.adjusted_amount_out AS rate_2,
        dt1.timestamp_ms AS timestamp_1,
        dt2.timestamp_ms AS timestamp_2,
        dt1.pool_id AS pool_1,
        dt2.pool_id AS pool_2
    FROM DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE dt1
    JOIN DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE dt2
        ON dt1.coin_in_symbol = dt2.coin_in_symbol
        AND dt1.coin_out_symbol = dt2.coin_out_symbol
        AND dt1.protocol != dt2.protocol
        AND ABS(dt1.timestamp_ms - dt2.timestamp_ms) <= 300000  -- Within 5 minutes
)
SELECT
    coin_in_symbol || '/' || coin_out_symbol AS trading_pair,
    protocol_1,
    protocol_2,
    rate_1,
    rate_2,
    ABS(rate_1 - rate_2) / ((rate_1 + rate_2) / 2) * 100 AS price_difference_pct,
    TO_TIMESTAMP(timestamp_1/1000) AS time_1,
    TO_TIMESTAMP(timestamp_2/1000) AS time_2,
    ABS(timestamp_1 - timestamp_2) / 1000 AS time_diff_seconds
FROM same_token_trades
WHERE ABS(rate_1 - rate_2) / ((rate_1 + rate_2) / 2) * 100 > 1  -- More than 1% difference
ORDER BY price_difference_pct DESC
LIMIT 100;
