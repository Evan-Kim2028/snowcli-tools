# Product Requirements Document: MCP-First Architecture Migration

**Version:** 1.0.0
**Date:** 2025-10-07
**Status:** Draft
**Owner:** Evan Kim

---

## Executive Summary

### Vision

Transform nanuk-mcp from a dual CLI+MCP interface into an **MCP-first platform** with a thin CLI wrapper, reducing maintenance overhead by 40-60% while improving the developer experience for AI-assisted workflows.

### Strategic Context

nanuk-mcp currently maintains two parallel interfaces:
1. **CLI interface** (`nanuk` command) - ~137 LOC in cli.py + ~1,769 LOC in commands/
2. **MCP interface** (`mcp_server.py`) - ~779 LOC with FastMCP integration

**Market Reality:**
- MCP adoption is growing rapidly (Claude Code, VS Code, Cursor, Windsurf)
- CLI adoption is minimal (primarily used for `mcp` subcommand)
- Documentation overhead: 32 docs with extensive CLI references (1,306 occurrences of "CLI")
- Maintenance burden: Dual API surface area with feature parity requirements

**Strategic Decision:** Deprecate standalone CLI in favor of MCP-first architecture with optional thin CLI wrapper using `mcp run`.

### Goals

**Primary Objectives:**
1. **Reduce Complexity:** Eliminate 40-60% of CLI-specific code and documentation
2. **Improve Maintainability:** Single source of truth for all functionality (MCP tools)
3. **Preserve Functionality:** Retain CLI-like usage through thin wrapper for existing users
4. **Enhance DX:** Better AI assistant integration with consolidated MCP interface

**Success Criteria:**
- LOC reduction: 500-1,000 lines removed
- Documentation reduction: 15-20 doc files consolidated
- Test coverage maintained: >90% for MCP tools
- Zero feature loss: All existing capabilities preserved via MCP
- Migration timeline: 2-3 release cycles (v1.10.0 → v1.11.0 → v1.12.0)

---

## Problem Statement

### Current Architecture Challenges

#### 1. **Dual Interface Maintenance Burden**

**Code Duplication:**
```
CLI Path:           cli.py → commands/*.py → service_layer/*.py → Snowflake
MCP Path:           mcp_server.py → service_layer/*.py → Snowflake
Commonality:        Both paths duplicate validation, error handling, configuration
```

**Maintenance Issues:**
- Feature additions require updates in 2+ places
- Bug fixes need parallel implementations
- Configuration changes impact multiple entry points
- Documentation must cover both interfaces

**Evidence:**
- `cli.py`: 137 LOC (basic wiring)
- `commands/`: ~1,769 LOC total (CLI command implementations)
- `mcp_server.py`: 779 LOC (MCP tool implementations)
- Service layer shared but entry points divergent

#### 2. **Documentation Overhead**

**Current State:**
- 32 total documentation files
- 1,306 CLI references across 46 files
- Separate guides for CLI and MCP usage
- Dual setup instructions create confusion

**Pain Points:**
- Users unclear which interface to use
- Setup guides reference both `nanuk` and MCP
- Troubleshooting duplicated across interfaces
- Onboarding friction from dual pathways

#### 3. **Low CLI Adoption**

**Usage Patterns:**
```bash
# Primary usage pattern (95%+ of users):
SNOWFLAKE_PROFILE=prod nanuk mcp  # Just starting MCP server

# Rare direct CLI usage (5%):
nanuk --profile prod catalog      # Direct CLI invocation
```

**Reality Check:**
- MCP is the expected usage pattern
- CLI is primarily used to launch MCP server
- Direct CLI commands rarely used in production
- AI assistants are primary interface

#### 4. **Feature Parity Challenges**

**Current Requirements:**
- New features must work in both CLI and MCP
- Error handling duplicated across interfaces
- Timeout/configuration logic maintained separately
- Testing covers both paths

**Impact:**
- Slower feature development
- Increased risk of interface divergence
- Higher testing burden
- Complex release coordination

### Root Cause Analysis

The dual interface architecture was a **transitional decision** during v1.4-v1.6 when MCP was experimental. Today:

1. **MCP is production-ready** (v1.0.0+, widely adopted)
2. **FastMCP is stable** (v2.8.1+, mature ecosystem)
3. **AI assistants are mainstream** (Claude Code, VS Code, Cursor standard tooling)
4. **CLI usage declining** (MCP wrapper is primary interface)

**Conclusion:** The dual interface served its purpose but is now technical debt.

---

## Proposed Solution: MCP-First Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐           ┌──────────────────┐        │
│  │   AI Assistants  │           │  CLI Wrapper     │        │
│  │  (Primary Path)  │           │  (Optional)      │        │
│  │                  │           │                  │        │
│  │ • Claude Code    │           │  mcp run         │        │
│  │ • VS Code        │           │  nanuk   │        │
│  │ • Cursor         │           │  (thin wrapper)  │        │
│  │ • Windsurf       │           │                  │        │
│  └────────┬─────────┘           └────────┬─────────┘        │
│           │                              │                  │
│           └──────────────┬───────────────┘                  │
│                          │                                  │
├──────────────────────────┼──────────────────────────────────┤
│                          ▼                                  │
│              ┌─────────────────────────┐                    │
│              │   MCP Server (FastMCP)  │                    │
│              │   Single Source of      │                    │
│              │   Truth for Features    │                    │
│              └───────────┬─────────────┘                    │
│                          │                                  │
├──────────────────────────┼──────────────────────────────────┤
│                          ▼                                  │
│              ┌─────────────────────────┐                    │
│              │   Service Layer         │                    │
│              │   (Unchanged)           │                    │
│              │                         │                    │
│              │ • CatalogService        │                    │
│              │ • LineageService        │                    │
│              │ • DependencyService     │                    │
│              │ • QueryService          │                    │
│              └───────────┬─────────────┘                    │
│                          │                                  │
├──────────────────────────┼──────────────────────────────────┤
│                          ▼                                  │
│              ┌─────────────────────────┐                    │
│              │   Snowflake Platform    │                    │
│              │   (via snowflake-labs-  │                    │
│              │    mcp integration)     │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. **MCP as Primary Interface**

