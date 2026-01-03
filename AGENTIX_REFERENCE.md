# AgentIX Content Types Reference

Complete reference for creating AgentIX Actions and Agents in XSIAM.

**Last Updated**: January 3, 2026
**Sources**: demisto-sdk repository, schema files, test examples

---

## Table of Contents

1. [AgentIX Actions](#agentix-actions)
2. [AgentIX Agents](#agentix-agents)
3. [File Structure](#file-structure)
4. [Field Reference](#field-reference)
5. [Examples](#examples)

---

## AgentIX Actions

AgentIX Actions wrap existing XSOAR commands, scripts, or playbooks to make them available to AI agents with natural language interfaces.

### File Location

```
Packs/{PackName}/AgentixActions/{ActionName}.yml
```

**Naming Convention**:
- Directory: `AgentixActions` (exact capitalization required)
- File: `{ActionName}.yml` (YAML format, not JSON)
- Example: `Packs/MyPack/AgentixActions/CVEEnrichment.yml`

### Minimal Example

```yaml
commonfields:
  id: CVEEnrichment
  version: -1
name: CVEEnrichment
display: CVE Enrichment
description: Enriches CVE identifiers with threat intelligence data.
underlyingcontentitem:
  id: CVE
  name: cve
  type: command
  version: -1
  command: cve
marketplaces:
  - platform
supportedModules:
  - agentix
```

### Complete Example with All Fields

```yaml
commonfields:
  id: CVEEnrichmentFull
  version: -1
name: CVEEnrichmentFull
display: CVE Enrichment - Full Featured
description: |-
  Enriches CVE identifiers with comprehensive threat intelligence.
  Provides CVSS scores, descriptions, publication dates, and more.
category: Data Enrichment & Threat Intelligence
tags:
  - cve
  - vulnerability
  - threat intelligence
  - security
  - enrichment
args:
  - name: cve
    description: One or more CVE identifiers (e.g., CVE-2014-1234, CVE-2020-0601)
    type: string
    required: true
    underlyingargname: cve
  - name: detailed
    description: Return detailed vulnerability information
    type: boolean
    required: false
    defaultvalue: "false"
    hidden: false
    disabled: false
    underlyingargname: detailed
    isgeneratable: false
outputs:
  - name: Indicator
    description: The CVE identifier that was tested.
    type: string
    underlyingoutputcontextpath: DBotScore.Indicator
    disabled: false
  - name: Vendor
    description: The vendor used to calculate the score.
    type: string
    underlyingoutputcontextpath: DBotScore.Vendor
  - name: CVE.ID
    description: The CVE ID.
    type: string
    underlyingoutputcontextpath: CVE.ID
  - name: CVE.Description
    description: Description of the CVE.
    type: string
    underlyingoutputcontextpath: CVE.Description
  - name: CVE.CVSS
    description: The CVSS score (0.0-10.0).
    type: number
    underlyingoutputcontextpath: CVE.CVSS
  - name: CVE.Published
    description: Date the CVE was published.
    type: date
    underlyingoutputcontextpath: CVE.Published
  - name: CVE.Modified
    description: Date the CVE was last modified.
    type: date
    underlyingoutputcontextpath: CVE.Modified
underlyingcontentitem:
  id: CVE
  name: cve
  type: command
  version: -1
  command: cve
requiresuserapproval: false
fewshots:
  - "Get CVE-2021-44228 details"
  - "What is the CVSS score for CVE-2020-0601?"
  - "Enrich CVE-2014-0160"
marketplaces:
  - platform
supportedModules:
  - agentix
```

---

## AgentIX Agents

AgentIX Agents are AI assistants configured with specific instructions, actions, and conversation starters.

### File Location

```
Packs/{PackName}/AgentixAgents/{AgentName}.yml
```

**Naming Convention**:
- Directory: `AgentixAgents` (exact capitalization required)
- File: `{AgentName}.yml` (YAML format, not JSON)
- Example: `Packs/MyPack/AgentixAgents/ThreatHunter.yml`

### Minimal Example

```yaml
commonfields:
  id: ThreatHunter
  version: -1
name: ThreatHunter
description: AI assistant for threat hunting and investigation.
color: "#FF5733"
visibility: public
marketplaces:
  - platform
supportedModules:
  - agentix
```

### Complete Example with All Fields

```yaml
commonfields:
  id: ThreatHunterFull
  version: -1
name: ThreatHunter
description: |-
  Advanced AI assistant specialized in threat hunting, incident investigation,
  and security analysis. Provides expert guidance on IOC enrichment, attack
  pattern detection, and remediation strategies.
color: "#FF5733"
visibility: public
category: Security Operations
tags:
  - threat-hunting
  - investigation
  - incident-response
  - security
actionids:
  - CVEEnrichment
  - IPEnrichment
  - DomainEnrichment
  - FileHashEnrichment
systeminstructions: |-
  You are a senior threat hunting analyst with expertise in:
  - IOC enrichment and analysis
  - Attack pattern recognition (MITRE ATT&CK)
  - Incident investigation workflows
  - Security tool orchestration

  When investigating incidents:
  1. Start by enriching all available IOCs
  2. Map observed behaviors to MITRE ATT&CK tactics
  3. Provide clear, actionable remediation steps
  4. Prioritize based on risk and impact
conversationstarters:
  - "Investigate this suspicious IP address"
  - "What CVEs should I prioritize this week?"
  - "Help me hunt for lateral movement in my environment"
  - "Analyze this file hash for malware indicators"
builtinactions:
  - search
  - query
  - analyze
autoenablenewactions: false
roles:
  - Administrator
  - Analyst
  - SOC Manager
sharedwithroles:
  - Analyst
  - SOC Manager
marketplaces:
  - platform
supportedModules:
  - agentix
```

---

## File Structure

### Pack Directory Structure

```
Packs/
└── MyPack/
    ├── pack_metadata.json
    ├── AgentixActions/
    │   ├── CVEEnrichment.yml
    │   ├── IPEnrichment.yml
    │   └── DomainEnrichment.yml
    └── AgentixAgents/
        ├── ThreatHunter.yml
        └── IncidentResponder.yml
```

### Pack Metadata Requirements

When creating AgentIX content, ensure `pack_metadata.json` includes:

```json
{
  "name": "MyPack",
  "marketplaces": ["platform"],
  "support": "community",
  "currentVersion": "1.0.0",
  "supportDetails": {},
  "modules": ["agentix"]
}
```

---

## Field Reference

### AgentIX Action Fields

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `commonfields.id` | string | Unique identifier | `CVEEnrichment` |
| `commonfields.version` | integer | Version number (use -1) | `-1` |
| `name` | string | Internal name | `CVEEnrichment` |
| `display` | string | Display name for UI | `CVE Enrichment` |
| `description` | string | Description of action | `Enriches CVE identifiers` |
| `underlyingcontentitem.id` | string | ID of underlying content | `CVE` |
| `underlyingcontentitem.name` | string | Name of underlying content | `cve` |
| `underlyingcontentitem.type` | string | Type: `command`, `script`, or `playbook` | `command` |
| `underlyingcontentitem.version` | integer | Version (use -1) | `-1` |
| `marketplaces` | array | Supported marketplaces | `["platform"]` |
| `supportedModules` | array | Supported modules | `["agentix"]` |

#### Optional Fields - Action

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `category` | string | - | Category for organization |
| `tags` | array | `[]` | Tags for discovery |
| `args` | array | `[]` | Input arguments |
| `outputs` | array | `[]` | Output fields |
| `requiresuserapproval` | boolean | `false` | Require approval before execution |
| `fewshots` | array | `[]` | Example prompts/queries |
| `underlyingcontentitem.command` | string | - | Command name (for type=command) |

#### Arguments Schema (args)

```yaml
args:
  - name: string           # Required: argument name
    description: string    # Required: argument description
    type: string          # Required: string, number, boolean, array
    required: boolean     # Required: is this arg required?
    underlyingargname: string  # Required: maps to underlying command arg
    defaultvalue: string  # Optional: default value
    hidden: boolean       # Optional: hide from UI (default: false)
    disabled: boolean     # Optional: disable this arg (default: false)
    isgeneratable: boolean # Optional: can AI generate this? (default: false)
```

**Argument Types**: `string`, `number`, `boolean`, `array`, `date`

#### Outputs Schema (outputs)

```yaml
outputs:
  - name: string           # Required: output field name
    description: string    # Required: output description
    type: string          # Required: string, number, boolean, date, array
    underlyingoutputcontextpath: string  # Required: maps to underlying output
    disabled: boolean     # Optional: disable this output (default: false)
```

**Output Types**: `string`, `number`, `boolean`, `date`, `array`

### AgentIX Agent Fields

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `commonfields.id` | string | Unique identifier | `ThreatHunter` |
| `commonfields.version` | integer | Version number (use -1) | `-1` |
| `name` | string | Agent name | `ThreatHunter` |
| `description` | string | Agent description | `AI threat hunting assistant` |
| `color` | string | Hex color code | `#FF5733` |
| `visibility` | string | `public` or `private` | `public` |
| `marketplaces` | array | Supported marketplaces | `["platform"]` |
| `supportedModules` | array | Supported modules | `["agentix"]` |

#### Optional Fields - Agent

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `category` | string | - | Category for organization |
| `tags` | array | `[]` | Tags for discovery |
| `actionids` | array | `[]` | List of AgentIX Action IDs |
| `systeminstructions` | string | `""` | System prompt/instructions |
| `conversationstarters` | array | `[]` | Suggested conversation starters |
| `builtinactions` | array | `[]` | Built-in action names |
| `autoenablenewactions` | boolean | `false` | Auto-enable new actions |
| `roles` | array | `[]` | Roles that can use this agent |
| `sharedwithroles` | array | `[]` | Roles that can view this agent |

#### Color Values

Hex color codes for agent UI appearance:
- Red: `#FF5733`, `#DC143C`
- Blue: `#3498DB`, `#1E90FF`
- Green: `#2ECC71`, `#228B22`
- Orange: `#FF8C00`, `#FFA500`
- Purple: `#9B59B6`, `#8A2BE2`
- Gray: `#95A5A6`, `#708090`

#### Visibility Values

- `public`: Visible to all users (within role restrictions)
- `private`: Only visible to creator/assigned users

---

## Examples

### Example 1: Simple IP Enrichment Action

```yaml
commonfields:
  id: IPEnrichment
  version: -1
name: IPEnrichment
display: IP Address Enrichment
description: Enriches IP addresses with threat intelligence and geolocation data.
category: Data Enrichment & Threat Intelligence
tags:
  - ip
  - enrichment
  - threat-intelligence
args:
  - name: ip
    description: IP address to enrich (IPv4 or IPv6)
    type: string
    required: true
    underlyingargname: ip
outputs:
  - name: IP
    description: The IP address
    type: string
    underlyingoutputcontextpath: IP.Address
  - name: Reputation
    description: IP reputation score
    type: string
    underlyingoutputcontextpath: DBotScore.Score
  - name: Country
    description: Country code
    type: string
    underlyingoutputcontextpath: IP.Geo.Country
underlyingcontentitem:
  id: ip
  name: ip
  type: command
  version: -1
  command: ip
marketplaces:
  - platform
supportedModules:
  - agentix
```

### Example 2: Script-Based Action

```yaml
commonfields:
  id: DetonateFile
  version: -1
name: DetonateFile
display: Detonate File in Sandbox
description: Submits a file to sandbox for detonation and analysis.
category: Forensics & Malware Analysis
args:
  - name: entry_id
    description: File entry ID from War Room
    type: string
    required: true
    underlyingargname: entryID
outputs:
  - name: Verdict
    description: Sandbox verdict (Malicious/Benign/Unknown)
    type: string
    underlyingoutputcontextpath: File.Malicious.Verdict
underlyingcontentitem:
  id: DetonateFileScript
  name: DetonateFileScript
  type: script
  version: -1
requiresuserapproval: true
marketplaces:
  - platform
supportedModules:
  - agentix
```

### Example 3: Playbook-Based Action

```yaml
commonfields:
  id: PhishingInvestigation
  version: -1
name: PhishingInvestigation
display: Investigate Phishing Email
description: Orchestrates comprehensive phishing email investigation workflow.
category: Investigation & Response
args:
  - name: email_id
    description: Email message ID or entry ID
    type: string
    required: true
    underlyingargname: emailID
outputs:
  - name: Verdict
    description: Investigation verdict
    type: string
    underlyingoutputcontextpath: Email.Investigation.Verdict
  - name: IOCs
    description: Extracted IOCs from email
    type: array
    underlyingoutputcontextpath: Email.Investigation.IOCs
underlyingcontentitem:
  id: PhishingInvestigationPlaybook
  name: Phishing Investigation - Generic
  type: playbook
  version: -1
requiresuserapproval: false
fewshots:
  - "Investigate suspicious email from sender@example.com"
  - "Analyze phishing email with subject 'Urgent: Verify your account'"
marketplaces:
  - platform
supportedModules:
  - agentix
```

### Example 4: SOC Analyst Agent

```yaml
commonfields:
  id: SOCAnalystAgent
  version: -1
name: SOC Analyst
description: |-
  AI-powered SOC analyst assistant that helps with alert triage,
  incident investigation, and threat hunting. Provides expert guidance
  based on MITRE ATT&CK framework and industry best practices.
color: "#3498DB"
visibility: public
category: Security Operations
tags:
  - soc
  - analyst
  - investigation
  - triage
actionids:
  - IPEnrichment
  - DomainEnrichment
  - FileHashEnrichment
  - CVEEnrichment
  - PhishingInvestigation
systeminstructions: |-
  You are an experienced SOC analyst with expertise in:

  - Alert triage and prioritization
  - Incident investigation using MITRE ATT&CK
  - IOC enrichment and correlation
  - Threat hunting methodologies
  - Forensic analysis techniques

  Investigation Workflow:
  1. Gather all available context (alerts, logs, IOCs)
  2. Enrich IOCs using available threat intelligence
  3. Map observed behaviors to MITRE ATT&CK tactics/techniques
  4. Determine scope and impact
  5. Provide actionable remediation recommendations

  Communication Style:
  - Be clear, concise, and actionable
  - Explain technical concepts in accessible terms
  - Prioritize findings by risk and impact
  - Provide confidence levels for assessments
conversationstarters:
  - "Help me triage this high-severity alert"
  - "Investigate suspicious network activity from 192.168.1.100"
  - "What are the latest critical vulnerabilities I should patch?"
  - "Analyze this file hash: abc123def456..."
builtinactions:
  - search
  - query
  - analyze
  - summarize
autoenablenewactions: false
roles:
  - Administrator
  - Analyst
  - SOC Manager
sharedwithroles:
  - Analyst
marketplaces:
  - platform
supportedModules:
  - agentix
```

---

## Key Differences from Other XSOAR Content

### File Format
- **AgentIX**: Uses `.yml` (YAML) format
- **Other Content**: May use `.json` or unified YAML structures

### Directory Names
- **AgentIX Actions**: `AgentixActions` (exact case)
- **AgentIX Agents**: `AgentixAgents` (exact case)
- **Case-sensitive**: Must match exactly

### Marketplace
- **Required**: Must include `platform` in marketplaces array
- **Module**: Must include `agentix` in supportedModules array

### Version
- **Convention**: Use `-1` for version fields (auto-incremented by system)

### Underlying Content Item
- **Purpose**: Links to existing command/script/playbook
- **Type values**: `command`, `script`, `playbook`
- **Command field**: Only required when type=`command`

---

## Validation Rules

Based on demisto-sdk validators:

1. **Marketplace**: Must be `platform` (AG101)
2. **Action Names**: Must be unique across all packs (GR112)
3. **Display Names**: Must be unique across all packs (GR111)
4. **Underlying Content**: Must reference existing content items (GR110)
5. **Types**: Arguments and outputs must use valid type values (AG105)
6. **Name Format**: Action names must follow naming conventions (AG106)
7. **Display Format**: Display names must be human-readable (AG107)
8. **Deployment**: AgentIX content should be deployed via content-test-conf, not content repo (AG100)

---

## Common Patterns

### Pattern 1: Enrichment Action
```yaml
# Enriches indicators (IP, domain, file, etc.)
underlyingcontentitem:
  type: command
  command: ip  # or domain, file, url, email, etc.
```

### Pattern 2: Analysis Action
```yaml
# Runs automated analysis
underlyingcontentitem:
  type: script
requiresuserapproval: true  # For destructive/expensive operations
```

### Pattern 3: Orchestration Action
```yaml
# Orchestrates complex workflows
underlyingcontentitem:
  type: playbook
fewshots:  # Help AI understand when to use this
  - "Run phishing investigation on email XYZ"
```

### Pattern 4: Specialized Agent
```yaml
# Domain-specific agent (threat hunting, forensics, compliance, etc.)
systeminstructions: |-
  [Detailed instructions about role, expertise, workflow]
conversationstarters:
  - [Example queries users can ask]
actionids:
  - [Curated list of relevant actions]
```

---

## Upload and Deployment

### Using demisto-sdk

```bash
# Validate AgentIX content
demisto-sdk validate -i Packs/MyPack/AgentixActions/CVEEnrichment.yml

# Upload to XSIAM (note: typically deployed via content-test-conf)
demisto-sdk upload -i Packs/MyPack
```

### Pack Structure Validation

Ensure your pack includes:
1. `pack_metadata.json` with `modules: ["agentix"]`
2. `AgentixActions/` directory (if creating actions)
3. `AgentixAgents/` directory (if creating agents)
4. Valid YAML syntax (use `yamllint` to check)

---

## Troubleshooting

### Common Issues

**Issue**: "Marketplace must be platform"
- **Solution**: Add `marketplaces: ["platform"]` to YAML

**Issue**: "Action name already exists"
- **Solution**: Use unique action ID across all packs

**Issue**: "Invalid underlying content item"
- **Solution**: Ensure referenced command/script/playbook exists

**Issue**: "Invalid argument type"
- **Solution**: Use valid types: string, number, boolean, array, date

**Issue**: "Directory not found"
- **Solution**: Use exact case: `AgentixActions`, `AgentixAgents`

---

## References

- **Schema Files**:
  - `/demisto-sdk/demisto_sdk/commands/common/schemas/agentixaction.yml`
  - `/demisto-sdk/demisto_sdk/commands/common/schemas/agentixagent.yml`
- **Test Examples**:
  - `/demisto-sdk/TestSuite/assets/default_agentix_action/agentix_action-sample.yml`
  - `/demisto-sdk/demisto_sdk/commands/validate/tests/AG_validators_test.py`
- **Parser Code**:
  - `/demisto-sdk/demisto_sdk/commands/content_graph/parsers/agentix_action.py`
  - `/demisto-sdk/demisto_sdk/commands/content_graph/parsers/agentix_agent.py`

---

**End of Reference Document**
