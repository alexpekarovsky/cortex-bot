# XSOAR/XSIAM Playbook Analysis
## Comprehensive Analysis of 22 Production Playbooks

**Date**: 2025-12-11
**Analyzed**: 22 production playbook YAML files
**Purpose**: Extract patterns, building blocks, and identify gaps for AI-powered playbook generation

---

## Executive Summary

**Playbooks Analyzed**: 22
- TIM - Process For EDL
- Block Account - Generic v2
- Block Indicators - Generic v3
- Calculate Severity - Generic v2
- Context Polling - Generic
- DBot Indicator Enrichment - Generic
- Phishing Investigation - Generic v2
- Endpoint Enrichment - Generic v2.1
- Dedup - Generic v4
- Detonate and Analyze File - Generic
- Email Headers Check - Generic
- Entity Enrichment - Generic v3
- Field Polling - Generic
- Get endpoint details - Generic
- Process Email - Generic v2
- Retrieve File from Endpoint - Generic
- Search And Delete Emails - Generic v2
- Search and Compare Process Executions - Generic
- Search Endpoints By Hash - Generic V2
- User Investigation - Generic
- Unisolate Endpoint - Generic
- Phishing - Generic v3

---

## CRITICAL TERMINOLOGY CORRECTIONS

### XSIAM vs XSOAR Terminology

**In XSIAM (the modern platform)**:
- **Issues** (NOT "alerts") - Individual security events
- **Cases** (NOT "incidents") - Collections of related issues
- Commands use `alert` context (e.g., `${alert.id}`, `${alert.severity}`)
- Modern pattern: `Builtin|||setAlert` command

**In XSOAR (the legacy platform)**:
- **Incidents** - Individual security events
- Commands use `incident` context (e.g., `${incident.id}`)
- Legacy pattern: `Builtin|||setIncident` command

**Evidence from playbooks**:
- Modern playbooks use `${alert.name}`, `${alert.severity}`, `${alert.emailto}`
- Commands: `Builtin|||setAlert`, `Builtin|||closeInvestigation`
- Inputs reference: `root: alert` in transformers

---

## Top 10 Most Common Building Blocks

### 1. **Condition Tasks** (Type: `condition`)
**Frequency**: Appears in ALL 22 playbooks
**Purpose**: Decision making, branching logic
**Common Patterns**:

```yaml
type: condition
task:
  name: Is there an endpoint to enrich?
  type: condition
  iscommand: false
nexttasks:
  '#default#':
    - "4"  # Default path (usually to Done/End)
  "yes":
    - "next_task_id"
conditions:
  - label: "yes"
    condition:
      - - operator: isNotEmpty
          left:
            value:
              simple: inputs.Hostname
            iscontext: true
```

**Common Operators**:
- `isNotEmpty` - Check if data exists
- `isEqualString` - String comparison
- `isExists` - Check if context key exists
- `greaterThanOrEqual` - Numeric comparison
- `containsGeneral` - Contains check
- `stringHasLength` - String length validation

**Linking Pattern**:
```yaml
nexttasks:
  '#default#':  # Fallback path
    - "task_id"
  "yes":         # Positive condition
    - "task_id"
  "No":          # Negative condition (note capital N)
    - "task_id"
  "Malicious":   # Custom labels
    - "task_id"
```

### 2. **Title Tasks** (Type: `title`)
**Frequency**: Every playbook (avg 3-5 per playbook)
**Purpose**: Visual organization, workflow sections

```yaml
type: title
task:
  name: Done
  type: title
  iscommand: false
separatecontext: false
nexttasks:
  '#none#':
    - "next_task_id"
```

**Common Titles**:
- "Done" / "End" - Playbook termination
- "Triage" - Initial analysis section
- "Investigation" - Deep dive section
- "Remediation" - Response actions
- "Enrichment" - Data gathering
- "Block Indicators" - Containment section

