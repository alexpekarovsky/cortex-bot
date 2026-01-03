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

Based on: Real-world implementation for Wiz Cloud Security Alert triage workflow
"""

from mcp import Context
from ..base_module import BaseModule

SLACK_INTERACTIVE_WORKFLOWS_GUIDE = """
# Slack Interactive Workflows for Cortex XSIAM

## ⚠️ CRITICAL REQUIREMENT: Sleep Between Multiple SlackAskV2 Calls

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

### 2. SlackAskV2 Script

Sends interactive message with buttons and creates entitlement for response tracking.

**Parameters:**
```yaml
!SlackAskV2
  channel: "team-channel"
  message: "Question text"
  option1: "Yes#green"           # Button 1 (green)
  option2: "No#red"              # Button 2 (red)
  additionalOptions: "Maybe#black"  # Button 3+ (optional)
  task: "4"                      # CRITICAL: Task ID to close
  lifetime: "4 hours"            # Timeout period
  defaultResponse: "NoResponse"  # Response if timeout
  reply: "Thank you!"            # Reply after click
```

**How It Works:**
1. Creates entitlement GUID
2. Builds entitlement string: `GUID@investigation_id|task_id`
3. Embeds in EACH button's value: `{"entitlement": "...", "reply": "..."}`
4. Sends via `send-notification` to SlackV3
5. SlackV3 posts to Slack
6. User clicks button → Slack sends webhook
7. SlackV3 (Socket Mode) receives webhook
8. Extracts entitlement, closes specified task
9. Posts button text to War Room (tagged "External")

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
        ✅ You chose YES

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
        🔴 You chose NO

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

## Custom Block Kit Support

### Using SlackAskV2CustomBlocks (Custom Script)

For advanced Block Kit with dropdowns:

```yaml
SlackAskV2CustomBlocks:
  custom_blocks: |
    {
      "blocks": [
        {
          "type": "section",
          "text": {"type": "mrkdwn", "text": "*Alert*"}
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

**How It Works:**
- Script injects entitlements into ALL buttons
- Each button can close the waiting task
- Dropdown is included in UI but response capture needs additional parsing

### Capturing Dropdown Selections

**With SlackBlockBuilder** (requires XSOAR API Key in SlackV3):
```yaml
Task 1: SlackBlockBuilder with blocks_url or list_name
Task 4: Conditional wait
Task 5: GetSlackBlockBuilderResponse  # Parses full state
# ${SlackBlockState.block_id.action_id.selected_user}
```

**Current Limitation:**
SlackAskV2 captures button clicks perfectly, but dropdown selections require:
- Either SlackBlockBuilder (with API key configured)
- Or custom parsing of Slack webhook payload

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
  ✅ You chose: "${response}"

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
- Long Running: ✅ Enabled
- Trust any certificate: ✅ Enabled
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

## Real-World Example: Wiz Cloud Security Triage

**Scenario:** Route Wiz cloud security alerts to teams via Slack for triage

**Flow:**
1. Correlation rule triggers on wiz_cloud_raw dataset
2. Main playbook queries Wiz data
3. Routes by cloud platform (AWS/GCP/Azure)
4. Routes by subscription to team channel
5. SlackAskV2 sends to team: "Is this FP?"
6. Team responds → XSOAR captures
7. If YES: Mark resolved in Wiz
8. If NO: Escalate to security team
9. Security team gets second interactive message
10. Final actions based on security response

**Key Files:**
- Main: `Wiz-Cloud-Issue-Slack-Triage.yml`
- Sub: `Wiz-Send-Team-Message.yml`
- Custom Script: `SlackAskV2CustomBlocks.yml` (for dropdown support)

## Advanced: Custom Blocks with Dropdown

**Coming Soon:** Fully working custom Block Kit with:
- users_select dropdown for assignment
- Multiple styled buttons
- Full state capture including dropdown selection
- Complete entitlement-based routing

**Current Status:** Basic buttons work via SlackAskV2. Dropdown requires additional configuration.

---

**Documentation Version:** 1.0
**Last Updated:** 2025-12-22
**Tested On:** Cortex XSIAM SaaS
**SlackV3 Version:** 3.5.37
"""


async def get_slack_interactive_workflows_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for building interactive Slack workflows in XSIAM.

    Covers:
    - SlackAskV2 usage and entitlements
    - Conditional task patterns for manual waits
    - Multi-step interactive workflows
    - Custom Block Kit integration
    - Production deployment best practices
    - Worker saturation issue and fixes
    - Sub-playbook architecture

    Returns:
        Complete markdown guide with examples
    """
    return SLACK_INTERACTIVE_WORKFLOWS_GUIDE


class SlackInteractiveWorkflowsGuide(BaseModule):
    """
    MCP tool for Slack interactive workflow documentation.

    Provides complete guide for building Slack integrations with XSIAM including:
    - SlackAskV2 entitlement patterns
    - Multi-step workflows with sub-playbooks
    - SlackBlockBuilder usage
    - Worker saturation issues and fixes
    - Production deployment patterns

    Based on real-world Wiz Cloud Security Alert triage implementation.

    Tools provided:
        - get_slack_interactive_workflows_guide: Complete Slack workflow guide
    """

    def register_tools(self):
        self._add_tool(get_slack_interactive_workflows_guide)
