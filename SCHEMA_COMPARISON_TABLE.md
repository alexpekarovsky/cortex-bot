# XSIAM Content Generator - Schema Compliance Table

**Analysis Date**: January 2, 2026
**Branch**: CRTX-194114-fix-openapi-tools

---

## ParsingRule Field Comparison

| Field Name | Required | Type | Default | Our Implementation | Status | Notes |
|------------|----------|------|---------|-------------------|--------|-------|
| `id` | ✅ | string | - | ✅ `sanitize_name(rule_name).lower()` | ✅ PASS | Auto-generated from rule_name |
| `name` | ✅ | string | - | ✅ From `rule_name` parameter | ✅ PASS | User-provided |
| `fromversion` | ✅ | string | - | ✅ `"8.7.0"` hardcoded | ✅ PASS | XSIAM minimum version |
| `tags` | ✅ | sequence | `[]` | ✅ `[]` empty array | ✅ PASS | Can be empty per schema |
| `toversion` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement: Add parameter |
| `rules` | ❌ | string | - | ✅ `''` empty string | ✅ PASS | Logic goes in .xif file |
| `samples` | ❌ | string | - | ✅ `''` empty string | ⚠️ OPTIONAL | Enhancement: Add parameter |
| `comment` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement: Add parameter |
| `deprecated` | ❌ | boolean | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement: Add parameter |

**Platform Overrides** (all optional):
- `name:{platform}` - ❌ Not implemented (low priority)
- `deprecated:{platform}` - ❌ Not implemented (low priority)
- `id:{platform}` - ❌ Not implemented (low priority)

**Platforms**: `xsoar`, `marketplacev2`, `xpanse`, `xsoar_saas`, `xsoar_on_prem`

---

## ModelingRule Field Comparison

| Field Name | Required | Type | Default | Our Implementation | Status | Notes |
|------------|----------|------|---------|-------------------|--------|-------|
| `id` | ✅ | string | - | ✅ `sanitize_name(rule_name).lower()` | ✅ PASS | Auto-generated |
| `name` | ✅ | string | - | ✅ From `rule_name` parameter | ✅ PASS | User-provided |
| `fromversion` | ✅ | string | - | ✅ `"8.7.0"` hardcoded | ✅ PASS | XSIAM minimum |
| `toversion` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |
| `tags` | ❌ | **string** | - | ⚠️ `tags:` (empty, no value) | ⚠️ **FIX NEEDED** | Should be `tags: ''` |
| `rules` | ❌ | string | - | ✅ `''` empty string | ✅ PASS | Logic in .xif file |
| `schema` | ❌ | string | - | ✅ `''` empty string | ✅ PASS | Optional schema def |
| `comment` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |
| `deprecated` | ❌ | boolean | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |

**⚠️ CRITICAL ISSUE**: `tags` field is empty (no value) - should be `tags: ''` (empty string)

**Platform Overrides** (all optional):
- Same as ParsingRule - not implemented

---

## AssetsModelingRule Field Comparison

| Field Name | Required | Type | Default | Our Implementation | Status | Notes |
|------------|----------|------|---------|-------------------|--------|-------|
| `id` | ✅ | string | - | ✅ `sanitize_name(rule_name).lower()` | ✅ PASS | Auto-generated |
| `name` | ✅ | string | - | ✅ From `rule_name` parameter | ✅ PASS | User-provided |
| `fromversion` | ✅ | string | - | ✅ `"8.7.0"` hardcoded | ✅ PASS | XSIAM minimum |
| `toversion` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |
| `tags` | ❌ | **string** | - | ⚠️ `tags:` (empty, no value) | ⚠️ **FIX NEEDED** | Should be `tags: ''` |
| `rules` | ❌ | string | - | ✅ `''` empty string | ✅ PASS | Logic in .xif file |
| `schema` | ❌ | string | - | ✅ `''` empty string | ✅ PASS | Optional schema def |
| `comment` | ❌ | string | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |
| `deprecated` | ❌ | boolean | - | ❌ Not implemented | ⚠️ OPTIONAL | Enhancement |

**⚠️ CRITICAL ISSUE**: Same as ModelingRule - `tags` field format

---

## ModelingRuleSchema Structure

**Purpose**: Defines the format of the `schema` field in ModelingRule/AssetsModelingRule

**Official Structure**:
```yaml
{dataset_name}_raw:
  field_name_1:
    type: "string" | "int" | "float" | "datetime" | "boolean"
    is_array: true | false
  field_name_2:
    type: "string"
    is_array: false
```

**Our Implementation**:
- We accept `schema_json` parameter (optional)
- Save as separate `{RuleName}_schema.json` file
- No validation of structure

**Status**: ⚠️ Needs research
- Unclear if schema should be embedded in YML or separate file
- No validation against schema structure
- **Priority**: Low (advanced feature)

---

## Summary by Priority

### 🔴 HIGH PRIORITY (Breaking Issues)

**None** - All required fields are correctly implemented.

---

### 🟡 MEDIUM PRIORITY (Should Fix Soon)

