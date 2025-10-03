# health_check

Get comprehensive health status for the MCP server and Snowflake connection.

## Parameters

None - returns full system status.

## Returns

```json
{
  "status": "healthy",
  "snowflake_connection": true,
  "profile": {
    "name": "default",
    "valid": true
  },
  "resources": {
    "catalog": "available",
    "lineage": "available",
    "cortex": "unavailable"
  },
  "version": "1.8.0",
  "timestamp": 1702345678.9
}
```

## Examples

```python
health = health_check()
print(f"Status: {health['status']}")
print(f"Version: {health['version']}")

if health['snowflake_connection']:
    print("Snowflake: Connected ✓")
else:
    print("Snowflake: Disconnected ✗")
```

## Related

- [test_connection](test_connection.md) - Test Snowflake only
- [get_resource_status](get_resource_status.md) - Resource availability
