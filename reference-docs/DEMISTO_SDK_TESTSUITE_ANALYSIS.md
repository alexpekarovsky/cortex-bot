# Demisto SDK TestSuite Analysis - XSIAM Content Creation

**Date**: January 2, 2026
**Analyzed Repository**: https://github.com/demisto/demisto-sdk/tree/master/TestSuite

---

## Executive Summary

The demisto-sdk TestSuite provides a **comprehensive framework for programmatically creating XSIAM content** with proper schemas, directory structures, and file formats. This analysis identifies utilities that can significantly enhance our MCP XSIAM content generator tools.

**Key Finding**: The `Rule` class in `rule.py` is the **golden standard** for creating ParsingRules and ModelingRules with proper XIF files, schemas, and samples.

---

## XSIAM-Specific Content Classes

### 1. **Rule Class** (`rule.py`) - THE MOST IMPORTANT
**Purpose**: Creates complete ParsingRule or ModelingRule directory structures with all required files.

**What It Creates**:
```
{name}/
├── {name}.yml          # YAML configuration
├── {name}.xif          # XQL rules file
├── {name}_schema.json  # Schema definition (ModelingRules only)
├── {name}_testdata.json # Test data (optional)
└── samples/            # Sample data directory (ParsingRules only)
    ├── sample-0.json
    ├── sample-1.json
    └── ...
```

**Key Methods**:
- `__init__(tmpdir, name, repo)` - Sets up directory structure
- `build(yml, rules, samples, schema)` - Populates all files
- `set_data(field, value)` - Updates YAML configuration

**Usage Pattern**:
```python
rule = Rule(tmpdir=parsing_rules_path, name="my-rule", repo=repo)
rule.build(
    yml={
        "id": "parsing-rule",
        "name": "Parsing Rule",
        "fromversion": "6.8.0",
        "tags": ["tag"],
        "rules": "",
        "samples": ""
    },
    rules='[INGEST:vendor="vendor", product="product", target_dataset="dataset", no_hit=drop]',
    samples=[{"log": "sample data"}]
)
```

**Why This Matters**: Our current tools create only YML+XIF files. We're missing schema, testdata, and samples directories!

---

### 2. **ParsingRule Class** (`parsing_rule.py`)
**Purpose**: Simplified wrapper for creating parsing rule YAML files only.

**What It Creates**:
- `{name}.yml` with minimal structure (id, name only)

**Limitation**: Does NOT create XIF files, samples, or complete structure. The `Pack.create_parsing_rule()` method uses the `Rule` class instead.

**Default Schema**:
```python
{
    "id": self.name,
    "name": self.name
}
```

---

### 3. **ModelingRule Class** (`modeling_rule.py`)
**Purpose**: Simplified wrapper for modeling rule YAML files only.

**What It Creates**:
- `{name}.yml` with minimal structure (id, name only)

**Limitation**: Does NOT create XIF files or schema. The `Pack.create_modeling_rule()` method uses the `Rule` class instead.

**Default Schema**:
```python
{
    "id": self.name,
    "name": self.name
}
```

---

### 4. **CaseField Class** (`case_field.py`)
**Purpose**: Creates CaseField JSON definitions.

**Default Schema**:
```python
{
    "id": f"casefield-{name}",
    "description": "",
    "cliName": name.lower(),
    "name": name,
    "associatedToAll": False,
    "type": "shortText",
    "associatedTypes": [],
    "threshold": 72,
    "fromVersion": "8.7.0"
}
```

**How It Helps**: Our tool creates similar schemas, but we can adopt their field names and defaults.

---

### 5. **CaseLayout Class** (`case_layout.py`)
**Purpose**: Creates CaseLayout JSON with proper tab structure.

**Default Schema**:
```python
{
    "detailsV2": {
        "tabs": [
            {"id": "overview", "name": "Overview", "type": "overview"},
            {"id": "alertInsights", "name": "Alerts & Insights", "type": "alertInsights"},
            {"id": "timeline", "name": "Timeline", "type": "timeline"},
            {"id": "executions", "name": "Executions", "type": "executions"}
        ]
    },
    "group": "case",
    "id": name,
    "name": name,
    "system": False,
    "version": -1,
    "fromVersion": "8.7.0",
    "description": ""
}
```

**How It Helps**: We use nearly identical schema. Validates our approach.

---

### 6. **CaseLayoutRule Class** (`case_layout_rule.py`)
**Purpose**: Creates CaseLayoutRule JSON with filter logic.

