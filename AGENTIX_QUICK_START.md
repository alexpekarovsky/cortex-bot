# AgentIX Quick Start Guide

Fast reference for creating AgentIX Actions and Agents.

---

## File Locations

```
Packs/MyPack/
├── AgentixActions/
│   └── ActionName.yml      # YAML, not JSON!
└── AgentixAgents/
    └── AgentName.yml        # YAML, not JSON!
```

**Critical**:
- Directory names are case-sensitive: `AgentixActions`, `AgentixAgents`
- File format is `.yml` (YAML), not `.json`

---

## AgentIX Action (Minimal)

```yaml
commonfields:
  id: MyAction               # Unique ID
  version: -1                # Always -1
name: MyAction
display: My Action Name      # Human-readable
description: What this action does.
underlyingcontentitem:
  id: script_or_command_id
  name: script_or_command_name
  type: command              # command, script, or playbook
  version: -1
  command: command_name      # Only for type=command
marketplaces:
  - platform                 # Required
supportedModules:
  - agentix                  # Required
```

---

## AgentIX Agent (Minimal)

```yaml
commonfields:
  id: MyAgent
  version: -1
name: My Agent
description: What this agent does.
color: "#3498DB"            # Hex color
visibility: public          # public or private
marketplaces:
  - platform
supportedModules:
  - agentix
```

---

## Common Fields Reference

### Action: Arguments

```yaml
args:
  - name: arg_name
    description: What this argument is for
    type: string              # string, number, boolean, array, date
    required: true
    underlyingargname: underlying_arg_name
```

### Action: Outputs

```yaml
outputs:
  - name: output_name
    description: What this output contains
    type: string
    underlyingoutputcontextpath: Context.Path.Here
```

### Agent: System Instructions

```yaml
systeminstructions: |-
  You are an expert in [domain].

  When helping users:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
```

### Agent: Actions

```yaml
actionids:
  - IPEnrichment
  - DomainEnrichment
  - FileHashEnrichment
```

### Agent: Conversation Starters

```yaml
conversationstarters:
  - "Example question 1"
  - "Example question 2"
  - "Example question 3"
```

---

## Underlying Content Types

### Type: command

```yaml
underlyingcontentitem:
  id: integration_id
  name: integration_name
  type: command
  version: -1
  command: command_name     # e.g., "ip", "domain", "file"
```

### Type: script

```yaml
underlyingcontentitem:
  id: ScriptID
  name: ScriptName
  type: script
  version: -1
```

### Type: playbook

```yaml
underlyingcontentitem:
  id: PlaybookID
  name: Playbook Name
  type: playbook
  version: -1
```

---

## Agent Colors (Hex Codes)

- Red: `#FF5733`, `#DC143C`
- Blue: `#3498DB`, `#1E90FF`
- Green: `#2ECC71`, `#228B22`
- Orange: `#FF8C00`, `#FFA500`
- Purple: `#9B59B6`, `#8A2BE2`
- Gray: `#95A5A6`, `#708090`

---

## Validation Checklist

- [ ] File in correct directory (`AgentixActions` or `AgentixAgents`)
- [ ] File is `.yml` format (YAML)
- [ ] `commonfields.id` is unique
- [ ] `commonfields.version` is `-1`
- [ ] `marketplaces: ["platform"]` included
- [ ] `supportedModules: ["agentix"]` included
- [ ] For Actions: `underlyingcontentitem` references valid content
- [ ] For Agents: `color` and `visibility` fields present
- [ ] Valid argument/output types (string, number, boolean, array, date)

---

## Common Mistakes

**Wrong directory name**: ~~`AgentIXActions`~~ → `AgentixActions`
**Wrong file format**: ~~`.json`~~ → `.yml`
**Missing marketplace**: Must include `platform`
**Missing module**: Must include `agentix`
**Wrong version**: Use `-1`, not `1` or other numbers
**Invalid color**: Use hex codes like `#3498DB`, not color names

---

## Testing

```bash
# Validate YAML syntax
yamllint Packs/MyPack/AgentixActions/MyAction.yml

# Validate with demisto-sdk
demisto-sdk validate -i Packs/MyPack/AgentixActions/MyAction.yml

# Upload to XSIAM
demisto-sdk upload -i Packs/MyPack
```

---

## Full Examples

See `AGENTIX_REFERENCE.md` for complete examples including:
- IP enrichment action
- Script-based action
- Playbook-based action
- SOC analyst agent with full system instructions

---

**Quick Reference Complete** - See AGENTIX_REFERENCE.md for detailed documentation.
