# Installation Guide

Step-by-step guide to add Cortex Bot community tools to your existing Palo Alto Networks Cortex MCP Server.

**Requires:** The official [Palo Alto Networks Cortex MCP Server](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) installed and working.

**Works with:** Claude Code, Gemini CLI, OpenAI Codex, or any MCP-compatible AI agent.

---

## Prerequisites

| Requirement | Check | Install |
|-------------|-------|---------|
| Official Palo Alto Networks Cortex MCP Server | Your AI agent shows base tools | [Palo Alto Networks docs](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) |
| Python 3.12+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| Git | `git --version` | [git-scm.com](https://git-scm.com/) |
| uv (for demisto-sdk) | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| XSIAM API key | See below | XSIAM > Settings > API Keys |

### Get your XSIAM API key

1. Log into your XSIAM instance
2. Go to **Settings > Configurations > API Keys**
3. Create a new key with **Security Level: Standard** and **Role: Instance Administrator**
4. Save three values: **API Key** (long string), **Key ID** (number), and your **tenant URL**

Your tenant URL format: `https://api-{tenant}.xdr.{region}.paloaltonetworks.com`

---

## Step 1: Clone and copy

```bash
# Clone this repo
git clone https://github.com/alexpekarovsky/cortex-bot.git

# Find your PANW MCP server installation
find ~ -name "main.py" -path "*/cortex*/src/main.py" 2>/dev/null
# Typical locations: ~/cortex-mcp, ~/.local/share/cortex-mcp

# Copy custom tools into it
cp -r cortex-bot/custom_components/* /path/to/cortex-mcp/src/usecase/custom_components/

# Verify: should show 42 Python files
ls /path/to/cortex-mcp/src/usecase/custom_components/*.py | wc -l
```

If `src/usecase/custom_components/` doesn't exist, create it first:
```bash
mkdir -p /path/to/cortex-mcp/src/usecase/custom_components
```

## Step 2: Install dependencies

```bash
cd /path/to/cortex-mcp
source venv/bin/activate
poetry install
```

This installs `aiohttp` and other dependencies required by the custom tools.

## Step 3: Install uv and demisto-sdk

The XSOAR SDK tools (`sdk_upload`, `sdk_validate`, etc.) need `demisto-sdk`, which conflicts with the MCP server's pydantic version. `uvx` solves this by running it in isolation.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify demisto-sdk works through uvx
uvx demisto-sdk --version
# Expected: demisto-sdk 1.x.x

# Create content directory (required for SDK tools)
mkdir -p ~/content/Packs
```

If you skip this step, 9 SDK tools won't work. The other 97 tools are unaffected.

## Step 4: Configure credentials

```bash
# In your PANW MCP server directory
cp .env.example .env
```

Edit `.env` with your three XSIAM values:

```bash
CORTEX_MCP_PAPI_URL=https://api-yourinstance.xdr.us.paloaltonetworks.com
CORTEX_MCP_PAPI_AUTH_HEADER=your_api_key_here
CORTEX_MCP_PAPI_AUTH_ID=1
```

**These same credentials are used by all tools**, including the demisto-sdk tools. The SDK automatically maps them:
- `CORTEX_MCP_PAPI_URL` → `DEMISTO_BASE_URL`
- `CORTEX_MCP_PAPI_AUTH_HEADER` → `DEMISTO_API_KEY`
- `CORTEX_MCP_PAPI_AUTH_ID` → `XSIAM_AUTH_ID`

No separate SDK credential setup is needed.

## Step 5: Configure your AI agent

### Claude Code

Add to `.claude/settings.local.json` (project-level) or `~/.claude/settings.json` (global):

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

Then in Claude Code, run `/mcp` to connect.

### Gemini CLI

Add to `~/.gemini/settings.json`:

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

### Any MCP client

The server uses **stdio transport** by default. Configure your client to run:
```
python /path/to/cortex-mcp/src/main.py
```
With the three `CORTEX_MCP_PAPI_*` environment variables set.

## Step 6: Verify

After connecting your AI agent, you should see **111 tools** (2 base + 109 custom).

Test with these prompts:

```
"Show me all my XSIAM cases"           → Tests case management + API connection
"Run XQL: dataset = xdr_data | limit 5" → Tests XQL execution
"List all endpoints"                     → Tests endpoint access
"Enrich IP 8.8.8.8"                     → Tests threat intel enrichment
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Only 6 tools visible | Custom files not copied — check `ls src/usecase/custom_components/*.py` shows 42 files |
| `401 Unauthorized` | Wrong API key — verify in `.env` |
| `ModuleNotFoundError: aiohttp` | Run `pip install aiohttp` in the MCP server venv, then restart |
| Import/pydantic errors | Don't `pip install demisto-sdk` in MCP venv — use `uvx` |
| `uvx: command not found` | Add to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc` |
| SDK tools fail | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `FileNotFoundError: Packs` | `mkdir -p ~/content/Packs` |
| `FileNotFoundError: README.md` (sdk_upload) | Create: `echo "# Pack" > ~/content/Packs/MyPack/README.md && touch ~/content/Packs/MyPack/.pack-ignore` |
| `Unable to find Repository` (sdk_upload) | Non-fatal warning — upload still works, safe to ignore |
| `Missing script Builtin\|\|\|setAlert` | Some tenants need `setIncident` instead — test both |
| `summarize` invalid XQL syntax | XQL has no `summarize` — use `comp count()` or `dedup` instead |
| Code changes not loading | MCP server caches at startup — restart it |

### Check credentials

```bash
# Verify .env is correct
grep CORTEX_MCP_PAPI /path/to/cortex-mcp/.env

# Check for env var overrides (higher priority than .env)
printenv | grep CORTEX_MCP_PAPI

# Test API directly
curl -s -X POST "$CORTEX_MCP_PAPI_URL/public_api/v1/incidents/get_incidents" \
  -H "Authorization: $CORTEX_MCP_PAPI_AUTH_HEADER" \
  -H "x-xdr-auth-id: $CORTEX_MCP_PAPI_AUTH_ID" \
  -H "Content-Type: application/json" \
  -d '{"request_data": {}}' | head -100
```

---

## What's next

Once installed, try:

- "Investigate case 123 and create an AI summary"
- "Hunt for PowerShell activity on domain controllers"
- "Create a phishing investigation playbook"
- "Build a custom integration for our ticketing system"

See [README.md](README.md) for the full tool reference.
