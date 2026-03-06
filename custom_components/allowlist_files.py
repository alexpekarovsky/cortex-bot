"""
Allow List Files Tool

Adds file hashes to the Cortex XSIAM allowlist to exempt them from security
restrictions and allow execution on managed endpoints.
"""

import logging
import re
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
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def allowlist_files(
    ctx: Context,
    hash_list: Annotated[list[str], Field(description="List of file hashes (MD5, SHA1, or SHA256) to add to allowlist")],
    comment: Annotated[str | None, Field(description="Optional comment explaining why these hashes are being allowlisted")] = None,
    incident_id: Annotated[int | None, Field(description="Optional incident/case ID to associate this allowlist action with")] = None,
    confirm_destructive_action: Annotated[bool, Field(
        description="REQUIRED: Must be True to execute. This action modifies security policies and cannot be easily reversed."
    )] = False,
) -> str:
    """
    Adds file hashes to the Cortex XSIAM allowlist to exempt them from security restrictions.

    HIGH RISK ACTION - Requires Confirmation
    This action exempts files from security controls across your entire environment.
    Allowlisting files that are actually malicious could compromise security.

    Use this when:
    - You've confirmed files are benign after thorough analysis
    - False positive detections need to be exempted from blocking
    - Legitimate applications are being incorrectly blocked
    - Your organization's custom/proprietary software is being flagged
    - You need to override blocklist decisions with explicit allowlist

    Reversal:
    - Allowlisted files can be removed via the API if security policy changes
    - The action is tracked via incident_id for audit purposes

    Args:
        ctx: The FastMCP context.
        hash_list: List of file hashes to allowlist. Accepts MD5, SHA1, or SHA256.
                  Example: ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "d41d8cd98f00b204e9800998ecf8427e"]
        comment: Optional explanation for why these files are being allowlisted.
                Example: "Confirmed safe - custom enterprise application v2.1"
        incident_id: Optional incident/case ID for tracking and audit purposes.
        confirm_destructive_action: Must be True to execute this action.

    Returns:
        JSON response with allowlist operation status and details.
    """

    # Safety check - require explicit confirmation
    if not confirm_destructive_action:
        return create_response(
            data={
                "error": "Action not confirmed",
                "message": "This is a HIGH risk action that exempts files from security controls. "
                          "Set confirm_destructive_action=True to proceed.",
                "risk_level": "HIGH",
                "reversible": True,
                "reversal_method": "Files can be removed from allowlist via API",
                "security_warning": "Allowlisting files can compromise security if done incorrectly. "
                                   "Only allowlist files after thorough verification."
            },
            is_error=True
        )

    # Validate hash_list is not empty
    if not hash_list or len(hash_list) == 0:
        return create_response(
            data={
                "error": "hash_list cannot be empty",
                "message": "At least one hash must be provided to allowlist"
            },
            is_error=True
        )


    # Validate hash format (MD5=32, SHA1=40, SHA256=64 hex chars)
    valid_lengths = {32, 40, 64}
    hex_pattern = re.compile(r'^[0-9a-fA-F]+$')
    invalid_hashes = [
        h for h in hash_list
        if len(h) not in valid_lengths or not hex_pattern.match(h)
    ]
    if invalid_hashes:
        return create_response(
            data={
                "error": "Invalid hash format",
                "invalid_hashes": invalid_hashes,
                "expected": "Hexadecimal string of length 32 (MD5), 40 (SHA1), or 64 (SHA256)",
            },
            is_error=True
        )

    try:
        logger.info(f"Adding {len(hash_list)} hashes to allowlist")

        fetcher = await get_fetcher(ctx)

        # Build the allowlist request
        payload = {
            "request_data": {
                "hash_list": hash_list
            }
        }

        # Add optional fields if provided
        if comment:
            payload["request_data"]["comment"] = comment

        if incident_id is not None:
            payload["request_data"]["incident_id"] = incident_id

        response = await fetcher.send_request(
            "/public_api/v1/hash_exceptions/allowlist",
            data=payload
        )

        # Extract relevant data from response
        result = {
            "hash_list": hash_list,
            "hash_count": len(hash_list),
            "status": "allowlist_initiated",
            "message": f"Successfully added {len(hash_list)} hash(es) to allowlist"
        }

        # Include optional fields if they were provided
        if comment:
            result["comment"] = comment

        if incident_id is not None:
            result["incident_id"] = incident_id

        # Include full response for reference if it's an object
        if isinstance(response, dict):
            result["response"] = response
        elif response is True:
            result["api_status"] = "success"
        else:
            result["api_response"] = response

        logger.info(f"Successfully allowlisted {len(hash_list)} hashes")
        return create_response(data=result)

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while allowlisting files: {e}")
        return create_response(
            data={
                "error": f"API error: {str(e)}",
                "hash_count": len(hash_list),
                "error_type": type(e).__name__
            },
            is_error=True
        )
    except Exception as e:
        logger.exception(f"Failed to allowlist files: {e}")
        return create_response(
            data={
                "error": str(e),
                "hash_count": len(hash_list)
            },
            is_error=True
        )


class AllowlistFilesModule(BaseModule):
    """
    Module for exempting files from security restrictions.

    This module provides the allowlist_files tool that adds file hashes to the
    Cortex XSIAM allowlist, exempting them from security controls on all
    managed endpoints.

    Tools provided:
        - allowlist_files: Add file hashes to the enterprise allowlist
    """

    def register_tools(self):
        self._add_tool(allowlist_files)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
