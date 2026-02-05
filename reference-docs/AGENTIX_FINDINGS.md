# AgentIX Research Findings

Research conducted on January 3, 2026 to understand AgentIX content types for MCP tool development.

---

## Executive Summary

**Goal**: Create MCP tools `create_agentix_action` and `create_agentix_agent` for programmatic XSIAM content generation.

**Key Findings**:
1. AgentIX uses **YAML format** (`.yml`), not JSON
2. Files are stored in **case-sensitive directories**: `AgentixActions/` and `AgentixAgents/`
3. Both content types have well-defined schemas with required and optional fields
4. Working examples found in demisto-sdk TestSuite
5. Complete schema documentation extracted from source code

---

## Data Sources

### Primary Sources
1. **Schema Files**:
   - `/tmp/demisto-sdk/demisto_sdk/commands/common/schemas/agentixaction.yml`
   - `/tmp/demisto-sdk/demisto_sdk/commands/common/schemas/agentixagent.yml`

2. **Working Examples**:
   - `/tmp/demisto-sdk/TestSuite/assets/default_agentix_action/agentix_action-sample.yml`
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/tests/test_data/agentix_action.yml`

3. **Parser Code**:
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/parsers/agentix_action.py`
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/parsers/agentix_agent.py`
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/parsers/agentix_base.py`

4. **Test Code**:
   - `/tmp/demisto-sdk/demisto_sdk/commands/validate/tests/AG_validators_test.py`

5. **Object Models**:
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/objects/agentix_action.py`
   - `/tmp/demisto-sdk/demisto_sdk/commands/content_graph/objects/agentix_agent.py`

---

## Critical Discoveries

### 1. File Format is YAML, Not JSON

**Finding**: Despite other XSIAM content using JSON (CaseFields, CaseLayouts, etc.), AgentIX content uses YAML format.

**Evidence**:
- Schema files are `.yml`
- Test examples are `.yml`
- Parser looks for `.yml` suffix: `path.suffix == ".yml"`
- Base parser extends `YAMLContentItemParser`

**Implication**: MCP tools must generate YAML, not JSON.

---

### 2. Directory Names are Case-Sensitive

**Finding**: Exact capitalization required for directory names.

**Correct**:
- `AgentixActions/`
- `AgentixAgents/`

**Incorrect**:
- ~~`AgentIXActions/`~~
- ~~`agentixactions/`~~
- ~~`AgentIxActions/`~~

**Evidence**: Constants defined in `demisto_sdk/commands/common/constants.py`:
```python
AGENTIX_ACTIONS_DIR = "AgentixActions"
AGENTIX_AGENTS_DIR = "AgentixAgents"
```

---

### 3. AgentIX Action Structure

**Required Fields**:
```yaml
commonfields:
  id: string          # Unique identifier
  version: -1         # Always -1 (auto-incremented)
name: string          # Internal name
display: string       # Display name
description: string   # Description
underlyingcontentitem:
  id: string
  name: string
  type: string        # "command", "script", or "playbook"
  version: -1
  command: string     # Only for type="command"
marketplaces: ["platform"]
supportedModules: ["agentix"]
```

**Optional Fields**:
- `category`: Category for organization
- `tags`: Array of tags
- `args`: Array of argument definitions
- `outputs`: Array of output definitions
- `requiresuserapproval`: Boolean (default: false)
- `fewshots`: Array of example prompts

---

### 4. AgentIX Agent Structure

**Required Fields**:
```yaml
commonfields:
  id: string
  version: -1
name: string
description: string
color: string         # Hex color code
visibility: string    # "public" or "private"
marketplaces: ["platform"]
supportedModules: ["agentix"]
```

**Optional Fields**:
- `category`: Category
- `tags`: Array of tags
- `actionids`: Array of AgentIX Action IDs
- `systeminstructions`: System prompt text
- `conversationstarters`: Array of conversation starters
- `builtinactions`: Array of built-in action names
- `autoenablenewactions`: Boolean (default: false)
- `roles`: Array of role names
- `sharedwithroles`: Array of role names

---

### 5. Argument Schema (for Actions)

```yaml
args:
  - name: string              # Required
    description: string       # Required
    type: string             # Required: string, number, boolean, array, date
    required: boolean        # Required
    underlyingargname: string # Required: maps to underlying command arg
    defaultvalue: string     # Optional
    hidden: boolean          # Optional (default: false)
    disabled: boolean        # Optional (default: false)
    isgeneratable: boolean   # Optional (default: false)
