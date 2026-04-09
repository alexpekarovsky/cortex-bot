# Cortex Bot v2.0 — Implementation Plan

**Platform**: macOS only
**License**: Apache 2.0
**No passwords on disk** — macOS Keychain via `security` CLI

---

## Project Structure

```
cortex_bot/                              # v2.0 source code
├── src/cortex_mcp/                      # Python package (PyPI: cortex-mcp)
│   ├── __init__.py                      # __version__
│   ├── __main__.py                      # python -m cortex_mcp
│   ├── cli.py                           # click CLI: configure, install, start, doctor
│   ├── server.py                        # FastMCP server + lifespan + middleware
│   ├── config.py                        # pydantic-settings
│   │
│   ├── core/
│   │   ├── client.py                    # XSIAM httpx async client (singleton, HTTP/2, pool)
│   │   ├── credentials.py              # macOS Keychain (security CLI) + env fallback
│   │   ├── cache.py                     # TTLCache for read-only endpoints
│   │   ├── circuit_breaker.py           # 5 fails → open → 30s → half-open → close
│   │   └── response.py                 # Field stripping + LLM truncation (80K chars)
│   │
│   ├── security/
│   │   ├── middleware.py                # FastMCP Middleware: audit + perms + rate limit
│   │   ├── permissions.py              # Tool tiers (READ/WRITE/DESTRUCTIVE/SDK)
│   │   ├── rate_limiter.py             # Token bucket per-tier
│   │   ├── audit.py                     # JSONL structured audit log
│   │   ├── log_scrubber.py             # Credential scrubbing in all logs
│   │   └── input_validation.py         # XQL injection, path traversal, ID format
│   │
│   ├── tools/                           # All MCP tools by category
│   │   ├── __init__.py                  # Auto-discover and register all
│   │   ├── cases.py                     # get_cases, get_incident_extra_data, update_incident,
│   │   │                                #   update_case_ai_summary, update_case_timeline
│   │   ├── issues.py                    # get_issues, create_issue, update_issue,
│   │   │                                #   get_alert_multi_events, get_contributing_events
│   │   ├── endpoints.py                 # get_endpoints, get_filtered_endpoints
│   │   ├── response_actions.py          # isolate, unisolate, scan, abort, terminate_process,
│   │   │                                #   terminate_causality, get_action_status
│   │   ├── files.py                     # quarantine, restore, retrieve, blocklist, allowlist,
│   │   │                                #   get_quarantine_status, get_file_retrieval_details
│   │   ├── xql.py                       # run_xql_query
│   │   ├── enrichment.py               # enrich_ip, domain, hash, url, run_xsoar_automation
│   │   ├── correlation_rules.py                 # insert_correlation_rule
│   │   ├── scripts.py                   # run_script, snippet, get_scripts, metadata, status, results
│   │   ├── playbooks.py                # create, get, insert, delete, run
│   │   ├── discovery.py                 # list_integrations, get_integration_commands
│   │   ├── widgets.py                   # get, insert, delete
│   │   ├── assets.py                    # get_assets, get_asset_by_id, get_vulnerabilities,
│   │   │                                #   get_assessment_profile_results
│   │   ├── risky_entities.py                      # list_risky_users, list_risky_hosts
│   │   ├── war_room.py                  # add/get war_room_entries
│   │   ├── indicators.py               # insert_indicators_json, insert_indicators_csv
│   │   ├── tenant.py                    # get_tenant_info
│   │   ├── sdk.py                       # 9 SDK tools (validate, lint, upload, etc.)
│   │   ├── sdk_base.py                  # uvx runner + credential mapping
│   │   │
│   │   ├── generators/                  # Content generators (local file creation)
│   │   │   ├── dashboards.py            # create_xsiam_dashboard, create_xsiam_report
│   │   │   ├── case_content.py          # create_case_field, create_case_layout, layout_rule
│   │   │   ├── data_rules.py            # parsing_rule, modeling_rule, assets_modeling_rule
│   │   │   ├── agentix.py              # create_agentix_action, create_agentix_agent
│   │   │   └── playbook_builder.py      # create_playbook (YAML generator)
│   │   │
│   │   └── guides/                      # Static text guides
│   │       ├── patterns.py              # pattern_guide, best_practices
│   │       ├── development.py           # long_running, event_collector, feed, scheduled, mirroring, layout
│   │       ├── operations.py            # playbook_operations, building_blocks, xsiam_content_guide
│   │       └── slack.py                 # slack_interactive_workflows_guide
│   │
│
├── tests/
│   ├── conftest.py
│   ├── test_credentials.py
│   ├── test_client.py
│   ├── test_middleware.py
│   ├── test_permissions.py
│   └── test_tools/
│
├── pyproject.toml
└── .github/workflows/
    ├── ci.yml
    └── publish.yml
```

---

## Phase 1 — MVP (28 hours / ~14 hrs with Claude Code / 3 days)

### Checklist

