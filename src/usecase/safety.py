"""
Safety Controls for Destructive MCP Tools

This module provides a registry and helper functions for managing destructive tools
that can modify endpoint state, terminate processes, or execute code remotely.

Safety is implemented in 3 layers:
1. Description warnings - All destructive tools have prominent warnings
2. Confirmation parameter - HIGH risk tools require explicit confirmation
3. Environment toggle - HIGH risk tools can be disabled entirely
"""

from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    """Risk levels for destructive tools."""
    HIGH = "HIGH"      # Requires all 3 safety layers
    MEDIUM = "MEDIUM"  # Warning + confirmation parameter
    LOW = "LOW"        # Warning only (reversal exists)


# Registry of destructive tools by risk level
DESTRUCTIVE_TOOLS: dict[RiskLevel, list[str]] = {
    RiskLevel.HIGH: [
        "isolate_endpoint",      # Network isolation - can block all network access
        "terminate_causality",   # Kill entire process tree
        "terminate_process",     # Kill processes by name
        "quarantine_files",      # Quarantine files on endpoint
        "run_snippet_code_script",  # Execute arbitrary code
        "run_script",            # Execute pre-registered scripts
    ],
    RiskLevel.MEDIUM: [
        "run_xsoar_automation",  # Execute XSOAR commands (can do anything)
        "scan_endpoint",         # Can impact endpoint performance
    ],
    RiskLevel.LOW: [
        "unisolate_endpoint",    # Reversal of isolation
        "restore_file",          # Reversal of quarantine
        "abort_scan",            # Reversal of scan
    ],
}

# Map tool names to their reversal tools (if any)
REVERSAL_TOOLS: dict[str, Optional[str]] = {
    "isolate_endpoint": "unisolate_endpoint",
    "terminate_causality": None,  # No reversal - permanent
    "terminate_process": None,    # No reversal - permanent
    "quarantine_files": "restore_file",
    "run_snippet_code_script": None,  # No reversal - depends on script
    "run_script": None,               # No reversal - depends on script
    "run_xsoar_automation": None,     # No reversal - depends on command
    "scan_endpoint": "abort_scan",
    "unisolate_endpoint": "isolate_endpoint",
    "restore_file": "quarantine_files",
    "abort_scan": "scan_endpoint",
}


def get_risk_level(tool_name: str) -> Optional[RiskLevel]:
    """
    Get the risk level for a tool.

    Args:
        tool_name: Name of the tool to check

    Returns:
        RiskLevel if tool is destructive, None otherwise
    """
    for level, tools in DESTRUCTIVE_TOOLS.items():
        if tool_name in tools:
            return level
    return None


def is_destructive(tool_name: str) -> bool:
    """
    Check if a tool is considered destructive.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool is destructive (any risk level)
    """
    return get_risk_level(tool_name) is not None


def is_high_risk(tool_name: str) -> bool:
    """
    Check if a tool is HIGH risk (requires all safety layers).

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool is HIGH risk
    """
    return tool_name in DESTRUCTIVE_TOOLS[RiskLevel.HIGH]


def get_reversal_tool(tool_name: str) -> Optional[str]:
    """
    Get the reversal tool for a destructive action, if one exists.

    Args:
        tool_name: Name of the destructive tool

    Returns:
        Name of reversal tool, or None if action is permanent
    """
    return REVERSAL_TOOLS.get(tool_name)


def get_all_high_risk_tools() -> list[str]:
    """Get list of all HIGH risk tool names."""
    return DESTRUCTIVE_TOOLS[RiskLevel.HIGH].copy()


def get_all_destructive_tools() -> list[str]:
    """Get list of all destructive tool names (all risk levels)."""
    all_tools = []
    for tools in DESTRUCTIVE_TOOLS.values():
        all_tools.extend(tools)
    return all_tools


def generate_warning_prefix(tool_name: str) -> str:
    """
    Generate a warning prefix for a destructive tool's description.

    Args:
        tool_name: Name of the tool

    Returns:
        Warning string to prepend to description
    """
    risk_level = get_risk_level(tool_name)
    if not risk_level:
        return ""

    reversal = get_reversal_tool(tool_name)
    reversal_text = f"Use {reversal} to reverse" if reversal else "This action cannot be reversed"

    return f"""DESTRUCTIVE ACTION - Risk Level: {risk_level.value}
{reversal_text}.

"""
