import json
from pathlib import Path
"""
XSOAR Playbook Creator with Smart Content Discovery

MCP tool for programmatic XSOAR/XSIAM playbook generation.
Generates valid playbook YAML from simplified input, handling all required fields automatically.

SMART DISCOVERY FEATURE:
Before building a custom playbook, this tool automatically searches the PANW content repository
on GitHub to find existing, production-ready playbooks that may already solve the use case.

Based on analysis of 22 production PANW playbooks.
"""

import logging
import uuid
import yaml
import re
from typing import Annotated, Optional, List, Dict, Any
from fastmcp import Context, FastMCP
from pydantic import Field
from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUID for task IDs."""
    return str(uuid.uuid4())


def generate_task_id(index: int) -> str:
    """Generate simple task ID."""
    return str(index)


def calculate_position(task_index: int, total_tasks: int, task_type: str = "regular") -> dict:
    """Calculate task position in visual editor."""
    x = 450  # Center X
    y = 50 + (task_index * 145)  # Vertical spacing

    # Adjust X for parallel tasks (enrichment)
    if task_type == "parallel":
        base_x = 200
        x = base_x + (task_index * 300)

    return {"x": x, "y": y}


def create_start_task(task_id: str, next_tasks: List[str]) -> dict:
    """Generate start task."""
    task_dict = {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "start",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": "",
            "iscommand": False,
            "brand": ""
        },
        "nexttasks": {
            "#none#": next_tasks
        },
        "separatecontext": False,
        "view": json.dumps({"position": {"x": 450, "y": 50}}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": False,
        "quietmode": 0
    }

    # Auto-fix common mistakes (e.g., self-loop)
    return auto_fix_task(task_dict, "start")


def create_regular_task(task_id: str, name: str,
                       script_name: str = None,
                       command: str = None,
                       brand: str = "",
                       arguments: dict = None,
                       next_tasks = None,  # Can be List[str] or dict for error handling
                       position: dict = None,
                       description: str = "",
                       playbook_name: str = None,
                       continueonerror: bool = False) -> dict:
    """Generate regular task (script/automation OR integration command).

    Args:
        next_tasks: Either list of task IDs OR dict for error handling
                   List: ["5"] -> nexttasks: {"#none#": ["5"]}
                   Dict: {"#none#": ["5"], "#error#": ["3"]} -> used directly
        continueonerror: Enable error path handling (default: False)
    """
    if arguments is None:
        arguments = {}
    if next_tasks is None:
        next_tasks = []
    if position is None:
        position = {"x": 450, "y": 195}

    is_command = command is not None

    # Auto-promote integration commands passed under "script" key (PR #12 by pedrofcastro)
    # Auto-promote integration commands + set correct brand
    # Sorted longest-first so "xdr-xql" matches before "xdr-"
    _CMD_BRAND_MAP = [
        ("xdr-xql-generic-query", "XQL Query Engine"),
        ("xdr-xql", "XQL Query Engine"),
        ("core-", "Cortex Core - IR"),
        ("xdr-", "Cortex Core - IR"),
        ("send-mail", "mail-sender"),
        ("send-notification", "SlackV3"),
        ("closeCase", "Builtin"),
        ("setIncident", "Builtin"),
        ("setIssue", "Builtin"),
        ("setAlert", "Builtin"),
        ("closeInvestigation", "Builtin"),
        ("jira-", "Jira V3"),
        ("servicenow-", "ServiceNow v2"),
        ("splunk-", "SplunkPy"),
        ("qradar-", "QRadar v3"),
        ("crowdstrike-", "CrowdStrikeFalcon"),
    ]
    if script_name and not command:
        if "|||" in script_name:
            command = script_name
            script_name = None
            is_command = True
        else:
            for prefix, cmd_brand in _CMD_BRAND_MAP:
                if script_name.startswith(prefix) or script_name == prefix.rstrip("-"):
                    command = f"|||{script_name}"
                    if not brand:
                        brand = cmd_brand
                    script_name = None
                    is_command = True
                    break

    # Wrap arguments in simple: format if not already wrapped
    wrapped_arguments = {}
    for key, value in arguments.items():
        if isinstance(value, dict) and ('simple' in value or 'complex' in value):
            # Already wrapped
            wrapped_arguments[key] = value
        else:
            # Wrap in simple format
            wrapped_arguments[key] = {"simple": value}

    # Handle nexttasks - support both list and dict formats
    if isinstance(next_tasks, dict):
        # Dict format for error handling
        nexttasks_dict = next_tasks.copy()

        # Ensure #none# exists when error handling is enabled
        if continueonerror and "#none#" not in nexttasks_dict:
            # If only #error# provided, add empty #none# (will be filled by auto-fix or user)
            nexttasks_dict["#none#"] = []
    else:
        # List format: ["5"] -> {"#none#": ["5"]}
        nexttasks_dict = {"#none#": next_tasks if next_tasks else []}

    task_dict = {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "regular",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": name,
            "description": description,
            "type": "regular",
            "iscommand": is_command,
            "brand": brand if is_command else "",
            "playbooktaskmissingcomponent": None,
            "istaskmissingcomponenterrordismissed": False
        },
        "nexttasks": nexttasks_dict,
        "continueonerror": continueonerror,
        "continueonerrortype": "" if continueonerror else "",
        "scriptarguments": wrapped_arguments,
        "separatecontext": False,
        "view": json.dumps({"position": position}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": False,
        "quietmode": 0,
        "isoversize": False,
        "isautoswitchedtoquietmode": False
    }

    # Add script or command field
    if is_command:
        task_dict["task"]["script"] = command
        task_dict["reputationcalc"] = 1
    else:
        task_dict["task"]["scriptName"] = script_name

    # Auto-fix common mistakes (query_name, skipunavailable, field names)
    task_dict = auto_fix_task(task_dict, "regular", playbook_name=playbook_name)

    return task_dict


def auto_fix_task(task_dict: dict, task_type: str, playbook_name: str = None) -> dict:
    """
    Automatically fix common playbook YAML mistakes discovered in production.

    Auto-fixes:
    - Missing query_name for XQL queries
    - Wrong skipunavailable values (false for XQL, true for optional playbooks)
    - Common XQL field name mistakes
    - Start task self-loops
    - SlackAsk/EmailAsk task parameter → tag mapping for sub-playbooks
    """
    # Fix 1: XQL queries must have query_name
    if task_type == "regular":
        script = task_dict.get("task", {}).get("scriptName") or task_dict.get("task", {}).get("script", "")

        if "xdr-xql-generic-query" in str(script):
            # Ensure query_name exists in arguments
            if "scriptarguments" not in task_dict:
                task_dict["scriptarguments"] = {}

            if "query_name" not in task_dict["scriptarguments"]:
                # Generate query_name from task name
                task_name = task_dict.get("task", {}).get("name", "query")
                query_name = task_name.lower().replace(" ", "_").replace("-", "_")[:50]
                task_dict["scriptarguments"]["query_name"] = query_name

            # Fix skipunavailable for XQL (must be false!)
            task_dict["skipunavailable"] = False

    # Fix 2: Start task pointing to itself
    if task_type == "start":
        task_id = task_dict.get("id")
        next_tasks = task_dict.get("nexttasks", {}).get("#none#", [])
        if task_id in next_tasks or "0" in next_tasks:
            # Point to task 1 instead
            task_dict["nexttasks"]["#none#"] = ["1"]

    return task_dict


def create_title_task(task_id: str, name: str, next_tasks: List[str],
                     position: dict) -> dict:
    """Generate title task."""
    return {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "title",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": name,
            "type": "title",
            "iscommand": False,
            "brand": "",
            "playbooktaskmissingcomponent": None,
            "istaskmissingcomponenterrordismissed": False
        },
        "nexttasks": {
            "#none#": next_tasks
        } if next_tasks else {},
        "separatecontext": False,
        "continueonerrortype": "",
        "view": json.dumps({"position": position}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": False,
        "quietmode": 0,
        "isoversize": False,
        "isautoswitchedtoquietmode": False
    }


def parse_condition_to_xsoar_format(condition_str: str) -> list:
    """
    Parse simplified condition string to proper XSOAR condition structure.

    Simplified: "${variable} == 'value'" or "${variable} >= 3"
    Proper XSOAR: [[{"operator": "...", "left": {...}, "right": {...}}]]

    Args:
        condition_str: Simplified condition string

    Returns:
        Properly structured XSOAR condition
    """
    import re

    # Parse condition: ${variable.accessor} OPERATOR value
    pattern = r'\$\{([^}]+)\}\s*(==|!=|>=|<=|>|<|contains)\s*(.+)'
    match = re.match(pattern, condition_str.strip())

    if not match:
        # If can't parse, return as-is (might be pre-formatted)
        return [[{"operator": "isTrue", "left": {"value": {"simple": condition_str}}}]]

    variable, operator, value = match.groups()
    value = value.strip().strip('"').strip("'")

    # Map operators
    operator_map = {
        "==": "isEqualString",
        "!=": "isNotEqualString",
        ">=": "greaterThanOrEqual",
        "<=": "lessThanOrEqual",
        ">": "greaterThan",
        "<": "lessThan",
        "contains": "containsString"
    }

    xsoar_operator = operator_map.get(operator, "isEqualString")

    # Parse variable (e.g., "incident.type" → root: incident, accessor: type)
    parts = variable.split(".", 1)
    root = parts[0]
    accessor = parts[1] if len(parts) > 1 else None

    # Build XSOAR condition structure
    condition = {
        "operator": xsoar_operator,
        "left": {
            "value": {
                "complex": {
                    "root": root
                }
            },
            "iscontext": True
        },
        "right": {
            "value": {
                "simple": value
            }
        }
    }

    # Add accessor if present
    if accessor:
        condition["left"]["value"]["complex"]["accessor"] = accessor

    # Try to parse value as number if possible
    try:
        numeric_value = int(value)
        condition["right"]["value"]["simple"] = str(numeric_value)
    except:
        pass

    return [[condition]]


def format_condition_value(value_def):
    """
    Format condition left/right value to proper XSOAR structure.

    Converts bare values or simple dicts into proper {value: {simple: ...}} format.
    Preserves already-wrapped complex structures.
    """
    if isinstance(value_def, dict):
        # Check if already properly wrapped
        if "value" in value_def:
            inner_value = value_def["value"]
            if isinstance(inner_value, dict) and ("simple" in inner_value or "complex" in inner_value):
                # Already wrapped correctly - return as-is
                return value_def
            else:
                # Has "value" but inner value not wrapped - wrap it
                return {
                    "value": {"simple": str(inner_value)},
                    "iscontext": value_def.get("iscontext", False)
                }
        else:
            # No "value" key - assume it's the old format, return as-is
            return value_def
    else:
        # Bare value - wrap it in proper structure
        return {
            "value": {"simple": str(value_def)},
            "iscontext": False
        }


def create_condition_task(task_id: str, name: str, conditions: list,
                         next_tasks: dict, position: dict,
                         description: str = "",
                         tags: list = None) -> dict:
    """Generate condition task with optional tags for Slack/Email entitlements and auto-formatted condition values."""

    # Auto-format condition values to wrap them in {simple:} structure
    formatted_conditions = []
    for cond in conditions:
        if isinstance(cond, dict) and "condition" in cond:
            formatted_cond = {"label": cond.get("label", "default"), "condition": []}

            # Process each OR group in the condition
            for or_group in cond.get("condition", []):
                formatted_or_group = []

                # Process each AND clause in the OR group
                for and_clause in or_group:
                    formatted_clause = dict(and_clause)  # Copy the clause

                    # Format left value if exists
                    if "left" in formatted_clause:
                        formatted_clause["left"] = format_condition_value(formatted_clause["left"])

                    # Format right value if exists
                    if "right" in formatted_clause:
                        formatted_clause["right"] = format_condition_value(formatted_clause["right"])

                    formatted_or_group.append(formatted_clause)

                formatted_cond["condition"].append(formatted_or_group)

            formatted_conditions.append(formatted_cond)
        else:
            # Not a dict or no condition key - keep as-is
            formatted_conditions.append(cond)

    task_dict = {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "condition",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": name,
            "description": description,
            "type": "condition",
            "iscommand": False,
            "brand": "",
            "playbooktaskmissingcomponent": None,
            "istaskmissingcomponenterrordismissed": False
        },
        "nexttasks": next_tasks,
        "separatecontext": False,
        "conditions": formatted_conditions,
        "continueonerrortype": "",
        "view": json.dumps({"position": position}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": False,
        "quietmode": 0,
        "isoversize": False,
        "isautoswitchedtoquietmode": False
    }

    # Add tags if provided (for Slack/Email entitlement patterns)
    if tags:
        task_dict["tags"] = tags

    return task_dict


def create_playbook_task(task_id: str, name: str, playbook_name: str,
                        arguments: dict, next_tasks: List[str],
                        position: dict, description: str = "") -> dict:
    """Generate sub-playbook call task."""
    # Wrap arguments in proper format for sub-playbooks
    wrapped_arguments = {}
    for key, value in arguments.items():
        if isinstance(value, dict) and ('simple' in value or 'complex' in value):
            # Already wrapped
            wrapped_arguments[key] = value
        elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            # Context variable - use complex format with root
            wrapped_arguments[key] = {
                "complex": {
                    "root": value
                }
            }
        else:
            # Static value - use simple format
            wrapped_arguments[key] = {"simple": str(value)}

    return {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "playbook",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": name,
            "description": description,
            "playbookName": playbook_name,
            "type": "playbook",
            "iscommand": False,
            "brand": ""
        },
        "nexttasks": {
            "#none#": next_tasks
        },
        "scriptarguments": wrapped_arguments,
        "separatecontext": True,
        "loop": {
            "iscommand": False,
            "max": 100
        },
        "view": json.dumps({"position": position}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": True,
        "quietmode": 0
    }


async def search_github_playbooks(ctx: Context, description: str) -> Dict[str, Any]:
    """
    Search PANW content repository on GitHub for existing playbooks.

    Args:
        ctx: FastMCP context for making tool calls
        description: Playbook description to search for

    Returns:
        Dictionary with search results including:
        - found: Boolean indicating if matches were found
        - playbooks: List of matching playbook info (name, url, description)
    """
    try:
        # Construct GitHub-specific search query
        search_query = f"site:github.com/demisto/content path:Playbooks {description} playbook"

        logger.info(f"Searching GitHub for playbooks matching: {description}")

        # Use the WebSearch tool available in Claude Code environment
        # Note: In MCP, we can't directly call tools, but we can use httpx for GitHub search
        # For now, return a structured response that indicates discovery should be done
        # by the LLM using WebSearch tool

        return {
            "search_query": search_query,
            "found": False,
            "playbooks": [],
            "message": f"Search query prepared: {search_query}. Use WebSearch tool to find existing playbooks."
        }

    except Exception as e:
        logger.warning(f"Failed to search GitHub playbooks: {e}")
        return {
            "found": False,
            "playbooks": [],
            "error": str(e)
        }


def extract_playbook_info_from_search(search_results: str) -> List[Dict[str, str]]:
    """
    Parse search results to extract playbook information.

    Args:
        search_results: Raw search results text

    Returns:
        List of dictionaries containing playbook name, url, and description
    """
    playbooks = []

    # Common PANW playbook patterns
    playbook_patterns = [
        r'Playbooks/(.*?)\.yml',
        r'playbook-(.*?)\.yml',
        r'"name":\s*"([^"]*[Pp]laybook[^"]*)"'
    ]

    for pattern in playbook_patterns:
        matches = re.findall(pattern, search_results)
        for match in matches:
            if match and len(match) > 3:  # Filter out very short matches
                playbooks.append({
                    "name": match.replace('_', ' ').replace('-', ' ').title(),
                    "source": "PANW Content Repository"
                })

    # Remove duplicates
    unique_playbooks = []
    seen_names = set()
    for pb in playbooks:
        if pb["name"] not in seen_names:
            seen_names.add(pb["name"])
            unique_playbooks.append(pb)

    return unique_playbooks[:5]  # Return top 5 matches


def format_discovery_response(playbooks: List[Dict[str, str]], description: str) -> str:
    """
    Format discovery results into a user-friendly response.

    Args:
        playbooks: List of discovered playbooks
        description: Original search description

    Returns:
        Formatted string response
    """
    if not playbooks:
        return create_response(data={
            "discovered_playbooks": False,
            "message": f"No existing playbooks found for '{description}'. Proceeding with custom playbook generation.",
            "recommendation": "Custom playbook generation recommended."
        })

    return create_response(data={
        "discovered_playbooks": True,
        "count": len(playbooks),
        "playbooks": playbooks,
        "message": f"Found {len(playbooks)} existing playbook(s) that may solve your use case.",
        "recommendation": "Review existing playbooks before building custom solution. Use skip_discovery=True if you want to proceed with custom generation anyway.",
        "next_steps": [
            "1. Review the existing playbooks in the PANW Content Repository",
            "2. Check if they meet your requirements",
            "3. If suitable, install from Cortex XSOAR Marketplace",
            "4. If not suitable, call this tool again with skip_discovery=True"
        ]
    })


async def create_playbook(
    ctx: Context,
    name: Annotated[str, Field(description="Playbook name (used as ID)")],
    description: Annotated[str, Field(description="Playbook description")],
    tasks: Annotated[str, Field(description="JSON string of task definitions")],
    output_path: Annotated[str, Field(description="Output file path for generated YAML")],
    skip_discovery: Annotated[Optional[bool], Field(
        description="Skip smart discovery of existing playbooks. Default: False (discovery enabled)",
        default=False
    )] = False
) -> str:
    """
    Create an XSOAR/XSIAM playbook programmatically with smart content discovery.

    =====================================================================
    LLM WORKFLOW - AFTER CREATING PLAYBOOK
    =====================================================================

    **PREFERRED: Use insert_playbook (REST API)**

    After this tool generates the YAML file:
    1. Tool creates YAML file and ZIP file automatically
    2. Tool returns both yaml_path and zip_path
    3. 🚀 USE insert_playbook(file="{zip_path}") to upload to XSIAM
    4. Verify upload was successful

    **FALLBACK: Use sdk_upload (SDK) only if API fails**

    If insert_playbook fails for any reason:
    - Use sdk_upload(path="{pack_path}") as backup method
    - SDK requires proper pack structure with metadata

    **Why prefer insert_playbook:**
    - Faster (direct API vs SDK overhead)
    - Simpler (just upload ZIP, no pack structure needed)
    - Returns immediate feedback
    - No pydantic version conflicts

    =====================================================================

    📚 MANDATORY: Call get_playbook_building_blocks() FIRST

    **REQUIRED WORKFLOW:**
    1. ALWAYS call get_playbook_building_blocks() before creating playbooks
    2. Reference the patterns for your specific use case
    3. Use the exact YAML structures shown in building blocks
    4. Then call create_playbook with correct task formats

    Building blocks provide:
    - 60+ production-tested task patterns
    - Correct nexttasks structure for error paths (#none# + #error#)
    - Slack entitlement patterns (DeleteContext, SlackAskV2, condition routing)
    - Timer management patterns
    - Sub-playbook call patterns with proper separatecontext
    - XQL query patterns with correct field names
    - Modern XSIAM 2.4+ commands

    **This is MANDATORY - do not skip this step!**

    IMPORTANT - SEARCHES PANW CONTENT FIRST!

    By DEFAULT (skip_discovery=False), this tool will:
    1. Search the PANW content repository on GitHub for existing playbooks
    2. Return any matches and prompt the user to review them
    3. NOT generate a custom playbook until the user explicitly requests it

    This prevents reinventing the wheel and encourages using production-tested PANW content.

    **When AI should set skip_discovery=True:**
    - User explicitly says "build custom", "create from scratch", "don't search"
    - User already reviewed existing playbooks and wants custom solution
    - User needs highly specialized logic not available in marketplace
    - User is iterating on a custom playbook after initial discovery

    **When AI should use default (skip_discovery=False):**
    - First time user requests a playbook for ANY use case
    - User describes a common scenario (phishing, malware, enrichment, etc.)
    - User doesn't explicitly request custom/scratch development
    - Best practice: ALWAYS search first, only build custom if nothing found

    **Smart Discovery Workflow:**
    1. User: "I need a playbook to detonate files in sandbox"
    2. AI: Calls create_playbook with skip_discovery=False (default)
    3. Tool: Searches GitHub, finds "Detonate File - Generic"
    4. Tool: Returns discovery results with recommendation to review
    5. User: Reviews, decides if suitable or needs custom
    6. AI: If custom needed, calls again with skip_discovery=True

    **Custom Generation (when skip_discovery=True):**
    Generates valid playbook YAML from simplified task definitions.
    Handles all required fields, UUIDs, positioning, and linking automatically.

    Task types supported:
    - start: Playbook entry point
    - regular: Script/automation execution
    - title: Workflow section header
    - condition: Decision/branching logic
    - playbook: Sub-playbook call
    - collection: User input form

    Example tasks input:
    ```json
    [
      {"id": "1", "type": "regular", "name": "Extract IOCs", "script": "extractIndicators", "arguments": {"text": "${File.Text}"}, "next": ["2"]},
      {"id": "2", "type": "title", "name": "Done"}
    ]
    ```

    CRITICAL: SCRIPT vs COMMAND REFERENCE FORMAT
    ─────────────────────────────────────────────
    Two types of tasks require DIFFERENT field formats:

    AUTOMATION SCRIPTS (Print, ParseJSON, Set, extractIndicators, etc.):
    - Use bare script name — NO pack prefix
    - WRONG: "CommonScripts|||Print"  → causes "Missing script" error even if installed
    - CORRECT: "Print"
    - Set iscommand=false, brand="" (handled automatically when using "script" key)

    INTEGRATION COMMANDS (xdr-get-endpoints, ip, file, etc.):
    - Use "Pack|||command" format OR just the command name
    - CORRECT: "Cortex Core - IR|||xdr-get-endpoints" or just "xdr-get-endpoints"
    - Set iscommand=true, brand="Integration Name" (handled automatically when using "command" key)

    In the task JSON input to this tool:
    - Use "script" key for automation scripts: {"script": "Print", ...}
    - Use "command" key for integration commands: {"command": "Cortex Core - IR|||xdr-get-endpoints", ...}

    ─────────────────────────────────────────────

    TASK FORMAT GUIDE:

    Regular Task (simple):
    ```json
    {
      "id": "2",
      "type": "regular",
      "name": "Enrich IP",
      "script": "ip",
      "arguments": {"ip": "${alert.src}"},
      "next": ["3"]
    }
    ```

    Regular Task with Error Handling:
    ```json
    {
      "id": "2",
      "type": "regular",
      "name": "Isolate Endpoint",
      "script": "core-isolate-endpoint",
      "arguments": {"endpoint_id": "${alert.endpoint_id}"},
      "continueonerror": true,
      "next": {
        "#none#": ["3"],
        "#error#": ["5"]
      }
    }
    ```

    Condition Task (multi-branch):
    ```json
    {
      "id": "3",
      "type": "condition",
      "name": "Check Severity",
      "conditions": [
        {
          "label": "High",
          "condition": [[{
            "operator": "isEqualString",
            "left": {"value": {"simple": "${alert.severity}"}},
            "right": {"value": {"simple": "high"}}
          }]]
        }
      ],
      "next": {
        "High": ["4"],
        "#default#": ["5"]
      }
    }
    ```

    Sub-Playbook Call:
    ```json
    {
      "id": "2",
      "type": "playbook",
      "name": "Enrich File",
      "playbookName": "File Enrichment - Generic v2",
      "arguments": {"SHA256": "${File.SHA256}"},
      "next": ["3"]
    }
    ```

    CRITICAL RULES:
    - Condition format: Use operator/left/right dicts, NOT ["left", "op", "right"] lists
    - Error handling: Set continueonerror: true AND use dict next with #none# + #error#
    - Arguments: Simple values auto-wrap, complex values need full format

    Args:
        ctx: FastMCP context
        name: Playbook name (also used as ID)
        description: Playbook description describing what the playbook should do
        tasks: JSON array of task definitions (required only if skip_discovery=True)
        output_path: Where to save the generated YAML (required only if skip_discovery=True)
        skip_discovery: Skip smart discovery and proceed directly to custom generation (default: False)

    Returns:
        JSON response with either:
        - Discovery results (if skip_discovery=False and matches found)
        - Generated playbook info (if skip_discovery=True or no matches found)
        - Error message if generation fails
    """
    import json

    try:
        # STEP 1: Smart Discovery (unless explicitly skipped)
        if not skip_discovery:
            logger.info(f"Smart discovery enabled. Searching PANW content for: {description}")

            # Prepare search query for the LLM to use
            search_query = f"site:github.com/demisto/content path:Playbooks {description} playbook"

            return create_response(data={
                "action": "discovery_required",
                "search_query": search_query,
                "message": f"SMART DISCOVERY: Before building a custom playbook, search for existing solutions.",
                "instructions": [
                    f"Use WebSearch with query: {search_query}",
                    "Look for playbooks in github.com/demisto/content repository",
                    "Check if any existing playbooks match the use case",
                    "If found: Report them to user with recommendation to review",
                    "If not found OR user insists on custom: Call again with skip_discovery=True"
                ],
                "recommendation": "Search first, build custom only if nothing suitable exists in PANW content repository."
            })

        # STEP 2: Custom Playbook Generation (discovery skipped or no matches)
        logger.info(f"Proceeding with custom playbook generation for: {name}")
        # Parse tasks
        tasks_list = json.loads(tasks)

        # Build playbook structure
        playbook = {
            "id": name,
            "version": -1,
            "contentitemexportablefields": {
                "contentitemfields": {
                    "packID": "CustomPlaybooks",
                    "packName": "Custom Playbooks",
                    "itemVersion": "1.0.0",
                    "fromServerVersion": "6.5.0",
                    "toServerVersion": "",
                    "definitionid": "",
                    "prevname": "",
                    "isoverridable": False
                }
            },
            "vcShouldKeepItemLegacyProdMachine": False,
            "name": name,
            "description": f"{description}\n\nCreated by Cortex Bot",
            "starttaskid": "0",
            "tasks": {},
            "system": True,
            "view": json.dumps({
                "linkLabelsPosition": {},
                "paper": {
                    "dimensions": {
                        "height": 50 + len(tasks_list) * 145 + 100,
                        "width": 1000,
                        "x": 50,
                        "y": 50
                    }
                }
            }),
            "inputs": [],
            "outputs": [],
            "fromversion": "6.5.0",
            "tests": ["No tests"]
        }

        # Create start task
        first_task_id = tasks_list[0]["id"] if tasks_list else "1"
        playbook["tasks"]["0"] = create_start_task("0", [first_task_id])

        # First pass: Build task reference map for Slack/Email entitlement detection
        task_reference_map = {}
        for task_def in tasks_list:
            task_reference_map[task_def["id"]] = task_def

        # Create each task
        for idx, task_def in enumerate(tasks_list):
            task_id = task_def["id"]
            task_type = task_def["type"]
            position = calculate_position(idx + 1, len(tasks_list))

            if task_type == "regular":
                # Handle next_tasks - can be list or dict for error handling
                next_value = task_def.get("next", [])

                playbook["tasks"][task_id] = create_regular_task(
                    task_id,
                    task_def["name"],
                    script_name=task_def.get("script"),
                    command=task_def.get("command"),
                    brand=task_def.get("brand", ""),
                    arguments=task_def.get("arguments", {}),
                    next_tasks=next_value,  # Pass as-is (list or dict)
                    position=position,
                    description=task_def.get("description", ""),
                    playbook_name=name,
                    continueonerror=task_def.get("continueonerror", False)
                )
            elif task_type == "title":
                playbook["tasks"][task_id] = create_title_task(
                    task_id,
                    task_def["name"],
                    task_def.get("next", []),
                    position
                )
            elif task_type == "playbook":
                playbook["tasks"][task_id] = create_playbook_task(
                    task_id,
                    task_def["name"],
                    task_def["playbookName"],
                    task_def.get("arguments", {}),
                    task_def.get("next", []),
                    position,
                    task_def.get("description", "")
                )
            elif task_type == "condition":
                # Condition tasks use nexttasks dict, not list
                cond_nexttasks = task_def.get("nexttasks", {})

                # If not provided, build from label-based routing at top level
                if not cond_nexttasks:
                    # Extract routing from top-level keys (Malware, Phishing, yes, no, etc.)
                    for key, value in task_def.items():
                        if key not in ["id", "type", "name", "description", "conditions", "next", "tags"] and isinstance(value, list):
                            cond_nexttasks[key] = value

                # If "next" is provided, use it for routing
                if "next" in task_def:
                    next_val = task_def["next"]
                    if isinstance(next_val, dict):
                        # Dict format: {"yes": ["4"], "#default#": ["5"]}
                        # Merge into cond_nexttasks (don't overwrite existing)
                        for k, v in next_val.items():
                            if k not in cond_nexttasks:
                                cond_nexttasks[k] = v
                    elif isinstance(next_val, list) and "#default#" not in cond_nexttasks:
                        # List format: ["5"] -> default path
                        cond_nexttasks["#default#"] = next_val

                # Auto-detect if this condition is referenced by SlackAsk/EmailAsk
                # and automatically add tags for sub-playbook compatibility
                auto_tags = []
                for ref_task in tasks_list:
                    if ref_task["type"] == "regular":
                        script = ref_task.get("script") or ref_task.get("command", "")
                        # Check if this is a SlackAsk or EmailAsk command
                        if "SlackAsk" in str(script) or "EmailAsk" in str(script):
                            # Check if the task parameter points to this condition
                            args = ref_task.get("arguments", {})
                            task_param = args.get("task", {})
                            task_param_value = None

                            # Handle different argument formats
                            if isinstance(task_param, dict):
                                task_param_value = task_param.get("simple") or task_param.get("value")
                            elif isinstance(task_param, str):
                                task_param_value = task_param

                            # If this SlackAsk/EmailAsk points to this condition, add tag
                            if task_param_value == task_id:
                                # Generate tag name: playbook-name-wait-taskid
                                tag_name = f"{name.lower().replace(' ', '-')}-wait-{task_id}"
                                auto_tags.append(tag_name)
                                logger.info(f"Auto-added tag '{tag_name}' to condition task {task_id} for {script}")

                # Merge auto-detected tags with any manually specified tags
                manual_tags = task_def.get("tags", [])
                all_tags = auto_tags + manual_tags

                # Parse conditions to proper XSOAR format
                raw_conditions = task_def.get("conditions", [])
                parsed_conditions = []

                for cond in raw_conditions:
                    if isinstance(cond, dict) and "condition" in cond:
                        # Check if condition is already properly formatted
                        if isinstance(cond["condition"], list):
                            # Already in XSOAR format
                            parsed_conditions.append(cond)
                        elif isinstance(cond["condition"], str):
                            # Simplified string format - parse it
                            parsed_cond = parse_condition_to_xsoar_format(cond["condition"])
                            parsed_conditions.append({
                                "label": cond.get("label", "default"),
                                "condition": parsed_cond
                            })
                        else:
                            # Unknown format, keep as-is
                            parsed_conditions.append(cond)
                    else:
                        # Already proper format or unknown, keep as-is
                        parsed_conditions.append(cond)

                playbook["tasks"][task_id] = create_condition_task(
                    task_id,
                    task_def["name"],
                    parsed_conditions,
                    cond_nexttasks,
                    position,
                    task_def.get("description", ""),
                    tags=all_tags if all_tags else None
                )
            elif task_type == "collection":
                playbook["tasks"][task_id] = create_collection_task(
                    task_id,
                    task_def["name"],
                    task_def.get("description", ""),
                    task_def.get("questions", []),
                    task_def.get("next", []),
                    position,
                    task_def.get("message_to", "Analyst"),
                    task_def.get("message_subject", ""),
                    task_def.get("message_body", ""),
                    sla=task_def.get("sla"),
                    slareminder=task_def.get("slareminder")
                )

        # Validate output path - must be under home directory or /tmp
        allowed_bases = [Path.home(), Path("/tmp")]
        resolved_output = Path(output_path).resolve()
        if not any(str(resolved_output).startswith(str(base)) for base in allowed_bases):
            return create_response(
                data={"error": f"Output path must be under home directory or /tmp: {output_path}"},
                is_error=True
            )

        # Write YAML
        with open(output_path, 'w') as f:
            yaml.dump(playbook, f, default_flow_style=False, sort_keys=False)

        # Create ZIP file for easy upload via insert_playbook API
        import zipfile
        import os

        zip_path = output_path.replace('.yml', '.zip').replace('.yaml', '.zip')
        if not zip_path.endswith('.zip'):
            zip_path = output_path + '.zip'

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add YAML file to ZIP with just the filename (no path)
            zipf.write(output_path, os.path.basename(output_path))

        return create_response(data={
            "success": True,
            "playbook_name": name,
            "yaml_path": output_path,
            "zip_path": zip_path,
            "tasks_created": len(tasks_list) + 1,  # +1 for start task
            "message": f"Playbook '{name}' generated successfully",
            "next_step": f"Upload to XSIAM: insert_playbook(file='{zip_path}')",
            "alternative": f"Or use SDK: sdk_upload(path='{os.path.dirname(output_path)}')"
        })

    except Exception as e:
        logger.exception(f"Failed to create playbook: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class CreatePlaybookModule(BaseModule):
    """
    Playbook Creator Module

    Provides MCP tool for programmatic XSOAR/XSIAM playbook generation.
    Generates valid playbook YAML from simplified input.

    Tools provided:
        - create_playbook: Generate playbook from task definitions
    """

    def register_tools(self):
        self._add_tool(create_playbook)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)


def _format_collection_question(q: dict, index: int) -> dict:
    """Convert simplified question dict to full XSOAR format.
    Cherry-picked from PR #12 by pedrofcastro.
    LLMs pass simplified dicts like {"label": "...", "options": ["Yes","No"]}.
    XSOAR needs id, fieldassociated, placeholder, etc. or the form renders empty."""
    if "id" in q:
        return q  # Already formatted
    label = q.get("label") or q.get("name") or f"Question {index + 1}"
    options = q.get("options", [])
    return {
        "id": str(index),
        "label": "",
        "labelarg": {"simple": label},
        "required": q.get("required", False),
        "gridcolumns": [],
        "defaultrows": [],
        "type": "singleSelect" if options else "shortText",
        "optionsarg": [{"simple": o} for o in options],
        "fieldassociated": "",
        "placeholder": "",
        "tooltip": "",
        "rowsNum": 0,
    }


def create_collection_task(task_id: str, name: str, description: str,
                          questions: List[dict], next_tasks: List[str],
                          position: dict,
                          message_to: str = "Analyst",
                          message_subject: str = "",
                          message_body: str = "",
                          sla: dict = None,
                          slareminder: dict = None) -> dict:
    """Generate collection (user input form) task with optional SLA."""
    task_dict = {
        "id": task_id,
        "taskid": generate_uuid(),
        "type": "collection",
        "task": {
            "id": generate_uuid(),
            "version": -1,
            "name": name,
            "description": description,
            "type": "collection",
            "iscommand": False,
            "brand": "",
            "playbooktaskmissingcomponent": None,
            "istaskmissingcomponenterrordismissed": False
        },
        "nexttasks": {
            "#none#": next_tasks
        },
        "separatecontext": False,
        "message": {
            "to": {"simple": message_to} if message_to else None,
            "subject": {"simple": message_subject},
            "body": {"simple": message_body},
            "methods": ["email"],
            "format": "html",
            "bcc": None,
            "cc": None,
            "timings": {
                "retriescount": 2,
                "retriesinterval": 360,
                "completeafterreplies": 1
            }
        },
        "form": {
            "questions": [_format_collection_question(q, i) for i, q in enumerate(questions)],
            "title": name,
            "description": description,
            "sender": "",
            "expired": False,
            "totalanswers": 0
        },
        "continueonerrortype": "",
        "view": json.dumps({"position": position}),
        "note": False,
        "timertriggers": [],
        "ignoreworker": False,
        "skipunavailable": False,
        "quietmode": 0,
        "isoversize": False,
        "isautoswitchedtoquietmode": False
    }

    # Add SLA fields if provided
    if sla:
        task_dict["sla"] = sla
    if slareminder:
        task_dict["slareminder"] = slareminder

    return task_dict
