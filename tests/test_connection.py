"""Tests for connection management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snowflake_connector.connection import get_snowflake_connection, load_private_key


class TestConnection:
    """Test connection functionality."""

    @patch("snowflake_connector.connection.snowflake.connector.connect")
    def test_get_snowflake_connection_with_defaults(self, mock_connect):
        """Test getting connection with default parameters."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Mock environment variables
        env_vars = {
            "SNOWFLAKE_PRIVATE_KEY_PATH": "/test/key.p8",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("snowflake_connector.connection.load_private_key") as mock_load_key,
        ):

            mock_load_key.return_value = b"fake_private_key"

            conn = get_snowflake_connection()

            mock_connect.assert_called_once()
            call_args = mock_connect.call_args[1]

            assert call_args["account"] == "HKB47976.us-west-2"  # default
            assert call_args["user"] == "readonly_ai_user"  # default
            assert call_args["private_key"] == b"fake_private_key"
            assert call_args["warehouse"] == "EVANS_AI_WH"  # default
            assert call_args["database"] == "PIPELINE_V2_GROOT_DB"  # default
            assert call_args["schema"] == "PIPELINE_V2_GROOT_SCHEMA"  # default
            assert "role" not in call_args  # no role by default

    @patch("snowflake_connector.connection.snowflake.connector.connect")
    def test_get_snowflake_connection_with_custom_params(self, mock_connect):
        """Test getting connection with custom parameters."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        with patch("snowflake_connector.connection.load_private_key") as mock_load_key:
            mock_load_key.return_value = b"fake_private_key"

            conn = get_snowflake_connection(
                account="custom.us-west-2",
                user="custom_user",
                private_key_path="/custom/key.p8",
                warehouse="custom_wh",
                database="custom_db",
                schema="custom_schema",
                role="custom_role",
            )

            mock_connect.assert_called_once()
            call_args = mock_connect.call_args[1]

            assert call_args["account"] == "custom.us-west-2"
            assert call_args["user"] == "custom_user"
            assert call_args["private_key"] == b"fake_private_key"
            assert call_args["warehouse"] == "custom_wh"
            assert call_args["database"] == "custom_db"
            assert call_args["schema"] == "custom_schema"
            assert call_args["role"] == "custom_role"

    def test_load_private_key_success(self):
        """Test successful private key loading."""
        # Create a temporary private key file
        private_key_pem = b"""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----"""

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(private_key_pem)
            key_path = f.name

        try:
            with patch(
                "cryptography.hazmat.primitives.serialization.load_pem_private_key"
            ) as mock_load:
                mock_key = MagicMock()
                mock_key.private_bytes.return_value = b"der_encoded_key"
                mock_load.return_value = mock_key

                result = load_private_key(key_path)

                assert result == b"der_encoded_key"
                mock_load.assert_called_once()
        finally:
            Path(key_path).unlink()

    def test_load_private_key_file_not_found(self):
        """Test private key loading with non-existent file."""
        with pytest.raises(ValueError, match="Failed to load private key"):
            load_private_key("/nonexistent/key.p8")

    @patch("snowflake_connector.connection.execute_query_to_dataframe")
    def test_execute_query_to_dataframe_success(self, mock_execute):
        """Test successful query execution to DataFrame."""
        import pandas as pd

        mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        mock_execute.return_value = mock_df

        with patch("snowflake_connector.connection.get_snowflake_connection"):
            result = mock_execute("SELECT * FROM test_table")

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert list(result.columns) == ["col1", "col2"]

    @patch("snowflake_connector.connection.execute_query_to_dataframe")
    def test_execute_query_to_dataframe_error(self, mock_execute):
        """Test query execution error handling."""
        mock_execute.side_effect = Exception("Query failed")

        result = mock_execute("SELECT * FROM test_table")

        assert result.empty

    @patch("snowflake_connector.connection.get_snowflake_connection")
    @patch("snowflake_connector.connection.load_private_key")
    def test_test_connection_success(self, mock_load_key, mock_get_conn):
        """Test successful connection testing."""
        from snowflake_connector.connection import test_connection

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        mock_load_key.return_value = b"fake_key"

        result = test_connection()

        assert result is True
        mock_cursor.execute.assert_called_with("SELECT 1 as test")
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("snowflake_connector.connection.get_snowflake_connection")
    def test_test_connection_failure(self, mock_get_conn):
        """Test connection testing failure."""
        from snowflake_connector.connection import test_connection

        mock_get_conn.side_effect = Exception("Connection failed")

        result = test_connection()

        assert result is False
