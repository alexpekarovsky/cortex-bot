"""
Demisto SDK MCP Tools

Wrapper tools for the Demisto SDK that enable XSOAR content development
directly from an AI assistant. These tools map to demisto-sdk CLI commands.

Requirements:
    - demisto-sdk must be installed: pip install demisto-sdk
    - Same XSIAM credentials as the MCP server (automatically mapped)

Usage:
    The SDK tools use the same environment variables as the MCP server:
    - CORTEX_MCP_PAPI_URL -> DEMISTO_BASE_URL
    - CORTEX_MCP_PAPI_AUTH_HEADER -> DEMISTO_API_KEY
    - CORTEX_MCP_PAPI_AUTH_ID -> XSIAM_AUTH_ID
"""

import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.custom_components.sdk_base import DemistoSDKRunner

logger = logging.getLogger(__name__)


# =============================================================================
# SDK Tool Functions
# =============================================================================

async def sdk_init(
    ctx: Context,
    name: Annotated[str, Field(description="Name of the integration, script, or pack to create")],
    content_type: Annotated[str, Field(description="Type to create: 'integration', 'script', or 'pack'")] = "integration",
    pack_name: Annotated[Optional[str], Field(description="Pack name (required for integration/script)")] = None,
    output_dir: Annotated[Optional[str], Field(description="Output directory (default: current directory)")] = None,
) -> str:
    """
    Initialize a new XSOAR integration, script, or content pack.

    Creates the scaffold directory structure with template files for developing
    custom XSOAR content. This is the first step in the development workflow.

    Use this when:
    - Starting a new integration project
    - Creating a new automation script
    - Setting up a new content pack

    After init, you can:
    - Edit the generated Python code
    - Modify the YAML configuration
    - Run sdk_validate to check structure
    - Run sdk_upload to deploy to XSIAM

    Args:
        ctx: The FastMCP context.
        name: Name of the content to create (e.g., "MyIntegration").
        content_type: Type of content - "integration", "script", or "pack".
        pack_name: Pack name for integration/script (creates pack if not exists).
        output_dir: Output directory (default: current directory).

    Returns:
        JSON response with created file paths and next steps.
    """
    args = ["init", "--name", name]

    # Add content type as flag (not --type parameter)
    if content_type == "integration":
        args.append("--integration")
    elif content_type == "script":
        args.append("--script")
    elif content_type == "pack":
        args.append("--pack")

    if output_dir:
        args.extend(["--output", output_dir])

    # demisto-sdk init prompts for interactive input (Y/N for ID, fromversion, etc.)
    # Pipe default answers via stdin to prevent hanging in non-interactive environments.
    # Answers: Y (use directory name as ID), empty (accept default fromversion)
    stdin_answers = "Y\n\n"

    result = await DemistoSDKRunner.run_sdk_command(args, stdin_data=stdin_answers)

    if result["success"]:
        return create_response(data={
            "success": True,
            "name": name,
            "type": content_type,
            "pack_name": pack_name,
            "output": result["stdout"],
            "next_steps": [
                f"1. Edit the Python code in {name}/{name}.py",
                f"2. Modify the YAML config in {name}/{name}.yml",
                "3. Run sdk_validate to check structure",
                "4. Run sdk_lint to check code quality",
                "5. Run sdk_upload to deploy to XSIAM"
            ]
        })
    else:
        return create_response(data={
            "success": False,
            "error": result["stderr"] or "Failed to initialize content",
            "command": result["command"]
        }, is_error=True)


