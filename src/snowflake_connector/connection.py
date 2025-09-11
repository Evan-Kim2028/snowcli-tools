"""Snowflake connection management and basic query execution."""

import os
from typing import Optional

import pandas as pd
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from .config import get_config


def load_private_key(private_key_path: str) -> bytes:
    """Load and prepare the private key for authentication.

    Args:
        private_key_path: Path to RSA private key file

    Returns:
        Private key bytes in DER format

    Raises:
        ValueError: If the private key cannot be loaded
    """
    try:
        # Expand ~ and relative paths to absolute paths
        expanded_path = os.path.expanduser(private_key_path)
        expanded_path = os.path.abspath(expanded_path)

        with open(expanded_path, "rb") as key_file:
            pkey = serialization.load_pem_private_key(
                key_file.read(),
                password=None,  # For unencrypted key; use password='your_passphrase'.encode() if encrypted
                backend=default_backend(),
            )

        return pkey.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except Exception as e:
        msg = f"Failed to load private key from {expanded_path} (original: {private_key_path}): {e}"
        raise ValueError(msg)


def get_snowflake_connection(
    account: Optional[str] = None,
    user: Optional[str] = None,
    private_key_path: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
    role: Optional[str] = None,
) -> snowflake.connector.connection.SnowflakeConnection:
    """Create and return a Snowflake connection.

    If parameters are not provided, they will be taken from the global configuration.

    Args:
        account: Snowflake account identifier
        user: Username for authentication
        private_key_path: Path to RSA private key file
        warehouse: Snowflake warehouse name
        database: Snowflake database name
        schema: Snowflake schema name
        role: Snowflake role (optional)

    Returns:
        Active Snowflake connection
    """
    config = get_config()

    # Use provided parameters or fall back to config
    connection_params = {
        "account": account or config.snowflake.account,
        "user": user or config.snowflake.user,
        "private_key": load_private_key(
            private_key_path or config.snowflake.private_key_path
        ),
        "warehouse": warehouse or config.snowflake.warehouse,
        "database": database or config.snowflake.database,
        "schema": schema or config.snowflake.schema,
    }

    if role or config.snowflake.role:
        connection_params["role"] = role or config.snowflake.role

    return snowflake.connector.connect(**connection_params)


def execute_query_to_dataframe(
    query: str,
    account: Optional[str] = None,
    user: Optional[str] = None,
    private_key_path: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> pd.DataFrame:
    """Execute a SQL query and return results as a pandas DataFrame.

    Args:
        query: SQL query to execute
        account: Snowflake account identifier (optional)
        user: Username for authentication (optional)
        private_key_path: Path to RSA private key file (optional)
        warehouse: Snowflake warehouse name (optional)
        database: Snowflake database name (optional)
        schema: Snowflake schema name (optional)

    Returns:
        Query results as DataFrame
    """
    conn = None
    try:
        conn = get_snowflake_connection(
            account=account,
            user=user,
            private_key_path=private_key_path,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )
        return pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def test_connection(
    account: Optional[str] = None,
    user: Optional[str] = None,
    private_key_path: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> bool:
    """Test Snowflake connection.

    Args:
        account: Snowflake account identifier (optional)
        user: Username for authentication (optional)
        private_key_path: Path to RSA private key file (optional)
        warehouse: Snowflake warehouse name (optional)
        database: Snowflake database name (optional)
        schema: Snowflake schema name (optional)

    Returns:
        True if connection successful, False otherwise
    """
    try:
        conn = get_snowflake_connection(
            account=account,
            user=user,
            private_key_path=private_key_path,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

        cur = conn.cursor()
        cur.execute("SELECT 1 as test")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return result is not None and result[0] == 1
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


# Test the connection when script is run directly
if __name__ == "__main__":
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        print("✅ Connected to Snowflake successfully!")

        # Test query
        cur.execute(
            "SELECT COUNT(*) as total_objects FROM PIPELINE_V2_GROOT_DB.PIPELINE_V2_GROOT_SCHEMA.object_parquet2",
        )
        rows = cur.fetchall()

        # Print results
        print("Test query results:")
        for row in rows:
            print(row)

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()
        print("Connection closed.")
