# Installation Guide

## MCP Gateway

The MCP Gateway installs and manages both packages automatically:

1. **Cortex MCP Server** (official PANW) — base MCP server with XSIAM connectivity
2. **Cortex Bot** — 106 community tools that extend the server

### Step 1: Get MCP Gateway access

Connect to the corporate network via Prisma Access. The MCP Gateway is available automatically.

### Step 2: Get your XSIAM API key

1. Log into your XSIAM instance
2. Go to **Settings > Configurations > API Keys**
3. Create a new key with **Security Level: Standard** and **Role: Instance Administrator**
4. Save three values: **API Key** (long string), **Key ID** (number), and your **tenant URL**

Your tenant URL format: `https://api-{tenant}.xdr.{region}.paloaltonetworks.com`

### Step 3: Connect your AI agent

#### Claude Code

```bash
claude mcp add cortex-xsiam -- cortex-bot
```

Or install manually:

```bash
# Clone this repo
git clone https://github.com/alexpekarovsky/cortex-bot.git

# Find your PANW MCP server installation
find ~ -name "main.py" -path "*/cortex*/src/main.py" 2>/dev/null
# Typical locations: ~/cortex-mcp, ~/.local/share/cortex-mcp

# Copy custom tools into it
cp -r cortex-bot/custom_components/* /path/to/cortex-mcp/src/usecase/custom_components/

# Verify: should show 43 Python files
ls /path/to/cortex-mcp/src/usecase/custom_components/*.py | wc -l
```

Or add to your MCP settings:

```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "cortex-bot",
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-yourinstance.xdr.us.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "1"
      }
    }
  }
}
```

Then run `/mcp` to connect.

#### Gemini CLI

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "cortex-xsiam": {
      "command": "cortex-bot",
      "env": {
        "CORTEX_MCP_PAPI_URL": "https://api-yourinstance.xdr.us.paloaltonetworks.com",
        "CORTEX_MCP_PAPI_AUTH_HEADER": "your_api_key",
        "CORTEX_MCP_PAPI_AUTH_ID": "1"
      }
    }
  }
}
```

#### Any MCP client

Use stdio transport with the `cortex-bot` command and the three `CORTEX_MCP_PAPI_*` environment variables.

### Step 4: Verify

After connecting your AI agent, you should see **112 tools** (2 base + 110 custom).

Test with these prompts:

```
"Show me all my XSIAM cases"
"Run XQL: dataset = xdr_data | limit 5"
"List all endpoints"
"Enrich IP 8.8.8.8"
```

---

## Optional: XSOAR SDK tools

9 of the 106 tools wrap `demisto-sdk` for XSOAR content development. These are optional.

```bash
# Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify demisto-sdk works through uvx
uvx demisto-sdk --version

# Create content directory
mkdir -p ~/content/Packs
```

If you skip this, the other 97 tools work fine.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| MCP Gateway not connecting | Check Prisma Access VPN is active |
| Only base tools visible | Cortex Bot package not approved in gateway — contact gateway team |
| Only 6 tools visible | Custom files not copied — check `ls src/usecase/custom_components/*.py` shows 43 files |
| `401 Unauthorized` | Wrong API key — verify in `.env` or gateway config |
| `ModuleNotFoundError: aiohttp` | Run `pip install aiohttp` in the MCP server venv, then restart |
| Import/pydantic errors | Don't `pip install demisto-sdk` in MCP venv — use `uvx` |
| `uvx: command not found` | Add to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc` |
| SDK tools fail in Docker | Docker image must include `uv` — rebuild with v1.2.0+ Dockerfile |
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

Once connected, try:

- "Investigate case 123 and create an AI summary"
- "Hunt for PowerShell activity on domain controllers"
- "Create a phishing investigation playbook"
- "Build a custom integration for our ticketing system"

See [README.md](README.md) for the full tool reference.
