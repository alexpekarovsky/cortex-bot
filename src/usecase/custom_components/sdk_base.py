"""
Demisto SDK Base Module

Base class and utilities for running Demisto SDK commands from the MCP server.
Maps MCP environment variables to SDK environment variables automatically.
"""

import asyncio
import logging
import os
import shutil
from typing import Optional

from fastmcp import FastMCP

from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)


class DemistoSDKRunner:
    """
    Base class for running Demisto SDK commands.

    Provides utilities for:
    - Mapping MCP environment variables to SDK environment variables
    - Running SDK commands asynchronously via subprocess
    - Handling command output and errors
    """

    @staticmethod
    def is_sdk_available() -> bool:
        """Check if uvx is available (used to run demisto-sdk in isolated environment)."""
        return shutil.which("uvx") is not None

    @staticmethod
    def get_env_with_sdk_vars() -> dict:
        """
        Create environment dictionary with SDK variables mapped from MCP variables.

        Maps:
            CORTEX_MCP_PAPI_URL -> DEMISTO_BASE_URL
            CORTEX_MCP_PAPI_AUTH_HEADER -> DEMISTO_API_KEY
            CORTEX_MCP_PAPI_AUTH_ID -> XSIAM_AUTH_ID

        Returns:
            dict: Environment variables for SDK subprocess
        """
        env = os.environ.copy()

        # Try to import config first (from main MCP server)
        try:
            from config.config import get_config
            config = get_config()
            papi_url = config.papi_url_env_key or os.getenv("CORTEX_MCP_PAPI_URL", "")
            papi_auth = config.papi_auth_header_key or os.getenv("CORTEX_MCP_PAPI_AUTH_HEADER", "")
            papi_auth_id = config.papi_auth_id_key or os.getenv("CORTEX_MCP_PAPI_AUTH_ID", "")
        except:
            # Fallback to environment variables only
            papi_url = os.getenv("CORTEX_MCP_PAPI_URL", "")
            papi_auth = os.getenv("CORTEX_MCP_PAPI_AUTH_HEADER", "")
            papi_auth_id = os.getenv("CORTEX_MCP_PAPI_AUTH_ID", "")

        if papi_url:
            env["DEMISTO_BASE_URL"] = papi_url
        if papi_auth:
            env["DEMISTO_API_KEY"] = papi_auth
        if papi_auth_id:
            env["XSIAM_AUTH_ID"] = papi_auth_id

        # Set content path for SDK operations (from env or default)
        content_path = os.getenv("DEMISTO_SDK_CONTENT_PATH") or os.getenv("CONTENT_PATH")
        if not content_path:
            # Try common default location
            default_path = os.path.expanduser("~/content")
            if os.path.exists(default_path):
                content_path = default_path

        if content_path:
            env["CONTENT_PATH"] = content_path
            env["DEMISTO_SDK_CONTENT_PATH"] = content_path

        return env

    @staticmethod
    async def run_sdk_command(
        args: list[str],
        timeout: int = 300,
        cwd: Optional[str] = None
    ) -> dict:
        """
        Run a demisto-sdk command asynchronously.

        Args:
            args: Command arguments (without 'demisto-sdk' prefix)
            timeout: Maximum seconds to wait for command completion
            cwd: Working directory for the command

        Returns:
            dict: {
                "success": bool,
                "return_code": int,
                "stdout": str,
                "stderr": str,
                "command": str
            }
        """
        if not DemistoSDKRunner.is_sdk_available():
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "uvx is not installed. Install uv package manager: pip install uv",
                "command": f"uvx demisto-sdk {' '.join(args)}"
            }

        command = f"uvx demisto-sdk {' '.join(args)}"
        logger.info(f"Running SDK command via uvx: {command}")

        # Use shared content directory if not specified
        if cwd is None:
            cwd = os.path.expanduser("~/content")
            logger.info(f"Using default content directory: {cwd}")

        # Get environment with SDK variables
        env = DemistoSDKRunner.get_env_with_sdk_vars()
        env["DEMISTO_SDK_IGNORE_CONTENT_WARNING"] = "1"

        try:
            proc = await asyncio.create_subprocess_exec(
                "uvx",
                "demisto-sdk",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "command": command
                }

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            result = {
                "success": proc.returncode == 0,
                "return_code": proc.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "command": command
            }

            if proc.returncode != 0:
                logger.warning(f"SDK command failed: {command}\nStderr: {stderr_str}")
            else:
                logger.info(f"SDK command succeeded: {command}")

            return result

        except Exception as e:
            logger.exception(f"Error running SDK command: {e}")
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }


def sdk_check_available() -> str:
    """
    Check if the Demisto SDK is available.

    Returns a JSON response indicating SDK availability.
    """
    if DemistoSDKRunner.is_sdk_available():
        return create_response(data={
            "available": True,
            "message": "Demisto SDK is installed and available"
        })
    else:
        return create_response(
            data={
                "available": False,
                "message": "Demisto SDK is not installed. Run: pip install demisto-sdk",
                "install_command": "pip install demisto-sdk"
            },
            is_error=True
        )


class SDKBaseModule(BaseModule):
    """
    Base module for SDK tools.

    Provides common functionality for all SDK wrapper tools.
    """

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
        self.runner = DemistoSDKRunner()

    def register_tools(self):
        """Override in subclass to register specific SDK tools."""
        pass

    def register_resources(self):
        """SDK modules don't register resources."""
        pass
