-- FILTERED_DEX_TRADES_VIEW - Business logic view showing only user-initiated trades
-- Source: PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.FILTERED_DEX_TRADES_VIEW

CREATE OR REPLACE VIEW FILTERED_DEX_TRADES_VIEW(
    PROTOCOL,
    TIMESTAMP_MS,
    TRANSACTION_DIGEST,
    EVENT_INDEX,
    EPOCH,
    CHECKPOINT,
    POOL_ID,
    SENDER,
    COIN_IN,
    COIN_OUT,
    AMOUNT_IN,
    AMOUNT_OUT,
    A_TO_B,
    FEE_AMOUNT,
    COIN_IN_NAME,
    COIN_IN_SYMBOL,
    COIN_IN_DECIMALS,
    COIN_OUT_NAME,
    COIN_OUT_SYMBOL,
    COIN_OUT_DECIMALS,
    ADJUSTED_AMOUNT_IN,
    ADJUSTED_AMOUNT_OUT
)
COMMENT = 'A filtered view of dex_trades_stable, containing only the entry-point trade of a swap. A trade is included if its input coin (coin_in) is present in the object state changes for that transaction, indicating it was directly sourced from the user''s wallet.'
AS
WITH TransactionUserCoins AS (
    -- Get the distinct set of coin types that were modified in the user's wallet for each transaction.
    SELECT DISTINCT
        previous_transaction AS transaction_digest,
        -- Normalize SUI address to the canonical short form '0x2::sui::SUI'
        CASE
            WHEN coin_type = '0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI' THEN '0x2::sui::SUI'
            ELSE coin_type
        END AS coin_type
    FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.OBJECT_PARQUET2
    WHERE coin_type IS NOT NULL AND previous_transaction IS NOT NULL
)
SELECT dts.*
FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.DEX_TRADES_STABLE dts
WHERE EXISTS (
    SELECT 1
    FROM TransactionUserCoins tuc
    WHERE tuc.transaction_digest = dts.transaction_digest
      -- A trade is valid ONLY IF its input coin matches a coin from the user's wallet changes.
      AND tuc.coin_type = (CASE WHEN dts.coin_in = '0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI' THEN '0x2::sui::SUI' ELSE dts.coin_in END)
);
