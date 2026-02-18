#!/bin/bash
# Force clean environment startup for MCP server with env -i

cd /Users/apekarovsky/projects/cortex-mcp

# Start with COMPLETELY CLEAN environment using env -i
# Then load ONLY from .env file
exec env -i \
  HOME="$HOME" \
  PATH="/usr/local/bin:/usr/bin:/bin" \
  $(grep -v '^#' .env | xargs) \
  /Users/apekarovsky/projects/cortex-mcp/venv/bin/python /Users/apekarovsky/projects/cortex-mcp/src/main.py
