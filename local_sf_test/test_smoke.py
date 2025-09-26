"""Simple MCP smoke test script.

Launch the FastMCP server separately, then run:

    uv run python test_smoke.py --transport stdio

For streamable HTTP, the script will connect via WebSocket using the MCP
client utilities.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

# Monkey patch Snowflake token cache to use file-based fallback on macOS
import snowflake.connector.token_cache as sf_tc
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.websocket import websocket_client
from mcp.types import TextContent
from snowflake.connector.compat import IS_MACOS


class HybridTokenCache(sf_tc.TokenCache):
    def __init__(self):
        self.keyring_cache = sf_tc.KeyringTokenCache()
        self.file_cache = sf_tc.FileTokenCache.make(skip_file_permissions_check=True)
        self.logger = sf_tc.logger

    def store(self, key: sf_tc.TokenKey, token: str) -> None:
        try:
            # Try keyring first
            self.keyring_cache.store(key, token)
        except Exception:
            # Fall back to file cache
            if self.file_cache:
                self.file_cache.store(key, token)
            else:
                self.logger.warning("No token cache available, token not stored")

    def retrieve(self, key: sf_tc.TokenKey) -> str | None:
        # Try keyring first
        token = self.keyring_cache.retrieve(key)
        if token:
            return token

        # Fall back to file cache
        if self.file_cache:
            return self.file_cache.retrieve(key)

        return None

    def remove(self, key: sf_tc.TokenKey) -> None:
        try:
            self.keyring_cache.remove(key)
        except Exception:
            pass

        if self.file_cache:
            try:
                self.file_cache.remove(key)
            except Exception:
                pass


# Patch the make method to use our hybrid cache on macOS
original_make = sf_tc.TokenCache.make


def patched_make(skip_file_permissions_check: bool = False) -> sf_tc.TokenCache:
    if IS_MACOS and sf_tc.installed_keyring:
        return HybridTokenCache()
    else:
        return original_make(skip_file_permissions_check)


sf_tc.TokenCache.make = patched_make


async def run_stdio(command: str, args: list[str]) -> None:
    server_params = StdioServerParameters(command=command, args=args)
    async with stdio_client(server_params) as (read, write):
        await exercise_session(read, write)


async def run_websocket(url: str) -> None:
    async with websocket_client(url) as (read, write):
        await exercise_session(read, write)


async def exercise_session(read, write) -> None:
    async with ClientSession(read, write) as session:
        await session.initialize()

        print("Server capabilities:")
        # Note: capabilities are available after initialize, but the API might be different
        # For now, just proceed with the tool calls

        # Test query: select * from object_parquet2 limit 5
        print(
            "\n=== Testing: select * from object_parquet2 order by timestamp_ms desc limit 2 ==="
        )
        object_query = await session.call_tool(
            "execute_query",
            {
                "statement": (
                    "SELECT * FROM object_parquet2 "
                    "ORDER BY timestamp_ms DESC LIMIT 2"
                )
            },
        )
        _print_tool_output(
            "execute_query (object_parquet2 order by timestamp_ms desc limit 2)",
            object_query,
        )


def _print_tool_output(name: str, result: list[Any]) -> None:
    print(f"\n{name} response:")
    structured: dict[str, Any] | None = None
    if hasattr(result, "structuredContent"):
        structured = getattr(result, "structuredContent")
    elif isinstance(result, list):
        # Older MCP client format
        for block in result:
            if isinstance(block, TextContent):
                try:
                    maybe = json.loads(block.text)
                    if isinstance(maybe, dict) and "rows" in maybe:
                        structured = maybe
                except json.JSONDecodeError:
                    continue
            elif isinstance(block, list) and len(block) == 2:
                key, value = block
                if key == "structuredContent" and isinstance(value, dict):
                    structured = value

    if structured and "rows" in structured:
        print("Rows:")
        for idx, row in enumerate(structured["rows"], start=1):
            if isinstance(row, dict):
                summary = {
                    key: row.get(key)
                    for key in (
                        "OBJECT_ID",
                        "TIMESTAMP_MS",
                        "TYPE",
                        "CHECKPOINT",
                        "OWNER_TYPE",
                    )
                    if key in row
                }
                print(f"Row {idx}:")
                print(json.dumps(summary, indent=2, default=str))
            else:
                print(json.dumps(row, indent=2, default=str))
    else:
        print(json.dumps(str(result), indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FastMCP smoke-test client")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport to use for the server connection",
    )
    parser.add_argument(
        "--stdio-command",
        default="uv",
        help="Command to launch the server under stdio transport",
    )
    parser.add_argument(
        "--stdio-args",
        nargs=argparse.REMAINDER,
        default=[
            "run",
            "python",
            "-m",
            "snowcli_tools.mcp_server",
            "--service-config-file",
            str((Path(__file__).parent / "service_config.yaml").resolve()),
            "--transport",
            "stdio",
            "--profile",
            "mystenlabs-keypair",
        ],
        help="Arguments to launch the server for stdio transport",
    )
    parser.add_argument(
        "--url",
        default="ws://localhost:9000/mcp",
        help="Streamable HTTP WebSocket URL",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.transport == "stdio":
        await run_stdio(args.stdio_command, args.stdio_args)
    else:
        await run_websocket(args.url)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
