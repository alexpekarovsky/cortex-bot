"""
XSOAR Playbook Runner Tool

Runs a playbook on a specified issue using the !setPlaybook command.
Handles the common workflow of either using an existing issue or creating a new one.
"""

import asyncio
import logging
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


def _get_ui_url_from_api_url(api_url: str) -> str:
    """
    Derives the XSIAM UI URL from the API URL.

    API URL format: https://api-{tenant}.xdr.{region}.paloaltonetworks.com
    UI URL format:  https://{tenant}.xdr.{region}.paloaltonetworks.com

    Args:
        api_url: The API URL (e.g., https://api-cortexxsiam.xdr.il.paloaltonetworks.com)

    Returns:
        The UI URL (e.g., https://cortexxsiam.xdr.il.paloaltonetworks.com)
    """
    # Remove "api-" from the URL
    if "://api-" in api_url:
        return api_url.replace("://api-", "://")
    return api_url


def _build_issue_url(base_ui_url: str, issue_id: str) -> str:
    """
    Builds the URL to open an issue in XSIAM UI.

    Args:
        base_ui_url: The base UI URL
        issue_id: The numeric issue ID

    Returns:
        Full URL to open the issue
    """
    return f"{base_ui_url}/alerts?action:openAlertDetails={issue_id}"


async def _create_playbook_test_issue(ctx: Context, playbook_name: str) -> dict:
    """
    Creates a new issue for playbook testing.

    Args:
        ctx: FastMCP context
        playbook_name: Name of playbook (used in issue name)

    Returns:
        Dict with issue details including numeric ID
    """
    import time

    fetcher = await get_fetcher(ctx)
    timestamp = int(time.time() * 1000)

    issue_payload = {
        "name": f"Playbook Test - {playbook_name}",
        "description": f"Test workspace for running playbook: {playbook_name}",
        "observation_time": timestamp,
        "domain": "SECURITY",
        "category": "THREAT_INTELLIGENCE",
        "severity": "MEDIUM",  # MEDIUM+ creates a Case with War Room
        "tags": ["playbook-test", "ai-workspace"],
        "is_excluded": False,
        "is_starred": False,
        "type": "AI Workspace",
        "extended_description": f"Created to test playbook: {playbook_name}",
        "custom_fields": {}
    }

    response = await fetcher.send_request(
        path="/public_api/v1/issue",
        method="POST",
        data={"request_data": {"issue": issue_payload}}
    )

    if isinstance(response, dict):
        reply = response.get("reply", response)
        external_id = reply.get("external_id")

        # Wait for indexing and get numeric ID
        await asyncio.sleep(3)

        issues_response = await fetcher.send_request(
            path="/public_api/v1/issues",
            method="POST",
            data={
                "request_data": {
                    "filters": [
                        {"field": "external_id", "operator": "in", "value": [external_id]}
                    ],
                    "search_from": 0,
                    "search_to": 1
                }
            }
        )

        if isinstance(issues_response, dict):
            issues = issues_response.get("reply", {}).get("DATA", [])
            if issues:
                issue = issues[0]
                return {
                    "issue_id": str(issue.get("id")),
                    "external_id": external_id,
                    "name": issue_payload["name"],
                    "severity": issue_payload["severity"]
                }

    return {"external_id": external_id, "error": "Could not get numeric issue ID"}