```

**Evidence**: Schema from `agentixaction.yml` and `AgentixActionArgument` model.

---

### 6. Output Schema (for Actions)

```yaml
outputs:
  - name: string                        # Required
    description: string                 # Required
    type: string                       # Required
    underlyingoutputcontextpath: string # Required: maps to underlying output
    disabled: boolean                   # Optional (default: false)
```

**Evidence**: Schema from `agentixaction.yml` and `AgentixActionOutput` model.

---

### 7. Underlying Content Item Types

**Supported Types**:
1. `command`: Integration commands (e.g., `!ip`, `!domain`, `!cve`)
2. `script`: Automation scripts
3. `playbook`: Playbooks

**Type-Specific Fields**:
- For `command`: Must include `command` field with command name
- For `script`: Uses script ID
- For `playbook`: Uses playbook ID

**Evidence**: Parser code in `agentix_action.py` lines 68-83 shows type handling.

---

### 8. Validation Rules

Based on validator code in `AG_validators_test.py`:

1. **AG100**: AgentIX content should not be uploaded through content repo (use content-test-conf)
2. **AG101**: Marketplace must be "platform"
3. **AG105**: Argument and output types must be valid
4. **AG106**: Action names must follow naming conventions
5. **AG107**: Display names must be human-readable
6. **GR110**: Underlying content item must exist
7. **GR111**: Display names must be unique across all packs
8. **GR112**: Action names must be unique across all packs

---

### 9. Marketplace and Module Requirements

**Required Values**:
```yaml
marketplaces:
  - platform        # Must be "platform"
supportedModules:
  - agentix         # Must be "agentix"
