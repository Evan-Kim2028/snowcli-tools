"""Parallel Query Executor for Snowflake.

Efficiently execute multiple queries in parallel for JSON object retrieval.
Supports connection pooling, progress tracking, error handling, and result aggregation.
"""

import asyncio
import builtins
import contextlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import polars as pl
import snowflake.connector

from .config import get_config
from .connection import load_private_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose Snowflake connector logging
logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
logging.getLogger("snowflake.connector.connection").setLevel(logging.WARNING)


@dataclass
class QueryResult:
    """Result container for individual query execution."""

    object_name: str
    query: str
    success: bool
    data: Optional[pl.DataFrame] = None
    json_data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    row_count: int = 0


@dataclass
class ParallelQueryConfig:
    """Configuration for parallel query execution."""

    max_concurrent_queries: int = 5
    connection_pool_size: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 300

    @classmethod
    def from_global_config(cls) -> "ParallelQueryConfig":
        """Create config from global configuration."""
        config = get_config()
        return cls(
            max_concurrent_queries=config.max_concurrent_queries,
            connection_pool_size=config.connection_pool_size,
            retry_attempts=config.retry_attempts,
            retry_delay=config.retry_delay,
            timeout_seconds=config.timeout_seconds,
        )


class SnowflakeConnectionPool:
    """Connection pool for managing Snowflake connections efficiently."""

    def __init__(self, config: Dict[str, Any], pool_size: int = 10):
        self.config = config
        self.pool_size = pool_size
        self.connections: List[snowflake.connector.connection.SnowflakeConnection] = []
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool."""
        successful_connections = 0
        for i in range(self.pool_size):
            try:
                conn = snowflake.connector.connect(**self.config)
                self.connections.append(conn)
                successful_connections += 1
            except Exception as e:
                logger.warning(
                    f"Failed to create connection {i + 1}/{self.pool_size}: {e}",
                )

        if successful_connections > 0:
            logger.info(
                f"🔗 Initialized connection pool: {successful_connections}/{self.pool_size} connections",
            )
        else:
            logger.error("❌ Failed to initialize any connections in pool")

    def get_connection(self) -> snowflake.connector.connection.SnowflakeConnection:
        """Get an available connection from the pool."""
        if not self.connections:
            # Create new connection if pool is empty
            try:
                conn = snowflake.connector.connect(**self.config)
                logger.debug("Created new connection outside pool")
                return conn
            except Exception as e:
                logger.exception(f"Failed to create new connection: {e}")
                raise

        return self.connections.pop()

    def return_connection(
        self, conn: snowflake.connector.connection.SnowflakeConnection
    ):
        """Return a connection to the pool."""
        if len(self.connections) < self.pool_size:
            self.connections.append(conn)
        else:
            conn.close()

    def close_all(self):
        """Close all connections in the pool."""
        if self.connections:
            logger.debug(f"Closing {len(self.connections)} connections")
            for conn in self.connections:
                with contextlib.suppress(builtins.BaseException):
                    conn.close()
            self.connections.clear()


class ParallelQueryExecutor:
    """
    Execute multiple Snowflake queries in parallel.

    Optimized for JSON object retrieval with:
    - Connection pooling for efficient resource usage
    - Configurable concurrency limits
    - Progress tracking and error handling
    - Result aggregation and formatting
    """

    def __init__(self, config: Optional[ParallelQueryConfig] = None):
        self.config = config or ParallelQueryConfig.from_global_config()
        self.connection_pool: Optional[SnowflakeConnectionPool] = None

    def _create_connection_config(
        self, private_key_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Snowflake connection configuration."""
        config = get_config()

        private_key = load_private_key(
            private_key_path or config.snowflake.private_key_path
        )

        connection_config = {
            "account": config.snowflake.account,
            "user": config.snowflake.user,
            "private_key": private_key,
            "warehouse": config.snowflake.warehouse,
            "database": config.snowflake.database,
            "schema": config.snowflake.schema,
        }

        if config.snowflake.role:
            connection_config["role"] = config.snowflake.role

        return connection_config

    def _execute_single_query(
        self,
        query: str,
        object_name: str,
        connection_config: Dict[str, Any],
    ) -> QueryResult:
        """Execute a single query and return results."""
        start_time = time.time()

        for attempt in range(self.config.retry_attempts):
            conn = None
            try:
                # Get connection from pool or create new one
                if self.connection_pool:
                    conn = self.connection_pool.get_connection()
                else:
                    conn = snowflake.connector.connect(**connection_config)

                cur = conn.cursor()

                # Set statement timeout if configured
                if (
                    hasattr(self.config, "timeout_seconds")
                    and self.config.timeout_seconds > 0
                ):
                    cur.execute(
                        f"SET STATEMENT_TIMEOUT_IN_SECONDS = {self.config.timeout_seconds}",
                    )
                    cur.execute("SET ABORT_DETACHED_QUERY = TRUE")

                # Execute query
                cur.execute(query)

                # Fetch results
                rows = cur.fetchall()
                columns = (
                    [desc[0] for desc in cur.description] if cur.description else []
                )

                # Convert to DataFrame
                df = (
                    pl.DataFrame(rows, schema=columns, strict=False)
                    if rows
                    else pl.DataFrame()
                )

                # Extract JSON data if available
                json_data = None
                if "object_json" in df.columns:
                    json_data = []
                    object_json_values = df.select("object_json").to_series().to_list()
                    for json_str in object_json_values:
                        try:
                            if json_str:
                                json_data.append(json.loads(json_str))
                        except (json.JSONDecodeError, TypeError):
                            continue

                execution_time = time.time() - start_time

                result = QueryResult(
                    object_name=object_name,
                    query=query,
                    success=True,
                    data=df,
                    json_data=json_data,
                    execution_time=execution_time,
                    row_count=len(df),
                )

                logger.info(
                    f"✅ {object_name}: {len(df)} rows in {execution_time:.2f}s",
                )
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Attempt {attempt + 1}: {e!s}"

                if attempt < self.config.retry_attempts - 1:
                    logger.warning(
                        f"⚠️  {object_name} failed ({error_msg}), retrying in {self.config.retry_delay}s...",
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    logger.exception(
                        f"❌ {object_name} failed after {self.config.retry_attempts} attempts: {error_msg}",
                    )
                    return QueryResult(
                        object_name=object_name,
                        query=query,
                        success=False,
                        error=error_msg,
                        execution_time=execution_time,
                    )

            finally:
                if conn:
                    if self.connection_pool:
                        self.connection_pool.return_connection(conn)
                    else:
                        with contextlib.suppress(builtins.BaseException):
                            conn.close()

    async def execute_queries_async(
        self,
        queries: Dict[str, str],
        private_key_path: Optional[str] = None,
    ) -> Dict[str, QueryResult]:
        """
        Execute multiple queries in parallel using asyncio.

        Args:
            queries: Dict mapping object names to SQL queries
            private_key_path: Path to private key file (optional)

        Returns:
            Dict mapping object names to QueryResult objects
        """
        connection_config = self._create_connection_config(private_key_path)
        logger.info("🔗 Establishing database connections...")
        self.connection_pool = SnowflakeConnectionPool(
            connection_config,
            self.config.connection_pool_size,
        )

        try:
            # Execute queries in parallel using ThreadPoolExecutor
            results: Dict[str, QueryResult] = {}
            logger.info(f"⚡ Executing {len(queries)} queries in parallel...")

            with ThreadPoolExecutor(
                max_workers=self.config.max_concurrent_queries,
            ) as executor:
                # Submit all queries
                future_to_object = {
                    executor.submit(
                        self._execute_single_query,
                        query,
                        object_name,
                        connection_config,
                    ): object_name
                    for object_name, query in queries.items()
                }

                # Process completed queries
                for future in as_completed(
                    future_to_object,
                    timeout=self.config.timeout_seconds,
                ):
                    object_name = future_to_object[future]
                    try:
                        result = future.result()
                        results[object_name] = result
                    except Exception as e:
                        logger.exception(f"Unexpected error for {object_name}: {e}")
                        results[object_name] = QueryResult(
                            object_name=object_name,
                            query=queries[object_name],
                            success=False,
                            error=f"Unexpected error: {e!s}",
                        )

            return results

        finally:
            if self.connection_pool:
                self.connection_pool.close_all()

    def execute_single_query(
        self,
        query: str,
        object_name: str = "query",
        private_key_path: Optional[str] = None,
    ) -> QueryResult:
        """Execute a single query.

        Args:
            query: SQL query string
            object_name: Name identifier for the query
            private_key_path: Path to private key file (optional)

        Returns:
            QueryResult with execution details
        """
        conn_config = self._create_connection_config(private_key_path)
        return self._execute_single_query(query, object_name, conn_config)

    def execute_queries(
        self,
        queries: Dict[str, str],
        private_key_path: Optional[str] = None,
    ) -> Dict[str, QueryResult]:
        """
        Synchronous wrapper for execute_queries_async.

        Args:
            queries: Dict mapping object names to SQL queries
            private_key_path: Path to private key file (optional)

        Returns:
            Dict mapping object names to QueryResult objects
        """
        return asyncio.run(self.execute_queries_async(queries, private_key_path))

    def get_execution_summary(self, results: Dict[str, QueryResult]) -> Dict[str, Any]:
        """Generate a summary of query execution results."""
        total_queries = len(results)
        successful_queries = sum(1 for r in results.values() if r.success)
        failed_queries = total_queries - successful_queries

        total_rows = sum(r.row_count for r in results.values() if r.success)
        total_execution_time = sum(r.execution_time for r in results.values())
        avg_execution_time = (
            total_execution_time / total_queries if total_queries > 0 else 0
        )

        # Calculate parallelization efficiency
        sequential_time = sum(r.execution_time for r in results.values())
        parallel_efficiency = (
            sequential_time / total_execution_time if total_execution_time > 0 else 1.0
        )

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (
                successful_queries / total_queries * 100 if total_queries > 0 else 0
            ),
            "total_rows_retrieved": total_rows,
            "total_execution_time": total_execution_time,
            "avg_execution_time_per_query": avg_execution_time,
            "parallel_efficiency": parallel_efficiency,
            "failed_objects": [
                name for name, result in results.items() if not result.success
            ],
        }


