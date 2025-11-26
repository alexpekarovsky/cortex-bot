import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError,
    PAPIClientError,
    PAPIClientRequestError,
    PAPIConnectionError,
    PAPIResponseError,
    PAPIServerError,
)
from entities.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def list_risky_users(
    ctx: Context,
) -> str:
    """
    Retrieves a list of users that XSIAM has identified as high-risk based on behavioral analytics.

    XSIAM continuously analyzes user behavior and assigns risk scores based on anomalous activities,
    suspicious patterns, authentication anomalies, and other risk indicators. Users flagged as risky
    may be compromised accounts or insiders engaging in malicious activity.

    Use this tool to:
    - Identify potentially compromised user accounts
    - Prioritize investigations based on user risk
    - Proactively hunt for insider threats
    - Review users requiring additional scrutiny
    - Focus incident response on high-risk accounts

    Risk indicators may include:
    - Unusual login patterns or locations
    - Privilege escalation attempts
    - Access to sensitive resources
    - Behavioral anomalies
    - Multiple failed authentication attempts
    - After-hours access patterns

    Args:
        ctx: The FastMCP context.

    Returns:
        JSON response containing list of risky users with their risk scores and reasons.
    """

    payload = {}

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/get_risky_users",
            data=payload
        )

        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while listing risky users: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to list risky users: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def list_risky_hosts(
    ctx: Context,
) -> str:
    """
    Retrieves a list of hosts/endpoints that XSIAM has identified as high-risk based on behavioral analytics.

    XSIAM continuously monitors endpoint behavior and assigns risk scores based on suspicious activities,
    malware indicators, unusual network connections, and other risk factors. Hosts flagged as risky
    may be compromised, infected with malware, or exhibiting anomalous behavior.

    Use this tool to:
    - Identify potentially compromised endpoints
    - Prioritize endpoint investigations
    - Proactively hunt for infected systems
    - Review hosts requiring immediate attention
    - Focus incident response on high-risk machines

    Risk indicators may include:
    - Malware or suspicious process execution
    - Unusual network connections or beaconing
    - Lateral movement attempts
    - Privilege escalation activities
    - Suspicious file modifications
    - Communication with known malicious IPs/domains
    - Behavioral anomalies compared to baseline

    Args:
        ctx: The FastMCP context.

    Returns:
        JSON response containing list of risky hosts with their risk scores and reasons.
    """

    payload = {}

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/get_risky_hosts",
            data=payload
        )

        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while listing risky hosts: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to list risky hosts: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class RiskyEntitiesModule(BaseModule):
    """
    Module for identifying high-risk users and hosts in the environment.

    This module provides access to XSIAM's behavioral analytics that identify
    risky entities based on anomalous behavior, suspicious activities, and
    threat indicators. Essential for proactive threat hunting and prioritizing
    security investigations.

    Tools provided:
        - list_risky_users: Get list of high-risk user accounts
        - list_risky_hosts: Get list of high-risk endpoints/hosts
    """

    def register_tools(self):
        self._add_tool(list_risky_users)
        self._add_tool(list_risky_hosts)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
