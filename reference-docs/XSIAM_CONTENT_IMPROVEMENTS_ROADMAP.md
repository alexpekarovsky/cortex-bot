# XSIAM Content Generator Improvements Roadmap

**Based on**: demisto-sdk TestSuite analysis (January 2, 2026)
**Status**: Action items prioritized
**File**: `/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsiam_content_generator.py`

---

## Quick Summary

Our current tools create **minimal** content:
- ✅ YML files (correct)
- ✅ XIF files (correct)
- ❌ Missing: Schema files
- ❌ Missing: Testdata files
- ❌ Missing: Samples directories
- ❌ Missing: Proper subdirectory structure

**What demisto-sdk does**:
```
ParsingRules/rule-name/          ModelingRules/rule-name/
├── rule-name.yml                ├── rule-name.yml
├── rule-name.xif                ├── rule-name.xif
├── rule-name_testdata.json      ├── rule-name_schema.json
└── samples/                     └── rule-name_testdata.json
    ├── sample-0.json
    └── sample-1.json
```

---

## Priority 1: Add Complete Directory Structure (CRITICAL)

### Current Implementation
```python
def create_parsing_rule(ctx, pack_name, rule_name, vendor, product, target_dataset, xql_rules, upload):
    # Creates:
    # - ParsingRules/RuleName/RuleName.yml
    # - ParsingRules/RuleName/RuleName.xif
```

### Target Implementation
```python
def create_parsing_rule(ctx, pack_name, rule_name, vendor, product, target_dataset, xql_rules, samples=None, upload=False):
    """
    Creates complete ParsingRule structure:
    - ParsingRules/{RuleName}/{RuleName}.yml
    - ParsingRules/{RuleName}/{RuleName}.xif
    - ParsingRules/{RuleName}/{RuleName}_testdata.json
    - ParsingRules/{RuleName}/samples/sample-0.json (if samples provided)
    """
    rule_dir = pack_dir / "ParsingRules" / rule_name
    rule_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    samples_dir = rule_dir / "samples"
    if samples:
        samples_dir.mkdir(exist_ok=True)

    # YML content with proper references
    yml_content = {
        "id": rule_name,
        "name": rule_name,
        "fromversion": "6.8.0",
        "tags": [vendor, product],
        "rules": "",  # Reference to XIF file
        "samples": ""  # Reference to samples directory
    }

    # XIF content (unchanged)
    xif_content = f'[INGEST:vendor="{vendor}", product="{product}", target_dataset="{target_dataset}", no_hit=drop]\n{xql_rules}'

    # NEW: Create testdata file
    testdata_path = rule_dir / f"{rule_name}_testdata.json"
    with open(testdata_path, 'w') as f:
        json.dump({}, f, indent=2)  # Empty for now

    # NEW: Create samples
    if samples:
        for idx, sample_data in enumerate(samples):
            sample_path = samples_dir / f"sample-{idx}.json"
            with open(sample_path, 'w') as f:
                json.dump(sample_data, f, indent=2)

    # Write YML and XIF (existing code)
    # ... rest of implementation
```

---

## Priority 2: Add Schema Support to ModelingRules (CRITICAL)

### Current Implementation
```python
def create_modeling_rule(ctx, pack_name, rule_name, dataset, model, xql_rules, upload):
    # Creates:
    # - ModelingRules/RuleName/RuleName.yml
    # - ModelingRules/RuleName/RuleName.xif
```

### Target Implementation
```python
def create_modeling_rule(ctx, pack_name, rule_name, dataset, model, xql_rules, schema_json=None, upload=False):
    """
    Creates complete ModelingRule structure:
    - ModelingRules/{RuleName}/{RuleName}.yml
    - ModelingRules/{RuleName}/{RuleName}.xif
    - ModelingRules/{RuleName}/{RuleName}_schema.json
    - ModelingRules/{RuleName}/{RuleName}_testdata.json
    """
    rule_dir = pack_dir / "ModelingRules" / rule_name
    rule_dir.mkdir(parents=True, exist_ok=True)

    # YML content with schema reference
    yml_content = {
        "id": rule_name,
        "name": rule_name,
        "fromversion": "6.8.0",
        "tags": [dataset, model],
        "rules": "",  # Reference to XIF file
        "schema": ""  # Reference to schema file
    }

    # XIF content (unchanged)
    xif_content = f'[MODEL: dataset="{dataset}", model="{model}", version=0.1]\n{xql_rules}'

    # NEW: Create schema file
    if not schema_json:
        # Default schema structure
        schema_json = {
            f"{dataset}_raw": {
                "example_field": {
                    "type": "string",
                    "is_array": False
                }
            }
        }

    schema_path = rule_dir / f"{rule_name}_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema_json, f, indent=2)

    # NEW: Create testdata file
    testdata_path = rule_dir / f"{rule_name}_testdata.json"
    with open(testdata_path, 'w') as f:
        json.dump({}, f, indent=2)

    # Write YML and XIF (existing code)
    # ... rest of implementation
```

