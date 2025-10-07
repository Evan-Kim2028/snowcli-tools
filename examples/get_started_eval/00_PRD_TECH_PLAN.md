# PRD & Technical Plan: SnowCLI Tools v1.9.1 Documentation & Architecture Upgrade

**Document Version**: 1.0
**Date**: October 7, 2025
**Branch**: `v1.9.1-doc-upgrades`
**Status**: Draft for Review
**Owner**: Project Maintainer

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Assessment](#current-state-assessment)
3. [Problem Statement](#problem-statement)
4. [Goals & Success Metrics](#goals--success-metrics)
5. [Proposed Solution](#proposed-solution)
6. [Technical Implementation Plan](#technical-implementation-plan)
7. [Detailed Task Breakdown](#detailed-task-breakdown)
8. [Architecture Migration Plan](#architecture-migration-plan)
9. [Testing & Validation](#testing--validation)
10. [Risk Assessment](#risk-assessment)
11. [Resource Requirements](#resource-requirements)
12. [Timeline & Milestones](#timeline--milestones)
13. [Appendix](#appendix)

---

## Executive Summary

### Overview

SnowCLI Tools v1.9.0 is a powerful Snowflake data operations toolkit with both CLI and MCP interfaces. Recent evaluation revealed critical documentation gaps blocking new user adoption and identified architectural opportunities to reduce maintenance burden by 50%.

### Key Issues

- **Documentation Quality**: 6.5/10 - Version inconsistencies, broken links (53%), missing prerequisites
- **New User Success Rate**: <10% - Users blocked by wrong command syntax, incomplete auth steps
- **Architecture Inefficiency**: 85% code duplication between CLI and MCP interfaces
- **Version Chaos**: 5 different versions referenced across codebase

### Proposed Solution

**Two-Track Approach**:

1. **Track 1 (Week 1)**: Quick documentation fixes to unblock users (2.5 hours)
2. **Track 2 (6 months)**: Strategic pivot to MCP-only architecture

### Expected Outcomes

- User success rate: <10% → >90%
- Documentation quality: 6.5/10 → 8.5/10
- Time to first success: 2-4 hours → 30-45 minutes
- Maintenance burden: -50% (CLI deprecation)
- Version consistency: 5 versions → 1 version

---

## Current State Assessment

### Documentation Quality Scores

| Category | Current Score | Target Score | Gap |
|----------|--------------|--------------|-----|
| **Version Consistency** | 3/10 | 10/10 | -7 |
| **Getting Started** | 5/10 | 9/10 | -4 |
| **Authentication** | 4/10 | 9/10 | -5 |
| **MCP Documentation** | 8/10 | 9/10 | -1 |
| **CLI Documentation** | 4/10 | N/A (deprecate) | N/A |
| **Architecture Docs** | 9/10 | 9/10 | 0 |
| **Troubleshooting** | 9/10 | 9/10 | 0 |
| **Overall** | **6.5/10** | **8.5/10** | **-2** |

### User Experience Metrics

| Metric | Current | Target |
|--------|---------|--------|
| New user setup success rate | <10% | >90% |
| Time to first successful query | 2-4 hours | 30-45 min |
| Documentation link health | 47% working | 100% working |
| Version consistency checks | 0% pass | 100% pass |

### Architecture State

| Component | LOC | Test Coverage | Maintenance Burden | Recommendation |
|-----------|-----|---------------|-------------------|----------------|
| CLI | 774 | 113 LOC (3.6%) | Medium | **Deprecate** |
| MCP | 780 | High | Medium | **Enhance** |
| Service Layer | 2,000+ | High | Low | **Keep** |
| Code Duplication | 85% | N/A | High | **Eliminate** |

### Technical Debt Identified

1. **Critical Issues** (P0):
   - Wrong command syntax in all docs (`-p` doesn't exist)
   - 5 different version numbers referenced
   - Missing prerequisites (Snowflake CLI installation)
   - Incomplete authentication setup (no key generation steps)

2. **High Priority** (P1):
   - 53% broken documentation links
   - MCP dependency confusion (duplicates)
   - Wrong project names in examples
   - No expected output examples

3. **Medium Priority** (P2):
   - CLI documentation outdated
   - Missing configuration documentation
   - Installation instructions ambiguous
   - No video tutorials

---

## Problem Statement

### Primary Problems

**Problem 1: New Users Cannot Get Started**

Current state:
- User follows README → getting-started.md
- Hits immediate blocker: wrong command syntax
- No prerequisites listed (Snowflake CLI)
- Authentication steps incomplete (missing key generation)
- Cannot verify setup worked (no expected output)

**Result**: <10% success rate, users abandon project

**Problem 2: Version Confusion**

5 different versions found:
- `pyproject.toml`: 1.9.0 (source of truth)
- `README.md`: 1.7.0 and 1.5.0
- `cli.py`: 1.6.0
- `getting-started.md`: 1.5.0
- Branch mentions: v1.10.0

**Result**: Users don't know which version they have or what features are available

**Problem 3: Architecture Inefficiency**

Both CLI and MCP are thin wrappers around the same service layer:

```python
# CLI wrapper
def build_catalog(profile: str, database: str):
    service = CatalogService(get_connector(profile))
    return service.build_catalog(database)

# MCP wrapper (duplicate logic)
def build_catalog(profile: str, database: str):
    service = CatalogService(get_connector(profile))
    return service.build_catalog(database)
```

**Result**:
- 85% code duplication
- Two interfaces to maintain
- Two documentation sets
- Two testing strategies
- Confused users: "Which should I use?"

---

## Goals & Success Metrics

### Primary Goals

1. **Unblock New Users** (Week 1)
   - Fix all P0 documentation blockers
   - Enable 90%+ setup success rate
   - Reduce time to first success to <45 minutes

2. **Improve Documentation Quality** (Weeks 2-4)
   - Achieve 8.5/10 documentation quality score
   - Fix all broken links (100% link health)
   - Complete missing documentation

3. **Simplify Architecture** (Months 1-6)
   - Deprecate CLI interface
   - Pivot to MCP-only
   - Reduce maintenance burden by 50%

4. **Ensure Version Consistency** (Week 1)
   - Single source of truth: `pyproject.toml`
   - All docs reference correct version
   - Automated version consistency checks

### Success Metrics

#### Short-term (Week 1)

- [ ] All P0 fixes completed (2.5 hours)
- [ ] Version standardized to 1.9.0 everywhere
- [ ] New user can complete setup without errors
- [ ] Command syntax correct in all docs

#### Medium-term (Month 1)

- [ ] Documentation quality score: 8.5/10
- [ ] Link health: 100%
- [ ] New user success rate: >90%
- [ ] Time to first success: <45 minutes
- [ ] All missing docs created

#### Long-term (Month 6)

- [ ] CLI deprecated and removed
- [ ] MCP as sole interface
- [ ] Maintenance burden reduced 50%
- [ ] Migration guide published
- [ ] User satisfaction: >85%

---

## Proposed Solution

### Three-Phase Approach

#### Phase 1: Emergency Fixes (Week 1) - 2.5 hours

**Goal**: Unblock all new users immediately

**P0 Critical Fixes** (1 hour):
1. Fix command syntax errors - 15 min
2. Standardize version to 1.9.0 - 30 min
3. Add prerequisites section - 10 min
4. Complete auth setup steps - 5 min

**P1 High Priority** (1.5 hours):
5. Fix MCP dependency confusion - 30 min
6. Correct project name in examples - 20 min
7. Add expected output examples - 40 min

#### Phase 2: Documentation Overhaul (Weeks 2-4) - 20 hours

**Goal**: Achieve 8.5/10 documentation quality

**Week 2** (6 hours):
- Create missing core docs (configuration.md, api-reference.md)
- Fix all broken links
- Separate user vs developer installation

**Week 3** (6 hours):
- Complete authentication guide with screenshots
- Add success indicators throughout
- Create quick-win tutorial

**Week 4** (8 hours):
- Polish CLI documentation (deprecation notices)
- Complete tool documentation
- User testing and feedback incorporation

#### Phase 3: Architecture Migration (Months 1-6) - 40 hours

**Goal**: Deprecate CLI, establish MCP-only architecture

**Month 1-2** (15 hours):
- Add CLI deprecation warnings
- Ensure MCP feature parity
- Create migration guide
- Update all docs to recommend MCP

**Month 3-4** (15 hours):
- Move CLI to legacy package
- Mark as optional dependency
- Archive CLI docs
- Implement MCP enhancements

**Month 5-6** (10 hours):
- Remove CLI from default install
- Clean up CLI-specific tests
- Final migration validation
- Release v2.0.0 announcement

---

## Technical Implementation Plan

### Phase 1: Emergency Fixes (Week 1)

#### Task 1.1: Fix Command Syntax (15 minutes)

**Issue**: Docs show `-p` flag that doesn't exist

**Files to Update**:
```bash
# Files affected
/Users/evandekim/Documents/snowcli_tools/README.md
/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md
/Users/evandekim/Documents/snowcli_tools/docs/mcp/mcp_server_user_guide.md
```

**Implementation**:
```bash
# Step 1: Find all occurrences
cd /Users/evandekim/Documents/snowcli_tools
grep -rn "\-p \|verify -p\|catalog -p\|lineage.*-p" docs/ README.md

# Step 2: Replace pattern
# Wrong: snowflake-cli verify -p my-profile
# Right: snowflake-cli --profile my-profile verify

# Step 3: Add global flag documentation
# Wrong: snowflake-cli catalog -d DB -p profile
# Right: snowflake-cli --profile profile catalog -d DB
```

**Acceptance Criteria**:
- [ ] No references to `-p` flag remain
- [ ] All command examples use `--profile` (global flag)
- [ ] Examples show 3 methods: global flag, env var, default

**Testing**:
```bash
# Verify no -p flags remain
grep -r " -p " docs/ README.md
# Should return no results
```

---

#### Task 1.2: Standardize Version Numbers (30 minutes)

**Issue**: 5 different versions across codebase

**Source of Truth**: `pyproject.toml` version = "1.9.0"

**Files to Update**:

1. **README.md**
   - Line 7: Change "v1.7.0" → "v1.9.0"
   - Line 209: Change "Version 1.5.0" → "Version 1.9.0"

2. **docs/getting-started.md**
   - Line 250: Change "Version 1.5.0" → "Version 1.9.0"

3. **src/snowcli_tools/cli.py**
   - Line 58: Change `version="1.6.0"` → `version="1.9.0"`

4. **docs/ai-agent-integration.md**
   - Change "v1.7.0" → "v1.9.0"

**Implementation**:
```bash
# Find all version references
grep -rn "1\.[5-7]\.0" docs/ README.md src/

# Replace with 1.9.0
find docs/ README.md -type f -name "*.md" -exec sed -i '' 's/1\.[567]\.0/1.9.0/g' {} +

# Update cli.py manually (code file)
# Line 58: @click.version_option(version="1.9.0")
```

**Automated Check** (add to CI):
```python
# scripts/check_version_consistency.py
import toml
import re
from pathlib import Path

def check_version_consistency():
    # Read canonical version
    with open('pyproject.toml') as f:
        canonical = toml.load(f)['project']['version']

    # Check all markdown files
    issues = []
    for md_file in Path('docs').rglob('*.md'):
        content = md_file.read_text()
        versions = re.findall(r'\d+\.\d+\.\d+', content)
        for v in versions:
            if v != canonical:
                issues.append(f"{md_file}:{v}")

    if issues:
        raise ValueError(f"Version inconsistencies: {issues}")

    print(f"✓ All versions consistent: {canonical}")

if __name__ == "__main__":
    check_version_consistency()
```

**Acceptance Criteria**:
- [ ] pyproject.toml version = "1.9.0"
- [ ] All docs reference only 1.9.0
- [ ] CLI --version returns 1.9.0
- [ ] No other version numbers found
- [ ] CI check added for future consistency

---

#### Task 1.3: Add Prerequisites Section (10 minutes)

**Issue**: Snowflake CLI dependency never mentioned

**File to Update**: `docs/getting-started.md`

**Add Section** (insert at line 15):
```markdown
## Prerequisites

Before installing SnowCLI Tools, ensure you have:

### Required

1. **Python 3.8+**
   ```bash
   python --version
   # Should show Python 3.8 or higher
   ```

2. **Snowflake CLI** (Required dependency)
   ```bash
   # Install via pip
   pip install snowflake-cli-labs

   # Or via uv
   uv pip install snowflake-cli-labs

   # Verify installation
   snowflake-cli --version
   ```

3. **Snowflake Account**
   - Active Snowflake account with credentials
   - Database access permissions
   - Warehouse access (for query execution)

### Optional

4. **UV Package Manager** (Recommended)
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

5. **Claude Code or MCP-compatible AI Assistant** (for MCP usage)
   - Claude Code CLI
   - Or any MCP-compatible client

### Verification

Run this to verify prerequisites:
```bash
python --version      # Python 3.8+
snowflake-cli --version  # Snowflake CLI installed
uv --version         # UV installed (optional)
```
```

**Acceptance Criteria**:
- [ ] Prerequisites section added before installation
- [ ] Snowflake CLI installation documented
- [ ] Python version requirement stated
- [ ] Verification commands provided
- [ ] Optional vs required clearly marked

---

#### Task 1.4: Complete Authentication Setup (5 minutes)

**Issue**: Key generation and upload steps missing

**File to Update**: `docs/getting-started.md`

**Add to Authentication Section** (after line 45):
```markdown
### Step-by-Step Authentication Setup

#### 1. Generate RSA Key Pair

```bash
# Create .snowflake directory
mkdir -p ~/.snowflake

# Generate private key (unencrypted for simplicity)
openssl genrsa -out ~/.snowflake/snowflake_rsa_key.pem 2048

# Generate public key
openssl rsa -in ~/.snowflake/snowflake_rsa_key.pem \
    -pubout -out ~/.snowflake/snowflake_rsa_key.pub

# Set proper permissions (important!)
chmod 400 ~/.snowflake/snowflake_rsa_key.pem
chmod 400 ~/.snowflake/snowflake_rsa_key.pub
```

#### 2. Upload Public Key to Snowflake

```sql
-- Copy your public key (remove header/footer)
-- From: ~/.snowflake/snowflake_rsa_key.pub
-- Remove "-----BEGIN PUBLIC KEY-----" and "-----END PUBLIC KEY-----"
-- Remove all newlines to create single-line string

-- In Snowflake, run:
ALTER USER <your_username> SET RSA_PUBLIC_KEY='<your_public_key_string>';

-- Verify it was set
DESC USER <your_username>;
-- Look for RSA_PUBLIC_KEY_FP (fingerprint)
```

**Helper Script**:
```bash
# scripts/format_public_key.sh
#!/bin/bash
# Formats public key for Snowflake

cat ~/.snowflake/snowflake_rsa_key.pub | \
    grep -v "BEGIN PUBLIC KEY" | \
    grep -v "END PUBLIC KEY" | \
    tr -d '\n'

echo ""
echo "Copy the above string and run in Snowflake:"
echo "ALTER USER <username> SET RSA_PUBLIC_KEY='<paste here>';"
```

#### 3. Create Configuration File

```bash
# Create config at ~/.snowflake/config.toml
cat > ~/.snowflake/config.toml << 'EOF'
[connections.my-profile]
account = "your-account"
user = "your-username"
authenticator = "SNOWFLAKE_JWT"
private_key_path = "~/.snowflake/snowflake_rsa_key.pem"

# Optional: Set defaults
[default]
connection = "my-profile"
EOF
```

#### 4. Verify Authentication

```bash
# Test connection
uv run snowflake-cli --profile my-profile verify

# Expected output:
# ✓ Verified Snow CLI and profile 'my-profile'.
# ✓ Connection successful
# ✓ Profile: my-profile
# ✓ Account: your-account
# ✓ User: your-username
```

**Troubleshooting**:
- If "JWT token invalid": Check public key uploaded correctly
- If "Account not found": Verify account name format (should be `org-account`)
- If "Permission denied": Check file permissions (`chmod 400`)
```

**Acceptance Criteria**:
- [ ] Key generation commands provided
- [ ] Public key upload to Snowflake documented
- [ ] Config file creation explained
- [ ] Verification step with expected output
- [ ] Troubleshooting tips included

---

#### Task 1.5: Fix MCP Dependency Confusion (30 minutes)

**Issue**: anthropic-mcp-server appears in both dependencies and optional-dependencies

**File to Update**: `pyproject.toml`

**Current State** (lines 25-45):
```toml
dependencies = [
    "anthropic-mcp-server>=0.1.0",  # Listed here
    "snowflake-connector-python>=3.0.0",
    # ... other deps
]

[project.optional-dependencies]
mcp = [
    "anthropic-mcp-server>=0.1.0",  # DUPLICATE!
    # ... other mcp deps
]
```

**Corrected Structure**:
```toml
# Core dependencies (required for CLI and basic usage)
dependencies = [
    "snowflake-connector-python>=3.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0",
]

# MCP-specific dependencies (optional)
[project.optional-dependencies]
mcp = [
    "anthropic-mcp-server>=0.1.0",
    "mcp>=0.1.0",
    "httpx>=0.25.0",
    "asyncio>=3.4.3",
]

# Development dependencies
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

# All optional dependencies
all = [
    "snowcli-tools[mcp]",
    "snowcli-tools[dev]",
]
```

**Update Installation Docs**:

In `README.md` and `getting-started.md`:
```markdown
## Installation

### For MCP Usage (Recommended)
```bash
# Install with MCP support
uv pip install "snowcli-tools[mcp]"

# Or from source
git clone <repo-url>
cd snowcli-tools
uv pip install -e ".[mcp]"
```

### For CLI Only (Deprecated - see migration guide)
```bash
# Minimal install
uv pip install snowcli-tools
```

### For Development
```bash
# All dependencies
uv pip install -e ".[all]"
```
```

**Acceptance Criteria**:
- [ ] No duplicate dependencies
- [ ] Clear separation: core vs MCP vs dev
- [ ] Installation instructions updated
- [ ] uv.lock regenerated
- [ ] Tests pass with new dependency structure

---

#### Task 1.6: Correct Project Names in Examples (20 minutes)

**Issue**: Examples show wrong project name "snowflake_connector_py" instead of "snowcli-tools"

**Files to Update**:
- `docs/mcp/mcp_server_user_guide.md`
- `README.md`
- `docs/ai-agent-integration.md`

**Find/Replace**:
```bash
# Find all wrong project names
grep -rn "snowflake_connector_py\|snowflake-connector-py" docs/ README.md

# Replace with correct name
find docs/ README.md -type f -exec sed -i '' \
    's/snowflake_connector_py/snowcli-tools/g' {} +
find docs/ README.md -type f -exec sed -i '' \
    's/snowflake-connector-py/snowcli-tools/g' {} +
```

**Update MCP Config Examples**:

In `docs/mcp/mcp_server_user_guide.md`:
```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/you/snowcli-tools",
        "run",
        "snowcli-mcp"
      ]
    }
  }
}
```

**Acceptance Criteria**:
- [ ] All references use "snowcli-tools"
- [ ] Config examples use correct project name
- [ ] File paths in examples are realistic
- [ ] No references to old names remain

---

#### Task 1.7: Add Expected Output Examples (40 minutes)

**Issue**: Users can't verify if commands succeeded - no "expected output" shown

**Files to Update**:
- `docs/getting-started.md`
- `docs/api/*.md` (all tool docs)
- `README.md`

**Pattern to Add** (after every command):
```markdown
### Example: Verify Connection

```bash
uv run snowflake-cli --profile my-profile verify
```

**Expected Output:**
```
✓ Verified Snow CLI and profile 'my-profile'.

Connection Details:
  Profile: my-profile
  Account: myorg-myaccount
  User: myuser
  Database: (not set - will prompt if needed)
  Schema: (not set - will prompt if needed)
  Warehouse: (not set - will prompt if needed)

Status: ✓ Connected successfully
```

**What This Means:**
- ✓ Your Snowflake credentials are valid
- ✓ The profile is configured correctly
- ✓ You can now run queries and commands

**If You See Errors:**
- "JWT token invalid" → Check public key upload (see Authentication section)
- "Account not found" → Verify account name format: `<org>-<account>`
- "User not found" → Check username spelling
```

**Apply to All Major Commands**:

1. **Catalog Build**:
```bash
uv run snowflake-cli --profile my-profile catalog -d MY_DATABASE
```
**Expected**: Progress bar, summary stats, file location

2. **Query Execution**:
```bash
uv run snowflake-cli --profile my-profile query "SELECT CURRENT_USER()"
```
**Expected**: Query results in table format

3. **MCP Server Start**:
```bash
uv run snowcli-mcp
```
**Expected**: Server listening message, no errors

**Locations to Add** (20 examples total):
- Getting started guide: 8 examples
- API reference docs: 10 examples (each tool)
- Troubleshooting: 2 examples

**Acceptance Criteria**:
- [ ] Every command example has expected output
- [ ] Output shows success indicators (✓, checkmarks)
- [ ] Errors are explained ("If you see...")
- [ ] Next steps provided after success

---

### Phase 1 Summary Checklist

**Week 1 Emergency Fixes** - Total: 2.5 hours

- [ ] Task 1.1: Fix command syntax (15 min)
- [ ] Task 1.2: Standardize versions (30 min)
- [ ] Task 1.3: Add prerequisites (10 min)
- [ ] Task 1.4: Complete auth setup (5 min)
- [ ] Task 1.5: Fix dependency confusion (30 min)
- [ ] Task 1.6: Correct project names (20 min)
- [ ] Task 1.7: Add expected outputs (40 min)

**Validation**:
- [ ] New user can complete setup without errors
- [ ] All commands use correct syntax
- [ ] Version consistent everywhere
- [ ] No broken links in updated docs
- [ ] Tests pass

**Success Metrics After Phase 1**:
- User success rate: <10% → 60%+
- Time to first success: 2-4hrs → 1hr
- Documentation quality: 6.5/10 → 7.5/10

---

## Phase 2: Documentation Overhaul (Weeks 2-4)

### Week 2: Foundation (6 hours)

#### Task 2.1: Create Missing Core Documentation (3 hours)

**Missing Files** (referenced but don't exist):
1. `docs/configuration.md` (referenced 4+ times)
2. `docs/api-reference.md`
3. `docs/mcp-integration.md`
4. `CONTRIBUTING.md`

**Implementation**:

**1. docs/configuration.md** (90 minutes)
```markdown
# Configuration Guide

## Overview
Configure SnowCLI Tools using profiles, environment variables, or direct parameters.

## Configuration Methods
1. Profile files (~/.snowflake/config.toml)
2. Environment variables
3. Command-line arguments

## Profile Configuration
### Location
- Default: `~/.snowflake/config.toml`
- Custom: Set `SNOWFLAKE_CONFIG_PATH`

### Format
[Show TOML structure with all options]

## Environment Variables
[List all SNOWFLAKE_* env vars]

## Precedence
[Explain order: CLI args > env vars > profile > defaults]

## Examples
[Common configurations]

## Troubleshooting
[Common config issues]
```

**2. docs/api-reference.md** (60 minutes)
```markdown
# API Reference

## MCP Tools

### Query Tools
- execute_query
- preview_table
- profile_table

### Catalog Tools
- build_catalog
- get_catalog_summary

### Lineage Tools
- query_lineage
- build_dependency_graph

[Link to detailed docs for each]

## CLI Commands (Deprecated)
[Link to legacy docs]

## Python API
[For programmatic usage]
```

**3. docs/mcp-integration.md** (45 minutes)
```markdown
# MCP Integration Guide

## What is MCP?
[Brief explanation]

## Integrating with AI Assistants

### Claude Code
[Setup instructions]

### Other MCP Clients
[Generic setup]

## Available Tools
[List with descriptions]

## Configuration
[MCP server config]

## Examples
[Real-world use cases]
```

**4. CONTRIBUTING.md** (15 minutes)
```markdown
# Contributing Guide

## Getting Started
[Fork, clone, install]

## Development Setup
[uv, dependencies, pre-commit]

## Making Changes
[Branching, commits, testing]

## Pull Requests
[PR process, review]

## Documentation
[Doc standards]

## Testing
[How to run tests]
```

**Acceptance Criteria**:
- [ ] All 4 files created with complete content
- [ ] All broken links now resolve
- [ ] Content follows style guide
- [ ] Examples are tested and work
- [ ] Cross-references added to other docs

---

#### Task 2.2: Fix All Broken Links (2 hours)

**Current State**: 53% broken links (16 of 30 links)

**Broken Links Found**:
```
docs/getting-started.md:
  - [configuration guide](configuration.md) → CREATE FILE
  - [API reference](api-reference.md) → CREATE FILE
  - [troubleshooting](../troubleshooting.md) → ALREADY EXISTS, FIX PATH

README.md:
  - [Getting Started](docs/getting-started.md) → ✓ EXISTS
  - [Configuration](docs/configuration.md) → CREATE FILE
  - [MCP Integration](docs/mcp-integration.md) → CREATE FILE

docs/api/execute_query.md:
  - [configuration guide](../configuration.md) → CREATE FILE
  - [authentication](../authentication.md) → CREATE FILE

[... 10 more broken links]
```

**Implementation**:
```bash
# Step 1: Audit all links
cd /Users/evandekim/Documents/snowcli_tools
find docs/ README.md -name "*.md" -exec \
    grep -H "\[.*\]([^http].*)" {} \; > link_audit.txt

# Step 2: Check each link
python scripts/check_links.py

# Step 3: Fix broken links
# - Create missing files (Task 2.1)
# - Fix incorrect paths
# - Update to correct filenames
# - Remove dead links
```

**Link Validation Script**:
```python
# scripts/check_links.py
import re
from pathlib import Path

def check_links():
    broken = []
    for md_file in Path('docs').rglob('*.md'):
        content = md_file.read_text()
        links = re.findall(r'\[([^\]]+)\]\(([^http][^\)]+)\)', content)

        for title, link in links:
            target = (md_file.parent / link).resolve()
            if not target.exists():
                broken.append(f"{md_file}:{link}")

    if broken:
        print("Broken links found:")
        for link in broken:
            print(f"  ❌ {link}")
        return False
    else:
        print("✓ All links valid")
        return True
```

**Acceptance Criteria**:
- [ ] Link health: 100% (all links resolve)
- [ ] Automated link checker added to CI
- [ ] No dead links remain
- [ ] All paths use correct relative format

---

#### Task 2.3: Separate User vs Developer Installation (1 hour)

**Issue**: README conflates user and developer installation

**Files to Update**:
- `README.md`
- `docs/getting-started.md`

**New Structure**:

**README.md** (User Focus):
```markdown
## Installation

### For End Users (MCP Usage)

**Recommended: Install with MCP support**
```bash
# Option 1: From PyPI (when published)
pip install "snowcli-tools[mcp]"

# Option 2: From source
git clone https://github.com/yourusername/snowcli-tools.git
cd snowcli-tools
uv pip install ".[mcp]"
```

### Quick Start
[5-minute tutorial to first query]

### For Developers
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.
```

**docs/getting-started.md** (Detailed User Guide):
```markdown
## Installation Options

### Option 1: Install from PyPI (Recommended)
For most users, install the published package:

```bash
pip install "snowcli-tools[mcp]"
```

**When to use**: Production use, stable releases

### Option 2: Install from Source
For latest features or custom modifications:

```bash
git clone https://github.com/yourusername/snowcli-tools.git
cd snowcli-tools
uv pip install ".[mcp]"
```

**When to use**: Testing new features, contributing

### Option 3: Development Install
For active development (see CONTRIBUTING.md):

```bash
git clone https://github.com/yourusername/snowcli-tools.git
cd snowcli-tools
uv pip install -e ".[all]"
pre-commit install
```

**When to use**: Contributing code, debugging
```

**Acceptance Criteria**:
- [ ] Clear separation: user vs developer
- [ ] "Quick start" is truly quick (<5 min)
- [ ] Each option explains "when to use"
- [ ] Development details moved to CONTRIBUTING.md
- [ ] README is more scannable

---

### Week 3: Enhanced Getting Started (6 hours)

#### Task 2.4: Complete Authentication Guide with Screenshots (3 hours)

Expand authentication documentation with visual aids.

**File**: `docs/authentication-guide.md` (new file)

**Sections**:
1. Overview (why key-pair auth)
2. Prerequisites
3. Step-by-step with screenshots
4. Configuration file setup
5. Verification
6. Troubleshooting (common errors)
7. Security best practices

**Acceptance Criteria**:
- [ ] Screenshots for Snowflake UI steps
- [ ] Copy-paste commands tested
- [ ] Every step has verification
- [ ] Security warnings included
- [ ] Linked from getting-started.md

---

#### Task 2.5: Add Success Indicators Throughout (2 hours)

Add verification steps after every major action.

**Pattern**:
```markdown
### Step X: [Action]

[Command to run]

**How to Verify Success:**
✓ You should see: [expected output]
✓ File created at: [location]
✓ Next step: [what to do next]

❌ If you see errors: [link to troubleshooting]
```

**Apply to**:
- Installation (5 checkpoints)
- Authentication (4 checkpoints)
- First query (3 checkpoints)
- MCP setup (6 checkpoints)

**Acceptance Criteria**:
- [ ] Every major step has success indicator
- [ ] Clear "what's next" after each step
- [ ] Error handling linked to troubleshooting
- [ ] User never uncertain if they succeeded

---

#### Task 2.6: Create Quick-Win Tutorial (1 hour)

**File**: `docs/5-minute-quickstart.md` (new)

**Goal**: User gets value in 5 minutes

**Tutorial Flow**:
1. Prerequisites check (30 sec)
2. Install (1 min)
3. Configure profile (1 min)
4. Run first query (30 sec)
5. See results (30 sec)
6. What's next? (1.5 min)

**Acceptance Criteria**:
- [ ] Takes <5 minutes for real user
- [ ] Uses existing Snowflake account
- [ ] Immediate gratification (query works)
- [ ] Links to deeper docs
- [ ] Featured prominently in README

---

### Week 4: Polish & Finalize (8 hours)

#### Task 2.7: CLI Documentation with Deprecation Notices (3 hours)

Update CLI docs to indicate deprecation path.

**Files**:
- `docs/cli-reference.md`
- All CLI command docs

**Add Banner**:
```markdown
> ⚠️ **CLI Deprecation Notice**
> The CLI interface is deprecated and will be removed in v2.0.0 (Q2 2026).
> Please migrate to the MCP interface. See [Migration Guide](migration-guide.md).
```

**Acceptance Criteria**:
- [ ] Every CLI doc has deprecation notice
- [ ] Migration guide created
- [ ] MCP equivalent shown for each CLI command
- [ ] Timeline clear (v2.0.0 removal)

---

#### Task 2.8: Complete Tool Documentation (3 hours)

Ensure every MCP tool has complete docs.

**Tools to Document** (10 tools):
1. execute_query
2. preview_table
3. profile_table
4. build_catalog
5. get_catalog_summary
6. query_lineage
7. build_dependency_graph
8. test_connection
9. health_check
10. show (SQL)

**Template per Tool**:
```markdown
# Tool: [name]

## Purpose
[What it does]

## Parameters
[Table with param, type, required, description]

## Returns
[What it returns]

## Examples
[3+ examples with expected output]

## Common Use Cases
[When to use this tool]

## Troubleshooting
[Common errors]

## Related Tools
[Links to related tools]
```

**Acceptance Criteria**:
- [ ] All 10 tools documented
- [ ] Consistent format across all docs
- [ ] Examples tested and work
- [ ] Cross-references between tools

---

#### Task 2.9: User Testing & Feedback (2 hours)

Recruit 3 users to test new documentation.

**Test Protocol**:
1. Recruit fresh users (no prior knowledge)
2. Give them only documentation (no help)
3. Ask them to:
   - Install snowcli-tools
   - Authenticate to Snowflake
   - Run their first query via MCP
   - Use 3 different tools

**Observe**:
- Where do they get stuck?
- What do they skip?
- What errors occur?
- Time to success?

**Acceptance Criteria**:
- [ ] 3 users tested
- [ ] Feedback incorporated
- [ ] Success rate measured
- [ ] Issues documented and fixed

---

### Phase 2 Summary Checklist

**Weeks 2-4: Documentation Overhaul** - Total: 20 hours

**Week 2 (6 hours)**:
- [ ] Task 2.1: Create missing docs (3 hrs)
- [ ] Task 2.2: Fix broken links (2 hrs)
- [ ] Task 2.3: Separate user/dev install (1 hr)

**Week 3 (6 hours)**:
- [ ] Task 2.4: Auth guide with screenshots (3 hrs)
- [ ] Task 2.5: Success indicators (2 hrs)
- [ ] Task 2.6: Quick-win tutorial (1 hr)

**Week 4 (8 hours)**:
- [ ] Task 2.7: CLI deprecation notices (3 hrs)
- [ ] Task 2.8: Complete tool docs (3 hrs)
- [ ] Task 2.9: User testing (2 hrs)

**Success Metrics After Phase 2**:
- Documentation quality: 7.5/10 → 8.5/10
- Link health: 100%
- New user success rate: 60% → 90%
- Time to first success: 1hr → 30-45min

---

## Phase 3: Architecture Migration (Months 1-6)

### Overview

**Goal**: Deprecate CLI interface, establish MCP-only architecture

**Strategy**: Gradual deprecation over 6 months
- Months 1-2: Preparation & warnings
- Months 3-4: Transition & migration
- Months 5-6: Removal & cleanup

**Impact**:
- Reduces codebase by ~774 LOC (CLI)
- Eliminates 85% code duplication
- Reduces maintenance burden by 50%
- Simplifies user experience (one interface)

---

### Months 1-2: Preparation (15 hours)

#### Task 3.1: Add CLI Deprecation Warnings (3 hours)

**Implementation**:

**1. Add warnings to CLI code**:
```python
# src/snowcli_tools/cli.py

import warnings

DEPRECATION_MESSAGE = """
╔══════════════════════════════════════════════════════════╗
║             CLI DEPRECATION WARNING                       ║
╠══════════════════════════════════════════════════════════╣
║ The CLI interface is deprecated and will be removed in   ║
║ version 2.0.0 (estimated Q2 2026).                       ║
║                                                           ║
║ Please migrate to the MCP interface for continued        ║
║ support and new features.                                ║
║                                                           ║
║ Migration guide:                                         ║
║ https://docs.snowcli-tools.com/migration-guide          ║
╚══════════════════════════════════════════════════════════╝
"""

@app.callback()
def main():
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
    print(DEPRECATION_MESSAGE)
```

**2. Update pyproject.toml**:
```toml
[project.entry-points.console_scripts]
snowflake-cli = "snowcli_tools.cli:main"  # Mark as deprecated

[project.entry-points."console_scripts.deprecated"]
snowflake-cli = "snowcli_tools.cli:main"
```

**3. Add deprecation to docs**:
- Banner on all CLI docs
- Redirects to MCP docs
- Migration timeline

**Acceptance Criteria**:
- [ ] Warning shown on every CLI invocation
- [ ] Warning is visible but not annoying
- [ ] Link to migration guide works
- [ ] Docs clearly state deprecation

---

#### Task 3.2: Ensure MCP Feature Parity (5 hours)

**Goal**: Verify MCP can do everything CLI can

**Audit Matrix**:

| Feature | CLI | MCP | Status | Action |
|---------|-----|-----|--------|--------|
| Execute query | ✓ | ✓ | ✓ Complete | None |
| Build catalog | ✓ | ✓ | ✓ Complete | None |
| Query lineage | ✓ | ✓ | ✓ Complete | None |
| Preview table | ✓ | ✓ | ✓ Complete | None |
| Profile table | ✓ | ✓ | ✓ Complete | None |
| Verify connection | ✓ | ✓ | ✓ Complete | None |
| Health check | ✓ | ✓ | ✓ Complete | None |
| Dependency graph | ✓ | ✓ | ✓ Complete | None |
| Profile selection | ✓ | ✓ | ✓ Complete | None |
| Error handling | ✓ | ✓ | ✓ Complete | None |

**Implementation**:
```bash
# Test script to verify parity
# scripts/test_cli_mcp_parity.sh

#!/bin/bash
set -e

echo "Testing CLI vs MCP feature parity..."

# Test 1: Execute query
CLI_RESULT=$(snowflake-cli query "SELECT 1" 2>&1)
MCP_RESULT=$(test-mcp-tool execute_query "SELECT 1" 2>&1)
# Compare results

# Test 2: Build catalog
# ... etc for all features

echo "✓ Feature parity verified"
```

**Acceptance Criteria**:
- [ ] All CLI features available in MCP
- [ ] MCP feature matrix documented
- [ ] Automated parity tests added
- [ ] No functional gaps

---

#### Task 3.3: Create Migration Guide (4 hours)

**File**: `docs/migration-guide.md` (new)

**Sections**:

1. **Why Migrate?**
   - MCP benefits
   - CLI deprecation timeline
   - What's improved

2. **Migration Checklist**
   ```markdown
   - [ ] Review current CLI usage
   - [ ] Install MCP dependencies
   - [ ] Configure MCP server
   - [ ] Test MCP tools
   - [ ] Update scripts/automation
   - [ ] Remove CLI from workflow
   ```

3. **Command Mapping**

   | CLI Command | MCP Equivalent |
   |-------------|----------------|
   | `snowflake-cli verify` | `execute_query` tool in MCP |
   | `snowflake-cli catalog -d DB` | `build_catalog` tool |
   | `snowflake-cli lineage TABLE` | `query_lineage` tool |

4. **Migration Examples**

   **Before (CLI)**:
   ```bash
   snowflake-cli --profile prod query "SELECT * FROM users LIMIT 10"
   ```

   **After (MCP)**:
   ```json
   {
     "tool": "execute_query",
     "arguments": {
       "statement": "SELECT * FROM users LIMIT 10",
       "role": "prod"
     }
   }
   ```

5. **Automation Migration**
   - Scripts using CLI
   - CI/CD pipeline updates
   - Scheduled jobs

6. **Troubleshooting**
   - Common migration issues
   - Getting help

**Acceptance Criteria**:
- [ ] Complete command mapping table
- [ ] Real-world migration examples
- [ ] Automation migration guidance
- [ ] FAQ section

---

#### Task 3.4: Update All Docs to Recommend MCP (3 hours)

**Files to Update**:
- README.md
- docs/getting-started.md
- All API docs

**Changes**:

**1. README.md**:
```markdown
## Quick Start

### Recommended: MCP Interface
[MCP setup instructions - prominent]

### Legacy: CLI Interface (Deprecated)
[CLI instructions - smaller, with deprecation notice]
```

**2. Getting Started**:
- Lead with MCP setup
- CLI section at end with deprecation
- All examples use MCP by default

**3. API Docs**:
- Primary examples: MCP
- CLI examples: removed or marked deprecated

**Acceptance Criteria**:
- [ ] MCP is primary path in all docs
- [ ] CLI clearly marked as legacy
- [ ] New users naturally choose MCP
- [ ] No confusion about which to use

---

### Months 3-4: Transition (15 hours)

#### Task 3.5: Move CLI to Legacy Package (6 hours)

**Goal**: Separate CLI into optional legacy package

**New Structure**:
```
src/snowcli_tools/
├── core/              # Core services (keep)
│   ├── catalog.py
│   ├── lineage.py
│   └── query.py
├── mcp/               # MCP interface (primary)
│   ├── server.py
│   └── tools/
├── legacy/            # CLI interface (deprecated)
│   ├── cli.py         # Moved from root
│   └── commands/
└── __init__.py
```

**pyproject.toml Changes**:
```toml
[project.optional-dependencies]
legacy-cli = [
    "typer>=0.9.0",
    "click>=8.0.0",
]

[project.entry-points."console_scripts.deprecated"]
snowflake-cli = "snowcli_tools.legacy.cli:main"
```

**Migration Steps**:
1. Create `src/snowcli_tools/legacy/` directory
2. Move CLI code: `mv cli.py legacy/cli.py`
3. Update imports in CLI code
4. Update tests to import from legacy
5. Verify all tests pass

**Acceptance Criteria**:
- [ ] CLI in separate package
- [ ] Optional install: `pip install snowcli-tools[legacy-cli]`
- [ ] All tests pass
- [ ] No breaking changes for CLI users (yet)

---

#### Task 3.6: Mark CLI as Optional Dependency (2 hours)

**pyproject.toml**:
```toml
# Default install: MCP only
dependencies = [
    "snowflake-connector-python>=3.0.0",
    "anthropic-mcp-server>=0.1.0",
    "mcp>=0.1.0",
    # No CLI dependencies here
]

# CLI only if explicitly requested
[project.optional-dependencies]
legacy-cli = [
    "typer>=0.9.0",
    "click>=8.0.0",
    "rich>=13.0.0",
]
```

**Installation Updates**:
```bash
# Default: MCP only
pip install snowcli-tools

# With legacy CLI
pip install "snowcli-tools[legacy-cli]"
```

**Acceptance Criteria**:
- [ ] Default install is MCP-only
- [ ] CLI available via optional dependency
- [ ] Package size reduced for default install
- [ ] Docs updated with new install instructions

---

#### Task 3.7: Archive CLI Documentation (2 hours)

**Create**: `docs/legacy/` directory

**Move**:
- `docs/cli-reference.md` → `docs/legacy/cli-reference.md`
- All CLI-specific docs → `docs/legacy/`

**Add**: `docs/legacy/README.md`
```markdown
# Legacy CLI Documentation (Deprecated)

> ⚠️ **This documentation is for the deprecated CLI interface.**
>
> The CLI will be removed in v2.0.0 (Q2 2026).
>
> **Please migrate to MCP**: [Migration Guide](../migration-guide.md)

## Why is CLI Deprecated?

[Explanation]

## CLI Documentation

[Links to archived docs]

## Migration Path

[Quick guide to MCP]
```

**Update Navigation**:
- Main docs sidebar: Remove CLI links
- Add single "Legacy Docs" link at bottom

**Acceptance Criteria**:
- [ ] CLI docs in separate legacy/ folder
- [ ] Clear deprecation warnings on all pages
- [ ] Not prominent in main navigation
- [ ] Migration guide linked from every page

---

#### Task 3.8: Implement MCP Enhancements (5 hours)

**Goal**: Make MCP interface better than CLI ever was

**Enhancements**:

1. **Better Error Messages** (2 hours)
   ```python
   # Before
   raise ValueError("Query failed")

   # After
   raise QueryError(
       message="Query failed",
       query=sql,
       error_code="SYNTAX_ERROR",
       suggestion="Check SQL syntax near line 5",
       docs_link="https://docs.snowcli-tools.com/troubleshooting#syntax"
   )
   ```

2. **Async Tool Support** (2 hours)
   - Long-running queries don't block
   - Progress updates during execution
   - Cancellation support

3. **Enhanced Tool Metadata** (1 hour)
   - Better descriptions
   - Example inputs/outputs
   - Related tools suggestions

**Acceptance Criteria**:
- [ ] MCP error messages better than CLI
- [ ] Async tools working
- [ ] Tool metadata enhanced
- [ ] User feedback positive

---

### Months 5-6: Removal & Cleanup (10 hours)

#### Task 3.9: Remove CLI from Default Installation (2 hours)

**Version**: v2.0.0-alpha

**Changes**:
```toml
# pyproject.toml
version = "2.0.0a1"  # Alpha release

# Remove CLI entry point from default
[project.entry-points.console_scripts]
# snowflake-cli = removed

# CLI only in legacy
[project.optional-dependencies.legacy-cli]
# ... CLI deps
```

**Communication**:
- Release notes explaining change
- Blog post about v2.0 direction
- Deprecation notice in v1.x releases (already done)

**Acceptance Criteria**:
- [ ] CLI not installed by default in v2.0.0-alpha
- [ ] Legacy package still available
- [ ] Migration guide prominent
- [ ] Support for v1.x users

---

#### Task 3.10: Clean Up CLI-Specific Tests (3 hours)

**Goal**: Remove or move CLI tests

**Current State**:
- 113 LOC of CLI-specific tests (3.6% of total)
- Located in `tests/test_cli.py` and `tests/commands/`

**Actions**:
1. Move CLI tests to `tests/legacy/`
2. Mark as legacy tests
3. Only run if legacy-cli installed
4. Remove from default test suite

**Test Configuration**:
```python
# pytest.ini
[tool.pytest.ini_options]
markers = [
    "legacy: Legacy CLI tests (skipped by default)",
]

# Skip legacy tests by default
addopts = "-m 'not legacy'"
```

**Acceptance Criteria**:
- [ ] CLI tests separated
- [ ] Default test suite doesn't include CLI
- [ ] CI only runs CLI tests if legacy-cli installed
- [ ] Test coverage maintained for MCP

---

#### Task 3.11: Final Migration Validation (3 hours)

**Goal**: Verify all users can migrate successfully

**Test Plan**:

1. **Automated Tests**:
   ```bash
   # Test migration script
   scripts/test_migration.sh

   # Tests:
   - CLI commands still work in v1.x
   - MCP equivalents work in v2.0
   - Migration guide accurate
   - No broken links
   ```

2. **User Testing**:
   - Recruit 5 users currently using CLI
   - Ask them to migrate following guide
   - Observe issues
   - Measure success rate

3. **Validation Criteria**:
   - [ ] 100% of CLI features available in MCP
   - [ ] Migration guide tested by real users
   - [ ] 90%+ of test users successfully migrate
   - [ ] All CLI deprecation warnings working

**Acceptance Criteria**:
- [ ] Migration tested end-to-end
- [ ] No unexpected blockers found
- [ ] Success rate >90%
- [ ] Documentation accurate

---

#### Task 3.12: Release v2.0.0 (2 hours)

**Goal**: Official release removing CLI

**Release Checklist**:
- [ ] Version bumped to 2.0.0
- [ ] CHANGELOG.md updated with breaking changes
- [ ] Migration guide finalized
- [ ] Release notes drafted
- [ ] Blog post published
- [ ] Social media announcement
- [ ] Support channel prepared for questions

**Breaking Changes**:
```markdown
# v2.0.0 Breaking Changes

## CLI Removed from Default Installation

The CLI interface has been removed from the default installation.

**Migration Required**: Follow the [Migration Guide](migration-guide.md)

**If you still need CLI**:
```bash
pip install "snowcli-tools[legacy-cli]==1.9.x"
```

**Legacy CLI Support**:
- Security fixes only
- No new features
- Removed in v3.0.0 (Q4 2026)

## MCP is Now Primary Interface

All new features will be MCP-only.
```

**Acceptance Criteria**:
- [ ] v2.0.0 released to PyPI
- [ ] Release notes comprehensive
- [ ] Migration guide prominent
- [ ] Support team briefed
- [ ] Metrics tracking migration adoption

---

### Phase 3 Summary Checklist

**Months 1-6: Architecture Migration** - Total: 40 hours

**Months 1-2: Preparation (15 hours)**:
- [ ] Task 3.1: CLI deprecation warnings (3 hrs)
- [ ] Task 3.2: MCP feature parity (5 hrs)
- [ ] Task 3.3: Migration guide (4 hrs)
- [ ] Task 3.4: Update docs for MCP (3 hrs)

**Months 3-4: Transition (15 hours)**:
- [ ] Task 3.5: Move CLI to legacy (6 hrs)
- [ ] Task 3.6: CLI as optional dep (2 hrs)
- [ ] Task 3.7: Archive CLI docs (2 hrs)
- [ ] Task 3.8: MCP enhancements (5 hrs)

**Months 5-6: Removal (10 hours)**:
- [ ] Task 3.9: Remove CLI from default (2 hrs)
- [ ] Task 3.10: Clean up CLI tests (3 hrs)
- [ ] Task 3.11: Migration validation (3 hrs)
- [ ] Task 3.12: Release v2.0.0 (2 hrs)

**Success Metrics After Phase 3**:
- Maintenance burden: -50%
- Code duplication: 85% → 0%
- User interface clarity: 100% (single path)
- Migration success rate: >90%

---

## Testing & Validation

### New User Testing Protocol

**Objective**: Validate documentation improvements

**Test Scenarios**:

#### Scenario 1: Fresh Install
**Profile**: User with no prior knowledge
**Goal**: Install and run first query in <45 minutes

**Steps**:
1. Find project (Google search or GitHub)
2. Read README
3. Follow installation instructions
4. Configure authentication
5. Run first query via MCP
6. Verify success

**Success Criteria**:
- [ ] Completes in <45 minutes
- [ ] No external help needed
- [ ] No errors encountered
- [ ] Understands what they did

---

#### Scenario 2: CLI to MCP Migration
**Profile**: Existing CLI user
**Goal**: Migrate to MCP in <2 hours

**Steps**:
1. Find migration guide
2. Understand why migrating
3. Install MCP dependencies
4. Configure MCP server
5. Test MCP equivalent of their CLI usage
6. Remove CLI from workflow

**Success Criteria**:
- [ ] Completes in <2 hours
- [ ] Migration guide is clear
- [ ] All CLI features available in MCP
- [ ] No data loss or disruption

---

#### Scenario 3: Advanced Usage
**Profile**: Power user
**Goal**: Use advanced features (lineage, catalog)

**Steps**:
1. Build catalog for large database
2. Query lineage for complex table
3. Profile table for optimization
4. Use multiple tools together
5. Troubleshoot an error

**Success Criteria**:
- [ ] Advanced docs are clear
- [ ] Tool interactions documented
- [ ] Error messages helpful
- [ ] Performance acceptable

---

### Automated Validation

**CI/CD Checks**:

```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation

on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check version consistency
        run: python scripts/check_version_consistency.py

      - name: Validate links
        run: python scripts/check_links.py

      - name: Test getting started
        run: |
          # Simulate new user following docs
          bash scripts/test_getting_started.sh

      - name: Check command syntax
        run: |
          # Verify no -p flags remain
          ! grep -r " -p " docs/ README.md
```

**Validation Scripts**:

1. **Version Consistency**:
   ```python
   # scripts/check_version_consistency.py
   # Ensures all docs reference same version
   ```

2. **Link Health**:
   ```python
   # scripts/check_links.py
   # Checks all internal links resolve
   ```

3. **Command Syntax**:
   ```bash
   # scripts/check_command_syntax.sh
   # Verifies commands use correct flags
   ```

---

### Documentation Quality Metrics

**Track Over Time**:

| Metric | Baseline | Week 1 | Week 4 | Month 6 |
|--------|----------|--------|--------|---------|
| **Version consistency** | 3/10 | 10/10 | 10/10 | 10/10 |
| **Link health** | 47% | 100% | 100% | 100% |
| **New user success** | <10% | 60% | 90% | 95% |
| **Time to first success** | 2-4 hrs | 1 hr | 45 min | 30 min |
| **Documentation quality** | 6.5/10 | 7.5/10 | 8.5/10 | 9/10 |

**Measurement Methods**:
- User testing sessions (N=5 per milestone)
- Analytics on doc pages (time on page, bounce rate)
- Support ticket volume (should decrease)
- GitHub issues tagged "documentation"

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Breaking changes in v2.0** | High | High | Clear migration guide, legacy support |
| **MCP missing CLI features** | Low | High | Feature parity audit, comprehensive testing |
| **Documentation still unclear** | Medium | Medium | User testing at each phase, iterate |
| **Users resist migration** | Medium | Low | Gradual deprecation, show benefits clearly |

---

### User Impact Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Existing CLI scripts break** | High | Legacy package available, migration guide |
| **Confusion about which to use** | Medium | Clear deprecation notices, prominent MCP docs |
| **Can't complete setup** | High | Phase 1 fixes (P0 blockers), success indicators |
| **Loss of features in MCP** | Critical | Feature parity audit, testing |

---

### Timeline Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Phase 1 delayed** | Low | High | Small scope (2.5 hrs), prioritize |
| **User testing takes longer** | Medium | Low | Schedule early, have backup testers |
| **v2.0 release delayed** | Medium | Low | Gradual migration allows flexibility |
| **Resource constraints** | Medium | Medium | Prioritize P0/P1, defer P2/P3 if needed |

---

## Resource Requirements

### Time Estimates by Phase

| Phase | Duration | Hours | Resources Needed |
|-------|----------|-------|------------------|
| **Phase 1: Emergency Fixes** | Week 1 | 2.5 | Doc writer |
| **Phase 2: Doc Overhaul** | Weeks 2-4 | 20 | Doc writer, designer (screenshots) |
| **Phase 3: Architecture** | Months 1-6 | 40 | Developer, architect |
| **Total** | 6 months | 62.5 | Distributed over time |

---

### Role Assignments

**Documentation Writer** (22.5 hours):
- Phase 1: All tasks (2.5 hrs)
- Phase 2: All tasks (20 hrs)

**Software Developer** (30 hours):
- Phase 3: Code migration (20 hrs)
- Phase 3: Testing (10 hrs)

**Architect** (10 hours):
- Phase 3: Architecture decisions
- Phase 3: Code reviews

**Designer** (optional, 5 hours):
- Phase 2: Screenshots for auth guide
- Phase 2: Diagrams for architecture docs

**User Testers** (voluntary):
- Phase 2: Week 4 testing
- Phase 3: Migration testing

---

### Budget (if outsourcing)

| Resource | Rate | Hours | Cost |
|----------|------|-------|------|
| Doc writer | $75/hr | 22.5 | $1,687.50 |
| Developer | $100/hr | 30 | $3,000.00 |
| Architect | $150/hr | 10 | $1,500.00 |
| Designer | $80/hr | 5 | $400.00 |
| **Total** | | **67.5** | **$6,587.50** |

*Note: These are estimates. Actual costs may vary.*

---

## Timeline & Milestones

### Gantt Chart Overview

```
Month:     Oct    Nov    Dec    Jan    Feb    Mar    Apr    May    Jun
           |------|------|------|------|------|------|------|------|
Phase 1:   ██
Phase 2:   ████████████
Phase 3:                 ████████████████████████████████████████████
           │      │      │      │      │      │      │      │      │
           W1     W2-4   M1-2                 M3-4              M5-6
```

---

### Detailed Timeline

#### Week 1 (October 7-13, 2025)
**Phase 1: Emergency Fixes**

- **Day 1 (Mon)**: Tasks 1.1-1.2 (command syntax, version)
- **Day 2 (Tue)**: Tasks 1.3-1.4 (prerequisites, auth)
- **Day 3 (Wed)**: Tasks 1.5-1.6 (dependencies, project names)
- **Day 4 (Thu)**: Task 1.7 (expected outputs)
- **Day 5 (Fri)**: Testing & validation

**Deliverable**: All P0 blockers fixed

---

#### Weeks 2-4 (October 14 - November 3, 2025)
**Phase 2: Documentation Overhaul**

**Week 2 (Oct 14-20)**:
- Mon-Tue: Task 2.1 (create missing docs)
- Wed-Thu: Task 2.2 (fix broken links)
- Fri: Task 2.3 (user/dev install separation)

**Week 3 (Oct 21-27)**:
- Mon-Tue: Task 2.4 (auth guide with screenshots)
- Wed-Thu: Task 2.5 (success indicators)
- Fri: Task 2.6 (quick-win tutorial)

**Week 4 (Oct 28 - Nov 3)**:
- Mon-Tue: Task 2.7 (CLI deprecation notices)
- Wed-Thu: Task 2.8 (complete tool docs)
- Fri: Task 2.9 (user testing)

**Deliverable**: Documentation quality 8.5/10

---

#### Months 1-2 (November-December 2025)
**Phase 3A: Preparation**

**November**:
- Week 1: Task 3.1 (deprecation warnings)
- Week 2-3: Task 3.2 (MCP feature parity)
- Week 4: Task 3.3 (migration guide)

**December**:
- Week 1: Task 3.4 (update docs for MCP)
- Week 2-4: Buffer, holiday break

**Deliverable**: CLI deprecated, migration path clear

---

#### Months 3-4 (January-February 2026)
**Phase 3B: Transition**

**January**:
- Week 1-2: Task 3.5 (move CLI to legacy)
- Week 3: Task 3.6 (CLI as optional dep)
- Week 4: Task 3.7 (archive CLI docs)

**February**:
- Week 1-3: Task 3.8 (MCP enhancements)
- Week 4: Testing & validation

**Deliverable**: CLI separated, MCP enhanced

---

#### Months 5-6 (March-April 2026)
**Phase 3C: Removal**

**March**:
- Week 1: Task 3.9 (remove CLI from default)
- Week 2: Task 3.10 (clean up CLI tests)
- Week 3-4: Task 3.11 (migration validation)

**April**:
- Week 1: Final testing
- Week 2: Task 3.12 (release v2.0.0)
- Week 3-4: Support, monitoring

**Deliverable**: v2.0.0 released, MCP-only

---

### Key Milestones

| Date | Milestone | Success Criteria |
|------|-----------|------------------|
| **Oct 13, 2025** | P0 Fixes Complete | User success rate >60% |
| **Nov 3, 2025** | Docs Overhaul Done | Documentation quality 8.5/10 |
| **Dec 20, 2025** | CLI Deprecated | Warnings visible, migration guide live |
| **Feb 28, 2026** | CLI Separated | CLI is optional, MCP primary |
| **Apr 15, 2026** | v2.0.0 Released | MCP-only, CLI removed |

---

### Review Points

**Weekly Reviews** (during active development):
- Progress against tasks
- Blockers identified
- Timeline adjustments

**Phase Reviews**:
- End of Phase 1: Go/no-go for Phase 2
- End of Phase 2: Go/no-go for Phase 3
- End of Phase 3: Retrospective

**Metrics Reviews** (monthly):
- Documentation quality score
- User success rate
- Support ticket volume
- Migration adoption rate

---

## Appendix

### A. Reference Documents

All evaluation documents located at:
`/Users/evandekim/Documents/snowcli_tools/examples/get_started_eval/`

1. **01_documentation_evaluation.md** - Comprehensive doc analysis
2. **02_executive_summary.md** - Quick overview
3. **03_architecture_analysis.md** - CLI vs MCP decision
4. **04_fix_checklist.md** - Task checklist
5. **05_file_by_file_issues.md** - Specific file issues
6. **06_README.md** - Evaluation guide
7. **07_new_user_walkthrough.md** - User simulation
8. **08_authentication_issues.md** - Auth problems
9. **09_mcp_setup_issues.md** - MCP config issues
10. **10_quick_fixes.md** - Priority fixes
11. **11_SIMULATION_SUMMARY.md** - Testing summary
12. **12_FINAL_RECOMMENDATIONS.md** - Recommendations

---

### B. Quick Reference Commands

**Version Standardization**:
```bash
# Find all version references
cd /Users/evandekim/Documents/snowcli_tools
grep -rn "1\.[5-7]\.0" docs/ README.md src/

# Replace with 1.9.0
find docs/ README.md -type f -name "*.md" -exec sed -i '' 's/1\.[567]\.0/1.9.0/g' {} +
```

**Command Syntax Fix**:
```bash
# Find wrong syntax
grep -rn "\-p \|verify -p\|catalog -p" docs/ README.md

# No automated replacement - manual fix needed
```

**Link Validation**:
```bash
# Check all links
python scripts/check_links.py

# Expected output: "✓ All links valid" or list of broken links
```

---

### C. File Locations

**Documentation**:
- README: `/Users/evandekim/Documents/snowcli_tools/README.md`
- Getting Started: `/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md`
- All docs: `/Users/evandekim/Documents/snowcli_tools/docs/`

**Code**:
- CLI: `/Users/evandekim/Documents/snowcli_tools/src/snowcli_tools/cli.py`
- MCP: `/Users/evandekim/Documents/snowcli_tools/src/snowcli_tools/mcp_server.py`
- Services: `/Users/evandekim/Documents/snowcli_tools/src/snowcli_tools/services/`

**Configuration**:
- pyproject.toml: `/Users/evandekim/Documents/snowcli_tools/pyproject.toml`
- MCP config: `/Users/evandekim/Documents/snowcli_tools/mcp_service_config.json`

**Tests**:
- All tests: `/Users/evandekim/Documents/snowcli_tools/tests/`
- CLI tests: `/Users/evandekim/Documents/snowcli_tools/tests/test_cli.py`

---

### D. Success Metrics Dashboard

**Track these metrics weekly**:

```markdown
## Week [X] Metrics

### Documentation Quality
- [ ] Version consistency: [score]/10
- [ ] Link health: [%] working
- [ ] Getting started clarity: [score]/10
- [ ] Overall quality: [score]/10

### User Success
- [ ] New user success rate: [%]
- [ ] Time to first success: [minutes]
- [ ] Setup completion rate: [%]

### Migration (Phase 3 only)
- [ ] CLI users migrated: [%]
- [ ] MCP adoption rate: [%]
- [ ] Support tickets (migration): [count]

### Code Health
- [ ] Code duplication: [%]
- [ ] Test coverage: [%]
- [ ] LOC (CLI): [count]
```

---

### E. Communication Templates

**Email: Phase 1 Complete**
```
Subject: SnowCLI Tools Documentation Fixes Complete

Team,

We've completed Phase 1 (Emergency Fixes) of the documentation upgrade:

✓ Fixed command syntax errors
✓ Standardized version to 1.9.0
✓ Added prerequisites section
✓ Completed authentication guide
✓ Fixed dependency confusion

Impact:
- User success rate improved from <10% to 60%+
- Time to first success reduced to ~1 hour
- All P0 blockers resolved

Next: Phase 2 (Documentation Overhaul) starts [date]

[Link to full report]
```

**Announcement: CLI Deprecation**
```
Subject: Important: CLI Interface Deprecation

SnowCLI Tools Community,

We're announcing the deprecation of the CLI interface in favor of the MCP interface.

Timeline:
- Today: Deprecation warnings added
- Q1 2026: CLI moved to legacy package
- Q2 2026: v2.0.0 released (CLI removed from default)

Why?
- Reduces maintenance burden by 50%
- MCP is the future of AI tool integration
- Simplifies user experience

Migration:
[Link to migration guide]

Questions?
[Support channels]
```

---

### F. Glossary

**CLI**: Command-Line Interface - the terminal-based interface (being deprecated)

**MCP**: Model Context Protocol - the AI assistant integration interface (primary)

**P0/P1/P2**: Priority levels (P0 = critical blocker, P1 = high priority, P2 = nice to have)

**Service Layer**: Core business logic shared by both CLI and MCP

**Feature Parity**: Ensuring MCP can do everything CLI can do

**Link Health**: Percentage of documentation links that resolve correctly

**User Success Rate**: Percentage of new users who complete setup without errors

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Oct 7, 2025 | Initial PRD created | Documentation Team |

---

## Approval

**Prepared by**: Documentation Engineer Agent
**Reviewed by**: [Pending]
**Approved by**: [Pending]

**Sign-off Date**: [Pending]

---

**END OF DOCUMENT**

*Total Pages: ~50 pages*
*Total Tasks: 28 tasks across 3 phases*
*Total Estimated Time: 62.5 hours over 6 months*
*Expected ROI: 50% reduction in maintenance burden, 90%+ user success rate*
