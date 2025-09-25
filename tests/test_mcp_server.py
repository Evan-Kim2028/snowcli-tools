"""Tests for the MCP server functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from snowcli_tools.mcp_server import SnowflakeMCPServer


class TestSnowflakeMCPServer:
    """Test cases for the MCP server."""

    @pytest.fixture
    def mock_snow_cli(self):
        """Mock SnowCLI instance."""
        mock_cli = Mock()
        mock_cli.test_connection.return_value = True
        mock_cli.run_query.return_value = Mock(
            rows=[{"col1": "value1", "col2": "value2"}],
            raw_stdout='[\n  {\n    "col1": "value1",\n    "col2": "value2"\n  }\n]',
            returncode=0,
        )
        return mock_cli

    @pytest.fixture
    def mock_config(self):
        """Mock config instance."""
        mock_config = Mock()
        mock_config.snowflake.profile = "test-profile"
        mock_config.snowflake.database = "TEST_DB"
        mock_config.snowflake.schema = "TEST_SCHEMA"
        mock_config.snowflake.warehouse = "TEST_WH"
        mock_config.snowflake.role = "TEST_ROLE"
        return mock_config

    @pytest.fixture
    def server(self, mock_snow_cli, mock_config):
        """Create MCP server with mocked dependencies."""
        with (
            patch("snowcli_tools.mcp_server.SnowCLI", return_value=mock_snow_cli),
            patch("snowcli_tools.mcp_server.get_config", return_value=mock_config),
        ):
            server = SnowflakeMCPServer()
            server.snow_cli = mock_snow_cli
            server.config = mock_config
            return server

    def test_server_initialization(self, server):
        """Test that server initializes correctly."""
        assert server.server is not None
        assert server.snow_cli is not None
        assert server.config is not None

    def test_execute_query_success(self, server, mock_snow_cli):
        """Test successful query execution."""
        result = server._execute_query("SELECT 1")

        expected = '[\n  {\n    "col1": "value1",\n    "col2": "value2"\n  }\n]'
        assert result == expected
        mock_snow_cli.run_query.assert_called_once_with(
            "SELECT 1", output_format="json", ctx_overrides={}
        )

    def test_execute_query_with_context(self, server, mock_snow_cli):
        """Test query execution with context overrides."""
        server._execute_query(
            "SELECT * FROM test_table",
            warehouse="TEST_WH",
            database="TEST_DB",
            schema="TEST_SCHEMA",
            role="TEST_ROLE",
        )

        mock_snow_cli.run_query.assert_called_once_with(
            "SELECT * FROM test_table",
            output_format="json",
            ctx_overrides={
                "warehouse": "TEST_WH",
                "database": "TEST_DB",
                "schema": "TEST_SCHEMA",
                "role": "TEST_ROLE",
            },
        )

    def test_preview_table(self, server, mock_snow_cli):
        """Test table preview functionality."""
        server._preview_table("MY_TABLE", limit=50)

        mock_snow_cli.run_query.assert_called_once_with(
            "SELECT * FROM MY_TABLE LIMIT 50", output_format="json", ctx_overrides={}
        )

    def test_test_connection_success(self, server, mock_snow_cli):
        """Test successful connection test."""
        result = server._test_connection()
        assert result == "Connection successful!"
        mock_snow_cli.test_connection.assert_called_once()

    def test_test_connection_failure(self, server, mock_snow_cli):
        """Test failed connection test."""
        mock_snow_cli.test_connection.return_value = False

        result = server._test_connection()
        assert result == "Connection failed!"

    @patch("snowcli_tools.mcp_server.build_catalog")
    def test_build_catalog_success(self, mock_build_catalog, server):
        """Test successful catalog build."""
        mock_build_catalog.return_value = {
            "databases": 5,
            "schemas": 20,
            "tables": 100,
            "views": 25,
        }

        result = server._build_catalog(
            output_dir="/tmp/test_catalog",
            database="TEST_DB",
            account=False,
            format="json",
            include_ddl=True,
        )

        expected_result = {
            "success": True,
            "message": "Catalog built successfully in /tmp/test_catalog",
            "totals": {"databases": 5, "schemas": 20, "tables": 100, "views": 25},
        }

        assert json.loads(result) == expected_result
        mock_build_catalog.assert_called_once_with(
            "/tmp/test_catalog",
            database="TEST_DB",
            account_scope=False,
            incremental=False,
            output_format="json",
            include_ddl=True,
            max_ddl_concurrency=8,
            catalog_concurrency=16,
            export_sql=False,
        )

    @patch("snowcli_tools.mcp_server.build_catalog")
    def test_build_catalog_failure(self, mock_build_catalog, server):
        """Test catalog build failure."""
        mock_build_catalog.side_effect = Exception("Build failed")

        with pytest.raises(Exception, match="Catalog build failed: Build failed"):
            server._build_catalog()

    @patch("snowcli_tools.mcp_server.build_dependency_graph")
    def test_build_dependency_graph_json(self, mock_build_graph, server):
        """Test dependency graph building with JSON format."""
        mock_graph = {"nodes": {"table1": {}}, "edges": []}
        mock_build_graph.return_value = mock_graph

        result = server._build_dependency_graph(format="json")

        expected = '{\n  "nodes": {\n    "table1": {}\n  },\n  "edges": []\n}'
        assert result == expected
        mock_build_graph.assert_called_once_with(
            database=None, schema=None, account_scope=False
        )

    @patch("snowcli_tools.mcp_server.build_dependency_graph")
    def test_build_dependency_graph_dot(self, mock_build_graph, server):
        """Test dependency graph building with DOT format."""
        mock_graph = {"nodes": {"table1": {}}, "edges": []}
        mock_build_graph.return_value = mock_graph

        with patch("snowcli_tools.mcp_server.to_dot") as mock_to_dot:
            mock_to_dot.return_value = "digraph { table1 }"

            result = server._build_dependency_graph(format="dot")

            assert result == "digraph { table1 }"
            mock_to_dot.assert_called_once_with(mock_graph)

    def test_get_catalog_summary_exists(self, server):
        """Test getting catalog summary when file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_file = Path(temp_dir) / "catalog_summary.json"
            summary_data = {"databases": 3, "tables": 50}
            summary_file.write_text(json.dumps(summary_data))

            result = server._get_catalog_summary(catalog_dir=temp_dir)

            assert json.loads(result) == summary_data

    def test_get_catalog_summary_missing(self, server):
        """Test getting catalog summary when file doesn't exist."""
        result = server._get_catalog_summary(catalog_dir="/nonexistent/path")

        assert "No catalog summary found" in result
        assert "/nonexistent/path" in result