**Default Schema**:
```python
{
    "rule_id": name,
    "rule_name": name,
    "layout_id": "test_layout",
    "description": "",
    "incidents_filter": {
        "AND": [
            {
                "SEARCH_FIELD": "status",
                "SEARCH_TYPE": "NEQ",
                "SEARCH_VALUE": "STATUS_030_RESOLVED_THREAT_HANDLED"
            }
        ]
    },
    "fromVersion": "8.7.0"
}
```

**How It Helps**: Shows proper filter syntax for incidents_filter field.

---

### 7. **XSIAMDashboard Class** (`xsiam_dashboard.py`)
**Purpose**: Creates XSIAMDashboard JSON with widgets and layout.

**Default Schema** (simplified):
```python
{
    "dashboards_data": [
        {
            "global_id": f"xsiam_dashboard_{name}",
            "name": name,
            "description": "",
            "status": "active",
            "layout": [
                {
                    "id": "row1",
                    "widgets": [{"key": "widget1"}]
                }
            ]
        }
    ],
    "widgets_data": [
        {
            "widget_key": "widget1",
            "phrase": "datamodel |filter xdm.observer.vendor=\"mock vendor\"",
            "time_frame": {
                "relativeTime": 2592000000  # 30 days in ms
            }
        }
    ]
}
```

**How It Helps**: Shows proper structure for dashboards_data and widgets_data.

---

### 8. **XSIAMReport Class** (`xsiam_report.py`)
**Purpose**: Creates XSIAMReport JSON with templates and widgets.

**Default Schema** (similar to XSIAMDashboard):
```python
{
    "templates_data": [
        {
            "global_id": f"xsiam_report_{name}",
            "name": name,
            "relative_time": 86400000,  # 1 day
            "layout": [
                {
                    "widgets": [{"key": "widget1"}]
                }
            ]
        }
    ],
    "widgets_data": []
}
```

---

### 9. **CorrelationRule Class** (`correlation_rule.py`)
**Purpose**: Creates CorrelationRule YAML.

**Default Schema**:
```python
{
    "global_rule_id": name,
    "name": name,
    "fromversion": "6.10.0"
}
```

**Note**: This is for file-based correlation rules (older format), not the API-based rules we use.

---

## Base Classes and Infrastructure

### **Pack Class** (`pack.py`) - MOST USEFUL FOR UNDERSTANDING PATTERNS

**Purpose**: Factory class for creating complete content packs with all content types.

**Directory Structure Created**:
```
Packs/{PackName}/
├── Integrations/
├── Scripts/
├── Playbooks/
├── ParsingRules/
├── ModelingRules/
├── CorrelationRules/
├── XSIAMDashboards/
├── XSIAMReports/
├── CaseLayouts/
├── CaseFields/
├── CaseLayoutRules/
├── pack_metadata.json
└── ... (30+ other directories)
```

**Key Factory Methods**:
- `create_parsing_rule(name, yml, rules, samples)` - Uses `Rule` class
- `create_modeling_rule(name, yml, rules, schema)` - Uses `Rule` class
- `create_case_layout(name, json_content)`
- `create_case_field(name, json_content)`
- `create_xsiam_dashboard(name, json_content)`
- `create_xsiam_report(name, json_content)`

**Default ParsingRule Pattern**:
```python
yml = {
    "id": "parsing-rule",
    "name": "Parsing Rule",
    "fromversion": "6.8.0",
    "tags": ["tag"],
    "rules": "",
    "samples": ""
}
rules = '[INGEST:vendor="vendor", product="product", target_dataset="dataset", no_hit=drop]'
```

**Default ModelingRule Pattern**:
```python
yml = {
    "id": "modeling-rule",
    "name": "Modeling Rule",
    "fromversion": "6.8.0",
    "tags": "tag",
    "rules": "",
    "schema": ""
}
rules = '[MODEL: dataset="dataset", model="Model", version=0.1]'
schema = {
    "test_audit_raw": {
        "name": {
            "type": "string",
            "is_array": False
        }
    }
}
```

---

### **JSONBased Class** (`json_based.py`)

**Purpose**: Base class for all JSON content types (CaseField, CaseLayout, XSIAMDashboard, etc.).

**Key Methods**:
- `write_json(data)` - Writes dictionary to JSON file
- `read_json_as_dict()` - Reads JSON as dictionary
- `update(data)` - Merges data into existing file
- `set_data(field, value)` - Updates nested fields using dot notation
- `_set_field_by_path(path, value)` - Supports bracket notation for arrays (e.g., `"alerts_filter.filter.AND.[0].SEARCH_FIELD"`)

**Why This Matters**: Our tools could use similar nested field update patterns.

---

### **YAML Class** (`yml.py`)

