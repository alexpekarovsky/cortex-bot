# Cortex Bot v2.0 — Combined Review Report

**Date**: March 26, 2026
**Reviewers**: 3 parallel agents (Security, Architecture, Documentation)
**Status**: Security + Documentation complete, Architecture in progress

---

## Security Review — 4 CRITICAL, 6 HIGH, 6 MEDIUM, 5 LOW

### CRITICAL (must fix before shipping)

| # | Finding | Location | Fix |
|---|---------|----------|-----|
| C-1 | **Keychain password exposed in `ps aux`** — `-p` flag passes password as CLI argument visible to all processes | ARCHITECTURE.md credentials.py, PLAN.md | Pipe password via stdin instead of `-p` flag |
| C-2 | **TLS disabled in configure/doctor** — `verify=False` in CLI connectivity tests | ARCHITECTURE.md cli.py | Remove `verify=False`, add `--ca-cert` flag for custom certs |
| C-3 | **TLS disabled in existing v1.0 playbook tools** — `verify=False` in get_playbook/insert_playbook | playbook_api.py | Default `verify=True`, add `--insecure` flag with warning |
| C-4 | **`run_snippet_code_script` has zero guardrails** — arbitrary Python execution on endpoints with no confirmation | script_tools.py | DESTRUCTIVE tier + `confirm_destructive_action` + audit full code |

### HIGH

| # | Finding | Fix |
|---|---------|-----|
| H-1 | XQL blocklist uses SQL keywords (irrelevant to XQL) | Replace with XQL-specific validation: require `dataset =` prefix, inject `limit`, block `config` dataset |
| H-2 | Path traversal check only catches `../` literal — misses URL encoding, null bytes, symlinks | Use `Path.resolve()` + base directory allowlist (pattern from create_playbook.py) |
| H-3 | Audit log has no integrity protection (no HMAC chain, 0644 permissions) | Set 0600 permissions, add HMAC chain, support syslog forwarding |
| H-4 | Circuit breaker can be weaponized — 5 failures blocks ALL tools for 30s | Per-category breakers, only count 5xx errors, higher threshold for reads |
| H-5 | Bearer token auth has no rotation/expiration | Write token to file (0600), add TTL, support revocation |
| H-6 | `run_xql_query` has no input validation | Inject `limit`, dataset allowlist, query length cap, full query in audit |

### Positive (12 items)
- Dedicated keychain isolation, SecretStr, localhost-only binding, tool tiers, audit always-on, credential scrubbing filter, no keyring library, middleware single entry point, path validation in existing code, `secrets.compare_digest`, circuit breaker pattern, `shlex.quote` in content generator

---

## Documentation Review — 4 Critical, 6 High, 8 Medium, 7 Low

### CRITICAL (will cause implementation confusion)

| # | Finding | Location |
|---|---------|----------|
| A1 | **Tool counts inconsistent** — SDK: 9 vs 10, existing: 75 vs 77, tables sum to 71-86 not 90 | All docs |
| A7 | **Rate limiter signature mismatch** — middleware calls `check(tool_name)` but implementation needs `check(tool_name, tier)` | ARCHITECTURE.md |
| B3 | **OpenAPI YAML references contradict "migrated to Python"** — structure shows `openapi/`, phase mentions YAML loader | ARCHITECTURE.md, HTML |
| D1 | **SecurityMiddleware has no `__init__`** — class uses `self.permissions`, `self.audit` etc but never initializes them | ARCHITECTURE.md |

### HIGH

| # | Finding |
|---|---------|
| B5 | `verify=False` in CLI code contradicts TLS security posture |
| B6 | SKILLS.md says "verify=false" but security fixes say "verify=True" |
| B4 | HTML mentions `sdk_init` (removed tool) |
| A2 | PLAN.md lists `fastmcp` as dependency (should be `mcp[cli]`) |
| E2 | Line 47 says "Keyring" (should be "Keychain") |
| B2 | Imports `PureWindowsPath` on macOS-only project |

### Missing implementations needed

