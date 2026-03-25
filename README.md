# Cortex Bot — Custom MCP Tools for Cortex XSIAM

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**84 custom MCP tools** that extend the official [Palo Alto Networks Cortex MCP Server](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) (6 base tools) to **90 total tools**.

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
| **XSOAR SDK** | 10 | Create, validate, lint, upload integrations and scripts |
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

10 tools require `demisto-sdk`: `sdk_init`, `sdk_validate`, `sdk_lint`, `sdk_upload`, `sdk_download`, `sdk_run`, `sdk_run_playbook`, `sdk_generate_docs`, `sdk_split`, `sdk_unify`. The other 80 tools work without it.

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

### OpenAPI tool

Create `custom_components/openapi/my_tool.yaml`:

```yaml
openapi: 3.0.0
info:
  title: My Tool
  version: 1.0.0
paths:
  /public_api/v1/your/endpoint:
    post:
      operationId: my_tool
      summary: What this tool does
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                param1:
                  type: string
              required: [param1]
      responses:
        '200':
          description: Success
```

Restart the MCP server after adding tools.

---

## Project Structure

```
cortex-bot/
├── custom_components/          # All custom MCP tools (this is what you install)
│   ├── openapi/                # 25+ OpenAPI YAML tool definitions
│   ├── sdk_base.py             # SDK runner (handles uvx + credential mapping)
│   ├── sdk_tools.py            # 10 XSOAR SDK wrapper tools
│   ├── xql_query.py            # XQL query execution
│   ├── xsiam_content_generator.py  # 11 content generation tools
│   └── ...                     # 28 Python modules total
├── .env.example                # Credential template
├── INSTALL.md                  # Detailed installation guide
├── push.sh                     # Safe push script (for contributors)
├── LICENSE                     # Apache 2.0
└── README.md                   # This file
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
| Only 6 tools show (not 90) | Files not copied — verify `ls /path/to/cortex-mcp/src/usecase/custom_components/*.py` shows 28+ files, then restart server |
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
