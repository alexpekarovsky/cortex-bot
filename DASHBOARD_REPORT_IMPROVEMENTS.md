# Dashboard & Report Tool Improvement Plan

**Date**: January 3, 2026
**Status**: Recommendations for XSIAMDashboard and XSIAMReport tools
**Priority**: Medium (tools work but produce empty content)

---

## Problem Statement

Current `create_xsiam_dashboard` and `create_xsiam_report` tools create **valid schema-compliant files** that upload successfully but appear **empty in the XSIAM UI** because they have no widget data.

### Current Behavior

```python
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Test Dashboard"
)
```

**Produces**:
```json
{
    "dashboards_data": [{
        "name": "Test Dashboard",
        "layout": [],  // ❌ EMPTY - No widgets
        "metadata": {"params": []}
    }],
    "widgets_data": []
}
```

**Result**: Dashboard uploads but shows blank screen in UI.

---

## Proposed Solutions

### Option 1: Add Widget Data Parameter (Recommended)

**Pros**:
- Maximum flexibility
- User provides exactly what they want
- Works for any use case

**Cons**:
- Complex JSON structure required
- Steep learning curve
- Easy to make mistakes

**Implementation**:

```python
async def create_xsiam_dashboard(
    ctx: Context,
    pack_name: str,
    dashboard_name: str,
    description: Optional[str] = None,
    widgets_json: Optional[str] = None,  # NEW: JSON array of widget definitions
    upload: bool = False,
) -> str:
    """
    Creates an XSIAMDashboard JSON file.

    Args:
        widgets_json: Optional JSON array of widget definitions. Each widget must have:
            - key: "xql" for XQL widgets
            - data: Widget configuration including:
                - type: "Custom XQL"
                - title: Widget title
                - width: Percentage (25, 33.33, 50, 100)
                - height: Pixels (400-845)
                - phrase: XQL query with "view graph" or "fields"
                - time_frame: {"relativeTime": milliseconds}
                - viewOptions: Chart type and parameters

        Example:
            '[{"key": "xql", "data": {"type": "Custom XQL", "title": "Total Alerts", ...}}]'
    """
    # Parse widgets_json if provided
    if widgets_json:
        try:
            widgets = json.loads(widgets_json)
            layout = [{"id": "row-1", "data": widgets}]
        except json.JSONDecodeError:
            return create_response(data={"error": "Invalid widgets_json"}, is_error=True)
    else:
        layout = []  # Empty as before

    dashboard_data = {
        "dashboards_data": [{
            "name": dashboard_name,
            "layout": layout,
            ...
        }]
    }
```

**Usage**:

```python
# Empty dashboard (current behavior)
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Test Dashboard"
)

# Dashboard with widgets
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Security Metrics",
    widgets_json='''[
        {
            "key": "xql",
            "data": {
                "type": "Custom XQL",
                "title": "Total Alerts",
                "width": 50,
                "height": 400,
                "phrase": "dataset = alerts | comp count() as total | view graph type = single subtype = standard yaxis = total",
                "time_frame": {"relativeTime": 86400000},
                "viewOptions": {
                    "type": "single",
                    "commands": [
                        {"command": {"op": "=", "name": "subtype", "value": "standard"}},
                        {"command": {"op": "=", "name": "yaxis", "value": "total"}}
                    ]
                }
            }
        }
    ]'''
)
```

---

### Option 2: Provide Template Library

**Pros**:
- Easy to use
- Pre-built working examples
- Covers common use cases

**Cons**:
- Limited to predefined templates
- Less flexible
- Requires maintaining template library

**Implementation**:

```python
DASHBOARD_TEMPLATES = {
    "blank": [],  # Current behavior
    "security_overview": [
        {
            "key": "xql",
            "data": {
                "type": "Custom XQL",
                "title": "Total Alerts (24h)",
                "width": 33.33,
                "height": 400,
                "phrase": "dataset = alerts | comp count() as total | view graph type = single subtype = standard yaxis = total",
                "time_frame": {"relativeTime": 86400000},
                "viewOptions": {
                    "type": "single",
                    "commands": [
                        {"command": {"op": "=", "name": "subtype", "value": "standard"}},
                        {"command": {"op": "=", "name": "yaxis", "value": "total"}}
                    ]
                }
            }
        },
        {
            "key": "xql",
            "data": {
                "type": "Custom XQL",
                "title": "Alerts by Severity",
                "width": 33.33,
                "height": 400,
                "phrase": "dataset = alerts | comp count() as count by severity | view graph type = pie xaxis = severity yaxis = count",
                "time_frame": {"relativeTime": 86400000},
                "viewOptions": {
                    "type": "pie",
                    "commands": [
                        {"command": {"op": "=", "name": "xaxis", "value": "severity"}},
                        {"command": {"op": "=", "name": "yaxis", "value": "count"}}
                    ]
                }
            }
        }
    ],
    "automation_metrics": [...],
    "threat_intel": [...]
}

async def create_xsiam_dashboard(
    ctx: Context,
    pack_name: str,
    dashboard_name: str,
    description: Optional[str] = None,
    template: str = "blank",  # NEW: Template name
    upload: bool = False,
) -> str:
    """
    Args:
        template: Dashboard template to use. Options:
            - "blank": Empty dashboard (default)
            - "security_overview": Security metrics and alerts
            - "automation_metrics": Playbook and automation stats
            - "threat_intel": Threat intelligence indicators
    """
    layout_widgets = DASHBOARD_TEMPLATES.get(template, [])
    layout = [{"id": "row-1", "data": layout_widgets}] if layout_widgets else []
```

**Usage**:

```python
# Use template
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Security Overview",
    template="security_overview"
)
```

---

### Option 3: Hybrid Approach (Best of Both)

Combine templates with custom widgets:

```python
async def create_xsiam_dashboard(
    ctx: Context,
    pack_name: str,
    dashboard_name: str,
    description: Optional[str] = None,
    template: str = "blank",  # Template name
    custom_widgets_json: Optional[str] = None,  # Additional custom widgets
    upload: bool = False,
) -> str:
    """
    Args:
        template: Pre-built template ("blank", "security_overview", etc.)
        custom_widgets_json: Additional widgets to append to template
    """
    # Start with template
    widgets = DASHBOARD_TEMPLATES.get(template, []).copy()

    # Add custom widgets if provided
    if custom_widgets_json:
        try:
            custom = json.loads(custom_widgets_json)
            widgets.extend(custom)
        except json.JSONDecodeError:
            return create_response(data={"error": "Invalid custom_widgets_json"}, is_error=True)

    layout = [{"id": "row-1", "data": widgets}] if widgets else []
```

**Usage**:

```python
# Template + custom widget
create_xsiam_dashboard(
    pack_name="MyPack",
    dashboard_name="Custom Security Dashboard",
    template="security_overview",
    custom_widgets_json='[{"key": "xql", "data": {...}}]'
)
```

---

### Option 4: Enhanced Documentation Only

**Don't change the code**, just improve documentation:

```python
async def create_xsiam_dashboard(
    ctx: Context,
    pack_name: str,
    dashboard_name: str,
    description: Optional[str] = None,
    upload: bool = False,
) -> str:
    """
    Creates an XSIAMDashboard JSON file.

    ⚠️ NOTE: This creates an EMPTY dashboard structure. To add widgets:

    1. Generate the empty dashboard with this tool
    2. Manually edit the JSON file and add widgets to the "layout" array
    3. Use the widget patterns from XSIAM_WIDGET_PATTERNS.md

    Minimum working widget example:
    {
        "layout": [
            {
                "id": "row-1",
                "data": [
                    {
                        "key": "xql",
                        "data": {
                            "type": "Custom XQL",
                            "title": "Sample Widget",
                            "width": 100,
                            "height": 400,
                            "phrase": "dataset = alerts | limit 10 | fields *",
                            "time_frame": {"relativeTime": 86400000},
                            "viewOptions": {"type": "table", "commands": []}
                        }
                    }
                ]
            }
        ]
    }

    For complete widget patterns and examples, see:
    /Users/apekarovsky/projects/cortex-mcp/XSIAM_WIDGET_PATTERNS.md

    Args:
        pack_name: Name of the pack to create the dashboard in
        dashboard_name: Name of the dashboard
        description: Optional description
        upload: If True, upload pack to XSIAM (requires -z flag)

    Returns:
        JSON response with file path
    """
```