# Convenience functions for common use cases


def query_multiple_objects(
    object_queries: Dict[str, str],
    max_concurrent: Optional[int] = None,
    private_key_path: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, QueryResult]:
    """
    Convenience function to query multiple objects in parallel.

    Args:
        object_queries: Dict mapping object names to SQL queries
        max_concurrent: Maximum number of concurrent queries (optional)
        private_key_path: Path to private key file (optional)
        timeout_seconds: Timeout in seconds for individual queries (optional)

    Returns:
        Dict mapping object names to QueryResult objects
    """
    config = ParallelQueryConfig.from_global_config()

    # Override defaults if provided
    if max_concurrent is not None:
        config.max_concurrent_queries = max_concurrent
    if timeout_seconds is not None:
        config.timeout_seconds = timeout_seconds

    executor = ParallelQueryExecutor(config)

    results = executor.execute_queries(object_queries, private_key_path)

    # Print summary
    summary = executor.get_execution_summary(results)
    print("\n📊 Query Summary:")
    print(
        f"   ✅ Successful: {summary['successful_queries']}/{summary['total_queries']}",
    )
    print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"   📋 Total Rows: {summary['total_rows_retrieved']:,}")
    print(f"   ⏱️  Total Time: {summary['total_execution_time']:.2f}s")
    print(f"   🚀 Parallel Efficiency: {summary['parallel_efficiency']:.2f}x")

    if summary["failed_objects"]:
        print(f"   ❌ Failed Objects: {', '.join(summary['failed_objects'])}")

    return results


