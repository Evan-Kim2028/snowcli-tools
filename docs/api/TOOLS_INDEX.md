# MCP Tools Quick Reference

## All 11 Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| [execute_query](tools/execute_query.md) | Execute SQL queries | statement, timeout_seconds |
| [preview_table](tools/preview_table.md) | Quick table preview | table_name, limit |
| [build_catalog](tools/build_catalog.md) | Build metadata catalog | database, format |
| [get_catalog_summary](tools/get_catalog_summary.md) | Get catalog info | catalog_dir |
| [query_lineage](tools/query_lineage.md) | Query dependencies | object_name, direction |
| [build_dependency_graph](tools/build_dependency_graph.md) | Build dep graph | database, format |
| [test_connection](tools/test_connection.md) | Test connectivity | none |
| [health_check](tools/health_check.md) | System health | none |
| [check_profile_config](tools/check_profile_config.md) | Validate profile | none |
| [get_resource_status](tools/get_resource_status.md) | Resource status | check_catalog |
| [check_resource_dependencies](tools/check_resource_dependencies.md) | Resource deps | resource_name |

## By Category

### Query & Data Access
- execute_query
- preview_table

### Metadata & Discovery
- build_catalog
- get_catalog_summary
- query_lineage
- build_dependency_graph

### Health & Diagnostics
- test_connection
- health_check
- check_profile_config
- get_resource_status
- check_resource_dependencies

## Common Workflows

### Getting Started
1. test_connection
2. check_profile_config
3. execute_query (simple test)

### Data Discovery
1. build_catalog
2. get_catalog_summary
3. query_lineage

### Troubleshooting
1. health_check
2. check_profile_config
3. test_connection
4. get_resource_status
