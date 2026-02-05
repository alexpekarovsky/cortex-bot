# XSIAM Terminology - FINAL CORRECT VERSION

## 🔴 THE TRUTH: XSIAM Modern Terminology

### What We Say AND What We Code:

**Individual Security Event:**
- Human: "**Issue**"
- YAML: `${issue.*}` 
- API: `/issue/`
- Command: `setIssue` (if exists, or maybe still `setAlert` for compatibility)

**Parent Collection:**
- Human: "**Case**"  
- YAML: `${case.*}` or parent context
- API: `/case/`
- Command: `closeInvestigation` (closes the case)

---

## Corrected Everywhere

### Old Playbooks (Legacy):
```yaml
# OLD - What the example playbooks use
${alert.id}           # Legacy
${alert.severity}     # Legacy
Builtin|||setAlert    # Legacy compatibility
```

### Modern XSIAM (What We Should Use):
```yaml
# NEW - Modern XSIAM
${issue.id}           # Correct
${issue.severity}     # Correct
Builtin|||setIssue    # Modern (or setAlert for compatibility)
${case.id}            # Parent case
```

---

## Building Block Examples (CORRECTED):

### Update Issue Severity:
```yaml
type: regular
script: Builtin|||setIssue  # or setAlert for compatibility
scriptarguments:
  severity: "3"
  customFields:
    investigationstatus: "Investigating"
description: "Update issue severity and investigation status"
```

### Close Case:
```yaml
type: regular
script: '|||closeInvestigation'
scriptarguments:
  closeReason: "Resolved - False Positive"
  closeNotes: "Issue ${issue.id} determined false positive. Case closed."
description: "Close case with documentation"
```

### Reference Issue Data:
```yaml
scriptarguments:
  endpoint_id:
    simple: ${issue.agentid}
  file_hash:
    simple: ${issue.filesha256}
  severity:
    simple: ${issue.severity}
```

---

## Summary Table

| What It Is | Say (Human) | Code (YAML) | API Endpoint | Old Name |
|------------|-------------|-------------|--------------|----------|
| Individual event | Issue | `${issue.*}` | `/issue/` | alert |
| Collection | Case | `${case.*}` | `/case/` | incident |
| Update event | Update issue | `setIssue` or `setAlert` | PATCH /issue/ | setAlert |
| Close collection | Close case | `closeInvestigation` | POST /case/close | closeInvestigation |

---

**Use "issue" everywhere - replace all instances of "alert"!**
