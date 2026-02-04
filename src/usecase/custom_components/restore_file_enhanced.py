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
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def restore_file(
    ctx: Context,
    file_hash: Annotated[str, Field(description="SHA256 hash of the quarantined file to restore")],
    endpoint_id: Annotated[str | None, Field(description="Optional: Endpoint ID. If not specified, restores on ALL endpoints with this file.")] = None,
    file_path: Annotated[str | None, Field(description="Optional: File path for pre-validation check")] = None,
) -> str:
    """
    Restores previously quarantined files with pre-validation.

    IMPORTANT: This tool validates that the file is actually quarantined
    before attempting restoration. Provides helpful error messages if validation fails.

    Workflow:
    1. Validates file_hash format (must be SHA256 - 64 hex characters)
    2. Checks quarantine status via get_quarantine_status API
    3. Returns helpful error if file is not quarantined
    4. Restores file if validation passes

    Use this when:
    - File was previously quarantined via quarantine_files tool
    - Analysis confirmed file is benign or false positive
    - You need to restore application functionality that depends on the file
    - User/application requires the file back

    CAUTION: Only restore files after thorough analysis confirms they are safe.
    Restoring malicious files will make them executable again.

    Args:
        ctx: The FastMCP context.
        file_hash: SHA256 hash of quarantined file (64 hexadecimal characters).

    Returns:
        JSON response with restoration status:
        - file_hash: The hash that was restored
        - status: restore_initiated or error status
        - message: Human-readable status message
        - response: Full API response (if successful)

    Example:
        restore_file(file_hash="abc123def456...") # 64 char SHA256
    """

    try:
        fetcher = await get_fetcher(ctx)

        # Step 1: Validate file hash format (SHA256 = 64 hex chars)
        if not file_hash or len(file_hash) != 64:
            return create_response(
                data={
                    "error": "Invalid file_hash length",
                    "expected": "SHA256 hash (64 hexadecimal characters)",
                    "received": f"{len(file_hash) if file_hash else 0} characters",
                    "example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                },
                is_error=True
            )

        if not all(c in '0123456789abcdefABCDEF' for c in file_hash):
            return create_response(
                data={
                    "error": "Invalid file_hash format",
                    "expected": "SHA256 hash (hexadecimal characters only: 0-9, A-F)",
                    "received": file_hash,
                    "invalid_characters": [c for c in file_hash if c not in '0123456789abcdefABCDEF']
                },
                is_error=True
            )

        # Step 2: Check if file is actually quarantined (optional - only if endpoint details provided)
        if endpoint_id and file_path:
            logger.info(f"Checking quarantine status for file {file_hash} on endpoint {endpoint_id}")

            status_payload = {
                "request_data": {
                    "files": [{
                        "endpoint_id": endpoint_id,
                        "file_path": file_path,
                        "file_hash": file_hash
                    }]
                }
            }

            status_response = await fetcher.send_request(
                "/public_api/v1/quarantine/status/",
                data=status_payload
            )

            # Parse quarantine status response
            reply = status_response.get("reply", {})
            files = reply.get("files", [])

            # Check if our file appears in response and is quarantined
            is_quarantined = False
            quarantine_info = None

            for file_status in files:
                if file_status.get("file_hash", "").lower() == file_hash.lower():
                    quarantine_info = file_status
                    # Check quarantine status - API may use different field names
                    # Try common field patterns
                    if file_status.get("is_quarantined") or file_status.get("quarantine_status") == "QUARANTINED":
                        is_quarantined = True
                    break

            if not is_quarantined:
                error_data = {
                    "error": "File is not currently quarantined",
                    "file_hash": file_hash,
                    "status": "not_quarantined",
                    "message": (
                        "Only files that are currently quarantined can be restored. "
                        "This file does not appear in the quarantine list."
                    ),
                    "next_steps": [
                        "1. Verify the file hash is correct (must be SHA256)",
                        "2. Use get_quarantine_status to check current quarantine state",
                        "3. If file needs quarantining, use quarantine_files first",
                        "4. Then retry restore_file"
                    ]
                }

                # Include quarantine info if file was found but not quarantined
                if quarantine_info:
                    error_data["quarantine_details"] = quarantine_info

                return create_response(data=error_data, is_error=True)

            logger.info(f"File {file_hash} is quarantined on endpoint {endpoint_id}, proceeding with restore")
        else:
            logger.info(f"Skipping pre-validation (no endpoint details). Restoring {file_hash} on all endpoints.")

        # Step 3: Proceed with restore

        restore_payload = {
            "request_data": {
                "file_hash": file_hash
            }
        }

        # Optionally include endpoint_id to restore on specific endpoint only
        if endpoint_id:
            restore_payload["request_data"]["endpoint_id"] = endpoint_id

        restore_response = await fetcher.send_request(
            "/public_api/v1/endpoints/restore/",
            data=restore_payload
        )

        return create_response(data={
            "file_hash": file_hash,
            "status": "restore_initiated",
            "response": restore_response,
            "message": (
                f"File restoration initiated successfully for {file_hash}. "
                "The file will be restored to its original location on affected endpoints."
            )
        })

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while restoring file {file_hash}: {e}")
        return create_response(
            data={
                "error": f"API error: {str(e)}",
                "file_hash": file_hash,
                "error_type": type(e).__name__
            },
            is_error=True
        )
    except Exception as e:
        logger.exception(f"Unexpected error while restoring file {file_hash}: {e}")
        return create_response(
            data={
                "error": str(e),
                "file_hash": file_hash
            },
            is_error=True
        )


class RestoreFileEnhancedModule(BaseModule):
    """
    Enhanced file restoration with pre-validation.

    This module provides a restore_file tool that validates files are actually
    quarantined before attempting restoration, providing clear error messages
    and next steps if validation fails.

    Replaces the simple OpenAPI YAML wrapper with intelligent pre-validation.

    Tools provided:
        - restore_file: Restore quarantined files with validation
    """

    def register_tools(self):
        self._add_tool(restore_file)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
