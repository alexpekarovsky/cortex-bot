# Slack/Email Entitlement Tags for Sub-Playbooks

## The Problem

When using `SlackAskV2` or `EmailAskUser` commands in **sub-playbooks** (playbooks called from other playbooks), button clicks fail to close the waiting conditional task. The message sends successfully, buttons appear, users can click them, but the playbook gets stuck waiting forever.

## Root Cause

**Main playbooks (top-level):**
- Entitlement uses `investigation_id` to find the task to close
- Works without any tags

**Sub-playbooks (nested):**
- Run in a separate playbook context
- Entitlement cannot find the task using only `investigation_id`
- **Requires tags as the lookup mechanism**

## The Solution: Task Parameter + Matching Tags

You must create a unique identifier that:
1. Is specified in the `task` parameter of `SlackAskV2`/`EmailAskUser`
2. Is added as a tag on the conditional wait task
3. Matches exactly between both locations

### Pattern

```yaml
# Task 1: SlackAskV2 - Send interactive message
type: regular
scriptName: SlackAskV2
scriptarguments:
  channel:
    simple: "security-team"
  message:
    simple: "Is this alert a false positive?"
  option1:
    simple: "Yes - False Positive#green"
  option2:
    simple: "No - Real Threat#red"
  task:
    simple: "my-playbook-wait-4"  # ← This is the tag reference
  lifetime:
    simple: "4 hours"
nexttasks:
  '#none#': ["4"]

# Task 4: Conditional Wait - Wait for user response
type: condition
task:
  name: Wait for Team Response
  description: Entitlement will close this task when user clicks button
tags:
  - "my-playbook-wait-4"  # ← CRITICAL: Must match task parameter exactly!
nexttasks:
  "Yes - False Positive": ["10"]
  "No - Real Threat": ["20"]
  '#default#': ["30"]
```

## Naming Convention

**Recommended format:** `{playbook-name}-wait-{task-id}`

**Examples:**
- Playbook: `Team-Escalation-Sub` → Tag: `team-escalation-sub-wait-4`
- Playbook: `Security Approval` → Tag: `security-approval-wait-2`
- Playbook: `FP Validation [Nested]` → Tag: `fp-validation-nested-wait-3`

**Rules:**
- Use lowercase
- Replace spaces with hyphens
- Include playbook name for uniqueness (especially important if you have multiple sub-playbooks)
- Include task ID to avoid collisions within same playbook
- Keep it descriptive but concise

## Complete Working Example

### Sub-Playbook: Team-Escalation-Nested.yml

```yaml
id: team-escalation-nested
version: -1
name: Team Escalation [Nested]
description: Sub-playbook for team approval workflow
starttaskid: "0"

tasks:
  "0":
    # Start task
    id: "0"
    type: start
    nexttasks:
      '#none#': ["1"]

  "1":
    # Delete old Slack responses (best practice)
    id: "1"
    type: regular
    task:
      name: Clear Old Responses
      scriptName: DeleteContext
    scriptarguments:
      key:
        simple: "slackresponse"
    nexttasks:
      '#none#': ["3"]

  "3":
    # Send interactive Slack message
    id: "3"
    type: regular
    task:
      name: Send Team Alert Message
      scriptName: SlackAskV2
    scriptarguments:
      channel:
        simple: "security-team"
      message:
        simple: "🚨 Security Alert - S3 Bucket Public Access\n\nIs this a false positive?"
      option1:
        simple: "Yes - False Positive#green"
      option2:
        simple: "No - Real Threat#red"
      option3:
        simple: "Unrelated to my team#black"
      task:
        simple: "team-escalation-nested-wait-4"  # ← Tag reference
      lifetime:
        simple: "24 hours"
      defaultResponse:
        simple: "NoResponse"
      persistent:
        simple: "true"
    nexttasks:
      '#none#': ["4"]

  "4":
    # Wait for user response
    id: "4"
    type: condition
    task:
      name: WAIT - Team Response
      description: Manual wait - closed by entitlement when user clicks button
    tags:
      - "team-escalation-nested-wait-4"  # ← CRITICAL: Matches task parameter!
    nexttasks:
      '#default#': ["10"]
      "Yes - False Positive": ["5"]
      "No - Real Threat": ["6"]
      "Unrelated to my team": ["7"]
      "NoResponse": ["20"]

  "5":
    # Handle false positive response
    id: "5"
    type: regular
    script: '|||send-notification'
    scriptarguments:
      channel:
        simple: "security-team"
      message:
        simple: |
          ✅ You marked this as FALSE POSITIVE
          
          Actions taken by XSOAR:
          - Alert marked as resolved
          - Case closed as false positive
          - Team notified
    nexttasks:
      '#none#': ["50"]

  "6":
    # Handle real threat response
    id: "6"
    type: regular
    script: '|||send-notification'
    scriptarguments:
      channel:
        simple: "security-team"
      message:
        simple: |
          🔴 You confirmed this is a REAL THREAT
          
          Actions taken by XSOAR:
          - Escalating to security operations
          - Creating incident ticket
          - Starting containment procedures
    nexttasks:
      '#none#': ["50"]

  "50":
    # Done
    id: "50"
    type: title
    task:
      name: Done
```

### Parent Playbook: Main-Security-Alert.yml

