# Release Notes

## v1.1.0 — April 6, 2026

**106 tools** (up from 90 in v1.0.0) — 16 new tools across 4 new categories.

### New Tools (16)

#### IOC & BIOC Management (4 new tools)
- `get_indicators` — List IOC rules with filtering (type, severity, rule_id)
- `get_biocs` — List Behavioral IOC rules with MITRE mapping
- `insert_bioc` — Create/update BIOC detection rules
- `get_datasets` — List all datasets available for XQL queries (name, type, size, event count)

#### Platform Tools (6 new tools)
- `get_audit_management_logs` — Who did what and when (API usage, config changes, user actions)
- `get_audit_agent_reports` — Agent installation, upgrade, and status events
- `get_distributions` — List agent distribution packages (installers)
- `get_endpoint_profiles` — Endpoint security profiles (prevention policies)
- `get_triage_presets` — Forensic triage data collection configurations
- `trigger_vulnerability_scan` — Trigger vulnerability scan on a specific asset

#### Detection Rules (3 new tools)
- `search_correlation_rules` — List/filter all correlation rules
- `get_correlation_rule` — Get a specific rule by ID
- `delete_correlation_rule` — Delete a correlation rule by ID

#### Threat Hunting (1 new tool)
- `discover_dataset_schema` — Returns field names, types, and sample values for any dataset

#### XQL Workflow
New recommended workflow for XQL queries:
1. `get_datasets` — see what datasets exist and have data
2. `discover_dataset_schema` — see what fields each dataset has
3. `run_xql_query` — write your query with correct field names

### Improvements

#### Tool Fixes
- **`insert_indicators_csv`** — Fixed: sends CSV as `{"request_data": csv_string}` (was broken JSON wrapper)
- **`get_issues`** — Added field aliases (`status` -> `status.progress`, `domain` -> `issue_domain`), sparse id-filter workaround (from community PR #11)
- **`create_playbook`** — Brand auto-detection with longest-prefix-first matching, `_is_integration_command()` detection (from community PR #12)
- **`asset_tools`** — Added 404 handling for `get_assets` (returns helpful message instead of crash)

#### Terminology Fix
- All tools now use XSIAM terminology: **issues** (not alerts) and **cases** (not incidents)
- `setIssue` instead of `setAlert`, `closeInvestigation` instead of `closeCase`

#### Response Actions
- `isolate_endpoint`, `unisolate_endpoint`, `scan_endpoint` now accept optional `incident_id` parameter for automatic Case Timeline entries

#### insert_bioc Format
- Correct format: `type: "OTHER"`, `is_xql: false`, `indicator: {}` for new BIOCs
- Omit `rule_id` for INSERT, provide `rule_id` only for UPDATE
- Updated tool description with working example

#### test_all_tools
- All 106 tools make real API calls — no static "AVAILABLE" or "LIMITED" labels
- Detection: creates correlation rule, then deletes it (full roundtrip)
- IOC/BIOC: creates actual BIOC, handles duplicate gracefully
- Platform: calls all 6 APIs including endpoint_profiles, triage_presets, vuln_scan

#### Documentation
- Updated tool counts across README, INSTALL, and CLAUDE.md (90 -> 106)
- Added IOC & BIOC, Platform, and Detection Rules sections to README
- Added XQL workflow documentation to `run_xql_query` and `get_datasets` descriptions
- Added RELEASE_NOTES.md with v1.1.0 and v1.0.0 entries

### Community Contributions
- PR #11 by @dor1412 — Sparse id-filter workaround for `get_issues` (cherry-picked)
- PR #12 by @dor1412 — Playbook integration command detection and collection questions (cherry-picked)

### Breaking Changes
- `insert_indicators_csv` parameter changed from `request_data` (dict) to `csv_data` (string). Pass CSV content directly with header row.

### Known Issues
- `get_contributing_events` — Returns 500 on external correlation alerts (PANW API bug)
- `get_endpoint_profiles` — Requires specific license
- `get_triage_presets` — Requires Forensics add-on license
- `list_risky_users` / `list_risky_hosts` — Require ITDR license

---

## v1.0.0 — March 25, 2026

Initial release. 90 tools across 13 categories.

- 84 community-built Python tools extending the official Palo Alto Networks Cortex MCP Server
- All OpenAPI YAML tools migrated to pure Python
- DictResponse patch for Palo Alto Networks OpenAPI compatibility
- Full test pass on live XSIAM tenant (88/90 tools PASS)
- Tested destructive tools on Gaming endpoint (all reverted)
- Apache 2.0 license
