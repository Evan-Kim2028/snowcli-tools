# MCP Connection Smoke Test

This folder contains a ready-to-run harness for validating the combined FastMCP
server with Snowflake key-pair authentication.

## Prerequisites

1. **Python environment** – use the repo's `uv` virtual environment.
2. **Snowflake credentials** – export key-pair variables that match your
   Snowflake role. Either export them as environment variables or update the
   `.env` file described below.
3. **Service configuration** – `service_config.yaml` enables the Snowflake
   query manager and allows basic `SELECT`/`DESCRIBE` statements. Adjust it if
   you need additional SQL verbs or Cortex services.

## Environment variables

Create a `.env` file in this directory (never commit it) or export the
variables before running the server:

```bash
# Required connection fields
export SNOWFLAKE_ACCOUNT="<account_name>"
export SNOWFLAKE_USER="<user_name>"
export SNOWFLAKE_PRIVATE_KEY_FILE="/absolute/path/to/rsa_key_evan.p8"
export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="<passphrase-if-needed>"
export SNOWFLAKE_ROLE="<role_name>"
export SNOWFLAKE_WAREHOUSE="<warehouse_name>"

# Optional overrides
export SNOWFLAKE_DATABASE="<default_database>"
export SNOWFLAKE_SCHEMA="<default_schema>"
```

If you prefer to reference the private key directly, set
`SNOWFLAKE_PRIVATE_KEY` instead of `SNOWFLAKE_PRIVATE_KEY_FILE`.

## Running the server (stdio transport)

```bash
uv run python -m snowcli_tools.mcp_server \
  --service-config-file "$(pwd)/service_config.yaml" \
  --transport stdio \
  --name "snowcli-tools FastMCP"
```

For streamable HTTP:

```bash
uv run python -m snowcli_tools.mcp_server \
  --service-config-file "$(pwd)/service_config.yaml" \
  --transport streamable-http \
  --endpoint /mcp \
  --name "snowcli-tools FastMCP"
```

## Smoke-test client

Use the bundled CLI client to verify authentication and a basic query:

```bash
uv run mcp client stdio \
  --command "uv" \
  -- args run python -m snowcli_tools.mcp_server \
        --service-config-file "$(pwd)/service_config.yaml" \
        --transport stdio
```

If you prefer a scripted check, run `python test_smoke.py` after the server is
listening; see below.

## Automated smoke test

1. Start the FastMCP server in another shell using stdio or streamable HTTP.
2. Run the client script:

```bash
uv run python test_smoke.py --transport stdio
```

The script issues a live query
`SELECT * FROM object_parquet2 ORDER BY timestamp_ms DESC LIMIT 2` using the
`execute_query` tool and prints the most recent rows so you can visually verify
results.

## Notes

- The Snowflake account must allow key-pair auth for the specified user.
- When using streamable HTTP, ensure the port (default 9000) is reachable and
  configure CORS if you test from a browser client.
- If you use a passphrase-protected key, `SNOWFLAKE_PRIVATE_KEY_FILE_PWD` must
  be present; otherwise omit it.
- Keep the private key files outside version control. The sample paths here
  reference the local repository (`../snowflake_keys_evan/rsa_key_evan.p8`).
