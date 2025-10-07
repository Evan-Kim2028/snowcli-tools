# Rebrand Plan: snowcli-tools → nanuk-mcp

**Document Version**: 1.0
**Date**: October 7, 2025
**Branch**: `v1.9.1-doc-upgrades`
**Status**: Draft for Review

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Rebrand Rationale](#rebrand-rationale)
3. [Impact Analysis](#impact-analysis)
4. [Migration Strategy](#migration-strategy)
5. [Detailed Implementation Plan](#detailed-implementation-plan)
6. [File-by-File Changes](#file-by-file-changes)
7. [Testing & Validation](#testing--validation)
8. [Communication Plan](#communication-plan)
9. [Rollout Timeline](#rollout-timeline)
10. [Risk Mitigation](#risk-mitigation)
11. [Appendix](#appendix)

---

## Executive Summary

### Overview

Rebranding from **snowcli-tools** to **nanuk-mcp** to better reflect:
- MCP-first architecture (not CLI-focused)
- Unique brand identity (not generic "tools")
- Cultural connection (Nanuk = polar bear in Inuit, ties to Snowflake)
- Professional naming convention

### Scope of Changes

| Category | Items to Update | Estimated Time |
|----------|----------------|----------------|
| **Repository** | GitHub repo name, URL | 5 min |
| **Documentation** | 15+ markdown files | 2 hours |
| **Code** | Package name, imports, entry points | 3 hours |
| **Configuration** | pyproject.toml, setup files | 1 hour |
| **Tests** | Import statements, test names | 1 hour |
| **Distribution** | PyPI package name | 30 min |
| **Infrastructure** | CI/CD, URLs, links | 1 hour |
| **Communication** | Announcements, docs | 1 hour |
| **Total** | | **9.5 hours** |

### Success Metrics

- [ ] Zero broken imports after rebrand
- [ ] All tests pass with new package name
- [ ] PyPI package published under new name
- [ ] GitHub redirects from old name working
- [ ] Users can find project under new name

---

## Rebrand Rationale

### Why "nanuk-mcp"?

#### 1. **Better Name Recognition**

**Before**: snowcli-tools
- Generic, forgettable
- Sounds like a CLI tool (we're deprecating CLI!)
- "tools" is vague

**After**: nanuk-mcp
- Unique, memorable
- Clear focus: MCP (Model Context Protocol)
- Professional naming
- Cultural connection to Snowflake (Nanuk = polar bear)

#### 2. **Alignment with Architecture**

| Aspect | snowcli-tools | nanuk-mcp |
|--------|---------------|-----------|
| **Primary Interface** | Implies CLI | Explicitly MCP |
| **Focus** | "tools" (generic) | MCP integration |
| **Brand** | Descriptive | Distinctive |
| **Positioning** | Database tools | AI-first data platform |

#### 3. **Market Positioning**

- **snowcli-tools**: Competes with generic Snowflake utilities
- **nanuk-mcp**: Unique position as Snowflake MCP provider

#### 4. **Future-Proofing**

As MCP ecosystem grows:
- Easier to find: "Snowflake MCP" → nanuk-mcp
- Clearer value prop
- Room to expand beyond just "tools"

---

## Impact Analysis

### What Needs to Change

#### High Impact (Breaking Changes)

1. **Package Name**
   - PyPI: `snowcli-tools` → `nanuk-mcp`
   - Import: `from snowcli_tools` → `from nanuk_mcp`
   - **Impact**: All existing code breaks

2. **GitHub Repository**
   - URL: `github.com/user/snowcli-tools` → `github.com/user/nanuk-mcp`
   - **Impact**: All links break (but GitHub redirects)

3. **Entry Points**
   - CLI: `snowflake-cli` → `nanuk` or `nanuk-cli` (legacy)
   - MCP: `snowcli-mcp` → `nanuk-mcp`
   - **Impact**: Commands change

#### Medium Impact (Documentation)

4. **All Documentation**
   - 15+ markdown files reference old name
   - Code examples with old imports
   - Installation instructions

5. **Configuration Files**
   - pyproject.toml
   - MCP config examples
   - CI/CD files

#### Low Impact (Internal)

6. **Internal Variables**
   - Some variable names
   - Log messages
   - Comments

---

### Backward Compatibility Strategy

#### Option 1: Hard Break (Not Recommended)
- Just change everything
- No backward compatibility
- **Risk**: Breaks all existing users

#### Option 2: Soft Transition (Recommended)
- Publish both packages temporarily
- `snowcli-tools` becomes a "tombstone" package
- Redirects imports to `nanuk-mcp`
- **Timeline**: 6-month transition

#### Option 3: Maintain Both (Not Recommended)
- Keep both packages
- Mirror releases
- **Risk**: Maintenance burden doubles

**Decision**: **Option 2 - Soft Transition**

---

## Migration Strategy

### Three-Phase Approach

#### Phase 1: Preparation (Week 1)
- Create new package structure
- Test imports work with new name
- Prepare documentation
- No public announcement yet

#### Phase 2: Soft Launch (Week 2-3)
- Publish `nanuk-mcp` to PyPI
- Keep `snowcli-tools` as tombstone
- Update all documentation
- Announce rebrand

#### Phase 3: Transition (Months 1-6)
- Support both names
- Gradual user migration
- After 6 months: deprecate old name

---

### Tombstone Package Strategy

**What is a tombstone package?**
A minimal package that redirects to the new name.

**Implementation**:

```python
# snowcli-tools (tombstone) on PyPI
# pyproject.toml
[project]
name = "snowcli-tools"
version = "2.0.0"  # Bump to signal change
description = "DEPRECATED: Use nanuk-mcp instead"
dependencies = ["nanuk-mcp>=2.0.0"]

# __init__.py
import warnings
warnings.warn(
    "snowcli-tools is deprecated. Use nanuk-mcp instead:\n"
    "  pip uninstall snowcli-tools\n"
    "  pip install nanuk-mcp",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from nanuk-mcp
from nanuk_mcp import *  # noqa
```

**User Experience**:
```python
# Old code still works but warns:
from snowcli_tools import CatalogService  # DeprecationWarning
# → Auto-imports from nanuk_mcp
```

---

## Detailed Implementation Plan

### Step 1: Rename Repository (5 minutes)

**GitHub Repository**:
```bash
# GitHub UI:
Settings → General → Repository name
  Old: snowcli-tools
  New: nanuk-mcp

# GitHub automatically creates redirect
# github.com/user/snowcli-tools → github.com/user/nanuk-mcp
```

**Update Local Clone**:
```bash
# Update remote URL
cd /Users/evandekim/Documents/snowcli_tools
git remote set-url origin https://github.com/user/nanuk-mcp.git

# Rename local directory (optional)
cd ..
mv snowcli_tools nanuk_mcp
cd nanuk_mcp
```

**Verification**:
```bash
# Check remote URL
git remote -v
# Should show: nanuk-mcp

# Old URL should redirect
curl -I https://github.com/user/snowcli-tools
# Should redirect to nanuk-mcp
```

---

### Step 2: Update Package Structure (3 hours)

#### 2.1: Rename Package Directory

```bash
# In repository root
cd src/
mv snowcli_tools nanuk_mcp
```

#### 2.2: Update pyproject.toml

**File**: `/Users/evandekim/Documents/nanuk_mcp/pyproject.toml`

**Changes**:
```toml
[project]
name = "nanuk-mcp"  # Was: snowcli-tools
version = "2.0.0"   # Bump major version for breaking change
description = "Snowflake MCP Server - AI-first data operations"  # Updated
authors = [
    {name = "Your Name", email = "you@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
keywords = ["snowflake", "mcp", "ai", "data", "analytics"]  # Updated
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "snowflake-connector-python>=3.0.0",
    "anthropic-mcp-server>=0.1.0",
    "mcp>=0.1.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0.0",
]

legacy-cli = [
    "typer>=0.9.0",
    "click>=8.0.0",
    "rich>=13.0.0",
]

all = [
    "nanuk-mcp[dev]",
    "nanuk-mcp[legacy-cli]",
]

[project.urls]
Homepage = "https://github.com/user/nanuk-mcp"
Documentation = "https://github.com/user/nanuk-mcp/docs"
Repository = "https://github.com/user/nanuk-mcp"
Issues = "https://github.com/user/nanuk-mcp/issues"
Changelog = "https://github.com/user/nanuk-mcp/blob/main/CHANGELOG.md"

[project.scripts]
nanuk-mcp = "nanuk_mcp.mcp_server:main"  # New MCP entry point
nanuk = "nanuk_mcp.legacy.cli:main"  # Legacy CLI

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/nanuk_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
target-version = "py38"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[[tool.mypy.overrides]]
module = "snowflake.*"
ignore_missing_imports = true
```

#### 2.3: Update Package __init__.py

**File**: `/Users/evandekim/Documents/nanuk_mcp/src/nanuk_mcp/__init__.py`

```python
"""
Nanuk MCP - Snowflake MCP Server

AI-first Snowflake operations via Model Context Protocol.
"""

__version__ = "2.0.0"
__name__ = "nanuk-mcp"

# Re-export main components
from nanuk_mcp.services.catalog import CatalogService
from nanuk_mcp.services.lineage import LineageService
from nanuk_mcp.services.query import QueryService
from nanuk_mcp.mcp_server import main as mcp_main

__all__ = [
    "CatalogService",
    "LineageService",
    "QueryService",
    "mcp_main",
    "__version__",
]
```

#### 2.4: Update All Internal Imports

**Find all imports**:
```bash
cd /Users/evandekim/Documents/nanuk_mcp
grep -r "from snowcli_tools" src/ tests/
grep -r "import snowcli_tools" src/ tests/
```

**Replace pattern**:
```bash
# Use sed to replace all at once
find src/ tests/ -type f -name "*.py" -exec sed -i '' \
    's/from snowcli_tools/from nanuk_mcp/g' {} +

find src/ tests/ -type f -name "*.py" -exec sed -i '' \
    's/import snowcli_tools/import nanuk_mcp/g' {} +
```

**Manual verification needed for**:
- String literals (e.g., log messages with package name)
- Comments
- Docstrings
- Configuration files

---

### Step 3: Update Documentation (2 hours)

#### 3.1: Global Search and Replace

**Files to update**:
```bash
cd /Users/evandekim/Documents/nanuk_mcp

# Find all references to old name
grep -r "snowcli-tools\|snowcli_tools" docs/ README.md *.md

# Replace in markdown files
find docs/ README.md *.md -type f -name "*.md" -exec sed -i '' \
    's/snowcli-tools/nanuk-mcp/g' {} +

find docs/ README.md *.md -type f -name "*.md" -exec sed -i '' \
    's/snowcli_tools/nanuk_mcp/g' {} +

# Replace command names
find docs/ README.md *.md -type f -name "*.md" -exec sed -i '' \
    's/snowflake-cli/nanuk/g' {} +

find docs/ README.md *.md -type f -name "*.md" -exec sed -i '' \
    's/snowcli-mcp/nanuk-mcp/g' {} +
```

#### 3.2: Update README.md

**File**: `/Users/evandekim/Documents/nanuk_mcp/README.md`

**Key Changes**:

**Header**:
```markdown
# Nanuk MCP - Snowflake MCP Server

> 🐻‍❄️ AI-first Snowflake operations via Model Context Protocol

Nanuk (Inuit for "polar bear") brings powerful Snowflake data operations
to your AI assistants through the Model Context Protocol (MCP).

[![PyPI version](https://badge.fury.io/py/nanuk-mcp.svg)](https://pypi.org/project/nanuk-mcp/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
# Install
pip install nanuk-mcp

# Configure
nanuk-mcp --configure

# Run MCP server
nanuk-mcp
```

## What is Nanuk?

Nanuk is a Model Context Protocol (MCP) server that provides AI assistants
with powerful Snowflake operations:

- 🔍 Query execution and data exploration
- 📊 Table profiling and statistics
- 🔗 Data lineage tracking
- 📚 Catalog building and metadata
- ⚡ Performance optimized for AI workflows
```

**Installation Section**:
```markdown
## Installation

### For AI Assistant Integration (Recommended)

```bash
pip install nanuk-mcp
```

### For Development

```bash
git clone https://github.com/user/nanuk-mcp.git
cd nanuk-mcp
uv pip install -e ".[dev]"
```

### Migrating from snowcli-tools?

See [Migration Guide](docs/migration-from-snowcli-tools.md)
```

**Examples Update**:
```markdown
## Examples

### Claude Code Integration

```json
{
  "mcpServers": {
    "nanuk": {
      "command": "nanuk-mcp",
      "args": ["--profile", "production"]
    }
  }
}
```

### Python API

```python
from nanuk_mcp import QueryService

# Execute query
service = QueryService(profile="production")
result = service.execute("SELECT * FROM users LIMIT 10")
```
```

#### 3.3: Update All Documentation Files

**Files to manually review and update**:

1. **docs/getting-started.md**
   - Package name in installation
   - Command examples
   - Import statements

2. **docs/mcp/mcp_server_user_guide.md**
   - MCP server command
   - Configuration examples

3. **docs/architecture.md**
   - Package structure diagrams
   - Component names

4. **docs/api/*.md** (all tool docs)
   - Tool namespace
   - Example code

5. **CHANGELOG.md**
   - Add entry for rebrand

6. **CONTRIBUTING.md**
   - Repository URL
   - Package name references

7. **docs/migration-from-snowcli-tools.md** (NEW)
   - Create migration guide for existing users

---

### Step 4: Update Configuration Files (1 hour)

#### 4.1: MCP Configuration Examples

**File**: `docs/mcp/mcp_server_user_guide.md`

**Update examples**:
```json
{
  "mcpServers": {
    "nanuk": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/nanuk-mcp",
        "run",
        "nanuk-mcp"
      ],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

#### 4.2: GitHub Actions

**Files**: `.github/workflows/*.yml`

**Update references**:
```yaml
name: Test Nanuk MCP

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/
```

#### 4.3: Pre-commit Configuration

**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
        name: Format code (nanuk-mcp)
```

---

### Step 5: Update Tests (1 hour)

#### 5.1: Update Import Statements

**Pattern**:
```python
# Before
from snowcli_tools.services import CatalogService
from snowcli_tools import __version__

# After
from nanuk_mcp.services import CatalogService
from nanuk_mcp import __version__
```

**Automated replacement**:
```bash
cd /Users/evandekim/Documents/nanuk_mcp

# Update all test files
find tests/ -type f -name "*.py" -exec sed -i '' \
    's/from snowcli_tools/from nanuk_mcp/g' {} +

find tests/ -type f -name "*.py" -exec sed -i '' \
    's/import snowcli_tools/import nanuk_mcp/g' {} +
```

#### 5.2: Update Test Names

**Files with package name in test names**:
```python
# Before
def test_snowcli_tools_version():
    from snowcli_tools import __version__
    assert __version__

# After
def test_nanuk_mcp_version():
    from nanuk_mcp import __version__
    assert __version__
```

#### 5.3: Update Mock Objects

**Pattern**:
```python
# Before
@patch('snowcli_tools.services.catalog.CatalogService')
def test_catalog(mock_service):
    pass

# After
@patch('nanuk_mcp.services.catalog.CatalogService')
def test_catalog(mock_service):
    pass
```

---

### Step 6: PyPI Package Distribution (30 minutes)

#### 6.1: Register New Package on PyPI

**Steps**:
1. Create account on PyPI (if needed)
2. Configure PyPI token
3. Build package
4. Upload to PyPI

**Commands**:
```bash
cd /Users/evandekim/Documents/nanuk_mcp

# Build package
uv build

# Upload to PyPI
uv publish

# Or using twine
pip install twine
twine upload dist/nanuk_mcp-2.0.0*
```

**Verification**:
```bash
# Test installation from PyPI
pip install nanuk-mcp

# Verify it works
python -c "from nanuk_mcp import __version__; print(__version__)"
# Should print: 2.0.0
```

#### 6.2: Create Tombstone Package

**New repository**: `snowcli-tools-tombstone/`

**Structure**:
```
snowcli-tools-tombstone/
├── pyproject.toml
├── src/
│   └── snowcli_tools/
│       └── __init__.py
└── README.md
```

**pyproject.toml**:
```toml
[project]
name = "snowcli-tools"
version = "2.0.0"
description = "DEPRECATED: This package has been renamed to nanuk-mcp"
dependencies = ["nanuk-mcp>=2.0.0"]
readme = "README.md"

[project.urls]
Homepage = "https://github.com/user/nanuk-mcp"
```

**src/snowcli_tools/__init__.py**:
```python
"""
DEPRECATED: snowcli-tools has been renamed to nanuk-mcp

This package is now a redirect to nanuk-mcp.
Please update your code:

    pip uninstall snowcli-tools
    pip install nanuk-mcp

Then update imports:
    from snowcli_tools → from nanuk_mcp
"""

import warnings

warnings.warn(
    "\n"
    "╔═══════════════════════════════════════════════════════════╗\n"
    "║                  PACKAGE RENAMED                          ║\n"
    "╠═══════════════════════════════════════════════════════════╣\n"
    "║ snowcli-tools has been renamed to nanuk-mcp               ║\n"
    "║                                                           ║\n"
    "║ Please update your installation:                         ║\n"
    "║   pip uninstall snowcli-tools                            ║\n"
    "║   pip install nanuk-mcp                                  ║\n"
    "║                                                           ║\n"
    "║ Then update your imports:                                ║\n"
    "║   from snowcli_tools → from nanuk_mcp                    ║\n"
    "║                                                           ║\n"
    "║ This redirect will be removed in 6 months (Apr 2026)    ║\n"
    "╚═══════════════════════════════════════════════════════════╝\n",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from nanuk-mcp
from nanuk_mcp import *  # noqa: F401, F403
```

**README.md**:
```markdown
# snowcli-tools → nanuk-mcp

⚠️ **This package has been renamed to `nanuk-mcp`**

## Migration Guide

### 1. Uninstall old package
```bash
pip uninstall snowcli-tools
```

### 2. Install new package
```bash
pip install nanuk-mcp
```

### 3. Update imports
```python
# Before
from snowcli_tools import CatalogService

# After
from nanuk_mcp import CatalogService
```

## Why the rename?

- **MCP-first**: Name reflects focus on Model Context Protocol
- **Unique branding**: "Nanuk" (polar bear) is memorable and distinctive
- **CLI deprecation**: "snowcli" implied CLI focus, which is deprecated

## Timeline

- **Oct 2025**: Tombstone package published
- **Apr 2026**: Tombstone package removed

See full migration guide: https://github.com/user/nanuk-mcp/docs/migration-from-snowcli-tools.md
```

**Publish tombstone**:
```bash
cd snowcli-tools-tombstone/
uv build
uv publish
```

---

### Step 7: Update Infrastructure (1 hour)

#### 7.1: CI/CD Pipeline

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Test Nanuk MCP

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/ -v --cov=nanuk_mcp --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: nanuk-mcp-coverage
```

#### 7.2: Documentation Hosting

**If using Read the Docs**:
```yaml
# .readthedocs.yml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - dev

sphinx:
  configuration: docs/conf.py
```

**Update docs/conf.py**:
```python
project = 'Nanuk MCP'
copyright = '2025, Your Name'
author = 'Your Name'

html_title = 'Nanuk MCP Documentation'
html_short_title = 'Nanuk MCP'
```

#### 7.3: Update Badges

**README.md badges**:
```markdown
[![PyPI version](https://badge.fury.io/py/nanuk-mcp.svg)](https://pypi.org/project/nanuk-mcp/)
[![Tests](https://github.com/user/nanuk-mcp/workflows/Test/badge.svg)](https://github.com/user/nanuk-mcp/actions)
[![codecov](https://codecov.io/gh/user/nanuk-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/user/nanuk-mcp)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

---

## File-by-File Changes

### Critical Files (Must Update)

#### 1. pyproject.toml
```toml
[project]
name = "nanuk-mcp"  # Was: snowcli-tools
# ... (see Step 2.2 above)
```

#### 2. README.md
```markdown
# Nanuk MCP - Snowflake MCP Server
# ... (see Step 3.2 above)
```

#### 3. src/snowcli_tools/ → src/nanuk_mcp/
```bash
# Rename entire directory
mv src/snowcli_tools src/nanuk_mcp
```

#### 4. All Python files in src/
```bash
# Update all imports
find src/ -type f -name "*.py" -exec sed -i '' \
    's/from snowcli_tools/from nanuk_mcp/g' {} +
```

#### 5. All Python files in tests/
```bash
# Update all imports
find tests/ -type f -name "*.py" -exec sed -i '' \
    's/from snowcli_tools/from nanuk_mcp/g' {} +
```

#### 6. docs/getting-started.md
```markdown
## Installation

```bash
pip install nanuk-mcp
```

## Quick Start

```python
from nanuk_mcp import QueryService
```
```

#### 7. docs/mcp/mcp_server_user_guide.md
```json
{
  "mcpServers": {
    "nanuk": {
      "command": "nanuk-mcp"
    }
  }
}
```

#### 8. .github/workflows/*.yml
```yaml
name: Test Nanuk MCP
# Update all references
```

#### 9. CHANGELOG.md
```markdown
## [2.0.0] - 2025-10-XX

### Breaking Changes
- **Package renamed from `snowcli-tools` to `nanuk-mcp`**
  - PyPI package: `pip install nanuk-mcp`
  - Imports: `from nanuk_mcp import ...`
  - See migration guide: docs/migration-from-snowcli-tools.md
```

#### 10. docs/migration-from-snowcli-tools.md (NEW)
```markdown
# Migration Guide: snowcli-tools → nanuk-mcp

[Full migration guide - see Communication Plan section]
```

---

### Secondary Files (Should Update)

#### 11. CONTRIBUTING.md
```markdown
# Contributing to Nanuk MCP

## Getting Started

```bash
git clone https://github.com/user/nanuk-mcp.git
cd nanuk-mcp
```
```

#### 12. docs/architecture.md
```markdown
# Architecture

Nanuk MCP consists of:
- `nanuk_mcp.services`: Core business logic
- `nanuk_mcp.mcp_server`: MCP interface
```

#### 13. All docs/api/*.md files
```markdown
# Tool: execute_query

Part of the Nanuk MCP toolkit.

```python
from nanuk_mcp import QueryService
```
```

#### 14. examples/ (if any)
```python
# Update all example scripts
from nanuk_mcp import CatalogService
```

#### 15. scripts/ (if any)
```bash
# Update any shell scripts with package name
#!/bin/bash
# Nanuk MCP helper script
```

---

### Tertiary Files (Nice to Update)

#### 16. LICENSE
```
MIT License

Copyright (c) 2025 Nanuk MCP Contributors
```

#### 17. CODE_OF_CONDUCT.md
```markdown
# Nanuk MCP Code of Conduct
```

#### 18. SECURITY.md
```markdown
# Security Policy for Nanuk MCP
```

---

## Testing & Validation

### Pre-Rebrand Testing

**Before making any changes**:

```bash
cd /Users/evandekim/Documents/snowcli_tools

# 1. Run full test suite
pytest tests/ -v

# 2. Build package
uv build

# 3. Test local install
pip install -e .

# 4. Test MCP server starts
snowcli-mcp --help

# 5. Test imports
python -c "from snowcli_tools import __version__; print(__version__)"

# All tests should pass before proceeding
```

---

### Post-Rebrand Testing

**After completing rebrand**:

```bash
cd /Users/evandekim/Documents/nanuk_mcp

# 1. Clean build artifacts
rm -rf dist/ build/ *.egg-info
uv clean

# 2. Build new package
uv build

# 3. Test local install
pip uninstall snowcli-tools nanuk-mcp  # Clean slate
pip install -e .

# 4. Test imports
python -c "from nanuk_mcp import __version__; print(__version__)"
# Should print: 2.0.0

# 5. Test entry points
nanuk-mcp --version
# Should work

# 6. Run full test suite
pytest tests/ -v --cov=nanuk_mcp
# All tests should pass

# 7. Test MCP server
nanuk-mcp --help
# Should show help text

# 8. Integration test
python -c "
from nanuk_mcp import CatalogService, QueryService
print('✓ Imports working')
"
```

---

### Validation Checklist

**Code Changes**:
- [ ] Package directory renamed: `src/nanuk_mcp/`
- [ ] All imports updated: `from nanuk_mcp`
- [ ] All tests pass
- [ ] No references to old name in code
- [ ] Entry points work: `nanuk-mcp` command
- [ ] Version is 2.0.0

**Documentation**:
- [ ] README.md updated
- [ ] All docs/*.md files updated
- [ ] Code examples use new name
- [ ] Installation instructions correct
- [ ] No broken links
- [ ] Migration guide created

**Configuration**:
- [ ] pyproject.toml updated
- [ ] GitHub Actions updated
- [ ] Pre-commit config updated
- [ ] MCP config examples updated

**Distribution**:
- [ ] Package builds successfully
- [ ] Published to PyPI as `nanuk-mcp`
- [ ] Tombstone package published
- [ ] GitHub repo renamed
- [ ] GitHub redirect works

**Communication**:
- [ ] CHANGELOG.md entry added
- [ ] Migration guide published
- [ ] Announcement drafted
- [ ] Social media posts ready

---

## Communication Plan

### Announcement Templates

#### 1. GitHub Release Notes (v2.0.0)

```markdown
# v2.0.0 - Package Rebrand: snowcli-tools → nanuk-mcp

## 🎉 Major Announcement

We're excited to announce that **snowcli-tools** has been rebranded to **nanuk-mcp**!

### Why "Nanuk"?

- 🐻‍❄️ Nanuk (Inuit for "polar bear") connects to Snowflake's arctic theme
- 🎯 MCP-first: Name reflects our focus on Model Context Protocol
- ✨ Unique & memorable: Stands out in the MCP ecosystem

### What Changed?

**Package Name**:
```bash
# Before
pip install snowcli-tools
from snowcli_tools import CatalogService

# After
pip install nanuk-mcp
from nanuk_mcp import CatalogService
```

**Commands**:
```bash
# Before
snowcli-mcp

# After
nanuk-mcp
```

### Migration Guide

See our comprehensive [Migration Guide](docs/migration-from-snowcli-tools.md) for step-by-step instructions.

**Quick Migration**:
```bash
# 1. Uninstall old package
pip uninstall snowcli-tools

# 2. Install new package
pip install nanuk-mcp

# 3. Update imports in your code
# from snowcli_tools → from nanuk_mcp
```

### Backward Compatibility

For the next 6 months (until April 2026), the old `snowcli-tools` package will remain on PyPI as a tombstone that redirects to `nanuk-mcp`. This gives you time to migrate.

### Breaking Changes

- Package name changed
- Import statements must be updated
- Command names changed

### What Stays the Same?

- All functionality
- API compatibility
- Configuration format
- MCP protocol support

### Questions?

- Migration issues? [Open an issue](https://github.com/user/nanuk-mcp/issues)
- General questions? [Discussions](https://github.com/user/nanuk-mcp/discussions)

Thank you for your support! 🐻‍❄️
```

---

#### 2. PyPI Package Description

**nanuk-mcp PyPI page**:

```markdown
# Nanuk MCP - Snowflake MCP Server

🐻‍❄️ AI-first Snowflake operations via Model Context Protocol

Nanuk (Inuit for "polar bear") brings powerful Snowflake data operations to your AI assistants through the Model Context Protocol (MCP).

## Features

- 🔍 Execute SQL queries
- 📊 Profile tables and analyze data
- 🔗 Track data lineage
- 📚 Build and query metadata catalogs
- ⚡ Optimized for AI workflows

## Quick Start

```bash
pip install nanuk-mcp
nanuk-mcp --configure
nanuk-mcp
```

## Documentation

[Full documentation](https://github.com/user/nanuk-mcp/docs)

## Migrating from snowcli-tools?

This package was formerly known as `snowcli-tools`. See the [migration guide](https://github.com/user/nanuk-mcp/docs/migration-from-snowcli-tools.md).
```

---

#### 3. Migration Guide Document

**File**: `docs/migration-from-snowcli-tools.md`

```markdown
# Migration Guide: snowcli-tools → nanuk-mcp

## Overview

As of version 2.0.0, **snowcli-tools** has been renamed to **nanuk-mcp** to better reflect:
- MCP-first architecture
- Unique brand identity
- Future direction of the project

## Why the Rebrand?

### Before: snowcli-tools
- Generic, forgettable name
- "CLI" implied command-line focus (we're deprecating CLI)
- "tools" was vague

### After: nanuk-mcp
- Unique, memorable name
- "MCP" explicitly highlights Model Context Protocol
- "Nanuk" (polar bear) connects to Snowflake's arctic theme
- Professional, distinctive branding

## Migration Steps

### Step 1: Uninstall Old Package

```bash
pip uninstall snowcli-tools
```

### Step 2: Install New Package

```bash
pip install nanuk-mcp
```

### Step 3: Update Imports

**Python Code**:
```python
# Before
from snowcli_tools import CatalogService, QueryService
from snowcli_tools.services import LineageService

# After
from nanuk_mcp import CatalogService, QueryService
from nanuk_mcp.services import LineageService
```

**Find/Replace in Your Project**:
```bash
# Find all occurrences
grep -r "from snowcli_tools" .
grep -r "import snowcli_tools" .

# Replace (bash)
find . -type f -name "*.py" -exec sed -i '' \
    's/from snowcli_tools/from nanuk_mcp/g' {} +

find . -type f -name "*.py" -exec sed -i '' \
    's/import snowcli_tools/import nanuk_mcp/g' {} +
```

### Step 4: Update Commands

**MCP Server**:
```bash
# Before
snowcli-mcp --profile my-profile

# After
nanuk-mcp --profile my-profile
```

**CLI (Legacy)**:
```bash
# Before
snowflake-cli verify

# After
nanuk verify  # (if you installed legacy-cli)
```

### Step 5: Update Configuration

**MCP Server Config** (e.g., Claude Code):
```json
{
  "mcpServers": {
    "snowflake": {
      "command": "nanuk-mcp",
      "args": ["--profile", "my-profile"]
    }
  }
}
```

### Step 6: Update Dependencies

**requirements.txt**:
```txt
# Before
snowcli-tools>=1.9.0

# After
nanuk-mcp>=2.0.0
```

**pyproject.toml**:
```toml
[project]
dependencies = [
    "nanuk-mcp>=2.0.0",  # Was: snowcli-tools>=1.9.0
]
```

### Step 7: Update CI/CD

**GitHub Actions**:
```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: |
    pip install nanuk-mcp  # Was: snowcli-tools
```

## Breaking Changes

### Package Name
- PyPI: `snowcli-tools` → `nanuk-mcp`
- Import: `snowcli_tools` → `nanuk_mcp`

### Command Names
- MCP: `snowcli-mcp` → `nanuk-mcp`
- CLI: `snowflake-cli` → `nanuk` (legacy)

### GitHub Repository
- URL: `github.com/user/snowcli-tools` → `github.com/user/nanuk-mcp`
- (GitHub redirect works automatically)

## What Stays the Same?

✅ **API Compatibility**
- All classes, functions, and methods have the same signatures
- Configuration format unchanged
- MCP protocol support unchanged

✅ **Functionality**
- All features work identically
- Performance unchanged
- Database compatibility unchanged

✅ **Documentation**
- Updated but content similar
- Same concepts and workflows

## Backward Compatibility

For the next **6 months** (until April 2026):

1. **Tombstone Package**: `snowcli-tools` will remain on PyPI as a redirect to `nanuk-mcp`
2. **Deprecation Warnings**: Using old package name will show migration reminder
3. **Auto-Import**: Old imports may work but will warn you to migrate

**After April 2026**:
- `snowcli-tools` package will be removed from PyPI
- Only `nanuk-mcp` will be available

## Automated Migration Script

We provide a script to automate most of the migration:

```bash
# Download migration script
curl -O https://raw.githubusercontent.com/user/nanuk-mcp/main/scripts/migrate_from_snowcli_tools.py

# Run in your project directory
python migrate_from_snowcli_tools.py .

# Review changes
git diff

# Test your project
pytest tests/
```

## Troubleshooting

### Issue: "No module named 'snowcli_tools'"

**Solution**: You forgot to update imports. Run find/replace (see Step 3).

### Issue: "Command 'snowcli-mcp' not found"

**Solution**: Use new command name `nanuk-mcp`.

### Issue: Tests failing after migration

**Solution**:
1. Check all imports updated
2. Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
3. Reinstall: `pip uninstall -y snowcli-tools nanuk-mcp && pip install nanuk-mcp`

### Issue: MCP server won't start

**Solution**: Update MCP configuration with new command name (see Step 5).

## Need Help?

- 🐛 **Bug or migration issue?** [Open an issue](https://github.com/user/nanuk-mcp/issues)
- 💬 **Questions?** [Discussions](https://github.com/user/nanuk-mcp/discussions)
- 📧 **Email:** support@example.com

## Feedback

We'd love to hear about your migration experience!

- ⭐ [Star the repo](https://github.com/user/nanuk-mcp) if you like the new name
- 💬 [Share feedback](https://github.com/user/nanuk-mcp/discussions)

Thank you for being part of the Nanuk community! 🐻‍❄️
```

---

#### 4. Social Media Announcements

**Twitter/X**:
```
🚨 Exciting News!

snowcli-tools is now nanuk-mcp! 🐻‍❄️

Why Nanuk?
✨ MCP-first architecture
🎯 Unique branding
❄️ Connects to Snowflake theme

Migration is easy:
pip uninstall snowcli-tools
pip install nanuk-mcp

Full guide: [link]

#Snowflake #MCP #DataEngineering
```

**LinkedIn**:
```
📢 Announcing: snowcli-tools → nanuk-mcp Rebrand

After careful consideration, we're rebranding our Snowflake MCP server to better reflect its purpose and direction.

🐻‍❄️ Why "Nanuk"?
• Nanuk (polar bear in Inuit) connects to Snowflake's arctic theme
• Emphasizes MCP-first architecture
• Creates unique, memorable brand identity

🔄 Smooth Migration
We've made the transition as smooth as possible with:
• Tombstone package for backward compatibility
• Comprehensive migration guide
• Automated migration scripts
• 6-month transition period

🚀 What's Next?
This rebrand aligns with our vision to be the premier Snowflake MCP provider in the AI-first data ecosystem.

Learn more: [link]

#DataEngineering #Snowflake #AI #MCP
```

---

#### 5. Email to Existing Users

**Subject**: Important: snowcli-tools → nanuk-mcp Rebrand

```
Hello snowcli-tools community,

We're excited to announce that snowcli-tools has been rebranded to nanuk-mcp!

WHY THE CHANGE?

After receiving feedback and analyzing our project's direction, we realized:
• "snowcli-tools" implied CLI focus (we're MCP-first now)
• We needed a unique, memorable name
• "Nanuk" (polar bear) connects perfectly to Snowflake's theme

WHAT YOU NEED TO DO

1. Update your installation:
   pip uninstall snowcli-tools && pip install nanuk-mcp

2. Update your imports:
   from snowcli_tools → from nanuk_mcp

3. Update commands:
   snowcli-mcp → nanuk-mcp

DETAILED MIGRATION GUIDE

We've prepared a comprehensive guide to help you:
[link to migration guide]

BACKWARD COMPATIBILITY

Don't worry! We've got you covered:
• Tombstone package maintains compatibility for 6 months
• All functionality remains the same
• Only names change, not behavior

TIMELINE

• Now: Both packages available
• April 2026: Old package removed

QUESTIONS?

• Issues: https://github.com/user/nanuk-mcp/issues
• Discussions: https://github.com/user/nanuk-mcp/discussions
• Email: support@example.com

Thank you for your continued support! We're excited about this new chapter for Nanuk MCP.

Best regards,
The Nanuk MCP Team 🐻‍❄️

P.S. Don't forget to star our repo under its new name!
```

---

## Rollout Timeline

### Week 1: Internal Preparation

**Days 1-2** (Mon-Tue):
- [ ] Create feature branch `rebrand-nanuk-mcp`
- [ ] Rename package directory
- [ ] Update pyproject.toml
- [ ] Update all imports in code
- [ ] Run tests locally

**Days 3-4** (Wed-Thu):
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Update GitHub Actions
- [ ] Test build process

**Day 5** (Fri):
- [ ] Final testing
- [ ] Create PR for review
- [ ] Internal team review

---

### Week 2: Soft Launch

**Monday**:
- [ ] Merge rebrand PR to main
- [ ] Rename GitHub repository
- [ ] Update local clones
- [ ] Verify GitHub redirect works

**Tuesday**:
- [ ] Build package: `uv build`
- [ ] Test package locally
- [ ] Create PyPI account (if needed)
- [ ] Publish to Test PyPI first

**Wednesday**:
- [ ] Publish to PyPI: `nanuk-mcp`
- [ ] Verify installation: `pip install nanuk-mcp`
- [ ] Test MCP server works
- [ ] Test imports work

**Thursday**:
- [ ] Create tombstone package
- [ ] Publish tombstone to PyPI
- [ ] Test tombstone redirects correctly
- [ ] Verify deprecation warning shows

**Friday**:
- [ ] Tag release: `v2.0.0`
- [ ] Create GitHub release with notes
- [ ] Update badges in README
- [ ] Monitor for issues

---

### Week 3: Public Announcement

**Monday**:
- [ ] Publish blog post (if you have blog)
- [ ] Post on Twitter/X
- [ ] Post on LinkedIn
- [ ] Post in relevant communities

**Tuesday**:
- [ ] Send email to users (if you have list)
- [ ] Update documentation sites
- [ ] Update any external references

**Wednesday-Friday**:
- [ ] Monitor GitHub issues
- [ ] Respond to questions
- [ ] Help users migrate
- [ ] Fix any bugs found

---

### Months 1-6: Transition Period

**Monthly**:
- [ ] Monitor tombstone package usage
- [ ] Track migration metrics
- [ ] Update docs based on feedback
- [ ] Support users with migration issues

**Milestones**:
- Month 1: 25% of users migrated
- Month 2: 50% of users migrated
- Month 3: 75% of users migrated
- Month 6: 90%+ of users migrated

---

### Month 6: Tombstone Removal (April 2026)

**Week 1**:
- [ ] Announce tombstone removal date
- [ ] Final migration push
- [ ] Offer migration support

**Week 2**:
- [ ] Remove tombstone package from PyPI
- [ ] Archive snowcli-tools-tombstone repo
- [ ] Update all communications

**Week 3**:
- [ ] Monitor for stragglers
- [ ] Help remaining users migrate
- [ ] Document lessons learned

**Week 4**:
- [ ] Retrospective meeting
- [ ] Update documentation
- [ ] Celebrate completion! 🎉

---

## Risk Mitigation

### Risk 1: Breaking Existing Installations

**Likelihood**: High
**Impact**: High

**Mitigation**:
- Tombstone package provides 6-month compatibility
- Clear deprecation warnings
- Comprehensive migration guide
- Automated migration scripts

**Contingency**:
If users experience major issues:
1. Extend tombstone period
2. Provide one-on-one migration support
3. Create video tutorials

---

### Risk 2: SEO/Discoverability Loss

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- GitHub redirect preserves incoming links
- Update all external references
- Maintain old name in keywords
- Cross-link from old docs

**Contingency**:
- Keep old name in PyPI package description
- Add "formerly snowcli-tools" everywhere
- SEO optimization for new name

---

### Risk 3: User Confusion

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Clear communication at every touchpoint
- Prominent migration guide
- Deprecation warnings in old package
- FAQ section

**Contingency**:
- Create video walkthrough
- Host Q&A session
- Offer migration office hours

---

### Risk 4: Lost Downloads/Stars

**Likelihood**: Medium
**Impact**: Low

**Mitigation**:
- GitHub repo redirect preserves stars
- PyPI redirects preserve download counts
- Announce to recapture attention

**Contingency**:
- Consider this a fresh start
- Focus on quality over numbers
- Rebuild community engagement

---

### Risk 5: Technical Issues After Rebrand

**Likelihood**: Low
**Impact**: High

**Mitigation**:
- Comprehensive testing before release
- Staged rollout (Test PyPI first)
- Keep old branch as backup
- Rollback plan prepared

**Contingency Plan**:
```bash
# If major issues found after release:

# 1. Immediately publish hotfix
uv build
uv publish

# 2. If unfixable, rollback
git revert <commit>
# Re-publish as 2.0.1

# 3. Communicate issue transparently
# Post issue on GitHub
# Email users
# Provide workaround
```

---

## Appendix

### A. Automated Migration Script

**File**: `scripts/migrate_from_snowcli_tools.py`

```python
#!/usr/bin/env python3
"""
Automated migration script: snowcli-tools → nanuk-mcp

Usage:
    python migrate_from_snowcli_tools.py /path/to/your/project
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in directory."""
    root = Path(root_dir)
    return list(root.rglob("*.py"))

def migrate_imports(file_path: Path) -> Tuple[int, List[str]]:
    """
    Migrate imports in a single file.
    Returns (num_changes, changed_lines)
    """
    content = file_path.read_text()
    original_content = content
    changes = []

    # Pattern 1: from snowcli_tools → from nanuk_mcp
    pattern1 = r'from snowcli_tools'
    replacement1 = 'from nanuk_mcp'
    content = re.sub(pattern1, replacement1, content)
    if pattern1 in original_content:
        changes.append(f"Updated: {pattern1} → {replacement1}")

    # Pattern 2: import snowcli_tools → import nanuk_mcp
    pattern2 = r'import snowcli_tools'
    replacement2 = 'import nanuk_mcp'
    content = re.sub(pattern2, replacement2, content)
    if pattern2 in original_content:
        changes.append(f"Updated: {pattern2} → {replacement2}")

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        return len(changes), changes

    return 0, []

def migrate_requirements(file_path: Path) -> bool:
    """Migrate requirements.txt or pyproject.toml."""
    content = file_path.read_text()
    original_content = content

    # Update package name
    content = re.sub(
        r'snowcli-tools([>=<~!]*[\d.]*)',
        r'nanuk-mcp\1',
        content
    )

    if content != original_content:
        file_path.write_text(content)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_from_snowcli_tools.py /path/to/project")
        sys.exit(1)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"Error: {project_dir} is not a directory")
        sys.exit(1)

    print(f"🔄 Migrating project: {project_dir}")
    print(f"   snowcli-tools → nanuk-mcp\n")

    # Migrate Python files
    python_files = find_python_files(project_dir)
    total_changes = 0
    files_changed = 0

    print(f"📝 Scanning {len(python_files)} Python files...")
    for py_file in python_files:
        num_changes, changes = migrate_imports(py_file)
        if num_changes > 0:
            files_changed += 1
            total_changes += num_changes
            print(f"\n✓ {py_file.relative_to(project_dir)}")
            for change in changes:
                print(f"  - {change}")

    # Migrate requirements files
    req_files = [
        Path(project_dir) / "requirements.txt",
        Path(project_dir) / "pyproject.toml",
    ]

    print("\n📦 Checking dependency files...")
    for req_file in req_files:
        if req_file.exists():
            if migrate_requirements(req_file):
                print(f"✓ Updated: {req_file.name}")
            else:
                print(f"  No changes needed: {req_file.name}")

    # Summary
    print("\n" + "="*60)
    print(f"✅ Migration complete!")
    print(f"   Files changed: {files_changed}")
    print(f"   Total changes: {total_changes}")
    print("="*60)

    if files_changed > 0:
        print("\n⚠️  Next steps:")
        print("1. Review changes: git diff")
        print("2. Update dependencies: pip install nanuk-mcp")
        print("3. Run tests: pytest tests/")
        print("4. Update CI/CD configs manually")
        print("5. Update MCP server configs manually")
    else:
        print("\n✓ No changes needed - you may already be using nanuk-mcp!")

if __name__ == "__main__":
    main()
```

---

### B. Validation Checklist

**Pre-Release Validation**:

```markdown
## Code
- [ ] Package directory renamed
- [ ] All imports updated
- [ ] All tests pass
- [ ] Build succeeds
- [ ] Local install works

## Documentation
- [ ] README.md updated
- [ ] All docs/*.md updated
- [ ] Migration guide created
- [ ] CHANGELOG.md updated
- [ ] No broken links

## Configuration
- [ ] pyproject.toml updated
- [ ] GitHub Actions updated
- [ ] Pre-commit hooks updated
- [ ] MCP config examples updated

## Distribution
- [ ] Package builds
- [ ] Published to Test PyPI
- [ ] Installed from Test PyPI works
- [ ] Published to PyPI
- [ ] Tombstone package created
- [ ] Tombstone published

## Infrastructure
- [ ] GitHub repo renamed
- [ ] GitHub redirect works
- [ ] Badges updated
- [ ] CI/CD passes

## Communication
- [ ] Release notes drafted
- [ ] Migration guide complete
- [ ] Announcement posts ready
- [ ] Email template ready

## Post-Release
- [ ] Package installable
- [ ] MCP server starts
- [ ] All examples work
- [ ] No critical bugs
```

---

### C. FAQ

**Q: Why rename now?**
A: We're already deprecating CLI, so this is a good time to align the name with our MCP-first direction.

**Q: Will my code break?**
A: Not immediately. The tombstone package provides 6 months of compatibility.

**Q: How long does migration take?**
A: 15-30 minutes for most projects. Use our automated script.

**Q: Can I keep using snowcli-tools?**
A: Yes, for 6 months (until April 2026). After that, only nanuk-mcp will be available.

**Q: What if I find a bug after migrating?**
A: Open an issue on GitHub. We'll fix it quickly during the transition period.

**Q: Will the tombstone package get security updates?**
A: Yes, the tombstone redirects to nanuk-mcp, so you'll get all updates automatically.

**Q: What happens to old GitHub issues/PRs?**
A: They stay intact. GitHub automatically redirects the URLs.

**Q: What about stars on GitHub?**
A: Stars are preserved when renaming a repository.

---

### D. Success Metrics

**Track these metrics during transition**:

```markdown
## Week 1
- [ ] PyPI downloads (nanuk-mcp): [count]
- [ ] PyPI downloads (snowcli-tools): [count]
- [ ] Migration rate: [%]
- [ ] GitHub issues related to migration: [count]

## Month 1
- [ ] Migration rate: [%]
- [ ] User satisfaction (survey): [score]/10
- [ ] Support tickets: [count]
- [ ] Stars on new repo: [count]

## Month 3
- [ ] Migration rate: [%]
- [ ] Old package downloads: [count]
- [ ] New package downloads: [count]
- [ ] Community engagement: [metric]

## Month 6
- [ ] Migration rate: [%] (target: 90%+)
- [ ] Ready to remove tombstone: Yes/No
- [ ] Lessons learned: [documented]
```

---

**END OF REBRAND PLAN**

*Total estimated time: 9.5 hours*
*Transition period: 6 months*
*Risk level: Medium (mitigated with tombstone package)*
