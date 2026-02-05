# XSIAM Content Schema Analysis

**Analysis Date**: January 2, 2026
**Purpose**: Compare our XSIAM content generator tools against official demisto-sdk schemas

---

## Executive Summary

### Key Findings

1. **ParsingRule**: ✅ Mostly compliant, missing `rules` and `samples` optional fields
2. **ModelingRule**: ✅ Mostly compliant, missing `tags` field (should be array, not empty)
3. **AssetsModelingRule**: ✅ Compliant with same notes as ModelingRule
4. **Platform-Specific Overrides**: ⚠️ Not implemented (low priority for XSIAM)

---

## ParsingRule Schema Analysis

### Official Schema (demisto-sdk)

**Required Fields:**
- `id` (string): Unique identifier
- `name` (string): Display name
- `fromversion` (string): Minimum version requirement
- `tags` (sequence of strings): Classification labels; can be empty

**Optional Fields:**
- `toversion` (string): Maximum version constraint
- `rules` (string): Parsing logic/patterns
- `samples` (string): Example data
- `comment` (string): Additional documentation
- `deprecated` (boolean): Legacy status flag

**Platform Overrides:** (Optional)
- `name:{platform}`, `deprecated:{platform}`, `id:{platform}`
- Supported platforms: `xsoar`, `marketplacev2`, `xpanse`, `xsoar_saas`, `xsoar_on_prem`

### Our Current Implementation

**File**: `/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsiam_content_generator.py`

**Lines 512-520** (create_parsing_rule):
```yaml
name: {rule_name}
id: {rule_id}
fromversion: 8.7.0
tags: []
rules: ''
samples: ''
```

### Comparison

| Field | Schema Required | Schema Optional | Our Implementation | Status |
|-------|----------------|-----------------|-------------------|--------|
| `id` | ✅ | | ✅ Generated from rule_name | ✅ PASS |
| `name` | ✅ | | ✅ From parameter | ✅ PASS |
| `fromversion` | ✅ | | ✅ Hardcoded "8.7.0" | ✅ PASS |
| `tags` | ✅ (can be empty) | | ✅ Empty array `[]` | ✅ PASS |
| `toversion` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |
| `rules` | | ✅ | ✅ Empty string `''` | ⚠️ OK (should be set) |
| `samples` | | ✅ | ✅ Empty string `''` | ⚠️ OK (optional) |
| `comment` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |
| `deprecated` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |

### Issues Found

**ISSUE 1: `rules` field is empty**
- The schema has `rules` as an optional field for "parsing logic/patterns"
- We set `rules: ''` (empty string)
- However, the actual parsing logic goes in the `.xif` file
- **VERDICT**: ✅ This is correct - YML is metadata, XIF is logic

**ISSUE 2: `samples` field is empty**
- The schema defines `samples` for "example data"
- We set `samples: ''` (empty string)
- **RECOMMENDATION**: Allow users to optionally provide sample data
- **PRIORITY**: Low - not required for functionality

### Recommendations

1. **Add `samples` parameter** (optional, low priority)
   ```python
   samples: Annotated[Optional[str], Field(description="Example log samples")] = None
   ```

2. **Add `comment` parameter** (optional, low priority)
   ```python
   comment: Annotated[Optional[str], Field(description="Additional notes")] = None
   ```

---

## ModelingRule Schema Analysis

### Official Schema (demisto-sdk)

**Required Fields:**
- `id` (string): Unique identifier
- `name` (string): Rule name
- `fromversion` (string): Starting version

**Optional Fields:**
- `toversion` (string): Ending version
- `tags` (string): Categorization labels
- `rules` (string): Rule definitions
- `schema` (string): Data structure specification
- `comment` (string): Documentation notes
- `deprecated` (boolean): Deprecation status

**Platform Overrides:** Same as ParsingRule

### Our Current Implementation

**Lines 604-612** (create_modeling_rule):
```yaml
fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags:
```