**Decision:** All functionality exposed exclusively through MCP tools.

**Rationale:**
- MCP is stable, standardized protocol (JSON-RPC 2.0)
- Native support in major AI assistants
- Better error handling (exception-based)
- Cleaner abstraction layer
- Future-proof for AI-first workflows

**Implementation:**
- `mcp_server.py` becomes the canonical interface
- All features implemented as MCP tools
- Service layer remains unchanged
- No CLI-specific code paths

#### 2. **Hybrid CLI Approach (Optional)**

**Decision:** Provide thin CLI wrapper using `mcp run` for backward compatibility.

**Three Options:**

##### Option A: Pure MCP (Recommended)
```bash
# Only MCP interface
SNOWFLAKE_PROFILE=prod python -m nanuk_mcp.mcp_server

# Configure in Claude Code / VS Code
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "python",
      "args": ["-m", "nanuk_mcp.mcp_server"]
    }
  }
}
```

**Pros:** Simplest, lowest maintenance, clear direction
**Cons:** Breaking change for direct CLI users (minimal impact)

##### Option B: `mcp run` Wrapper (Recommended for Migration)
```bash
# Thin wrapper using mcp CLI
nanuk build-catalog --database MYDB

# Translates to:
mcp run nanuk-mcp build_catalog --database MYDB

# Where nanuk is just:
#!/usr/bin/env python
import sys
from subprocess import run
run(["mcp", "run", "nanuk-mcp"] + sys.argv[1:])
```

**Pros:** Backward compatible, minimal maintenance, uses standard tooling
**Cons:** Requires `mcp` CLI installed

##### Option C: Custom CLI Wrapper
```bash
# Custom argparse → MCP tool invocation
nanuk build-catalog --database MYDB

# Internally:
1. Parse CLI args
2. Convert to MCP tool call
3. Invoke MCP tool directly
4. Format output for terminal
```

**Pros:** Full control over UX
**Cons:** Highest maintenance burden, reinvents wheel

**Recommendation:** **Option B** (mcp run wrapper) for v1.10.0-v1.11.0 migration period, transition to **Option A** (pure MCP) in v1.12.0.

#### 3. **Documentation Strategy**

**Decision:** Consolidate to single MCP-first documentation set.

**Before (Current):**
```
docs/
├── getting-started.md          (CLI + MCP setup)
├── architecture.md             (CLI + MCP architecture)
├── configuration.md            (CLI + MCP config)
├── mcp/
│   ├── mcp_server_user_guide.md
│   ├── mcp_server_technical_guide.md
│   └── mcp_architecture.md
├── api/
│   ├── tools/                  (MCP tool docs)
│   └── README.md
└── [25+ other files]
```

**After (Proposed):**
```
docs/
├── README.md                   (Overview, quick start)
├── getting-started.md          (MCP-first setup)
├── architecture.md             (MCP architecture only)
├── configuration.md            (Profile + MCP config)
├── tools/                      (MCP tool reference)
│   ├── README.md
│   ├── build_catalog.md
│   ├── query_lineage.md
│   ├── execute_query.md
│   └── [8 other tools]
├── guides/
│   ├── catalog-workflow.md
│   ├── lineage-analysis.md
│   └── troubleshooting.md
└── migration/
    └── v1.9-to-v1.10.md        (CLI deprecation guide)
```

**Reduction:** 32 files → 18 files (-44%)

---

## Goals & Non-Goals

### Goals

#### Phase 1: Deprecation (v1.10.0)
- Mark CLI commands as deprecated with clear migration path
- Add deprecation warnings to all CLI commands
- Update documentation with migration timeline
- Provide `mcp run` wrapper examples
- Maintain 100% feature parity

#### Phase 2: Migration (v1.11.0)
- Implement thin CLI wrapper using `mcp run`
- Consolidate documentation to MCP-first approach
- Update all examples to use MCP interface
- Add migration guide with step-by-step instructions
- Support both interfaces during transition

#### Phase 3: Removal (v1.12.0)
- Remove CLI command implementations (~1,769 LOC)
- Remove CLI-specific tests
- Consolidate documentation (remove CLI references)
- Simplify configuration (MCP-only paths)
- Update package metadata and PyPI description

#### Long-term Goals
- 40-60% reduction in codebase size
- 50% reduction in documentation maintenance
- Faster feature development (single interface)
- Better AI assistant integration
- Clearer product positioning

### Non-Goals

#### What We're NOT Changing
- **Service Layer:** Catalog, Lineage, Dependency services remain unchanged
- **MCP Tools:** Existing MCP tool implementations stay as-is
- **Configuration:** Profile management and authentication unchanged
- **Features:** No functionality removed (all accessible via MCP)
- **Testing:** Test coverage maintained at current levels

#### What We're NOT Adding
- **New Features:** Migration is refactoring only
- **Breaking Changes:** Phased approach maintains compatibility
- **Alternative Protocols:** MCP is the standard, no GraphQL/REST/etc.
- **CLI Enhancements:** No new CLI-specific features during deprecation

#### Out of Scope
- Rewriting service layer (works fine)
- Changing authentication mechanisms
- Adding new MCP tools (separate roadmap)
- Performance optimization (separate effort)
- Multi-account management (future consideration)

---

## User Impact Analysis

### User Segments

#### 1. **AI Assistant Users (Primary - 95%)**

**Current Workflow:**
```bash
# Setup MCP in Claude Code
SNOWFLAKE_PROFILE=prod nanuk mcp

# Use via AI assistant
"Build a catalog for the ANALYTICS database"
"Show me lineage for CUSTOMER_ORDERS table"
```

