"""
XSOAR Playbook Building Blocks

Provides modern XSOAR/XSIAM playbook building blocks as MCP tools.
Based on analysis of 22 production playbooks from PANW content repository.

CRITICAL TERMINOLOGY (XSIAM):
- "Issues" (individual security events) - NOT "alerts"
- "Cases" (collections of issues) - NOT "incidents"
- Context: ${issue.*} - NOT ${incident.*} or ${alert.*}

All building blocks verified against production playbooks (2025).
"""

import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

# ============================================================================
# MODERN XSOAR PLAYBOOK BUILDING BLOCKS (2025)
# ============================================================================

PLAYBOOK_BUILDING_BLOCKS = """
# Modern XSOAR/XSIAM Playbook Building Blocks (2025)

**Based on analysis of 22 production PANW playbooks**

## CRITICAL: XSIAM Terminology

**Correct Terms:**
- **"Issue"** - Individual security event (use ${issue.*} in YAML)
- **"Case"** - Collection of related issues (parent container)

**Commands:**
- Update issue: `Builtin|||setIssue`
- Close case: `Builtin|||closeInvestigation`
- War Room notes: Use `Print` script (NOT `addEntries` — it requires JSON, not plain text)

**Context Variables:** Always use `${issue.*}` (e.g., ${issue.id}, ${issue.severity}, ${issue.agentid})

---

## CRITICAL: Script vs Command Reference Format in Playbook YAML

**Two types of tasks — each uses a DIFFERENT field format:**

### Automation Scripts (e.g., Print, ParseJSON, Set)
```yaml
task:
  script: Print          # Bare script name — NO pack prefix (not "CommonScripts|||Print")
  iscommand: false
  brand: ""
```
- `iscommand: false` — it is a script/automation, not an integration command
- `brand: ""` — leave blank for scripts
- **WRONG:** `script: CommonScripts|||Print` → causes "Missing script" error even if installed
- **CORRECT:** `script: Print`

### Integration Commands (e.g., xdr-get-endpoints, ip, file)
```yaml
task:
  script: Cortex Core - IR|||xdr-get-endpoints   # Pack|||command format
  iscommand: true
  brand: "Cortex Core - IR"
```
- `iscommand: true` — it is an integration command
- `brand` must match the exact integration name from list_integrations

---

## CRITICAL: Incremental Playbook Development - COMPLETE ALL 4 PHASES

**Build playbooks iteratively - Start simple, progressively add ALL complexity:**

**IMPORTANT:** This is a PROGRESSION, not a stopping point. You MUST complete all 4 phases to deliver a production-ready playbook. Do NOT stop at Phase 1!

### Phase 1 - Minimal Viable Playbook (5 tasks)
```yaml
Start → Title → Core Task → setIssue Documentation → Done
```
**Purpose:** Validate basic playbook structure
**Actions:**
1. Create minimal playbook with 1 main task
2. Test the task independently before adding to playbook
3. Upload playbook
4. Test in XSIAM - verify task executes successfully
5. Fix any structural errors

**Example Core Tasks by Use Case:**
- **Investigation:** XQL threat hunt, IoC collection, malware analysis
- **Remediation:** Patch deployment, configuration change, service restart
- **Validation:** Health check, compliance scan, configuration verification
- **Ticketing:** Create ticket, assign owner, set priority
- **Reporting:** Data aggregation, metrics collection, template population
- **Response:** Containment actions, isolation, threat neutralization
- **Automation:** Data transformation, routing, workflow orchestration
- **Integration:** External system sync, API calls, data synchronization
**Then:** PROCEED TO PHASE 2

### Phase 2 - Add Core Logic
```yaml
Start → Title → Task 1 → Task 2 → Task 3 → setIssue → Done
```
**Purpose:** Build primary playbook functionality
**Actions:**
1. Add 2-3 additional main tasks
2. Test each task independently
3. Upload playbook
4. Test in XSIAM - verify task sequence executes
5. Fix any task execution errors

**Example Additions by Use Case:**
- **Investigation:** Additional threat hunts, scope analysis, timeline building
- **Remediation:** Validation checks, rollback preparation, dependency updates
- **Response:** Containment actions, evidence collection, notification chains
- **Automation:** Data processing, transformation, routing logic
- **Reporting:** Multi-source data aggregation, dashboard updates
- **Ticketing:** Status synchronization, comment updates, escalation routing
**Then:** PROCEED TO PHASE 3

### Phase 3 - Add Supporting Features
```yaml
Start → Supporting Tasks → Core Logic → setIssue → Done
```
**Purpose:** Enhance playbook with supporting capabilities
**Actions:**
1. Add supporting tasks relevant to your use case
2. Upload playbook
3. Test in XSIAM - verify integrations work
4. Fix any integration errors

**Example Supporting Features by Use Case:**
- **Investigation:** Enrichment lookups, threat intelligence, sandbox analysis
- **Remediation:** Backup validation, health checks, compliance scanning
- **Ticketing:** External system sync, approval routing, escalation
- **Reporting:** Data aggregation, template population, distribution
**Then:** PROCEED TO PHASE 4

### Phase 4 - Add Advanced Features & Finalization (As many tasks as needed)
```yaml
Start → Supporting → Core → Conditions → Advanced → Final Summary → Done
```
**Purpose:** Production-ready playbook with complete automation
**Actions:**
1. Add conditional branching and decision logic
2. Add advanced automation and workflows
3. Add manual approval points where appropriate
4. Update final setIssue with comprehensive summary
5. Upload playbook
6. Test complete end-to-end flow
7. Verify all conditional branches execute correctly

**Example Advanced Features by Use Case:**
- **Investigation:** Auto-containment decisions, escalation logic, case closure workflows
- **Remediation:** Rollback on failure, multi-stage deployment, verification loops
- **Compliance:** Approval chains, audit trail generation, exception handling
- **Integration:** Cross-platform orchestration, data synchronization, callback handling
**This phase is your production deliverable**

### Why This Process Works:
- Phase 1: Validates structural correctness with minimal complexity
- Phase 2: Confirms all core logic executes properly
- Phase 3: Integrates supporting features safely
- Phase 4: Adds advanced automation
- Each phase is validated independently
- Final playbook is fully tested and production-ready

**CRITICAL RULES:**
1. Test ALL XQL queries with `run_xql_query` tool BEFORE adding to ANY phase
2. Upload and test AFTER EACH phase
3. Fix errors before proceeding to next phase
4. COMPLETE ALL 4 PHASES - don't stop at Phase 1!
5. Phase 4 is the deliverable - Phases 1-3 are building blocks

**Important:** Complete ALL 4 phases. Phase 1 is a checkpoint, not a final deliverable. Phase 4 is your production playbook.

---

## Top 10 Most Common Building Blocks

### 1. Condition Tasks (Decision Making)
**Frequency**: ALL playbooks use conditions
**Common Operators**: isNotEmpty, isEqualString, isExists, greaterThanOrEqual, containsGeneral

```yaml
type: condition
task:
  name: Is there malicious data?
  type: condition
conditions:
  - label: "yes"
    condition:
      - - operator: isNotEmpty
          left:
            value:
              simple: ${File.Malicious}
            iscontext: true
nexttasks:
  "yes": ["next_task"]
  "#default#": ["done_task"]
```

### 2. Title Tasks (Workflow Sections)
**Frequency**: Avg 3-5 per playbook
**Purpose**: Organize playbook into sections

```yaml
type: title
task:
  name: Enrichment Phase
  type: title
nexttasks:
  '#none#': ["task_id"]
```

Common section names: Done, Triage, Investigation, Remediation, Enrichment

### 3. Sub-Playbook Calls (Modular Reuse)
**Frequency**: 18 of 22 playbooks
**Key**: Use separatecontext for isolation

```yaml
type: playbook
task:
  name: Enrich File Hash
  playbookName: File Enrichment - Generic v2
scriptarguments:
  MD5:
    complex:
      root: ${issue.filemd5}
      transformers:
        - operator: uniq
separatecontext: true
loop:
  max: 100
```

### 4. Transformers (Data Manipulation)
**Most Common**: uniq (95% of playbooks), append, split, join, If-Then-Else

```yaml
# Remove duplicates
transformers:
  - operator: uniq

# Combine arrays
transformers:
  - operator: append
    args:
      item:
        value:
          simple: ${inputs.SHA256}

# Conditional transformation
transformers:
  - operator: If-Then-Else
    args:
      condition:
        value:
          simple: lhs==rhs
      then:
        value:
          simple: "Value if true"
      else:
        value:
          simple: "Value if false"
```

### 5. Filters (Context Filtering)
**Purpose**: Filter data before processing

```yaml
scriptarguments:
  Hash:
    complex:
      root: File
      filters:
        - - operator: isExists
            left:
              value:
                simple: File.Malicious
              iscontext: true
      accessor: SHA256
```

---

## Enrichment Blocks

### File Enrichment
```yaml
type: playbook
playbookName: File Enrichment - Generic v2
inputs:
  - MD5: ${issue.filemd5}
  - SHA256: ${issue.filesha256}
outputs:
  - File.Malicious
  - File.MD5
  - File.SHA256
```

### IP Enrichment
```yaml
type: playbook
playbookName: IP Enrichment - Generic v2
inputs:
  - IP: ${issue.src}
outputs:
  - IP.Malicious
  - IP.Address
  - IP.ASN
```

### Domain Enrichment
```yaml
type: playbook
playbookName: Domain Enrichment - Generic v2
inputs:
  - Domain: ${issue.domain}
outputs:
  - Domain.Malicious
  - Domain.Name
```

### Email Enrichment
```yaml
type: playbook
playbookName: Email Address Enrichment - Generic v2
inputs:
  - Email: ${issue.emailaddress}
outputs:
  - Account.Email.Malicious
```

---

## Containment Blocks (XSIAM 2.4+)

### Isolate Endpoint
```yaml
type: regular
script: '|||core-isolate-endpoint'
scriptarguments:
  endpoint_id: ${issue.agentid}
separatecontext: false
continueonerror: true  # Don't fail playbook if isolation fails
description: "Isolate compromised endpoint from network"
```

### Quarantine File
```yaml
type: regular
script: '|||core-quarantine-files-quick-action'
scriptarguments:
  file_path: ${File.Path}
  file_hash: ${File.SHA256}
  endpoint_id: ${issue.agentid}
separatecontext: false
continueonerror: true  # Don't fail playbook if quarantine fails
description: "Quarantine malicious file"
```

### Terminate Process
```yaml
type: regular
script: '|||core-terminate-causality-quick-action'
scriptarguments:
  causality_id: ${issue.causalityid}
  agent_id: ${issue.agentid}
separatecontext: false
continueonerror: true  # Don't fail playbook if termination fails
description: "Terminate malicious process tree"
```

### Block Indicators
```yaml
type: regular
script: '|||xdr-blocklist-files'
scriptarguments:
  hash_list: ${File.SHA256}
  comment: "Blocked via playbook - confirmed malicious"
separatecontext: false
continueonerror: true  # Don't fail playbook if blocklist fails
description: "Add file hash to blocklist"
```

---

## Case Blocks

### Endpoint Case Plan
```yaml
type: playbook
playbookName: Endpoint Case Plan
inputs:
  - Endpoint: ${issue.agentid}
outputs:
  - Endpoint.Status
  - Endpoint.Isolated
```

### Account Case Plan
```yaml
type: playbook
playbookName: Account Case Plan
inputs:
  - Username: ${issue.username}
outputs:
  - Account.Username
  - Account.Disabled
```

### MITRE ATT&CK Tactic Hunt
```yaml
type: playbook
playbookName: Get entity alerts by MITRE tactics
inputs:
  - EntityType: Host          # REQUIRED: "Host" or "User"
  - EntityID: ${issue.hostname}  # REQUIRED: hostname or username
  - RunAll: "True"            # Run all tactic hunts
  - timeRange: "7 days"       # Lookback window
outputs:
  - PATacticsResults
```

**CRITICAL:** Input names are `EntityType`/`EntityID` (NOT `HuntEntityType`/`HuntEntity`).
Set `RunAll: "True"` to execute all MITRE tactic hunts in one call.

---

## Decision Blocks

### Check if Malicious
```yaml
type: condition
conditions:
- label: "yes"
  condition:
  - - operator: isExists
      left:
        value: ${File.Malicious}
        iscontext: true
  - - operator: greaterThanOrEqual
      left:
        value: ${issue.severity}
        iscontext: true
      right:
        value: "3"
```

### Check Integration Availability
```yaml
type: condition
conditions:
- label: "available"
  condition:
  - - operator: isExists
      left:
        value: ${modules.VirusTotal}
        iscontext: true
```

---

## Closure Blocks (Modern Commands)

### Close as False Positive
```yaml
type: regular
script: '|||closeCase'
scriptarguments:
  closeReason: "Resolved - False Positive"
  closeNotes: "Case complete. No threat detected. Indicators verified as benign."
description: "Close case as false positive"
```

### Close as Threat Handled
```yaml
type: regular
script: '|||closeCase'
scriptarguments:
  closeReason: "Resolved - Threat Handled"
  closeNotes: "Threat successfully contained, eradicated, and remediated. Systems restored."
description: "Close case after successful remediation"
```

### Close as Duplicate
```yaml
type: regular
script: '|||closeCase'
scriptarguments:
  closeReason: "Resolved - Duplicate"
  closeNotes: "Duplicate of case ${LinkedCaseID}. Closing to avoid double-handling."
description: "Close as duplicate case"
```

### Close as Known Issue
```yaml
type: regular
script: '|||closeCase'
scriptarguments:
  closeReason: "Resolved - Known Issue"
  closeNotes: "Known false positive pattern. Detection rule threshold tuning recommended."
description: "Close known false positive"
```

---

## Update Blocks

### Update Case Metadata (Case-Level)
```yaml
type: regular
script: '|||setIncident'  # Updates case-level fields only
scriptarguments:
  severity: "4"
  customFields:
    containmentstatus: "Contained"
    casestatus: "Completed"
description: "Update case metadata"
```

### Update Issue Fields (Issue-Level) - CRITICAL DISTINCTION

**BREAKING CHANGE IN XSIAM:**
- Old Demisto: Used `setIncident` for everything
- Modern XSIAM: Must use `setIssue` for alerts/issues, `setIncident` only for cases

**Use setIssue (Required for Alert Playbooks):**
```yaml
type: regular
script: Builtin|||setIssue  # Updates issue/alert fields
scriptarguments:
  closeNotes:
    simple: 'Investigation complete. Findings documented.'
  severity:
    simple: "3"
description: "Document findings on the ISSUE"
```

**Working Issue Fields:**
- `closeNotes` - Investigation summary (RECOMMENDED - always works)
- `severity` - Update severity level (1=low, 2=medium, 3=high, 4=critical)
- `customFields` - Update custom fields (if field exists in schema)
- NOT SUPPORTED: `investigationsummary` - Does NOT exist in XSIAM (will fail)

**CRITICAL RULES:**
- DO NOT use setIncident in alert playbooks - Updates parent case, not the alert
- USE setIssue in alert playbooks - Updates the alert/issue itself
- USE closeNotes field - Most reliable for documentation
- AVOID investigationsummary - Field doesn't exist, causes failures

**Why This Matters:**
XSIAM has two-level structure: Cases (parent containers) and Issues (individual alerts).
Alert playbooks run on Issues. Using setIncident updates the wrong entity or fails entirely.

### Add War Room Entry
```yaml
# Use Print script for War Room notes (addEntries requires JSON, not plain text)
type: regular
script: Print
scriptarguments:
  value:
    simple: "Case findings documented. Investigation complete."
description: "Document findings in War Room"
```

---

## Response Plan Blocks

### Containment Plan
```yaml
type: playbook
playbookName: Containment Plan
inputs:
  - AutoContainment: "true"
  - HostAutoContainment: "true"
  - FileRemediation: "Quarantine"
outputs:
  - ContainmentStatus
```

### Eradication Plan
```yaml
type: playbook
playbookName: Eradication Plan
inputs:
  - AutoEradication: "false"
outputs:
  - EradicationStatus
```

### Recovery Plan
```yaml
type: playbook
playbookName: Recovery Plan
inputs:
  - AutoRecovery: "false"
outputs:
  - RecoveryStatus
```

---

## Modern XQL Query Blocks

### Search for File Hash
```yaml
type: regular
script: '|||xdr-xql-generic-query'
scriptarguments:
  query_name:
    simple: file_hash_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.FILE
    | filter action_file_sha256 = "${File.SHA256}"
    | fields _time, agent_hostname, action_file_path, actor_effective_username
    | sort desc _time
    | limit 100
  time_frame:
    simple: 30 days
description: "Search for file hash execution across environment"
```

### Search for Process Execution
```yaml
type: regular
script: '|||xdr-xql-generic-query'
scriptarguments:
  query_name:
    simple: process_execution_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.PROCESS
    | filter action_process_image_name = "${ProcessName}"
    | fields _time, agent_hostname, action_process_image_command_line
    | sort desc _time
    | limit 50
  time_frame:
    simple: 7 days
description: "Find process executions"
```

---

## XQL Query Best Practices

### CRITICAL: Required Parameters for xdr-xql-generic-query

**ALL XQL queries MUST include these parameters:**
1. **query_name** - Unique identifier (lowercase, underscores) - REQUIRED
2. **query** - The XQL query itself - REQUIRED
3. **time_frame** - Relative time range - REQUIRED

**Failure to include query_name will cause playbook execution error:**
```
Missing argument **query_name** for script **xdr-xql-generic-query**
```

**Minimal Valid Example:**
```yaml
scriptarguments:
  query_name:
    simple: my_threat_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.PROCESS
    | limit 100
  time_frame:
    simple: 30 days
```

### XQL Testing Workflow (RECOMMENDED)

**ALWAYS test XQL queries before adding to playbooks using the run_xql_query MCP tool:**

**Step 1 - Test with MCP tool:**
```python
run_xql_query(
    query='''
    dataset = xdr_data
    | filter event_type = ENUM.PROCESS
    | filter action_process_image_name = "mimikatz.exe"
    | fields _time, agent_hostname, action_process_image_command_line
    | limit 10
    ''',
    time_frame="7 days"
)
```

**Step 2 - Verify results, check field names, confirm syntax**

**Step 3 - Add to playbook ONLY after validation**

This prevents runtime errors from invalid field names or syntax issues.

### Common XQL Field Name Mistakes

| Wrong Field Name | Correct Field Name | Notes |
|-----------------|-------------------|-------|
| `action_process_command_line` | `action_process_image_command_line` | Most common error |
| `action_command_line` | `action_process_image_command_line` | Missing process_image |
| `process_command_line` | `action_process_image_command_line` | Missing action and image |
| `file_sha256` | `action_file_sha256` or `actor_process_image_sha256` | Depends on context |
| `hostname` | `agent_hostname` | Agent-specific field |
| `os_type` | `operating_system` | Endpoints dataset — NOT os_type |
| `ip` | `ip_address` | Endpoints dataset — returns array |
| `users` | `user` | Endpoints dataset — singular, not plural |

### Endpoints Dataset Schema Reference

**CRITICAL: Use `dataset = endpoints` (NOT `preset = endpoints`) in XQL queries run via xdr-xql-generic-query.**

The `preset =` syntax works in the XSIAM UI but causes 500 errors when executed through the XSOAR integration command.

**Common fields (verified on production tenant):**
```
endpoint_name, endpoint_id, endpoint_type, endpoint_status,
operating_system, os_version, ip_address, mac_address,
user, domain, agent_version, platform, last_seen,
content_version, content_status, is_edr_enabled,
encryption_status, network_location, endpoint_isolated,
assigned_prevention_policy, assigned_extensions_policy,
operational_status, scan_status, agent_license_type,
install_date, first_seen, last_successful_scan
```

**Example — Get all endpoints:**
```yaml
scriptarguments:
  query_name:
    simple: endpoint_inventory
  query: |
    dataset = endpoints
    | fields endpoint_name, endpoint_id, endpoint_type, endpoint_status,
             operating_system, ip_address, user, domain, agent_version,
             platform, last_seen
    | limit 20
  time_frame:
    simple: 30 days
```

**Best Practice:** Always reference XDM schema documentation or test queries first

### Error Handling: skipunavailable Parameter

**CRITICAL PARAMETER - Controls Whether Tasks Execute or Skip**

**Default Behavior:** `skipunavailable: false` (task MUST execute)

**When to use skipunavailable: true (Explicitly Skip if Unavailable):**
**Optional sub-playbooks** - Playbook might not be installed
   ```yaml
   type: playbook
   playbookName: Optional External Enrichment
   skipunavailable: true  # OK - playbook is optional
   ```

**Optional integrations** - Integration might not be configured
   ```yaml
   type: regular
   script: '|||optional-integration-command'
   skipunavailable: true  # OK - integration is optional
   ```

**Non-critical enrichment** - Nice-to-have, not required for workflow
   ```yaml
   type: playbook
   playbookName: VirusTotal File Enrichment
   skipunavailable: true  # OK - enrichment is optional
   ```

**When to use skipunavailable: false (DEFAULT - Task Must Run):**
**ALL XQL queries** - Queries should execute, never skip
**ALL regular commands** - Commands must run for proper workflow
**ALL scripts** - Scripts are part of core logic
**Critical tasks** - Required for investigation/remediation

**CRITICAL WARNING:**
Setting `skipunavailable: true` on regular/command tasks causes them to **SKIP ENTIRELY** - they will NOT execute!

**Common Mistake - XQL Query Skipping:**
```yaml
# WRONG - Query will SKIP, not execute!
script: '|||xdr-xql-generic-query'
skipunavailable: true  # Query skips entirely!

# CORRECT - Query executes
script: '|||xdr-xql-generic-query'
skipunavailable: false  # Query runs
```

**Best Practice:** When in doubt, use `skipunavailable: false` (or omit - false is default)

### Error Paths: Handling Task Failures Gracefully (XSOAR 6.8+)

**CRITICAL FEATURE - Prevents Playbook Halting on Errors**

By default, when a task fails (command returns error), the playbook **STOPS**.
Error paths allow you to handle failures gracefully and continue execution.

**How Error Paths Work:**

1. Set `continueonerror: true` on the task
2. Add `#error#` branch in nexttasks
3. When task fails → follows `#error#` path
4. When task succeeds → follows `#none#` path

**Basic Pattern:**
```yaml
type: regular
continueonerror: true        # REQUIRED: Allow error handling
continueonerrortype: ""
nexttasks:
  '#none#':                   # Success path
  - "next_task"
  '#error#':                  # Error path (when command fails)
  - "error_handler_task"
script: '|||core-isolate-endpoint'
scriptarguments:
  endpoint_id: ${inputs.endpoint_id}
```

**Complete Example - Containment with Error Handling:**
```yaml
# Task 4: Isolate Endpoint (may fail if endpoint offline)
"4":
  continueonerror: true
  continueonerrortype: ""
  nexttasks:
    '#none#':
    - "5"           # Success: proceed to next stage
    '#error#':
    - "7"           # Error: go to error handler
  scriptarguments:
    endpoint_id:
      simple: ${inputs.endpoint_id}
  task:
    name: Isolate Compromised Endpoint
    script: '|||core-isolate-endpoint'
    iscommand: true
    type: regular

# Task 7: Error Handler
"7":
  nexttasks:
    '#none#':
    - "5"           # Continue to next stage after logging
  scriptarguments:
    value:
      simple: |
        ERROR: Endpoint isolation failed for ${inputs.endpoint_id}
        Reason: Endpoint may be offline or unreachable
        Action: Manual intervention required
  task:
    name: Log Isolation Failure
    script: Print
    type: regular
```

**When to Use Error Paths:**

**Containment actions** - Endpoints may be offline
```yaml
script: '|||core-isolate-endpoint'
continueonerror: true
nexttasks:
  '#error#': ["log_isolation_failure"]
```

**File operations** - Files may be locked or missing
```yaml
script: '|||core-quarantine-files'
continueonerror: true
nexttasks:
  '#error#': ["log_quarantine_failure"]
```

**Process termination** - Process may have already exited
```yaml
script: '|||core-terminate-causality'
continueonerror: true
nexttasks:
  '#error#': ["continue_anyway"]
```

**External API calls** - Services may be unavailable
```yaml
script: '|||external-enrichment-api'
continueonerror: true
nexttasks:
  '#error#': ["skip_enrichment"]
```

**Recovery/cleanup actions** - Final steps that shouldn't block completion
```yaml
script: '|||core-unisolate-endpoint'
continueonerror: true
nexttasks:
  '#error#': ["complete_playbook"]  # Continue to completion
```

**Error Path vs skipunavailable:**

| Feature | `continueonerror: true` | `skipunavailable: true` |
|---------|------------------------|-------------------------|
| **Purpose** | Handle runtime errors | Skip if command/playbook missing |
| **When triggered** | Command fails with error | Command/playbook not installed |
| **Routing** | Routes to `#error#` path | Skips task entirely |
| **Use case** | Expected failures (offline endpoint) | Optional integrations |

**Common Mistakes:**

**Missing continueonerror:**
```yaml
# ERROR: Playbook stops if task fails!
nexttasks:
  '#none#': ["5"]
  '#error#': ["7"]   # This branch NEVER executes without continueonerror!
script: '|||core-isolate-endpoint'
```

**Correct - include continueonerror:**
```yaml
continueonerror: true   # REQUIRED for #error# to work
nexttasks:
  '#none#': ["5"]
  '#error#': ["7"]      # Now this branch works
script: '|||core-isolate-endpoint'
```

**Error handler stops playbook:**
```yaml
# Task 7 - Error handler that doesn't continue
"7":
  task:
    name: Log Error
    script: Print
  # No nexttasks! Playbook stops here
```

**Error handler continues:**
```yaml
# Task 7 - Error handler that continues
"7":
  nexttasks:
    '#none#': ["5"]   # Continue to next stage
  task:
    name: Log Error
    script: Print
```

**Multi-Stage Error Handling Pattern:**

For complex containment playbooks, add error paths to each critical stage:

```yaml
# Stage 1: Isolation
Task 4 (Isolate) → Success → Stage 2
                 → Error → Task 7 (Log) → Stage 2

# Stage 2: Quarantine
Task 10 (Quarantine) → Success → Stage 3
                     → Error → Task 13 (Log) → Stage 3

# Stage 3: Termination
Task 17 (Terminate) → Success → Stage 4
                    → Error → Stage 4 (continue anyway)

# Stage 4: Blocklist
Task 21 (Blocklist) → Success → Completion
                    → Error → Completion (continue anyway)
```

**Best Practice Summary:**

1. Always add `continueonerror: true` when using `#error#` paths
2. Error handlers should continue to next stage (not dead-end)
3. Use error paths for actions that may legitimately fail
4. Log errors for audit trail before continuing
5. Consider whether failure should block subsequent stages
6. Don't use error paths for critical validation that MUST succeed

---

### SLA and Timer Management in XSIAM

**IMPORTANT:** XSIAM SLA architecture differs significantly from XSOAR!

#### XSIAM Native Timer Fields (Cases Only)

Cases have built-in timer fields that work automatically:

```json
"custom_fields": {
  "timetoassign": {
    "runStatus": "running",    // "running" or "idle"
    "startDate": "2026-01-22 22:05:48"
  },
  "timetoresolve": {
    "runStatus": "idle"        // Starts when owner assigned
  },
  "sla": {
    "goal": "00:05:00",
    "goalName": "All Incidents"
  }
}
```

**Native Timers:**
- `timetoassign` - Starts at case creation, stops when owner assigned
- `timetoresolve` - Starts when owner assigned, stops when resolved
- Configure in: **Settings → Cases → Case SLAs**
- NO playbook configuration needed - these are automatic!

**Issues do NOT have native timer fields** - only basic fields (status, severity, assigned_to).

---

#### Task-Level SLAs (Collection Tasks)

Collection tasks have built-in SLA properties that work without custom fields:

```yaml
"4":
  type: collection
  sla:                    # Task deadline
    days: 0
    hours: 2              # 2-hour SLA for this task
    minutes: 0
    weeks: 0
  slareminder:            # Warning notification
    days: 0
    hours: 0
    minutes: 90           # Notify 90 mins before deadline (75%)
    weeks: 0
  form:
    title: Complete Triage Assessment
    description: |-
      Complete the triage within the SLA deadline.
      Timer starts when task activates.
    questions:
    - id: "0"
      labelarg:
        simple: Assessment Complete?
      optionsarg:
      - simple: "Yes - Proceed"
      - simple: "No - Need More Time"
      type: singleSelect
      required: true
  task:
    name: Complete Triage Assessment
    type: collection
```

**Key Properties:**
- `sla:` - Deadline for task completion (hours/minutes/days/weeks)
- `slareminder:` - When to send warning notification
- Timer starts automatically when task becomes active
- Timer stops when form is submitted

---

#### SLA Best Practices

**For Case-Level Metrics (MTTR, Time to Assignment):**
- Use XSIAM native case timers (timetoassign, timetoresolve)
- Configure in Settings → Cases → Case SLAs
- No playbook work needed

**For Phase-Level Tracking (Triage SLA, Investigation SLA):**
- Use collection task `sla:` property
- Set `slareminder:` at 50-75% of deadline
- Works out of the box - no custom fields needed

**Recommended SLA Reminder Timing:**
| SLA Duration | Reminder At |
|--------------|-------------|
| 5 minutes    | 3 minutes (60%) |
| 30 minutes   | 20 minutes (67%) |
| 2 hours      | 90 minutes (75%) |
| 8 hours      | 6 hours (75%) |
| 24 hours     | 18 hours (75%) |

**Example: Two-Phase SLA Workflow:**
```yaml
# Phase 1: Triage (5 min SLA)
"4":
  type: collection
  sla:
    minutes: 5
  slareminder:
    minutes: 3
  form:
    title: Complete Triage
  nexttasks:
    '#none#': ["5"]

# Phase 2: Investigation (10 min SLA)
"6":
  type: collection
  sla:
    minutes: 10
  slareminder:
    minutes: 5
  form:
    title: Complete Investigation
  nexttasks:
    '#none#': ["7"]
```

**XSOAR vs XSIAM SLA Differences:**

| Feature | XSOAR | XSIAM |
|---------|-------|-------|
| Case timers | Manual custom fields | Native (timetoassign, timetoresolve) |
| Timer triggers | Required for custom fields | Only for custom fields |
| Collection task SLA | Built-in | Built-in |
| Custom SLA fields | Create in Settings | Create in Settings (same) |
| Auto-start/stop | Via timertriggers | Native + timertriggers |

---

### XQL Query Patterns for Malware Investigation

#### Credential Dumping Detection
```yaml
scriptarguments:
  query_name:
    simple: credential_dumping_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.PROCESS
    | filter action_process_image_name in ("mimikatz.exe", "cachedump.exe", "pwdump.exe", "procdump.exe")
      or action_process_image_command_line contains "sekurlsa"
      or action_process_image_command_line contains "lsadump"
    | fields _time, agent_hostname, action_process_image_name, action_process_image_command_line, actor_effective_username
    | sort desc _time
    | limit 50
  time_frame:
    simple: 30 days
```

#### Lateral Movement Detection
```yaml
scriptarguments:
  query_name:
    simple: lateral_movement_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.NETWORK
    | filter action_remote_port in (445, 135, 139, 3389, 5985, 5986)
    | fields _time, agent_hostname, action_remote_ip, action_remote_port, actor_effective_username
    | dedup action_remote_ip
    | limit 50
  time_frame:
    simple: 7 days
```

#### Process Injection Detection
```yaml
scriptarguments:
  query_name:
    simple: process_injection_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.PROCESS
    | filter action_process_image_name in ("regsvr32.exe", "rundll32.exe", "mshta.exe")
      or causality_actor_process_image_name in ("WINWORD.EXE", "EXCEL.EXE", "powershell.exe")
    | fields _time, agent_hostname, causality_actor_process_image_name, action_process_image_name, action_process_image_command_line
    | sort desc _time
    | limit 50
  time_frame:
    simple: 7 days
```

#### Ransomware Indicators
```yaml
scriptarguments:
  query_name:
    simple: ransomware_hunt
  query: |
    dataset = xdr_data
    | filter event_type = ENUM.FILE
    | filter action_file_name ~= ".*\\.(encrypted|locked|crypt|enc)$"
      or action_file_name contains "DECRYPT"
      or action_file_name contains "README"
    | fields _time, agent_hostname, action_file_path, action_file_name
    | sort desc _time
    | limit 100
  time_frame:
    simple: 7 days
```

---

## SlackBlockBuilder - Advanced Block Kit with Form Capture

### Overview

SlackBlockBuilder is the recommended approach for stunning Block Kit messages that capture
dropdown selections, user pickers, and other form inputs - NOT just button clicks.

**When to use SlackBlockBuilder:**
- Need user pickers (users_select)
- Need dropdowns (static_select)
- Need multi-select, date pickers, time pickers
- Want professional Block Kit visuals
- Need to capture ALL form values (not just which button)

**When to use SlackAskV2 instead:**
- Simple button choices (Yes/No, Approve/Reject)
- Don't need form inputs
- Button text directly routes playbook

### CRITICAL: No API Key Needed!

Despite documentation suggesting "XSOAR API Key" is required, **it's NOT actually used**.
SlackBlockBuilder v3.3.0+ uses war room entries instead of API callbacks.

**Requirements:**
- App Token (xapp-...) - enables Socket Mode
- Long Running Instance - enabled
- Bot Token (xoxb-...) - for sending messages

### SlackBlockBuilder Workflow Pattern

```yaml
# Task 3: Send Block Kit message with SlackBlockBuilder
"3":
  type: regular
  scriptName: SlackBlockBuilder
  scriptarguments:
    blocks_url:
      simple: "https://app.slack.com/block-kit-builder#%7B%22blocks%22:..."
    channel_id:
      simple: "C0A9GLWQPPY"  # Use channel_id, not channel name
    task:
      simple: "4"  # Points to condition task
    reply:
      simple: "Response received"
  nexttasks:
    '#none#': ["4"]

# Task 4: Condition - waits for Submit click
"4":
  type: condition
  task:
    name: Wait for Slack Response
    description: Entitlement closes this when user clicks Submit
  nexttasks:
    '#default#': ["5"]  # SlackBlockBuilder uses #default#

# Task 5: Parse response with GetSlackBlockBuilderResponse
"5":
  type: regular
  scriptName: GetSlackBlockBuilderResponse
  nexttasks:
    '#none#': ["6"]

# Task 6: Use captured values
"6":
  type: regular
  script: Print
  scriptarguments:
    value:
      simple: |
        Selected user: ${SlackBlockState.values.users_select_0.users_select0.selected_user}
        Selected action: ${SlackBlockState.values.static_select_1.static_select1.selected_option.value}
```

### Block Kit URL Encoding

The `blocks_url` parameter is a URL from Slack's Block Kit Builder with encoded JSON.

**Example Block Kit with user picker + dropdown:**
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "🚨 Security Alert", "emoji": true}
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Issue:*\\n${incident.id}"},
        {"type": "mrkdwn", "text": "*Severity:*\\n${incident.severity}"}
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*Assign to analyst:*"},
      "accessory": {
        "type": "users_select",
        "placeholder": {"type": "plain_text", "text": "Select user"},
        "action_id": "user-select"
      }
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*Action:*"},
      "accessory": {
        "type": "static_select",
        "placeholder": {"type": "plain_text", "text": "Choose action"},
        "options": [
          {"text": {"type": "plain_text", "text": "Approve"}, "value": "approve"},
          {"text": {"type": "plain_text", "text": "Investigate"}, "value": "investigate"},
          {"text": {"type": "plain_text", "text": "Escalate"}, "value": "escalate"}
        ],
        "action_id": "action-select"
      }
    }
  ]
}
```

### SlackBlockState Context Structure

After GetSlackBlockBuilderResponse, access values via:

```yaml
# User picker value (Slack user ID)
${SlackBlockState.values.users_select_0.users_select0.selected_user}

# Dropdown selected option value
${SlackBlockState.values.static_select_1.static_select1.selected_option.value}

# Dropdown selected option text
${SlackBlockState.values.static_select_1.static_select1.selected_option.text.text}

# Submit button status
${SlackBlockState.xsoar-button-submit}  # Returns "Successful"
```

**Context path pattern:**
`${SlackBlockState.values.<block_id>.<action_id>.<property>}`

### How SlackBlockBuilder Works Internally

1. **SlackBlockBuilder** parses blocks_url and extracts Block Kit JSON
2. **Auto-adds Submit button** with action_id: "xsoar-button-submit"
3. **Injects entitlement** into Submit button value
4. **Sends via send-notification** to SlackV3
5. **User fills form** and clicks Submit
6. **SlackV3 (Socket Mode)** receives interaction
7. **Writes response** to war room as entry containing "xsoar-button-submit"
8. **GetSlackBlockBuilderResponse** searches war room for that entry
9. **Parses JSON** and populates SlackBlockState context

### SlackBlockBuilder vs SlackAskV2 Comparison

| Feature | SlackAskV2 | SlackBlockBuilder |
|---------|-----------|-------------------|
| Button clicks | Captured | Captured |
| User picker | Display only | Captured |
| Dropdowns | Display only | Captured |
| Multi-select | Not supported | Captured |
| Date picker | Not supported | Captured |
| Routing | Button text = nexttask | Use #default# |
| Parse script | Not needed | GetSlackBlockBuilderResponse |
| Complexity | Simpler | More powerful |

---

## Slack/Email Interactive Blocks - Sub-Playbook Pattern

### CRITICAL: Tags Required for Sub-Playbook Entitlements

When using SlackAsk or EmailAsk commands in **sub-playbooks** (playbooks called from other playbooks),
you MUST add tags to the conditional wait task. Without tags, the entitlement cannot find the correct
task to close when running in a sub-playbook context.

**Pattern:**
```yaml
# Task 1: SlackAsk/EmailAsk - Specifies task parameter
type: regular
scriptName: SlackAskV2
scriptarguments:
  task:
    simple: "my-playbook-wait-4"  # MUST match tag exactly!
  channel:
    simple: "team-channel"
  message:
    simple: "Approve this action?"
  option1: "Yes#green"
  option2: "No#red"

# Task 4: Conditional Wait - MUST have matching tag
type: condition
task:
  name: Wait for Response
tags:
  - "my-playbook-wait-4"  # Tag MUST match task parameter!
nexttasks:
  "Yes": ["10"]
  "No": ["20"]
```

**Why This is Required:**

In **main playbooks** (top-level):
- Entitlement uses investigation_id to find task
- Works without tags

In **sub-playbooks** (nested):
- Sub-playbook runs in separate context
- Entitlement cannot find task by investigation_id alone
- Tags provide the lookup mechanism

**Naming Convention:**
- Format: `{playbook-name}-wait-{task-id}`
- Example: `team-escalation-wait-4`
- Lowercase, hyphens instead of spaces
- Must be unique per playbook

**Auto-Generation Pattern:**
```python
# Playbook builder automatically generates:
task_param = f"{playbook_name.lower().replace(' ', '-')}-wait-{task_id}"

# SlackAsk scriptarguments:
scriptarguments:
  task:
    simple: "{playbook_name}-wait-{task_id}"

# Condition tags:
tags:
  - "{playbook_name}-wait-{task_id}"
```

**Complete Working Example - Sub-Playbook:**
```yaml
id: team-escalation-subplaybook
name: Team Escalation [Nested]
tasks:
  "3":
    # Send interactive message
    type: regular
    scriptName: SlackAskV2
    scriptarguments:
      channel:
        simple: "security-team"
      message:
        simple: "Is this alert a false positive?"
      option1: "Yes - False Positive#green"
      option2: "No - Real Threat#red"
      task:
        simple: "team-escalation-subplaybook-wait-4"  # Tag reference
      lifetime:
        simple: "4 hours"
    nexttasks:
      '#none#': ["4"]

  "4":
    # Wait for user response
    type: condition
    task:
      name: Wait for Team Response
      description: Entitlement closes this task
    tags:
      - "team-escalation-subplaybook-wait-4"  # CRITICAL: Matches task parameter!
    nexttasks:
      "Yes - False Positive": ["10"]
      "No - Real Threat": ["20"]
      '#default#': ["30"]

  "10":
    # Handle false positive
    type: regular
    script: '|||send-notification'
    scriptarguments:
      message:
        simple: "Marked as false positive"

  "20":
    # Handle real threat
    type: regular
    script: '|||send-notification'
    scriptarguments:
      message:
        simple: "🚨 Escalating to incident response"
```

**Common Mistakes:**

**Missing tag entirely:**
```yaml
type: condition
task:
  name: Wait
# ERROR: No tags! Entitlement will fail in sub-playbook
nexttasks:
  "Yes": ["10"]
```

**Tag doesn't match task parameter:**
```yaml
scriptarguments:
  task:
    simple: "wait-task-4"  # One name

tags:
  - "my-playbook-wait-4"  # Different name - ERROR!
```

**Using task ID instead of tag:**
```yaml
scriptarguments:
  task:
    simple: "4"  # Just the task ID - works in main, fails in sub!
```

**Correct pattern:**
```yaml
scriptarguments:
  task:
    simple: "my-playbook-wait-4"  # Full tag name

tags:
  - "my-playbook-wait-4"  # Exact match
```

**Testing Sub-Playbook Entitlements:**

1. Create parent playbook that calls your sub-playbook
2. Run parent playbook
3. Check if Slack/Email message appears
4. Click button in Slack/Email
5. Verify sub-playbook task closes correctly
6. If task doesn't close: Check tag matches task parameter exactly

**Automation Note:**

The `create_playbook` MCP tool automatically detects SlackAsk/EmailAsk tasks
and adds appropriate tags to referenced conditional tasks when generating playbooks.

---

## Notification Blocks

### Send Email Notification
```yaml
type: regular
script: '|||send-mail'
scriptarguments:
  to: "security-team@company.com"
  subject: "XSIAM Security Issue: ${issue.name}"
  body: "Issue ${issue.id} requires attention. Severity: ${issue.severity}"
description: "Notify security team"
```

### Microsoft Teams Message
```yaml
type: regular
script: '|||send-notification'
scriptarguments:
  message: "XSIAM Issue ${issue.id}: ${issue.name}"
  channel: "security-issues"
description: "Post to Teams channel"
```

---

## Collection Blocks (User Input Forms)

### Analyst Decision with Manual Approval
```yaml
type: collection
task:
  id: decision-task-uuid
  version: -1
  name: Analyst Decision - Terminate Process?
  description: Manual decision to terminate malicious process
  type: collection
  iscommand: false
  brand: ''
nexttasks:
  '#none#':
  - next_task_id
separatecontext: false
message:
  body:
    simple: 'Process Details:\n\n- Process: ${incident.processname}\n- Command Line: ${incident.commandline}\n- Host: ${incident.hostname}\n\nDo you want to terminate this process and its entire causality chain?'
  replyOptions:
  - 'Yes - Terminate Process'
  - 'No - Skip Termination'
form:
  questions:
  - id: '0'
    labelarg:
      simple: Terminate Malicious Process?
    required: false
    type: singleSelect
    optionsarg:
    - simple: 'Yes - Terminate Process'
    - simple: 'No - Skip Termination'
  title: Analyst Decision - Terminate Process?
  description: Review the process details and decide whether to terminate
view: |-
  {
    "position": {
      "x": 450,
      "y": 1200
    }
  }
note: false
ignoreworker: false
skipunavailable: false
quietmode: 0
```

### War Room Documentation
```yaml
type: regular
script: '|||addEntries'
scriptarguments:
  entries:
    simple: 'Investigation findings documented. Threat hunting queries completed successfully.'
description: "Document findings in War Room"
```

**IMPORTANT - addEntries Best Practices:**
- Avoid markdown headers (#) in text with context variables
- Keep entries simple and clean
- Use plain text descriptions instead of complex formatting

**Wrong (causes errors):**
```yaml
entries:
  simple: '### Results: ${File.SHA256}\n\n**Count**: ${File.count}'
```

**Correct:**
```yaml
entries:
  simple: 'Investigation complete. Files analyzed and documented in context.'
```

---

## Summary: Modern Command Reference

| Old Demisto (Deprecated) | Modern XSOAR/XSIAM (2025) | Status |
|--------------------------|---------------------------|--------|
| N/A | `core-isolate-endpoint` | XSIAM 2.4+ |
| N/A | `core-quarantine-files-quick-action` | XSIAM 2.4+ |
| N/A | `core-terminate-causality-quick-action` | XSIAM 2.4+ |
| `closeCase` | `closeCase` | Still Current |
| `setIncident` | `setIncident` | Still Current |
| N/A | `xdr-xql-generic-query` | Modern |
| `getDemistoVersion` | `core-api-get` | Migrated |

**Key Takeaway**: `closeCase` and `setIncident` are **CURRENT** commands, still used in XSIAM 2025!
"""