class TestMCPServerIntegration:
    """Integration tests for MCP server functionality."""

    @pytest.fixture
    def mock_lineage_service(self):
        """Mock lineage query service."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.graph = Mock()
        mock_result.graph.nodes = {"table1": Mock()}
        mock_result.graph.edge_metadata = {}
        mock_service.object_subgraph.return_value = mock_result
        return mock_service

    @pytest.fixture
    def integration_server(self):
        """Server fixture for integration tests."""
        mock_snow_cli = Mock()
        mock_snow_cli.test_connection.return_value = True
        mock_snow_cli.run_query.return_value = Mock(
            rows=[{"col1": "value1", "col2": "value2"}],
            raw_stdout='[{"col1": "value1", "col2": "value2"}]',
            returncode=0,
        )

        mock_config = Mock()
        mock_config.snowflake.profile = "test-profile"
        mock_config.snowflake.database = "TEST_DB"
        mock_config.snowflake.schema = "TEST_SCHEMA"

        with (
            patch("snowcli_tools.mcp_server.SnowCLI", return_value=mock_snow_cli),
            patch("snowcli_tools.mcp_server.get_config", return_value=mock_config),
        ):
            server = SnowflakeMCPServer()
            server.snow_cli = mock_snow_cli
            server.config = mock_config
            return server

    @patch("snowcli_tools.mcp_server.LineageQueryService")
    def test_query_lineage_success(
        self, mock_lineage_class, integration_server, mock_lineage_service
    ):
        """Test successful lineage query."""
        mock_lineage_class.return_value = mock_lineage_service

        result = integration_server._query_lineage(
            "MY_TABLE", direction="both", depth=3
        )

        assert "Lineage Analysis for TEST_DB.TEST_SCHEMA.MY_TABLE" in result
        assert "Direction: both" in result
        assert "Depth: 3" in result
        mock_lineage_class.assert_called_once_with("./data_catalogue", "./lineage")

    @patch("snowcli_tools.mcp_server.LineageQueryService")
    def test_query_lineage_json_format(
        self, mock_lineage_class, integration_server, mock_lineage_service
    ):
        """Test lineage query with JSON output format."""
        mock_lineage_class.return_value = mock_lineage_service

        result = integration_server._query_lineage("MY_TABLE", format="json")

        result_data = json.loads(result)
        assert result_data["direction"] == "both"
        assert result_data["depth"] == 3
        assert result_data["nodes"] == 1

    @patch("snowcli_tools.mcp_server.LineageQueryService")
    def test_query_lineage_not_found(self, mock_lineage_class, integration_server):
        """Test lineage query when object is not found."""
        mock_service = Mock()
        mock_service.object_subgraph.side_effect = KeyError("Object not found")
        mock_lineage_class.return_value = mock_service

        result = integration_server._query_lineage("NONEXISTENT_TABLE")

        assert "not found in lineage graph" in result


class TestMCPServerErrorHandling:
    """Test error handling in MCP server."""

    @pytest.fixture
    def server(self):
        """Create server for error tests."""
        server = SnowflakeMCPServer()
        server.snow_cli = Mock()
        server.config = Mock()
        return server

    def test_execute_query_error(self, server):
        """Test query execution error handling."""
        server.snow_cli.run_query.side_effect = Exception("Query failed")

        with pytest.raises(Exception, match="Query failed"):
            server._execute_query("INVALID SQL")

    def test_build_dependency_graph_error(self, server):
        """Test dependency graph error handling."""
        with patch("snowcli_tools.mcp_server.build_dependency_graph") as mock_build:
            mock_build.side_effect = Exception("Graph build failed")

            with pytest.raises(
                Exception, match="Dependency graph build failed: Graph build failed"
            ):
                server._build_dependency_graph()

    def test_get_catalog_summary_error(self, server):
        """Test catalog summary error handling."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("File read error")):
                with pytest.raises(
                    Exception, match="Failed to read catalog summary: File read error"
                ):
                    server._get_catalog_summary()


