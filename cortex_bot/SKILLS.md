# Cortex Bot v2.0 — Skills System Design

## What is a Skill?

A skill is a **pre-built SOC workflow** that Claude Code can execute using MCP tools. Each skill encodes:
- Complete XSIAM domain knowledge (terminology, API quirks, best practices)
- Exact tool sequence with correct parameters
- Decision logic (what to do based on results)
- Error handling and fallback paths

Users invoke skills naturally: "investigate case 474" or explicitly: `/investigate 474`

---

## Architecture

```
User: "investigate case 474"
  │
  ▼
Claude Code (CLAUDE.md loaded with skill definitions)
  │
  ├── Matches intent → "investigate" skill
  ├── Expands into full SOC analyst workflow prompt
  ├── Calls MCP tools in sequence:
  │     get_incident_extra_data(474)
  │     → get_alert_multi_events(alert_id)
  │     → enrich_ip_address(suspicious_ip)
  │     → run_xql_query(hunt for IOCs)
  │     → update_case_ai_summary(474)
  │
  └── Returns structured investigation report
```

### Three layers:

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Knowledge Base                        │
│  CLAUDE.md — XSIAM terminology, API quirks,     │
│  field names, common mistakes, tool selection    │
├─────────────────────────────────────────────────┤
│  Layer 2: Skills (workflows)                    │
│  /investigate, /hunt, /triage, /respond,         │
│  /detect, /build, /report, /monitor             │
├─────────────────────────────────────────────────┤
│  Layer 3: MCP Tools (90 tools)                  │
│  get_cases, run_xql_query, isolate_endpoint...   │
└─────────────────────────────────────────────────┘
```

---

## Layer 1: Knowledge Base (CLAUDE.md)

Loaded into every conversation automatically. Contains everything Claude Code needs to be a senior XSIAM analyst.

### Sections:

```markdown
# Cortex Bot — CLAUDE.md

