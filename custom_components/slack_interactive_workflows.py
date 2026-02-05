"""
Slack Interactive Workflows Guide for Cortex XSIAM/XSOAR

This module provides guidance on creating interactive Slack workflows with XSIAM
using SlackV3 integration, SlackAskV2, and custom Block Kit messages.

Key Features:
- Multi-step interactive workflows
- Entitlement-based response capture
- Conditional routing based on button clicks
- Custom Block Kit with dropdowns and buttons
- Nested interactive messages

Based on: Real-world implementation for security alert triage workflows
"""

from fastmcp import Context

from usecase.base_module import BaseModule

SLACK_INTERACTIVE_WORKFLOWS_GUIDE = """
# Slack Interactive Workflows for Cortex XSIAM

## Table of Contents
1. [Critical Requirements](#critical-requirements)
2. [SlackAskV2 Complete Reference](#slackaaskv2-complete-reference)
3. [SlackBlockBuilder Workflow](#slackblockbuilder-workflow)
4. [Entitlements Deep Dive](#entitlements-deep-dive)
5. [Sub-Playbook Tag References](#sub-playbook-tag-references)
6. [Architecture & Patterns](#architecture--patterns)
7. [Troubleshooting](#troubleshooting)

---

## Critical Requirements

###  REQUIREMENT 1: Sleep Between Multiple SlackAskV2 Calls

**If you have multiple SlackAskV2 calls in one playbook:**

You MUST add a 10-second Sleep task before EVERY SlackAskV2 call after the first one.

```yaml
Task 1: SlackAskV2 #1
Task 2: Wait
Task 10: Confirmation
Task 10.5: Sleep 10 seconds  # REQUIRED!
Task 11: SlackAskV2 #2
Task 12: Wait
Task 20: Confirmation
Task 20.5: Sleep 10 seconds  # REQUIRED!
Task 21: SlackAskV2 #3
```

**Without the Sleep task:**
- Second/third SlackAskV2 messages send successfully
- But button clicks don't register
- Task remains stuck waiting forever

**Why:** First entitlement needs time to fully process before creating second entitlement.

**Recommended Sleep Duration:** 10 seconds (tested and working on XSIAM SaaS)

###  REQUIREMENT 2: Slack Message Size Limit

**HARD LIMIT: 3000 characters (Slack API)**

The total message size includes:
- Your Block Kit JSON content: ~1500 chars (safe zone)
- Entitlement metadata: ~300 chars
- Per-button entitlement data: ~150 chars per button

**Example Calculation:**
```
Custom Block Kit:        2467 chars
+ Entitlement metadata:  ~300 chars
+ 3 buttons × 150 chars: ~450 chars
= Total:                 ~3217 chars - EXCEEDS LIMIT
```

**Symptom if exceeded:**
- Message sends successfully to Slack - Message displays correctly - But button clicks don't respond - Task hangs indefinitely

**Solution:** Keep your Block Kit content under 1500 characters to leave room for entitlement metadata

###  REQUIREMENT 3: DeleteContext Before SlackAskV2CustomBlocks

**Always call DeleteContext BEFORE SlackAskV2CustomBlocks:**

```yaml
Task 0.5: DeleteContext
  scriptarguments:
    key:
      simple: "slackresponse"

Task 3: SlackAskV2CustomBlocks
  # Your Slack message
```

**Why:** Clears old Slack responses from context, prevents wrong routing

## Overview

This guide explains how to create fully interactive Slack workflows in Cortex XSIAM where:
- XSOAR sends interactive messages to Slack (with buttons, dropdowns, etc.)
- Users respond by clicking buttons
- XSOAR captures the response and continues the playbook
- Multi-step workflows with multiple manual interaction points

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    XSOAR Playbook                          │
├────────────────────────────────────────────────────────────┤
│  Task 1: SlackAskV2 (creates entitlement, sends message)   │
│     ↓                                                      │
│  Task 2: Conditional Task (WAITS for response)            │
│     ↓                                                      │
│  [User clicks button in Slack]                            │
│     ↓                                                      │
│  SlackV3 receives webhook via Socket Mode                 │
│     ↓                                                      │
│  Entitlement closes Task 2 with button text               │
│     ↓                                                      │
│  Task 3+: Conditional routing based on response           │
└────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. SlackV3 Integration Configuration

**Required Settings:**
- **App Token**: For Socket Mode (xapp-...)
- **Bot Token**: For sending messages (xoxb-...)
- **Long Running Instance**: MUST be enabled
- **Trust any certificate**: Recommended

**Socket Mode vs Webhooks:**
- XSIAM SaaS uses **Socket Mode** (via App Token)
- NOT traditional HTTP webhooks
- No need for public webhook URLs

---

## SlackAskV2 Complete Reference

### All 15 Parameters Explained

```yaml
!SlackAskV2
  # REQUIRED PARAMETERS (5)
  channel: "team-channel"              # Slack channel name or ID
  message: "Question text"              # The question to ask
  option1: "Yes#green"                  # First button (green)
  option2: "No#red"                     # Second button (red)
  task: "4"                             # Task ID to close when button clicked

  # OPTIONAL PARAMETERS (10)
  additionalOptions: "Maybe#black"      # Button 3+ (comma-separated for multiple)
  lifetime: "4 hours"                   # Entitlement timeout (default: 1 day)
  defaultResponse: "NoResponse"         # Response if timeout occurs
  reply: "Thank you!"                   # Reply message after button click
  persistent: "false"                   # One-time vs persistent entitlement

  replyEntriesTag: "SlackResponse"      # Tag for War Room entries
  entitlement: ""                       # Pre-created entitlement (advanced)
  thread: ""                            # Thread ID to reply in
  blocks: ""                            # Custom Block Kit JSON (advanced)
  investigationId: ""                   # Override investigation ID
```

### Parameter Details

#### Required Parameters

**1. channel** (string)
- Slack channel name (without #) or channel ID
- Examples: `"security-alerts"`, `"C01234ABCD"`

**2. message** (string)
- The question text displayed above buttons
- Supports markdown formatting
- Keep concise for better UX

**3. option1** (string)
- First button text and color
- Format: `"Text#color"`
- Colors: `green`, `red`, `black`, `primary`, `danger`, `default`
- Example: `"Approve#green"`

**4. option2** (string)
- Second button (same format as option1)
- Example: `"Reject#red"`

**5. task** (string)
- Task ID (as string!) that will be closed when button clicked
- CRITICAL: Must match a conditional task ID in playbook
- Example: `"4"` (not `4` as integer)

#### Optional Parameters

**6. additionalOptions** (string)
- Additional buttons beyond option1 and option2
- Comma-separated for multiple buttons
- Example: `"Maybe#black,Escalate#danger"`
- Each follows same `Text#color` format

**7. lifetime** (string, default: "1 day")
- How long entitlement remains active
- After lifetime expires, defaultResponse is used
- Examples: `"30 minutes"`, `"4 hours"`, `"2 days"`

**8. defaultResponse** (string, default: "")
- Response to use if lifetime expires with no click
- Should match one of your nexttasks labels or use #default#
- Example: `"NoResponse"`, `"Timeout"`

**9. reply** (string, default: "Thank you for your response")
- Message posted in Slack after button click
- Can include markdown
- Example: `" Response recorded. XSOAR is processing..."`

**10. persistent** (string, default: "false")
- `"false"` = One-time entitlement (button disabled after first click)
- `"true"` = Persistent (button can be clicked multiple times)
- See [Entitlements Deep Dive](#entitlements-deep-dive) for details

**11. replyEntriesTag** (string, default: "")
- Tag applied to War Room entries from this interaction
- Useful for filtering entries
- Example: `"SlackResponse"`, `"TeamApproval"`

**12. entitlement** (string, default: "" - auto-generated)
- Pre-created entitlement GUID
- Advanced use only - normally leave blank for auto-generation
- Format: `GUID@investigation_id|task_id`

**13. thread** (string, default: "")
- Thread timestamp ID to reply within an existing thread
- Example: `"1234567890.123456"`
- Leave blank to create new message

**14. blocks** (string, default: "")
- Custom Block Kit JSON to override default message
- Advanced use - prefer SlackAskV2CustomBlocks for complex layouts
- Must be valid JSON string

**15. investigationId** (string, default: current investigation)
- Override which investigation the entitlement belongs to
- Advanced use - normally leave blank

### How SlackAskV2 Works Internally

1. **Creates entitlement GUID** (if not provided)
2. **Builds entitlement string:** `GUID@investigation_id|task_id`
3. **Embeds in EACH button's value:** `{"entitlement": "...", "reply": "..."}`
4. **Sends via send-notification** to SlackV3 integration
5. **SlackV3 posts** message to Slack via Bot Token
6. **User clicks button** → Slack sends interaction webhook
7. **SlackV3 (Socket Mode) receives** webhook via App Token
8. **Extracts entitlement** from button value
9. **Closes specified task** with button text as result
10. **Posts button text** to War Room (tagged "External")

### 3. Conditional Task (Manual Wait Point)

**CRITICAL PATTERN:**

```yaml
tasks:
  "2":
    id: "2"
    type: condition      # Type MUST be "condition"
    task:
      type: condition
      name: "Wait for Response"
      description: "Manual wait - closed by entitlement"
    nexttasks:
      "Yes":              # MUST match button text EXACTLY
      - "10"
      "No":
      - "20"
      '#default#':        # Fallback for timeout/unknown
      - "30"
    separatecontext: false
```

**Key Points:**
- Type: `condition` (NOT `collection` - that needs forms)
- nexttasks labels: MUST match button text exactly
- No actual conditions defined
- Task waits indefinitely until entitlement closes it
- Entitlement provides which nexttask path to take

### 3.1. Tags for Sub-Playbooks - CRITICAL!

**When using SlackAsk/EmailAsk in sub-playbooks, you MUST add tags:**

```yaml
# SlackAsk task - References tag
scriptName: SlackAskV2
scriptarguments:
  task:
    simple: "my-playbook-wait-4"  # Must match tag!
  message: "Approve?"

# Conditional wait - Must have matching tag
type: condition
tags:
  - "my-playbook-wait-4"  # CRITICAL!
nexttasks:
  "Yes": ["10"]
  "No": ["20"]
```

**Why Required:**
- Main playbooks: Works without tags
- Sub-playbooks: Tags are lookup mechanism

**Without tags in sub-playbooks:**
- Message sends - Buttons appear - User clicks - Task never closes 
### 4. Response Flow

```
User clicks "No" button in Slack
    ↓
Slack webhook → SlackV3 (Socket Mode)
    ↓
SlackV3 extracts entitlement: "abc123@9648|2"
    ↓
Closes Task 2 with result: "No"
    ↓
Playbook routes to nexttasks["No"] → Task 20
    ↓
Task 20 executes (sends confirmation, etc.)
```

## Working Example: Multi-Step Workflow

```yaml
id: multi_step_interactive_demo
tasks:
  "1":
    # STEP 1: Send initial question
    type: regular
    scriptName: SlackAskV2
    scriptarguments:
      channel: "alerts"
      message: "Is this a false positive?"
      option1: "Yes#green"
      option2: "No#red"
      task: "2"        # Links to Task 2
    nexttasks:
      '#none#': ["2"]

  "2":
    # STEP 2: WAIT for user click (manual task)
    type: condition
    task:
      name: "WAIT - Team Response"
    nexttasks:
      "Yes": ["10"]
      "No": ["20"]
    # Entitlement closes this when user clicks

  "10":
    # STEP 3: Confirm YES to Slack
    type: regular
    script: '|||send-notification'
    scriptarguments:
      channel: "alerts"
      message: |
         You chose YES

        What XSOAR did:
        - Marked as resolved
        - Closed ticket
        - Notified team
    nexttasks:
      '#none#': ["50"]

  "20":
    # STEP 3: Confirm NO and escalate
    type: regular
    script: '|||send-notification'
    scriptarguments:
      channel: "alerts"
      message: |
         You chose NO

        What XSOAR did:
        - Escalating to security
        - Creating ticket
    nexttasks:
      '#none#': ["21"]

  "21":
    # STEP 4: Second interactive (nested)
    type: regular
    scriptName: SlackAskV2
    scriptarguments:
      channel: "security"
      message: "Security: Take action?"
      option1: "Investigate#green"
      option2: "Resolve#red"
      task: "22"        # Links to Task 22
    nexttasks:
      '#none#': ["22"]

  "22":
    # STEP 5: WAIT for security click
    type: condition
    task:
      name: "WAIT - Security Response"
    nexttasks:
      "Investigate": ["24"]
      "Resolve": ["25"]

  "24":
    # STEP 6: Confirm security investigation
    type: regular
    script: '|||send-notification'
    scriptarguments:
      message: |
        🔍 Security chose INVESTIGATE

        What XSOAR did:
        - Created case
        - Assigned analyst
        - Started collection

  "50":
    # FINAL: Summary
    type: regular
    script: '|||send-notification'
    scriptarguments:
      message: "Workflow complete!"
```

---

## SlackBlockBuilder Workflow

### Overview

SlackBlockBuilder is the recommended approach for capturing form data including dropdowns, user pickers,
multi-selects, and other interactive elements beyond simple buttons.

**When to use:**
-  Need user pickers (users_select) - returns Slack user ID
-  Need dropdown selections (static_select)
-  Need multi-select inputs
-  Need date picker values
-  Complex forms with multiple input types
-  Want stunning Block Kit visuals

**When NOT to use:**
-  Simple button choices (use SlackAskV2 instead - simpler)

### Prerequisites - UPDATED (No API Key Needed!)

**CRITICAL DISCOVERY:** Despite documentation, **XSOAR API Key is NOT required!**
SlackBlockBuilder v3.3.0+ changed to use war room entries instead of API callbacks.

**Required Configuration in SlackV3:**
-  App Token (xapp-...) - enables Socket Mode
-  Long Running Instance enabled
-  Bot Token (xoxb-...) - for sending messages
-  XSOAR API Key - NOT actually needed (parameter exists but unused in code)

### SlackBlockBuilder Parameters

```yaml
!SlackBlockBuilder
  # REQUIRED
  channel: "team-channel"              # Slack channel
  task: "4"                             # Task ID to close

  # OPTION 1: Use predefined block list
  list_name: "MyBlockList"              # Name from SlackV3 block lists

  # OPTION 2: Use URL to fetch blocks
  blocks_url: "https://..."             # URL returning Block Kit JSON

  # OPTION 3: Inline blocks
  blocks: |                             # Block Kit JSON
    [
      {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Form*"}
      },
      {
        "type": "actions",
        "block_id": "user_assignment",
        "elements": [
          {
            "type": "users_select",
            "action_id": "assigned_user",
            "placeholder": {"type": "plain_text", "text": "Select user"}
          }
        ]
      }
    ]

  # OPTIONAL
  entitlement: ""                       # Pre-created entitlement
  lifetime: "4 hours"                   # Timeout
  thread: ""                            # Thread ID
```

### Complete SlackBlockBuilder Workflow

```yaml
# STEP 1: Send form with SlackBlockBuilder
Task 1: SlackBlockBuilder
  scriptarguments:
    channel: "security"
    task: "2"
    blocks: |
      [
        {
          "type": "section",
          "text": {"type": "mrkdwn", "text": "*Incident Triage*"}
        },
        {
          "type": "actions",
          "block_id": "assignment_block",
          "elements": [
            {
              "type": "users_select",
              "action_id": "assigned_user",
              "placeholder": {"type": "plain_text", "text": "Assign to"}
            },
            {
              "type": "static_select",
              "action_id": "severity",
              "placeholder": {"type": "plain_text", "text": "Severity"},
              "options": [
                {"text": {"type": "plain_text", "text": "High"}, "value": "high"},
                {"text": {"type": "plain_text", "text": "Medium"}, "value": "medium"},
                {"text": {"type": "plain_text", "text": "Low"}, "value": "low"}
              ]
            },
            {
              "type": "button",
              "text": {"type": "plain_text", "text": "Submit"},
              "style": "primary",
              "action_id": "submit"
            }
          ]
        }
      ]

# STEP 2: Conditional wait (button closes this)
Task 2: Conditional Wait
  type: condition
  nexttasks:
    '#default#': ["3"]

# STEP 3: Parse form state with GetSlackBlockBuilderResponse
Task 3: GetSlackBlockBuilderResponse
  scriptarguments:
    entitlement:
      complex:
        root: incident
        accessor: entitlement_id
  # This extracts ALL form values including dropdowns

# STEP 4: Access the captured values
Task 4: Set Variables
  scriptarguments:
    assigned_user:
      complex:
        root: SlackBlockState
        accessor: assignment_block.assigned_user.selected_user
    severity:
      complex:
        root: SlackBlockState
        accessor: assignment_block.severity.selected_option.value
```

### GetSlackBlockBuilderResponse Output Structure

After calling GetSlackBlockBuilderResponse, data is available in context.

**ACTUAL Structure (Tested in XSIAM January 2026):**

```json
{
  "SlackBlockState": {
    "values": {
      "users_select_0": {
        "users_select0": {
          "selected_user": "U0A3A5L191R",
          "type": "users_select"
        }
      },
      "static_select_1": {
        "static_select1": {
          "selected_option": {
            "text": {
              "emoji": true,
              "text": "Approve Containment",
              "type": "plain_text"
            },
            "value": "approve"
          },
          "type": "static_select"
        }
      }
    },
    "xsoar-button-submit": "Successful"
  }
}
```

**Accessing values in playbook (CORRECT paths):**
```yaml
# User picker - returns Slack user ID (e.g., "U0A3A5L191R")
${SlackBlockState.values.users_select_0.users_select0.selected_user}

# Dropdown selection - value
${SlackBlockState.values.static_select_1.static_select1.selected_option.value}

# Dropdown selection - display text
${SlackBlockState.values.static_select_1.static_select1.selected_option.text.text}

# Submit button status
${SlackBlockState.xsoar-button-submit}  # Returns "Successful"
```

**Context path pattern:**
`${SlackBlockState.values.<block_id>.<action_id>.<property>}`

**Note:** Block IDs are auto-generated (users_select_0, static_select_1) based on element order.

### SlackAskV2CustomBlocks (Alternative)

For custom Block Kit WITHOUT capturing dropdown values:

```yaml
!SlackAskV2CustomBlocks
  custom_blocks: |
    {
      "blocks": [
        {
          "type": "section",
          "text": {"type": "mrkdwn", "text": "*Alert Details*"}
        },
        {
          "type": "actions",
          "elements": [
            {
              "type": "users_select",
              "placeholder": {"type": "plain_text", "text": "Assign user"},
              "action_id": "assign_user"
            },
            {
              "type": "button",
              "text": {"type": "plain_text", "text": "Yes"},
              "style": "primary",
              "action_id": "response_yes"
            }
          ]
        }
      ]
    }
  channel: "team-channel"
  task: "4"
  lifetime: "4 hours"
```

**Limitations:**
-  Button clicks captured perfectly
-  Dropdown selections NOT captured (display only)
-  Beautiful UX with custom Block Kit
-  Must stay under 1500 chars for content (3000 total with entitlements)

---

## Entitlements Deep Dive

### What is an Entitlement?

An **entitlement** is a unique identifier that links a Slack button to an XSOAR task. When clicked, it tells XSOAR:
1. Which investigation to update
2. Which task to close
3. What value to return (the button text)

**Format:** `GUID@investigation_id|task_id`
**Example:** `abc123-def456@9648|4`

### Entitlement Types Comparison

| Feature | One-Time Entitlement | Persistent Entitlement |
|---------|---------------------|------------------------|
| **Parameter** | `persistent="false"` (default) | `persistent="true"` |
| **Button Behavior** | Disabled after first click | Can be clicked multiple times |
| **Use Cases** | Approvals, yes/no decisions | Surveys, ongoing monitoring |
| **Task Closure** | Closes task once | Can close task multiple times |
| **War Room Entries** | Single entry per button | Multiple entries per button |
| **Typical Lifetime** | Hours to days | Days to weeks |

### One-Time Entitlement (Default)

**Example:**
```yaml
!SlackAskV2
  channel: "security"
  message: "Approve this change?"
  option1: "Approve#green"
  option2: "Reject#red"
  task: "4"
  persistent: "false"  # Or omit - this is default
```

**Behavior:**
1. User clicks "Approve" → Button disables 2. Task 4 closes with result "Approve"
3. Playbook continues
4. Other users see button as disabled
5. Entitlement expires

**Use for:**
- Binary decisions (approve/reject)
- Workflow gates
- One-time confirmations
- Triage decisions

### Persistent Entitlement

**Example:**
```yaml
!SlackAskV2
  channel: "security"
  message: "Mark incidents you're investigating"
  option1: "Working on it#primary"
  option2: "Completed#green"
  task: "4"
  persistent: "true"
  lifetime: "7 days"
```

**Behavior:**
1. User clicks "Working on it" → Button STAYS enabled 2. Task 4 closes with result "Working on it"
3. Another user can click same/different button
4. Task 4 closes again with new result
5. Process repeats until lifetime expires

**Use for:**
- Status updates
- Ongoing surveys
- Multi-user feedback
- Progress tracking

### Entitlement Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREATED                                                  │
│    SlackAskV2 called → Generates GUID                       │
│    Status: Active, waiting for click                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CLICKED                                                  │
│    User clicks button in Slack                              │
│    Webhook sent to SlackV3 (Socket Mode)                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PROCESSED                                                │
│    SlackV3 extracts entitlement                             │
│    Closes specified task with button text                   │
│    Posts to War Room                                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ ONE-TIME         │    │ PERSISTENT       │
│ Button disabled  │    │ Button active    │
│ Entitlement ends │    │ Wait for next    │
└──────────────────┘    └──────────────────┘
```

### Entitlement Timeout Behavior

When `lifetime` expires without any click:

```yaml
!SlackAskV2
  lifetime: "4 hours"
  defaultResponse: "NoResponse"
```

**What happens:**
1. 4 hours pass with no button click
2. Task automatically closes with result: `"NoResponse"`
3. Playbook routes to nexttasks["NoResponse"] or #default#
4. Buttons become disabled in Slack

**Best practices:**
- Always define `defaultResponse` for timeout scenarios
- Include timeout path in nexttasks or use #default#
- Set realistic lifetimes (consider timezones!)

### Entitlement Security

**Built-in protections:**
-  GUID prevents guessing valid entitlements
-  Investigation ID scopes to specific case
-  Task ID prevents closing wrong tasks
-  Lifetime limits exposure window

**Manual security considerations:**
- Ensure Slack users are authorized (use private channels)
- Monitor War Room for unexpected entries
- Use appropriate lifetimes (don't leave open indefinitely)

---

## Sub-Playbook Tag References

### The Problem

When calling sub-playbooks that use SlackAskV2, you need a way to reference tasks created by the sub-playbook from the parent playbook.

### Solution: Tag-Based Task References

**In Sub-Playbook (Wiz-Send-Message-to-Team-Nested.yml):**
```yaml
tasks:
  "4":
    id: "4"
    type: condition
    task:
      name: "Wait for Response"
    tags:
      - "team_response_wait"  # TAG for parent reference
    nexttasks:
      "Yes": ["10"]
      "No": ["20"]
```

**In Parent Playbook:**
```yaml
tasks:
  "5":
    id: "5"
    type: playbook
    task:
      name: "Send to Security Team"
      playbookName: Wiz-Send-Message-to-Team-Nested
    nexttasks:
      '#none#': ["6"]

  "6":
    id: "6"
    type: regular
    scriptName: Print
    scriptarguments:
      value:
        # Access sub-playbook task output by TAG
        complex:
          root: "playbookQuery"
          filters:
            - - left:
                  value:
                    simple: "playbookQuery.task.tags"
                  iscontext: true
                operator: containsGeneral
                right:
                  value:
                    simple: "team_response_wait"
          accessor: "outputs.response"
```

### Tag Naming Best Practices

**Use descriptive, hierarchical tags:**
```yaml
tags:
  - "slack_team_response"           # Good: Specific purpose
  - "approval_wait"                 # Good: Clear intent
  - "security_decision_point"       # Good: Descriptive

  - "wait"                          # Bad: Too generic
  - "task4"                         # Bad: Not meaningful
  - "temp"                          # Bad: Unclear purpose
```

### Common Tag Patterns

```yaml
# Approval workflows
tags: ["manager_approval_wait"]

# Team routing
tags: ["team_selection_wait"]

# Escalation
tags: ["escalation_decision_wait"]

# Multi-stage
tags: ["stage1_response", "triage"]
tags: ["stage2_response", "investigation"]
```

### Accessing Tagged Task Results

**Method 1: playbookQuery with filter**
```yaml
complex:
  root: "playbookQuery"
  filters:
    - - left:
          value:
            simple: "playbookQuery.task.tags"
          iscontext: true
        operator: containsGeneral
        right:
          value:
            simple: "your_tag_here"
  accessor: "outputs.result"
```

**Method 2: Direct context path (if tag is unique)**
```yaml
simple: "${playbookQuery(val.task.tags.indexOf('your_tag') != -1).outputs.result}"
```

---

## Best Practices

### 1. Naming Conventions

**Button Text = nexttasks Label:**
```yaml
option1: "Start Investigation#green"
# Creates button with text: "Start Investigation"

nexttasks:
  "Start Investigation":  # MUST match exactly (case-sensitive)
  - "10"
```

### 2. Task ID References

Always reference tasks by ID string:
```yaml
task: "4"  # String, not integer
```

### 3. Multiple Manual Waits

**CRITICAL: Add Sleep task before EVERY SlackAskV2 call after the first one!**

You can chain multiple interactive steps, but MUST add 5-second sleep between them:

```yaml
Task 1: SlackAskV2 (ask question 1) → task="2"
Task 2: Conditional wait
Task 10: send-notification (confirm)
Task 10.5: Sleep 5 seconds  # REQUIRED before second SlackAskV2!
Task 11: SlackAskV2 (ask question 2) → task="12"
Task 12: Conditional wait (second manual interaction)
Task 20: send-notification (confirm)
Task 20.5: Sleep 5 seconds  # REQUIRED before third SlackAskV2!
Task 21: SlackAskV2 (ask question 3) → task="22"
Task 22: Conditional wait
```

**Why Sleep is Required:**
- First entitlement needs time to fully process/cleanup
- Without sleep: Second entitlement doesn't register properly
- Symptom: Second SlackAskV2 message sends, but button clicks don't close task
- Solution: Add Sleep task (5 seconds) between consecutive SlackAskV2 calls

### 4. Notification Messages

Always send confirmation back to Slack showing:
- What the user chose
- What XSOAR did in response
- What's happening next

```yaml
message: |
   You chose: "${response}"

  What XSOAR did:
  - Action 1
  - Action 2
  - Action 3

  Next: ...
```

## Troubleshooting

### Issue: Task Closes Immediately

**Cause:** Using `type: condition` with actual conditions defined
**Fix:** Use `type: condition` with NO conditions, only nexttasks labels

### Issue: Response Not Captured

**Causes:**
1. SlackV3 not running as long-running instance
2. App Token not configured
3. Task ID mismatch (task parameter ≠ conditional task ID)
4. Button text doesn't match nexttasks label

**Check:**
```bash
!GetInstances | grep SlackV3
# Verify: state = active
```

### Issue: Dropdown Not Captured

**Cause:** SlackAskV2 only captures button clicks, not form state
**Solution:** Use SlackBlockBuilder with:
- XSOAR API Key configured in SlackV3
- GetSlackBlockBuilderResponse to parse state

### Issue: Routing to Wrong Path

**Cause:** Button text doesn't match nexttasks label exactly
**Fix:** Ensure exact match (case-sensitive, no extra spaces)

```yaml
# Button sends: "No - Needs Investigation"
nexttasks:
  "No - Needs Investigation":  # Must match exactly!
  - "11"
```

## Production Deployment

### 1. Configure SlackV3

```
Settings → Integrations → SlackV3
- App Token: xapp-... (for Socket Mode)
- Bot Token: xoxb-... (for sending)
- Long Running:  Enabled
- Trust any certificate:  Enabled
```

### 2. Test Flow

```
1. Create test playbook
2. Run on test alert/case
3. Click buttons in Slack
4. Verify routing works
5. Check all confirmations sent
```

### 3. Production Playbook Structure

```
Main Playbook:
  - Query data
  - Route by team
  - Call sub-playbook for each team

Sub-Playbook (Team Message):
  - SlackAskV2 to team channel
  - Conditional wait
  - Route by response
  - Send confirmations
  - Call escalation sub-playbook if needed

Sub-Playbook (Escalation):
  - SlackAskV2 to security
  - Conditional wait
  - Handle security response
```

## Integration Example: Third-Party Security Tool Alert Routing

**Scenario:** Route cloud security alerts from external monitoring tools to appropriate teams via Slack for collaborative triage

**Flow:**
1. Correlation rule triggers on external_cloud_raw dataset (configure for your security tool)
2. Main playbook queries external security tool data
3. Routes by cloud platform (AWS/GCP/Azure)
4. Routes by subscription to appropriate team channel
5. SlackAskV2 sends interactive message to team: "Severity assessment?"
6. Team responds → XSOAR captures decision
7. If False Positive: Mark resolved in source system
8. If Confirmed: Escalate to security operations team
9. Security team receives follow-up interactive message
10. Final remediation actions based on security response

**Example Files (Template - Customize for your tool):**
- Main: `ExternalTool-Alert-Slack-Triage.yml`
- Sub: `Send-Team-Alert-Message.yml`
- Custom Script: `SlackAskV2CustomBlocks.yml` (for dropdown support)

**Note:** Replace "ExternalTool" and dataset names with your actual security tool (e.g., Wiz, Prisma Cloud, Orca, Aqua, etc.)

## Advanced: Custom Blocks with Dropdown - WORKING!

**FULLY WORKING** as of January 2026:

### Complete Working Example

```yaml
# Task 3: Send stunning Block Kit with user picker + dropdown
"3":
  type: regular
  scriptName: SlackBlockBuilder
  scriptarguments:
    blocks_url:
      simple: "https://app.slack.com/block-kit-builder#%7B%22blocks%22:%5B%7B%22type%22:%22header%22,%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22%F0%9F%9A%A8%20Security%20Alert%22,%22emoji%22:true%7D%7D,%7B%22type%22:%22section%22,%22fields%22:%5B%7B%22type%22:%22mrkdwn%22,%22text%22:%22*Issue:*%5Cn${incident.id}%22%7D,%7B%22type%22:%22mrkdwn%22,%22text%22:%22*Severity:*%5CnHigh%22%7D%5D%7D,%7B%22type%22:%22divider%22%7D,%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*Assign%20to:*%22%7D,%22accessory%22:%7B%22type%22:%22users_select%22,%22placeholder%22:%7B%22type%22:%22plain_text%22,%22text%22:%22Select%20user%22%7D,%22action_id%22:%22user-select%22%7D%7D,%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*Action:*%22%7D,%22accessory%22:%7B%22type%22:%22static_select%22,%22options%22:%5B%7B%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22Approve%22%7D,%22value%22:%22approve%22%7D,%7B%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22Investigate%22%7D,%22value%22:%22investigate%22%7D%5D,%22action_id%22:%22action-select%22%7D%7D%5D%7D"
    channel_id:
      simple: "C0A9GLWQPPY"
    task:
      simple: "4"
  nexttasks:
    '#none#': ["4"]

# Task 4: Wait for Submit
"4":
  type: condition
  nexttasks:
    '#default#': ["5"]

# Task 5: Parse response
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
        User: ${SlackBlockState.values.users_select_0.users_select0.selected_user}
        Action: ${SlackBlockState.values.static_select_1.static_select1.selected_option.value}
```

### What Gets Captured

| Element Type | Context Path | Example Value |
|--------------|--------------|---------------|
| users_select | `${SlackBlockState.values.users_select_0.users_select0.selected_user}` | `U0A3A5L191R` |
| static_select value | `${SlackBlockState.values.static_select_1.static_select1.selected_option.value}` | `approve` |
| static_select text | `${SlackBlockState.values.static_select_1.static_select1.selected_option.text.text}` | `Approve Containment` |
| Submit status | `${SlackBlockState.xsoar-button-submit}` | `Successful` |

### Key Discovery

**NO API KEY REQUIRED!** The XSOAR API Key parameter in SlackV3 is defined but never used in code.
SlackBlockBuilder v3.3.0+ writes responses to war room, GetSlackBlockBuilderResponse reads them.

---

**Documentation Version:** 2.0
**Tested On:** Cortex XSIAM SaaS
**SlackV3 Version:** 3.5.37
"""


