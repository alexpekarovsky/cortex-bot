# Cortex Bot v2.0 — Standalone MCP Server

This folder contains planning and source code for Cortex Bot v2.0 — a standalone MCP server with no PANW dependency.

**Status**: Planning phase. v1.0 (PANW-based) is tagged and released.

## Architecture

See `docs/ARCHITECTURE.md` for the full design spec.

## Key Differences from v1.0

| | v1.0 | v2.0 |
|--|------|------|
| Server | PANW MCP Server (dependency) | Our own FastMCP server |
| Credentials | `.env` file on disk | Dedicated macOS Keychain (`~/.cortex-bot/cortex-bot.keychain-db`) |
| Security | None | Audit, permissions, rate limiting, tiers |
| Install | Clone + copy + poetry | `uvx cortex-mcp configure` |
| Distribution | GitHub only | PyPI (`pip install cortex-mcp`) |
| Destructive tools | Always enabled | Disabled by default, opt-in |
| Platform | Any | macOS only |

## Estimate

~130 hours solo / ~42 hours with Claude Code / ~10 calendar days

## Phases

1. **MVP** (28 hrs) — Server, keychain creds, httpx client, 15 core tools, audit
2. **Full Tools** (36 hrs) — Migrate all 90 tools, response optimization, install command
3. **Security** (26 hrs) — Middleware, tiers, rate limiting, circuit breaker, caching
4. **Production** (40 hrs) — HTTP transport, auth, CI/CD, tests, PyPI, docs
