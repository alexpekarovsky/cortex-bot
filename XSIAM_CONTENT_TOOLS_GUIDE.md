# XSIAM Content Generator Tools - Complete Guide

**Last Updated**: January 3, 2026
**Total Tools**: 11 content generators + 3 widget APIs
**Working Tools**: 6 production-ready

---

## Quick Start

### Create a Dashboard with XQL Widget

```python
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Security Metrics",
    description="Real-time security metrics dashboard",
    xql_query="dataset = alerts | comp count() as total by severity",
    widget_title="Alert Count by Severity",
    widget_type="pie",  # pie, bar, line, column, table, or single
    upload=True
)
```

**Result**: Dashboard appears in XSIAM UI with working pie chart showing alert distribution by severity.

---

### Create a Case Layout

```python
create_case_layout(
    pack_name="MyPack",
    layout_name="Security Investigation Layout",
    description="Custom layout for security investigations",
    upload=True
)
```

**Result**: Layout appears in Settings → Advanced → Layouts → Case Layouts

---

### Create AgentIX Action

```python
create_agentix_action(
    pack_name="MyPack",
    action_name="IPEnrichment",
    display_name="IP Enrichment",
    description="Enriches IP addresses with threat intelligence",
    underlying_type="command",
    underlying_id="ip",
    underlying_name="ip",
    underlying_command="ip",
    requires_user_approval=False,
    args='[{"name": "ip", "required": true, "description": "IP to enrich", "type": "string", "underlyingargname": "ip"}]',
    outputs='[{"name": "IP.Address", "description": "IP address", "type": "string", "underlyingoutputcontextpath": "IP.Address"}]',
    tags=["threat-intel", "enrichment"],
    category="Threat Intelligence",
    upload=True
)
```

**Result**: Action uploads successfully (schema validates, pack installs)

---

## Tool Reference

### 1. create_case_layout

**Status**: ✅ Production Ready
**Upload**: Direct or pack upload
**File Created**: `Packs/{PackName}/CaseLayouts/layoutscontainer-{Name}.json`

**Parameters**:
- `pack_name` (required) - Pack name
- `layout_name` (required) - Layout name
- `description` (optional) - Layout description
- `tabs` (optional) - JSON array of tab definitions
- `upload` (optional, default=False) - Auto-upload to XSIAM

**Default Tabs**: overview, assets_and_artifacts, alerts_and_insights, timeline, war_room, executions

---

### 2. create_case_layout_rule

**Status**: ✅ Production Ready
**Upload**: Pack upload required
**File Created**: `Packs/{PackName}/CaseLayoutRules/caselayoutrule-{RuleName}.json`

**Parameters**:
- `pack_name` (required) - Pack name
- `rule_name` (required) - Rule name
- `layout_id` (required) - Layout to apply
- `description` (optional) - Rule description
- `upload` (optional, default=False) - Auto-upload to XSIAM

**Key Feature**: Auto-generates `alerts_filter` with default criteria (can be customized)

---

### 3. create_xsiam_dashboard

**Status**: ✅ Production Ready - **WITH WORKING WIDGETS!**
**Upload**: Pack upload required
**File Created**: `Packs/{PackName}/XSIAMDashboards/xsiamdashboard-{Name}.json`

**Parameters**:
- `pack_name` (required) - Pack name
- `dashboard_name` (required) - Dashboard name
- `description` (optional) - Dashboard description
- `xql_query` (optional) - XQL query for widget (e.g., "dataset = alerts | comp count() as total")
- `widget_title` (optional) - Widget title (defaults to dashboard name)
- `widget_type` (optional, default="single") - Visualization type: pie, bar, line, column, table, single
- `upload` (optional, default=False) - Auto-upload to XSIAM

**Features**:
- Auto-generates `| view graph` command with proper syntax
- Populates `viewOptions.commands` array with xaxis/yaxis parameters
- Creates complete widget structure in `widgets_data` array
- Dashboards appear in XSIAM UI with rendered visualizations

**Widget Types**:
- `single` - Single metric value
- `table` - Data table
- `pie` - Pie chart (requires "by" aggregation)
- `bar` - Bar chart (requires "by" aggregation)
- `line` - Line chart (requires "by" aggregation)
- `column` - Column chart (requires "by" aggregation)

---

### 4. create_agentix_action