**Purpose**: Base class for YAML content types (ParsingRule, ModelingRule, CorrelationRule).

**Key Methods**:
- `write_dict(data)` - Writes dictionary to YAML
- `read_dict()` - Reads YAML as dictionary
- `update(data)` - Updates fields
- `set_data(field, value)` - Nested field updates
- `delete_key(key)` - Removes keys

---

### **TextBased Class** (`text_based.py`)

**Purpose**: Base class for text files (XIF rules files).

**Key Methods**:
- `write_text(text)` - Writes string to file
- `write_list(lst)` - Writes list as newline-separated text

**Why This Matters**: XIF files are plain text, not structured data.

---

## Critical Insights for Our MCP Tools

### 1. **We're Missing Complete Directory Structures**

**Current State**: Our tools create:
- ParsingRules: `{name}.yml` + `{name}.xif`
- ModelingRules: `{name}.yml` + `{name}.xif`

**What We Should Create** (based on demisto-sdk):
```
ParsingRules/{name}/
├── {name}.yml
├── {name}.xif
├── {name}_testdata.json
└── samples/
    └── sample-0.json

ModelingRules/{name}/
├── {name}.yml
├── {name}.xif
├── {name}_schema.json
└── {name}_testdata.json
```

### 2. **XIF Files Are Plain Text, Not JSON**

The `Rule` class uses `File.write()` for XIF files, confirming they're plain text XQL rules.

**Current Approach**: Correct - we write XIF as text.

### 3. **Schema Files Should Be Separate JSON**

ModelingRules need a separate `{name}_schema.json` file, not embedded in YAML.

**Example Schema Format**:
```json
{
    "test_audit_raw": {
        "name": {
            "type": "string",
            "is_array": false
        },
        "user_id": {
            "type": "int",
            "is_array": false
        }
    }
}
```

### 4. **Samples Should Be in Subdirectory**

ParsingRules should have a `samples/` directory with numbered JSON files.

**Example**:
```
samples/
├── sample-0.json
├── sample-1.json
└── sample-2.json
```

### 5. **YAML Metadata Standards**

All rules should include:
```yaml
id: unique-id
name: Display Name
fromversion: "6.8.0"  # or "8.7.0" for XSIAM-specific
tags: [tag1, tag2]
rules: ""  # Reference to XIF file
schema: ""  # Reference to schema file (ModelingRules)
samples: ""  # Reference to samples directory (ParsingRules)
```

### 6. **Pack Metadata Standards**

From `Pack` class:
```json
{
    "name": "PackName",
    "description": "Pack description",
    "support": "xsoar",
    "url": "https://paloaltonetworks.com",
    "author": "Cortex XSOAR",
    "currentVersion": "1.0.0",
    "tags": [],
    "categories": [],
    "useCases": [],
    "keywords": []
}
```

### 7. **Directory Naming Conventions**

From `Pack` class directory creation:
- ParsingRules (not ParsingRule)
- ModelingRules (not ModelingRule)
- XSIAMDashboards (not Dashboards)
- CaseLayouts (not Layouts)
- CaseFields (not IncidentFields)

---

## Recommended Changes to Our MCP Tools

### **Priority 1: Adopt Rule Class Pattern**

Update `create_parsing_rule` and `create_modeling_rule` to create full directory structures:

```python
def create_parsing_rule(pack_name, rule_name, vendor, product, target_dataset, xql_rules):
    """
    Creates:
    - ParsingRules/{rule_name}/{rule_name}.yml
    - ParsingRules/{rule_name}/{rule_name}.xif
    - ParsingRules/{rule_name}/{rule_name}_testdata.json
    - ParsingRules/{rule_name}/samples/sample-0.json
    """
    rule_dir = f"Packs/{pack_name}/ParsingRules/{rule_name}"
    os.makedirs(f"{rule_dir}/samples", exist_ok=True)

    # Create YML
    yml_content = {
        "id": rule_name,
        "name": rule_name,
        "fromversion": "6.8.0",
        "tags": [],
        "rules": "",
        "samples": ""
    }

    # Create XIF
    xif_content = f'[INGEST:vendor="{vendor}", product="{product}", target_dataset="{target_dataset}", no_hit=drop]\n{xql_rules}'

    # Create testdata (empty for now)
    testdata = {}

    # Create sample
    samples = [{"log": "example log entry"}]
```

### **Priority 2: Add Schema Support to ModelingRules**

