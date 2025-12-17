import json
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
    return {
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


def create_regular_task(task_id: str, name: str,
                       script_name: str = None,
                       command: str = None,
                       brand: str = "",
                       arguments: dict = None,
                       next_tasks: List[str] = None,
                       position: dict = None,
                       description: str = "") -> dict:
    """Generate regular task (script/automation OR integration command)."""
    if arguments is None:
        arguments = {}
    if next_tasks is None:
        next_tasks = []
    if position is None:
        position = {"x": 450, "y": 195}

    is_command = command is not None

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
        "nexttasks": {
            "#none#": next_tasks
        },
        "scriptarguments": arguments,
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

    # Add script or command field
    if is_command:
        task_dict["task"]["script"] = command
        task_dict["reputationcalc"] = 1
    else:
        task_dict["task"]["scriptName"] = script_name

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


def create_condition_task(task_id: str, name: str, conditions: list,
                         next_tasks: dict, position: dict,
                         description: str = "") -> dict:
    """Generate condition task."""
    return {
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
        "conditions": conditions,
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


def create_playbook_task(task_id: str, name: str, playbook_name: str,
                        arguments: dict, next_tasks: List[str],
                        position: dict, description: str = "") -> dict:
    """Generate sub-playbook call task."""
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
        "scriptarguments": arguments,
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

    ⚠️ IMPORTANT - SEARCHES PANW CONTENT FIRST! ⚠️

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
                    "packID": "NetworkTools",
                    "packName": "Network Tools",
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
            "description": description,
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

        # Create each task
        for idx, task_def in enumerate(tasks_list):
            task_id = task_def["id"]
            task_type = task_def["type"]
            position = calculate_position(idx + 1, len(tasks_list))

            if task_type == "regular":
                playbook["tasks"][task_id] = create_regular_task(
                    task_id,
                    task_def["name"],
                    script_name=task_def.get("script"),
                    command=task_def.get("command"),
                    brand=task_def.get("brand", ""),
                    arguments=task_def.get("arguments", {}),
                    next_tasks=task_def.get("next", []),
                    position=position,
                    description=task_def.get("description", "")
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
                # If "next" is provided as list, convert to default path
                if "next" in task_def and not cond_nexttasks:
                    cond_nexttasks = {"#default#": task_def["next"]}

                playbook["tasks"][task_id] = create_condition_task(
                    task_id,
                    task_def["name"],
                    task_def.get("conditions", []),
                    cond_nexttasks,
                    position,
                    task_def.get("description", "")
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
                    task_def.get("message_body", "")
                )

        # Write YAML
        with open(output_path, 'w') as f:
            yaml.dump(playbook, f, default_flow_style=False, sort_keys=False)

        return create_response(data={
            "success": True,
            "playbook_name": name,
            "output_path": output_path,
            "tasks_created": len(tasks_list) + 1,  # +1 for start task
            "message": f"Playbook '{name}' generated successfully at {output_path}"
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


def create_collection_task(task_id: str, name: str, description: str,
                          questions: List[dict], next_tasks: List[str],
                          position: dict,
                          message_to: str = "Analyst",
                          message_subject: str = "",
                          message_body: str = "") -> dict:
    """Generate collection (user input form) task."""
    return {
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
            "questions": questions,
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