### 3. **Sub-Playbook Calls** (Type: `playbook`)
**Frequency**: 18 of 22 playbooks
**Purpose**: Modular workflow reuse

```yaml
type: playbook
task:
  name: Block File - Generic v2
  playbookName: Block File - Generic v2
  type: playbook
  iscommand: false
nexttasks:
  '#none#':
    - "next_task"
scriptarguments:
  Hash:
    complex:
      root: inputs.MD5
      transformers:
        - operator: uniq
separatecontext: true
loop:
  iscommand: false
  exitCondition: ""
  wait: 1
  max: 100
```

**Key Parameters**:
- `separatecontext: true` - Isolate sub-playbook context (most common)
- `separatecontext: false` - Share context with parent
- `loop.max: 100` - Maximum iterations
- `skipunavailable: true` - Continue if integration unavailable

**Common Sub-Playbooks**:
- Block IP - Generic v3
- Block File - Generic v2
- Block Account - Generic v2
- Search And Delete Emails - Generic v2
- Entity Enrichment - Generic v3
- Calculate Severity - Generic v2

### 4. **Integration Command Execution** (Type: `regular`)
**Frequency**: ALL playbooks
**Purpose**: Execute XSOAR/XSIAM commands

```yaml
type: regular
task:
  name: Get host information from Active Directory
  description: Retrieves detailed information about a computer account
  script: '|||ad-get-computer'
  type: regular
  iscommand: true
  brand: ""
nexttasks:
  '#none#':
    - "next_task"
scriptarguments:
  name:
    complex:
      root: inputs.Hostname
      transformers:
        - operator: uniq
separatecontext: false
skipunavailable: true
```

**Modern Command Patterns**:
```yaml
# Core/Built-in commands (no prefix)
script: Builtin|||setAlert
script: Builtin|||appendIndicatorField
script: Builtin|||closeInvestigation
script: Builtin|||extractIndicators

# Integration commands (prefix|||command)
script: '|||ad-get-computer'
script: '|||xdr-get-endpoints'
script: '|||cs-falcon-search-device'
script: '|||send-mail'
```

### 5. **Set Context Data** (Automation: `Set` / `SetAndHandleEmpty`)
**Frequency**: 20 of 22 playbooks
**Purpose**: Store data in context

```yaml
type: regular
task:
  name: Set indicators to block - Auto
  scriptName: Set
  type: regular
  iscommand: false
scriptarguments:
  key:
    simple: IndicatorsToBlock
  value:
    complex:
      root: inputs.IP
      transformers:
        - operator: append
          args:
            item:
              value:
                simple: inputs.URL
              iscontext: true
        - operator: uniq
separatecontext: false
```

**SetAndHandleEmpty** - Prevents empty value errors:
```yaml
scriptName: SetAndHandleEmpty
scriptarguments:
  append:
    simple: "true"
  key:
    simple: Blocklist.Final
  value:
    complex:
      root: inputs.Username
```

### 6. **Transformers** (Data Manipulation)
**Frequency**: ALL playbooks with complex data
**Purpose**: Transform, filter, format data

**Most Common Transformers**:

```yaml
# 1. uniq - Remove duplicates (appears in 95% of playbooks)
transformers:
  - operator: uniq

# 2. append - Combine arrays
transformers:
  - operator: append
    args:
      item:
        value:
          simple: inputs.SHA256
        iscontext: true

# 3. split - String to array
transformers:
  - operator: split
    args:
      delimiter:
        value:
          simple: ','

# 4. join - Array to string
transformers:
  - operator: join
    args:
      separator:
        value:
          simple: ','

# 5. If-Then-Else - Conditional transformation
transformers:
  - operator: If-Then-Else
    args:
      condition:
        value:
          simple: lhs==rhs
      lhs:
        value:
          simple: inputs.AutoBlockIndicators
        iscontext: true
      rhs:
        value:
          simple: "True"
      then:
        value:
          simple: inputs.IP
        iscontext: true
      else:
        value:
          simple: Manual.IP
        iscontext: true

# 6. SetIfEmpty - Default values
transformers:
  - operator: SetIfEmpty
    args:
      defaultValue:
        value:
          simple: No indicators to block

# 7. replace - String replacement
transformers:
  - operator: replace
    args:
      toReplace:
        value:
          simple: ' '
      replaceWith: {}

# 8. FirstArrayElement - Get first item
transformers:
  - operator: FirstArrayElement

# 9. sort - Sort arrays
transformers:
  - operator: sort
    args:
      descending:
        value:
          simple: "true"
```