| # | Component | Status |
|---|-----------|--------|
| D2 | `Permissions` class (is_allowed, tier mapping, blocklist) | No code |
| D3 | Tool registration pattern (`@mcp.tool()` + lifespan context) | No code |
| D4 | `config.py` (pydantic-settings) | No code |
| D5 | Skills are prompt-only — should clarify not server-side | Unclear |

---

## Architecture Review — 1 CRITICAL, 3 HIGH, 5 MEDIUM, 2 LOW

### CRITICAL

| # | Finding | Location | Fix |
|---|---------|----------|-----|
| A-1 | **FastMCP Middleware API may not exist as documented** — imports `from mcp.server.fastmcp.server import Middleware` but this is unverified against actual `mcp[cli]` package. Codebase uses standalone `fastmcp`, not `mcp.server.fastmcp` | ARCHITECTURE.md sec 5.1 | **Verify before Phase 1** — install `mcp[cli]`, check if Middleware class exists. Fallback: monkey-patch `_tool_manager.call_tool` |

### HIGH

| # | Finding | Fix |
|---|---------|-----|
| A-2 | `create_server()` called in CLI but never defined in server.py — server uses module-level singleton | Define factory function or refactor CLI |
| A-3 | No tool registration pattern shown — v1.0 `BaseModule` removed but v2.0 `@mcp.tool()` + context access not demonstrated | Add complete tool example with decorator, context, error handling |
| A-4 | `verify=False` in CLI contradicts security posture (same as C-2) | Remove, add `--insecure` flag |

### MEDIUM

| # | Finding | Fix |
|---|---------|-----|
| A-5 | `_truncate()` last-resort JSON will crash — `json.loads(truncated_string)` produces invalid JSON | Return summary dict instead of parsing truncated string |
| A-6 | `_unlock_keychain()` called 3x on startup (once per credential) — 6 subprocess calls when 2 would suffice | Unlock once in `__init__`, read 3 creds |
| A-7 | Rate limiter API mismatch (same as docs A7) | Resolve tier in middleware before calling check() |
| A-8 | `XSIAMClient.post()` used in migration pattern but only `.request()` defined | Add `.post()` convenience method |
| A-9 | `SecurityMiddleware.__init__` not shown — unclear how deps are injected since middleware created before lifespan | Accept deps as constructor params or lazy-init from context |

### Feasibility Assessment

| Phase | Estimate | Verdict |
|-------|----------|---------|
| Phase 1 (28h) | Realistic | Biggest risk: middleware API verification |
| Phase 2 (36h) | Realistic | Mostly mechanical, but `xsiam_content_generator.py` (1626 lines) is heavy |
| Phase 3 (26h) | Realistic | Code samples are nearly complete |
| Phase 4 (31h) | **Underestimated 30-50%** | Tests + CI/CD + PyPI + docs is a lot for 10h with Claude |

**Overall: 7.5/10 — Nearly ready to build after 2-4 hours of design fixes.**

---

## Action Items (prioritized)

### P0 — MUST fix before building (blockers)

| # | Item | Sources |
|---|------|---------|
| 1 | **Verify FastMCP Middleware API** — install `mcp[cli]`, confirm `Middleware` class, `on_call_tool` hook, `add_middleware()` exist | Arch A-1 |
| 2 | **Fix keychain password in `-p` argument** → pipe via stdin, not CLI arg visible in `ps aux` | Sec C-1 |
| 3 | **Remove `verify=False` everywhere** → default True, add `--insecure` flag with warning | Sec C-2/C-3, Arch A-4, Docs B5/B6 |
| 4 | **Define `create_server()` factory function** — CLI calls it but server.py uses module-level singleton | Arch A-2 |
| 5 | **Add complete tool registration example** — `@mcp.tool()`, context access, error handling, `register_all()` | Arch A-3, Docs D3 |
| 6 | **Add `SecurityMiddleware.__init__`** — show how permissions, audit, rate_limiter, validator are injected | Arch A-9, Docs D1 |
| 7 | **Fix rate limiter signature** — middleware calls `check(tool_name)` but method needs `check(tool_name, tier)` | Arch A-7, Docs A7 |
| 8 | **Standardize tool count** — pick actual number (88? 90?), update all 5 documents | Docs A1 |
| 9 | **Remove OpenAPI YAML references** — contradicts "migrated to Python", remove from structure/phases/deps | Docs B3 |

