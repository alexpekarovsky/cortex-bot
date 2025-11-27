# OpenAPI Schema Fixes Needed for Response Action Tools

Based on comprehensive testing of all 24 Cortex XSIAM MCP tools, 11 response action tools have schema mismatches between our OpenAPI YAML definitions and the actual Cortex XSIAM API requirements.

## Test Results Summary
- ✅ **9 tools working** (37.5%) - All investigation/query tools
- ❌ **4 tools API 500 errors** (16.7%) - XSIAM server-side issues
- 💥 **11 tools schema errors** (45.8%) - OpenAPI YAML fixes needed

## Tools Requiring Schema Fixes

### 1. get_action_status
**Error:** `group_action_id param is missing`
**Current Schema:** Expects `action_id` or `action_ids`
**Required Schema:** Needs `group_action_id` parameter
**File:** `src/usecase/custom_components/openapi/get_action_status.yaml`

### 2. quarantine_files
**Error:** `file_hash param is missing`
**Current Schema:** Has `file_path` but API also requires `file_hash`
**Required Schema:** Need both `file_path` AND `file_hash` parameters
**File:** `src/usecase/custom_components/openapi/quarantine_files.yaml`

### 3. run_script
**Error:** `script_uid param is missing`
**Current Schema:** Has `script_content`
**Required Schema:** Needs `script_uid` instead of or in addition to `script_content`
**File:** `src/usecase/custom_components/openapi/run_script.yaml`

### 4. isolate_endpoint
**Error:** `No endpoint was found / can't create group action id for ISOLATE`
**Issue:** Likely needs valid endpoint IDs that exist in the system
**Status:** May work with real endpoint IDs, needs validation
**File:** `src/usecase/custom_components/openapi/isolate_endpoint.yaml`

### 5. scan_endpoint
**Error:** `No endpoint was found / can't create group action id for SCAN`
**Issue:** Same as isolate_endpoint
**File:** `src/usecase/custom_components/openapi/scan_endpoint.yaml`

### 6. retrieve_files
**Error:** `No endpoint was found / can't create group action id for FILES_RETRIEVAL`
**Issue:** Same as isolate_endpoint
**File:** `src/usecase/custom_components/openapi/retrieve_files.yaml`

### 7. terminate_process
**Error:** `Internal Server Error` (500)
**Issue:** Schema may be incorrect or endpoint has issues
**File:** `src/usecase/custom_components/openapi/terminate_process.yaml`

### 8. terminate_causality
**Error:** `Field 'agent_id': Field required; Field 'causality_id': Field required`
**Current Schema:** Uses `filters` and `causality_group_hash`
**Required Schema:** Needs `agent_id` and `causality_id` instead
**File:** Need to create terminate_causality.yaml (currently missing from openapi/)

### 9. restore_file
**Error:** `No suitable agents found`
**Issue:** May need valid file_hash of previously quarantined file
**File:** Need to create restore_file.yaml (currently missing from openapi/)

### 10. add_indicator_rule
**Error:** `Internal Server Error` (500)
**Issue:** Schema may be incorrect
**File:** `src/usecase/custom_components/openapi/add_indicator_rule.yaml`

### 11. get_assessment_profile_results
**Error:** `Internal Server Error` (500)
**Issue:** May require additional license or wrong endpoint
**File:** `src/usecase/builtin_components/openapi/get_assessment_results.yaml`

## Known API Issues (Not Our Fault)
These tools consistently return HTTP 500 from the XSIAM API server:
1. **get_issues** - `/v1/issue/search` endpoint
2. **get_contributing_events** - `/public_api/v1/alerts/get_contributing_event/`
3. **update_issue** - `/v1/issue/{id}` endpoint
4. **get_assessment_profile_results** - May require additional licensing

## Action Plan

### Priority 1 - Fix Clear Parameter Mismatches
1. ✅ `get_action_status` - Change `action_id`/`action_ids` to `group_action_id`
2. ✅ `quarantine_files` - Add `file_hash` parameter requirement
3. ✅ `run_script` - Add `script_uid` parameter
4. ✅ `terminate_causality` - Change to use `agent_id` and `causality_id`

### Priority 2 - Create Missing YAML Files
1. Create `terminate_causality.yaml` with correct schema
2. Create `restore_file.yaml` with correct schema

### Priority 3 - Investigate & Fix
1. Check `add_indicator_rule.yaml` schema against API docs
2. Validate endpoint action tools work with real endpoint IDs
3. Determine if `get_assessment_profile_results` needs special license

### Priority 4 - Report to XSIAM Team
Report the 4 tools with persistent HTTP 500 errors to Palo Alto Networks support for investigation.

## Testing Strategy
After fixes:
1. Run comprehensive test again on all 24 tools
2. Target: 20/20 working tools (excluding 4 known API issues)
3. Success criteria: 100% for investigation tools + response actions

## Files Modified
- 11 OpenAPI YAML files in `src/usecase/custom_components/openapi/`
- 2 new YAML files to create
- Test results documented in HTML report

## References
- Official API Docs: https://docs-cortex.paloaltonetworks.com/r/Cortex-XSIAM-REST-API
- Test Report: `/Users/apekarovsky/projects/cortex-mcp/cortex-mcp-comprehensive-report.html`
- Error logs from comprehensive tool testing
