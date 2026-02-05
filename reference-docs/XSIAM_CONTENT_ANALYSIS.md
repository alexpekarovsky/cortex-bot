# XSIAM Content Type Analysis - Working vs Generated

**Date**: January 3, 2026
**Branch**: CRTX-194114-fix-openapi-tools
**Purpose**: Compare official PANW content with our MCP generator output

---

## Executive Summary

**Key Finding**: Our generators create valid schema-compliant content, BUT dashboards/reports need **actual widget data** to appear in UI.

| Content Type | Our Output | Status | Critical Missing Element |
|--------------|------------|--------|--------------------------|
| **ParsingRule** | ✅ Valid | Working | content_id in INGEST (added) |
| **ModelingRule** | ✅ Valid | Working | schema.json file (added) |
| **XSIAMDashboard** | ⚠️ Valid but empty | Creates but no UI | **Widget data in layout** |
| **XSIAMReport** | ⚠️ Valid but empty | Creates but no UI | **Widget data in layout** |
| **CaseLayout** | ✅ Valid | Working | None |
| **CaseField** | ✅ Valid | Working | None |

---

## 1. XSIAMDashboard - Deep Dive

### What We Generate (Empty Dashboard)

```json
{
    "fromVersion": "8.7.0",
    "dashboards_data": [
        {
            "global_id": "test_dashboard",
            "status": "ENABLED",
            "name": "Test Dashboard",
            "description": "XSIAM Dashboard: Test Dashboard",
            "default_dashboard_id": null,
            "layout": [],  // ❌ EMPTY - Dashboard won't show widgets
            "metadata": {"params": []}
        }
    ],
    "widgets_data": []
}
```

### What Actually Works (CommonDashboards Example)

```json
{
    "dashboards_data": [
        {
            "name": "Automation Insights",
            "description": "Provides a high-level overview...",
            "status": "ENABLED",
            "layout": [
                {
                    "id": "row-3968",  // Row container
                    "data": [
                        {
                            "key": "xql",  // Widget type
                            "data": {
                                "type": "Custom XQL",
                                "title": "Automated actions by status",
                                "width": 33.333333333333336,
                                "height": 511,
                                "phrase": "dataset = playbook_tasks\n| filter automated = true...",
                                "time_frame": {
                                    "relativeTime": 604800000  // 7 days in ms
                                },
                                "viewOptions": {
                                    "type": "single",
                                    "commands": [
                                        {
                                            "command": {
                                                "op": "=",
                                                "name": "subtype",
                                                "value": "standard"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            ],
            "default_dashboard_id": 1,
            "global_id": "03ffcf649a8a4cd6b9e0170b794baa89",
            "metadata": {"params": []}
        }
    ],
    "widgets_data": [],  // Always empty in examples
    "fromVersion": "6.10.0"
}
```

### Critical Differences

| Element | Our Output | Working Example | Impact |
|---------|------------|-----------------|--------|
| `layout` | Empty array `[]` | Nested rows with widget data | **Dashboard appears empty in UI** |
| `default_dashboard_id` | `null` | `1` | May affect default behavior |
| `global_id` | Sanitized name | UUID-like hash | Uniqueness/conflicts |
| `widgets_data` | Empty array | Empty array | No impact (always empty) |

### Widget Data Structure

Each widget in `layout` requires:

```json
{
    "key": "xql",  // Widget type (xql, text, chart, etc.)
    "data": {
        "type": "Custom XQL",  // Display type
        "title": "Widget Title",
        "width": 33.33,  // Percentage of row width
        "height": 511,  // Pixels
        "phrase": "dataset = ... | view graph type = pie ...",  // XQL query
        "time_frame": {
            "relativeTime": 604800000  // Time range in milliseconds
        },
        "viewOptions": {  // Chart type and parameters
            "type": "pie",
            "commands": [
                {"command": {"op": "=", "name": "xaxis", "value": "field_name"}}
            ]
        }
    }
}
```

**Widget Types Observed**:
- `single` - Single value metric (with `subtype: standard`)
- `pie` - Pie chart
- `column` - Column/bar chart (with `subtype: grouped`)
- `line` - Line chart (with `series` for multiple lines)
- `table` - Data table

---

## 2. XSIAMReport - Deep Dive

### What We Generate (Empty Report)

```json
{
    "templates_data": [
        {
            "global_id": "test_report",
            "report_name": "Test Report",
            "report_description": "XSIAM Report: Test Report",
            "fromVersion": "8.7.0",
            "layout": [],  // ❌ EMPTY - Report has no content
            "default_template_id": 1,
            "time_frame": {"relativeTime": 86400000},
            "time_offset": 0,
            "metadata": "{\"params\": []}"  // JSON string
        }
    ],
    "fromVersion": "8.7.0",
    "widgets_data": []
}
```

### What Actually Works (Veeam Report Example)

