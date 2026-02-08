# Cortex XSIAM MCP Server - Installation Guide

> Complete setup guide for integrating Palo Alto Networks Cortex XSIAM with Claude Code via the Model Context Protocol (MCP)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Available Tools](#available-tools)

---

## Overview

This guide walks through the complete installation and configuration of the Cortex XSIAM MCP Server, enabling Claude Code to:

- Query security issues and alerts from Cortex XSIAM
- Search and filter security cases/incidents
- Generate interactive security reports with direct XSIAM links
- Access 90+ additional Cortex XSIAM tools via MCP

**What was installed:**
- Cortex MCP Server (Python-based, FastMCP framework)
- Poetry for dependency management
- MCP server integration with Claude Code
- Bash profile configuration for PATH access

---

## Prerequisites

### Required Software

- **macOS** (tested on Darwin 24.6.0)
- **Python 3.12+** (we used Python 3.13.5)
- **Claude Code CLI** (installed at `~/.local/bin/claude`)
- **Google Chrome** or **Prisma Access Browser**

### Required Credentials

From your Palo Alto Networks Cortex XSIAM tenant:

1. **Tenant URL**: `https://api-YOUR-TENANT.xdr.eu.paloaltonetworks.com`
2. **API Key ID**: `13`
3. **API Key Secret**: `your_128_character_api_key_here`

> **Security Note**: These credentials provide API access to your Cortex XSIAM tenant. Store securely and rotate regularly.

---

## Installation Steps

### Step 1: Extract the Cortex MCP Server

```bash
cd /Users/yourname/Projects/MCP
unzip cortex-mcp.zip -d cortex-mcp
```

**Expected output:**
```
Archive:  cortex-mcp.zip
   creating: cortex-mcp/src
   ...
   inflating: cortex-mcp/README.md
```

### Step 2: Install Poetry

Poetry is required for Python dependency management:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Verification:**
```bash
export PATH="$HOME/.local/bin:$PATH"
poetry --version
# Output: Poetry (version 2.3.2)
```

### Step 3: Install Project Dependencies

Navigate to the project and install all 87 dependencies:

```bash
cd /Users/yourname/Projects/MCP/cortex-mcp
python3 -m venv .venv
poetry install
```

**Expected output:**
```
Installing dependencies from lock file
Package operations: 87 installs, 0 updates, 0 removals
  - Installing annotated-doc (0.0.4)
  ...
  - Installing websockets (15.0.1)
Installing the current project: CortexMCP (1.0.1)
```

**Installed dependencies include:**
- `fastmcp` (2.13.1) - MCP server framework
- `httpx` (0.28.1) - HTTP client
- `pydantic` (2.11.7) - Data validation
- `fastapi` (0.122.0) - API framework
- Plus 83 additional packages

### Step 4: Fix PATH for Claude CLI

Create `~/.bash_profile` to ensure `claude` command is available in new terminals:

```bash
cat > ~/.bash_profile << 'EOF'
# Source .bashrc if it exists
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc"
fi
EOF
```

Verify your `~/.bashrc` contains:
```bash
cat ~/.bashrc
# Should show:
export PATH="$HOME/.local/bin:$PATH"
```

**Apply changes:**
```bash
source ~/.bash_profile
which claude
# Output: /Users/yourname/.local/bin/claude
```

---

## Configuration

### Register MCP Server with Claude Code

Use the Claude CLI to register the Cortex MCP server:

```bash
export PATH="$HOME/.local/bin:$PATH"

claude mcp add-json "cortex-mcp-server" --scope user '{
  "type": "stdio",
  "command": "/Users/yourname/Projects/MCP/cortex-mcp/.venv/bin/python",
  "args": ["/Users/yourname/Projects/MCP/cortex-mcp/src/main.py"],
  "env": {
    "CORTEX_MCP_PAPI_URL": "https://api-YOUR-TENANT.xdr.eu.paloaltonetworks.com",
    "CORTEX_MCP_PAPI_AUTH_HEADER": "your_128_character_api_key_here",
    "CORTEX_MCP_PAPI_AUTH_ID": "13",
    "MCP_TRANSPORT": "stdio"
  }
}'
```

**Expected output:**
```
Added stdio MCP server cortex-mcp-server to user config
```

### Configuration File Location

The configuration is stored in:
```
~/.claude.json
```

This makes the MCP server available across all your Claude Code sessions (user scope).

---

## Verification

### 1. Verify MCP Server Registration

```bash
claude mcp list
```

**Expected output:**
```
Checking MCP server health...

cortex-mcp-server: /Users/yourname/Projects/MCP/cortex-mcp/.venv/bin/python /Users/yourname/Projects/MCP/cortex-mcp/src/main.py - ✓ Connected
```

### 2. Start Claude Code and Test

```bash
claude
```

In Claude Code, test with:
```
Get the top 5 issues from my Cortex tenant in the last 24 hours
```

You should see Claude successfully query your XSIAM tenant and return results.

### 3. Verify Available Tools

In Claude Code, run `/mcp` to see all loaded tools. You should see:

```
Loaded
├ mcp__cortex-mcp-server__get_issues
├ mcp__cortex-mcp-server__get_cases
└ ... (90+ additional tools)
```

---

## Usage Examples

### Example 1: Query Recent Security Issues

**Prompt:**
```
Get the top issues from Cortex in the last 3 days
```

**What happens:**
1. Claude calls `mcp__cortex-mcp-server__get_issues`
2. Filters by `_insert_time >= (3 days ago timestamp)`
3. Sorts by severity (High → Medium → Low)
4. Returns formatted results with issue details

### Example 2: Generate Security Report

**Prompt:**
```
Create a beautiful HTML report summarizing all issues and cases, then open it in Prisma Access Browser
```

**What happens:**
1. Claude fetches issues via `get_issues`
2. Claude fetches cases via `get_cases`
3. Generates an interactive HTML dashboard at `/Users/yourname/Projects/MCP/cortex-report.html`
4. Opens the report in Prisma Access Browser
5. All issues/cases are clickable links to your XSIAM tenant

**Report features:**
- Stats dashboard (issue counts by severity)
- Key findings cards
- Related cases section
- Clickable cards that deep-link to XSIAM
- Responsive design with dark theme
- Direct links: `https://YOUR-TENANT.xdr.eu.paloaltonetworks.com/issue-view?issueId=...`

### Example 3: Search Specific Issues

**Prompt:**
```
Show me all HIGH severity issues with external_id containing "7597340922312920988"
```

**What happens:**
1. Claude constructs filter: `[{"field": "severity", "operator": "in", "value": ["HIGH"]}, {"field": "external_id", "operator": "contains", "value": "7597340922312920988"}]`
2. Calls `get_issues` with filters
3. Returns matching issues with full details

---

## Available Tools

### Core Security Tools (Most Used)

| Tool | Description | Use Case |
|------|-------------|----------|
| `get_issues` | Retrieve security issues/alerts | Monitor threats, investigate incidents |
| `get_cases` | Retrieve security cases/incidents | Track investigation progress |
| `get_filtered_endpoints` | Query endpoint inventory | Asset discovery, threat hunting |
| `get_vulnerabilities` | Fetch vulnerability data | Risk assessment, patch planning |
| `get_assets` | Query asset inventory | Asset management, exposure analysis |
| `run_xql_query` | Execute XQL queries | Advanced threat hunting |

### Threat Intelligence Tools

| Tool | Description |
|------|-------------|
| `enrich_domain` | Get threat intel on domains |
| `enrich_ip_address` | Get threat intel on IPs |
| `enrich_file_hash` | Get threat intel on file hashes |
| `enrich_url` | Get threat intel on URLs |

### Response Actions

| Tool | Description |
|------|-------------|
| `isolate_endpoint` | Isolate a compromised endpoint |
| `unisolate_endpoint` | Remove endpoint isolation |
| `quarantine_files` | Quarantine malicious files |
| `restore_file` | Restore quarantined files |
| `terminate_process` | Kill malicious processes |
| `retrieve_files` | Retrieve files from endpoints |

### Content Management (90+ Tools Total)

- **Playbook operations**: `run_playbook`, `create_playbook`, `get_playbook`, etc.
- **Integration management**: `list_integrations`, `get_integration_commands`
- **Content creation**: `create_xsiam_dashboard`, `create_xsiam_report`, `create_modeling_rule`
- **SDK operations**: `sdk_init`, `sdk_validate`, `sdk_lint`, `sdk_upload`, etc.
- **Documentation**: `get_xsoar_best_practices`, `get_xsiam_content_guide`, etc.

**View all tools:**
```bash
claude mcp list
```

Or in a Claude Code session:
```
/mcp
```

---

## Troubleshooting

### Issue: "No MCP servers configured"

**Cause**: The MCP server wasn't registered correctly or Claude Code can't find the config.

**Solution:**
```bash
# Verify registration
claude mcp list

# If not listed, re-run the add-json command from Configuration section
```

### Issue: "cortex-mcp-server: ✗ Connection failed"

**Possible causes:**
1. Python venv not activated or incorrect path
2. Missing dependencies
3. Invalid XSIAM credentials

**Solution:**
```bash
# Test Python path
/Users/yourname/Projects/MCP/cortex-mcp/.venv/bin/python --version
# Should show: Python 3.13.5

# Test manual start
cd /Users/yourname/Projects/MCP/cortex-mcp
export CORTEX_MCP_PAPI_URL="https://api-YOUR-TENANT.xdr.eu.paloaltonetworks.com"
export CORTEX_MCP_PAPI_AUTH_HEADER="YOUR_API_KEY"
export CORTEX_MCP_PAPI_AUTH_ID="13"
export MCP_TRANSPORT="stdio"
.venv/bin/python src/main.py
```

### Issue: `claude` command not found in new terminal

**Cause**: `~/.bash_profile` not sourcing `~/.bashrc`

**Solution:**
```bash
# Verify .bash_profile exists
cat ~/.bash_profile
# Should contain: source "$HOME/.bashrc"

# If missing, recreate:
cat > ~/.bash_profile << 'EOF'
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc"
fi
EOF

# Apply immediately
source ~/.bash_profile
```

### Issue: Authentication errors (401/403)

**Cause**: Invalid or expired API credentials

**Solution:**
1. Log into your Cortex XSIAM tenant
2. Navigate to Settings → API Keys
3. Verify the API Key ID (`13`) and regenerate the secret if needed
4. Update the MCP configuration:
```bash
claude mcp remove cortex-mcp-server
claude mcp add-json "cortex-mcp-server" --scope user '{...}' # with new credentials
```

### Issue: "Module not found" errors when running

**Cause**: Dependencies not installed in venv

**Solution:**
```bash
cd /Users/yourname/Projects/MCP/cortex-mcp
poetry install
```

---

## Project Structure

```
/Users/yourname/Projects/MCP/
├── cortex-mcp.zip                    # Original distribution
├── cortex-mcp/                       # Extracted project
│   ├── .venv/                        # Python virtual environment
│   ├── src/
│   │   ├── main.py                   # MCP server entry point
│   │   ├── service/cortex_mcp/       # Server implementation
│   │   ├── usecase/                  # Business logic
│   │   │   ├── builtin_components/   # Built-in MCP tools
│   │   │   │   ├── issues.py         # Issues tool
│   │   │   │   ├── cases.py          # Cases tool
│   │   │   │   └── openapi/          # OpenAPI-based tools
│   │   │   ├── custom_components/    # User-defined tools
│   │   │   └── remote_components/    # Cortex-managed tools
│   │   ├── config/                   # Configuration
│   │   ├── pkg/                      # HTTP client & utilities
│   │   └── entities/                 # Data models
│   ├── pyproject.toml                # Poetry configuration
│   ├── poetry.lock                   # Locked dependencies
│   └── README.md                     # Project documentation
├── cortex-report.html                # Generated security report
└── INSTALLATION_GUIDE.md             # This file
```

---

## Security Best Practices

### API Key Security

1. **Never commit credentials** to version control
2. **Rotate API keys regularly** (recommended: every 90 days)
3. **Use user-scoped MCP config** to keep credentials out of project files
4. **Limit API key permissions** to only what's needed

### Network Security

1. **Prisma Access Browser** provides secure access to XSIAM tenant
2. All API calls use **HTTPS** (enforced by the client)
3. **Tenant URL includes API subdomain** (`api-YOUR-TENANT...`)

### Audit

Monitor API usage in your XSIAM tenant:
- Settings → Audit Logs → API Activity

---

## Next Steps

### Extend Functionality

Add custom MCP tools to `cortex-mcp/src/usecase/custom_components/`:

1. Create a new Python file (e.g., `custom_search.py`)
2. Inherit from `BaseModule`
3. Implement `register_tools()` and `register_resources()`
4. Restart Claude Code to load the new tool

**Example:**
```python
from fastmcp import FastMCP, Context
from usecase.base_module import BaseModule

async def custom_search(ctx: Context, query: str) -> str:
    """Custom search implementation"""
    # Your logic here
    return f"Search results for: {query}"

class CustomSearchModule(BaseModule):
    def register_tools(self):
        self._add_tool(custom_search)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
```

### Update Remote Tools

Cortex provides managed tools that auto-update:

```bash
cd /Users/yourname/Projects/MCP/cortex-mcp
export PATH="$HOME/.local/bin:$PATH"

# Run the CLI update command
.venv/bin/python src/cli.py update \
  --api_key_id 13 \
  --api_key_secret "YOUR_KEY" \
  --server-url "https://api-YOUR-TENANT.xdr.eu.paloaltonetworks.com"
```

This downloads the latest tools into `src/usecase/remote_components/`.

### Automate Report Generation

Create a scheduled report using cron:

```bash
# Add to crontab (crontab -e)
0 8 * * * /Users/yourname/.local/bin/claude -c "Generate Cortex security report for yesterday and email it to me"
```

---

## Support & Resources

### Official Documentation

- **Cortex MCP Server**: `/Users/yourname/Projects/MCP/cortex-mcp/README.md`
- **Claude Code Docs**: https://code.claude.com/docs
- **MCP Protocol Spec**: https://modelcontextprotocol.io

### Key Files

- **MCP Config**: `~/.claude.json`
- **Bash Profile**: `~/.bash_profile` and `~/.bashrc`
- **Project Root**: `/Users/yourname/Projects/MCP/cortex-mcp/`
- **Virtual Env**: `/Users/yourname/Projects/MCP/cortex-mcp/.venv/`

### Logs & Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
claude
```

Check MCP server health:
```bash
claude mcp list
```

---

## Summary

You now have a fully functional Cortex XSIAM MCP server integrated with Claude Code, providing:

✅ 90+ security operations tools
✅ Real-time threat intelligence
✅ Automated security reporting
✅ Direct XSIAM tenant integration
✅ Extensible architecture for custom tools

**Quick test:**
```bash
source ~/.bash_profile
claude
# In Claude: "Get the top 5 high severity issues from the last week"
```

---

*Installation completed: February 5, 2026*
*Tenant: YOUR-TENANT.xdr.eu.paloaltonetworks.com*
*Python: 3.13.5 | Poetry: 2.3.2 | FastMCP: 2.13.1*
