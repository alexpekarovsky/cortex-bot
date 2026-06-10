"""
Destructive Tools Gate

Enforces the ENABLE_DESTRUCTIVE_TOOLS environment variable documented in
README.md, SECURITY.md and .env.example. When the flag is not explicitly
enabled, destructive tools (endpoint isolation, process termination, file
quarantine, blocklist/allowlist changes, script execution) are not
registered with the MCP server at all, so the LLM can never call them.
"""

import logging
import os

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}


def destructive_tools_enabled() -> bool:
    """True only when ENABLE_DESTRUCTIVE_TOOLS is explicitly enabled (default: disabled)."""
    return os.getenv("ENABLE_DESTRUCTIVE_TOOLS", "false").strip().lower() in _TRUE_VALUES


def register_destructive(module, *tools) -> None:
    """Register destructive tools on a module only if the flag allows it.

    When disabled, logs which tools were withheld so operators can see why
    they are missing from the tool list.
    """
    if destructive_tools_enabled():
        for tool in tools:
            module._add_tool(tool)
        return

    skipped = ", ".join(getattr(t, "__name__", str(t)) for t in tools)
    logger.warning(
        "ENABLE_DESTRUCTIVE_TOOLS is disabled — not registering: %s "
        "(set ENABLE_DESTRUCTIVE_TOOLS=true in .env to enable)",
        skipped,
    )