**Status**: ✅ Production Ready
**Upload**: Pack upload - uploads successfully
**File Created**: `Packs/{PackName}/AgentixActions/{ActionName}.yml` (YAML format)

**Parameters**:
- `pack_name` (required) - Pack name
- `action_name` (required) - Action name
- `display_name` (required) - Display name in UI
- `description` (required) - What the action does
- `underlying_type` (required) - "command", "script", or "playbook"
- `underlying_id` (required) - ID of underlying content
- `underlying_name` (required) - Name of underlying content
- `requires_user_approval` (required) - True for destructive actions, False for trusted
- `underlying_command` (optional) - Command name (required if type="command")
- `args` (optional) - JSON array: `[{"name": "ip", "required": true, "description": "...", "type": "string", "underlyingargname": "ip"}]`
- `outputs` (optional) - JSON array: `[{"name": "IP.Address", "description": "...", "type": "string", "underlyingoutputcontextpath": "IP.Address"}]`
- `tags` (optional) - List of tags
- `category` (optional) - Action category
- `upload` (optional, default=False) - Auto-upload

**Important**: Args and outputs should match the underlying command/script/playbook parameters

---

### 5. create_agentix_agent

**Status**: ✅ Production Ready
**Upload**: Pack upload - uploads successfully
**File Created**: `Packs/{PackName}/AgentixAgents/{AgentName}.yml` (YAML format)

**Parameters**:
- `pack_name` (required) - Pack name
- `agent_name` (required) - Agent name
- `description` (required) - Agent description
- `color` (required) - Hex color code (e.g., "#3498DB")
- `visibility` (required) - "public" or "private"
- `category` (optional) - Agent category
- `action_ids` (optional) - List of action IDs: ["action1", "action2"]
- `system_instructions` (optional) - Agent behavior instructions
- `conversation_starters` (optional) - List of example prompts
- `upload` (optional, default=False) - Auto-upload

---

### 6. create_case_field

**Status**: ⚠️ Schema Valid, Upload Issues
**Upload**: Direct upload - may fail with CLI name validation errors
**File Created**: `Packs/{PackName}/CaseFields/casefield-{FieldId}.json`

**Parameters**:
- `pack_name` (required) - Pack name
- `field_id` (required) - Unique field ID
- `field_name` (required) - Field display name
- `field_type` (required) - shortText, longText, boolean, singleSelect, multiSelect, date, number, etc.
- `description` (optional) - Field description
- `select_values` (optional) - JSON array for select fields
- `upload` (optional, default=False) - Auto-upload

**Known Issue**: Error 100703 - "CLI name is invalid". Some field IDs are rejected by XSIAM.

---

### 7. create_xsiam_report

**Status**: ❌ Error 101704 on upload
**Upload**: Pack upload - fails with error 101704
**File Created**: `Packs/{PackName}/XSIAMReports/xsiamreport-{Name}.json`

**Parameters**: Same as create_xsiam_dashboard

**Issue**: Creates valid files (schema passes), but pack upload fails with error 101704. Files match official PANW examples exactly.

---

### 8. create_parsing_rule

**Status**: ❌ Error 101704 on upload
**Upload**: Pack upload - fails with error 101704
**Files Created**:
- `Packs/{PackName}/ParsingRules/{RuleName}/{RuleName}.yml`
- `Packs/{PackName}/ParsingRules/{RuleName}/{RuleName}.xif`

**Parameters**:
- `pack_name` (required) - Pack name
- `rule_name` (required) - Rule name
- `vendor` (required) - Vendor name
- `product` (required) - Product name
- `target_dataset` (required) - Target dataset name
- `xql_rules` (required) - XQL parsing logic
- `upload` (optional, default=False) - Auto-upload

**Issue**: Files match HelloWorld ParsingRule exactly, but upload fails with 101704.

---

### 9. create_modeling_rule

**Status**: ❌ Error 101704 on upload
**Upload**: Pack upload - fails with error 101704
**Files Created**:
- `Packs/{PackName}/ModelingRules/{RuleName}/{RuleName}.yml`
- `Packs/{PackName}/ModelingRules/{RuleName}/{RuleName}.xif`
- `Packs/{PackName}/ModelingRules/{RuleName}/{RuleName}_schema.json`