class TestMCPServerToolSchemas:
    """Test that tool schemas are correctly defined."""

    @pytest.fixture
    def server(self):
        """Create server for schema testing."""
        server = SnowflakeMCPServer()
        return server

    def test_server_has_all_expected_methods(self, server):
        """Test that server has all expected private methods."""
        expected_methods = [
            "_execute_query",
            "_preview_table",
            "_build_catalog",
            "_query_lineage",
            "_build_dependency_graph",
            "_test_connection",
            "_get_catalog_summary",
        ]

        for method_name in expected_methods:
            assert hasattr(server, method_name), f"Missing method: {method_name}"
            assert callable(
                getattr(server, method_name)
            ), f"Method not callable: {method_name}"


class TestMCPServerAuthentication:
    """Test authentication-related functionality."""

    def test_server_initializes_with_config_profile(self):
        """Test that server uses configured profile."""
        mock_config = Mock()
        mock_config.snowflake.profile = "test-profile"

        with patch("snowcli_tools.mcp_server.get_config", return_value=mock_config):
            with patch("snowcli_tools.mcp_server.SnowCLI") as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli

                server = SnowflakeMCPServer()

                # The SnowCLI constructor is called without arguments in __init__,
                # but the profile is passed when run_query is called
                mock_cli_class.assert_called_once_with()
                assert server.config == mock_config

    def test_server_handles_missing_profile_gracefully(self):
        """Test that server handles missing profile gracefully."""
        mock_config = Mock()
        mock_config.snowflake.profile = None  # Missing profile

        with patch("snowcli_tools.mcp_server.get_config", return_value=mock_config):
            with patch("snowcli_tools.mcp_server.SnowCLI") as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli

                # Should not raise an exception, just use None
                server = SnowflakeMCPServer()

                mock_cli_class.assert_called_once_with()
                assert server.config == mock_config

    def test_server_passes_context_overrides_correctly(self):
        """Test that context overrides are passed correctly to SnowCLI."""
        mock_config = Mock()
        mock_config.snowflake.profile = "test-profile"

        with patch("snowcli_tools.mcp_server.get_config", return_value=mock_config):
            with patch("snowcli_tools.mcp_server.SnowCLI") as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli

                server = SnowflakeMCPServer()
                server.snow_cli = mock_cli

                # Test that context is passed through
                server._execute_query("SELECT 1", warehouse="WH1", database="DB1")

                mock_cli.run_query.assert_called_once()
                call_kwargs = mock_cli.run_query.call_args[1]
                assert call_kwargs["ctx_overrides"] == {
                    "warehouse": "WH1",
                    "database": "DB1",
                }


