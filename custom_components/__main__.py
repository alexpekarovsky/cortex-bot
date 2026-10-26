"""
Cortex Bot entry point — starts the official Cortex MCP server with custom tools loaded.

Usage:
    uvx cortex-bot                    # stdio transport (default, for MCP gateway)
    cortex-bot --transport http       # HTTP transport

Discovery order for the official CortexMCP server:
    1. CORTEX_MCP_SERVER_PATH env var (explicit path)
    2. 'src' package already on PYTHONPATH (pip installed CortexMCP)
    3. Common install locations (~/.cortex-mcp/src, ./src)
"""
import os
import sys
from pathlib import Path

SEARCH_PATHS = [
    Path.home() / ".cortex-mcp" / "src",
    Path.home() / "cortex-mcp" / "src",
    Path("/opt/cortex-mcp/src"),
    Path.cwd() / "src",
]


def find_server():
    explicit = os.environ.get("CORTEX_MCP_SERVER_PATH")
    if explicit:
        p = Path(explicit)
        if (p / "main.py").exists():
            return p
        if (p / "src" / "main.py").exists():
            return p / "src"

    try:
        from src.main import main as server_main
        return server_main
    except ImportError:
        pass

    for path in SEARCH_PATHS:
        if (path / "main.py").exists():
            return path

    return None


def main():
    result = find_server()

    if callable(result):
        result()
        return

    if isinstance(result, Path):
        sys.path.insert(0, str(result.parent))
        sys.path.insert(0, str(result))
        from src.main import main as server_main
        server_main()
        return

    print(
        "Error: Official Cortex MCP Server not found.\n\n"
        "Install options:\n"
        "  1. pip install CortexMCP\n"
        "  2. Set CORTEX_MCP_SERVER_PATH=/path/to/cortex-mcp\n"
        "  3. Place server at ~/.cortex-mcp/src/\n\n"
        "Download: https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
