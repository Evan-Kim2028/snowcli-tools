#!/usr/bin/env python3
"""Test script to validate SQL validation bug fix.

This script tests that the lowercase statement type fix in config.py
and sql_validation.py correctly allows SELECT queries.

Bug: SQL validation was failing because:
- config.py returned capitalized types: ["Select", "Show", ...]
- Upstream validation expects lowercase: ["select", "show", ...]

Fix: Changed get_allow_list() and get_disallow_list() to return lowercase.
"""

import sys
from pathlib import Path

# Add src to path for imports
# ruff: noqa: E402
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from snowcli_tools.config import SQLPermissions  # noqa: E402
from snowcli_tools.sql_validation import validate_sql_statement  # noqa: E402


def test_lowercase_lists():
    """Test that permission lists return lowercase statement types."""
    print("=" * 60)
    print("TEST 1: Verify permission lists are lowercase")
    print("=" * 60)

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    print(f"\nAllow list: {allow_list}")
    print(f"Disallow list: {disallow_list}")

    # All should be lowercase
    assert all(
        t.islower() for t in allow_list
    ), "Allow list contains non-lowercase types"
    assert all(
        t.islower() for t in disallow_list
    ), "Disallow list contains non-lowercase types"

    # Check expected defaults
    assert "select" in allow_list, "select not in allow list"
    assert "delete" in disallow_list, "delete not in disallow list"
    assert "drop" in disallow_list, "drop not in disallow list"

    print("✅ PASS: All lists are lowercase")
    return True


def test_select_query_validation():
    """Test that SELECT queries are allowed."""
    print("\n" + "=" * 60)
    print("TEST 2: Validate SELECT query is allowed")
    print("=" * 60)

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    test_query = "SELECT 1"
    print(f"\nQuery: {test_query}")

    stmt_type, is_valid, error_msg = validate_sql_statement(
        test_query, allow_list, disallow_list
    )

    print(f"Statement type: {stmt_type}")
    print(f"Is valid: {is_valid}")
    print(f"Error: {error_msg}")

    assert is_valid, f"SELECT query should be valid, got error: {error_msg}"
    assert stmt_type == "Select", f"Expected 'Select', got '{stmt_type}'"
    assert error_msg is None, "SELECT query should not have error message"

    print("✅ PASS: SELECT query validated successfully")
    return True


def test_delete_blocked():
    """Test that DELETE queries are blocked with alternatives."""
    print("\n" + "=" * 60)
    print("TEST 3: Validate DELETE is blocked with alternatives")
    print("=" * 60)

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    test_query = "DELETE FROM test_table WHERE id = 1"
    print(f"\nQuery: {test_query}")

    stmt_type, is_valid, error_msg = validate_sql_statement(
        test_query, allow_list, disallow_list
    )

    print(f"Statement type: {stmt_type}")
    print(f"Is valid: {is_valid}")
    print(f"Error message:\n{error_msg}")

    assert not is_valid, "DELETE query should be blocked"
    assert stmt_type == "Delete", f"Expected 'Delete', got '{stmt_type}'"
    assert error_msg is not None, "DELETE should have error message"
    assert "Safe alternatives" in error_msg, "Error should include safe alternatives"

    print("✅ PASS: DELETE blocked with alternatives")
    return True


def test_drop_blocked():
    """Test that DROP queries are blocked with alternatives."""
    print("\n" + "=" * 60)
    print("TEST 4: Validate DROP is blocked with alternatives")
    print("=" * 60)

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    test_query = "DROP TABLE test_table"
    print(f"\nQuery: {test_query}")

    stmt_type, is_valid, error_msg = validate_sql_statement(
        test_query, allow_list, disallow_list
    )

    print(f"Statement type: {stmt_type}")
    print(f"Is valid: {is_valid}")
    print(f"Error message:\n{error_msg}")

    assert not is_valid, "DROP query should be blocked"
    assert stmt_type == "Drop", f"Expected 'Drop', got '{stmt_type}'"
    assert error_msg is not None, "DROP should have error message"
    assert "Safe alternatives" in error_msg, "Error should include safe alternatives"

    print("✅ PASS: DROP blocked with alternatives")
    return True


def test_information_schema_query():
    """Test INFORMATION_SCHEMA query (common use case)."""
    print("\n" + "=" * 60)
    print("TEST 5: Validate INFORMATION_SCHEMA query")
    print("=" * 60)

    permissions = SQLPermissions()
    allow_list = permissions.get_allow_list()
    disallow_list = permissions.get_disallow_list()

    test_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'TABLES'
        LIMIT 5
    """
    print(f"\nQuery: {test_query.strip()}")

    stmt_type, is_valid, error_msg = validate_sql_statement(
        test_query, allow_list, disallow_list
    )

    print(f"Statement type: {stmt_type}")
    print(f"Is valid: {is_valid}")
    print(f"Error: {error_msg}")

    assert is_valid, f"INFORMATION_SCHEMA query should be valid, got error: {error_msg}"
    assert stmt_type == "Select", f"Expected 'Select', got '{stmt_type}'"

    print("✅ PASS: INFORMATION_SCHEMA query validated successfully")
    return True


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("SQL VALIDATION BUG FIX VERIFICATION")
    print("=" * 60)
    print("\nTesting case sensitivity fix for SQL validation")
    print("Bug: Capitalized types didn't match lowercase comparison")
    print("Fix: Changed allow/disallow lists to return lowercase")

    tests = [
        test_lowercase_lists,
        test_select_query_validation,
        test_delete_blocked,
        test_drop_blocked,
        test_information_schema_query,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✅ All tests passed! SQL validation bug fix is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