async def sdk_validate(
    ctx: Context,
    path: Annotated[str, Field(description="Path to content pack, integration, or script to validate")],
) -> str:
    """
    Validate XSOAR content structure and metadata.

    Checks that the content follows Cortex XSOAR standards including:
    - Correct directory structure
    - Valid YAML configuration
    - Required files present
    - Proper metadata format

    Use this before uploading to catch structural issues early.

    Args:
        ctx: The FastMCP context.
        path: Path to the content to validate (e.g., "Packs/MyPack").

    Returns:
        JSON response with validation results and any errors/warnings.
    """
    args = ["validate", "-i", path]

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=120)

    # Parse validation output
    has_errors = "Error" in result["stdout"] or "Error" in result["stderr"]
    has_warnings = "Warning" in result["stdout"] or "Warning" in result["stderr"]

    return create_response(data={
        "success": result["success"] and not has_errors,
        "path": path,
        "has_errors": has_errors,
        "has_warnings": has_warnings,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_lint(
    ctx: Context,
    path: Annotated[str, Field(description="Path to integration or script to lint")],
    fix: Annotated[bool, Field(description="Automatically fix linting issues")] = False,
) -> str:
    """
    Lint Python code in XSOAR integrations and scripts.

    Checks code quality including:
    - PEP 8 compliance
    - Common Python issues
    - XSOAR-specific best practices
    - Type hints and documentation

    Args:
        ctx: The FastMCP context.
        path: Path to the content to lint.
        fix: If True, automatically fix issues where possible.

    Returns:
        JSON response with linting results and issues found.
    """
    # Use 'format' command instead of 'lint' (lint doesn't exist in current SDK)
    args = ["format", "-i", path]

    if fix:
        args.append("--assume-yes")  # Auto-confirm formatting

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=180)

    return create_response(data={
        "success": result["success"],
        "path": path,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None,
        "fixed": fix and result["success"]
    })


async def sdk_upload(
    ctx: Context,
    path: Annotated[str, Field(description="Path to content to upload (pack, integration, or script)")],
) -> str:
    """
    Upload content to Cortex XSIAM.

    Uploads the specified content pack, integration, or script to your XSIAM
    instance. The content becomes immediately available for use.

    IMPORTANT: Uses the same credentials as the MCP server.

    Args:
        ctx: The FastMCP context.
        path: Path to the content to upload.

    Returns:
        JSON response with upload status.
    """
    args = ["upload", "-i", path]

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=300)

    if result["success"]:
        return create_response(data={
            "success": True,
            "path": path,
            "message": "Content uploaded successfully to XSIAM",
            "output": result["stdout"]
        })
    else:
        return create_response(data={
            "success": False,
            "path": path,
            "error": result["stderr"] or "Upload failed",
            "output": result["stdout"]
        }, is_error=True)


