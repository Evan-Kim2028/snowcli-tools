import pandas as pd
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def get_snowflake_connection(
    account: str = "HKB47976.us-west-2",
    user: str = "readonly_ai_user",
    private_key_path: str = "/Users/evandekim/Documents/snowflake_keys/rsa_key.p8",
    warehouse: str = "EVANS_AI_WH",
    database: str = "PIPELINE_V2_GROOT_DB",
    schema: str = "PIPELINE_V2_GROOT_SCHEMA",
):
    """
    Create and return a Snowflake connection.

    Args:
        account: Snowflake account identifier
        user: Username for authentication
        private_key_path: Path to RSA private key file
        warehouse: Snowflake warehouse name
        database: Snowflake database name
        schema: Snowflake schema name

    Returns:
        snowflake.connector.connection.SnowflakeConnection: Active Snowflake connection
    """
    # Load the private key
    with open(private_key_path, "rb") as key_file:
        pkey = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # For unencrypted key; use password='your_passphrase'.encode() if encrypted
            backend=default_backend(),
        )

    private_key = pkey.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Connection parameters
    conn_params = {
        "account": account,
        "user": user,
        "private_key": private_key,
        "warehouse": warehouse,
        "database": database,
        "schema": schema,
    }

    # Establish connection
    return snowflake.connector.connect(**conn_params)


def execute_query_to_dataframe(query: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.

    Args:
        query (str): SQL query to execute

    Returns:
        pd.DataFrame: Query results as DataFrame
    """
    conn = None
    try:
        conn = get_snowflake_connection()
        return pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# Test the connection when script is run directly
if __name__ == "__main__":
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        print("Connected to Snowflake successfully!")

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
        print(f"Error: {e}")

    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()
        print("Connection closed.")