**Impact:** **ZERO** - No changes to MCP interface

**Action Required:** None

#### 2. **Direct CLI Users (Secondary - 5%)**

**Current Workflow:**
```bash
nanuk --profile prod catalog --database ANALYTICS
nanuk --profile prod lineage CUSTOMER_ORDERS
```

**Impact:** **MODERATE** - Must migrate to MCP or use wrapper

**Migration Options:**

**Option 1: Switch to MCP (Recommended)**
```bash
# One-time setup
# Configure MCP server in .mcp.json or use mcp CLI

# Then use via AI assistant or mcp CLI
mcp run nanuk-mcp build_catalog --database ANALYTICS
```

**Option 2: Use CLI Wrapper (Temporary)**
```bash
# v1.10.0-v1.11.0: Wrapper available
nanuk build-catalog --database ANALYTICS
# Internally calls: mcp run nanuk-mcp build_catalog ...

# Deprecation warning shown
```

**Option 3: Direct Python Import**
```python
# For programmatic usage
from nanuk_mcp.service_layer import CatalogService
from nanuk_mcp.context import create_service_context

context = create_service_context()
catalog_service = CatalogService(context=context)
result = catalog_service.build_catalog(database="ANALYTICS")
```

#### 3. **CI/CD Pipeline Users**

**Current Workflow:**
```bash
# GitHub Actions / Jenkins
nanuk --profile ci catalog --database PROD
```

**Impact:** **LOW** - Wrapper maintains compatibility through v1.11.0

**Migration Path:**
```yaml
# v1.10.0-v1.11.0: Use wrapper (no changes needed)
- run: nanuk catalog --database PROD

# v1.12.0+: Migrate to MCP CLI or Python import
- run: mcp run nanuk-mcp build_catalog --database PROD

# Or: Direct Python execution
- run: python -c "from nanuk_mcp import ..."
```

#### 4. **Library/SDK Users**

**Current Workflow:**
```python
from nanuk_mcp.service_layer import CatalogService
# Direct service layer usage
```

**Impact:** **ZERO** - Service layer unchanged

**Action Required:** None

### Communication Strategy

#### Timeline

**v1.10.0 (Deprecation Notice - Release: January 2026)**
- Add deprecation warnings to all CLI commands
- Update README with migration timeline
- Publish migration guide
- Announce on GitHub, PyPI, documentation site

**v1.11.0 (Migration Period - Release: March 2026)**
- Provide `mcp run` wrapper for CLI compatibility
- Update all documentation to MCP-first
- Send migration reminders in release notes
- Host migration webinar/tutorial

**v1.12.0 (CLI Removal - Release: May 2026)**
- Remove CLI command implementations
- Remove wrapper (optional: keep thin wrapper permanently)
- Consolidate documentation
- Final migration guide for stragglers

#### Communication Channels

**Phase 1 (Deprecation Announcement):**
- GitHub announcement issue
- PyPI project description update
- README banner notice
- Release notes prominent section

**Phase 2 (Migration Reminders):**
- Deprecation warnings in CLI output
- Email to known users (if available)
- Stack Overflow / Reddit announcements
- Documentation migration guides

**Phase 3 (Final Notice):**
- v1.11.0 release notes with removal timeline
- GitHub discussions for questions
- Migration support via issues
- Updated roadmap documentation

---

## Success Metrics

### Quantitative Metrics

#### Code Metrics
| Metric | Current (v1.9.0) | Target (v1.12.0) | Reduction |
|--------|------------------|------------------|-----------|
| Total LOC | ~8,500 | ~7,000 | -18% |
| CLI-specific LOC | ~1,900 | ~100 | -95% |
| MCP-specific LOC | ~780 | ~800 | +3% |
| Test LOC | ~2,500 | ~2,200 | -12% |
| Commands module LOC | ~1,769 | ~0 | -100% |

#### Documentation Metrics
| Metric | Current | Target | Reduction |
|--------|---------|--------|-----------|
| Total docs | 32 | 18 | -44% |
| CLI references | 1,306 | ~50 | -96% |
| Setup guides | 5 | 1 | -80% |
| Troubleshooting guides | 4 | 2 | -50% |

#### Maintenance Metrics
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Feature implementation time | 4 hrs | 2 hrs | -50% |
| Bug fix time | 2 hrs | 1 hr | -50% |
| Documentation update time | 3 hrs | 1.5 hrs | -50% |
| Test coverage | 90% | 95% | +5% |

### Qualitative Metrics

#### Developer Experience
- **Onboarding Time:** 2 hours → 1 hour (simpler setup)
- **Clarity:** Single clear path to usage (MCP)
- **Documentation Quality:** Focused, comprehensive MCP guides
- **Feature Discovery:** MCP tool catalog vs scattered CLI commands

#### User Satisfaction
- **AI Assistant Users:** Improved (clearer focus)
- **CLI Users:** Neutral (wrapper maintains functionality)
- **Contributors:** Improved (simpler codebase)

#### Product Positioning
- **Clear Value Prop:** "MCP server for Snowflake AI workflows"
- **Differentiation:** Not another CLI tool, but AI-first interface
- **Market Fit:** Aligns with AI assistant ecosystem growth

### Success Criteria

**Release v1.10.0 Success:**
- [ ] Deprecation warnings deployed to 100% of CLI commands
- [ ] Migration guide published and linked from README
- [ ] Zero regression in MCP functionality
- [ ] Community announcement posted (GitHub, social media)

**Release v1.11.0 Success:**
- [ ] `mcp run` wrapper functional for all commands
- [ ] Documentation 90%+ migrated to MCP-first approach
- [ ] At least 50% of known CLI users migrated to MCP
- [ ] No P0/P1 bugs related to migration