### P1 — Fix before building (important)

| # | Item | Sources |
|---|------|---------|
| 10 | Write `Permissions` class code (is_allowed, get_tier, blocklist/allowlist) | Docs D2 |
| 11 | Write `config.py` pydantic-settings implementation | Docs D4 |
| 12 | Add `XSIAMClient.post()` convenience method (migration pattern uses it) | Arch A-8 |
| 13 | Optimize keychain unlock — once per session, not per credential | Arch A-6 |
| 14 | Add `run_snippet_code_script` to DESTRUCTIVE tier + confirmation | Sec C-4 |
| 15 | Replace XQL SQL blocklist with XQL-specific validation | Sec H-1 |
| 16 | Fix path traversal — use `Path.resolve()` + base directory allowlist | Sec H-2 |
| 17 | Remove `PureWindowsPath` import (macOS only) | Docs B2 |
| 18 | Fix "Keyring" → "Keychain" on ARCHITECTURE.md line 47 | Docs E2 |
| 19 | Fix PLAN.md `fastmcp` → `mcp[cli]` dependency name | Docs A2 |
| 20 | Remove `sdk_init` from HTML | Docs B4 |
| 21 | Add `click` to HTML dependencies table | Docs A3 |
| 22 | Fix `_truncate()` last-resort — return summary dict, not parse truncated JSON | Arch A-5, Docs C4 |

### P2 — Improve (before production)

| # | Item | Sources |
|---|------|---------|
| 23 | Add HMAC chain to audit log for tamper detection | Sec H-3 |
| 24 | Per-category circuit breakers (not global) | Sec H-4 |
| 25 | Token rotation/expiration for HTTP auth | Sec H-5 |
| 26 | XQL input validation (limit injection, dataset allowlist, length cap) | Sec H-6 |
| 27 | Set `~/.cortex-bot/` directory permissions to 0700 | Sec M-3 |
| 28 | Audit log file permissions to 0600 | Sec H-3 |
| 29 | Align env var tables between ARCHITECTURE.md and HTML | Docs A8/A9 |
| 30 | Increase Phase 4 time estimate by 30-50% | Arch feasibility |
| 31 | Add keychain auto-lock handling (re-unlock during long sessions) | Arch 5.2 |
| 32 | Add keychain ACL setup for headless/background operation | Arch 3.6 |
| 33 | Clarify skills are prompt-engineering, not server-side | Docs D5 |
| 34 | Move SKILLS.md Step 2 to separate roadmap doc | Arch 3.4 |
| 35 | Align `SERVICE` vs `KEYCHAIN_SERVICE` constant name | Docs A5 |

---

## Positive Observations (across all 3 reviews)

- **Dedicated keychain isolation** — limits blast radius, well-reasoned
- **SecretStr usage** — prevents accidental credential logging
- **Localhost-only HTTP binding** — fixes real PANW bug
- **Tool tier system** — DESTRUCTIVE disabled by default is strong defense-in-depth
- **Audit logging always on** — structured JSONL with scrubbing is production-grade
- **Credential scrubbing filter** — catches leaks from third-party libs
- **Circuit breaker pattern** — state machine correctly implemented
- **`secrets.compare_digest`** — prevents timing attacks on auth token
- **`shlex.quote`** — command injection fix correctly applied
- **Response optimization** — three-layer approach appropriate for LLM context
- **Lifespan pattern** — correct FastMCP resource lifecycle management
- **Caching strategy** — category-based TTL with explicit NEVER_CACHE is good design
- **Overall architecture rated 9/10** for design quality

---

## Verdict

**Nearly ready to build.** 9 P0 items need fixing first (estimated 3-4 hours of design work). The single biggest risk is item #1 — verifying the FastMCP Middleware API actually exists. Everything else is documentation fixes and missing code samples.

After P0 fixes, Phase 1 implementation can begin with confidence.