- [ ] `pyproject.toml` — hatchling, dependencies (mcp[cli], httpx, pydantic, pydantic-settings, click, cachetools, tenacity, pyyaml)
- [ ] `src/cortex_mcp/__init__.py` — `__version__ = "2.0.0"`
- [ ] `src/cortex_mcp/__main__.py` — `python -m cortex_mcp`
- [ ] `src/cortex_mcp/cli.py` — click: `configure`, `start`, `version`
- [ ] `src/cortex_mcp/core/credentials.py` — dedicated keychain (`~/.cortex-bot/cortex-bot.keychain-db`), SecretStr, keychain ONLY (no env vars for secrets)
- [ ] `cortex-mcp configure` — interactive prompt, create dedicated keychain, store creds, test connectivity
- [ ] `src/cortex_mcp/core/client.py` — httpx singleton, connection pool, HTTP/2, retry (tenacity)
- [ ] `src/cortex_mcp/server.py` — FastMCP, lifespan, yield client/creds
- [ ] `src/cortex_mcp/security/audit.py` — JSONL structured log
- [ ] `src/cortex_mcp/security/log_scrubber.py` — credential scrubbing filter
- [ ] Migrate 15 core tools: cases, issues, endpoints, XQL, enrichment
- [ ] `src/cortex_mcp/tools/__init__.py` — auto-register
- [ ] Manual test: `cortex-mcp start` → 15 tools working

### Key design decisions
- No `.env` file — dedicated keychain for secrets, env vars only for settings (tiers, log level)
- No `keyring` library — macOS `security` CLI directly (subprocess)
- **Dedicated keychain** (`~/.cortex-bot/cortex-bot.keychain-db`) — isolated from login keychain
- Keychain password stored in login keychain under ACL (only cortex-mcp can read)
- No cross-platform — macOS only
- httpx singleton created in lifespan, shared via FastMCP context
- Tools get client from context: `ctx.request_context.lifespan_context["client"]`

---

## Phase 2 — Full Tool Coverage (36 hours / ~14 hrs with Claude Code / 3 days)

### Checklist

- [ ] Migrate remaining 75 tools from `custom_components/`
- [ ] `src/cortex_mcp/core/response.py` — strip low-value fields, truncate to 80K chars
- [ ] Add missing tools: get_indicators, get_correlation_rules, get_audit_logs, xql_streaming
- [ ] `cortex-mcp install --claude` — write `.claude/settings.local.json`
- [ ] `cortex-mcp install --gemini` — write `~/.gemini/settings.json`
- [ ] `cortex-mcp install --cursor` — write `.cursor/mcp.json`
- [ ] Full wet test: all 90+ tools on live tenant

### Migration pattern (search-and-replace)
```python
# v1.0 pattern:
fetcher = await get_fetcher(ctx)
resp = await fetcher.send_request(path, method="POST", data=payload)
return create_response(data=resp)

# v2.0 pattern:
client = ctx.request_context.lifespan_context["client"]
return await client.post(path, json=payload)
```

---

## Phase 3 — Security Hardening (26 hours / ~8 hrs with Claude Code / 1-2 days)

### Checklist

- [ ] `security/middleware.py` — FastMCP Middleware with on_call_tool hook
- [ ] `security/permissions.py` — ToolTier enum (READ/WRITE/DESTRUCTIVE/SDK), tier map, blocklist/allowlist
- [ ] `security/rate_limiter.py` — token bucket: READ 60/min, WRITE 20/min, DESTRUCTIVE 5/min
- [ ] `security/input_validation.py` — XQL injection, path traversal, endpoint ID format
- [ ] `core/circuit_breaker.py` — 5 failures → open → 30s → half-open → close
- [ ] `core/cache.py` — TTLCache: integrations 10min, endpoints 2min, tenant_info 30min
- [ ] `cortex-mcp doctor` — check keychain, test API, verify tools, check audit log
- [ ] Test: middleware blocks disabled tools, rate limits work, audit entries written

### Env vars for control
```
CORTEX_MCP_ENABLED_TIERS=READ,WRITE          # default (no DESTRUCTIVE)
CORTEX_MCP_ENABLE_DESTRUCTIVE=false           # shortcut
CORTEX_MCP_TOOL_BLOCKLIST=                    # block specific tools
CORTEX_MCP_TOOL_ALLOWLIST=                    # if set, ONLY these tools
```

---

## Phase 4 — Production Ready (40 hours / ~14 hrs with Claude Code / 3 days)

### Checklist

- [ ] HTTP transport — FastMCP streamable-http, bind 127.0.0.1
- [ ] `auth_provider.py` — TokenVerifier for HTTP transport, bearer token
- [ ] `.github/workflows/ci.yml` — ruff lint + pytest on macOS runner
- [ ] `.github/workflows/publish.yml` — PyPI trusted publishing on tag
- [ ] Test suite: conftest, mock XSIAM, test credentials, test permissions, test middleware
- [ ] PyPI: hatch build, test on TestPyPI, publish
- [ ] README: install, usage, security, tool reference
- [ ] MCP Registry listing
- [ ] SDK tools: port demisto-sdk wrapper via uvx
- [ ] Final e2e: `uvx cortex-mcp configure → start → run all tools`

---

## Dependencies (no keyring — macOS security CLI instead)