### 7. **Filter Patterns** (Context Filtering)
**Frequency**: 18 of 22 playbooks
**Purpose**: Filter context data

```yaml
# Filter DBotScore by type and score
complex:
  root: DBotScore
  filters:
    - - operator: isEqualString
        left:
          value:
            simple: DBotScore.Type
          iscontext: true
        right:
          value:
            simple: ip
        ignorecase: true
    - - operator: greaterThanOrEqual
        left:
          value:
            simple: DBotScore.Score
          iscontext: true
        right:
          value:
            simple: "3"
  accessor: Indicator
  transformers:
    - operator: uniq

# Filter modules by brand and state
filters:
  - - operator: isEqualString
      left:
        value:
          simple: modules.brand
        iscontext: true
      right:
        value:
          simple: CrowdstrikeFalcon
      ignorecase: true
  - - operator: isEqualString
      left:
        value:
          simple: modules.state
        iscontext: true
      right:
        value:
          simple: active
```

**Filter Structure**:
- Outer array: AND conditions
- Inner array: OR conditions
- Pattern: `[[OR, OR], [AND], [AND]]`

### 8. **User Collection Forms** (Type: `collection`)
**Frequency**: 8 of 22 playbooks
**Purpose**: Get user input/approval

```yaml
type: collection
task:
  name: Ask the user for verification
  type: collection
  iscommand: false
nexttasks:
  '#none#':
    - "next_task"
message:
  to:
    simple: Analyst
  subject:
    simple: Block Account - User Verification Form
  body:
    simple: |
      Dear XSOAR user,
      This notification informs you that the following list of accounts will be blocked...
  methods:
    - email
  format: html
  timings:
    retriescount: 2
    retriesinterval: 360
    completeafterreplies: 1
    completeafterv2: true
form:
  questions:
    - id: "0"
      label: ""
      labelarg:
        simple: 'Users to be blocked:'
      required: false
      type: multiSelect
      options: []
      optionsarg:
        - complex:
            root: Blocklist.Potential
  title: 'Which Users you would like to Block?'
  description: ""
```

**Form Field Types**:
- `multiSelect` - Multiple choice
- `singleSelect` - Single choice
- `shortText` - Text input
- `longText` - Textarea

### 9. **Email Notification** (Command: `send-mail`)
**Frequency**: 6 of 22 playbooks
**Purpose**: Notify users

```yaml
type: regular
task:
  name: Acknowledge alert was received
  script: '|||send-mail'
  type: regular
  iscommand: true
scriptarguments:
  to:
    complex:
      root: ReporterAddress
  subject:
    simple: 'Re: Phishing Investigation - ${alert.name}'
  body:
    simple: |
      Hi ${ReporterAddress},
      We've received your email and are investigating.

      Cordially,
      Your security team
```

### 10. **Integration Availability Check**
**Frequency**: 16 of 22 playbooks
**Purpose**: Check if integration is configured

**Pattern 1: IsIntegrationAvailable Automation**:
```yaml
type: condition
task:
  name: Is CrowdStrike Falcon enabled?
  scriptName: IsIntegrationAvailable
  type: condition
  iscommand: false
nexttasks:
  '#default#':
    - "done_task"
  "yes":
    - "use_integration_task"
scriptarguments:
  brandname:
    simple: CrowdstrikeFalcon
```

