# Cortex XSIAM MCP Server - Installation & Configuration Guide

## Overview

The Cortex XSIAM MCP (Model Context Protocol) Server provides 41 security operations tools for AI assistants including Claude Code, Claude Desktop, and Google Gemini CLI. These tools enable comprehensive security incident investigation, threat hunting, and automated response capabilities.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Client Setup](#client-setup)
   - [Claude Code](#claude-code-cli)
   - [Claude Desktop](#claude-desktop)
   - [Google Gemini CLI](#google-gemini-cli)
5. [Adding Custom Tools](#adding-custom-tools)
6. [Tool Reference](#tool-reference)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.12 or higher
- **Operating System**: macOS, Linux, or Windows (with WSL)
- **Memory**: Minimum 4GB RAM
- **Disk**: 500MB free space

### Cortex XSIAM Requirements
- Active Cortex XSIAM tenant
- API Key with appropriate permissions
- API Key ID
- Tenant API URL (e.g., `https://api-{tenant}.xdr.{region}.paloaltonetworks.com`)

### Required API Permissions
Your API key should have the following permissions:
- Incidents: Read, Update
- Alerts/Issues: Read, Update
- Endpoints: Read, Isolate, Scan
- Scripts: Execute
- Files: Quarantine, Retrieve
- IOCs: Read, Write
- War Room: Read, Write

---

## Installation

### Option 1: Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/PaloAltoNetworks/cortex-mcp.git
cd cortex-mcp

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
poetry install
```

### Option 2: Docker

```bash
# Clone the repository
git clone https://github.com/PaloAltoNetworks/cortex-mcp.git
cd cortex-mcp

# Build the Docker image
docker build -t cortex-mcp .
```

### Option 3: pip (Minimal)

```bash
# Clone the repository
git clone https://github.com/PaloAltoNetworks/cortex-mcp.git
cd cortex-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies manually
pip install fastmcp mcp requests fastapi uvicorn
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required - Cortex XSIAM API Configuration
CORTEX_MCP_PAPI_URL=https://api-{tenant}.xdr.{region}.paloaltonetworks.com
CORTEX_MCP_PAPI_AUTH_HEADER=your_api_key_here
CORTEX_MCP_PAPI_AUTH_ID=your_api_key_id_here

# Optional - Transport Configuration
MCP_TRANSPORT=stdio                    # Options: stdio, streamable-http
MCP_HOST=0.0.0.0                       # For HTTP transport
MCP_PORT=8080                          # For HTTP transport
MCP_PATH=/api/v1/stream/mcp            # For HTTP transport
```

### Getting Your API Credentials

1. Log into Cortex XSIAM console
2. Navigate to **Settings** → **Configurations** → **API Keys**
3. Click **+ New Key**
4. Select required permissions (see Prerequisites)
5. Copy the **API Key** and **API Key ID**
6. Note your tenant URL from the browser address bar

---

## Client Setup

### Claude Code CLI

Claude Code uses a JSON configuration file to define MCP servers.

#### Step 1: Add the MCP Server

Run this command to add the Cortex XSIAM MCP server:

```bash
claude mcp add cortex-xsiam \
  -e CORTEX_MCP_PAPI_URL=https://api-{tenant}.xdr.{region}.paloaltonetworks.com \
  -e CORTEX_MCP_PAPI_AUTH_HEADER=your_api_key \
  -e CORTEX_MCP_PAPI_AUTH_ID=your_api_key_id \
  -- python /path/to/cortex-mcp/src/main.py
```

#### Step 2: Verify Installation

```bash
claude mcp list
```

You should see `cortex-xsiam` in the list of configured servers.

#### Step 3: Using the Tools

Start Claude Code and the tools will be automatically available:

```bash
claude
```

Example prompts:
- "Show me the latest high severity cases"
- "Investigate case 350 and generate an AI summary"
- "Hunt for PowerShell execution in the last 24 hours"
- "Isolate endpoint Server-DC-1"

---

### Claude Desktop

Claude Desktop uses a `claude_desktop_config.json` file for MCP server configuration.

#### Step 1: Locate Configuration File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Step 2: Add MCP Server Configuration

**Option A: Local Python Installation**

```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "python",
      "args": [
        "/path/to/cortex-mcp/src/main.py"
      ],
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-{tenant}.xdr.{region}.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "your_api_key_id",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Option B: Docker Container**

```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "docker",
      "args": [
        "run",
        "--env-file",
        "/path/to/.env",
        "-i",
        "--rm",
        "cortex-mcp"
      ]
    }
  }
}
```

**Option C: HTTP Transport (Remote Server)**

First, start the server:
```bash
MCP_TRANSPORT=streamable-http MCP_PORT=8080 python src/main.py
```

Then configure Claude Desktop:
```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8080/api/v1/stream/mcp",
        "--transport",
        "http-only",
        "--allow-http"
      ]
    }
  }
}
```

#### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

---

### Google Gemini CLI

Google Gemini CLI supports MCP servers through its configuration system.

#### Step 1: Install Gemini CLI

```bash
npm install -g @anthropic-ai/gemini-cli
# or
pip install google-gemini-cli
```

#### Step 2: Configure MCP Server

Create or edit `~/.gemini/config.json`:

```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "python",
      "args": ["/path/to/cortex-mcp/src/main.py"],
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-{tenant}.xdr.{region}.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "your_api_key_id"
      }
    }
  }
}
```

#### Step 3: Using with Gemini

```bash
gemini chat --mcp cortex-xsiam
```

---

## Adding Custom Tools

The Cortex XSIAM MCP server supports two types of custom tools:

### Python Tools

Place Python files in: `src/usecase/custom_components/`

```python
# Example: my_custom_tool.py
import logging
from typing import Annotated
from fastmcp import Context, FastMCP
from pydantic import Field
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher
from pkg.util import create_response

logger = logging.getLogger(__name__)

async def my_custom_tool(
    ctx: Context,
    param1: Annotated[str, Field(description="Description of parameter")],
) -> str:
    """
    Tool description shown to the AI.
    """
    fetcher = await get_fetcher(ctx)
    response = await fetcher.send_request("/your/api/endpoint", data={})
    return create_response(data=response)

class MyCustomModule(BaseModule):
    def register_tools(self):
        self._add_tool(my_custom_tool)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
```

### OpenAPI Tools

Place YAML files in: `src/usecase/custom_components/openapi/`

```yaml
# Example: my_api_tool.yaml
openapi: 3.0.0
paths:
  /public_api/v1/your/endpoint:
    post:
      summary: Short description
      description: |-
        Detailed description of what the tool does.
        Use this when:
        - Scenario 1
        - Scenario 2
      operationId: my_api_tool
      tags:
        - Category
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                request_data:
                  type: object
      responses:
        '200':
          description: Success
```

### Archive Contents

The `cortex-xsiam-tools/` archive contains:

```
cortex-xsiam-tools/
├── __init__.py
├── contributing_events.py      # Correlation alert events
├── enrich_domain.py            # Domain reputation lookup
├── enrich_file_hash.py         # File hash reputation
├── enrich_ip_address.py        # IP reputation lookup
├── enrich_url.py               # URL reputation lookup
├── incident_details.py         # Case forensic data
├── integration_discovery.py    # XSOAR integration list
├── risky_entities.py           # ITDR risky users/hosts
├── run_xsoar_automation.py     # Execute XSOAR commands
├── terminate_process.py        # Kill process by name
├── threat_intel_enrichment.py  # TI enrichment wrapper
├── update_case_summary.py      # AI investigation summary
├── update_case_timeline.py     # HTML timeline generator
├── update_incident.py          # Update case properties
├── update_issue.py             # Update alert properties
├── xql_query.py                # XQL threat hunting
└── openapi/
    ├── abort_scan.yaml
    ├── add_war_room_entry.yaml
    ├── get_action_status.yaml
    ├── get_alert_events.yaml
    ├── get_endpoints.yaml
    ├── get_file_retrieval_details.yaml
    ├── get_quarantine_status.yaml
    ├── get_script_execution_results.yaml
    ├── get_script_execution_status.yaml
    ├── get_script_metadata.yaml
    ├── get_scripts.yaml
    ├── get_war_room_entries.yaml
    ├── insert_indicators_csv.yaml
    ├── insert_indicators_json.yaml
    ├── isolate_endpoint.yaml
    ├── quarantine_files.yaml
    ├── restore_file.yaml
    ├── retrieve_files.yaml
    ├── run_script.yaml
    ├── run_snippet_code_script.yaml
    ├── scan_endpoint.yaml
    ├── terminate_causality.yaml
    └── unisolate_endpoint.yaml
```

To install: Copy contents to `src/usecase/custom_components/`

---

## Tool Reference

### Cases (5 tools)
| Tool | Description |
|------|-------------|
| `get_cases` | List and filter security cases |
| `get_incident_extra_data` | Get full forensic case details |
| `update_incident` | Update case status, assignment, severity |
| `update_case_ai_summary` | Generate AI investigation summary |
| `update_case_timeline` | Generate visual HTML timeline |

### Alerts (4 tools)
| Tool | Description |
|------|-------------|
| `get_issues` | List and filter security alerts |
| `get_alert_multi_events` | Get detailed alert event data |
| `get_contributing_events` | Get correlation alert events |
| `update_issue` | Update alert severity/status |

### Threat Hunting (1 tool)
| Tool | Description |
|------|-------------|
| `run_xql_query` | Execute XQL queries for threat hunting |

### ITDR (2 tools)
| Tool | Description |
|------|-------------|
| `list_risky_users` | List high-risk user accounts |
| `list_risky_hosts` | List high-risk endpoints |

### Endpoints & Assets (3 tools)
| Tool | Description |
|------|-------------|
| `get_endpoints` | Get endpoint inventory and details |
| `get_assets` | Get asset inventory |
| `get_assessment_profile_results` | Get security assessments |

### Response Actions (6 tools)
| Tool | Description |
|------|-------------|
| `isolate_endpoint` | Isolate endpoint from network |
| `unisolate_endpoint` | Restore endpoint connectivity |
| `scan_endpoint` | Initiate malware scan |
| `abort_scan` | Cancel running scan |
| `terminate_process` | Kill process by name |
| `terminate_causality` | Kill entire process tree |

### File Operations (5 tools)
| Tool | Description |
|------|-------------|
| `quarantine_files` | Quarantine suspicious files |
| `restore_file` | Restore quarantined files |
| `get_quarantine_status` | Check quarantine status |
| `retrieve_files` | Retrieve files from endpoint |
| `get_file_retrieval_details` | Get file download URL |

### Scripts (6 tools)
| Tool | Description |
|------|-------------|
| `run_script` | Execute pre-registered scripts |
| `get_scripts` | List available scripts |
| `get_script_metadata` | Get script parameters |
| `get_script_execution_status` | Monitor script progress |
| `get_script_execution_results` | Get script output |
| `run_snippet_code_script` | Execute ad-hoc Python code |

### IOC Management (2 tools)
| Tool | Description |
|------|-------------|
| `insert_indicators_json` | Add IOCs via JSON |
| `insert_indicators_csv` | Add IOCs via CSV |

### War Room (2 tools)
| Tool | Description |
|------|-------------|
| `add_war_room_entry` | Add notes/commands to War Room |
| `get_war_room_entries` | Get War Room history |

### XSOAR & Enrichment (5 tools)
| Tool | Description |
|------|-------------|
| `run_xsoar_automation` | Execute any XSOAR command |
| `enrich_ip_address` | IP reputation lookup |
| `enrich_domain` | Domain reputation lookup |
| `enrich_file_hash` | File hash reputation |
| `enrich_url` | URL reputation lookup |

### Monitoring (1 tool)
| Tool | Description |
|------|-------------|
| `get_action_status` | Check response action status |

---

## Troubleshooting

### Common Issues

#### "Connection refused" error
- Verify the CORTEX_MCP_PAPI_URL is correct
- Check firewall rules allow outbound HTTPS
- Ensure the API endpoint is accessible

#### "401 Unauthorized" error
- Verify API key and API key ID are correct
- Check API key has not expired
- Ensure API key has required permissions

#### "405 Method Not Allowed" error
- This usually indicates an incorrect API endpoint
- Check the tool is using the correct HTTP method (POST/GET)

#### Tools not appearing in Claude
- Restart the MCP server
- Check the configuration file syntax
- Verify Python path is correct
- Check logs at `cortex-mcp.log`

#### "ITDR not configured" error
- The `list_risky_users` and `list_risky_hosts` tools require ITDR module
- These tools will fail gracefully if ITDR is not enabled

#### Enrichment tools failing
- `enrich_file_hash` and `enrich_url` require VirusTotal/WildFire integrations
- Install required integrations in XSOAR or use `run_xsoar_automation` directly

### Logs

Check the log file for detailed error messages:
```bash
tail -f cortex-mcp.log
```

### Testing Connection

Test your API credentials:
```bash
curl -X POST "https://api-{tenant}.xdr.{region}.paloaltonetworks.com/public_api/v1/incidents/get_incidents/" \
  -H "x-xdr-auth-id: {your_api_key_id}" \
  -H "Authorization: {your_api_key}" \
  -H "Content-Type: application/json" \
  -d '{"request_data": {}}'
```

---

## Support

- **Documentation**: https://docs-cortex.paloaltonetworks.com
- **API Reference**: https://cortex-panw.stoplight.io
- **Issues**: https://github.com/PaloAltoNetworks/cortex-mcp/issues

---

*Last Updated: 2025-11-28*
*Version: 1.0.0*
*Tools Count: 41*
