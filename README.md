# Snowflake Connector

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A high-performance Python CLI tool and library for Snowflake database operations with parallel query execution, connection pooling, and comprehensive error handling.

## Features

- 🚀 **Parallel Query Execution**: Execute multiple queries simultaneously with configurable concurrency
- 🔗 **Connection Pooling**: Efficient connection management for high-throughput operations
- 🛡️ **Robust Error Handling**: Automatic retry mechanisms and detailed error reporting
- 📊 **Rich CLI Interface**: Beautiful command-line interface with progress tracking
- 🔧 **Flexible Configuration**: Environment variables, YAML config files, or programmatic setup
- 📈 **Performance Monitoring**: Detailed execution statistics and efficiency metrics
- 🎯 **JSON Object Support**: Optimized for blockchain/SUI object data retrieval

## Installation

### Using UV (Recommended)

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new project with the Snowflake Connector
uv init my-snowflake-project
cd my-snowflake-project

# Add Snowflake Connector as a dependency
uv add snowflake-connector
```

### Using pip

```bash
pip install snowflake-connector
```

### From Source

```bash
git clone https://github.com/Evan-Kim2028/snowflake-connector.git
cd snowflake-connector
uv install
```

## Quick Start

### 1. Set up Authentication

The connector uses key-pair authentication with Snowflake. Set up your environment:

```bash
# Option 1: Environment Variables (Recommended)
export SNOWFLAKE_PRIVATE_KEY_PATH="/Users/youruser/Documents/snowflake_keys/rsa_key.p8"
export SNOWFLAKE_ACCOUNT="your_account.us-west-2"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_WAREHOUSE="your_warehouse"
export SNOWFLAKE_DATABASE="your_database"
export SNOWFLAKE_SCHEMA="your_schema"

# Option 2: Configuration File
snowflake-cli init-config config.yaml
# Edit config.yaml with your settings
```

### 2. Test Connection

```bash
# Test your Snowflake connection
snowflake-cli test
```

### 3. Execute Queries

```bash
# Simple query
snowflake-cli query "SELECT COUNT(*) FROM your_table"

# Query with custom output
snowflake-cli query "SELECT * FROM your_table LIMIT 100" --output results.csv

# Preview table
snowflake-cli preview your_table --limit 50
```

### 4. Parallel Queries

```bash
# Query multiple objects in parallel
snowflake-cli parallel "0x1::coin::CoinInfo" "0x1::account::Account" "0x2::sui::SUI"

# Custom query template
snowflake-cli parallel "object1" "object2" \
  --query-template "SELECT * FROM custom_table WHERE type = '{object}'"

# Save results to files
snowflake-cli parallel "object1" "object2" --output-dir ./results --format parquet
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to RSA private key | `~/Documents/snowflake_keys/rsa_key.p8` |
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier | `HKB47976.us-west-2` |
| `SNOWFLAKE_USER` | Snowflake username | `readonly_ai_user` |
| `SNOWFLAKE_WAREHOUSE` | Default warehouse | `EVANS_AI_WH` |
| `SNOWFLAKE_DATABASE` | Default database | `PIPELINE_V2_GROOT_DB` |
| `SNOWFLAKE_SCHEMA` | Default schema | `PIPELINE_V2_GROOT_SCHEMA` |
| `SNOWFLAKE_ROLE` | Snowflake role (optional) | None |
| `MAX_CONCURRENT_QUERIES` | Max parallel queries | `5` |
| `CONNECTION_POOL_SIZE` | Connection pool size | `10` |
| `RETRY_ATTEMPTS` | Query retry attempts | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `1.0` |
| `TIMEOUT_SECONDS` | Query timeout | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |

### YAML Configuration

Create a `config.yaml` file:

```yaml
snowflake:
  account: "your_account.us-west-2"
  user: "your_user"
  private_key_path: "/path/to/your/private/key.p8"
  warehouse: "your_warehouse"
  database: "your_database"
  schema: "your_schema"
  role: "your_role"  # optional

max_concurrent_queries: 5
connection_pool_size: 10
retry_attempts: 3
retry_delay: 1.0
timeout_seconds: 300
log_level: "INFO"
```

Use with: `snowflake-cli --config config.yaml <command>`

## CLI Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `test` | Test Snowflake connection |
| `query` | Execute a single SQL query |
| `parallel` | Execute multiple queries in parallel |
| `preview` | Preview table contents |
| `config` | Show current configuration |
| `init-config` | Create a new configuration file |