**Release v1.12.0 Success:**
- [ ] CLI commands removed, ~1,900 LOC deleted
- [ ] Documentation consolidated to 18 files
- [ ] Test coverage maintained at 90%+
- [ ] Zero user complaints about missing functionality
- [ ] PyPI description updated to reflect MCP-first positioning

---

## Migration Strategy

### Phased Rollout

#### Phase 1: Deprecation (v1.10.0 - January 2026)

**Duration:** 2 weeks development + 2 months user transition

**Implementation Tasks:**
1. **Add Deprecation Warnings** (Week 1)
   ```python
   # In cli.py and commands/*.py
   import warnings

   def catalog_command(...):
       warnings.warn(
           "CLI commands are deprecated and will be removed in v1.12.0. "
           "Please migrate to MCP interface. "
           "See: https://docs.nanuk-mcp.io/migration",
           DeprecationWarning,
           stacklevel=2
       )
       # Existing implementation
   ```

2. **Update Documentation** (Week 1-2)
   - Add migration guide (`docs/migration/v1.9-to-v1.10.md`)
   - Update README with deprecation notice
   - Add banner to getting-started guide
   - Update architecture docs with timeline

3. **Create Migration Guide** (Week 2)
   - CLI → MCP command mapping table
   - Setup instructions for MCP
   - Example workflows migrated
   - FAQ section

4. **Community Communication** (Week 2)
   - GitHub announcement issue
   - PyPI description update
   - Social media posts
   - Email to known users

**Deliverables:**
- [ ] Deprecation warnings in all CLI commands
- [ ] Migration guide published
- [ ] README updated with timeline
- [ ] Community announcement posted

**Risk Mitigation:**
- Keep 100% CLI functionality during this phase
- Provide multiple migration options
- Clear timeline communication
- Support channel for questions

#### Phase 2: Migration Period (v1.11.0 - March 2026)

**Duration:** 4 weeks development + 2 months transition

**Implementation Tasks:**

1. **Build `mcp run` Wrapper** (Week 1-2)
   ```python
   # src/nanuk_mcp/cli_wrapper.py
   import sys
   import subprocess
   from typing import List

   def cli_to_mcp_args(cli_args: List[str]) -> List[str]:
       """Convert CLI args to MCP tool invocation."""
       # Map CLI commands to MCP tools
       command_map = {
           "catalog": "build_catalog",
           "lineage": "query_lineage",
           "depgraph": "build_dependency_graph",
           # ...
       }

       # Parse and convert
       # Return mcp run compatible args

   def main():
       cli_args = sys.argv[1:]
       mcp_args = cli_to_mcp_args(cli_args)

       # Show migration notice
       print("⚠️  CLI wrapper - please migrate to MCP (removal in v1.12.0)")

       # Execute via mcp run
       subprocess.run(["mcp", "run", "nanuk-mcp"] + mcp_args)
   ```

2. **Consolidate Documentation** (Week 2-3)
   - Merge CLI/MCP guides into MCP-first guides
   - Remove redundant setup instructions
   - Update all code examples to MCP
   - Reorganize docs/ directory structure

3. **Update All Examples** (Week 3)
   - Convert examples/ to use MCP
   - Update tutorial notebooks
   - Revise sample workflows
   - Add MCP-specific best practices

4. **Enhanced Migration Tooling** (Week 4)
   - Auto-detection of CLI usage in logs
   - Migration script for CI/CD configs
   - Interactive migration wizard
   - Validation tool for MCP setup

**Deliverables:**
- [ ] Functional `mcp run` wrapper
- [ ] Documentation 90%+ migrated
- [ ] All examples updated to MCP
- [ ] Migration tooling released

**Risk Mitigation:**
- Wrapper maintains backward compatibility
- Extensive testing of arg mapping
- Clear documentation of differences
- Support for edge cases

#### Phase 3: CLI Removal (v1.12.0 - May 2026)

**Duration:** 3 weeks development

**Implementation Tasks:**

1. **Remove CLI Implementation** (Week 1)
   - Delete `src/nanuk_mcp/commands/` directory
   - Simplify `cli.py` to just MCP launcher or remove entirely
   - Remove CLI-specific tests
   - Update `pyproject.toml` scripts section

2. **Clean Up Configuration** (Week 1)
   - Remove CLI-specific config options
   - Simplify config validation
   - Update default configs
   - Clean up environment variable handling

3. **Consolidate Documentation** (Week 2)
   - Remove CLI-specific docs
   - Update architecture diagrams
   - Consolidate troubleshooting guides
   - Final pass on all references

4. **Update Package Metadata** (Week 2)
   - Update PyPI description
   - Revise README
   - Update keywords and categories
   - Refresh screenshots/examples

5. **Final Testing** (Week 3)
   - Full regression test suite
   - Documentation review
   - User acceptance testing
   - Performance benchmarking

**Deliverables:**
- [ ] CLI code removed (~1,900 LOC)
- [ ] Documentation consolidated
- [ ] All tests passing
- [ ] PyPI metadata updated

**Success Criteria:**
- Zero functionality loss
- All MCP tools working
- Documentation complete and accurate
- No P0/P1 bugs

### Deprecation Timeline

```
v1.9.0              v1.10.0            v1.11.0            v1.12.0
(Current)           (Jan 2026)         (Mar 2026)         (May 2026)
   |                    |                  |                  |
   |---- CLI + MCP -----|-- Deprecation --|-- Migration -----|-- MCP Only --|
   |                    |                  |                  |              |
   |                    | Warnings added   | Wrapper added    | CLI removed  |
   |                    | Guide published  | Docs migrated    | Docs clean   |
   |                    |                  |                  |              |
   |<-- 2 months ------>|<--- 2 months --->|<--- 2 months --->|              |
        Development         Adoption          Transition         Completion
```

**Key Milestones:**
- **Jan 2026:** Deprecation warnings live, migration guide published
- **Mar 2026:** Wrapper available, majority of docs migrated
- **May 2026:** CLI fully removed, MCP-only release

