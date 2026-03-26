# Cortex Bot — Custom MCP Tools for Cortex XSIAM

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**84 custom MCP tools** that extend the official [Palo Alto Networks Cortex MCP Server](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) (6 base tools) to **90 total tools**. All tools are **pure Python** — no OpenAPI YAML dependencies.

Works with any MCP-compatible AI coding agent: **Claude Code**, **Gemini CLI**, **OpenAI Codex**, or any other MCP client.

> **Prerequisites:** You must install the [official Cortex MCP Server](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) first. This repo adds custom tools on top of it.

---

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/alexpekarovsky/cortex-bot.git

# 2. Copy custom tools into your PANW MCP server installation
cp -r cortex-bot/custom_components/* /path/to/cortex-mcp/src/usecase/custom_components/

# 3. Install dependencies (in PANW MCP server directory)
cd /path/to/cortex-mcp
source venv/bin/activate
poetry install

# 4. Install uv + demisto-sdk (required for SDK tools)
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx demisto-sdk --version   # verifies it works

# 5. Create content repo (required for SDK tools)
mkdir -p ~/content/Packs

# 6. Configure credentials in .env (same keys used by all tools including SDK)
cp .env.example .env
# Edit .env with your XSIAM API URL, key, and key ID

# 7. Restart MCP server — in your AI agent, reconnect to see 90 tools
```

For detailed step-by-step instructions, see [INSTALL.md](INSTALL.md).

---

## What You Get

### Tool Categories (90 total)

| Category | Tools | What it does |
|----------|-------|-------------|
| **Case Management** | 5 | Investigate cases, generate AI summaries, create visual timelines |
| **Issue Management** | 5 | Triage alerts, get forensic event data, create investigation workspaces |
| **Response Actions** | 6 | Isolate endpoints, terminate processes, scan for malware |
| **File Operations** | 7 | Quarantine, restore, blocklist, allowlist, retrieve files |
| **Threat Hunting** | 6 | Run XQL queries, enrich IPs/domains/files/URLs, run XSOAR automations |
| **Detection Rules** | 1 | Create XQL-based correlation rules |
| **Script Execution** | 6 | Run scripts and Python snippets on endpoints |
| **XSOAR SDK** | 9 | Validate, lint, upload, download integrations and scripts |
| **Development Guides** | 11 | Pattern guides, building blocks, playbook generation |
| **Content Generators** | 11 | Dashboards, parsing rules, modeling rules, layouts |
| **Playbook Management** | 4 | Get, insert, delete, run playbooks via API |
| **Integration Discovery** | 2 | List integrations and commands in your XSIAM instance |
| **Widget Management** | 3 | Create, list, delete XQL dashboard widgets |
| **Assets & Risk** | 8 | Endpoints, assets, vulnerabilities, risky users/hosts |
| **War Room & IOC** | 4 | War Room entries, IOC insertion (JSON/CSV) |
| **Other** | 1 | test_all_tools, get_action_status, get_tenant_info, Slack guide |

### Example Prompts

| You say | What happens |
|---------|-------------|
| "Show me all critical cases from the last 24 hours" | Lists cases with alert counts and affected hosts |
| "Investigate case 100 and generate an AI summary" | Gets full forensics, creates investigation report |
| "Hunt for PowerShell on domain controllers" | Runs XQL query, shows process trees |
| "Is IP 45.33.32.156 malicious?" | Enriches via threat intel, shows reputation |
| "Isolate endpoint Server-DC-1" | Isolates from network, monitors status |
| "Create an SSH brute force detection rule" | Creates XQL correlation rule |
| "Create a ServiceNow integration" | Scaffolds code, writes Python, uploads to XSIAM |
| "Create a playbook that checks if NGFW sessions ended and closes the issue. Upload it, run it on a test issue, fix any errors, and keep going until it completes 100%." | Creates playbook YAML, uploads to XSIAM, creates test issue, opens War Room, runs playbook, reads errors from War Room, fixes YAML, re-uploads, retests — iterates until fully working |

### Complete Tool Reference

<details>
<summary><b>Case Management (5 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_cases` | "Show me all critical cases from the last 24 hours" |
| `get_incident_extra_data` | "Give me full details on case 474 including all alerts" |
| `update_incident` | "Assign case 474 to analyst@company.com" |
| `update_case_ai_summary` | "Generate an AI investigation summary for case 474" |
| `update_case_timeline` | "Create a visual timeline for case 474" |

</details>

<details>
<summary><b>Issue Management (5 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_issues` | "Show me all new high severity alerts" |
| `create_issue` | "Create a scratch pad issue for IP investigation" |
| `update_issue` | "Mark alert 11222 as resolved false positive" |
| `get_alert_multi_events` | "Show me the raw events that triggered alert 11223" |
| `get_contributing_events` | "Get contributing events for alert 10781" |

</details>

<details>
<summary><b>Response Actions (7 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `isolate_endpoint` | "Isolate the Gaming endpoint from the network" |
| `unisolate_endpoint` | "Restore network access to Gaming" |
| `scan_endpoint` | "Run a malware scan on Gaming" |
| `abort_scan` | "Cancel the running scan on Gaming" |
| `terminate_process` | "Kill notepad.exe on the Gaming endpoint" |
| `terminate_causality` | "Terminate the entire process tree for causality abc123" |
| `get_action_status` | "Check the status of action 149" |

</details>

<details>
<summary><b>File Operations (7 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `quarantine_files` | "Quarantine C:\malware.exe on the Gaming endpoint" |
| `restore_file` | "Restore the quarantined file on Gaming" |
| `retrieve_files` | "Pull the hosts file from Gaming for analysis" |
| `get_file_retrieval_details` | "Get download link for file retrieval action 155" |
| `get_quarantine_status` | "Check if malware.exe is quarantined on Gaming" |
| `blocklist_files` | "Block hash e3b0c44... across all endpoints" |
| `allowlist_files` | "Allowlist our custom app hash a1b2c3..." |

</details>

<details>
<summary><b>Threat Hunting (6 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `run_xql_query` | "Hunt for PowerShell with bypass flag in the last 7 days" |
| `enrich_ip_address` | "Is 45.33.32.156 malicious?" |
| `enrich_domain` | "Check reputation of suspicious-domain.com" |
| `enrich_file_hash` | "Look up file hash d7a8fbb307... in threat intel" |
| `enrich_url` | "Is https://phishing-site.com/login safe?" |
| `run_xsoar_automation` | "Run !GetInstances to see all configured integrations" |

</details>

<details>
<summary><b>Detection Rules (1 tool)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `insert_correlation_rule` | "Create a rule to detect SSH brute force over 10 failed logins" |

</details>

<details>
<summary><b>Script Execution (6 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `run_script` | "Run process_get on Gaming to list running processes" |
| `run_snippet_code_script` | "Run `import platform; print(platform.version())` on Gaming" |
| `get_scripts` | "List all available scripts I can run on endpoints" |
| `get_script_metadata` | "Show me the parameters for the process_get script" |
| `get_script_execution_status` | "Is script action 153 still running?" |
| `get_script_execution_results` | "Show me the output from script action 153" |

</details>

<details>
<summary><b>XSOAR SDK (9 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `sdk_validate` | "Validate the structure of Packs/MyIntegration" |
| `sdk_lint` | "Lint the Python code in Packs/MyIntegration" |
| `sdk_upload` | "Upload Packs/MyIntegration to XSIAM" |
| `sdk_download` | "Download the CommonScripts pack from XSIAM" |
| `sdk_run` | "Run the ip command with ip=8.8.8.8 via SDK" |
| `sdk_run_playbook` | "Trigger the Gaming Endpoint Check playbook via SDK" |
| `sdk_generate_docs` | "Generate README docs for my integration" |
| `sdk_split` | "Split a unified YAML into directory structure" |
| `sdk_unify` | "Unify Packs/MyPack into a single deployable package" |

</details>

<details>
<summary><b>Development Guides (12 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_xsoar_pattern_guide` | "What integration pattern should I use for a webhook listener?" |
| `get_xsoar_long_running_guide` | "How do I build a long-running monitoring integration?" |
| `get_xsoar_event_collector_guide` | "How do I build a ServiceNow event collector?" |
| `get_xsoar_scheduled_commands_guide` | "How do I implement async polling for sandbox analysis?" |
| `get_xsoar_mirroring_guide` | "How do I build bidirectional sync with Jira?" |
| `get_xsoar_feed_guide` | "How do I build a TAXII threat feed integration?" |
| `get_xsoar_layout_guide` | "How do I create a custom alert layout with buttons?" |
| `get_xsoar_playbook_operations_guide` | "How do I run a playbook on a specific alert?" |
| `get_xsoar_best_practices` | "What are the threading and state management rules?" |
| `get_playbook_building_blocks` | "Show me building blocks for containment playbooks" |
| `get_slack_interactive_workflows_guide` | "How do I build Slack approval workflows with buttons?" |
| `get_xsiam_content_guide` | "What content types can I create for XSIAM?" |

</details>

<details>
<summary><b>Content Generators (11 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `create_xsiam_dashboard` | "Create a dashboard showing total events by host" |
| `create_xsiam_report` | "Create a weekly alert summary report" |
| `create_case_field` | "Create a singleSelect field called Investigation Priority" |
| `create_case_layout` | "Create a custom case layout for phishing investigations" |
| `create_case_layout_rule` | "Route phishing cases to the phishing layout" |
| `create_parsing_rule` | "Create a parsing rule for our custom app logs" |
| `create_modeling_rule` | "Map parsed logs to the XDM Audit model" |
| `create_assets_modeling_rule` | "Map host inventory to the Assets model" |
| `create_agentix_action` | "Wrap the ip command as an AgentIX action" |
| `create_agentix_agent` | "Create an AI agent that can enrich IPs and domains" |
| `create_playbook` | "Build a playbook that checks NGFW sessions and auto-closes" |

</details>

<details>
<summary><b>Playbook Management (4 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_playbook` | "Download the YAML for the phishing playbook" |
| `insert_playbook` | "Upload my playbook ZIP to XSIAM" |
| `delete_playbook` | "Delete the old test playbook" |
| `run_playbook` | "Run the NGFW Session Check playbook on alert 11223" |

</details>

<details>
<summary><b>Integration Discovery (2 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `list_integrations` | "What integrations are configured in my XSIAM?" |
| `get_integration_commands` | "What commands does Cortex Core - IR support?" |

</details>

<details>
<summary><b>Widget Management (3 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_widgets` | "List all my XQL dashboard widgets" |
| `insert_widgets` | "Create a widget showing alert count by severity" |
| `delete_widgets` | "Delete widget xql_tool_test_123" |

</details>

<details>
<summary><b>Assets & Risk (8 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_endpoints` | "List all my endpoints with their status" |
| `get_filtered_endpoints` | "Show me only connected Windows endpoints" |
| `get_assets` | "List assets in the inventory" |
| `get_asset_by_id` | "Get details for asset ID abc123" |
| `get_vulnerabilities` | "Show me critical CVEs in my environment" |
| `get_assessment_profile_results` | "Show CIS benchmark compliance results" |
| `list_risky_users` | "Who are the riskiest users in my environment?" |
| `list_risky_hosts` | "Which hosts have the highest risk scores?" |

</details>

<details>
<summary><b>War Room & IOC (4 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `add_war_room_entry` | "Add a note to alert 11222: confirmed false positive" |
| `get_war_room_entries` | "Show me the War Room history for alert 11222" |
| `insert_indicators_json` | "Add 10.99.99.99 as a suspicious IOC" |
| `insert_indicators_csv` | "Bulk import IOCs from CSV" |

</details>

<details>
<summary><b>Other (2 tools)</b></summary>

| Tool | Example Prompt |
|------|---------------|
| `get_tenant_info` | "Show me my XSIAM license and expiration dates" |
| `test_all_tools` | "Run the built-in tool connectivity test" |

</details>

---

## Configuration

### Credentials

All tools (including demisto-sdk) use the same three environment variables:

```bash
# .env file in your PANW MCP server directory
CORTEX_MCP_PAPI_URL=https://api-{tenant}.xdr.{region}.paloaltonetworks.com
CORTEX_MCP_PAPI_AUTH_HEADER=your_api_key
CORTEX_MCP_PAPI_AUTH_ID=your_key_id
```

Get these from: **XSIAM > Settings > Configurations > API Keys** (Security Level: Standard, Role: Instance Administrator).

SDK tools automatically map these to `DEMISTO_BASE_URL`, `DEMISTO_API_KEY`, and `XSIAM_AUTH_ID` — no separate SDK credential setup needed.

### MCP Server Setup per AI Agent

**Claude Code** — add to `.claude/settings.local.json` in your project:
```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "python",
      "args": ["/path/to/cortex-mcp/src/main.py"],
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-yourinstance.xdr.us.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "1"
      }
    }
  }
}
```

**Gemini CLI** — add to `~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "python",
      "args": ["/path/to/cortex-mcp/src/main.py"],
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-yourinstance.xdr.us.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "1"
      }
    }
  }
}
```

**Any MCP client** — the server uses stdio transport by default. Point your client to `python /path/to/cortex-mcp/src/main.py` and pass the three env vars above.

### Local LLMs with MCP Support

You can run Cortex Bot with local models instead of cloud APIs. For Apple Silicon Macs (M4 and above recommended), use MLX for best performance.

**Recommended setup:**

| Option | MLX | MCP | Notes |
|--------|-----|-----|-------|
| **LM Studio** | Yes | Yes | Best all-in-one — GUI, MLX backend, built-in MCP server support |
| **Ollama** + **msty** | Metal (partial) | Yes (msty handles MCP) | Easy install, large model library |
| **mlx-lm** + MCP client | Pure MLX | Via client | CLI-based, fastest inference on Apple Silicon |

**Recommended models (MLX quantized, from `mlx-community` on HuggingFace):**

| Model | Size | Min RAM | Best for |
|-------|------|---------|----------|
| `Llama-4-Scout-17B-16E-Instruct-4bit` | ~30GB | 32GB | Best overall capability |
| `Mistral-Large-Instruct-2411-4bit` | ~65GB | 64GB | Best tool/function calling |
| `gemma-3-27b-it-4bit` | ~15GB | 16GB | Best for 16GB Macs |
| `Phi-4-4bit` | ~8GB | 8GB | Lightest, still capable |

**Quick start with LM Studio:**
1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Enable MLX backend in settings
3. Download a model (Gemma 3 27B recommended for most Macs)
4. Enable MCP server, point it to `python /path/to/cortex-mcp/src/main.py` with the credential env vars

**Quick start with mlx-lm:**
```bash
pip install mlx-lm
mlx_lm.server --model mlx-community/gemma-3-27b-it-4bit --port 8080
# Then configure an MCP client to connect to your cortex-mcp server
```

> **Performance note:** MLX runs natively on Apple Silicon unified memory. M4 Pro/Max/Ultra chips with 32GB+ RAM deliver the best local LLM experience. M1/M2 chips work but are significantly slower on larger models.

---

## Demisto SDK (Required for XSOAR Development Tools)

9 tools require `demisto-sdk`: `sdk_validate`, `sdk_lint`, `sdk_upload`, `sdk_download`, `sdk_run`, `sdk_run_playbook`, `sdk_generate_docs`, `sdk_split`, `sdk_unify`. The other 81 tools work without it.

### Why uvx?

The MCP server needs **pydantic 2.x**, but demisto-sdk needs **pydantic 1.x**. They cannot coexist in the same virtualenv. `uvx` runs demisto-sdk in an isolated environment automatically.

### Install

```bash
# 1. Install uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Verify demisto-sdk works through uvx
uvx demisto-sdk --version
# Expected: demisto-sdk 1.x.x

# 3. Create content directory (required)
mkdir -p ~/content/Packs
```

### Credentials

SDK tools automatically use the same XSIAM credentials from your `.env`:
- `CORTEX_MCP_PAPI_URL` → `DEMISTO_BASE_URL`
- `CORTEX_MCP_PAPI_AUTH_HEADER` → `DEMISTO_API_KEY`
- `CORTEX_MCP_PAPI_AUTH_ID` → `XSIAM_AUTH_ID`

No separate SDK credential configuration needed.

### Manual SDK usage (outside MCP)

```bash
# Upload a content pack
uvx demisto-sdk upload -i Packs/MyPack

# Validate content
uvx demisto-sdk validate -i Packs/MyPack

# Create new integration
uvx demisto-sdk init --name MyIntegration --type integration
```

---

## Architecture

```
AI Agent (Claude Code / Gemini / Codex)
  └── MCP Protocol (stdio)
        └── Cortex MCP Server (PANW base + custom tools)
              ├── REST API → Cortex XSIAM (cases, issues, endpoints, XQL)
              └── demisto-sdk (via uvx) → XSOAR content management
```

This repo provides `custom_components/` — you copy them into the PANW server's `src/usecase/custom_components/` directory.

---

## Adding Custom Tools

### Python tool

Create `custom_components/my_tool.py`:

```python
from fastmcp import Context
from usecase.base_module import BaseModule

async def my_custom_tool(ctx: Context, param: str) -> str:
    """Tool description for the AI."""
    return '{"result": "success"}'

class MyModule(BaseModule):
    def register_tools(self):
        self._add_tool(my_custom_tool)
    def register_resources(self):
        pass
```

Restart the MCP server after adding tools.

---

## Project Structure

```
cortex-bot/
├── custom_components/              # All custom MCP tools (this is what you install)
│   ├── client_patch.py             # DictResponse patch for PANW OpenAPI compatibility
│   ├── endpoint_tools.py           # Endpoint: get, isolate, scan, terminate
│   ├── file_tools.py               # File: quarantine, retrieve, status
│   ├── script_tools.py             # Script: run, snippet, metadata, results
│   ├── misc_tools.py               # Widgets, indicators, alert events
│   ├── war_room.py                 # War Room: add/get entries
│   ├── asset_tools.py              # Assets, vulnerabilities, assessment
│   ├── sdk_base.py                 # SDK runner (handles uvx + credential mapping)
│   ├── sdk_tools.py                # 9 XSOAR SDK wrapper tools
│   ├── xql_query.py                # XQL query execution
│   ├── xsiam_content_generator.py  # 11 content generation tools
│   └── ...                         # 39 Python modules total
├── .env.example                    # Credential template
├── INSTALL.md                      # Detailed installation guide
├── push.sh                         # Safe push script (for contributors)
├── LICENSE                         # Apache 2.0
└── README.md                       # This file
```

---

## Safety

| Tool | Risk | Reversible | Notes |
|------|------|-----------|-------|
| `isolate_endpoint` | HIGH | Yes (`unisolate_endpoint`) | Cuts network access |
| `terminate_process` | HIGH | No | Kills process permanently |
| `terminate_causality` | HIGH | No | Kills entire process tree |
| `quarantine_files` | HIGH | Yes (`restore_file`) | Moves files to quarantine |
| `run_script` | HIGH | Depends | Executes on endpoint |

Control with `ENABLE_DESTRUCTIVE_TOOLS=true/false` in `.env`.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| Only 6 tools show (not 90) | Files not copied — verify `ls /path/to/cortex-mcp/src/usecase/custom_components/*.py` shows 39 files, then restart server |
| `401 Unauthorized` | Check `.env` credentials match your XSIAM API key |
| `pydantic` import errors | Don't install demisto-sdk in MCP venv — use `uvx demisto-sdk` |
| SDK tools fail silently | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `FileNotFoundError: Packs` | Create content dir: `mkdir -p ~/content/Packs` |
| Changes not taking effect | MCP server caches code at startup — restart it |
| `ModuleNotFoundError: aiohttp` | Run `poetry install` in MCP server directory |

---

## Contributing

1. Fork this repo
2. Create a feature branch
3. Make your changes in `custom_components/`
4. Open a PR targeting `main`

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

These tools extend the official PANW Cortex MCP Server, which has its own license. The base server is not included in this repository.