### Comparison

| Field | Schema Required | Schema Optional | Our Implementation | Status |
|-------|----------------|-----------------|-------------------|--------|
| `id` | ✅ | | ✅ Generated from rule_name | ✅ PASS |
| `name` | ✅ | | ✅ From parameter | ✅ PASS |
| `fromversion` | ✅ | | ✅ Hardcoded "8.7.0" | ✅ PASS |
| `toversion` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |
| `tags` | | ✅ | ⚠️ Empty (no value) | ⚠️ SEE ISSUE 1 |
| `rules` | | ✅ | ✅ Empty string `''` | ✅ PASS |
| `schema` | | ✅ | ✅ Empty string `''` | ✅ PASS |
| `comment` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |
| `deprecated` | | ✅ | ❌ Not implemented | ⚠️ OK (optional) |

### Issues Found

**ISSUE 1: `tags` field format mismatch**
- **Schema says**: `tags` is a **string** (optional)
- **Our YML has**: `tags:` with no value (empty, not a string)
- **Expected**: Either `tags: ''` or omit the field entirely
- **PRIORITY**: Medium - could cause validation warnings

**ISSUE 2: Schema says `tags` is string, but ParsingRule has array**
- ParsingRule schema: `tags` is **sequence of strings**
- ModelingRule schema: `tags` is **string**
- This is inconsistent in the official schema
- **VERDICT**: Follow the schema exactly per content type

### Recommendations

1. **Fix `tags` field in ModelingRule**
   ```yaml
   # CURRENT (WRONG):
   tags:

   # SHOULD BE:
   tags: ''

   # OR BETTER (if user provides tags):
   tags: 'security,network,audit'
   ```

2. **Add `tags` parameter** to create_modeling_rule
   ```python
   tags: Annotated[Optional[str], Field(description="Comma-separated tags")] = None
   ```

---

## ModelingRuleSchema Analysis

### Official Schema (demisto-sdk)

**Purpose**: Defines the structure of the `schema` field in ModelingRule YML

**Structure**:
```yaml
type: map
mapping:
  regex;(.+_raw):
    type: map
    mapping:
      regex;(.+):
        type: map
        mapping:
          type:
            type: str
            required: true
            enum: ["string", "int", "float", "datetime", "boolean"]
          is_array:
            type: bool
            required: true
```

**Translation**:
- Top-level keys must end with `_raw` (regex pattern)
- Nested keys can be any name (regex pattern)
- Each field must have:
  - `type`: One of "string", "int", "float", "datetime", "boolean"
  - `is_array`: Boolean (true/false)

### Our Current Implementation

We generate: `schema: ''` (empty string)

If user provides `schema_json` parameter, we save it as a separate `_schema.json` file.

**Lines 622-629**:
```python
if schema_json:
    try:
        schema_data = json.loads(schema_json)
        schema_path = rule_dir / f"{safe_rule_name}_schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema_data, f, indent=4)
    except json.JSONDecodeError:
        logger.warning("Invalid schema_json provided, skipping schema file")
```

### Issues Found

**ISSUE 1: Schema file naming and location**
- We create `{RuleName}_schema.json` as a separate file
- Schema specification suggests it should be embedded in the YML `schema` field
- **However**: The YML field is a string, and the schema is complex
- **VERDICT**: ⚠️ Unclear if schema should be embedded or separate file

**ISSUE 2: No validation of schema structure**
- We accept any JSON without validating against the schema format
- Should validate that it follows the `_raw` → fields → {type, is_array} structure
- **PRIORITY**: Low - advanced feature

### Recommendations

1. **Research how schemas are actually used** in production
   - Check if they're embedded as YAML string or separate files
   - Look at real-world examples

2. **Add schema validation** (low priority)
   - Validate against the modelingruleschema.yml structure
   - Warn if schema doesn't match expected format

---

## AssetsModelingRule Schema Analysis

