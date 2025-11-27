"""
Endpoint Isolation Response Action

Isolates endpoints from the network to contain threats and prevent lateral movement.
"""

import logging
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError,
    PAPIClientError,
    PAPIClientRequestError,
    PAPIConnectionError,
    PAPIResponseError,
    PAPIServerError,
)
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def isolate_endpoint(
    ctx: Context,
    endpoint_id: Annotated[str, Field(description="Endpoint ID to isolate")],
) -> str:
    """
    Isolates an endpoint from the network to contain threats and prevent lateral movement.
    When an endpoint is isolated, it can only communicate with the Cortex agent and cannot
    access other network resources. This is critical for incident response to contain
    compromised systems.

    Use this when:
    - A system is confirmed compromised and needs immediate containment
    - You need to prevent malware from spreading to other systems
    - An endpoint is exhibiting malicious behavior
    - As part of incident response to isolate affected systems

    The endpoint can be un-isolated later once the threat is remediated.

    Args:
        ctx: The FastMCP context.
        endpoint_id: The endpoint ID to isolate.

    Returns:
        JSON response with action_id for tracking the isolation operation.
    """
    payload = {
        "request_data": {
            "filters": [
                {
                    "field": "endpoint_id_list",
                    "operator": "in",
                    "value": [endpoint_id]
                }
            ]
        }
    }

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/endpoints/isolate/",
            data=payload
        )

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while isolating endpoint: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to isolate endpoint: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def unisolate_endpoint(
    ctx: Context,
    endpoint_id: Annotated[str, Field(description="Endpoint ID to unisolate")],
) -> str:
    """
    Removes network isolation from an endpoint, restoring normal network connectivity.
    Use this after an isolated endpoint has been remediated and cleaned of threats.

    IMPORTANT: Only unisolate endpoints after:
    - Threat has been completely removed
    - System has been verified clean
    - Incident response is complete

    This is the reversal operation for isolate_endpoint.

    Args:
        ctx: The FastMCP context.
        endpoint_id: The endpoint ID to unisolate.

    Returns:
        JSON response with action_id for tracking the unisolation operation.
    """
    payload = {
        "request_data": {
            "filters": [
                {
                    "field": "endpoint_id_list",
                    "operator": "in",
                    "value": [endpoint_id]
                }
            ]
        }
    }

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/endpoints/unisolate/",
            data=payload
        )

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while unisolating endpoint: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to unisolate endpoint: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class EndpointIsolationModule(BaseModule):
    """
    Module for endpoint network isolation response actions.

    Provides tools to isolate and unisolate endpoints for threat containment
    and remediation workflows.

    Tools provided:
        - isolate_endpoint: Isolate endpoint from network
        - unisolate_endpoint: Restore endpoint network connectivity
    """

    def register_tools(self):
        self._add_tool(isolate_endpoint)
        self._add_tool(unisolate_endpoint)

    def register_resources(self):
        pass