```json
{
    "templates_data": [
        {
            "report_name": "All Veeam failed multi-factor authentication events...",
            "report_description": "Provides an overview of failed Veeam...",
            "layout": [
                {
                    "id": "Row 1",
                    "data": [
                        {
                            "key": "header",  // Report header widget
                            "data": {
                                "name": "All failed multi-factor authentication...",
                                "type": "",
                                "width": 100,
                                "height": 140,
                                "description": "Provides an overview..."
                            }
                        }
                    ]
                },
                {
                    "id": "row-8151",
                    "data": [
                        {
                            "key": "xql",  // XQL query widget
                            "data": {
                                "type": "Custom XQL",
                                "title": "Failed Multi-Factor Authentication Events by User",
                                "width": 100,
                                "height": 250,
                                "phrase": "dataset in (veeam_*) ... | view graph type = pie ...",
                                "time_frame": {"relativeTime": 86400000},
                                "viewOptions": {
                                    "type": "pie",
                                    "commands": [...]
                                }
                            }
                        }
                    ]
                }
            ],
            "default_template_id": 1,
            "time_frame": {"relativeTime": 86400000},
            "global_id": "c5e709240d634a42ad404f34a972f6bb",
            "time_offset": 10800,
            "metadata": "{\"params\": []}"  // JSON string, not object!
        }
    ],
    "fromVersion": "8.9.0",
    "widgets_data": []
}
```

### Critical Differences

| Element | Our Output | Working Example | Impact |
|---------|------------|-----------------|--------|
| `layout` | Empty array | Rows with header + widgets | **Report is blank** |
| `metadata` | JSON string `"{...}"` | JSON string `"{...}"` | ✅ Correct (must be string) |
| `time_offset` | `0` | `10800` (3 hours) | Timezone offset |
| `global_id` | Sanitized name | UUID-like hash | May cause conflicts |

### Report-Specific Widget: Header

```json
{
    "key": "header",
    "data": {
        "name": "Report Title",
        "type": "",
        "width": 100,
        "height": 140,
        "description": "Report description text"
    }
}
```

---

## 3. ParsingRule - Working Correctly

### What We Generate

```
fromversion: 8.7.0
id: test_parsing_rule
name: Test Parsing Rule
tags: []
rules: ''
samples: ''
```

**XIF File**:
```
[INGEST:vendor="myvendor", product="myproduct", target_dataset="myvendor_myproduct_raw", no_hit=keep, content_id="test_parsing_rule"]
alter _time = created_time;
```

### Official HelloWorld Example

```
fromversion: 8.4.0
id: HelloWorldParsingRule
name: HelloWorld Parsing Rule
tags: []
rules: ''
samples: ''
```

**XIF File**:
```
[INGEST:vendor="hello", product="world", target_dataset="hello_world_raw", no_hit = keep]
alter _time = created_time;
```

### What We Added (Critical!)

✅ **content_id parameter** - Required by this XSIAM tenant (error 101704 without it)

### Field Order Matches

Our YML field order: `fromversion, id, name, tags, rules, samples` ✅
Official field order: `fromversion, id, name, tags, rules, samples` ✅

**Status**: ✅ **WORKING** - Generates valid ParsingRules with content_id

---

## 4. ModelingRule - Working Correctly

### What We Generate

```
fromversion: 8.7.0
id: test_modeling_rule
name: Test Modeling Rule
rules: ''
schema: ''
tags: ''
```

**XIF File**:
```
[MODEL: dataset = myvendor_myproduct_raw]
alter
    xdm.event.id = to_string(id),
    xdm.event.description = description;
```

**Schema File** (`test_modeling_rule_schema.json`):
```json
{
    "myvendor_myproduct_raw": {
        "_raw_log": {
            "type": "string",
            "is_array": false
        }
    }
}
```

### Official HelloWorld Example

```
fromversion: 8.4.0
id: HelloWorldModelingRule
name: HelloWorld Modeling Rule
rules: ''
schema: ''
```

**XIF File**:
```
[MODEL: dataset=hello_world_raw]
alter
    xdm.event.id = to_string(id),
    xdm.event.description = description,
    xdm.source.user.identifier = json_extract_scalar(custom_details, "$.triggered_by_uuid"),
    xdm.target.port = t_port,
    xdm.network.protocol_layers = arraycreate(protocol);
```

**Schema File** (`HelloWorldModelingRules_schema.json`):
```json
{
    "hello_world_raw": {
        "id": {"type": "int", "is_array": false},
        "t_port": {"type": "int", "is_array": false},
        "protocol": {"type": "string", "is_array": false},
        "description": {"type": "string", "is_array": false},
        "custom_details": {"type": "string", "is_array": false},
        "created_time": {"type": "datetime", "is_array": false}
    }
}
```

### What We Added (Critical!)

✅ **schema.json file** - Required for ModelingRules to validate

### Differences

| Element | Our Output | Official | Impact |
|---------|------------|----------|--------|
| Dataset syntax | `dataset = name` | `dataset=name` | No impact (both work) |
| Schema detail | Minimal (just _raw_log) | Full field definitions | Our approach works but less detailed |

**Status**: ✅ **WORKING** - Generates valid ModelingRules with schema

---

## 5. CaseLayout & CaseField - Working Correctly

### CaseLayout