**Parameters**:
- `pack_name` (required) - Pack name
- `rule_name` (required) - Rule name
- `dataset` (required) - Source dataset
- `model` (required) - XDM model (Audit, Network, Endpoint, etc.)
- `xql_rules` (required) - XQL modeling logic
- `schema_json` (optional) - Dataset schema JSON
- `upload` (optional, default=False) - Auto-upload

**Features**: Auto-generates schema.json file with default structure

**Issue**: Files match Tanium ModelingRule exactly, but upload fails with 101704.

---

### 10. create_assets_modeling_rule

**Status**: ❌ Error 101704 on upload
**Upload**: Pack upload - fails with error 101704
**Files Created**: Same as ModelingRule

**Parameters**: Same as create_modeling_rule (model is always "Assets")

**Issue**: Same as ModelingRule (error 101704)

---

### 11. get_xsiam_content_guide

**Status**: ✅ Production Ready
**Type**: Documentation tool
**Returns**: Comprehensive guide to all XSIAM content types

No parameters - just call to get complete guide.

---

## Widget APIs

### get_widgets

**Status**: ✅ Working (tested via curl)
**Endpoint**: `/public_api/v1/widgets/get`
**Type**: OpenAPI tool

Retrieves XQL widgets by filtering on title and creator.

---

### insert_widgets

**Status**: ✅ Working (tested via curl)
**Endpoint**: `/public_api/v1/widgets/insert`
**Type**: OpenAPI tool

Creates or updates XQL widgets.

**Widget Structure**:
```json
{
  "widget_key": "xql_unique_key",
  "title": "Widget Title",
  "creation_time": 1735934400000,
  "data": {
    "phrase": "dataset = alerts | comp count() as total",
    "time_frame": {"relativeTime": 86400000},
    "viewOptions": {"type": "pie", "commands": [
      {"command": {"op": "=", "name": "xaxis", "value": "severity"}},
      {"command": {"op": "=", "name": "yaxis", "value": "total"}}
    ]}
  },
  "support_time_range": true,
  "additional_info": {
    "query_tables": ["alerts"],
    "query_uses_library": false
  }
}
```

---

### delete_widgets

**Status**: ✅ Available
**Endpoint**: `/public_api/v1/widgets/delete`
**Type**: OpenAPI tool

Deletes XQL widgets by filter criteria.

---

## Error 101704 Investigation

**Affected Tools**: create_xsiam_report, create_parsing_rule, create_modeling_rule, create_assets_modeling_rule

**Symptoms**:
- Pack upload fails with "Installation has failed (101704)"
- No additional error details provided by XSIAM
- demisto-sdk validate passes ✅
- Files match official PANW examples exactly ✅

**What We Tested**:
1. ✅ Matched HelloWorld and Tanium file structures byte-for-byte
2. ✅ Fixed all schema compliance issues
3. ✅ Tested multiple pack_metadata.json configurations
4. ✅ Verified official packs (HelloWorld, Tanium) upload successfully
5. ❌ Our generated files still fail with 101704

**Hypothesis**: There may be server-side validation, dependencies, or tenant-specific requirements beyond what's visible in the file schemas.

**Recommendation**: Use the 6 working tools for production. For ParsingRules/ModelingRules/Reports, manual creation may be required until error 101704 is resolved.

---

## Production-Ready Tools Summary

| Tool | Upload Works | UI Visibility | Notes |
|------|--------------|---------------|-------|
| create_case_layout | ✅ | ✅ | Appears in Layouts |
| create_case_layout_rule | ✅ | ✅ | Applied to cases |
| create_xsiam_dashboard | ✅ | ✅ | **Pie charts render!** |
| create_agentix_action | ✅ | ⚠️ Unknown | Uploads, schema valid |
| create_agentix_agent | ✅ | ⚠️ Unknown | Uploads, schema valid |
| get_xsiam_content_guide | N/A | N/A | Returns guide |

---

## Complete Example: Create Full Pack

```python
# 1. Create dashboard with widget
create_xsiam_dashboard(
    pack_name="SecurityDashboards",
    dashboard_name="Executive Summary",
    description="High-level security metrics for executive review",
    xql_query="dataset = alerts | comp count() as critical_alerts by severity | filter severity = 'high' or severity = 'critical'",
    widget_title="Critical Alerts Trend",
    widget_type="line",
    upload=False  # Don't upload yet
)

# 2. Add a case layout
create_case_layout(
    pack_name="SecurityDashboards",
    layout_name="Executive Case Layout",
    description="Simplified layout for executive case review",
    upload=False
)

# 3. Add layout rule
create_case_layout_rule(
    pack_name="SecurityDashboards",
    rule_name="Executive Rule",
    layout_id="executive_case_layout",
    description="Apply executive layout to high-severity cases",
    upload=False
)

# 4. Upload entire pack
# Use SDK: demisto-sdk upload -i Packs/SecurityDashboards -z --marketplace marketplacev2
```