## XSIAM Terminology (CRITICAL)
- "issues" = alerts (API term). Use get_issues, update_issue.
- "cases" = incidents (UI term). Use get_cases, update_incident.
- Close an issue: Builtin|||closeInvestigation (NOT closeCase)
- Update an issue: Builtin|||setAlert (NOT setIssue — it doesn't exist)
- War Room runs on ISSUES, not cases. Always use alert_id.

## Tool Selection Guide
- Need case list? → get_cases
- Need alert details? → get_issues + get_alert_multi_events
- Need forensic data? → run_xql_query
- Need to check a file/IP/domain? → enrich_* tools
- Need to run a command on XSIAM? → run_xsoar_automation
- Need endpoint info? → get_endpoints / get_filtered_endpoints
- Need to act on endpoint? → isolate/scan/terminate (DESTRUCTIVE)
- Building a playbook? → ALWAYS call get_playbook_building_blocks first
- Building an integration? → ALWAYS call get_xsoar_pattern_guide first

## XQL Field Reference
- Correct: action_process_image_command_line (NOT action_process_command_line)
- Correct: agent_hostname (NOT hostname)
- Correct: action_file_sha256 (NOT file_sha256)
- Correct: _vendor, _product (NOT event_vendor, event_product)
- ALWAYS test XQL with run_xql_query before adding to playbooks

## API Quirks
- get_vulnerabilities requires use_page_token: true
- insert_playbook: use --insecure flag if tenant has self-signed cert
- Playbook Builtin commands need iscommand:true, brand:Builtin, script: field
- update_issue returns 204 No Content on success (not JSON)
- War Room needs investigation active — open case in browser or add_war_room_entry first

## Common Mistakes to Avoid
- Don't use scriptName: for Builtin commands — use script:
- Don't use closeCase in playbooks — use closeInvestigation
- Don't assume War Room exists — check/create first
- Don't use event_vendor in XQL — use _vendor
- Don't send required dict params without str fallback parsing
```

---

## Layer 2: Skills (Workflows)

### Skill: `/investigate`

```
Trigger: "investigate case X", "look into case X", "what happened in case X"
```

**Workflow:**
1. `get_incident_extra_data(case_id)` — get full case with all alerts
2. For each alert: `get_alert_multi_events(alert_id)` — get raw events
3. Extract IOCs (IPs, domains, hashes) from events
4. Enrich each IOC: `enrich_ip_address`, `enrich_domain`, `enrich_file_hash`
5. `run_xql_query` — hunt for related activity across environment
6. `get_war_room_entries` — check existing investigation notes
7. Generate findings report with MITRE ATT&CK mapping
8. `update_case_ai_summary(case_id)` — save summary to case
9. Present actionable recommendations

**Decision points:**
- If malicious IOC found → recommend containment (isolate, blocklist)
- If lateral movement detected → escalate, check other endpoints
- If false positive → recommend closure with reason

---

### Skill: `/hunt`

```
Trigger: "hunt for X", "look for X activity", "search for X"
```

**Workflow:**
1. Parse hunt target (IP, domain, hash, process, technique)
2. Select appropriate XQL dataset and filters
3. `run_xql_query` — execute hunt query (7 days default)
4. If results found:
   - Identify affected endpoints and users
   - `get_filtered_endpoints` — check endpoint status
   - Correlate with existing cases: `get_cases`
   - Enrich any new IOCs
5. If no results: broaden search (30 days, different datasets)
6. Present findings with timeline

**Pre-built hunts:**
- PowerShell with bypass: `event_type = ENUM.PROCESS and action_process_image_name = "powershell.exe" and action_process_image_command_line contains "bypass"`
- Lateral movement: `event_type = ENUM.NETWORK and action_remote_port in (445, 3389, 5985, 5986)`
- Credential dumping: `action_process_image_name in ("mimikatz.exe", "procdump.exe") or action_process_image_command_line contains "sekurlsa"`
- Persistence: `event_type = ENUM.REGISTRY and action_registry_key_name contains "Run"`
- Data exfil: `event_type = ENUM.NETWORK and action_upload_bytes > 100000000`

---

### Skill: `/triage`

```
Trigger: "triage alerts", "show new alerts", "what needs attention"
```

**Workflow:**
1. `get_issues(filters=[status=new], sort=severity desc)` — get unresolved alerts
2. `get_cases(filters=[status=New])` — get open cases
3. Group by severity, category, affected hosts
4. For HIGH/CRITICAL:
   - `get_alert_multi_events` — quick forensic check
   - Enrich key IOCs
   - Assess if real threat or false positive
5. Present prioritized triage queue:
   - CRITICAL: Immediate action required
   - HIGH: Investigate within 1 hour
   - MEDIUM: Review within 4 hours
   - LOW: Batch review
6. `list_risky_users` + `list_risky_hosts` — context on affected entities

---

### Skill: `/respond`

```
Trigger: "contain endpoint X", "respond to case X", "isolate and investigate"
```

**Workflow:**
1. Assess situation: `get_incident_extra_data` or `get_filtered_endpoints`
2. Confirm target endpoint and threat type
3. **Containment** (with confirmation):
   - `isolate_endpoint` — cut network
   - `quarantine_files` — quarantine malicious files
   - `blocklist_files` — block hash globally
4. **Evidence collection**:
   - `retrieve_files` — pull suspicious files
   - `run_script(process_get)` — capture running processes
   - `run_snippet_code_script` — collect forensic artifacts
5. **Documentation**:
   - `add_war_room_entry` — document all actions taken
   - `update_case_ai_summary` — update case with response summary
6. **Recovery** (when threat eradicated):
   - `unisolate_endpoint` — restore network
   - Verify endpoint health

---

### Skill: `/detect`

```
Trigger: "create detection for X", "build rule for X", "detect when X"
```

**Workflow:**
1. Understand detection target (technique, IOC pattern, behavior)
2. `run_xql_query` — test detection logic against historical data
3. Refine query until it catches known-bad and avoids false positives
4. `insert_correlation_rule` — create the rule (disabled first)
5. Monitor for test period
6. Enable when validated

---

### Skill: `/build`

```
Trigger: "create integration for X", "build playbook for X", "create dashboard"
```

**Sub-skills:**

#### `/build playbook`
1. `get_playbook_building_blocks` — get reference patterns
2. Design playbook tasks
3. `create_playbook` — generate YAML (fix Builtin script format)
4. `insert_playbook` — upload to XSIAM
5. `create_issue` — create test issue
6. Open case in browser (activate War Room)
7. `run_playbook` — execute
8. `get_war_room_entries` — check for errors
9. Fix errors, re-upload, re-test
10. Iterate until 100% complete

#### `/build integration`
1. `get_xsoar_pattern_guide` — identify pattern (long-running, event collector, regular)
2. Call appropriate guide (get_xsoar_long_running_guide, etc.)
3. `sdk_validate` → `sdk_lint` → `sdk_upload` cycle
4. Test via `run_xsoar_automation`

#### `/build dashboard`
1. `create_xsiam_dashboard` — generate dashboard JSON
2. `sdk_upload` — upload pack
3. Verify in XSIAM UI

---

### Skill: `/report`

```
Trigger: "weekly report", "summary of last 24 hours", "executive briefing"
```

**Workflow:**
1. `get_cases` — all cases in time range
2. `get_issues` — all alerts in time range
3. `list_risky_users` + `list_risky_hosts` — risk posture
4. `get_vulnerabilities` — vuln stats
5. `run_xql_query` — event volume, top talkers, anomalies
6. Generate executive report:
   - Case metrics (opened, resolved, MTTR)
   - Alert distribution by severity/category
   - Top affected hosts and users
   - Risk score trends
   - Recommendations

---

### Skill: `/monitor`

```
Trigger: "watch for X", "alert me if X", "check every 5 minutes"
```

**Workflow (uses Claude Code /loop):**
1. Define check: XQL query, case filter, or endpoint status
2. Set interval (default: 5 minutes)
3. Loop:
   - Run check
   - Compare with previous state
   - If change detected → alert user
4. Examples:
   - "Monitor for new critical cases" → `get_cases(severity=critical)` every 5 min
   - "Watch if Gaming endpoint goes offline" → `get_filtered_endpoints` every 2 min
   - "Alert if new high severity alerts" → `get_issues(severity=HIGH, status=new)` every 3 min

---

## Layer 3: Skill Registration

Skills are **prompt-engineering artifacts** defined in CLAUDE.md — not server-side code.
Claude Code loads CLAUDE.md automatically into every conversation, giving it the knowledge
and workflow patterns to execute skills. No MCP-side skill registration is needed.

```markdown
# In CLAUDE.md — Skill definitions

## Available Skills

### /investigate <case_id>
Full case investigation with forensics, IOC enrichment, XQL hunting,
and AI summary generation. Follows SOC analyst workflow.

### /hunt <target>
Threat hunt across XDR data. Accepts IPs, domains, hashes, process names,
or MITRE technique IDs. Tests XQL queries, enriches findings.

### /triage
Show prioritized alert queue. Groups by severity, enriches HIGH/CRITICAL,
recommends actions. Includes risky users/hosts context.

### /respond <endpoint_or_case>
Incident response workflow: contain → collect evidence → document → recover.
Requires confirmation for destructive actions.

### /detect <description>
Create XQL correlation rule. Tests against historical data first,
creates disabled rule, monitors before enabling.

### /build playbook|integration|dashboard <name>
End-to-end content creation with iterative testing until 100% working.

### /report [time_range]
Executive security report with case metrics, risk posture, recommendations.

### /monitor <condition> [interval]
Proactive monitoring loop. Checks condition at interval, alerts on change.
Uses Claude Code /loop under the hood.
```

---

## Documentation Index

The skills system needs to know ALL Cortex XSIAM documentation. This is encoded in:

### Bundled as MCP Resources (served by the MCP server):

| Resource | Content | Size |
|----------|---------|------|
| `xsiam://docs/xql-reference` | Complete XQL field reference, operators, functions | ~50KB |
| `xsiam://docs/api-reference` | All API endpoints, params, response formats | ~80KB |
| `xsiam://docs/playbook-reference` | Task types, script formats, condition syntax | ~40KB |
| `xsiam://docs/content-types` | All XSIAM content types (parsing rules, modeling rules, etc.) | ~30KB |
| `xsiam://docs/mitre-mapping` | MITRE ATT&CK techniques → XQL detection patterns | ~60KB |

### Already built as guide tools (12 tools):

| Tool | Documentation |
|------|---------------|
| `get_playbook_building_blocks` | 60+ playbook task patterns |
| `get_xsoar_pattern_guide` | Integration pattern selection |
| `get_xsoar_long_running_guide` | Long-running integration dev |
| `get_xsoar_event_collector_guide` | Event collector dev |
| `get_xsoar_feed_guide` | Feed integration dev |
| `get_xsoar_layout_guide` | Layout development |
| `get_xsoar_mirroring_guide` | Bidirectional sync |
| `get_xsoar_scheduled_commands_guide` | Async polling pattern |
| `get_xsoar_playbook_operations_guide` | Running playbooks on alerts |
| `get_xsoar_best_practices` | Threading, state management |
| `get_xsiam_content_guide` | Content types reference |
| `get_slack_interactive_workflows_guide` | Slack integration |

### To be built (new documentation tools):

| Tool | Content | Priority |
|------|---------|----------|
| `get_xql_reference` | Complete XQL syntax, fields, functions, operators | P0 |
| `get_api_reference` | All 90+ API endpoints with params and examples | P0 |
| `get_mitre_detection_patterns` | MITRE technique → XQL query mapping | P1 |
| `get_incident_response_playbook` | IR procedures by incident type | P1 |
| `get_compliance_reference` | CIS benchmarks, NIST mappings | P2 |

---

## Step 2 Preview: Proactive Loops & Schedulers & UI

### Proactive Loops
```
cortex-mcp monitor --check "new critical cases" --interval 5m --notify slack
cortex-mcp monitor --check "endpoint offline" --target Gaming --interval 2m
cortex-mcp monitor --xql "dataset = xdr_data | filter severity = HIGH | comp count() as c | filter c > 0" --interval 10m
```

### Schedulers
```
cortex-mcp schedule --daily "generate security report" --time 08:00 --output slack
cortex-mcp schedule --weekly "run compliance check" --day monday --time 09:00
cortex-mcp schedule --on-alert "auto-triage new HIGH alerts"
```

### UI (TUI — Terminal UI)
```
cortex-mcp ui

┌─ Cortex Bot ─────────────────────────────────────────┐
│                                                       │
│  Cases: 5 new │ 3 investigating │ 282 resolved        │
│  Alerts: 12 new (3 HIGH, 9 MEDIUM)                   │
│  Endpoints: 3 connected │ 2 disconnected              │
│  Risk: alexp (LOW 40) │ alex mac pro (MED 50)        │
│                                                       │
│  > investigate case 474                               │
│  ─────────────────────────────────────────            │
│  Running investigation...                             │
│  ✓ Case details loaded (1 alert)                     │
│  ✓ Events retrieved                                   │
│  ✓ IOCs enriched (2 IPs, 1 domain)                   │
│  ✓ XQL hunt complete (0 related events)              │
│  ✓ Summary generated                                 │
│                                                       │
│  Verdict: False Positive                              │
│  Recommendation: Close as known issue                 │
│                                                       │
│  [Close Case] [Escalate] [Hunt More] [Report]        │
└───────────────────────────────────────────────────────┘
```

Technologies:
- **TUI**: Textual (Python) — rich terminal UI framework
- **Loops**: asyncio tasks + state persistence
- **Notifications**: Slack (via SlackV3), email (via mail-sender)
- **Scheduling**: APScheduler or built-in asyncio
