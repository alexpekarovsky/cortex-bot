# XSIAM Dashboard & Report Widget Patterns

**Date**: January 3, 2026
**Purpose**: Reference guide for creating working dashboards and reports
**Source**: Official PANW content from demisto/content repository

---

## Widget Pattern Catalog

### 1. Single Value Widget

**Use**: Display one metric (count, average, sum)

```json
{
    "key": "xql",
    "data": {
        "type": "Custom XQL",
        "title": "Failed automation tasks",
        "width": 25,
        "height": 547,
        "phrase": "dataset = playbook_tasks\n| filter task_status = \"Error\" and automated = true\n| comp count() as error_count\n| view graph type = single subtype = standard yaxis = error_count",
        "time_frame": {
            "relativeTime": 604800000
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
                },
                {
                    "command": {
                        "op": "=",
                        "name": "yaxis",
                        "value": "error_count"
                    }
                }
            ]
        }
    }
}
```

**XQL Pattern**:
```xql
dataset = ...
| filter ...
| comp count() as metric_name
| view graph type = single subtype = standard yaxis = metric_name
```

---

### 2. Pie Chart Widget

**Use**: Show proportions/distribution

```json
{
    "key": "xql",
    "data": {
        "type": "Custom XQL",
        "title": "Actions by verdict",
        "width": 33.333333333333336,
        "height": 511,
        "phrase": "dataset = indicators\n| filter verdict != null and verdict != \"\"\n| comp count() as action_count by verdict\n| sort desc action_count\n| view graph type = pie xaxis = verdict yaxis = action_count legend_percentage = `true`",
        "time_frame": {
            "relativeTime": 604800000
        },
        "viewOptions": {
            "type": "pie",
            "commands": [
                {
                    "command": {
                        "op": "=",
                        "name": "xaxis",
                        "value": "verdict"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "yaxis",
                        "value": "action_count"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "legend_percentage",
                        "value": "`true`"
                    }
                }
            ]
        }
    }
}
```

**XQL Pattern**:
```xql
dataset = ...
| filter field != null and field != ""
| comp count() as count_name by category_field
| sort desc count_name
| view graph type = pie xaxis = category_field yaxis = count_name legend_percentage = `true`
```

**Variations**:
- `subtype = full` - Full circle pie chart
- `legend_percentage = true` - Show percentages in legend

---

### 3. Column Chart Widget

**Use**: Compare values across categories

```json
{
    "key": "xql",
    "data": {
        "type": "Custom XQL",
        "title": "Command executions per integration category",
        "height": 511,
        "phrase": "dataset = soar_execution_metrics\n| filter type = \"integration\"\n| filter category != null and category != \"\"\n| comp count() as exec_count by category\n| sort desc exec_count\n| view graph type = column subtype = grouped xaxis = category yaxis = exec_count",
        "time_frame": {
            "relativeTime": 604800000
        },
        "viewOptions": {
            "type": "column",
            "commands": [
                {
                    "command": {
                        "op": "=",
                        "name": "subtype",
                        "value": "grouped"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "xaxis",
                        "value": "category"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "yaxis",
                        "value": "exec_count"
                    }
                }
            ]
        }
    }
}
```

**XQL Pattern**:
```xql
dataset = ...
| filter ...
| comp count() as metric by category
| sort desc metric
| view graph type = column subtype = grouped xaxis = category yaxis = metric
```

**With Series (Multiple Bars)**:
```xql
dataset = playbook_tasks
| filter automated = true
| comp count() as exec_count by task_name, task_status
| sort desc exec_count
| view graph type = column subtype = grouped xaxis = task_name yaxis = exec_count series = task_status
```

---

### 4. Line Chart Widget

**Use**: Show trends over time

```json
{
    "key": "xql",
    "data": {
        "type": "Custom XQL",
        "title": "Incidents closed over time",
        "width": 33.333333333333336,
        "height": 511,
        "phrase": "dataset = incidents\n| filter resolved_ts != null and resolved_ts != \"\"\n| alter resolved_time = to_timestamp(resolved_ts)\n| bin resolved_time span = 1d\n| comp count() as closed_count by resolved_time, alert_categories\n| sort asc resolved_time\n| view graph type = line xaxis = resolved_ts yaxis = closed_count series = alert_categories",
        "time_frame": {
            "relativeTime": 604800000
        },
        "viewOptions": {
            "type": "line",
            "commands": [
                {
                    "command": {
                        "op": "=",
                        "name": "xaxis",
                        "value": "resolved_ts"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "yaxis",
                        "value": "closed_count"
                    }
                },
                {
                    "command": {
                        "op": "=",
                        "name": "series",
                        "value": "alert_categories"
                    }
                }
            ]
        }
    }
}
```

