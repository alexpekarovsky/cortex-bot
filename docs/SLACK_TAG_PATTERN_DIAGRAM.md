# Slack/Email Entitlement Tag Pattern - Visual Guide

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PARENT PLAYBOOK                                │
│                                                                     │
│   Task 1: Call Sub-Playbook                                        │
│   ─────────────────────────────                                    │
│   type: playbook                                                    │
│   playbookName: "Team Escalation [Nested]"                         │
│   separatecontext: true  ← Creates separate context!               │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Calls sub-playbook in
                           │ SEPARATE CONTEXT
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUB-PLAYBOOK (Separate Context)                  │
│                                                                     │
│   Task 3: SlackAskV2                                                │
│   ────────────────────────────────────────                         │
│   scriptarguments:                                                  │
│     task:                                                           │
│       simple: "team-escalation-wait-4"  ← Tag reference!           │
│     message: "Approve?"                                             │
│     option1: "Yes#green"                                            │
│     option2: "No#red"                                               │
│                                                                     │
│   Creates entitlement: "abc123@investigation_id|4"                 │
│   BUT: investigation_id belongs to sub-playbook context            │
│        Main context cannot find it!                                 │
│                                                                     │
│                           │                                         │
│                           ▼                                         │
│   Task 4: Conditional Wait                                          │
│   ────────────────────────────────────────                         │
│   tags:                                                             │
│     - "team-escalation-wait-4"  ← CRITICAL! Matches task param     │
│   nexttasks:                                                        │
│     "Yes": ["10"]                                                   │
│     "No": ["20"]                                                    │
│                                                                     │
│   Tag provides the lookup mechanism!                                │
│   Entitlement can find task via tag instead of investigation_id    │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ User clicks button
                           │ in Slack
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SLACK (Socket Mode)                            │
│                                                                     │
│   Button clicked: "Yes"                                             │
│   Payload contains:                                                 │
│     - entitlement: "abc123@investigation_id|4"                      │
│     - button text: "Yes"                                            │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Webhook via
                           │ Socket Mode
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SLACKV3 INTEGRATION                              │
│                                                                     │
│   1. Receives webhook from Slack                                    │
│   2. Extracts entitlement: "abc123@investigation_id|4"              │
│   3. Tries to find task:                                            │
│                                                                     │
│      WITHOUT TAGS (❌ FAILS):                                       │
│      ─────────────────────────                                     │
│      • Looks in investigation_id context                            │
│      • Sub-playbook investigation_id not found                      │
│      • Task 4 not found                                             │
│      • Button click ignored                                         │
│      • Task stays waiting forever                                   │
│                                                                     │
│      WITH TAGS (✅ WORKS):                                          │
│      ─────────────────────────                                     │
│      • Extracts task parameter from entitlement: "4"                │
│      • Searches for tasks with tag matching pattern                 │
│      • Finds task 4 with tag: "team-escalation-wait-4"              │
│      • Closes task 4 with result: "Yes"                             │
│      • Playbook continues with nexttasks["Yes"]                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Side-by-Side Comparison

### Main Playbook (Works Without Tags)

```yaml
┌──────────────────────────────────────────────────────────┐
│  MAIN PLAYBOOK                                           │
│  Context: investigation_1234                             │
│                                                          │
│  Task 3: SlackAskV2                                      │
│    task: "4"  ← Just task ID                            │
│                                                          │
│  Task 4: Condition                                       │
│    (no tags needed)                                      │
│                                                          │
│  Entitlement: "abc@1234|4"                               │
│              └─ investigation_1234 ─┘                    │
│                                                          │
│  ✅ SlackV3 can find task 4 in investigation_1234        │
└──────────────────────────────────────────────────────────┘
```

### Sub-Playbook (Requires Tags)