async def get_playbook_building_blocks(
    ctx: Context,
    category: Annotated[Optional[str], Field(
        description="Filter by category: 'enrichment', 'containment', 'investigation', 'closure', 'transformers', 'all'. Default: 'all'",
        default="all"
    )] = "all"
) -> str:
    """
    Get modern XSOAR/XSIAM playbook building blocks library.

    Returns comprehensive reference of modern playbook components:
    - Enrichment blocks (file, IP, domain, email)
    - Containment blocks (isolate, quarantine, terminate)
    - Case plans
    - Decision/condition blocks
    - Closure blocks with modern commands
    - Response plan sub-playbooks
    - XQL query blocks
    - Notification blocks

    All blocks use current XSOAR/XSIAM commands (not outdated Demisto).
    Based on PANW official content repository and XSIAM 2.4+ best practices.

    Use this tool when:
    - Creating new playbooks
    - Need reference for modern commands
    - Building case automation
    - Implementing response workflows

    Returns: Complete building blocks reference with modern YAML examples
    """
    return PLAYBOOK_BUILDING_BLOCKS


class PlaybookBlocksModule(BaseModule):
    """
    Playbook Building Blocks Module

    Provides modern XSOAR/XSIAM playbook building blocks as a reference tool.
    All blocks use current commands and follow XSIAM 2.4+ best practices.

    Tools provided:
        - get_playbook_building_blocks: Complete reference library
    """

    def register_tools(self):
        self._add_tool(get_playbook_building_blocks)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
