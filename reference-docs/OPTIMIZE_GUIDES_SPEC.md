# Specification: Optimize XSOAR Dev Guides - On-Demand Loading

## Overview

Refactor the XSOAR development guides from hardcoded Python strings to external markdown files loaded on-demand. This reduces MCP server startup time and memory usage.

---

## Current Implementation

### File Location
```
/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsoar_dev_guides.py
```

### Current Structure
- **Total lines**: ~1,819 lines
- **Guide content**: ~1,546 lines of markdown embedded as Python string constants
- **Loading behavior**: All content loaded into memory at MCP server startup
- **Problem**: Wastes memory if guides are never used

### Current String Constants

| Constant Name | Approx Lines | Description |
|---------------|--------------|-------------|
| `PATTERN_RECOGNITION_GUIDE` | 156 | How to identify integration patterns |
| `LONG_RUNNING_GUIDE` | 416 | Long-running integration development |
| `EVENT_COLLECTOR_GUIDE` | 318 | Event collector/fetch integration |
| `SCHEDULED_COMMANDS_GUIDE` | 177 | Polling pattern (@polling_function) |
| `MIRRORING_GUIDE` | 176 | Bidirectional sync integrations |
| `FEED_GUIDE` | 202 | Threat intel feed integrations |
| `THREADING_BEST_PRACTICES` | 45 | Why background threads fail |
| `STATE_MANAGEMENT_GUIDE` | 56 | Integration context vs in-memory |

### Current Tool Functions

```python
async def get_xsoar_pattern_guide(ctx: Context) -> str:
    """Get guide for recognizing which XSOAR integration pattern to use."""
    return PATTERN_RECOGNITION_GUIDE

async def get_xsoar_long_running_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR long-running integrations."""
    return LONG_RUNNING_GUIDE

# ... similar for other guides ...

async def get_xsoar_best_practices(
    ctx: Context,
    topic: Annotated[str, Field(description="...")] = "all"
) -> str:
    """Get XSOAR integration development best practices for specific topics."""
    practices = {
        "threading": THREADING_BEST_PRACTICES,
        "state": STATE_MANAGEMENT_GUIDE
    }
    if topic == "all":
        return "\n\n---\n\n".join(practices.values())
    if topic in practices:
        return practices[topic]
    return f"Unknown topic '{topic}'. Available: {', '.join(practices.keys())}, all"
```

---

## Target Implementation

### New Directory Structure

```
/Users/apekarovsky/projects/cortex-mcp/
├── src/usecase/custom_components/
│   ├── xsoar_dev_guides.py          # Refactored - slim loader (~80 lines)
│   └── guides/                       # NEW directory
│       ├── pattern_recognition.md
│       ├── long_running.md
│       ├── event_collector.md
│       ├── scheduled_commands.md
│       ├── mirroring.md
│       ├── feed.md
│       ├── best_practices_threading.md
│       └── best_practices_state.md
```

### File Mapping

| Old Constant | New File |
|--------------|----------|
| `PATTERN_RECOGNITION_GUIDE` | `guides/pattern_recognition.md` |
| `LONG_RUNNING_GUIDE` | `guides/long_running.md` |
| `EVENT_COLLECTOR_GUIDE` | `guides/event_collector.md` |
| `SCHEDULED_COMMANDS_GUIDE` | `guides/scheduled_commands.md` |
| `MIRRORING_GUIDE` | `guides/mirroring.md` |
| `FEED_GUIDE` | `guides/feed.md` |
| `THREADING_BEST_PRACTICES` | `guides/best_practices_threading.md` |
| `STATE_MANAGEMENT_GUIDE` | `guides/best_practices_state.md` |

---

## Implementation Steps

### Step 1: Create guides/ Directory

Create directory at:
```
/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/guides/
```

### Step 2: Extract Content to MD Files

For each string constant in `xsoar_dev_guides.py`:

1. Find the constant (e.g., `PATTERN_RECOGNITION_GUIDE = """...."""`)
2. Copy the content between the triple quotes
3. Save to corresponding `.md` file
4. Ensure no leading/trailing whitespace issues

**Important**: The content starts with markdown headers (e.g., `# XSOAR Integration Pattern Recognition Guide`). Keep the content exactly as-is.

### Step 3: Refactor xsoar_dev_guides.py

Replace the entire file with this implementation:

```python
"""
XSOAR Development Pattern Guides

Provides comprehensive development guides for XSOAR integrations as MCP tools.
Guides are loaded on-demand from external markdown files to reduce startup time.
"""

import logging
from pathlib import Path
from typing import Annotated
from fastmcp import Context, FastMCP
from pydantic import Field
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

# Directory containing guide markdown files
GUIDES_DIR = Path(__file__).parent / "guides"

# In-memory cache for loaded guides (per MCP server session)
_guide_cache: dict[str, str] = {}


def _load_guide(filename: str) -> str:
    """
    Load guide content on-demand from markdown file.

    Uses simple caching - each guide loaded once per server session.
    """
    if filename in _guide_cache:
        return _guide_cache[filename]

    guide_path = GUIDES_DIR / filename
    if not guide_path.exists():
        error_msg = f"Guide file not found: {guide_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    try:
        content = guide_path.read_text(encoding="utf-8")
        _guide_cache[filename] = content
        logger.debug(f"Loaded guide: {filename}")
        return content
    except Exception as e:
        error_msg = f"Failed to load guide {filename}: {e}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

async def get_xsoar_pattern_guide(ctx: Context) -> str:
    """Get guide for recognizing which XSOAR integration pattern to use.

    **CALL THIS TOOL FIRST** before creating any XSOAR integration!

    This tool teaches you how to automatically identify the correct integration
    pattern based on the user's request, without them needing to specify
    "long-running" or "event collector".

    Recognition keywords:
    - "monitor", "continuously", "every X seconds" → Long-Running Integration
    - "fetch", "pull", "import", "send to XSIAM" → Event Collector Integration
    - "query", "get", "lookup" (one-time) → Regular Integration

    Returns complete guide with:
    - Pattern recognition decision tree
    - Keywords to look for in user requests
    - Which guide to call for each pattern
    - Quick reference for all three patterns
    """
    return _load_guide("pattern_recognition.md")


async def get_xsoar_long_running_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR long-running integrations.

    Use this tool when user requests:
    - Monitoring integrations (ping monitors, service health checks)
    - Webhook receivers (Slack, Teams, generic webhooks)
    - Polling integrations (checking APIs on intervals)
    - Any integration that runs continuously

    Based on real debugging experience fixing PingMonitor integration.

    Covers:
    - Complete architecture pattern (while True in main thread)
    - ❌ Critical mistakes: background threading, executeCommand, exiting loop
    - State management with integration context
    - Creating incidents for alerts
    - Complete working example (PingMonitor)
    - Testing checklist

    Returns: Complete markdown guide with working code examples
    """
    return _load_guide("long_running.md")


async def get_xsoar_event_collector_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR event collector integrations.

    Use this tool when user requests:
    - Fetching data from external sources (ServiceNow, Jira, Splunk)
    - Importing logs/events into XSIAM
    - Pulling tickets/alerts periodically
    - Collecting data from APIs and sending to XSIAM

    Covers:
    - fetch-incidents command pattern
    - send_events_to_xsiam() usage
    - Last run tracking (demisto.getLastRun/setLastRun)
    - Pagination for large datasets
    - Deduplication strategies
    - Complete working example (ServiceNow)

    Returns: Complete markdown guide with working code examples
    """
    return _load_guide("event_collector.md")


async def get_xsoar_scheduled_commands_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR scheduled commands (polling pattern).

    Use this tool when user requests:
    - Sandbox file analysis (submit → poll → get results)
    - Long-running searches that require status checking
    - Async external operations (detonation, scanning, analysis)
    - Any operation that can't return results immediately

    Covers:
    - polling: true configuration
    - @polling_function decorator usage
    - PollResult object and args_for_next_run
    - Complete working example (VirusTotal file scan)
    - Polling intervals and timeouts

    Returns: Complete markdown guide with working code examples
    """
    return _load_guide("scheduled_commands.md")


async def get_xsoar_mirroring_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR mirroring integrations.

    Use this tool when user requests:
    - Bidirectional sync with ServiceNow, Jira, ticketing systems
    - Chat-based incident management (Slack, Teams)
    - Two-way incident synchronization
    - Mirror incidents between XSOAR and external systems

    Covers:
    - ismappable: true configuration
    - Required commands: get-remote-data, update-remote-system, get-modified-remote-data, get-mapping-fields
    - dbotMirror fields (direction, id, instance, tags)
    - Complete implementation patterns
    - Optimization with get-modified-remote-data

    Returns: Complete markdown guide with working code examples
    """
    return _load_guide("mirroring.md")


async def get_xsoar_feed_guide(ctx: Context) -> str:
    """Get comprehensive guide for implementing XSOAR feed integrations.

    Use this tool when user requests:
    - Threat intelligence feed ingestion
    - TAXII or STIX feed integration
    - Custom IOC sources (APIs, RSS, CSV files)
    - Indicator collection from threat intelligence vendors

    Covers:
    - isFeed: true configuration
    - Naming convention (must end with "Feed")
    - 6 required feed parameters (reputation, reliability, expiration, etc.)
    - fetch-indicators command pattern
    - demisto.createIndicators() with batching (~2000 per batch)
    - Incremental feed support

    Returns: Complete markdown guide with working code examples
    """
    return _load_guide("feed.md")


async def get_xsoar_best_practices(
    ctx: Context,
    topic: Annotated[
        str,
        Field(
            default="all",
            description="Best practices topic: 'threading', 'state', or 'all'"
        )
    ] = "all"
) -> str:
    """Get XSOAR integration development best practices for specific topics.

    Use this tool to:
    - Check specific patterns when unsure
    - Fix issues (e.g., threading errors)
    - Learn state management
    - Understand error handling

    Args:
        topic: Specific topic or "all". Options:
            - "all": All best practices (default)
            - "threading": Threading patterns (why background threads fail)
            - "state": State management (integration context vs in-memory)

    Returns: Best practices guide for the specified topic
    """
    topic_to_file = {
        "threading": "best_practices_threading.md",
        "state": "best_practices_state.md"
    }

    if topic == "all":
        guides = []
        for file in topic_to_file.values():
            guides.append(_load_guide(file))
        return "\n\n---\n\n".join(guides)

    if topic in topic_to_file:
        return _load_guide(topic_to_file[topic])

    return f"Unknown topic '{topic}'. Available: {', '.join(topic_to_file.keys())}, all"


# ============================================================================
# MODULE REGISTRATION
# ============================================================================

class XSOARDevGuidesModule(BaseModule):
    """
    MCP module providing XSOAR development guides.

    Guides are loaded on-demand from external markdown files
    to reduce server startup time and memory usage.
    """

    def register_tools(self):
        """Register all guide tools with the MCP server."""
        self._add_tool(get_xsoar_pattern_guide)
        self._add_tool(get_xsoar_long_running_guide)
        self._add_tool(get_xsoar_event_collector_guide)
        self._add_tool(get_xsoar_scheduled_commands_guide)
        self._add_tool(get_xsoar_mirroring_guide)
        self._add_tool(get_xsoar_feed_guide)
        self._add_tool(get_xsoar_best_practices)

    def register_resources(self):
        """No resources for guides module."""
        pass
```