**Pattern 2: Manual modules Check**:
```yaml
type: condition
conditions:
  - label: "yes"
    condition:
      - - operator: isEqualString
          left:
            value:
              complex:
                root: modules
                filters:
                  - - operator: isEqualString
                      left:
                        value:
                          simple: modules.brand
                        iscontext: true
                      right:
                        value:
                          simple: Panorama
                accessor: state
            iscontext: true
          right:
            value:
              simple: active
          ignorecase: true
```

---

## XSIAM-Specific Modern Patterns

### 1. **Modern Command Syntax**

**Old (XSOAR)**:
```yaml
script: Builtin|||setIncident
scriptarguments:
  severity:
    simple: high
```

**New (XSIAM)**:
```yaml
script: Builtin|||setAlert
scriptarguments:
  severity:
    simple: high
```

### 2. **Context References**

**Alert Context** (Modern):
```yaml
value:
  complex:
    root: alert
    accessor: severity

# Common alert fields
${alert.id}
${alert.name}
${alert.severity}
${alert.emailfrom}
${alert.emailto}
${alert.emailsubject}
${alert.attachmentname}
${alert.labels.Email/from}
```

**Incident Context** (Legacy):
```yaml
value:
  complex:
    root: incident
    accessor: severity
```

### 3. **XQL Query Integration** (Not seen in samples, but modern XSIAM pattern)

Expected pattern:
```yaml
script: '|||xdr-xql-query'
scriptarguments:
  query:
    simple: 'dataset = xdr_data | filter event_type = ENUM.PROCESS'
  time_frame:
    simple: '24 hours'
```

---

## Input/Output Patterns

### Common Input Patterns

```yaml
inputs:
  # String input with default
  - key: AutoBlockIndicators
    value:
      simple: "True"
    required: false
    description: Should indicators be automatically blocked?

  # Complex input from context
  - key: Hostname
    value:
      complex:
        root: Endpoint
        accessor: Hostname
        transformers:
          - operator: uniq
    required: false

  # Query input (indicators)
  - key: ""
    value: {}
    playbookInputQuery:
      query: (verdict:Malicious) and (expirationStatus:active)
      queryEntity: indicators
```

### Common Output Patterns

```yaml
outputs:
  - contextPath: DBotScore
    description: The Indicator's object
    type: unknown

  - contextPath: DBotScore.Indicator
    description: The Indicator
    type: string

  - contextPath: DBotScore.Score
    description: The DBot score
    type: number

  - contextPath: IndicatorsToBlock
    description: Selected indicators to block
    type: unknown
```

---

## Enrichment Patterns

### 1. **Indicator Enrichment**

```yaml
# Get internal DBot score
scriptName: GetIndicatorDBotScore
scriptarguments:
  indicator:
    simple: ${inputs.MD5}
```

### 2. **Entity Enrichment**

```yaml
# Enrich email address
playbookName: Email Address Enrichment - Generic v2.1
scriptarguments:
  Email:
    complex:
      root: ReporterAddress
      transformers:
        - operator: uniq
separatecontext: true
```

### 3. **Endpoint Enrichment**

```yaml
# Multiple product checks in parallel
nexttasks:
  '#none#':
    - "check_active_directory"
    - "check_crowdstrike"
    - "check_carbon_black"
    - "check_cortex_xdr"
```

---

## Investigation Patterns

### 1. **Polling Pattern**

```yaml
playbookName: GenericPolling
scriptarguments:
  Ids:
    complex:
      root: inputs.key
  Interval:
    complex:
      root: inputs.frequency
  PollingCommandName:
    simple: CheckContextValue
  Timeout:
    complex:
      root: inputs.timeout
  dt:
    simple: CheckContextKey(val.key=='${inputs.key}' && val.exists==false).key
```

### 2. **Deduplication Pattern**