```yaml
id: main-security-alert
name: Main Security Alert Handler
starttaskid: "0"

tasks:
  "0":
    id: "0"
    type: start
    nexttasks:
      '#none#': ["1"]

  "1":
    # Call sub-playbook
    id: "1"
    type: playbook
    task:
      name: Escalate to Team
      playbookName: Team Escalation [Nested]
    scriptarguments:
      ManagerEmail:
        simple: "manager@company.com"
    separatecontext: true  # Sub-playbook runs in separate context!
    loop:
      max: 100
    nexttasks:
      '#none#': ["10"]

  "10":
    id: "10"
    type: title
    task:
      name: Done
```

## Common Mistakes

### ❌ Mistake 1: Missing Tag Entirely

```yaml
# SlackAsk specifies task parameter ✅
scriptarguments:
  task:
    simple: "team-escalation-wait-4"

# But conditional task has NO tags ❌
type: condition
task:
  name: Wait
# Missing: tags!
nexttasks:
  "Yes": ["10"]
```

**Result:** Task never closes when button clicked in sub-playbook.

### ❌ Mistake 2: Tag Doesn't Match Task Parameter

```yaml
# SlackAsk uses one name
scriptarguments:
  task:
    simple: "wait-task-4"  # One name

# Conditional uses different name ❌
tags:
  - "my-playbook-wait-4"  # Different name!
```

**Result:** Entitlement can't find task, gets stuck waiting.

### ❌ Mistake 3: Using Only Task ID (Not Full Tag)

```yaml
# SlackAsk uses just task ID ❌
scriptarguments:
  task:
    simple: "4"  # Works in main playbook, fails in sub!

# Conditional has no tags
type: condition
task:
  name: Wait
```

**Result:** Works in main playbook, fails in sub-playbook.

### ✅ Correct Pattern

```yaml
# SlackAsk uses full tag name
scriptarguments:
  task:
    simple: "team-escalation-nested-wait-4"  # Full tag

# Conditional has exact matching tag
tags:
  - "team-escalation-nested-wait-4"  # Exact match
```

## Testing Your Sub-Playbook

1. **Create parent playbook** that calls your sub-playbook
2. **Run parent playbook** (not sub-playbook directly)
3. **Verify Slack message appears** with buttons
4. **Click a button** in Slack
5. **Check if sub-playbook task closes** and routing works
6. **If stuck:** Verify tag matches task parameter exactly (case-sensitive, character-for-character)

### Debug Checklist

- [ ] Sub-playbook called with `separatecontext: true`
- [ ] SlackAskV2 task parameter specified (not empty)
- [ ] Conditional task has tags array
- [ ] Tag value matches task parameter exactly
- [ ] SlackV3 integration is Long Running
- [ ] SlackV3 uses Socket Mode (App Token configured)
- [ ] Button text matches nexttasks labels

## EmailAskUser Pattern

The same pattern applies to `EmailAskUser`:

```yaml
# Email ask task
scriptName: EmailAskUser
scriptarguments:
  subject:
    simple: "Security Alert - Approval Required"
  message:
    simple: "Please approve or reject this action"
  option1:
    simple: "Approve"
  option2:
    simple: "Reject"
  task:
    simple: "my-playbook-wait-5"  # Tag reference

# Conditional wait
type: condition
tags:
  - "my-playbook-wait-5"  # Matching tag
nexttasks:
  "Approve": ["10"]
  "Reject": ["20"]
```

## Automatic Tag Generation

The `create_playbook` MCP tool automatically detects `SlackAskV2` and `EmailAskUser` tasks and adds appropriate tags to referenced conditional tasks when generating playbooks.

### How It Works

1. Tool scans for `SlackAskV2`/`EmailAskUser` tasks
2. Extracts the `task` parameter value
3. Finds the conditional task with matching ID
4. Generates tag: `{playbook-name}-wait-{task-id}`
5. Adds tag to conditional task's tags array
6. Updates SlackAsk task parameter to use full tag name

### Example

**Input:**
```json
{
  "name": "Team-Approval-Sub",
  "tasks": [
    {
      "id": "1",
      "type": "regular",
      "script": "SlackAskV2",
      "arguments": {
        "task": {"simple": "2"}
      }
    },
    {
      "id": "2",
      "type": "condition",
      "nexttasks": {"Yes": ["10"], "No": ["20"]}
    }
  ]
}
```

**Output:**
```yaml
tasks:
  "1":
    scriptName: SlackAskV2
    scriptarguments:
      task:
        simple: "team-approval-sub-wait-2"  # Auto-generated

  "2":
    type: condition
    tags:
      - "team-approval-sub-wait-2"  # Auto-added
    nexttasks:
      "Yes": ["10"]
      "No": ["20"]
```

## Summary

**Main Playbooks:**
- Tags optional (but recommended for consistency)
- Entitlement uses investigation_id

**Sub-Playbooks:**
- Tags REQUIRED
- Without tags: Buttons won't work
- Tag must match task parameter exactly

**Best Practice:**
- Always use tags for all SlackAsk/EmailAsk conditional waits
- Use consistent naming: `{playbook-name}-wait-{task-id}`
- Test in parent playbook context before production
- Use playbook builder tool for automatic tag generation
