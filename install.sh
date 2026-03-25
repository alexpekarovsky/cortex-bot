#!/bin/bash
#
# Cortex Bot Custom Tools - Installation Script
#
# SECURITY NOTE: Review this script before running!
# This script copies custom MCP tools to your official PANW Cortex MCP installation.
#
# What this script does:
# 1. Locates your PANW MCP installation directory
# 2. Verifies the installation is valid
# 3. Copies custom_components/ folder
# 4. Verifies files were copied correctly
# 5. Restarts the MCP server
# 6. Reports installation status
#
# NO network requests, NO sudo required, NO hidden operations
#
# Usage:
#   ./install.sh
#   or
#   ./install.sh /path/to/your/cortex-mcp
#

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Cortex Bot Custom Tools - Installation                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Locate PANW MCP installation
echo "Step 1: Locating PANW Cortex MCP installation..."

if [ -n "$1" ]; then
    MCP_PATH="$1"
    echo "  Using provided path: $MCP_PATH"
else
    # Auto-detect MCP installation
    MCP_MAIN=$(find ~ -path "*/cortex*/src/main.py" -type f 2>/dev/null | grep -v ".venv\|venv\|__pycache__" | head -1)

    if [ -z "$MCP_MAIN" ]; then
        echo -e "${RED}✗ Could not find PANW MCP installation${NC}"
        echo ""
        echo "Please install the official PANW Cortex MCP Server first:"
        echo "  https://docs-cortex.paloaltonetworks.com/"
        echo ""
        echo "Or provide the path manually:"
        echo "  ./install.sh /path/to/cortex-mcp"
        exit 1
    fi

    MCP_PATH=$(dirname "$(dirname "$MCP_MAIN")")
    echo -e "  ${GREEN}✓ Found MCP at: $MCP_PATH${NC}"
fi

# Step 2: Verify MCP installation
echo ""
echo "Step 2: Verifying PANW MCP installation..."

if [ ! -f "$MCP_PATH/src/main.py" ]; then
    echo -e "${RED}✗ Invalid MCP path: src/main.py not found${NC}"
    exit 1
fi

if [ ! -d "$MCP_PATH/src/usecase" ]; then
    echo -e "${RED}✗ Invalid MCP path: src/usecase directory not found${NC}"
    exit 1
fi

echo -e "  ${GREEN}✓ Valid PANW MCP installation${NC}"

# Step 3: Create custom_components directory if it doesn't exist
echo ""
echo "Step 3: Preparing custom_components directory..."

CUSTOM_DIR="$MCP_PATH/src/usecase/custom_components"

if [ ! -d "$CUSTOM_DIR" ]; then
    mkdir -p "$CUSTOM_DIR"
    echo -e "  ${GREEN}✓ Created custom_components directory${NC}"
else
    echo -e "  ${GREEN}✓ custom_components directory exists${NC}"
fi

# Step 4: Copy custom tools
echo ""
echo "Step 4: Copying custom tools..."

if [ ! -d "custom_components" ]; then
    echo -e "${RED}✗ custom_components directory not found in current directory${NC}"
    echo ""
    echo "Please run this script from the cortex-bot-custom-tools directory:"
    echo "  cd cortex-bot-custom-tools"
    echo "  ./install.sh"
    exit 1
fi

# Count files before copying
PYTHON_FILES=$(find custom_components -name "*.py" -type f | wc -l | tr -d ' ')
YAML_FILES=$(find custom_components -name "*.yaml" -type f | wc -l | tr -d ' ')

echo "  Copying $PYTHON_FILES Python files and $YAML_FILES YAML files..."

cp -r custom_components/* "$CUSTOM_DIR/"

# Step 5: Verify files were copied
echo ""
echo "Step 5: Verifying installation..."

COPIED_PYTHON=$(find "$CUSTOM_DIR" -maxdepth 1 -name "*.py" -type f | wc -l | tr -d ' ')
COPIED_YAML=$(find "$CUSTOM_DIR/openapi" -name "*.yaml" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "  Python files copied: $COPIED_PYTHON (expected: 28)"
echo "  YAML files copied: $COPIED_YAML (expected: 25)"

if [ "$COPIED_PYTHON" -ge 28 ] && [ "$COPIED_YAML" -ge 25 ]; then
    echo -e "  ${GREEN}✓ All files copied successfully${NC}"
else
    echo -e "  ${YELLOW}⚠ File count mismatch - some files may not have copied${NC}"
fi

# Step 6: Restart MCP server
echo ""
echo "Step 6: Restarting MCP server..."

if pgrep -f "cortex.*main.py" > /dev/null; then
    pkill -f "cortex.*main.py"
    echo -e "  ${GREEN}✓ MCP server process stopped${NC}"
    echo "  (Server will auto-restart when you open Claude)"
else
    echo "  MCP server not currently running (will start when needed)"
fi

# Success message
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Open Claude Desktop or Claude Code"
echo "  2. Reconnect to MCP server (if needed): /mcp"
echo "  3. Verify tools loaded:"
echo "     - Type: /mcp"
echo "     - Expected: Connected to cortex-xsiam (90 tools)"
echo ""
echo "  4. Test a tool:"
echo "     - Ask Claude: 'Show me my top 5 XSIAM cases'"
echo ""
echo "If you see 90 tools, installation was successful! ✅"
echo ""
echo "If you see only 6 tools, check the troubleshooting guide in INSTALL.md"
echo ""