```yaml
# Filter out duplicates
transformers:
  - operator: uniq

# Filter out existing context
filters:
  - - operator: isNotEqualString
      left:
        value:
          simple: Account.Email.Address
        iscontext: true
      right:
        value:
          simple: ReporterAddress
        iscontext: true
```

### 3. **Severity Calculation**

```yaml
# Calculate from multiple sources
playbookName: Calculate Severity - Generic v2
scriptarguments:
  DBotScoreIndicators:
    complex:
      root: inputs.DBotScoreIndicators
  EmailAuthenticity Check:
    complex:
      root: inputs.EmailAuthenticityCheck
  CriticalUsers:
    complex:
      root: inputs.CriticalUsers
```

**Decision Logic**:
```yaml
conditions:
  - label: Critical
    condition:
      - - operator: isNotEmpty
          left:
            value:
              complex:
                root: Severities
                filters:
                  - - operator: containsGeneral
                      left:
                        value:
                          simple: Severities.DBotScoreSeverity
                        iscontext: true
                      right:
                        value:
                          simple: Critical
```

---

## Containment/Response Patterns

### 1. **Block Indicators**

```yaml
# Parallel blocking across multiple integrations
nexttasks:
  '#none#':
    - "Block IP"
    - "Block URL"
    - "Block File"
    - "Block Account"
    - "Block Email"
    - "Block Domain"

# Each calls sub-playbook
playbookName: Block IP - Generic v3
scriptarguments:
  IP:
    complex:
      root: DBotScore
      filters:
        - - operator: isEqualString
            left:
              value:
                simple: DBotScore.Type
              iscontext: true
            right:
              value:
                simple: ip
        - - operator: greaterThanOrEqual
            left:
              value:
                simple: DBotScore.Score
              iscontext: true
            right:
              value:
                simple: "3"
      accessor: Indicator
separatecontext: true
```

### 2. **Search and Delete Emails**

```yaml
playbookName: Search And Delete Emails - Generic v2
scriptarguments:
  From:
    complex:
      root: alert
      accessor: emailfrom
  Subject:
    complex:
      root: alert
      accessor: emailsubject
  AttachmentName:
    complex:
      root: alert
      accessor: attachmentname
  O365ExchangeLocation:
    simple: All
  O365KQL:
    simple: from:${alert.emailfrom} AND subject:"${alert.emailsubject}"
  SearchAndDeleteIntegration:
    complex:
      root: inputs.SearchAndDeleteIntegration
separatecontext: true
```

### 3. **Endpoint Isolation**

Expected pattern (not in samples):
```yaml
script: '|||xdr-isolate-endpoint'
scriptarguments:
  endpoint_id:
    complex:
      root: Endpoint
      accessor: ID
  incident_id:
    complex:
      root: alert
      accessor: id
```

---

## Closure Patterns

### 1. **Close Investigation**

```yaml
type: regular
task:
  name: Close investigation
  script: Builtin|||closeInvestigation
  type: regular
  iscommand: true
  brand: Builtin
nexttasks:
  '#none#':
    - "Done"
```

### 2. **Tag Indicators**

```yaml
script: Builtin|||appendIndicatorField
scriptarguments:
  field:
    simple: tags
  fieldValue:
    simple: ${inputs.IndicatorTagName}
  indicatorsValues:
    complex:
      root: ${playbookQuery
      accessor: value}
      transformers:
        - operator: uniq
```

---

## SLA/Timer Patterns

```yaml
# Start timer
timertriggers:
  - fieldname: detectionsla
    action: start

# Stop timer
timertriggers:
  - fieldname: detectionsla
    action: stop

# Remediation timer
timertriggers:
  - fieldname: remediationsla
    action: start
```

---

## Error Handling Patterns

### 1. **Skip Unavailable Integrations**

```yaml
skipunavailable: true  # Continue even if integration unavailable
continueonerror: true   # Continue even if command fails
```

### 2. **Default Paths**

```yaml
nexttasks:
  '#default#':  # Always provide fallback
    - "done_task"
  "yes":
    - "action_task"
```