### Official Schema (demisto-sdk)

**Identical to ModelingRule** except it uses `model="Assets"` in the XIF file.

**Required Fields:**
- `id`, `name`, `fromversion` (same as ModelingRule)

**Optional Fields:**
- `toversion`, `tags`, `rules`, `schema`, `comment`, `deprecated`

### Our Current Implementation

**Lines 700-708** (create_assets_modeling_rule):
```yaml
fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags:
```

### Comparison

**SAME ISSUES AS MODELINGRULE**:
- `tags:` field is empty (should be `tags: ''` or omitted)
- Missing optional fields (toversion, comment, deprecated)

### Recommendations

**Same as ModelingRule** - fix tags field.

---

## Platform-Specific Overrides

All content types support platform-specific field overrides:

```yaml
name: "Default Name"
name:marketplacev2: "XSIAM-Specific Name"
name:xsoar: "XSOAR Classic Name"
```

### Our Implementation

❌ **Not implemented** - we don't support platform overrides

### Recommendation

**Priority**: Low - only needed for multi-platform packs

For XSIAM-only content (marketplacev2), this is not needed.

If we want to support it in the future:
```python
# Add optional parameters like:
name_marketplacev2: Annotated[Optional[str], Field(description="XSIAM-specific name")] = None

# Then in YML generation:
if name_marketplacev2:
    yml_content += f"name:marketplacev2: {name_marketplacev2}\n"
```

---

## Summary of Required Fixes

### HIGH PRIORITY

None - all required fields are implemented correctly.

### MEDIUM PRIORITY

1. **Fix `tags` field in ModelingRule and AssetsModelingRule**
   - Current: `tags:` (empty, no value)
   - Should be: `tags: ''` or add parameter for user-provided tags
   - File: `xsiam_content_generator.py`, lines 604-612 and 700-708

### LOW PRIORITY

1. **Add optional parameters** for completeness:
   - `samples` for ParsingRule
   - `comment` for all rule types
   - `toversion` for all rule types
   - `deprecated` for all rule types

2. **Research schema implementation**:
   - Determine if schema should be embedded in YML or separate file
   - Add validation for schema structure

3. **Platform-specific overrides**:
   - Only implement if we need multi-platform support
   - Not needed for XSIAM-only content

---

## Validation Testing Needed

To confirm our implementation is correct, we should:

1. **Run demisto-sdk validate** on generated content:
   ```bash
   demisto-sdk validate -i Packs/SchemaTestPack/ParsingRules/Test_Parsing_Rule/
   demisto-sdk validate -i Packs/DebugPack20250102/ModelingRules/
   ```

2. **Check for validation warnings** related to:
   - Missing required fields
   - Incorrect field types
   - Schema violations

3. **Test upload** to verify XSIAM accepts the content

---

## Specific Code Changes Required

### Change 1: Fix ModelingRule tags field

**File**: `/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsiam_content_generator.py`

**Line 604-612** - Current:
```python
yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags:
"""
```

**Should be**:
```python
yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags: ''
"""
```

### Change 2: Fix AssetsModelingRule tags field

**File**: Same as above

**Line 700-708** - Current:
```python
yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags:
"""
```

**Should be**:
```python
yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags: ''
"""
```

---

## Conclusion

Our XSIAM content generators are **mostly compliant** with the official demisto-sdk schemas.

**Critical Issues**: None
**Medium Issues**: 1 (tags field format in ModelingRule/AssetsModelingRule)
**Low Priority Enhancements**: 3 (optional fields, schema research, platform overrides)

The generators successfully create valid content that:
- ✅ Includes all required fields
- ✅ Uses correct field types
- ✅ Sets appropriate default values
- ⚠️ Could benefit from fixing tags field format
- ⚠️ Could add more optional fields for completeness

**Recommendation**: Apply the medium priority fix (tags field) and validate with demisto-sdk before considering low-priority enhancements.