**Status**: ✅ **WORKING** - Direct upload works, appears in UI

**Key Field**: `"group": "case"` - Distinguishes from incident layouts

### CaseField

**Status**: ⚠️ **WORKING but needs unique IDs**

**Known Issue**: Field IDs must be globally unique or upload fails

---

## Root Cause Analysis

### Why Dashboards/Reports Don't Appear

1. **Empty `layout` array** - No widgets = nothing to display
2. **No default content** - We can't guess what XQL queries user wants
3. **Complex widget structure** - Each widget needs:
   - XQL query (`phrase`)
   - Visualization type (`viewOptions.type`)
   - Chart parameters (`viewOptions.commands`)
   - Time frame
   - Dimensions (width/height)

### Why ParsingRules/ModelingRules Failed Initially

1. **Missing content_id** - Specific to this XSIAM tenant (error 101704)
2. **Missing schema.json** - ModelingRules require schema definitions
3. **Pack upload requirement** - These content types need `-z` flag

---

## Recommendations

### For XSIAMDashboard Tool

**Option 1: Require Widget Data Parameter**
```python
async def create_xsiam_dashboard(
    ...,
    widgets_json: str = None  # JSON array of widget definitions
)
```

**Option 2: Provide Templates**
```python
# Common templates: security_overview, automation_metrics, threat_intel
template: str = "blank"  # or "security_overview"
```

**Option 3: Document Minimum Working Example**
Include in tool docstring:
```json
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
                        "phrase": "dataset = xdr_data | limit 10",
                        "time_frame": {"relativeTime": 86400000},
                        "viewOptions": {"type": "table", "commands": []}
                    }
                }
            ]
        }
    ]
}
```

### For XSIAMReport Tool

Similar approach - require `layout_json` parameter or provide templates.

### For ParsingRule/ModelingRule Tools

✅ **Already Fixed** - Current implementation works correctly

---

## Testing Checklist

- [x] ParsingRule creates valid YML + XIF with content_id
- [x] ModelingRule creates valid YML + XIF + schema.json
- [x] CaseLayout uploads successfully
- [x] CaseField uploads successfully (with unique IDs)
- [ ] XSIAMDashboard with actual widgets appears in UI
- [ ] XSIAMReport with actual widgets appears in UI
- [ ] CaseLayoutRule applies correctly (requires pack upload)
- [ ] AssetsModelingRule uploads and processes correctly

---

## Reference Links

### Official PANW Content Examples

1. **CommonDashboards Pack**: [Cortex Marketplace](https://cortex.marketplace.pan.dev/marketplace/details/CommonDashboards/)
   - Contains: Automation Insights, Troubleshooting Playbooks, Troubleshooting Instances
   - Source: `/tmp/demisto-content/Packs/CommonDashboards/XSIAMDashboards/`

2. **Veeam Pack**: [Cortex Marketplace](https://cortex.marketplace.pan.dev/marketplace/details/Veeam/)
   - Contains: 7 reports, 2 dashboards
   - Source: `/tmp/demisto-content/Packs/Veeam/XSIAMReports/`

3. **HelloWorld Pack**: Developer example
   - Contains: ParsingRule, ModelingRule with schema
   - Source: `/tmp/demisto-content/Packs/HelloWorld/`

### XSIAM Documentation

- [Dashboard Widgets](https://docs-cortex.paloaltonetworks.com/r/Cortex-XSIAM/Cortex-XSIAM-Administrator-Guide/Dashboard-Widgets)
- [Create Parsing Rules](https://docs-cortex.paloaltonetworks.com/r/Cortex-XSIAM/Cortex-XSIAM-Administrator-Guide/Create-Parsing-Rules)
- [Cortex Marketplace](https://www.paloaltonetworks.com/cortex/cortex-xsoar/marketplace)

### GitHub Resources

- [Cortex XQL Queries Repository](https://github.com/PaloAltoNetworks/cortex-xql-queries)
- [demisto/content Repository](https://github.com/demisto/content)

---

## Conclusion

Our XSIAM content generators are **structurally correct** but need **widget/layout data** to be useful:

| Content Type | Schema Valid? | Uploads? | Appears in UI? | Why? |
|--------------|---------------|----------|----------------|------|
| ParsingRule | ✅ Yes | ✅ Yes | ✅ Yes | Complete with content_id + XIF |
| ModelingRule | ✅ Yes | ✅ Yes | ✅ Yes | Complete with schema.json + XIF |
| CaseLayout | ✅ Yes | ✅ Yes | ✅ Yes | Minimal structure works |
| CaseField | ✅ Yes | ✅ Yes | ✅ Yes | Basic fields work |
| XSIAMDashboard | ✅ Yes | ✅ Yes | ⚠️ Empty | No widgets in layout |
| XSIAMReport | ✅ Yes | ✅ Yes | ⚠️ Empty | No widgets in layout |

**Next Steps**:
1. Add widget data parameter to dashboard/report tools
2. Provide working examples in tool docstrings
3. Create template library for common dashboard patterns
4. Test dashboard/report with actual widget data on XSIAM tenant