### 3. **Quiet Mode**

```yaml
quietmode: 0  # Normal output
quietmode: 2  # Suppress output (for bulk operations)
```

---

## Task Linkage Patterns

### Common nexttasks Structures

```yaml
# Single next task
nexttasks:
  '#none#':
    - "task_id"

# Conditional branches
nexttasks:
  '#default#':
    - "default_task"
  "yes":
    - "yes_task"
  "no":
    - "no_task"

# Multiple parallel tasks
nexttasks:
  '#none#':
    - "task1"
    - "task2"
    - "task3"
    - "task4"

# Multiple condition outcomes
nexttasks:
  '#default#':
    - "done"
  "Critical":
    - "critical_task"
  "High":
    - "high_task"
  "Medium":
    - "medium_task"
  "Low":
    - "low_task"
```

---

## Gaps in Current Building Blocks

### Missing Commands We Don't Have

Based on analysis, these commands appear in playbooks but we may not have documented:

1. **Core Indicator Commands**:
   - `Builtin|||appendIndicatorField` - Add tags to indicators
   - `Builtin|||extractIndicators` - Extract indicators from text

2. **Email Operations**:
   - `|||send-mail` - Send email notifications
   - Email search/delete integration commands

3. **Automation Scripts**:
   - `GetIndicatorDBotScore` - Get internal reputation
   - `IsIntegrationAvailable` - Check integration status
   - `CheckEmailAuthenticity` - DKIM/SPF/DMARC validation
   - `DBotPredictPhishingWords` - ML phishing detection
   - `AssignAnalystToIncident` - Auto-assignment
   - `SetAndHandleEmpty` - Safe context setting

4. **Integration-Specific Commands** (we need generic patterns):
   - Active Directory: `ad-get-computer`, `ad-disable-account`
   - CrowdStrike: `cs-falcon-search-device`
   - Carbon Black: `cb-edr-sensors-list`
   - XDR: `xdr-get-endpoints`, `xdr-list-risky-hosts`
   - McAfee ePO: `epo-find-system`

### Missing Playbook Patterns

1. **Polling Mechanisms**:
   - Generic polling playbook structure
   - Field polling vs context polling
   - Timeout and interval management

2. **Campaign Detection**:
   - Email similarity detection
   - Linking related alerts
   - Campaign management

3. **ML/AI Integration**:
   - Phishing prediction
   - Automated classification
   - Confidence scoring

4. **Complex User Interaction**:
   - Multi-stage approval workflows
   - Form validation
   - Dynamic form generation

### Missing Task Types We Should Document

1. **Collection Task Variations**:
   - Different question types
   - Validation patterns
   - Multi-recipient messaging

2. **Loop Patterns**:
   - Sub-playbook loops
   - Max iteration handling
   - Exit conditions

3. **Error Recovery**:
   - Retry mechanisms
   - Fallback chains
   - Graceful degradation

---

## Recommendations for playbook_blocks.py

### 1. Add Modern XSIAM Patterns

```python
# Update terminology
XSIAM_CONTEXT = {
    'alert_id': '${alert.id}',
    'alert_name': '${alert.name}',
    'alert_severity': '${alert.severity}',
    'set_alert_cmd': 'Builtin|||setAlert',
    'close_investigation_cmd': 'Builtin|||closeInvestigation',
}

# vs Legacy XSOAR
XSOAR_CONTEXT = {
    'incident_id': '${incident.id}',
    'set_incident_cmd': 'Builtin|||setIncident',
}
```

### 2. Add Transformer Library

```python
COMMON_TRANSFORMERS = {
    'uniq': {'operator': 'uniq'},
    'append': {
        'operator': 'append',
        'args': {
            'item': {
                'value': {'simple': 'value'},
                'iscontext': True
            }
        }
    },
    'split': {
        'operator': 'split',
        'args': {
            'delimiter': {'value': {'simple': ','}}
        }
    },
    # ... etc
}
```

