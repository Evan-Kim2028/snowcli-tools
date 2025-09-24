-- BTC_DEX_TRADES_USD_DT - Dynamic table for BTC trades with USD pricing
-- Source: PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.BTC_DEX_TRADES_USD_DT

CREATE OR REPLACE DYNAMIC TABLE BTC_DEX_TRADES_USD_DT(
    PROTOCOL,
    TIMESTAMP_MS,
    TIMESTAMP_UTC,
    TRANSACTION_DIGEST,
    POOL_ID,
    POOL_NAME,
    SENDER,
    COIN_IN,
    COIN_OUT,
    A_TO_B,
    COIN_IN_NAME,
    COIN_IN_SYMBOL,
    COIN_OUT_NAME,
    COIN_OUT_SYMBOL,
    COIN_A_AMOUNT,
    COIN_B_AMOUNT,
    AMOUNT_IN_USD,
    AMOUNT_OUT_USD,
    COIN_A_VALUE_USD,
    COIN_B_VALUE_USD,
    AVG_TRADE_VALUE_USD,
    COIN_IN_PRICE_USD,
    COIN_OUT_PRICE_USD
)
TARGET_LAG = '1 day'
REFRESH_MODE = FULL
INITIALIZE = ON_CREATE
WAREHOUSE = DEFI_WH
COMMENT = 'Dynamic table that tracks btc trades and calculates the usd price value for these trades. Only supplies pool names for cetus and bluefin for now...only updates once a day. Shows all current btc coins based on updated coin_info_btc dataset'
AS
WITH btc_pools AS (
    SELECT
        POOL_ID
    FROM
        PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.LIQUIDITY_USD_DAILY_AGG
    WHERE
        -- Use btc_coin_info table instead of hardcoded coin types
        (COIN_TYPE_A IN (SELECT COIN_TYPE FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.COIN_INFO_BTC)
        OR COIN_TYPE_B IN (SELECT COIN_TYPE FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.COIN_INFO_BTC))
        AND pool_id != '0x7ee331364a3574197f211cb0f236622512341b019c11d87bc87aa7f9960ca3fd'
    GROUP BY
        POOL_ID
    HAVING
        COUNT(*) >= 4
),
avg_prices AS (
    SELECT
        DAY_WINDOW,
        NON_SUI_TOKEN,
        AVG(PRICE_USD) AS AVG_PRICE_USD
    FROM
        dex_prices_stable
    WHERE
        TOTAL_DATA_POINTS > 100
    GROUP BY
        DAY_WINDOW,
        NON_SUI_TOKEN
),
pool_names AS (
    SELECT DISTINCT
        POOL_ID,
        FIRST_VALUE(POOL_NAME) OVER (PARTITION BY POOL_ID ORDER BY TIMESTAMP_UTC DESC) AS POOL_NAME
    FROM (
        -- Bluefin data
        SELECT
            POOL_ID,
            POOL_NAME,
            TIMESTAMP_UTC
        FROM
            liquidity_bluefin_raw
        WHERE
            POOL_ID IN (SELECT POOL_ID FROM btc_pools)

        UNION ALL

        -- Cetus data
        SELECT
            POOL_ID,
            POOL_NAME,
            TIMESTAMP_UTC
        FROM
            liquidity_cetus_raw
        WHERE
            POOL_ID IN (SELECT POOL_ID FROM btc_pools)
    )
)
SELECT
    dt.PROTOCOL,
    dt.TIMESTAMP_MS,
    TO_TIMESTAMP(dt.TIMESTAMP_MS/1000) AS TIMESTAMP_UTC,
    dt.TRANSACTION_DIGEST,
    dt.POOL_ID,
    pn.POOL_NAME,
    dt.SENDER,
    dt.COIN_IN,
    dt.COIN_OUT,
    dt.A_TO_B,
    dt.COIN_IN_NAME,
    dt.COIN_IN_SYMBOL,
    dt.COIN_OUT_NAME,
    dt.COIN_OUT_SYMBOL,
    -- Directional coin amounts
    CASE
        WHEN dt.a_to_b THEN dt.ADJUSTED_AMOUNT_IN
        ELSE dt.ADJUSTED_AMOUNT_OUT
    END AS COIN_A_AMOUNT,
    CASE
        WHEN dt.a_to_b THEN dt.ADJUSTED_AMOUNT_OUT
        ELSE dt.ADJUSTED_AMOUNT_IN
    END AS COIN_B_AMOUNT,
    -- Calculate amount_in USD
    dt.adjusted_amount_in * p_in.AVG_PRICE_USD AS AMOUNT_IN_USD,
    -- Calculate amount_out USD
    dt.adjusted_amount_out * p_out.AVG_PRICE_USD AS AMOUNT_OUT_USD,
    -- Directional coin A and B values based on a_to_b flag
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_in * p_in.AVG_PRICE_USD
        ELSE dt.adjusted_amount_out * p_out.AVG_PRICE_USD
    END AS COIN_A_VALUE_USD,
    CASE
        WHEN dt.a_to_b THEN dt.adjusted_amount_out * p_out.AVG_PRICE_USD
        ELSE dt.adjusted_amount_in * p_in.AVG_PRICE_USD
    END AS COIN_B_VALUE_USD,
    -- Improved average trade value calculation
    CASE
        WHEN (dt.a_to_b AND p_in.AVG_PRICE_USD IS NOT NULL AND p_out.AVG_PRICE_USD IS NOT NULL) OR
             (NOT dt.a_to_b AND p_out.AVG_PRICE_USD IS NOT NULL AND p_in.AVG_PRICE_USD IS NOT NULL) THEN
            (dt.adjusted_amount_in * p_in.AVG_PRICE_USD + dt.adjusted_amount_out * p_out.AVG_PRICE_USD) / 2
        WHEN dt.a_to_b AND p_in.AVG_PRICE_USD IS NOT NULL THEN
            dt.adjusted_amount_in * p_in.AVG_PRICE_USD
        WHEN dt.a_to_b AND p_out.AVG_PRICE_USD IS NOT NULL THEN
            dt.adjusted_amount_out * p_out.AVG_PRICE_USD
        WHEN NOT dt.a_to_b AND p_out.AVG_PRICE_USD IS NOT NULL THEN
            dt.adjusted_amount_out * p_out.AVG_PRICE_USD
        WHEN NOT dt.a_to_b AND p_in.AVG_PRICE_USD IS NOT NULL THEN
            dt.adjusted_amount_in * p_in.AVG_PRICE_USD
        ELSE NULL
    END AS AVG_TRADE_VALUE_USD,
    -- Original price data
    p_in.AVG_PRICE_USD AS COIN_IN_PRICE_USD,
    p_out.AVG_PRICE_USD AS COIN_OUT_PRICE_USD
FROM
    dex_trades_stable dt
JOIN
    btc_pools bp ON dt.pool_id = bp.pool_id
LEFT JOIN
    avg_prices p_in
    ON dt.coin_in = p_in.NON_SUI_TOKEN
    AND DATE_TRUNC('day', TO_TIMESTAMP(dt.timestamp_ms/1000)) = p_in.DAY_WINDOW
LEFT JOIN
    avg_prices p_out
    ON dt.coin_out = p_out.NON_SUI_TOKEN
    AND DATE_TRUNC('day', TO_TIMESTAMP(dt.timestamp_ms/1000)) = p_out.DAY_WINDOW
LEFT JOIN
    pool_names pn
    ON dt.pool_id = pn.pool_id
ORDER BY
    dt.timestamp_ms DESC;