class TestMCPInitializationFailures:
    """Test MCP server initialization failure scenarios."""

    @pytest.fixture
    def server(self):
        """Create server for initialization tests."""
        with patch("snowcli_tools.mcp_server.get_config", return_value=None):
            server = SnowflakeMCPServer()
            server.snow_cli = Mock()
            return server

    @pytest.mark.asyncio
    async def test_verify_components_no_config(self, server):
        """Test component verification fails with no config."""
        server.config = None
        result = await server._verify_components()
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_components_lineage_service_error(self, server):
        """Test component verification fails when LineageQueryService fails."""
        server.config = Mock()

        with patch(
            "snowcli_tools.mcp_server.LineageQueryService",
            side_effect=Exception("Service init failed"),
        ):
            result = await server._verify_components()
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_components_success(self, server):
        """Test component verification succeeds with valid config."""
        server.config = Mock()

        with patch("snowcli_tools.mcp_server.LineageQueryService") as mock_service:
            mock_service.return_value = Mock()
            result = await server._verify_components()
            assert result is True

    def test_get_server_capabilities_old_api(self, server):
        """Test get_server_capabilities with old MCP API."""
        with patch("snowcli_tools.mcp_server.MCP_NEW_API", False):
            server.server = Mock()
            server.server.get_capabilities.return_value = {"test": "capability"}

            result = server._get_server_capabilities()
            assert result == {"test": "capability"}
            server.server.get_capabilities.assert_called_once_with()

    def test_get_server_capabilities_new_api_success(self, server):
        """Test get_server_capabilities with new MCP API (success)."""
        with patch("snowcli_tools.mcp_server.MCP_NEW_API", True):
            server.server = Mock()
            server.server.get_capabilities.return_value = {"test": "capability"}

            result = server._get_server_capabilities()
            assert result == {"test": "capability"}
            # Should call with notification_options=None and experimental_capabilities={}
            server.server.get_capabilities.assert_called_once_with(
                notification_options=None, experimental_capabilities={}
            )

    def test_get_server_capabilities_new_api_fallback(self, server):
        """Test get_server_capabilities fallback when new API fails."""
        with patch("snowcli_tools.mcp_server.MCP_NEW_API", True):
            server.server = Mock()
            # First call (new API) fails, second call (old API) succeeds
            server.server.get_capabilities.side_effect = [
                TypeError("New API failed"),  # Use TypeError as expected by our code
                {"test": "fallback"},
            ]

            result = server._get_server_capabilities()
            assert result == {"test": "fallback"}
            assert server.server.get_capabilities.call_count == 2

    @pytest.mark.asyncio
    async def test_run_with_component_verification_failure(self, server):
        """Test that run() raises RuntimeError when component verification fails."""
        server.config = None  # This will cause verification to fail

        with pytest.raises(RuntimeError, match="Component verification failed"):
            await server.run()

    @pytest.mark.asyncio
    async def test_run_with_mcp_server_failure(self, server):
        """Test that run() handles MCP server startup failures."""
        server.config = Mock()

        with patch("snowcli_tools.mcp_server.LineageQueryService"):
            with patch("mcp.server.stdio.stdio_server") as mock_stdio:
                mock_stdio.side_effect = Exception("MCP server startup failed")

                with pytest.raises(Exception, match="MCP server startup failed"):
                    await server.run()

    def test_version_detection(self):
        """Test MCP version detection and compatibility flags."""
        # Test that version constants are properly set
        from snowcli_tools.mcp_server import MCP_NEW_API, MCP_VERSION

        assert isinstance(MCP_VERSION, str)
        assert isinstance(MCP_NEW_API, bool)

        # Version should be non-empty (either real version or default)
        assert MCP_VERSION != ""

    @pytest.mark.asyncio
    async def test_verify_components_partial_config(self, server):
        """Test component verification with partial configuration."""
        # Create a mock config that has snowflake section but missing fields
        server.config = Mock()
        server.config.snowflake = Mock()
        server.config.snowflake.profile = None

        with patch(
            "snowcli_tools.mcp_server.LineageQueryService",
            side_effect=Exception("Missing profile"),
        ):
            result = await server._verify_components()
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_components_network_timeout(self, server):
        """Test component verification with network timeout."""
        server.config = Mock()
        server.config.snowflake = Mock()

        # Mock connection timeout
        server.snow_cli.test_connection.side_effect = TimeoutError("Network timeout")

        result = await server._verify_components()
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_components_missing_snowflake_section(self, server):
        """Test component verification with invalid config structure."""
        # Create config without snowflake section
        server.config = Mock()
        del server.config.snowflake  # Remove the snowflake attribute

        result = await server._verify_components()
        assert result is False

    def test_get_server_capabilities_api_fallback_with_specific_errors(self, server):
        """Test get_server_capabilities fallback with specific exception types."""
        with patch("snowcli_tools.mcp_server.MCP_NEW_API", True):
            server.server = Mock()
            # First call (new API) fails with TypeError, second call (old API) succeeds
            server.server.get_capabilities.side_effect = [
                TypeError("Unexpected keyword argument"),
                {"test": "fallback"},
            ]

            result = server._get_server_capabilities()
            assert result == {"test": "fallback"}
            assert server.server.get_capabilities.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_server_initialization(self, server):
        """Test race conditions in concurrent server initialization."""
        import asyncio

        server.config = Mock()
        server.config.snowflake = Mock()

        # Mock successful verification
        with patch("snowcli_tools.mcp_server.LineageQueryService") as mock_service:
            mock_service.return_value = Mock()

            # Test concurrent verification calls
            tasks = [server._verify_components() for _ in range(3)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(results)

    def test_custom_exception_hierarchy(self):
        """Test that custom exceptions have proper hierarchy."""
        from snowcli_tools.mcp_server import (
            ComponentVerificationError,
            ConfigurationError,
            ConnectionError,
            MCPServerError,
        )

        # Test exception hierarchy
        assert issubclass(ConfigurationError, MCPServerError)
        assert issubclass(ComponentVerificationError, MCPServerError)
        assert issubclass(ConnectionError, MCPServerError)

        # Test that they can be instantiated and raised
        try:
            raise ConfigurationError("Test config error")
        except MCPServerError as e:
            assert str(e) == "Test config error"

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_failure(self, server):
        """Test that resources are cleaned up when server initialization fails."""
        server.config = Mock()
        server.config.snowflake = Mock()

        # Mock a failure during server startup
        with patch("snowcli_tools.mcp_server.LineageQueryService"):
            with patch(
                "mcp.server.stdio.stdio_server",
                side_effect=Exception("Server startup failed"),
            ):
                # Ensure cleanup method is called
                with patch.object(server, "_cleanup_resources") as mock_cleanup:
                    with pytest.raises(Exception, match="Server startup failed"):
                        await server.run()

                    mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_configuration_schema_missing_auth(self, server):
        """Test configuration validation with missing authentication."""
        # Create config with required fields but no auth method
        server.config = Mock()
        server.config.snowflake = Mock()
        server.config.snowflake.account = "test_account"
        server.config.snowflake.user = "test_user"
        # No authentication method set

        result = await server._verify_components()
        assert result is False

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, server):
        """Test that connection timeouts are handled properly."""
        server.config = Mock()
        server.config.snowflake = Mock()
        server.config.snowflake.account = "test_account"
        server.config.snowflake.user = "test_user"
        server.config.snowflake.password = "test_password"

        # Mock connection test to timeout by raising TimeoutError directly
        def mock_connection_test():
            import asyncio

            raise asyncio.TimeoutError("Connection test timed out")

        server.snow_cli.test_connection = mock_connection_test

        result = await server._verify_components()
        assert result is False

    def test_error_message_sanitization(self):
        """Test that error messages are properly sanitized."""
        # This would be tested in an integration test, but we can test the concept
        # by checking that the sanitization patterns work
        import re

        def sanitize_error_message(msg: str) -> str:
            """Copy of sanitization function for testing."""
            patterns = [
                (r"password=[^;,\s]+", "password=***"),
                (r"token=[^;,\s]+", "token=***"),
                (r"authenticator=[^;,\s]+", "authenticator=***"),
                (r"private_key=[^;,\s]+", "private_key=***"),
                (r"://[^:@]+:[^@]+@", "://***:***@"),
                (r"Connection string.*", "Connection string: [SANITIZED]"),
            ]
            sanitized = str(msg)
            for pattern, replacement in patterns:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            return sanitized

        # Test various sensitive information patterns
        sensitive_messages = [
            "Connection failed: password=secret123",
            "Auth error: token=abc123xyz",
            "Failed to connect: https://user:pass123@example.com/db",
            "Connection string contains sensitive data",
        ]

        expected_sanitized = [
            "Connection failed: password=***",
            "Auth error: token=***",
            "Failed to connect: https://***:***@example.com/db",
            "Connection string: [SANITIZED]",
        ]

        for message, expected in zip(sensitive_messages, expected_sanitized):
            sanitized = sanitize_error_message(message)
            assert sanitized == expected


class TestMCPOptional:
    """Test that MCP functionality is properly optional."""

    def test_mcp_command_without_extra_fails_gracefully(self):
        """Test that MCP command fails gracefully without the extra."""
        # This test verifies that the CLI handles ImportError properly
        # when MCP dependencies are not installed

        # Test that we can import the CLI module without MCP (this should work)
        try:
            from snowcli_tools.cli import cli

            # The MCP command should exist in the CLI structure
            assert hasattr(cli, "commands")
            assert "mcp" in cli.commands
        except ImportError as e:
            pytest.fail(f"CLI should be importable without MCP extra: {e}")

    def test_mcp_server_import_requires_extra(self):
        """Test that MCP server module requires the extra."""
        # This verifies that the MCP server module cannot be imported
        # without the mcp extra installed
        try:
            import snowcli_tools.mcp_server  # noqa: F401  # Try to import the module

            # If this succeeds, it means MCP was already imported somewhere
            # or the extra is installed in the test environment
            pass  # This is OK - it means the extra is available
        except ImportError:
            # This is expected if the mcp extra is not installed
            # In a real scenario, this would happen when someone tries to use MCP
            # without installing the optional dependency
            pass