async def get_slack_interactive_workflows_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for building interactive Slack workflows in XSIAM.

    **Complete Reference Including:**

    1. **SlackAskV2 Complete Reference**
       - All 15 parameters explained in detail
       - Required vs optional parameters
       - Internal workflow mechanics

    2. **SlackBlockBuilder Workflow**
       - Full workflow with GetSlackBlockBuilderResponse
       - Capturing dropdown, multi-select, date picker values
       - SlackBlockState context structure
       - Prerequisites and configuration

    3. **Entitlements Deep Dive**
       - One-time vs persistent entitlements comparison table
       - Lifecycle diagrams
       - Security considerations
       - Timeout behavior

    4. **Sub-Playbook Tag References**
       - Tag-based task references from parent playbooks
       - Best practices for tag naming
       - Access patterns with playbookQuery

    5. **Critical Requirements**
       - Sleep between multiple SlackAskV2 calls (10 seconds)
       - 3000 character Slack message limit
       - DeleteContext before SlackAskV2CustomBlocks

    6. **Architecture & Patterns**
       - Conditional task patterns for manual waits
       - Multi-step interactive workflows
       - Custom Block Kit integration
       - Production deployment best practices

    7. **Troubleshooting**
       - Common errors and solutions
       - Debugging entitlement issues
       - Message size problems

    Based on real-world production debugging experience including the 3000 character
    limit discovery and Socket Mode entitlement patterns.

    Returns:
        Complete markdown guide with working examples and reference tables
    """
    return SLACK_INTERACTIVE_WORKFLOWS_GUIDE


class SlackInteractiveWorkflowsGuide(BaseModule):
    """
    MCP tool for Slack interactive workflow documentation.

    Provides comprehensive reference guide for building Slack integrations with XSIAM.

    **Coverage:**
    - SlackAskV2: All 15 parameters with detailed explanations
    - SlackBlockBuilder: Complete workflow for capturing dropdown/form values
    - Entitlements: One-time vs persistent comparison, lifecycle, security
    - Sub-Playbook Tags: Tag-based task references and access patterns
    - Critical Requirements: Sleep timings, message size limits, DeleteContext
    - Architecture: Conditional tasks, multi-step flows, custom Block Kit
    - Troubleshooting: Common errors, debugging, production issues

    **Based on real production experience:**
    - 3000 character Slack message limit discovery
    - Socket Mode entitlement patterns
    - Multi-step workflow debugging
    - SlackV3 configuration requirements

    **Perfect for:**
    - Building Slack-based approval workflows
    - Interactive security alert triage
    - Team escalation with user interaction
    - Custom Block Kit message design
    - Sub-playbook communication patterns

    Tools provided:
        - get_slack_interactive_workflows_guide: Complete Slack integration reference
    """

    def register_tools(self):
        self._add_tool(get_slack_interactive_workflows_guide)

    def register_resources(self):
        """Slack guide module doesn't register resources."""
        pass