```yaml
┌──────────────────────────────────────────────────────────┐
│  SUB-PLAYBOOK                                            │
│  Context: investigation_5678 (separate!)                 │
│                                                          │
│  Task 3: SlackAskV2                                      │
│    task: "my-sub-playbook-wait-4"  ← Full tag           │
│                                                          │
│  Task 4: Condition                                       │
│    tags: ["my-sub-playbook-wait-4"]  ← REQUIRED!        │
│                                                          │
│  Entitlement: "abc@5678|4"                               │
│              └─ investigation_5678 ─┘                    │
│                 (sub-context)                            │
│                                                          │
│  ❌ SlackV3 cannot find investigation_5678 from main     │
│  ✅ SlackV3 CAN find task via tag lookup                 │
└──────────────────────────────────────────────────────────┘
```

## The Tag Matching Mechanism

```
SlackAskV2 Task Parameter          Conditional Task Tag
─────────────────────────         ─────────────────────

scriptarguments:                   type: condition
  task:                            tags:
    simple: "my-pb-wait-4" ────────► ["my-pb-wait-4"]
                                      │
                                      │ MUST MATCH!
                                      │ (exact, case-sensitive)
                                      │
                                      ▼
                           When button clicked:
                           1. Extract task ID from entitlement
                           2. Search for task with matching tag
                           3. Close that task with button result
```

## Common Mistake: Mismatched Names

```
❌ WRONG - Names don't match:

Task 3:                            Task 4:
  task: "wait-task-4"                tags: ["my-playbook-wait-4"]
         └─ One name ─┘                     └─ Different name ─┘

Result: Entitlement cannot find task, button does nothing


✅ CORRECT - Names match exactly:

Task 3:                            Task 4:
  task: "my-pb-wait-4"               tags: ["my-pb-wait-4"]
         └─ Same ────────────────────────┘

Result: Entitlement finds task, closes it with button result
```

## Automatic Tag Generation Flow

```
┌─────────────────────────────────────────────────────────┐
│  INPUT: Task Definitions                                │
│  ─────────────────────────                             │
│  {                                                      │
│    "id": "1",                                           │
│    "type": "regular",                                   │
│    "script": "SlackAskV2",                              │
│    "arguments": {                                       │
│      "task": {"simple": "2"}  ← References task 2      │
│    }                                                    │
│  },                                                     │
│  {                                                      │
│    "id": "2",                                           │
│    "type": "condition"  ← No tags specified            │
│  }                                                      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  PLAYBOOK BUILDER LOGIC                                 │
│  ─────────────────────────                             │
│  1. Detect: "SlackAskV2" in task 1                      │
│  2. Extract: task parameter = "2"                       │
│  3. Find: Conditional task with id = "2"                │
│  4. Generate: tag = "{playbook-name}-wait-2"            │
│  5. Add: tags array to task 2                           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  OUTPUT: Playbook YAML with Auto-Generated Tags         │
│  ───────────────────────────────────────────────        │
│  tasks:                                                 │
│    "1":                                                 │
│      scriptName: SlackAskV2                             │
│      scriptarguments:                                   │
│        task:                                            │
│          simple: "2"  ← Or auto-update to full tag     │
│                                                         │
│    "2":                                                 │
│      type: condition                                    │
│      tags:                                              │
│        - "team-approval-sub-wait-2"  ← AUTO-ADDED!     │
│      nexttasks:                                         │
│        "Yes": ["10"]                                    │
│        "No": ["20"]                                     │
└─────────────────────────────────────────────────────────┘
```

## Summary: When Tags Are Required

```
┌────────────────┬──────────────┬─────────────────────────┐
│  Scenario      │  Tags Req?   │  Reason                 │
├────────────────┼──────────────┼─────────────────────────┤
│ Main playbook  │  ❌ Optional │  investigation_id works │
│ Sub-playbook   │  ✅ REQUIRED │  Separate context       │
│ Nested in loop │  ✅ REQUIRED │  Multiple contexts      │
│ Called via API │  ✅ REQUIRED │  Different context      │
└────────────────┴──────────────┴─────────────────────────┘

Best Practice: ALWAYS USE TAGS for consistency!
```
