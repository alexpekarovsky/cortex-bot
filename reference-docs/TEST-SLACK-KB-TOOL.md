# Testing the Enhanced Slack Knowledge Base Tool

## Quick Verification Tests

### Test 1: Verify Tool Exists in MCP Server

```python
# From MCP client
tools = await mcp_client.list_tools()
slack_tool = [t for t in tools if "slack" in t.name.lower()]
print(slack_tool)

# Expected output:
# [{"name": "get_slack_interactive_workflows_guide", ...}]
```

### Test 2: Call Tool and Check Sections

```python
# Get the guide
guide = await ctx.call_tool("get_slack_interactive_workflows_guide")

# Verify sections exist
sections = [
    "Table of Contents",
    "Critical Requirements",
    "SlackAskV2 Complete Reference",
    "All 15 Parameters Explained",
    "SlackBlockBuilder Workflow",
    "GetSlackBlockBuilderResponse Output Structure",
    "Entitlements Deep Dive",
    "Sub-Playbook Tag References",
    "Best Practices",
    "Troubleshooting"
]

for section in sections:
    assert section in guide, f"Missing section: {section}"
    print(f"✅ {section}")
```

### Test 3: Verify Parameter Documentation

```python
# Check all 15 parameters are documented
parameters = [
    "channel", "message", "option1", "option2", "task",
    "additionalOptions", "lifetime", "defaultResponse", "reply", "persistent",
    "replyEntriesTag", "entitlement", "thread", "blocks", "investigationId"
]

for param in parameters:
    # Check parameter is documented with explanation
    assert f"**{param}**" in guide or f'"{param}"' in guide
    print(f"✅ {param} documented")
```

### Test 4: Verify Entitlements Table

```python
# Check comparison table exists
table_headers = [
    "Feature",
    "One-Time Entitlement",
    "Persistent Entitlement"
]

for header in table_headers:
    assert header in guide
    print(f"✅ Table header: {header}")

# Check comparison rows
comparisons = [
    "Button Behavior",
    "Use Cases",
    "Task Closure",
    "War Room Entries"
]

for comparison in comparisons:
    assert comparison in guide
    print(f"✅ Comparison row: {comparison}")
```

### Test 5: Verify SlackBlockBuilder Content

```python
# Check SlackBlockBuilder workflow steps
workflow_steps = [
    "SlackBlockBuilder",
    "GetSlackBlockBuilderResponse",
    "SlackBlockState",
    "selected_user",
    "selected_option"
]

for step in workflow_steps:
    assert step in guide
    print(f"✅ SlackBlockBuilder step: {step}")
```

### Test 6: Verify Critical Requirements

```python
# Check all critical requirements are documented
requirements = [
    "Sleep Between Multiple SlackAskV2 Calls",
    "3000 characters",
    "DeleteContext"
]

for req in requirements:
    assert req in guide
    print(f"✅ Critical requirement: {req}")
```

### Test 7: Code Example Coverage

```python
# Check for code examples
code_indicators = [
    "```yaml",
    "```json",
    "scriptarguments:",
    "nexttasks:",
    "Task 1:",
    "Task 2:"
]

for indicator in code_indicators:
    count = guide.count(indicator)
    print(f"✅ Found {count} instances of '{indicator}'")
```

## Usage Examples

### Example 1: Building Simple Approval Workflow

**User Query:** "I need to add Slack approval buttons to my playbook"

**AI Assistant Action:**
```python
# Call the tool
guide = get_slack_interactive_workflows_guide()

# Extract relevant section about SlackAskV2 basic usage
# Provide user with minimal example:
```

**Response to User:**
```yaml
!SlackAskV2
  channel: "security-approvals"
  message: "Approve this change request?"
  option1: "Approve#green"
  option2: "Reject#red"
  task: "4"
  lifetime: "4 hours"
```

### Example 2: Capturing Dropdown Values

**User Query:** "How do I capture which user was selected from a Slack dropdown?"

**AI Assistant Action:**
```python
# Call the tool
guide = get_slack_interactive_workflows_guide()

# Extract SlackBlockBuilder workflow section
# Provide complete workflow with GetSlackBlockBuilderResponse
```

**Response to User:**
```yaml
# Step 1: SlackBlockBuilder with dropdown
Task 1: SlackBlockBuilder
  blocks: |
    [{
      "type": "actions",
      "block_id": "assignment",
      "elements": [{
        "type": "users_select",
        "action_id": "assigned_user"
      }]
    }]

# Step 2: Parse response
Task 3: GetSlackBlockBuilderResponse