def create_object_queries(
    object_names: List[str],
    base_query_template: str = "SELECT * FROM object_parquet2 WHERE type = '{object}' LIMIT 100",
) -> Dict[str, str]:
    """
    Create queries for multiple objects using a template.

    Args:
        object_names: List of object names to query
        base_query_template: SQL template with {object} placeholder

    Returns:
        Dict mapping object names to SQL queries
    """
    return {obj: base_query_template.format(object=obj) for obj in object_names}


# Example usage and testing
if __name__ == "__main__":
    # Example: Query multiple object types in parallel
    objects_to_query = [
        "0x1::coin::CoinInfo",
        "0x1::account::Account",
        "0x1::table::Table",
        "0x2::sui::SUI",
        "0x3::staking_pool::StakingPool",
    ]

    # Create queries using template
    queries = create_object_queries(objects_to_query)

    # Execute queries in parallel
    print("🚀 Starting parallel query execution...")
    results = query_multiple_objects(queries, max_concurrent=3)

    # Process results
    for obj_name, result in results.items():
        if result.success:
            print(f"\n✅ {obj_name}:")
            print(f"   Rows: {result.row_count}")
            print(
                f"   JSON objects: {len(result.json_data) if result.json_data else 0}",
            )
        else:
            print(f"\n❌ {obj_name}: {result.error}")