**Communication Cadence:**
- **v1.10.0 release:** Major announcement, migration guide
- **v1.10.0 + 1 month:** Reminder email/post
- **v1.11.0 release:** Migration tools announced, wrapper released
- **v1.11.0 + 1 month:** Final notice for v1.12.0 removal
- **v1.12.0 release:** Completion announcement

### Backward Compatibility

#### Guaranteed Through v1.11.0
- All CLI commands functional (via wrapper)
- Existing scripts continue working
- CI/CD pipelines unaffected
- Python imports unchanged

#### Breaking in v1.12.0
- Direct CLI commands removed
- `nanuk catalog` → Error or redirect to MCP
- Scripts must migrate to MCP or Python imports
- Optional: Keep minimal wrapper permanently

#### Service Layer Stability
- **No changes** to service layer APIs
- Programmatic usage unaffected
- Python library imports continue working
- Internal architecture preserved

---

## Documentation Strategy

### Consolidation Plan

#### Current State (32 docs, 1,306 CLI references)

**Primary Documentation:**
- README.md - Mixed CLI/MCP instructions
- docs/getting-started.md - Dual setup paths
- docs/architecture.md - CLI + MCP architecture
- docs/configuration.md - CLI + MCP config
- docs/mcp-integration.md - MCP-specific guide

**MCP Documentation:**
- docs/mcp/mcp_server_user_guide.md
- docs/mcp/mcp_server_technical_guide.md
- docs/mcp/mcp_architecture.md

