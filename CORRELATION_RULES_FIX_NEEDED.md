# Correlation Rules Tool - Critical Fixes Needed

## Current Issues

The tool at `src/usecase/custom_components/correlation_rules.py` is INCOMPLETE and will fail.

## Required Fixes

### 1. Fix Payload Structure

**Current (WRONG)**:
```python
payload = {
    "request_data": {
        "rules": [{...}]  # WRONG - extra nesting
    }
}
```

**Correct**:
```python
payload = {
    "request_data": [{...}]  # Direct array
}
```

### 2. Add ALL Required Fields

The payload MUST include:
```python
{
    "name": name,
    "severity": severity,
    "xql_query": xql_query,  # NOT "search_query"
    "is_enabled": is_enabled,
    "description": description,
    "alert_name": alert_name,
    "alert_category": alert_category,
    "alert_description": alert_description,  # REQUIRED
    "execution_mode": "SCHEDULED",  # MUST be SCHEDULED
    "search_window": search_window,
    "simple_schedule": schedule,  # REQUIRED
    "timezone": timezone,  # REQUIRED
    "crontab": crontab,  # REQUIRED
    "dataset": "alerts",  # MUST be "alerts"
    "action": "ALERTS",  # MUST be "ALERTS"
    "mapping_strategy": "CUSTOM",  # MUST be "CUSTOM"
    "suppression_enabled": suppression_enabled,
    "suppression_duration": suppression_duration,
    "suppression_fields": suppression_fields,
    "alert_fields": {  # REQUIRED object
        "agent_hostname": None,
        "action_local_ip": None,
        "action_remote_ip": None,
        # ... all 10 fields
    },
    "user_defined_severity": None,
    "user_defined_category": None,
    "mitre_defs": {},
    "investigation_query_link": "",
    "drilldown_query_timeframe": "ALERT"
}
```

### 3. Add Validation

```python
# Validate minimum search window
if "5 min" in search_window:
    search_window = "10 minutes"

# Only include rule_id for UPDATES
if rule_id is not None:
    payload["rule_id"] = rule_id
else:
    # NEW RULE - don't include rule_id
    pass
```

### 4. Update Function Signature

Add missing parameters:
- alert_description
- simple_schedule (defaults to search_window)
- timezone (default: "UTC")
- suppression_enabled (default: True)
- suppression_duration (default: "24 hours")
- suppression_fields (default: [])
- alert_field_mappings (default: all null)

## Next Session TODO

1. Update correlation_rules.py with correct payload structure
2. Add all required fields
3. Add validation for minimum 10 minutes
4. Test with a simple rule
5. Verify it works before documenting

**This is CRITICAL - the tool won't work until these fixes are applied!**
