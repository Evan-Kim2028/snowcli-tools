-- COIN_INFO - Dynamic table with cryptocurrency metadata
-- Source: PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.COIN_INFO

CREATE OR REPLACE DYNAMIC TABLE COIN_INFO(
    TYPE,
    COIN_TYPE,
    COIN_DECIMALS,
    COIN_NAME,
    COIN_SYMBOL
)
TARGET_LAG = '1 hour'
REFRESH_MODE = INCREMENTAL
INITIALIZE = ON_CREATE
WAREHOUSE = ANALYTICS_WH
AS
SELECT
    type,
    split_part(split_part(type, '<', 2), '>', 1) AS coin_type,
    object_json:decimals AS coin_decimals,
    object_json:name AS coin_name,
    object_json:symbol AS coin_symbol
FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.OBJECT_PARQUET2
WHERE
    type LIKE '0x2::coin::CoinMetadata%'
QUALIFY RANK() OVER (PARTITION BY type ORDER BY version DESC) = 1;