```

**Other marketplace values are invalid** (will fail validation).

**Evidence**: Validator `IsCorrectMPValidator` in test code.

---

### 10. Version Convention

**Convention**: Use `-1` for version fields.

**Reasoning**: XSIAM auto-increments versions on upload. Using `-1` signals "use next version".

**Applies To**:
- `commonfields.version`
- `underlyingcontentitem.version`

**Evidence**: All examples use `-1` for versions.

---

## Working Example Analysis

### Example: CVE Enrichment Action

From `/tmp/demisto-sdk/TestSuite/assets/default_agentix_action/agentix_action-sample.yml`:

**Structure**:
- 62 lines total
- Uses multiline description (with `|-`)
- 7 arguments defined
- 7 outputs defined
- Maps to `cve` command from integration
- Includes comprehensive tags
- Category: "Data Enrichment & Threat Intelligence"

**Key Observations**:
1. Arguments map 1:1 to underlying command args via `underlyingargname`
2. Outputs map to context paths via `underlyingoutputcontextpath`
3. All required fields present
4. Follows YAML best practices (multiline strings, consistent indentation)

---

## Test Agent Example

From `/tmp/demisto-sdk/demisto_sdk/commands/validate/tests/AG_validators_test.py`:

**Minimal Agent**:
```python
AgentixAgent(
    color="red",
    visibility="public",
    actionids=["test_action"],
    systeminstructions="Test system instructions",
    conversationstarters=["Test conversation starter"],
    autoenablenewactions=False,
    description="",
    display="display Name",
    path=Path("test.yml"),
    marketplaces=["platform"],
    name="test",
    # ... other fields ...
)
```

**Observations**:
- Color can be simple names in code, but hex recommended for YAML
- Visibility is string, not boolean
- Action IDs reference other AgentIX Actions
- System instructions are freeform text

---

## Comparison with Other XSIAM Content Types

| Aspect | AgentIX | CaseFields/Layouts | Correlation Rules |
|--------|---------|-------------------|-------------------|
| Format | YAML | JSON | API payload |
| Directory | `AgentixActions/`, `AgentixAgents/` | `CaseFields/`, `CaseLayouts/` | N/A |
| Upload | demisto-sdk | Direct API / SDK | Direct API |
| Marketplace | `platform` | `marketplacev2` | N/A |
| Module | `agentix` | N/A | N/A |
| Version | `-1` | `-1` | N/A |

**Key Difference**: AgentIX is the only XSIAM content type using YAML format (not JSON).

---

## MCP Tool Design Recommendations

### Tool: create_agentix_action

**Parameters**:
```python
def create_agentix_action(
    pack_name: str,
    action_name: str,
    display_name: str,
    description: str,
    underlying_type: str,  # "command", "script", "playbook"
    underlying_id: str,
    underlying_name: str,
    underlying_command: Optional[str] = None,  # Required for type=command
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    args: Optional[str] = None,  # JSON string
    outputs: Optional[str] = None,  # JSON string
    requires_approval: bool = False,
    fewshots: Optional[List[str]] = None,
    upload: bool = False
) -> dict:
```

**Implementation**:
1. Create YAML structure using `ruamel.yaml` (preserves formatting)
2. Validate required fields
3. Save to `Packs/{pack_name}/AgentixActions/{action_name}.yml`
4. Optionally upload via `demisto-sdk upload`

**Example Usage**:
```python
create_agentix_action(
    pack_name="ThreatIntel",
    action_name="CVEEnrichment",
    display_name="CVE Enrichment",
    description="Enriches CVE identifiers",
    underlying_type="command",
    underlying_id="CVE",
    underlying_name="cve",
    underlying_command="cve",
    category="Data Enrichment & Threat Intelligence",
    tags=["cve", "vulnerability"]
)
```

---

### Tool: create_agentix_agent

**Parameters**:
```python
def create_agentix_agent(
    pack_name: str,
    agent_name: str,
    description: str,
    color: str,
    visibility: str = "public",
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    action_ids: Optional[List[str]] = None,
    system_instructions: Optional[str] = None,
    conversation_starters: Optional[List[str]] = None,
    builtin_actions: Optional[List[str]] = None,
    auto_enable_new_actions: bool = False,
    roles: Optional[List[str]] = None,
    shared_with_roles: Optional[List[str]] = None,
    upload: bool = False
) -> dict:
```

**Implementation**:
1. Create YAML structure
2. Validate color format (hex code)
3. Validate visibility ("public" or "private")
4. Save to `Packs/{pack_name}/AgentixAgents/{agent_name}.yml`
5. Optionally upload via `demisto-sdk upload`

**Example Usage**:
```python
create_agentix_agent(
    pack_name="SOC",
    agent_name="ThreatHunter",
    description="AI threat hunting assistant",
    color="#3498DB",
    visibility="public",
    action_ids=["CVEEnrichment", "IPEnrichment"],
    system_instructions="You are a senior threat hunter...",
    conversation_starters=["Investigate this IP", "What CVEs should I patch?"]
)
```

---

## Implementation Checklist

### create_agentix_action Tool

- [ ] Parse action parameters
- [ ] Validate underlying content type ("command", "script", "playbook")
- [ ] Generate YAML structure with all required fields
- [ ] Parse args JSON string if provided
- [ ] Parse outputs JSON string if provided
- [ ] Set default values (version=-1, marketplaces=["platform"], etc.)
- [ ] Create pack directory structure if needed
- [ ] Save to `Packs/{PackName}/AgentixActions/{ActionName}.yml`
- [ ] Optionally validate with demisto-sdk
- [ ] Optionally upload with demisto-sdk
- [ ] Return success response with file path

### create_agentix_agent Tool

- [ ] Parse agent parameters
- [ ] Validate color format (hex code starting with #)
- [ ] Validate visibility ("public" or "private")
- [ ] Generate YAML structure with all required fields
- [ ] Set default values (version=-1, marketplaces=["platform"], etc.)
- [ ] Create pack directory structure if needed
- [ ] Save to `Packs/{PackName}/AgentixAgents/{AgentName}.yml`
- [ ] Optionally validate with demisto-sdk
- [ ] Optionally upload with demisto-sdk
- [ ] Return success response with file path

---

## Next Steps

1. **Create MCP tools** using the specifications above
2. **Test with real examples** from AGENTIX_REFERENCE.md
3. **Add to XSIAM content guide** explaining AgentIX alongside other content types
4. **Update tool count** in CLAUDE.md (from 78 to 80 tools)
5. **Document in README.md** under XSIAM content generation section

---

## References

- Full documentation: `AGENTIX_REFERENCE.md`
- Quick start guide: `AGENTIX_QUICK_START.md`
- This findings document: `AGENTIX_FINDINGS.md`

---

**Research Complete** - Ready for MCP tool implementation.