async def run_playbook(
    ctx: Context,
    playbook_name: Annotated[str, Field(description="Name of the playbook to run (e.g., 'Mission 05 - Team Escalation')")],
    issue_id: Annotated[Optional[str], Field(description="Issue/Alert ID to run playbook on (e.g., '4099'). If not provided, will create a new issue.")] = None,
    create_new_issue: Annotated[bool, Field(description="If True and no issue_id provided, creates a new test issue. Default: True")] = True,
    wait_for_investigation: Annotated[bool, Field(description="If True, waits and retries if investigation not ready. Default: True")] = True,
    max_retries: Annotated[int, Field(description="Maximum retries if investigation not ready. Default: 3")] = 3,
) -> str:
    """
    Runs an XSOAR playbook on an issue using the !setPlaybook command.

    =====================================================================
    IMPORTANT WORKFLOW FOR NEW ISSUES
    =====================================================================

    **CRITICAL: When creating a new issue (no issue_id provided), follow this exact sequence:**

    1. Call run_playbook(playbook_name="X") - Tool creates issue
    2. Tool returns issue_url and issue_id
    3. STOP - Playbook has NOT started yet!
    4. TELL THE USER: "I created issue {issue_id}. Please open this URL to activate the investigation: {issue_url}"
    5. WAIT for user to confirm they opened the link
    6. RETRY: run_playbook(playbook_name="X", issue_id="{issue_id}")
    7. Now playbook runs successfully

    **WHY THIS MATTERS:**
    XSIAM requires a human to open the issue in the UI before the War Room
    investigation becomes active. Without an active investigation, !setPlaybook
    will fail with "Could not find investigation" error.

    **DO NOT:**
    - Assume playbook started after creating issue
    - Skip telling user to open the URL
    - Continue without user confirmation

    =====================================================================
    HOW TO USE THIS TOOL
    =====================================================================

    **OPTION 1: Run on existing issue** RECOMMENDED
    ─────────────────────────────────────────────────────────────────────
    When: Issue already exists and was opened by a human

    run_playbook(playbook_name="My Playbook", issue_id="4099")

    Result: Playbook starts immediately (War Room already active)

    **OPTION 2: Create new issue** REQUIRES USER ACTION
    ─────────────────────────────────────────────────────────────────────
    When: Testing a playbook or no existing issue available

    Step 1: run_playbook(playbook_name="My Playbook")  # No issue_id
    Step 2: Tell user to click the returned issue_url
    Step 3: Wait for user confirmation
    Step 4: run_playbook(playbook_name="My Playbook", issue_id="{returned_id}")

    =====================================================================
    EXAMPLES
    =====================================================================

    Example 1 - Existing Issue (one step):
    >>> run_playbook(playbook_name="Phishing Investigation", issue_id="6543")
    {"success": True, "message": "Playbook started", ...}

    Example 2 - New Issue (two steps with user action):
    >>> result = run_playbook(playbook_name="File Investigation")
    # Returns: {"issue_id": "6544", "issue_url": "https://...",
    #           "user_action_required": "...", "next_step": "..."}

    🗣️ LLM MUST say: "I created issue 6544. Please open: {issue_url}"
    ⏸️ LLM MUST wait for user to confirm

    >>> run_playbook(playbook_name="File Investigation", issue_id="6544")
    {"success": True, "message": "Playbook started", ...}

    =====================================================================

    Args:
        ctx: The FastMCP context.
        playbook_name: Exact name of the playbook to run.
        issue_id: Issue/Alert ID to run on (optional).
        create_new_issue: Auto-create test issue if no issue_id provided.
        wait_for_investigation: Retry if investigation not ready.
        max_retries: Max retry attempts.

    Returns:
        JSON with execution status, issue URL, and any errors.
    """

    fetcher = await get_fetcher(ctx)

    # Get the UI URL from the API URL dynamically
    ui_base_url = _get_ui_url_from_api_url(fetcher.url)

    investigation_id = None
    issue_url = None
    created_issue = None

    # Determine which investigation to use
    if issue_id:
        investigation_id = issue_id
        issue_url = _build_issue_url(ui_base_url, issue_id)
    elif create_new_issue:
        # Create a new test issue
        logger.info(f"Creating new test issue for playbook: {playbook_name}")
        created_issue = await _create_playbook_test_issue(ctx, playbook_name)

        if "error" in created_issue:
            return create_response(
                data={
                    "error": f"Failed to create test issue: {created_issue.get('error')}",
                    "created_issue": created_issue
                },
                is_error=True
            )

        investigation_id = created_issue.get("issue_id")
        issue_url = _build_issue_url(ui_base_url, investigation_id)

        logger.info(f"Created test issue with ID: {investigation_id}")
    else:
        return create_response(
            data={
                "error": "No issue_id provided and create_new_issue=False",
                "hint": "Provide issue_id, or set create_new_issue=True"
            },
            is_error=True
        )

    # Build the setPlaybook command (capital P is required)
    command = f'!setPlaybook name="{playbook_name}"'

    logger.info(f"Running playbook '{playbook_name}' on investigation {investigation_id}")

    # Try to execute with retries
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await fetcher.send_request(
                path="/entries/insert",
                method="POST",
                data={
                    "id": investigation_id,
                    "data": command
                }
            )

            if isinstance(response, dict):
                # Check for known errors
                error = response.get("error", "")

                if "Could not find investigation" in str(error) or "noInv" in str(response.get("id", "")):
                    last_error = "Investigation not active. USER ACTION REQUIRED: Open the issue URL in XSIAM UI to activate the War Room, then retry this command"

                    if wait_for_investigation and attempt < max_retries - 1:
                        logger.warning(f"Investigation not ready, waiting... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(5)
                        continue
                    else:
                        # Return helpful error with instructions
                        return create_response(
                            data={
                                "error": last_error,
                                "playbook_name": playbook_name,
                                "investigation_id": investigation_id,
                                "issue_url": issue_url,
                                "action_required": "Open the issue URL in your browser to activate the investigation, then retry",
                                "created_issue": created_issue
                            },
                            is_error=True
                        )

                elif "error" in response or response.get("status") == 400:
                    error_detail = response.get("detail", response.get("error", str(response)))
                    return create_response(
                        data={
                            "error": f"Playbook execution failed: {error_detail}",
                            "playbook_name": playbook_name,
                            "investigation_id": investigation_id,
                            "issue_url": issue_url,
                            "response": response
                        },
                        is_error=True
                    )

                else:
                    # Success!
                    result = {
                        "success": True,
                        "message": f"Playbook '{playbook_name}' started successfully",
                        "playbook_name": playbook_name,
                        "investigation_id": investigation_id,
                        "issue_url": issue_url,
                        "entry_id": response.get("id"),
                        "created": response.get("created"),
                        "command_executed": command
                    }

                    if created_issue:
                        result["created_issue"] = created_issue
                        result["note"] = "IMPORTANT: A new issue was created but the playbook has NOT started yet"
                        result["user_action_required"] = "Please open the issue URL in your browser to activate the War Room investigation"
                        result["next_step"] = f"After opening the URL, retry with: run_playbook(playbook_name='{playbook_name}', issue_id='{investigation_id}')"

                    return create_response(data=result)

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(3)
                continue

    # All retries exhausted
    return create_response(
        data={
            "error": f"Failed after {max_retries} attempts: {last_error}",
            "playbook_name": playbook_name,
            "investigation_id": investigation_id,
            "issue_url": issue_url,
            "hint": "Try opening the issue URL in your browser first, then retry"
        },
        is_error=True
    )


class RunPlaybookModule(BaseModule):
    """Module for running XSOAR playbooks via the !setPlaybook command"""

    def register_tools(self):
        self._add_tool(run_playbook)

    def register_resources(self):
        pass
