-- DeFi Sample Dataset: Raw Data Layer
-- These tables represent the "bronze" layer - raw blockchain data

-- Create sample database and schema
CREATE DATABASE IF NOT EXISTS DEFI_SAMPLE_DB;
CREATE SCHEMA IF NOT EXISTS DEFI_SAMPLE_DB.RAW;

-- Raw transaction data (simplified from blockchain)
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.RAW.RAW_TRANSACTIONS (
    transaction_digest VARCHAR(66) COMMENT 'Unique transaction hash identifier',
    timestamp_ms NUMBER(38,0) COMMENT 'Transaction timestamp in milliseconds',
    epoch NUMBER(38,0) COMMENT 'Blockchain epoch number',
    checkpoint NUMBER(38,0) COMMENT 'Blockchain checkpoint number',
    sender VARCHAR(66) COMMENT 'Transaction sender address',
    gas_used NUMBER(38,0) COMMENT 'Gas consumed by transaction',
    gas_price NUMBER(38,0) COMMENT 'Gas price in smallest unit',
    success BOOLEAN COMMENT 'Whether transaction succeeded',
    block_height NUMBER(38,0) COMMENT 'Block number containing transaction',
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw blockchain transactions - source of truth for all DEX activity';

-- Object state changes (represents blockchain object modifications)
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.RAW.OBJECT_CHANGES (
    object_id VARCHAR(66) COMMENT 'Unique object identifier',
    previous_transaction VARCHAR(66) COMMENT 'Transaction that modified this object',
    coin_type VARCHAR(200) COMMENT 'Type identifier for cryptocurrency',
    object_type VARCHAR(50) COMMENT 'Type of blockchain object (coin, nft, etc)',
    version NUMBER(38,0) COMMENT 'Object version number',
    owner_address VARCHAR(66) COMMENT 'Current owner of the object',
    balance_change NUMBER(38,0) COMMENT 'Change in balance (positive=received, negative=sent)',
    object_json VARIANT COMMENT 'Full object metadata as JSON',
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    -- Add some constraints for data quality
    CONSTRAINT pk_object_changes PRIMARY KEY (object_id, version),
    CONSTRAINT fk_object_transaction FOREIGN KEY (previous_transaction) REFERENCES RAW_TRANSACTIONS(transaction_digest)
)
COMMENT = 'Object state changes from blockchain transactions - tracks all asset movements';

-- Raw DEX events (extracted from transaction logs)
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS (
    transaction_digest VARCHAR(66) COMMENT 'Parent transaction hash',
    event_index NUMBER(38,0) COMMENT 'Event position within transaction',
    protocol VARCHAR(50) COMMENT 'DEX protocol name',
    pool_id VARCHAR(66) COMMENT 'Trading pool identifier',
    event_type VARCHAR(20) COMMENT 'Type of event (swap, mint, burn)',
    sender VARCHAR(66) COMMENT 'Address that initiated the swap',
    recipient VARCHAR(66) COMMENT 'Address that received the output',

    -- Token A (first token in pair)
    token_a_type VARCHAR(200) COMMENT 'Token A type identifier',
    token_a_amount NUMBER(38,0) COMMENT 'Raw token A amount (before decimal adjustment)',
    token_a_reserve NUMBER(38,0) COMMENT 'Token A reserve after swap',

    -- Token B (second token in pair)
    token_b_type VARCHAR(200) COMMENT 'Token B type identifier',
    token_b_amount NUMBER(38,0) COMMENT 'Raw token B amount (before decimal adjustment)',
    token_b_reserve NUMBER(38,0) COMMENT 'Token B reserve after swap',

    -- Swap metadata
    fee_amount NUMBER(38,0) COMMENT 'Protocol fee charged',
    sqrt_price NUMBER(38,0) COMMENT 'Pool price after swap (for concentrated liquidity)',
    liquidity NUMBER(38,0) COMMENT 'Pool liquidity after swap',
    tick NUMBER(38,0) COMMENT 'Current tick (for concentrated liquidity pools)',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT pk_raw_dex_events PRIMARY KEY (transaction_digest, event_index),
    CONSTRAINT fk_dex_transaction FOREIGN KEY (transaction_digest) REFERENCES RAW_TRANSACTIONS(transaction_digest)
)
CLUSTER BY (transaction_digest, protocol)
COMMENT = 'Raw DEX swap events extracted from transaction logs';

-- Price feed data (external price oracles)
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.RAW.PRICE_FEEDS (
    feed_id VARCHAR(50) COMMENT 'Price feed identifier',
    token_type VARCHAR(200) COMMENT 'Token type being priced',
    price_usd FLOAT COMMENT 'Token price in USD',
    timestamp_ms NUMBER(38,0) COMMENT 'Price timestamp in milliseconds',
    volume_24h FLOAT COMMENT '24-hour trading volume in USD',
    market_cap FLOAT COMMENT 'Market capitalization in USD',
    source VARCHAR(50) COMMENT 'Price feed source (coingecko, chainlink, etc)',
    confidence_score FLOAT COMMENT 'Price confidence score (0-1)',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (timestamp_ms, token_type)
COMMENT = 'External price feed data for USD conversions';

-- Liquidity pool snapshots
CREATE OR REPLACE TABLE DEFI_SAMPLE_DB.RAW.LIQUIDITY_SNAPSHOTS (
    snapshot_id VARCHAR(100) COMMENT 'Unique snapshot identifier',
    pool_id VARCHAR(66) COMMENT 'Trading pool identifier',
    protocol VARCHAR(50) COMMENT 'DEX protocol name',
    timestamp_ms NUMBER(38,0) COMMENT 'Snapshot timestamp',

    -- Pool composition
    token_a_type VARCHAR(200) COMMENT 'Token A in the pool',
    token_b_type VARCHAR(200) COMMENT 'Token B in the pool',
    token_a_reserve NUMBER(38,0) COMMENT 'Token A reserves',
    token_b_reserve NUMBER(38,0) COMMENT 'Token B reserves',

    -- Pool metrics
    total_liquidity_usd FLOAT COMMENT 'Total liquidity in USD',
    volume_24h_usd FLOAT COMMENT '24-hour volume in USD',
    fees_24h_usd FLOAT COMMENT '24-hour fees collected in USD',
    apr FLOAT COMMENT 'Annual percentage rate for liquidity providers',

    -- Pool metadata
    pool_name VARCHAR(100) COMMENT 'Human-readable pool name',
    fee_tier NUMBER(38,6) COMMENT 'Pool fee percentage (e.g., 0.003 for 0.3%)',

    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (timestamp_ms, protocol)
COMMENT = 'Periodic snapshots of liquidity pool state and metrics';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_transactions_timestamp ON RAW_TRANSACTIONS(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_raw_transactions_sender ON RAW_TRANSACTIONS(sender);
CREATE INDEX IF NOT EXISTS idx_object_changes_coin_type ON OBJECT_CHANGES(coin_type);
CREATE INDEX IF NOT EXISTS idx_object_changes_transaction ON OBJECT_CHANGES(previous_transaction);
CREATE INDEX IF NOT EXISTS idx_raw_dex_events_protocol ON RAW_DEX_EVENTS(protocol);
CREATE INDEX IF NOT EXISTS idx_price_feeds_token ON PRICE_FEEDS(token_type, timestamp_ms);
