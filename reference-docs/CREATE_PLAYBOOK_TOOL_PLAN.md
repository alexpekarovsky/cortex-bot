# create_playbook MCP Tool - Implementation Plan

## Research Summary (Based on 22 Production Playbooks)

### Minimal Required Fields Per Task Type

#### Start Task:
```yaml
id, taskid, type: start, task: {id, version: -1, name: "", iscommand: false, brand: ""}
nexttasks, separatecontext: false, view, note: false, timertriggers: [], ignoreworker: false
```

#### Regular Task (Script/Command):
```yaml
id, taskid, type: regular, task: {id, version, name, description, scriptName OR script, type: regular, iscommand, brand}
nexttasks, scriptarguments, separatecontext, view, note, timertriggers, ignoreworker, skipunavailable
```

#### Condition Task:
```yaml
id, taskid, type: condition, task: {id, version, name, type: condition, iscommand: false, brand: ""}
nexttasks: {"#default#": [], "yes": []}, conditions, separatecontext, view, note, timertriggers, ignoreworker
```

#### Title Task:
```yaml
id, taskid, type: title, task: {id, version, name, type: title, iscommand: false, brand: ""}
nexttasks OR (none if last), separatecontext, view, note, timertriggers, ignoreworker
```

#### Sub-Playbook Task:
```yaml
id, taskid, type: playbook, task: {id, version, name, playbookName, type: playbook, iscommand: false, brand: ""}
nexttasks, scriptarguments, separatecontext: true, loop: {max: 100}, view, note, timertriggers, ignoreworker, skipunavailable
```

#### Collection Task (User Input):
```yaml
id, taskid, type: collection, task: {id, version, name, type: collection, iscommand: false, brand: ""}
nexttasks, message: {subject, body, replyOptions, timings}, form: {questions, title}, separatecontext, view, note, timertriggers, ignoreworker
```

---

## Tool Design: create_playbook

### Input Schema (Simplified):
```python
{
  "name": "MyPlaybook",
  "description": "Playbook description",
  "tasks": [
    {
      "id": "1",
      "type": "regular",
      "name": "Extract Indicators",
      "script": "extractIndicators",
      "arguments": {"text": "${File.Text}"},
      "next": ["2"]
    },
    {
      "id": "2",
      "type": "title",
      "name": "Done"
    }
  ]
}
```

### Output: Complete Valid YAML

Tool auto-generates:
- UUIDs for all tasks
- View positions (auto-calculated)
- All required fields (note, timertriggers, ignoreworker, etc.)
- Proper nexttasks linking
- contentitemexportablefields header
- inputs/outputs sections

---

## Implementation Approach

### Option A: YAML Template + Jinja2
Use templates for each task type, fill in with user data

### Option B: Python Dict Building
Build Python dict structure, yaml.dump() to file

### Option C: Copy Reference + Modify
Take working playbook, modify tasks programmatically

**Recommendation**: Option B (most flexible)

---

## Next Session TODO

1. Create `create_playbook.py` in custom_components
2. Implement task generators for each type
3. Add UUID generation
4. Add position calculation
5. Add validation
6. Test with ProcessCSVIndicators use case
7. Register as MCP tool

This will make playbook creation 10x easier!