### Step 4: Verify

After implementation:

1. **Check files exist**:
   ```bash
   ls -la /Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/guides/
   ```

2. **Test each tool** via MCP:
   - Call `get_xsoar_pattern_guide` - should return pattern recognition content
   - Call `get_xsoar_long_running_guide` - should return long-running guide
   - Call `get_xsoar_best_practices` with topic="threading" - should return threading guide
   - Call `get_xsoar_best_practices` with topic="all" - should return both best practices

3. **Verify caching**: Call same guide twice, second call should be from cache (check logs)

---

## Content Extraction Reference

### How to Extract Each Guide

Open `/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsoar_dev_guides.py` and:

1. **pattern_recognition.md**: Lines ~24-179 (content of `PATTERN_RECOGNITION_GUIDE`)
2. **long_running.md**: Lines ~185-600 (content of `LONG_RUNNING_GUIDE`)
3. **event_collector.md**: Lines ~606-923 (content of `EVENT_COLLECTOR_GUIDE`)
4. **scheduled_commands.md**: Lines ~1038-1214 (content of `SCHEDULED_COMMANDS_GUIDE`)
5. **mirroring.md**: Lines ~1220-1395 (content of `MIRRORING_GUIDE`)
6. **feed.md**: Lines ~1401-1603 (content of `FEED_GUIDE`)
7. **best_practices_threading.md**: Lines ~929-973 (content of `THREADING_BEST_PRACTICES`)
8. **best_practices_state.md**: Lines ~979-1032 (content of `STATE_MANAGEMENT_GUIDE`)

**Note**: Line numbers are approximate. Look for the constant name and extract content between the triple quotes.

---

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| Startup memory | ~1,546 lines loaded | 0 lines loaded |
| First guide call | Instant (already loaded) | ~1ms (file read) |
| Subsequent calls | Instant | Instant (cached) |
| Maintainability | Edit Python strings | Edit markdown files |
| IDE support | Poor (strings in Python) | Full (native markdown) |

---

## Acceptance Criteria

- [ ] 8 markdown files created in `guides/` directory
- [ ] `xsoar_dev_guides.py` refactored to ~80 lines
- [ ] All 7 tool functions still work correctly
- [ ] Guide content matches original exactly
- [ ] Caching works (verified via logs)
- [ ] No Python syntax errors
- [ ] MCP server starts without errors
