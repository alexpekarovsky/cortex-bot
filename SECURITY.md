# Security Policy - Cortex Bot Custom Tools

## Overview

This document describes the security considerations, data access, and permissions required for Cortex Bot custom tools.

## What These Tools Access

### API Access

The custom tools connect to your Cortex XSIAM tenant via REST API using credentials you provide:
- **API Endpoint:** Your XSIAM tenant URL
- **Authentication:** API Key + API Key ID (configured in official PANW MCP server)
- **Protocol:** HTTPS only (enforced)

### Permissions Required

The tools require API permissions based on functionality:

| Tool Category | Required Permissions |
|--------------|---------------------|
| Case/Issue Management | Read incidents, Read alerts, Update incidents, Update alerts |
| Threat Hunting | Execute XQL queries, Read security data |
| Enrichment | Access threat intelligence integrations |
| Response Actions | Isolate endpoints, Terminate processes, Quarantine files, Execute scripts |
| SDK Tools | Upload content, Validate content, Download content |
| Assets | Read asset inventory, Read endpoints |

**Principle of Least Privilege:** Only grant permissions your organization requires. Destructive tools can be disabled via configuration.

## Data Handling

### Data Storage

**The tools DO NOT store any data persistently.**

- No credentials stored in tool code
- No security data cached locally
- No logs containing sensitive information
- All data retrieved on-demand from XSIAM API

### Data Transmission

- All API calls use **HTTPS** (TLS 1.2+)
- Credentials passed via HTTP headers (never in URLs)
- No data sent to third parties
- Communication only between: MCP Server ↔ XSIAM API

### Credentials

**Where credentials are stored:**
- Official PANW MCP server configuration (`.env` file or Claude config JSON)
- **NOT** in custom tools code
- **NOT** in git repository
- **NOT** in logs

**Custom tools inherit credentials automatically** from the PANW MCP server - they never store or transmit credentials separately.

## Code Review

### Transparency

All source code is available for review:
- **Python tools:** `custom_components/*.py` (28 files)
- **YAML tools:** `custom_components/openapi/*.yaml` (25 files)
- **Total:** ~15,000 lines of reviewable code

### No Obfuscation

- No compiled binaries
- No minified code
- No encrypted payloads
- Plain Python and YAML - fully auditable

### Dependencies

Tools use only the dependencies already installed by official PANW MCP server:
- `fastmcp` - MCP framework
- `httpx` - HTTP client
- `pydantic` - Data validation
- Standard Python libraries

**No additional dependencies installed.**

## Installation Security

### What the Installer Does

The optional `install.sh` script (reviewable before running):
1. Locates PANW MCP installation directory (via `find` command)
2. Verifies it's a valid MCP installation (checks for `src/main.py`)
3. Copies `custom_components/` folder to `src/usecase/custom_components/`
4. Verifies file count matches expected
5. Restarts MCP server (via `pkill`)

**No operations requiring elevated privileges (no `sudo`).**

### Integrity Verification

Verify package integrity before installation:

```bash
# Download CHECKSUMS.txt
wget https://github.com/alexpekarovsky/cortex-bot/releases/latest/download/CHECKSUMS.txt

# Verify ZIP file
sha256sum -c CHECKSUMS.txt
```

## Threat Model

### Risks Mitigated

✅ **Credential Exposure:** Credentials never in code, logs, or git
✅ **Code Tampering:** SHA256 checksums provided for verification
✅ **Unauthorized Access:** Tools inherit PANW MCP's access controls
✅ **Data Leakage:** No persistent storage, no third-party transmission

### Risks Users Should Consider

⚠️ **API Permissions:** Tools can perform actions based on API key permissions
⚠️ **Destructive Actions:** Some tools can isolate endpoints, terminate processes, etc.
⚠️ **Trust Boundary:** Tools execute in PANW MCP server environment with its privileges

### Mitigation Strategies

1. **Use Instance Administrator role** - Provides audit trail
2. **Enable tool restrictions** - Set `ENABLE_DESTRUCTIVE_TOOLS=false` in config
3. **Review logs** - Monitor `cortex-mcp.log` for API activity
4. **Rotate credentials regularly** - Change API keys every 90 days
5. **Use separate API key** - Dedicated key for MCP (not your personal admin key)

## Destructive Tools

The following tools can make irreversible changes:

| Tool | Action | Risk Level | Reversible |
|------|--------|------------|-----------|
| `isolate_endpoint` | Network isolation | HIGH | Yes (unisolate_endpoint) |
| `terminate_process` | Kill process | HIGH | No |
| `terminate_causality` | Kill process tree | HIGH | No |
| `quarantine_files` | Quarantine files | HIGH | Yes (restore_file) |
| `run_script` | Execute scripts | HIGH | Depends on script |
| `run_snippet_code_script` | Execute code | HIGH | Depends on code |

To control destructive tools, configure in your `.env` file:
```bash
# In PANW MCP .env file:
ENABLE_DESTRUCTIVE_TOOLS=true   # or false to restrict
```

## Audit and Compliance

### Audit Trail

All tool operations are logged:
- **MCP Server Logs:** `cortex-mcp.log` - Shows all tool invocations
- **XSIAM Audit Logs:** Settings → Audit Logs → API Activity
- **War Room:** Investigation notes (for case/issue operations)

### Compliance Considerations

- Tools support SOC 2, ISO 27001, and GDPR workflows
- No PII stored by tools (only accessed from XSIAM)
- All operations traceable via audit logs
- Credentials managed per organizational policy

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Open a private security advisory on GitHub
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you on remediation.

## Security Best Practices

### For Administrators

1. **Separate API Keys:** Use dedicated MCP API key (not personal admin key)
2. **Minimum Permissions:** Grant only necessary API permissions
3. **Regular Rotation:** Rotate API keys every 90 days
4. **Monitor Usage:** Review API audit logs weekly
5. **Test First:** Use in test/dev environment before production

### For Users

1. **Verify Installation:** Check SHA256 checksums before extracting
2. **Review Code:** Audit tool source code before installation
3. **Understand Tools:** Read documentation for destructive tools
4. **Use Carefully:** Confirm actions before executing destructive operations
5. **Report Issues:** Contact administrators if tools behave unexpectedly

## Third-Party Dependencies

### PANW MCP Server Dependencies (Inherited)

Custom tools use only dependencies from the official PANW MCP server:
- No additional packages installed
- No external library downloads
- Uses PANW's vetted dependency tree

### SDK Tools (Optional)

If using SDK tools, they require:
- `demisto-sdk` (installed via `uvx` in isolated environment)
- `uv` package manager (for isolation)

Both are open source and auditable:
- demisto-sdk: https://github.com/demisto/demisto-sdk
- uv: https://github.com/astral-sh/uv

## License

This project is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.

These tools extend the official Palo Alto Networks Cortex MCP Server, which is distributed under its own license.

---

**Last Updated:** 2026-02-08
**Security Contact:** [Open a private security advisory](https://github.com/alexpekarovsky/cortex-bot/security/advisories)
**Version:** 1.0.0