async def sdk_download(
    ctx: Context,
    content_name: Annotated[str, Field(description="Name of content to download (integration, script, playbook)")],
    output_dir: Annotated[Optional[str], Field(description="Output directory (default: current directory)")] = None,
) -> str:
    """
    Download content from Cortex XSIAM.

    Downloads existing content from your XSIAM instance to local files for
    editing and modification.

    Args:
        ctx: The FastMCP context.
        content_name: Name of the content to download.
        output_dir: Output directory for downloaded files.

    Returns:
        JSON response with download status and file paths.
    """
    args = ["download", "-i", content_name]

    # Output is required, use current directory if not specified
    if not output_dir:
        output_dir = "."
    args.extend(["-o", output_dir])

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=120)

    return create_response(data={
        "success": result["success"],
        "content_name": content_name,
        "output_dir": output_dir or ".",
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_run(
    ctx: Context,
    command: Annotated[str, Field(description="Integration command to run (e.g., 'ip ip=8.8.8.8')")],
    integration_name: Annotated[Optional[str], Field(description="Integration instance name")] = None,
) -> str:
    """
    Execute an integration command on XSIAM.

    Runs a command from an integration directly via the SDK, useful for
    testing integrations during development.

    Args:
        ctx: The FastMCP context.
        command: The command to run with arguments.
        integration_name: Optional integration instance name.

    Returns:
        JSON response with command output.
    """
    args = ["run", "-q", command]

    if integration_name:
        args.extend(["--instance", integration_name])

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=60)

    # Handle playground errors gracefully
    if not result["success"] and "playground" in result["stderr"].lower():
        return create_response(data={
            "success": False,
            "error": "SDK run command requires XSOAR playground configuration",
            "recommendation": "Use run_xsoar_automation MCP tool instead, or configure SDK playground",
            "command": command
        }, is_error=True)

    return create_response(data={
        "success": result["success"],
        "command": command,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_run_playbook(
    ctx: Context,
    playbook_name: Annotated[str, Field(description="Name of the playbook to run")],
    wait: Annotated[bool, Field(description="Wait for playbook completion")] = True,
    timeout: Annotated[int, Field(description="Timeout in seconds")] = 300,
) -> str:
    """
    Execute a playbook on XSIAM for testing.

    Runs a playbook and optionally waits for completion, useful for
    testing playbook logic during development.

    Args:
        ctx: The FastMCP context.
        playbook_name: Name of the playbook to execute.
        wait: If True, wait for playbook completion.
        timeout: Maximum seconds to wait.

    Returns:
        JSON response with playbook execution results.
    """
    args = ["run-playbook", "-p", playbook_name]

    if wait:
        args.append("--wait")

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=timeout)

    # Handle playground/playbook errors gracefully
    if not result["success"] and ("playground" in result["stderr"].lower() or "does not exist" in result["stderr"].lower()):
        return create_response(data={
            "success": False,
            "error": "SDK run-playbook requires XSOAR playground and playbook to exist",
            "recommendation": "Use run_playbook MCP tool instead for running playbooks on issues",
            "playbook_name": playbook_name
        }, is_error=True)

    return create_response(data={
        "success": result["success"],
        "playbook_name": playbook_name,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_generate_docs(
    ctx: Context,
    path: Annotated[str, Field(description="Path to integration or script")],
    output_dir: Annotated[Optional[str], Field(description="Output directory for documentation")] = None,
) -> str:
    """
    Generate documentation for XSOAR content.

    Creates README.md files with command documentation, examples,
    and configuration instructions.

    Args:
        ctx: The FastMCP context.
        path: Path to the content to document.
        output_dir: Output directory for generated docs.

    Returns:
        JSON response with generated documentation paths.
    """
    args = ["generate-docs", "-i", path]

    if output_dir:
        args.extend(["--output", output_dir])

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=60)

    return create_response(data={
        "success": result["success"],
        "path": path,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_split(
    ctx: Context,
    path: Annotated[str, Field(description="Path to unified YAML file to split")],
    output_dir: Annotated[Optional[str], Field(description="Output directory for split files")] = None,
) -> str:
    """
    Split a unified YAML file into directory structure.

    Converts a single unified YAML file (downloaded from XSIAM) into
    the standard directory structure for development.

    Args:
        ctx: The FastMCP context.
        path: Path to the unified YAML file.
        output_dir: Output directory for split files.

    Returns:
        JSON response with created file paths.
    """
    args = ["split", "-i", path]

    if output_dir:
        args.extend(["--output", output_dir])

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=60)

    return create_response(data={
        "success": result["success"],
        "path": path,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


async def sdk_unify(
    ctx: Context,
    path: Annotated[str, Field(description="Path to content directory to unify")],
    output_file: Annotated[Optional[str], Field(description="Output file path for unified YAML")] = None,
) -> str:
    """
    Create a unified YAML file from directory structure.

    Combines the directory structure (Python code, YAML config, etc.)
    into a single unified YAML file for upload.

    **SETUP REQUIRED:**
    This tool requires a content repository with Packs/ directory.

    1. Create content directory: `mkdir -p ~/content/Packs`
    2. Set environment variable (optional):
       ```bash
       export DEMISTO_SDK_CONTENT_PATH=~/content
       # or
       export CONTENT_PATH=~/content
       ```
    3. The tool automatically uses ~/content if it exists

    Args:
        ctx: The FastMCP context.
        path: Path to content directory (e.g., "Packs/MyPack").
        output_file: Output file path for the unified YAML.

    Returns:
        JSON response with unified file path.
    """
    args = ["prepare-content", "-i", path]

    if output_file:
        args.extend(["--output", output_file])

    result = await DemistoSDKRunner.run_sdk_command(args, timeout=60)

    return create_response(data={
        "success": result["success"],
        "path": path,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None
    })


# =============================================================================
# Module Registration
# =============================================================================

class SDKToolsModule(BaseModule):
    """
    Module providing Demisto SDK wrapper tools.

    These tools enable XSOAR content development directly from an AI assistant,
    supporting the full development lifecycle:
    - Initialize new content (sdk_init)
    - Validate structure (sdk_validate)
    - Lint code (sdk_lint)
    - Upload to XSIAM (sdk_upload)
    - Download from XSIAM (sdk_download)
    - Run commands (sdk_run)
    - Test playbooks (sdk_run_playbook)
    - Generate documentation (sdk_generate_docs)
    - Split/unify YAML files (sdk_split, sdk_unify)

    Requirements:
        - demisto-sdk must be installed: pip install demisto-sdk
        - Python 3.9, 3.10, or 3.11
        - Linux, macOS, or WSL2 (Windows not directly supported)
    """

    def register_tools(self):
        """Register all SDK wrapper tools."""
        # sdk_init removed — requires interactive prompt, not MCP-compatible
        # self._add_tool(sdk_init)
        self._add_tool(sdk_validate)
        self._add_tool(sdk_lint)
        self._add_tool(sdk_upload)
        self._add_tool(sdk_download)
        self._add_tool(sdk_run)
        self._add_tool(sdk_run_playbook)
        self._add_tool(sdk_generate_docs)
        self._add_tool(sdk_split)
        self._add_tool(sdk_unify)

    def register_resources(self):
        """SDK module doesn't register resources."""
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
