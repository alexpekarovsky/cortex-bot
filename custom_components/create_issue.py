"""
XSIAM Issue Creation Tool

Creates a new issue (alert) that can be used as a "scratch pad" for running
War Room automation commands like enrichment without needing an existing case.
"""

import logging
import time
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def create_issue(
    ctx: Context,
    name: Annotated[Optional[str], Field(description="Issue name (default: 'AI Workspace - {timestamp}')")] = None,
    description: Annotated[Optional[str], Field(description="Issue description (default: 'Scratch pad issue for AI-driven enrichment and automation')")] = None,
    severity: Annotated[str, Field(description="Severity level: INFO, LOW, MEDIUM, HIGH, CRITICAL (default: MEDIUM - creates a Case with War Room)")] = "MEDIUM",
    domain: Annotated[str, Field(description="Issue domain: SECURITY, IDENTITY, CLOUD (default: SECURITY)")] = "SECURITY",
    category: Annotated[str, Field(description="Issue category: CONFIGURATION, THREAT_INTELLIGENCE, etc. (default: THREAT_INTELLIGENCE)")] = "THREAT_INTELLIGENCE",
    tags: Annotated[Optional[list], Field(description="Tags to apply to the issue (default: ['ai-workspace', 'scratch-pad'])")] = None,
) -> str:
    """
    Creates a new issue (alert) in XSIAM that can be used as a "scratch pad" for
    running War Room automation commands.

    =====================================================================
    WHY USE THIS TOOL?
    =====================================================================

    When you need to run enrichment or automation commands but don't have a
    specific case/issue to work with, use this tool to create a dedicated
    workspace. This is much cleaner than searching for existing issues to
    use as scratch pads.

    WORKFLOW:
    1. Call create_issue() to create a scratch pad
    2. Use the returned external_id as alert_id for enrichment tools
    3. All enrichment results will be stored in this issue's War Room

    Example:
        # Create scratch pad
        issue = create_issue(name="IP Investigation Workspace")
        # Returns: {"external_id": "abc123...", ...}

        # Use for enrichment
        enrich_ip_address(ip_address="8.8.8.8", alert_id="abc123...")
        enrich_domain(domain="google.com", alert_id="abc123...")
        run_xsoar_automation(command="!GetInstances", alert_id="abc123...")

    =====================================================================

    The created issue:
    - Uses MEDIUM severity by default (triggers Case creation with War Room)
    - Is clearly labeled as an AI workspace
    - Has a War Room ready for automation commands
    - Can be resolved/closed when done

    NOTE: MEDIUM+ severity issues automatically get grouped into a Case,
    which provides the War Room needed for running automation commands.

    Args:
        ctx: The FastMCP context.
        name: Custom name for the issue. Defaults to "AI Workspace - {timestamp}".
        description: Custom description. Defaults to scratch pad explanation.
        severity: Severity level (INFO, LOW, MEDIUM, HIGH, CRITICAL). Default: MEDIUM.
        domain: Issue domain (SECURITY, IDENTITY, CLOUD). Default: SECURITY.
        category: Issue category. Default: THREAT_INTELLIGENCE.
        tags: List of tags. Default: ['ai-workspace', 'scratch-pad'].

    Returns:
        JSON response with external_id (use as alert_id for other tools),
        detection_method, and creation details.
    """
    # Set defaults
    timestamp = int(time.time() * 1000)  # Current time in milliseconds

    if name is None:
        name = f"AI Workspace - {time.strftime('%Y-%m-%d %H:%M:%S')}"

    if description is None:
        description = "Scratch pad issue for AI-driven enrichment and automation commands. This issue was created programmatically to serve as a War Room workspace."

    if tags is None:
        tags = ["ai-workspace", "scratch-pad"]

    # Validate severity
    valid_severities = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if severity.upper() not in valid_severities:
        return create_response(
            data={"error": f"Invalid severity '{severity}'. Must be one of: {valid_severities}"},
            is_error=True
        )

    # Validate domain
    valid_domains = ["SECURITY", "IDENTITY", "CLOUD"]
    if domain.upper() not in valid_domains:
        return create_response(
            data={"error": f"Invalid domain '{domain}'. Must be one of: {valid_domains}"},
            is_error=True
        )

    logger.info(f"Creating scratch pad issue: {name}")

    try:
        fetcher = await get_fetcher(ctx)

        # Build minimal issue payload (only required fields + useful extras)
        issue_payload = {
            "name": name,
            "description": description,
            "observation_time": timestamp,
            "issue_domain": domain.upper(),
            "category": category.upper(),
            "severity": severity.upper(),
            "tags": ",".join(tags) if isinstance(tags, list) else tags,
            "is_excluded": False,
            "is_starred": False,
            "type": "AI Workspace",
            "extended_description": "This issue serves as a workspace for running XSOAR automation commands and threat intelligence enrichment via AI assistants.",
            "custom_fields": {}
        }

        request_data = {
            "request_data": {
                "issue": issue_payload
            }
        }

        response = await fetcher.send_request(
            path="/public_api/v1/issue",
            method="POST",
            data=request_data
        )

        logger.info(f"Create issue API response: {response}")

        if isinstance(response, dict):
            # Handle both direct response and "reply" wrapped response
            if "reply" in response:
                actual_response = response["reply"]
            else:
                actual_response = response

            external_id = actual_response.get("external_id")
            detection_method = actual_response.get("detection_method")

            # Query to get the numeric issue_id (War Room needs numeric ID, not UUID)
            numeric_issue_id = None
            try:
                import asyncio
                await asyncio.sleep(5)  # Wait for issue to be indexed (2s was too short)

                issues_response = await fetcher.send_request(
                    path="/issue/search/",
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
                    reply = issues_response.get("reply", {})
                    issues = reply.get("DATA", [])
                    if issues and len(issues) > 0:
                        numeric_issue_id = str(issues[0].get("id"))
                        logger.info(f"Found numeric issue_id: {numeric_issue_id}")

            except Exception as e:
                logger.warning(f"Could not retrieve numeric issue_id: {e}")

            alert_id_to_use = numeric_issue_id or external_id

            result = {
                "success": True,
                "external_id": external_id,
                "alert_id": alert_id_to_use,  # Numeric ID for War Room commands
                "detection_method": detection_method,
                "issue_name": name,
                "severity": severity.upper(),
                "domain": domain.upper(),
                "category": category.upper(),
                "tags": tags,
                "usage_instructions": {
                    "message": "Use the 'alert_id' value with enrichment and automation tools",
                    "example_ip_enrichment": f"enrich_ip_address(ip_address='8.8.8.8', alert_id='{alert_id_to_use}')",
                    "example_domain_enrichment": f"enrich_domain(domain='example.com', alert_id='{alert_id_to_use}')",
                    "example_automation": f"run_xsoar_automation(command='!GetInstances', alert_id='{alert_id_to_use}')"
                }
            }

            logger.info(f"Successfully created scratch pad issue with alert_id: {alert_id_to_use} (external_id: {external_id})")
            return create_response(data=result)

        return create_response(data=response)

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Failed to create issue: {e}")

        return create_response(
            data={"error": f"Failed to create issue: {error_msg}"},
            is_error=True
        )


class CreateIssueModule(BaseModule):
    """Module for creating scratch pad issues for War Room automation"""

    def register_tools(self):
        self._add_tool(create_issue)

    def register_resources(self):
        pass