```toml
dependencies = [
    "mcp[cli]>=1.0",
    "httpx[http2]>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "cachetools>=5.3",
    "tenacity>=8.2",
    "click>=8.0",
]
```

No keyring. No aiohttp. No requests. No fastapi. No uvicorn.

---

## Credential Flow — Dedicated Keychain

Cortex Bot uses its own isolated keychain (`~/.cortex-bot/cortex-bot.keychain-db`),
**not** the login keychain. This prevents a compromised tool or dependency from
accessing iCloud, SSH, browser passwords, or anything else in the login keychain.

### Keychain Architecture

```
Login Keychain (macOS default)
  └── "cortex-bot-keychain-password"     ← password to unlock our keychain (ACL: cortex-mcp only)

~/.cortex-bot/cortex-bot.keychain-db     ← dedicated keychain (encrypted, isolated)
  ├── cortex-mcp/api_url                 ← tenant URL
  ├── cortex-mcp/api_key                 ← API key
  └── cortex-mcp/api_key_id             ← key ID
```

### CLI Flow

```
cortex-mcp configure
  → prompt for URL, API Key ID, API Key
  → create dedicated keychain: security create-keychain (password piped via stdin) ~/.cortex-bot/cortex-bot.keychain-db
  → store keychain password in login keychain: security add-generic-password -a cortex-bot -s cortex-bot-keychain-password -w <pw> -U
  → unlock dedicated keychain: security unlock-keychain (password piped via stdin) ~/.cortex-bot/cortex-bot.keychain-db
  → store credentials: security add-generic-password -a cortex-bot -s <key> -w <value> -U ~/.cortex-bot/cortex-bot.keychain-db
  → test connectivity (httpx POST to /public_api/v1/system/get_tenant_info)
  → lock keychain: security lock-keychain ~/.cortex-bot/cortex-bot.keychain-db
  → print "Credentials stored in dedicated keychain. Run 'cortex-mcp install --claude' to register."

cortex-mcp start
  → read keychain password from login keychain: security find-generic-password -a cortex-bot -s cortex-bot-keychain-password -w
  → unlock dedicated keychain: security unlock-keychain (password piped via stdin) ~/.cortex-bot/cortex-bot.keychain-db
  → read credentials: security find-generic-password -a cortex-bot -s <key> -w ~/.cortex-bot/cortex-bot.keychain-db
  → if keychain not found: error "Run cortex-mcp configure first"
  → create httpx.AsyncClient with creds
  → start FastMCP server (stdio)
  → on shutdown: security lock-keychain ~/.cortex-bot/cortex-bot.keychain-db
```

### Why a dedicated keychain?

| | Login keychain | Dedicated keychain |
|--|----------------|-------------------|
| Blast radius | ALL your passwords (iCloud, SSH, browser, WiFi) | Only XSIAM credentials |
| If compromised | Everything leaks | Only SOC API keys leak |
| Access control | Any app can read (with prompt) | Only cortex-mcp can unlock |
| Cleanup | Must find and delete individual entries | `rm ~/.cortex-bot/cortex-bot.keychain-db` |

### Implementation

```python
# core/credentials.py
KEYCHAIN_PATH = Path.home() / ".cortex-bot" / "cortex-bot.keychain-db"
SERVICE = "cortex-bot"
KEYCHAIN_PW_KEY = "cortex-bot-keychain-password"

def _unlock_keychain(self):
    """Get keychain password from login keychain, unlock dedicated keychain."""
    pw = subprocess.run(
        ["security", "find-generic-password", "-a", SERVICE,
         "-s", KEYCHAIN_PW_KEY, "-w"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(
        ["security", "unlock-keychain", str(KEYCHAIN_PATH)],
        input=pw + "\n", capture_output=True, text=True, check=True,
        check=True
    )

def _read(self, key: str) -> str:  # keychain already unlocked in __init__
    """Read from dedicated keychain."""
    self._unlock_keychain()
    return subprocess.run(
        ["security", "find-generic-password", "-a", SERVICE,
         "-s", key, "-w", str(KEYCHAIN_PATH)],
        capture_output=True, text=True, check=True
    ).stdout.strip()

def _write(self, key: str, value: str):
    """Write to dedicated keychain."""
    self._unlock_keychain()
    subprocess.run(
        ["security", "add-generic-password", "-a", SERVICE,
         "-s", key, "-w", value, "-U", str(KEYCHAIN_PATH)],
        check=True
    )
```

---

## What we're removing (v1.0 → v2.0)

| Remove | Why |
|--------|-----|
| PANW `src/` dependency | We have our own server |
| `client_patch.py` (DictResponse) | No PANW PAPIClient to patch |
| `get_issues_fix.py` | Correct API path from start |
| `.env` / `.env.example` | Keychain, no disk secrets |
| `BaseModule` pattern | FastMCP `@mcp.tool()` or `register(mcp, client)` |
| `create_response()` wrapper | Return dicts directly |
| `openapi/` YAML files | Already migrated to Python in v1.0 |
| 4 `.bak` files in PANW builtins | No builtins to work around |
| Symlink `src/usecase/custom_components/` | No PANW server |