**API Documentation:**
- docs/api/README.md
- docs/api/tools/*.md (8 MCP tool docs)

**Feature Guides:**
- docs/advanced_lineage_features.md
- docs/incremental_catalog_guide.md
- docs/cortex/*.md (6 guides)

**Troubleshooting:**
- docs/profile_troubleshooting_guide.md
- docs/profile_validation_quickstart.md
- docs/mcp_diagnostic_tools.md
- docs/testing_coverage_report.md

#### Target State (18 docs, ~50 CLI references)

```
docs/
├── README.md                      # Overview, positioning, quick start
├── getting-started.md             # MCP-first setup (consolidated)
├── architecture.md                # MCP architecture only
├── configuration.md               # Profile + MCP configuration
│
├── tools/                         # MCP Tool Reference (8 tools)
│   ├── README.md                  # Tool catalog
│   ├── build_catalog.md
│   ├── query_lineage.md
│   ├── execute_query.md
│   ├── preview_table.md
│   ├── build_dependency_graph.md
│   ├── test_connection.md
│   ├── health_check.md
│   └── get_catalog_summary.md
│
├── guides/                        # Workflow Guides
│   ├── catalog-workflows.md      # Building and using catalogs
│   ├── lineage-analysis.md       # Data lineage best practices
│   ├── cortex-ai.md              # Cortex AI integration
│   └── troubleshooting.md        # Common issues (consolidated)
│
└── migration/
    └── cli-to-mcp.md             # CLI deprecation migration guide
```

**Total: 18 files (-44% reduction)**

### Documentation Principles

#### 1. Single Source of Truth
- **All functionality documented via MCP tools**
- No parallel CLI/MCP documentation
- Consistent terminology throughout
- Centralized troubleshooting

#### 2. Progressive Disclosure
```
Level 1: Quick Start (5 min)
    ↓
Level 2: Common Workflows (15 min)
    ↓
Level 3: Advanced Features (30 min)
    ↓
Level 4: Architecture Deep Dive (1+ hr)
```

#### 3. Task-Oriented
- **Focus on user goals, not technical details**
- Workflow-based organization
- Clear examples for each use case
- Troubleshooting integrated with features

#### 4. MCP-Native Conventions
```markdown
# Tool: build_catalog

## Overview
Build comprehensive metadata catalog from Snowflake database.

## Quick Example
```
# Via AI Assistant
"Build a catalog for my ANALYTICS database"

# Via MCP CLI
mcp run nanuk-mcp build_catalog --database ANALYTICS
```

## Parameters
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| output_dir | string | No | ./data_catalogue | Output directory |
| database | string | No | (from profile) | Database to catalog |
...
```

### Migration Guide Template

```markdown
# Migrating from CLI to MCP

## Why Migrate?
- Simplified maintenance
- Better AI assistant integration
- Future-proof architecture

## Quick Migration

### Before (CLI)
```bash
nanuk --profile prod catalog --database ANALYTICS
```

### After (MCP)
```bash
# Option 1: Via AI Assistant (Recommended)
"Build a catalog for ANALYTICS database"

# Option 2: Via MCP CLI
mcp run nanuk-mcp build_catalog --database ANALYTICS

# Option 3: Python Import
from nanuk_mcp.service_layer import CatalogService
...
```

## Command Mapping

| Old CLI Command | New MCP Tool | Notes |
|----------------|--------------|-------|
| `nanuk catalog` | `build_catalog` | Same functionality |
| `nanuk lineage TABLE` | `query_lineage` | Enhanced options |
| `nanuk depgraph` | `build_dependency_graph` | Same output |
...

## Migration Checklist
- [ ] Update MCP configuration
- [ ] Test MCP tools work
- [ ] Update CI/CD scripts
- [ ] Remove old CLI references
- [ ] Validate workflows

## Need Help?
- [Troubleshooting Guide](./troubleshooting.md)
- [GitHub Discussions](https://github.com/...)
- [Migration FAQ](#faq)
```

---

## Risk Assessment

### Technical Risks

#### 1. **Breaking Changes for CLI Users**

**Risk Level:** MEDIUM
**Probability:** High (intentional deprecation)
**Impact:** Medium (affects 5% of users)

**Mitigation:**
- Phased approach with 6-month timeline
- Wrapper maintains compatibility through v1.11.0
- Clear migration documentation
- Multiple migration paths (MCP, wrapper, Python imports)

**Contingency:**
- Extend wrapper support if adoption slower than expected
- Provide migration assistance via GitHub discussions
- Consider permanent minimal wrapper if demand exists

#### 2. **Documentation Gaps**

**Risk Level:** MEDIUM
**Probability:** Medium
**Impact:** Medium (confusion during transition)

**Mitigation:**
- Comprehensive migration guide
- Command mapping table
- Example workflows for all use cases
- Staged documentation updates

**Contingency:**
- Quick response to documentation issues
- Community-driven FAQ
- Video tutorials if needed

#### 3. **CI/CD Pipeline Disruption**

**Risk Level:** LOW
**Probability:** Low (wrapper provides compatibility)
**Impact:** High (if occurs)

**Mitigation:**
- Wrapper maintains exact CLI interface through v1.11.0
- Clear upgrade path for CI/CD
- Example GitHub Actions / Jenkins configs
- Early testing with common CI platforms

**Contingency:**
- Emergency wrapper extension if critical issues found
- Direct support for enterprise users
- Rollback plan if major issues discovered

#### 4. **Feature Parity Issues**

**Risk Level:** LOW
**Probability:** Low (MCP already has full feature set)
**Impact:** High (missing functionality)

**Mitigation:**
- Comprehensive testing of all MCP tools
- Feature matrix validation (CLI vs MCP)
- User acceptance testing phase
- Pre-release testing with early adopters

**Contingency:**
- Rapid patch releases for any gaps
- Temporary CLI retention for specific features
- Clear communication of any limitations

### Business Risks

#### 1. **User Attrition**

**Risk Level:** LOW
**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Gradual transition period (6 months)
- Multiple migration options
- Superior MCP experience
- Active support during migration

**Indicators:**
- GitHub issue volume
- PyPI download trends
- User survey responses
- Community engagement

#### 2. **Reputation Impact**

**Risk Level:** LOW
**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Professional communication strategy
- Clear rationale for changes
- Responsive support
- Demonstrate improved value

**Contingency:**
- Address concerns promptly
- Adjust timeline if major pushback
- Highlight success stories

#### 3. **Market Timing**

**Risk Level:** LOW
**Probability:** Low
**Impact:** Low

**Mitigation:**
- MCP adoption growing rapidly
- AI assistants becoming standard
- Aligns with industry trends
- Early mover advantage

**Indicators:**
- MCP ecosystem growth
- AI assistant adoption rates
- Competitor strategies
- User feedback

### Mitigation Strategies

#### Pre-Release
1. **Beta Testing Program**
   - Recruit 10-20 active users
   - Test wrapper functionality
   - Validate documentation
   - Gather feedback

2. **Feature Parity Audit**
   - Verify all CLI features in MCP
   - Test edge cases
   - Validate error handling
   - Confirm performance

3. **Documentation Review**
   - Technical accuracy check
   - User testing of guides
   - Example validation
   - Link verification

#### Post-Release
1. **Monitoring**
   - GitHub issue tracking
   - PyPI download analytics
   - User sentiment analysis
   - Performance metrics

2. **Support**
   - Dedicated migration support channel
   - Quick response to issues
   - FAQ updates based on questions
   - Office hours for complex migrations

3. **Iteration**
   - Weekly release cadence for fixes
   - Documentation updates as needed
   - Wrapper improvements based on feedback
   - Feature enhancements for MCP tools

---

## Implementation Roadmap

### v1.10.0 - Deprecation Notice (January 2026)

**Sprint 1 (Week 1-2): Core Changes**
- [ ] Add deprecation warnings to all CLI commands
- [ ] Create migration guide document
- [ ] Update README with deprecation notice
- [ ] Add banner to getting-started guide

**Sprint 2 (Week 3-4): Communication**
- [ ] Publish GitHub announcement issue
- [ ] Update PyPI project description
- [ ] Social media announcements
- [ ] Email known users (if available)

**Testing:**
- [ ] Verify warnings display correctly
- [ ] Test all CLI commands still functional
- [ ] Validate migration guide accuracy
- [ ] Review documentation changes

**Success Metrics:**
- Zero regression in functionality
- Clear deprecation warnings visible
- Migration guide published and accessible
- Community awareness established

### v1.11.0 - Migration Period (March 2026)

**Sprint 1 (Week 1-2): Wrapper Development**
- [ ] Implement `cli_to_mcp_args()` mapping
- [ ] Build `mcp run` wrapper script
- [ ] Test all CLI commands via wrapper
- [ ] Add migration notices to wrapper output

**Sprint 2 (Week 3-4): Documentation**
- [ ] Consolidate getting-started guide
- [ ] Merge architecture docs
- [ ] Update all tool documentation
- [ ] Reorganize docs/ directory

**Sprint 3 (Week 5-6): Examples & Testing**
- [ ] Convert examples/ to MCP
- [ ] Update tutorial content
- [ ] Comprehensive wrapper testing
- [ ] User acceptance testing

**Testing:**
- [ ] All CLI commands work via wrapper
- [ ] MCP tools 100% functional
- [ ] Documentation accurate and complete
- [ ] No performance regression

**Success Metrics:**
- Wrapper functional for 100% of commands
- 90%+ documentation migrated
- 50%+ CLI users migrated to MCP
- No P0/P1 migration bugs

### v1.12.0 - CLI Removal (May 2026)

**Sprint 1 (Week 1-2): Code Removal**
- [ ] Delete `src/nanuk_mcp/commands/` directory
- [ ] Simplify or remove `cli.py`
- [ ] Remove CLI-specific tests
- [ ] Update `pyproject.toml`

**Sprint 2 (Week 3-4): Documentation & Polish**
- [ ] Remove CLI-specific documentation
- [ ] Final docs consolidation
- [ ] Update architecture diagrams
- [ ] Refresh all examples

**Sprint 3 (Week 5-6): Testing & Release**
- [ ] Full regression testing
- [ ] Performance benchmarking
- [ ] Documentation review
- [ ] Release preparation

**Testing:**
- [ ] All MCP tools working perfectly
- [ ] Service layer unchanged and functional
- [ ] Documentation complete
- [ ] Zero feature loss

**Success Metrics:**
- ~1,900 LOC removed
- Documentation reduced to 18 files
- Test coverage maintained at 90%+
- Clean, focused codebase

### Post-v1.12.0 - Optimization

**Ongoing Activities:**
- Monitor user feedback
- Address edge cases
- Optimize MCP tool performance
- Expand MCP tool capabilities

**Future Enhancements:**
- Advanced MCP features (streaming, etc.)
- Additional AI assistant integrations
- Enhanced error handling
- Performance optimizations

---

## Open Questions

### Technical

1. **Wrapper Permanence**
   - Should we keep a minimal CLI wrapper permanently?
   - What percentage of users would benefit long-term?
   - Maintenance cost vs user value?

   **Decision Point:** v1.11.0 release + 1 month
   **Data Needed:** Wrapper usage analytics, user feedback

2. **Python Import API**
   - Should we formalize Python import API as public?
   - Document service layer for programmatic usage?
   - Versioning strategy for service layer?

   **Decision Point:** v1.12.0 planning
   **Data Needed:** Library usage patterns, user requests

3. **Configuration Simplification**
   - Can we simplify config further with MCP-only approach?
   - Remove CLI-specific environment variables?
   - Consolidate profile management?

   **Decision Point:** v1.12.0 development
   **Data Needed:** Config usage analysis, pain points

### Product

4. **Market Positioning**
   - How to position as "MCP server" vs "Snowflake tool"?
   - PyPI categories and keywords?
   - Target audience messaging?

   **Decision Point:** v1.10.0 release
   **Data Needed:** Market research, competitor analysis

5. **Pricing/Licensing**
   - Any implications for open source licensing?
   - Enterprise support model?
   - Commercial partnerships?

   **Decision Point:** Ongoing
   **Data Needed:** User feedback, market demand

6. **Ecosystem Integration**
   - Deeper integration with specific AI assistants?
   - Partnerships with MCP tool directories?
   - Contribution to MCP protocol development?

   **Decision Point:** v1.12.0+
   **Data Needed:** Ecosystem trends, partnership opportunities

### Community

7. **Migration Support**
   - Dedicated migration support channel?
   - Office hours for complex migrations?
   - Video tutorials needed?

   **Decision Point:** v1.10.0 release
   **Data Needed:** User questions, support volume

8. **Beta Program**
   - Size and composition of beta tester group?
   - Incentives for early adopters?
   - Feedback collection mechanism?

   **Decision Point:** Pre-v1.10.0
   **Data Needed:** Community engagement, volunteer availability

9. **Documentation Format**
   - Interactive documentation (e.g., docs site)?
   - Video content in addition to written guides?
   - AI assistant training data contribution?

   **Decision Point:** v1.11.0 planning
   **Data Needed:** User preferences, resource availability

---

## Appendices

### Appendix A: Command Mapping Table

| CLI Command | MCP Tool | Notes |
|-------------|----------|-------|
| `nanuk catalog` | `build_catalog` | Identical functionality |
| `nanuk lineage TABLE` | `query_lineage` | Enhanced depth/direction options |
| `nanuk depgraph` | `build_dependency_graph` | Same output formats |
| `nanuk query "SQL"` | `execute_query` | Timeout/verbose options added |
| `nanuk preview TABLE` | `preview_table` | Same limit parameter |
| `nanuk test` | `test_connection` | Enhanced health checks |
| `nanuk verify` | `test_connection` | Merged into health check |
| `nanuk config` | (Profile management) | Use `snow connection` CLI |
| `nanuk mcp` | `python -m nanuk_mcp.mcp_server` | Direct server launch |

### Appendix B: File Removal List

**Directories to Remove:**
```
src/nanuk_mcp/commands/
├── __init__.py
├── analyze.py
├── discover.py
├── query.py
├── registry.py
├── setup.py
└── utils.py
```

**Files to Simplify:**
```
src/nanuk_mcp/cli.py          (137 LOC → ~20 LOC or remove)
tests/test_cli.py                  (Remove CLI-specific tests)
docs/* (CLI references)            (Update or remove)
```

**Files Unchanged:**
```
src/nanuk_mcp/mcp_server.py    (Keep as-is)
src/nanuk_mcp/service_layer/   (No changes)
src/nanuk_mcp/catalog/         (No changes)
src/nanuk_mcp/lineage/         (No changes)
src/nanuk_mcp/dependency/      (No changes)
```

### Appendix C: Documentation Reorganization

**Before:**
```
docs/
├── getting-started.md          # CLI + MCP setup
├── architecture.md             # CLI + MCP arch
├── configuration.md            # CLI + MCP config
├── mcp/
│   ├── mcp_server_user_guide.md
│   ├── mcp_server_technical_guide.md
│   └── mcp_architecture.md
├── api/
│   ├── README.md
│   └── tools/ (8 files)
├── advanced_lineage_features.md
├── incremental_catalog_guide.md
├── cortex/ (6 files)
├── profile_troubleshooting_guide.md
├── profile_validation_quickstart.md
├── mcp_diagnostic_tools.md
└── testing_coverage_report.md
```

**After:**
```
docs/
├── README.md                   # Product overview
├── getting-started.md          # MCP setup only
├── architecture.md             # MCP architecture
├── configuration.md            # Profile + MCP config
├── tools/ (8 files)            # MCP tool reference
│   ├── README.md
│   ├── build_catalog.md
│   ├── query_lineage.md
│   └── ...
├── guides/
│   ├── catalog-workflows.md   # Merged from multiple sources
│   ├── lineage-analysis.md    # Advanced lineage + use cases
│   ├── cortex-ai.md           # Consolidated Cortex guides
│   └── troubleshooting.md     # Merged troubleshooting
└── migration/
    └── cli-to-mcp.md          # Migration guide
```

### Appendix D: LOC Reduction Breakdown

**Current State:**
```
Component               LOC
─────────────────────  ─────
cli.py                   137
commands/*.py          1,769
mcp_server.py            779
service_layer/         2,500
lineage/               1,800
catalog/                 800
dependency/              400
Other                  1,315
─────────────────────  ─────
Total                  8,500
```

**Target State (v1.12.0):**
```
Component               LOC    Change
─────────────────────  ─────  ──────
cli.py                   ~20   -117
commands/*.py             0  -1,769
mcp_server.py           ~800    +21
service_layer/         2,500      0
lineage/               1,800      0
catalog/                 800      0
dependency/              400      0
Other                  1,180   -135
─────────────────────  ─────  ──────
Total                  7,000  -1,500
```

**Reduction: 18% overall, 95% CLI-specific code**

### Appendix E: Testing Strategy

**Test Coverage by Phase:**

**v1.10.0 (Deprecation):**
- Existing tests unchanged
- Add tests for deprecation warnings
- Verify CLI functionality preserved

**v1.11.0 (Migration):**
- Wrapper tests (CLI → MCP mapping)
- MCP tool integration tests
- Documentation examples tested
- Performance benchmarks

**v1.12.0 (Removal):**
- Remove CLI-specific tests (~300 LOC)
- Expand MCP tool tests
- Service layer tests unchanged
- End-to-end workflow tests

**Target Coverage:**
- MCP tools: 95%+
- Service layer: 90%+
- Integration: 85%+
- Overall: 90%+

### Appendix F: Communication Templates

#### GitHub Announcement Template

```markdown
# 🚀 Announcing MCP-First Architecture: CLI Deprecation

## TL;DR

nanuk-mcp is transitioning to an MCP-first architecture:
- **v1.10.0 (Jan 2026):** CLI commands deprecated
- **v1.11.0 (Mar 2026):** Migration wrapper provided
- **v1.12.0 (May 2026):** CLI removed, MCP only

## Why?

The future of nanuk-mcp is AI assistants. 95% of users interact via MCP through Claude Code, VS Code, and Cursor. Maintaining dual interfaces slows development and creates confusion.

## What's Changing?

✅ **MCP Interface:** Enhanced, primary path
⚠️ **CLI Commands:** Deprecated, removed in v1.12.0
✅ **Service Layer:** Unchanged, stable
✅ **Python Imports:** Unchanged, supported

## Migration Path

**Option 1: MCP (Recommended)**
```bash
# Configure in .mcp.json
"nanuk-mcp": {
  "command": "python",
  "args": ["-m", "nanuk_mcp.mcp_server"]
}
```

**Option 2: Wrapper (Temporary)**
```bash
# v1.11.0: Use wrapper
nanuk catalog  # Works via mcp run wrapper
```

**Option 3: Python Import**
```python
from nanuk_mcp.service_layer import CatalogService
```

## Timeline

- **Now - Jan 2026:** Use CLI as normal
- **Jan 2026:** Warnings added, migration guide published
- **Mar 2026:** Wrapper available, docs migrated
- **May 2026:** CLI removed, MCP only

## Resources

- [Migration Guide](./docs/migration/cli-to-mcp.md)
- [MCP Setup](./docs/getting-started.md)
- [FAQ](./docs/migration/cli-to-mcp.md#faq)

## Questions?

Ask in this issue or [GitHub Discussions](#).
```

#### PyPI Description Update

```markdown
# nanuk-mcp: MCP Server for Snowflake AI Workflows

**MCP-first platform for AI-powered Snowflake data discovery and lineage analysis.**

## Quick Start

```python
# Install
pip install nanuk-mcp

# Configure MCP
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "python",
      "args": ["-m", "nanuk_mcp.mcp_server"],
      "env": {"SNOWFLAKE_PROFILE": "prod"}
    }
  }
}

# Use via AI Assistant
"Build a catalog of my ANALYTICS database"
"Show me lineage for CUSTOMER_ORDERS"
```

## Features

- 🤖 **AI-Native:** Built for Claude, VS Code, Cursor, Windsurf
- 📊 **Data Cataloging:** Automated metadata extraction
- 🔗 **Lineage Analysis:** Column-level dependency tracking
- 📈 **Dependency Graphs:** Visual object relationships
- 🛡️ **SQL Safety:** Prevents destructive operations
- 🚀 **High Performance:** Parallel operations, connection pooling

## MCP Tools

- `build_catalog` - Extract metadata
- `query_lineage` - Analyze dependencies
- `execute_query` - Run SQL safely
- `build_dependency_graph` - Map relationships
- `preview_table` - Sample data
- `test_connection` - Verify setup

## Documentation

- [Getting Started](https://docs.nanuk-mcp.io/getting-started)
- [MCP Tool Reference](https://docs.nanuk-mcp.io/tools)
- [Architecture](https://docs.nanuk-mcp.io/architecture)

## License

MIT

---

**Note:** CLI interface deprecated. See [migration guide](https://docs.nanuk-mcp.io/migration/cli-to-mcp) for details.
```

---

## Approval & Sign-Off

### Stakeholders

**Product Owner:** Evan Kim
**Technical Lead:** [TBD]
**Documentation Lead:** [TBD]
**Community Manager:** [TBD]

### Approval Checklist

- [ ] Product owner review
- [ ] Technical feasibility validated
- [ ] Resource availability confirmed
- [ ] Timeline approved
- [ ] Risk mitigation accepted
- [ ] Community communication planned

### Sign-Off

**Product Owner:** _________________ Date: _______

**Technical Lead:** _________________ Date: _______

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-07 | Claude Code | Initial PRD creation |

---

**Document Status:** Draft
**Next Review:** [TBD]
**Feedback:** [GitHub Discussion Link]