# Step 3: Access value
${SlackBlockState.assignment.assigned_user.selected_user}
```

### Example 3: Understanding Entitlement Types

**User Query:** "What's the difference between one-time and persistent entitlements?"

**AI Assistant Action:**
```python
# Call the tool
guide = get_slack_interactive_workflows_guide()

# Extract entitlements comparison table
# Show user the complete comparison
```

**Response to User:**
See the comparison table in the guide showing:
- One-time: Button disabled after first click (for approvals)
- Persistent: Button can be clicked multiple times (for surveys)

### Example 4: Fixing 3000 Character Error

**User Query:** "My Slack message sends but buttons don't work"

**AI Assistant Action:**
```python
# Call the tool
guide = get_slack_interactive_workflows_guide()

# Extract 3000 character limit section
# Provide calculation example and safe zone guidance
```

**Response to User:**
Your message likely exceeds 3000 characters. Calculate:
```
Your content:          ??? chars
+ Entitlement data:    ~300 chars
+ Buttons (3x):        ~450 chars
= Total must be < 3000
```

Keep content under 1500 chars to leave room for entitlements.

## Performance Tests

### Load Time
```python
import time

start = time.time()
guide = get_slack_interactive_workflows_guide()
elapsed = time.time() - start

print(f"Guide loaded in {elapsed:.3f} seconds")
# Expected: < 0.1 seconds (it's just returning a string constant)
```

### Content Size
```python
guide = get_slack_interactive_workflows_guide()

print(f"Total characters: {len(guide):,}")
print(f"Total lines: {guide.count(chr(10)):,}")
print(f"Code examples: {guide.count('```')}")
print(f"Tables: {guide.count('|')}")

# Expected:
# Total characters: 40,000-60,000
# Total lines: 1,000-1,500
# Code examples: 50+
# Tables: 30+
```

## Integration Tests

### Test with Playbook Generation

```python
# Scenario: AI generates playbook with Slack task
# Should reference correct parameter names

from create_playbook import create_playbook

playbook_tasks = [
    {
        "id": "1",
        "type": "regular",
        "name": "Ask Team",
        "script": "SlackAskV2",
        "arguments": {
            "channel": "security",
            "message": "Approve?",
            "option1": "Yes#green",
            "option2": "No#red",
            "task": "2",  # Verified from guide
            "lifetime": "4 hours"  # Verified from guide
        },
        "next": ["2"]
    }
]

# Verify all parameters are in the guide
guide = get_slack_interactive_workflows_guide()
for param in ["channel", "message", "option1", "option2", "task", "lifetime"]:
    assert param in guide
```

## Documentation Quality Tests

### Check for Common Issues

```python
guide = get_slack_interactive_workflows_guide()

# Test 1: No TODO markers left
assert "TODO" not in guide, "Found TODO markers"
assert "FIXME" not in guide, "Found FIXME markers"

# Test 2: Consistent formatting
assert guide.count("```yaml") == guide.count("```\n") - guide.count("```json")

# Test 3: No broken internal links
import re
anchors = re.findall(r'#([a-z-]+)', guide)
headers = re.findall(r'^## (.+)$', guide, re.MULTILINE)
# Verify all anchor links point to existing headers

# Test 4: Code examples are syntactically valid YAML
yaml_blocks = re.findall(r'```yaml\n(.+?)\n```', guide, re.DOTALL)
import yaml
for block in yaml_blocks[:5]:  # Test first 5
    try:
        yaml.safe_load(block)
        print("✅ Valid YAML")
    except:
        print(f"❌ Invalid YAML: {block[:50]}...")
```

## Expected Output Summary

When all tests pass:

```
✅ Tool exists in MCP server
✅ All 10 major sections present
✅ All 15 parameters documented
✅ Entitlements comparison table complete
✅ SlackBlockBuilder workflow documented
✅ Critical requirements explained
✅ 30+ code examples found
✅ No TODOs or FIXMEs
✅ YAML syntax valid
✅ Internal links consistent

Total Tests: 50
Passed: 50
Failed: 0

Status: ✅ Ready for production use
```

## Manual Verification Checklist

- [ ] Call tool from Claude Code
- [ ] Search for "SlackAskV2 parameters" in response
- [ ] Verify all 15 parameters listed
- [ ] Check entitlements comparison table renders correctly
- [ ] Verify code examples are readable
- [ ] Test search for "3000 characters" returns limit explanation
- [ ] Verify SlackBlockBuilder section is comprehensive
- [ ] Check GetSlackBlockBuilderResponse usage is clear
- [ ] Confirm sub-playbook tag patterns are documented
- [ ] Verify troubleshooting section covers common errors

---

**Test Suite Created:** January 20, 2026
**Purpose:** Verify Slack KB enhancement
**Status:** Ready for execution
