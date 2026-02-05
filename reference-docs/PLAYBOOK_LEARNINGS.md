# Key Learnings from XSIAM Playbook Analysis

## 🔴 CRITICAL CORRECTION: XSIAM Terminology

**WRONG** (what I was using):
- ❌ "alerts" 
- ❌ "incidents"
- ❌ `${incident.id}`
- ❌ `setIncident`

**CORRECT** (XSIAM modern):
- ✅ **"issues"** - Individual security events
- ✅ **"cases"** - Collections of related issues
- ✅ `${alert.id}` - Context references use "alert"
- ✅ `setAlert` - Modern command

**Evidence**: All 22 production playbooks use `${alert.severity}`, `${alert.name}`, `Builtin|||setAlert`

---

## Top 10 Building Blocks Discovered

From analyzing 22 production playbooks:

1. **Condition Tasks** - Branching logic (ALL playbooks use)
2. **Title Tasks** - Workflow sections (avg 3-5 per playbook)
3. **Sub-Playbook Calls** - Modular reuse (18 of 22 playbooks)
4. **Integration Commands** - Execute actions (ALL playbooks)
5. **Set Context** - Store data (20 of 22 playbooks)
6. **Transformers** - Data manipulation (uniq, append, split, join)
7. **Filters** - DBotScore, module availability
8. **User Collection** - Forms and surveys (multiSelect, singleSelect)
9. **Email Notifications** - send-mail with templating
10. **Integration Checks** - IsIntegrationAvailable patterns

---

## Commands We're Missing

**From the analysis of 22 playbooks:**

### Automation Scripts:
- `appendIndicatorField` - Add tags/fields to indicators
- `extractIndicators` - Parse IOCs from text
- `GetIndicatorDBotScore` - Get reputation scores
- `IsIntegrationAvailable` - Check if integration configured
- `CheckEmailAuthenticity` - SPF/DKIM/DMARC validation
- `DBotPredictPhishingWords` - ML phishing detection
- `SetAndHandleEmpty` - Safe context setting
- `Dedup - Generic v4` - Deduplication with ML
- `CalculateSeverity` - Severity scoring

### Integration Commands:
- `ad-get-computer` - Active Directory lookups
- `cs-falcon-search-device` - CrowdStrike queries
- `xdr-get-endpoints` - XDR endpoint data
- `send-mail` - Email notifications
- `mcafee-epo-find-system` - McAfee EPO
- `cb-binary-search` - Carbon Black

---

## Patterns We Need to Add

### 1. Complex Argument Passing
```yaml
scriptarguments:
  Hash:
    complex:
      root: inputs.MD5
      transformers:
        - operator: uniq
        - operator: append
          args:
            item:
              value:
                simple: inputs.SHA256
```

### 2. Polling Mechanisms
```yaml
type: playbook
playbookName: GenericPolling
inputs:
  - Ids: ${TaskIDs}
  - PollingCommandName: task-status
  - Timeout: 600
  - Interval: 60
```

### 3. User Input Collection
```yaml
type: collection
task:
  name: Get analyst decision
  form:
    questions:
      - id: "0"
        label: "Action?"
        fieldAssociated: ""
        fieldType: multiSelect
        required: true
        options:
          - Block
          - Allow
          - Escalate
```

### 4. Filter Patterns
```yaml
filters:
  - - operator: greaterThanOrEqual
      left:
        value:
          simple: DBotScore.Score
        iscontext: true
      right:
        value:
          simple: "3"
```

---

## Gaps in Our Current Building Blocks

### Missing from `playbook_blocks.py`:

1. **Transformers Library** - uniq, append, split, join, If-Then-Else
2. **Filter Patterns** - DBotScore, module checks
3. **Polling Patterns** - GenericPolling, ScheduledCommand
4. **Collection Forms** - User input gathering
5. **Complex Arguments** - Nested transformers
6. **Automation Scripts** - Built-in utilities
7. **Email Operations** - send-mail, search-and-delete
8. **AD/CrowdStrike/McAfee** - Common integrations
9. **Dedup Patterns** - ML-based deduplication
10. **Severity Calculation** - Automated scoring

---

## Action Items

### Immediate Updates Needed:

1. **Fix Terminology** in `playbook_blocks.py`:
   - Change all `${incident.*}` → `${alert.*}`
   - Update `setIncident` → `setAlert`
   - Document "issues" and "cases" (not "alerts" and "incidents")

2. **Add Missing Blocks**:
   - Transformer library
   - Filter patterns
   - Polling mechanisms
   - User collection forms

3. **Enhance Examples**:
   - Use production-tested YAML from these 22 playbooks
   - Add complex argument passing
   - Show loop parameters
   - Include separatecontext patterns

---

## Statistics

- **Playbooks**: 22 analyzed
- **Condition Tasks**: ~150
- **Title Tasks**: ~80
- **Sub-Playbook Calls**: ~45
- **Commands**: ~200
- **Transformers**: ~500
- **Filters**: ~100

**Key Insight**: Production playbooks are HEAVILY modular - they call 2-3 sub-playbooks each, not implementing everything inline!

---

**Saved**: `/Users/apekarovsky/projects/cortex-mcp/PLAYBOOK_LEARNINGS.md`
**Full Analysis**: `/Users/apekarovsky/projects/cortex-mcp/docs/PLAYBOOK_ANALYSIS.md` (1385 lines)