### Command Examples

```bash
# Test connection with custom parameters
snowflake-cli test --account "custom.us-west-2" --user "custom_user"

# Execute query with JSON output
snowflake-cli query "SELECT * FROM users" --format json

# Parallel execution with custom concurrency
snowflake-cli parallel "obj1" "obj2" "obj3" --max-concurrent 3

# Preview with output file
snowflake-cli preview users --limit 100 --output users_sample.csv

# Show configuration
snowflake-cli config
```

## Python API

### Basic Usage

```python
from snowflake_connector import get_snowflake_connection, execute_query_to_dataframe

# Simple connection
conn = get_snowflake_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM your_table")
results = cursor.fetchall()
conn.close()

# Query to DataFrame
df = execute_query_to_dataframe("SELECT * FROM your_table LIMIT 100")
print(df.head())
```

### Parallel Execution

```python
from snowflake_connector import ParallelQueryExecutor, query_multiple_objects

# Using the executor class
executor = ParallelQueryExecutor()
queries = {
    "coins": "SELECT * FROM coins WHERE type = '0x1::coin::CoinInfo'",
    "accounts": "SELECT * FROM accounts WHERE type = '0x1::account::Account'",
}
results = executor.execute_queries(queries)

# Using convenience function
queries = {"obj1": "SELECT * FROM table WHERE type = 'obj1'"}
results = query_multiple_objects(queries)
```

### Configuration

```python
from snowflake_connector import Config, set_config

# Load from environment
config = Config.from_env()

# Load from YAML
config = Config.from_yaml("config.yaml")

# Set global config
set_config(config)
```

## Advanced Features

### Connection Pooling

The connector automatically manages connection pools for optimal performance:

```python
from snowflake_connector import ParallelQueryExecutor

# Configure pool size
executor = ParallelQueryExecutor()
# Pool size is automatically configured from settings
```

### Error Handling and Retries

Built-in retry mechanisms with exponential backoff:

```python
from snowflake_connector import ParallelQueryConfig, ParallelQueryExecutor

config = ParallelQueryConfig(
    retry_attempts=5,
    retry_delay=2.0,
    timeout_seconds=600
)
executor = ParallelQueryExecutor(config)
```

### JSON Data Processing

Optimized for blockchain data with automatic JSON parsing:

```python
# Queries with JSON columns are automatically parsed
results = query_multiple_objects({
    "objects": "SELECT object_json FROM object_parquet2 WHERE type = '0x1::coin::CoinInfo'"
})

for obj_name, result in results.items():
    if result.success and result.json_data:
        print(f"{obj_name}: {len(result.json_data)} JSON objects")
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Evan-Kim2028/snowflake-connector.git
cd snowflake-connector

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linter
uv run flake8 src/

# Format code
uv run black src/
```

### Project Structure

```
snowflake-connector/
├── src/
│   └── snowflake_connector/
│       ├── __init__.py          # Package initialization
│       ├── cli.py              # Command-line interface
│       ├── config.py           # Configuration management
│       ├── connection.py       # Basic connection utilities
│       └── parallel.py         # Parallel execution engine
├── tests/                      # Test suite
├── docs/                       # Documentation
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Authentication Setup

### Generating RSA Key Pair

If you need to generate a new RSA key pair for Snowflake:

```bash
# Generate private key
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes256 -out rsa_key.p8

# Generate public key from private key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

### Snowflake User Setup

1. Log into Snowflake web interface
2. Navigate to Account → Users
3. Select your user or create a new one
4. In the "Security" section, paste your public key
5. Save the user settings

## Performance Tips

1. **Connection Pooling**: Use connection pooling for multiple queries
2. **Concurrency Limits**: Adjust `max_concurrent_queries` based on your warehouse size
3. **Query Optimization**: Use appropriate LIMIT clauses for large datasets
4. **Batch Processing**: Group similar queries together for better efficiency
5. **Result Caching**: Cache frequently accessed data when possible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📧 **Email**: ekcopersonal@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/Evan-Kim2028/snowflake-connector/issues)
- 📖 **Documentation**: [GitHub Wiki](https://github.com/Evan-Kim2028/snowflake-connector/wiki)

## Changelog

### v0.1.0 (Current)
- Initial release with core functionality
- Parallel query execution
- CLI interface
- Configuration management
- Connection pooling
- Error handling and retries