---

## Priority 3: Update Function Signatures (HIGH)

### Add New Parameters

**create_parsing_rule**:
```python
@mcp.tool()
async def create_parsing_rule(
    ctx,
    pack_name: str,
    rule_name: str,
    vendor: str,
    product: str,
    target_dataset: str,
    xql_rules: str,
    samples: str | None = None,  # NEW: JSON array of sample data
    upload: bool | None = False
) -> dict:
    """
    Creates a ParsingRule with complete directory structure.

    Args:
        samples: Optional JSON array of sample log data:
                 '[{"log": "example 1"}, {"log": "example 2"}]'
    """
```

**create_modeling_rule**:
```python
@mcp.tool()
async def create_modeling_rule(
    ctx,
    pack_name: str,
    rule_name: str,
    dataset: str,
    model: str,
    xql_rules: str,
    schema_json: str | None = None,  # NEW: JSON schema definition
    upload: bool | None = False
) -> dict:
    """
    Creates a ModelingRule with schema and testdata files.

    Args:
        schema_json: Optional JSON schema:
                     '{"dataset_raw": {"field": {"type": "string", "is_array": false}}}'
    """
```

---

## Priority 4: Improve Default YML Schemas (MEDIUM)

### Current YML Templates
Our current templates are minimal. Enhance them based on demisto-sdk defaults.

**ParsingRule YML** (current):
```yaml
id: RuleName
name: RuleName
```

**ParsingRule YML** (should be):
```yaml
id: rule-name
name: Descriptive Rule Name
fromversion: "6.8.0"
tags:
  - vendor-name
  - product-name
rules: ""
samples: ""
```

**ModelingRule YML** (should be):
```yaml
id: rule-name
name: Descriptive Rule Name
fromversion: "6.8.0"
tags:
  - dataset-name
  - model-name
rules: ""
schema: ""
```

---

## Priority 5: Add Validation (MEDIUM)

### Validate Against demisto-sdk Patterns

```python
def validate_parsing_rule_structure(rule_dir: Path) -> list[str]:
    """
    Validates ParsingRule has all required files:
    - {name}.yml
    - {name}.xif
    - {name}_testdata.json
    - samples/ directory (optional but recommended)
    """
    errors = []
    rule_name = rule_dir.name

    required_files = [
        f"{rule_name}.yml",
        f"{rule_name}.xif",
        f"{rule_name}_testdata.json"
    ]

    for file in required_files:
        if not (rule_dir / file).exists():
            errors.append(f"Missing required file: {file}")

    return errors

def validate_modeling_rule_structure(rule_dir: Path) -> list[str]:
    """
    Validates ModelingRule has all required files:
    - {name}.yml
    - {name}.xif
    - {name}_schema.json
    - {name}_testdata.json
    """
    errors = []
    rule_name = rule_dir.name

    required_files = [
        f"{rule_name}.yml",
        f"{rule_name}.xif",
        f"{rule_name}_schema.json",
        f"{rule_name}_testdata.json"
    ]

    for file in required_files:
        if not (rule_dir / file).exists():
            errors.append(f"Missing required file: {file}")

    return errors
```

---

## Priority 6: Update Documentation (LOW)

### Update Tool Descriptions

**Current**:
```
Creates a ParsingRule with YML and XIF files for XSIAM.
```

**Should Be**:
```
Creates a complete ParsingRule directory structure for XSIAM.

Creates:
- ParsingRules/{RuleName}/{RuleName}.yml (metadata)
- ParsingRules/{RuleName}/{RuleName}.xif (XQL parsing rules)
- ParsingRules/{RuleName}/{RuleName}_testdata.json (test data)
- ParsingRules/{RuleName}/samples/ (sample log files)

Based on demisto-sdk TestSuite patterns for production-quality content.
```

### Add Schema Examples to Docstrings

```python
@mcp.tool()
async def create_modeling_rule(..., schema_json: str | None = None, ...):
    """
    Args:
        schema_json: JSON schema defining source dataset fields.
                     Example:
                     {
                         "nginx_access_raw": {
                             "client_ip": {"type": "string", "is_array": false},
                             "status_code": {"type": "int", "is_array": false},
                             "request_path": {"type": "string", "is_array": false}
                         }
                     }
    """
```

---

## Implementation Checklist

### Phase 1: Core Structure (Week 1)
- [ ] Update `create_parsing_rule` to create subdirectories
- [ ] Add `_testdata.json` file creation
- [ ] Add `samples/` directory creation
- [ ] Update function signature with `samples` parameter
- [ ] Test with real XSIAM upload

### Phase 2: Schema Support (Week 1)
- [ ] Update `create_modeling_rule` to create schema file
- [ ] Add `_schema.json` file creation
- [ ] Add `_testdata.json` file creation
- [ ] Update function signature with `schema_json` parameter
- [ ] Test with real XSIAM upload

