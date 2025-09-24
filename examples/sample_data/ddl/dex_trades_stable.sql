-- DEX_TRADES_STABLE - Main fact table for DEX trading data
-- Source: PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.DEX_TRADES_STABLE

CREATE OR REPLACE TABLE DEX_TRADES_STABLE
CLUSTER BY (timestamp_ms, protocol) (
    PROTOCOL VARCHAR(16777216) COMMENT 'DEX protocol name',
    TIMESTAMP_MS NUMBER(38,0) COMMENT 'The number of milliseconds that the PTB was executed.',
    TRANSACTION_DIGEST VARCHAR(16777216) COMMENT 'Unique identifier for each PTB, represented as a string.',
    EVENT_INDEX NUMBER(38,0) COMMENT 'Holds data representing unique positional identifiers for specific events within a PTB. Currently is buggy',
    EPOCH NUMBER(38,0) COMMENT 'An epoch refers to a fixed time period during which the network operates under a specific set of conditions, such as validator configurations, staking rewards, and gas fees. Each epoch typically lasts 24 hours, after which the network transitions to a new epoch, allowing for updates like validator rotations or protocol adjustments. It''s a mechanism to organize network governance and operations in a decentralized system.',
    CHECKPOINT NUMBER(38,0) COMMENT 'A checkpoint is a periodic snapshot of the network''s state that validators agree upon to ensure consistency and finality of transactions. It acts as a reference point, summarizing a batch of processed PTBs and their effects on the ledger.',
    POOL_ID VARCHAR(16777216) COMMENT 'Unique object address for a specific trading pool.',
    SENDER VARCHAR(16777216) COMMENT 'Cryptographic hash values representing the sender''s SUI address.',
    COIN_IN VARCHAR(16777216) COMMENT 'Coin type for which coin is getting swapped into the pool',
    COIN_OUT VARCHAR(16777216) COMMENT 'Coin type for which coins is getting swapped out of the pool.',
    AMOUNT_IN NUMBER(38,0) COMMENT 'Raw coin amount for amount of coins that get swapped into the pool',
    AMOUNT_OUT NUMBER(38,0) COMMENT 'Raw coin amount for amount of coins that get swapped out of the pool',
    A_TO_B BOOLEAN COMMENT 'Directional relationship between the pool swaps. Boolean identifies whether the swap direction goes from Token A -> Token B or from Token B -> Token A.',
    FEE_AMOUNT NUMBER(38,0) COMMENT 'Monetary value representing various fees associated with a trade.',
    COIN_IN_NAME VARCHAR(16777216) COMMENT 'coin in token name',
    COIN_IN_SYMBOL VARCHAR(16777216) COMMENT 'coin in token symbol',
    COIN_IN_DECIMALS NUMBER(38,0) COMMENT 'coin in decimals',
    COIN_OUT_NAME VARCHAR(16777216) COMMENT 'coin out token name',
    COIN_OUT_SYMBOL VARCHAR(16777216) COMMENT 'coin out token symbol',
    COIN_OUT_DECIMALS NUMBER(38,0) COMMENT 'coin out decimals',
    ADJUSTED_AMOUNT_IN FLOAT COMMENT 'coin in swapped amount divided by decimals',
    ADJUSTED_AMOUNT_OUT FLOAT COMMENT 'coin out swapped amount divided by decimals'
)
WITH TAG (
    DATA_OWNER='evan_kim',
    PROJECT='defi',
    SUB_PROJECT='dex'
)
COMMENT='Contains all dex swaps with coin metadata from multiple DEX protocols - aftermath, bluefin, bluemove, cetus, flowx, metastable';