**XQL Pattern**:
```xql
dataset = ...
| filter timestamp_field != null
| alter time_value = to_timestamp(timestamp_field)
| bin time_value span = 1d
| comp count() as metric by time_value, series_field
| sort asc time_value
| view graph type = line xaxis = time_value yaxis = metric series = series_field
```

**Time Binning Options**:
- `span = 1h` - Hourly
- `span = 1d` - Daily
- `span = 1w` - Weekly

---

### 5. Table Widget

**Use**: Display detailed data rows

```json
{
    "key": "xql",
    "data": {
        "type": "Custom XQL",
        "title": "Latest Failed Multi-Factor Authentication Events",
        "width": 100,
        "height": 845,
        "phrase": "dataset in (veeam_*)\n| filter _vendor=\"Veeam\"\n| alter\n    _time= parse_timestamp(\"%FT%H:%M:%E6S%Ez\", arrayindex(regextract(_raw_log, \"<\\d+>1\\s+(\\S+)\\s\"), 0)),\n    _host=regextract(_raw_log , \"\\s(\\S+)\\s(?:Veeam_MP|Veeam_Backup)\"),\n    _description=arrayindex(regextract(_raw_log, \"Description=\\\"([^\\\"]*)(?:\\\"|$)\"),0),\n    _severity=\"High\",\n    _user=arrayindex(regextract(_raw_log, \"UserName=\\\"([^\\\"]*)\\\"\"), 0)\n| sort desc _time\n| fields\n    _host as `Data Source`, _time as `Date`, _user as `User`, _description as `Message Details`, _severity as `Severity`",
        "time_frame": {
            "relativeTime": 86400000
        },
        "viewOptions": {
            "type": "table",
            "commands": []
        }
    }
}
```

**XQL Pattern**:
```xql
dataset = ...
| filter ...
| alter field1 = ..., field2 = ...
| sort desc _time
| fields field1 as `Column Name`, field2 as `Another Column`
```

**Key Points**:
- Use `fields` to select columns
- Use `as` with backticks for column headers
- `viewOptions.commands` is empty array for tables
- No `view graph` in XQL - table is inferred from `fields`

---

### 6. Report Header Widget

**Use**: Title section for reports (not used in dashboards)

```json
{
    "key": "header",
    "data": {
        "name": "All failed multi-factor authentication events for the last 24h",
        "type": "",
        "width": 100,
        "height": 140,
        "tenantId": "2209138820274",
        "description": "Provides an overview of failed Veeam Backup & Replication multi-factor authentication events created for the last 24 hours.",
        "customerName": "Veeam Software Corporation (Tech Partner Only)"
    }
}
```

**Note**: Only use in XSIAMReports, not XSIAMDashboards

---

## Common XQL Patterns

### Dataset Selection

```xql
# Single dataset
dataset = xdr_data

# Multiple datasets with wildcard
dataset in (veeam_*)

# Multiple specific datasets
dataset in (dataset1, dataset2, dataset3)
```

### Filtering

```xql
# Simple filter
| filter field = "value"

# Null check
| filter field != null and field != ""

# Numeric comparison
| filter count > 10

# Pattern matching
| filter field ~= "pattern.*"

# Multiple conditions
| filter condition1 and condition2
```

### Aggregation

```xql
# Count
| comp count() as total

# Count by category
| comp count() as count by category_field

# Multiple aggregations
| comp count() as total, avg(metric) as average by category

# Count distinct
| comp count(distinct field) as unique_count
```

### Time Manipulation

```xql
# Parse timestamp
| alter time_value = parse_timestamp("%Y-%m-%dT%H:%M:%SZ", timestamp_field)

# Convert to timestamp
| alter time_value = to_timestamp(field)

# Bin time
| bin time_value span = 1d
```

### Field Transformation

```xql
# Create new field
| alter new_field = existing_field

# Conditional logic
| alter category = if(field = "value", "Category1", "Category2")

# Extract with regex
| alter extracted = arrayindex(regextract(field, "pattern"), 0)

# JSON parsing
| alter value = json_extract_scalar(json_field, "$.path.to.value")
```

---

## Layout Structure

### Dashboard Layout

```json
{
    "layout": [
        {
            "id": "row-1",  // Unique row ID
            "data": [
                // Widget 1
                {"key": "xql", "data": {...}},
                // Widget 2
                {"key": "xql", "data": {...}}
            ]
        },
        {
            "id": "row-2",
            "data": [
                // More widgets
            ]
        }
    ]
}
```

### Report Layout

```json
{
    "layout": [
        {
            "id": "Row 1",
            "data": [
                {"key": "header", "data": {...}}  // Header first
            ]
        },
        {
            "id": "row-2",
            "data": [
                {"key": "xql", "data": {...}}  // Then widgets
            ]
        }
    ]
}
```

---

## Widget Dimensions

### Width Percentages

```json
// Full row
"width": 100

// Half row (2 widgets)
"width": 50

// Third row (3 widgets)
"width": 33.333333333333336

// Quarter row (4 widgets)
"width": 25
```