### 3. Add Filter Patterns

```python
def create_dbot_score_filter(indicator_type: str, min_score: int = 3):
    """Create standard DBotScore filter pattern"""
    return {
        'root': 'DBotScore',
        'filters': [
            [{'operator': 'isEqualString',
              'left': {'value': {'simple': 'DBotScore.Type'}, 'iscontext': True},
              'right': {'value': {'simple': indicator_type}},
              'ignorecase': True}],
            [{'operator': 'greaterThanOrEqual',
              'left': {'value': {'simple': 'DBotScore.Score'}, 'iscontext': True},
              'right': {'value': {'simple': str(min_score)}}}]
        ],
        'accessor': 'Indicator',
        'transformers': [{'operator': 'uniq'}]
    }
```

### 4. Add Integration Check Patterns

```python
def create_integration_check(integration_brand: str):
    """Create integration availability check condition"""
    return {
        'type': 'condition',
        'task': {
            'name': f'Is {integration_brand} enabled?',
            'scriptName': 'IsIntegrationAvailable',
            'type': 'condition',
            'iscommand': False
        },
        'scriptarguments': {
            'brandname': {'simple': integration_brand}
        },
        'nexttasks': {
            '#default#': ['done_task_id'],
            'yes': ['integration_task_id']
        }
    }
```

### 5. Add Sub-Playbook Call Patterns

```python
def create_subplaybook_call(
    playbook_name: str,
    arguments: dict,
    separate_context: bool = True,
    skip_unavailable: bool = True,
    max_loops: int = 100
):
    """Create standard sub-playbook invocation"""
    return {
        'type': 'playbook',
        'task': {
            'name': playbook_name,
            'playbookName': playbook_name,
            'type': 'playbook',
            'iscommand': False
        },
        'scriptarguments': arguments,
        'separatecontext': separate_context,
        'skipunavailable': skip_unavailable,
        'loop': {
            'iscommand': False,
            'exitCondition': '',
            'wait': 1,
            'max': max_loops
        }
    }
```

### 6. Add Collection/Form Patterns

```python
def create_user_approval_form(
    title: str,
    question_label: str,
    options_context_path: str,
    form_type: str = 'multiSelect'
):
    """Create user approval form task"""
    # Full structure from examples above
```

### 7. Add Common Enrichment Blocks

```python
ENRICHMENT_BLOCKS = {
    'indicator_enrichment': {
        'playbookName': 'Entity Enrichment - Generic v3',
        # ...
    },
    'endpoint_enrichment': {
        'playbookName': 'Endpoint Enrichment - Generic v2.1',
        # ...
    },
    'email_enrichment': {
        'playbookName': 'Email Address Enrichment - Generic v2.1',
        # ...
    }
}
```

### 8. Add Severity Calculation Pattern

```python
def create_severity_decision(severity_sources: list):
    """Create multi-source severity calculation"""
    # Based on Calculate Severity - Generic v2 pattern
```

### 9. Add Containment Action Blocks

```python
CONTAINMENT_ACTIONS = {
    'block_ip': {'playbookName': 'Block IP - Generic v3'},
    'block_file': {'playbookName': 'Block File - Generic v2'},
    'block_account': {'playbookName': 'Block Account - Generic v2'},
    'block_url': {'playbookName': 'Block URL - Generic v2'},
    'isolate_endpoint': {'script': '|||xdr-isolate-endpoint'},
    'search_delete_email': {'playbookName': 'Search And Delete Emails - Generic v2'},
}
```

### 10. Add Title Section Generator

```python
def create_workflow_sections():
    """Generate standard workflow section titles"""
    return {
        'triage': create_title_task('Triage'),
        'enrichment': create_title_task('Enrichment'),
        'investigation': create_title_task('Investigation'),
        'containment': create_title_task('Containment'),
        'remediation': create_title_task('Remediation'),
        'closure': create_title_task('Done')
    }
```

---