### Phase 3: Quality Improvements (Week 2)
- [ ] Enhance default YML templates
- [ ] Add validation functions
- [ ] Update tool descriptions
- [ ] Add comprehensive examples to docstrings
- [ ] Update XSIAM content guide

### Phase 4: Testing (Week 2)
- [ ] Create test ParsingRule with samples
- [ ] Create test ModelingRule with schema
- [ ] Upload to XSIAM and validate
- [ ] Run demisto-sdk validate
- [ ] Document any upload errors

---

## Testing Strategy

### Test Case 1: ParsingRule with Samples
```python
samples = [
    {"log": '192.168.1.1 - - [01/Jan/2026:10:00:00 +0000] "GET / HTTP/1.1" 200'},
    {"log": '10.0.0.5 - - [01/Jan/2026:10:01:00 +0000] "POST /api HTTP/1.1" 201'}
]

result = create_parsing_rule(
    pack_name="TestPack",
    rule_name="nginx-access-logs",
    vendor="nginx",
    product="access_log",
    target_dataset="nginx_access_raw",
    xql_rules='_raw_log = arrayindex(regextract(_raw_log, "^(?P<ip>\\S+)"), 0)',
    samples=json.dumps(samples)
)
```

**Expected Output**:
```
ParsingRules/nginx-access-logs/
├── nginx-access-logs.yml
├── nginx-access-logs.xif
├── nginx-access-logs_testdata.json
└── samples/
    ├── sample-0.json
    └── sample-1.json
```

### Test Case 2: ModelingRule with Schema
```python
schema = {
    "nginx_access_raw": {
        "client_ip": {"type": "string", "is_array": False},
        "status_code": {"type": "int", "is_array": False}
    }
}

result = create_modeling_rule(
    pack_name="TestPack",
    rule_name="nginx-access-model",
    dataset="nginx_access_raw",
    model="Network",
    xql_rules="alter xdm.network.source.ipv4 = client_ip",
    schema_json=json.dumps(schema)
)
```

**Expected Output**:
```
ModelingRules/nginx-access-model/
├── nginx-access-model.yml
├── nginx-access-model.xif
├── nginx-access-model_schema.json
└── nginx-access-model_testdata.json
```

---

## Reference: demisto-sdk Rule Class Pattern

```python
# From TestSuite/rule.py
class Rule(TestSuiteBase):
    def __init__(self, tmpdir: Path, name: str, repo: Repo):
        self._tmpdir_rule_path = tmpdir / f"{self.name}"
        self._tmpdir_rule_path.mkdir()

        self.yml = YAML(self._tmpdir_rule_path / f"{self.name}.yml", self._repo.path)
        self.rules = File(self._tmpdir_rule_path / f"{self.name}.xif", self._repo.path)
        self.schema = JSONBased(self._tmpdir_rule_path, f"{self.name}_schema", "")
        self.testdata = JSONBased(self._tmpdir_rule_path, f"{self.name}_testdata", "")

        self.samples: list[JSONBased] = []
        self.samples_dir_path = tmpdir / self.name / SAMPLES_DIR

    def build(self, yml: dict, rules: str | None = None, samples: list[dict] | None = None, schema: dict | None = None):
        self.yml.write_dict(yml)
        if rules:
            self.rules.write(rules)
        if schema:
            self.schema.write_json(schema)
        if samples:
            self.samples_dir_path.mkdir()
            for sample in samples:
                sample_file = JSONBased(dir_path=self.samples_dir_path, name=f"sample-{len(self.samples)}", prefix="")
                sample_file.write_json(sample)
                self.samples.append(sample_file)
```

**Key Takeaway**: We should mirror this pattern exactly.

---

## Success Metrics

### Before Improvements
- ✅ 2 files created per ParsingRule (YML + XIF)
- ✅ 2 files created per ModelingRule (YML + XIF)
- ❌ No validation against demisto-sdk standards
- ⚠️ Upload works but structure incomplete

### After Improvements
- ✅ 3-4 files created per ParsingRule (YML + XIF + testdata + samples)
- ✅ 4 files created per ModelingRule (YML + XIF + schema + testdata)
- ✅ Matches demisto-sdk TestSuite structure
- ✅ Passes demisto-sdk validate
- ✅ Production-quality content

---

## Next Steps

1. **Read this document** to understand the gaps
2. **Read full analysis** at `/Users/apekarovsky/projects/cortex-mcp/DEMISTO_SDK_TESTSUITE_ANALYSIS.md`
3. **Update xsiam_content_generator.py** with Priority 1 & 2 changes
4. **Test locally** before committing
5. **Update CLAUDE.md** with new file structures
6. **Document examples** in USECASES.md

**Estimated Time**: 4-6 hours for full implementation
**Impact**: Production-quality XSIAM content that matches Palo Alto standards
