#!/bin/bash
# Cortex Bot Tools - Installation Pack Creator
# This script creates a complete installation package for the 84 custom tools

set -e

PACK_NAME="cortex-bot-tools-v1.0"
PACK_DIR="${PACK_NAME}"

echo "Creating Cortex Bot Tools Installation Pack..."

# Clean up any previous pack
rm -rf "${PACK_DIR}" "${PACK_DIR}.tar.gz"

# Create pack directory structure
mkdir -p "${PACK_DIR}"

# Copy custom components
echo "Copying custom components..."
cp -r src/usecase/custom_components "${PACK_DIR}/"

# Copy installation guide
echo "Copying installation guide..."
cp INSTALL_CORTEX_BOT_TOOLS.md "${PACK_DIR}/"

# Copy main README for reference
echo "Copying README..."
cp README.md "${PACK_DIR}/"

# Create a file manifest
echo "Creating file manifest..."
cat > "${PACK_DIR}/MANIFEST.txt" << 'EOF'
Cortex Bot Tools Installation Pack
Version: 1.0
Created: $(date)

This package contains:
- 84 custom MCP tools for Cortex XSIAM
- Installation guide (INSTALL_CORTEX_BOT_TOOLS.md)
- Full README for reference
- All source files in custom_components/

File count:
EOF

# Add file counts to manifest
echo "  Python files: $(find "${PACK_DIR}/custom_components" -name "*.py" | wc -l)" >> "${PACK_DIR}/MANIFEST.txt"
echo "  OpenAPI files: $(find "${PACK_DIR}/custom_components" -name "*.yaml" -o -name "*.yml" | wc -l)" >> "${PACK_DIR}/MANIFEST.txt"
echo "  Total files: $(find "${PACK_DIR}/custom_components" -type f | wc -l)" >> "${PACK_DIR}/MANIFEST.txt"

# Create quick start file
echo "Creating quick start guide..."
cat > "${PACK_DIR}/QUICKSTART.txt" << 'EOF'
CORTEX BOT TOOLS - QUICK START
================================

PREREQUISITES:
✅ Official Cortex MCP Server installed and working (6 tools)
✅ Python 3.12+
✅ Claude Desktop or Claude Code configured

INSTALLATION (3 STEPS):
1. Find your official MCP installation:
   find / -name "main.py" -path "*/cortex-mcp/*" 2>/dev/null

2. Copy custom tools:
   cp -r custom_components/* /path/to/official-mcp/src/usecase/custom_components/

3. Restart MCP server:
   docker restart cortex-mcp
   # OR
   pkill -f "cortex-mcp.*main.py" && restart via client

VERIFY:
Open Claude and type: /mcp
Expected: "Connected to cortex-xsiam (90 tools)"

FULL INSTRUCTIONS:
See INSTALL_CORTEX_BOT_TOOLS.md

TROUBLESHOOTING:
If tools don't appear:
- Check file permissions: chmod -R 755 custom_components/
- Install dependencies: pip install fastmcp aiohttp requests
- View logs: LOG_LEVEL=DEBUG python /path/to/mcp/src/main.py
EOF

# Create a checksums file
echo "Creating checksums..."
cd "${PACK_DIR}"
find custom_components -type f -exec sha256sum {} \; > CHECKSUMS.txt
cd ..

# Create tarball
echo "Creating compressed archive..."
tar -czf "${PACK_DIR}.tar.gz" "${PACK_DIR}"

# Create a zip file as alternative
echo "Creating ZIP archive..."
zip -r "${PACK_DIR}.zip" "${PACK_DIR}" > /dev/null

# Final summary
echo ""
echo "✅ Installation pack created successfully!"
echo ""
echo "Created files:"
echo "  - ${PACK_DIR}.tar.gz (for Linux/Mac)"
echo "  - ${PACK_DIR}.zip (for Windows)"
echo ""
echo "Package contents:"
echo "  - 84 custom MCP tools"
echo "  - Installation guide"
echo "  - Quick start guide"
echo "  - Full README"
echo "  - File manifest"
echo "  - SHA256 checksums"
echo ""
echo "To distribute:"
echo "  1. Share ${PACK_DIR}.tar.gz or ${PACK_DIR}.zip"
echo "  2. Recipient extracts and follows INSTALL_CORTEX_BOT_TOOLS.md"
echo ""
echo "Archive sizes:"
ls -lh "${PACK_DIR}.tar.gz" "${PACK_DIR}.zip"