1. **Fix `tags` field format in ModelingRule and AssetsModelingRule**
   - **File**: `xsiam_content_generator.py`
   - **Lines**: 609 (ModelingRule), 705 (AssetsModelingRule)
   - **Current**: `tags:` (empty, no value)
   - **Should be**: `tags: ''` (empty string)
   - **Impact**: May cause demisto-sdk validation warnings
   - **Effort**: Trivial (add two characters)

---

### 🟢 LOW PRIORITY (Nice to Have)

1. **Add optional field parameters**:
   - `samples` (ParsingRule only)
   - `comment` (all rule types)
   - `toversion` (all rule types)
   - `deprecated` (all rule types)
   - **Benefit**: More complete metadata
   - **Effort**: Low (add parameters and YML generation)

2. **Research and implement schema handling**:
   - Determine if schema should be in YML or separate file
   - Add validation against modelingruleschema.yml structure
   - **Benefit**: Better schema validation
   - **Effort**: Medium (requires research)

3. **Add platform-specific override support**:
   - `name:{platform}`, `id:{platform}`, `deprecated:{platform}`
   - **Benefit**: Multi-platform pack support
   - **Effort**: Medium
   - **Priority**: Very low (not needed for XSIAM-only content)

---

## Validation Test Commands

To validate our generated content against official schemas:

```bash
# Test ParsingRule
demisto-sdk validate -i /Users/apekarovsky/projects/content/Packs/SchemaTestPack/ParsingRules/Test_Parsing_Rule/

# Test ModelingRule (if exists)
demisto-sdk validate -i /Users/apekarovsky/projects/content/Packs/*/ModelingRules/*/

# Test AssetsModelingRule (if exists)
demisto-sdk validate -i /Users/apekarovsky/projects/content/Packs/*/AssetsModelingRules/*/

# Validate entire pack
demisto-sdk validate -i /Users/apekarovsky/projects/content/Packs/DebugPack20250102/
```

---

## Required Code Changes

### Fix 1: ModelingRule tags field

**File**: `/Users/apekarovsky/projects/cortex-mcp/src/usecase/custom_components/xsiam_content_generator.py`

**Line 609** - Change from:
```python
tags:
"""
```

**To**:
```python
tags: ''
"""
```

---

### Fix 2: AssetsModelingRule tags field

**File**: Same as above

**Line 705** - Change from:
```python
tags:
"""
```

**To**:
```python
tags: ''
"""
```

---

## Expected Outcomes After Fixes

### Before Fix
```bash
demisto-sdk validate -i Packs/TestPack/ModelingRules/MyRule/
```
**Possible warnings**:
- "Field 'tags' has invalid value (empty)"
- "Expected string value for 'tags' field"

### After Fix
```bash
demisto-sdk validate -i Packs/TestPack/ModelingRules/MyRule/
```
**Expected**:
- ✅ No schema validation warnings
- ✅ All required fields present
- ✅ All field types correct

---

## Testing Checklist

- [ ] Apply tags field fix to ModelingRule (line 609)
- [ ] Apply tags field fix to AssetsModelingRule (line 705)
- [ ] Restart MCP server to reload code
- [ ] Create test ModelingRule: `create_modeling_rule(pack_name="TestPack", ...)`
- [ ] Create test AssetsModelingRule: `create_assets_modeling_rule(pack_name="TestPack", ...)`
- [ ] Run demisto-sdk validate on generated content
- [ ] Verify no validation errors
- [ ] Test upload to XSIAM (optional, may fail due to 101704 error)
- [ ] Update CLAUDE.md with results

---

## Implementation Status

| Content Type | Required Fields | Optional Fields | Tags Field | Upload Tested | Status |
|--------------|----------------|-----------------|------------|---------------|--------|
| ParsingRule | ✅ ALL | ⚠️ PARTIAL | ✅ CORRECT | ❌ Needs pack upload | ✅ COMPLIANT |
| ModelingRule | ✅ ALL | ⚠️ PARTIAL | ⚠️ **FIX NEEDED** | ❌ Needs pack upload | ⚠️ NEEDS FIX |
| AssetsModelingRule | ✅ ALL | ⚠️ PARTIAL | ⚠️ **FIX NEEDED** | ❌ Needs pack upload | ⚠️ NEEDS FIX |
| CaseLayout | ✅ ALL | ✅ ALL | N/A | ✅ Works | ✅ COMPLIANT |
| CaseField | ✅ ALL | ✅ ALL | N/A | ✅ Works | ✅ COMPLIANT |
| CaseLayoutRule | ✅ ALL | ✅ ALL | N/A | ❌ Needs pack upload | ✅ COMPLIANT |
| XSIAMDashboard | ✅ ALL | ✅ ALL | N/A | ❌ Needs pack upload | ✅ COMPLIANT |
| XSIAMReport | ✅ ALL | ✅ ALL | N/A | ❌ Needs pack upload | ✅ COMPLIANT |

---

## Conclusion

**Overall Assessment**: 🟢 Good
- 3/9 content types need minor fixes (tags field)
- All required fields correctly implemented
- Optional fields are truly optional
- No breaking issues

**Next Steps**:
1. Apply medium priority fix (tags field) - **2 minutes**
2. Test with demisto-sdk validate - **5 minutes**
3. Consider low priority enhancements - **future session**

**Risk**: Low - fixes are trivial and isolated
**Impact**: Medium - improves schema compliance and validation