### Height Guidelines

```json
// Small widget (single value)
"height": 400

// Medium widget (chart)
"height": 511

// Large widget (detailed table)
"height": 845
```

---

## Time Frames

```json
// Last hour
"time_frame": {"relativeTime": 3600000}

// Last 24 hours
"time_frame": {"relativeTime": 86400000}

// Last 7 days
"time_frame": {"relativeTime": 604800000}

// Last 30 days
"time_frame": {"relativeTime": 2592000000}
```

**Formula**: `milliseconds = seconds * 1000`

---

## Common Datasets

### XSOAR/XSIAM Internal Data

```xql
playbook_runs       # Playbook execution data
playbook_tasks      # Individual task executions
indicators          # Threat intelligence indicators
incidents           # Cases/incidents
soar_execution_metrics  # Automation metrics
```

### XDR Security Data

```xql
xdr_data           # All XDR events
alerts             # Security alerts
host_inventory     # Asset/endpoint data
```

### Vendor-Specific

```xql
veeam_*            # Veeam datasets (all)
msft_defender_*    # Microsoft Defender
palo_networks_*    # Palo Alto Networks
```

---

## Complete Working Examples

### Example 1: Security Metrics Dashboard

```json
{
    "dashboards_data": [{
        "name": "Security Metrics",
        "description": "Overview of security operations",
        "status": "ENABLED",
        "layout": [
            {
                "id": "row-1",
                "data": [
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
                    },
                    {
                        "key": "xql",
                        "data": {
                            "type": "Custom XQL",
                            "title": "Critical Alerts",
                            "width": 33.33,
                            "height": 400,
                            "phrase": "dataset = alerts | filter severity = \"Critical\" | comp count() as critical_count | view graph type = single subtype = standard yaxis = critical_count",
                            "time_frame": {"relativeTime": 86400000},
                            "viewOptions": {
                                "type": "single",
                                "commands": [
                                    {"command": {"op": "=", "name": "subtype", "value": "standard"}},
                                    {"command": {"op": "=", "name": "yaxis", "value": "critical_count"}}
                                ]
                            }
                        }
                    }
                ]
            }
        ],
        "default_dashboard_id": 1,
        "global_id": "security_metrics_dashboard",
        "metadata": {"params": []}
    }],
    "widgets_data": [],
    "fromVersion": "8.7.0"
}
```

### Example 2: Daily Security Report

```json
{
    "templates_data": [{
        "report_name": "Daily Security Summary",
        "report_description": "Overview of security events for the last 24 hours",
        "layout": [
            {
                "id": "Row 1",
                "data": [{
                    "key": "header",
                    "data": {
                        "name": "Daily Security Summary",
                        "type": "",
                        "width": 100,
                        "height": 140,
                        "description": "Security events and metrics for the last 24 hours"
                    }
                }]
            },
            {
                "id": "row-2",
                "data": [{
                    "key": "xql",
                    "data": {
                        "type": "Custom XQL",
                        "title": "Top 10 Alert Sources",
                        "width": 100,
                        "height": 500,
                        "phrase": "dataset = alerts | comp count() as alert_count by source | sort desc alert_count | limit 10 | fields source as `Alert Source`, alert_count as `Count`",
                        "time_frame": {"relativeTime": 86400000},
                        "viewOptions": {
                            "type": "table",
                            "commands": []
                        }
                    }
                }]
            }
        ],
        "default_template_id": 1,
        "time_frame": {"relativeTime": 86400000},
        "global_id": "daily_security_summary",
        "time_offset": 0,
        "metadata": "{\"params\": []}"
    }],
    "fromVersion": "8.7.0",
    "widgets_data": []
}
```

---

## Key Takeaways

1. **Empty layouts don't display** - Always include at least one widget
2. **XQL must include `view graph`** - Except for tables (use `fields` instead)
3. **viewOptions must match XQL** - If XQL says `type = pie`, viewOptions must say `"type": "pie"`
4. **Time frames in milliseconds** - 86400000 = 24 hours
5. **Width must sum to 100** - Within each row
6. **metadata is a JSON string** - In reports: `"{\"params\": []}"`
7. **widgets_data always empty** - Never populated in any examples
8. **Reports need header** - Dashboards don't use header widget

---

## Testing Checklist

Before deploying a dashboard/report:

- [ ] Layout is not empty
- [ ] Each widget has valid XQL with `view graph` or `fields`
- [ ] viewOptions type matches XQL view graph type
- [ ] All required viewOptions.commands present (xaxis, yaxis for charts)
- [ ] time_frame is set (in milliseconds)
- [ ] Width percentages sum to 100 per row
- [ ] For reports: Header widget in first row
- [ ] global_id is unique
- [ ] Test XQL query in XSIAM query builder first