```python
def create_modeling_rule(pack_name, rule_name, dataset, model, xql_rules, schema_json=None):
    """
    Creates:
    - ModelingRules/{rule_name}/{rule_name}.yml
    - ModelingRules/{rule_name}/{rule_name}.xif
    - ModelingRules/{rule_name}/{rule_name}_schema.json
    - ModelingRules/{rule_name}/{rule_name}_testdata.json
    """
    if not schema_json:
        schema_json = {
            f"{dataset}_raw": {
                "field_name": {
                    "type": "string",
                    "is_array": False
                }
            }
        }
```

### **Priority 3: Validate Against TestSuite Schemas**

Use the default schemas from TestSuite classes as validation references:
- CaseField defaults
- CaseLayout tab structure
- XSIAMDashboard widget patterns

### **Priority 4: Adopt Nested Field Update Pattern**

Implement `_set_field_by_path()` pattern from `JSONBased` for better field manipulation:

```python
def set_field_by_path(self, path: str, value):
    """
    Update nested fields using dot notation:
    - "incidents_filter.AND.[0].SEARCH_FIELD"
    - "dashboards_data.[0].layout.[0].widgets.[0].key"
    """
```

---

## File Locations Reference

| File | Purpose | Key Classes/Methods |
|------|---------|---------------------|
| `rule.py` | Complete rule directory creation | `Rule.__init__`, `Rule.build()` |
| `pack.py` | Pack factory with all content types | `Pack.create_parsing_rule()`, `Pack.create_modeling_rule()` |
| `json_based.py` | Base for JSON content | `JSONBased._set_field_by_path()` |
| `yml.py` | Base for YAML content | `YAML.write_dict()`, `YAML.read_dict()` |
| `text_based.py` | Base for text files (XIF) | `TextBased.write_text()` |
| `parsing_rule.py` | Simplified parsing rule wrapper | `ParsingRule.create_default_parsing_rule()` |
| `modeling_rule.py` | Simplified modeling rule wrapper | `ModelingRule.create_default_modeling_rule()` |
| `case_field.py` | CaseField creation | `CaseField.create_default()` |
| `case_layout.py` | CaseLayout creation | `CaseLayout.create_default()` |
| `case_layout_rule.py` | CaseLayoutRule creation | `CaseLayoutRule.create_default_case_layout_rule()` |
| `xsiam_dashboard.py` | XSIAMDashboard creation | `XSIAMDashboard.create_default()` |
| `xsiam_report.py` | XSIAMReport creation | `XSIAMReport.create_default()` |
| `correlation_rule.py` | CorrelationRule creation | `CorrelationRule.create_default_correlation_rule()` |

---

## Example: Complete ParsingRule Creation (Demisto SDK Way)

```python
from TestSuite.rule import Rule
from TestSuite.pack import Pack

# Create pack
pack = Pack(tmpdir, "MyPack", repo)

# Create parsing rule using Pack factory
parsing_rule = pack.create_parsing_rule(
    name="nginx-access-logs",
    yml={
        "id": "nginx-access-logs",
        "name": "NGINX Access Logs Parser",
        "fromversion": "6.8.0",
        "tags": ["nginx", "web"],
        "rules": "",
        "samples": ""
    },
    rules='[INGEST:vendor="nginx", product="access_log", target_dataset="nginx_access_raw", no_hit=drop]\n_raw_log = arrayindex(regextract(_raw_log, "^(?P<ip>\\S+)"), 0)',
    samples=[
        {"log": '192.168.1.1 - - [01/Jan/2026:10:00:00 +0000] "GET / HTTP/1.1" 200'},
        {"log": '10.0.0.5 - - [01/Jan/2026:10:01:00 +0000] "POST /api HTTP/1.1" 201'}
    ]
)

# This creates:
# ParsingRules/nginx-access-logs/
# ├── nginx-access-logs.yml
# ├── nginx-access-logs.xif
# ├── nginx-access-logs_testdata.json
# └── samples/
#     ├── sample-0.json
#     └── sample-1.json
```

---

## Conclusion

The demisto-sdk TestSuite provides the **definitive reference** for XSIAM content structure. Our MCP tools should:

1. **Adopt the Rule class pattern** for complete directory structures
2. **Add schema support** to ModelingRules
3. **Add samples directory** to ParsingRules
4. **Use default schemas** from TestSuite classes as validation
5. **Implement nested field updates** for better data manipulation

**Next Steps**:
1. Refactor `create_parsing_rule` to match `Rule.build()` pattern
2. Refactor `create_modeling_rule` to include schema files
3. Add testdata file creation to both
4. Update documentation with complete file structure examples
5. Consider creating a local TestSuite-style testing framework

**Impact**: This will bring our XSIAM content generators to **production quality**, matching Palo Alto's official SDK standards.