## Standard Playbook Structure Template

Based on analysis, a typical investigation playbook follows this structure:

```
Start (task 0)
  |
  v
Check Inputs (condition)
  |
  +-- No inputs --> Done
  |
  +-- Has inputs
      |
      v
  Start Detection Timer (title + timer trigger)
      |
      +-- Parallel Branches:
      |   |
      |   +-- Engage with User (title)
      |   |   |
      |   |   +-- Extract reporter info
      |   |   +-- Send acknowledgment email
      |   |   +-- Enrich reporter account
      |   |
      |   +-- Triage (title)
      |       |
      |       +-- Process Email sub-playbook
      |       +-- Extract Indicators
      |       +-- Detonate Files
      |
      +-- (All branches converge)
      |
      v
  Indicator Enrichment (title)
      |
      +-- Entity Enrichment sub-playbook
      |
      v
  Investigation (title)
      |
      +-- Parallel Checks:
      |   |
      |   +-- Email Authenticity Check
      |   +-- Email Campaign Search
      |   +-- Microsoft Headers Check
      |   +-- Machine Learning Analysis
      |
      +-- (All converge to)
      |
      v
  Calculate Severity sub-playbook
      |
      v
  Assign to analyst
      |
      v
  Is malicious? (condition)
      |
      +-- No / Undetermined
      |   |
      |   +-- Manual Review
      |   +-- Send "safe" email to user
      |   +-- Close investigation
      |
      +-- Yes (Malicious)
          |
          +-- Check if part of campaign
          |   |
          |   +-- No --> Send "malicious" email
          |   +-- Yes --> Send "campaign" email
          |
          v
      Start Remediation Timer
          |
          +-- Parallel Remediation:
          |   |
          |   +-- Block Indicators (if enabled)
          |   +-- Search & Delete Emails (if enabled)
          |   +-- Manual Remediation
          |
          +-- (All converge to)
          |
          v
      Stop Remediation Timer
          |
          v
      Close Investigation
          |
          v
      Done
```

---

## Key Takeaways for AI Playbook Generation

1. **Always use modern XSIAM terminology** (Issues/Cases, not Alerts/Incidents)
2. **Condition tasks are the backbone** - Every decision point needs one
3. **Title tasks organize workflow** - Use them liberally for clarity
4. **Sub-playbooks enable reuse** - Don't reinvent wheels, call existing playbooks
5. **Transformers are essential** - `uniq`, `append`, `If-Then-Else` appear everywhere
6. **Filters use AND/OR logic** - Outer array is AND, inner array is OR
7. **Check integration availability** - Always verify before using integration commands
8. **Parallel execution is common** - Multiple enrichment/remediation branches
9. **User interaction is structured** - Collection tasks for approvals, send-mail for notifications
10. **Error handling is built-in** - `skipunavailable: true`, `#default#` paths

---

## File Analysis Summary

| Category | Count | Examples |
|----------|-------|----------|
| Total Playbooks | 22 | All generic/reusable playbooks |
| Condition Tasks | ~150 | Decision points throughout |
| Title Tasks | ~80 | Workflow organization |
| Sub-Playbook Calls | ~45 | Modular reuse |
| Regular Commands | ~200 | Integration/automation execution |
| Collection Tasks | ~12 | User interaction forms |
| Transformers Used | ~500 | Data manipulation |
| Filters Applied | ~100 | Context filtering |

---

## Next Steps

1. **Update playbook_blocks.py** with patterns identified above
2. **Create transformer library** for common data manipulations
3. **Build integration check templates** for all major products
4. **Document sub-playbook patterns** for reusable workflows
5. **Add form/collection templates** for user interaction
6. **Create severity calculation helpers** for multi-source analysis
7. **Build containment action library** for response operations
8. **Add XSIAM-specific context helpers** for modern platform
9. **Create workflow structure templates** for common investigation types
10. **Build filter pattern library** for common context queries

---

*End of Analysis*
