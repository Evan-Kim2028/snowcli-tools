#!/usr/bin/env python3
"""Quick test to verify MCP server can start with mystenlabs-keypair profile.

This script validates:
1. Snowflake profile exists and is accessible
2. MCP server can initialize
3. Basic SQL validation works
"""

import os
import subprocess
import sys
from pathlib import Path

# Set environment
os.environ["SNOWFLAKE_PROFILE"] = "mystenlabs-keypair"

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_profile_exists():
    """Test that mystenlabs-keypair profile is configured."""
    print("=" * 60)
    print("TEST 1: Verify Snowflake profile exists")
    print("=" * 60)

    result = subprocess.run(
        [".venv/bin/snow", "connection", "list"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    print(f"Exit code: {result.returncode}")
    print(f"\nOutput:\n{result.stdout}")

    if "mystenlabs-keypair" in result.stdout:
        print("✅ PASS: mystenlabs-keypair profile found")
        return True
    else:
        print("❌ FAIL: mystenlabs-keypair profile not found")
        return False


def test_sql_validation():
    """Test SQL validation with the fixed lowercase lists."""
    print("\n" + "=" * 60)
    print("TEST 2: Verify SQL validation fix works")
    print("=" * 60)

    from snowcli_tools.config import SQLPermissions  # noqa: E402
    from snowcli_tools.sql_validation import validate_sql_statement  # noqa: E402

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    # Test SELECT
    stmt_type, is_valid, error = validate_sql_statement(
        "SELECT 1", allow_list, disallow_list
    )

    print(f"Query: SELECT 1")
    print(f"Statement type: {stmt_type}")
    print(f"Is valid: {is_valid}")

    if is_valid:
        print("✅ PASS: SELECT query is allowed")
        return True
    else:
        print(f"❌ FAIL: SELECT query blocked: {error}")
        return False


def test_mcp_imports():
    """Test that MCP server can import successfully."""
    print("\n" + "=" * 60)
    print("TEST 3: Verify MCP server imports")
    print("=" * 60)

    try:
        # Import MCP server components
        from snowcli_tools.mcp_server import (  # noqa: E402
            ExecuteQueryTool,
            HealthCheckTool,
        )

        print("✅ PASS: MCP server imports successful")
        print(f"  - ExecuteQueryTool: {ExecuteQueryTool}")
        print(f"  - HealthCheckTool: {HealthCheckTool}")
        return True
    except Exception as e:
        print(f"❌ FAIL: MCP import error: {e}")
        return False


def main():
    """Run all startup tests."""
    print("\n" + "=" * 60)
    print("MCP SERVER STARTUP VERIFICATION")
    print("=" * 60)
    print(f"\nProject root: {project_root}")
    print(f"Profile: {os.environ.get('SNOWFLAKE_PROFILE')}")

    tests = [
        ("Profile exists", test_profile_exists),
        ("SQL validation", test_sql_validation),
        ("MCP imports", test_mcp_imports),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(results.values())
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All checks passed! MCP server is ready.")
        print("\nNext step: Restart Factory to load the MCP server")
        print("Then you can test with:")
        print("  mcp__snowcli-tools__execute_query(statement='SELECT 1')")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