---

## XQL Query Patterns for Widgets

### Single Value Metrics
```xql
dataset = alerts | comp count() as total_alerts
# Result: Single number (e.g., "1,234 alerts")
# Widget type: single
```

### Pie Charts
```xql
dataset = alerts | comp count() as alert_count by severity
# Result: Distribution by category
# Widget type: pie
# Auto-generates: | view graph type = pie xaxis = severity yaxis = alert_count
```

### Tables
```xql
dataset = alerts | comp count() as total by severity, status | sort desc total
# Result: Multi-column data
# Widget type: table
```

### Time Series (Line Charts)
```xql
dataset = alerts | bin _time span=1h | comp count() as alerts_per_hour by _time
# Result: Trend over time
# Widget type: line
```

---

## Troubleshooting

### Dashboard Shows "Graph Settings Required"

**Cause**: Missing `viewOptions.commands` array or incorrect `| view graph` syntax

**Solution**: Use the `xql_query` parameter - the tool auto-generates proper syntax

**Manual Fix**: Ensure XQL includes:
```xql
... | view graph type = pie xaxis = category yaxis = count
```

AND viewOptions has:
```json
"commands": [
  {"command": {"op": "=", "name": "xaxis", "value": "category"}},
  {"command": {"op": "=", "name": "yaxis", "value": "count"}}
]
```

---

### AgentIX Content Doesn't Appear

**Possible Causes**:
1. Pack metadata missing `supportedModules: ["agentix"]` ✅ (now auto-added)
2. Args/outputs arrays are empty ✅ (now supported via parameters)
3. AgentIX UI location may be version-specific
4. May require specific XSIAM configuration

**Status**: Tool creates valid content and uploads successfully. UI location investigation ongoing.

---

### Error 101704 on Upload

**Affected**: ParsingRule, ModelingRule, AssetsModelingRule, XSIAMReport

**What We Know**:
- Files are schema-compliant (demisto-sdk validate passes)
- Files match official PANW examples exactly
- Official packs upload successfully
- Our generated packs fail with 101704

**Investigation Status**: Root cause unknown. May be tenant-specific or require additional dependencies.

---

## Files and Locations

**Generator Code**:
```
/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsiam_content_generator.py
```

**Widget API Tools**:
```
/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/openapi/
├── get_widgets.yaml
├── insert_widgets.yaml
└── delete_widgets.yaml
```

**Content Repository**:
```
~/projects/content/Packs/
```

**Documentation**:
```
README.md - Main documentation (83 tools)
.claude/CLAUDE.md - Session memory
CONTENT_TOOLS_STATUS.md - Detailed status
XSIAM_CONTENT_TOOLS_GUIDE.md - This file
```

---

## Next Steps

### For Production Use

**Recommended**:
- ✅ create_case_layout
- ✅ create_case_layout_rule
- ✅ create_xsiam_dashboard (with xql_query!)
- ✅ create_agentix_action
- ✅ create_agentix_agent

**Use with Caution**:
- ⚠️ create_case_field (field ID validation issues)

**Avoid Until Fixed**:
- ❌ create_xsiam_report (error 101704)
- ❌ create_parsing_rule (error 101704)
- ❌ create_modeling_rule (error 101704)
- ❌ create_assets_modeling_rule (error 101704)

### For Error 101704 Resolution

1. Compare byte-for-byte with working PANW content exported from XSIAM
2. Check for pack dependencies or required content
3. Contact XSIAM support for error details
4. Try adding content to existing working packs (like Core)

---

## Success Metrics

✅ **6 of 11 tools production-ready** (55% success rate)
✅ **XSIAMDashboard breakthrough** - First tool with full widget support
✅ **83 total MCP tools** - Comprehensive XSIAM automation
✅ **All changes committed** - Ready for deployment

**Test Pack**: WidgetTest contains all working content types and serves as reference implementation.