---

## Recommendation Matrix

| Approach | Ease of Use | Flexibility | Maintenance | Recommended For |
|----------|-------------|-------------|-------------|-----------------|
| **Option 1: Widget Parameter** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Advanced users, custom use cases |
| **Option 2: Templates** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Quick starts, common use cases |
| **Option 3: Hybrid** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **Best balance - RECOMMENDED** |
| **Option 4: Docs Only** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | If time-constrained |

---

## Recommended Implementation Plan

### Phase 1: Documentation (Immediate)

1. ✅ Create `XSIAM_CONTENT_ANALYSIS.md` - Done
2. ✅ Create `XSIAM_WIDGET_PATTERNS.md` - Done
3. ⬜ Update tool docstrings to reference these guides
4. ⬜ Add warning about empty dashboards in tool description

**Effort**: 1 hour
**Impact**: Users understand why dashboards are empty

### Phase 2: Template Library (Short-term)

1. ⬜ Create `XSIAM_DASHBOARD_TEMPLATES` constant with 3-5 common templates:
   - `security_overview` - Alerts, severity, trends
   - `automation_metrics` - Playbook stats, task execution
   - `threat_intel` - Indicators, malware, IOCs
   - `asset_inventory` - Endpoints, vulnerabilities
   - `compliance` - Policy violations, audit logs

2. ⬜ Add `template` parameter to `create_xsiam_dashboard`
3. ⬜ Add `template` parameter to `create_xsiam_report`

**Effort**: 4-6 hours
**Impact**: Users can create working dashboards instantly

### Phase 3: Custom Widgets (Medium-term)

1. ⬜ Add `custom_widgets_json` parameter
2. ⬜ Add widget validation helper
3. ⬜ Add widget builder tool (optional advanced feature)

**Effort**: 6-8 hours
**Impact**: Advanced users can create any dashboard

### Phase 4: Testing & Refinement (Ongoing)

1. ⬜ Test each template on live XSIAM tenant
2. ⬜ Gather user feedback
3. ⬜ Add more templates based on demand
4. ⬜ Create widget library helpers

**Effort**: Ongoing
**Impact**: Continuous improvement

---

## Minimal Viable Improvement (MVP)

**If time-constrained, do this**:

1. ✅ Create widget patterns guide - **DONE**
2. ⬜ Update `create_xsiam_dashboard` docstring with:
   - Warning about empty dashboards
   - Link to `XSIAM_WIDGET_PATTERNS.md`
   - Minimal working widget example
3. ⬜ Same for `create_xsiam_report`

**Total effort**: 30 minutes
**Impact**: Users understand the limitation and have a path forward

---

## Decision Required

**Choose implementation approach**:

- [ ] **Option 1**: Widget parameter only (max flexibility)
- [ ] **Option 2**: Templates only (max ease of use)
- [x] **Option 3**: Hybrid (templates + custom) - **RECOMMENDED**
- [ ] **Option 4**: Documentation only (minimal effort)

**Rationale for Option 3**:
- Covers 80% use cases with templates
- Allows 20% custom cases with widget parameter
- Best ROI: moderate effort, high impact
- Incremental: can start with templates, add custom later

---

## Reference Documents

Created during this analysis:

1. **XSIAM_CONTENT_ANALYSIS.md** - Deep dive comparison of our output vs official PANW content
   - Shows why dashboards/reports are empty
   - Documents ParsingRule/ModelingRule fixes
   - Comprehensive testing checklist

2. **XSIAM_WIDGET_PATTERNS.md** - Complete widget reference guide
   - 6 widget types with examples (single, pie, column, line, table, header)
   - Common XQL patterns
   - Layout structure templates
   - Time frame calculations
   - Complete working examples

Both documents are located at: `/Users/apekarovsky/projects/cortex-mcp/`
