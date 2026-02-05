# Instructions for LLM: Installing Cortex Bot Tools

## Context

You are being given an installation package containing **84 custom MCP tools** that extend the official Palo Alto Networks Cortex MCP Server from 6 base tools to 90 total tools.

## Your Task

Install these custom tools into an existing official Cortex MCP Server installation.

## Package Contents

The archive contains:
- `custom_components/` - Directory with 84 custom tools (Python + OpenAPI YAML files)
- `INSTALL_CORTEX_BOT_TOOLS.md` - Complete installation guide
- `QUICKSTART.txt` - Quick reference
- `README.md` - Full project documentation
- `MANIFEST.txt` - File inventory
- `CHECKSUMS.txt` - SHA256 checksums for verification

## Installation Steps

### 1. Verify Prerequisites

Before starting, confirm:
- ✅ Official Cortex MCP Server is installed and working
- ✅ User can see 6 base tools when checking `/mcp`
- ✅ Python 3.12+ is installed
- ✅ User has access to the official MCP installation directory

### 2. Extract the Package

```bash
# For .tar.gz (Linux/Mac):
tar -xzf cortex-bot-tools-v1.0.tar.gz
cd cortex-bot-tools-v1.0

# For .zip (Windows):
unzip cortex-bot-tools-v1.0.zip
cd cortex-bot-tools-v1.0
```

### 3. Locate Official MCP Installation

Help the user find their official MCP installation:

```bash
# Common locations:
# - Docker: /opt/cortex-mcp/ or /usr/local/cortex-mcp/
# - Poetry: ~/.local/share/cortex-mcp/
# - Manual: wherever extracted

# Search command:
find / -name "main.py" -path "*/cortex-mcp/*" 2>/dev/null
```

### 4. Copy Custom Components

```bash
# Copy the custom_components directory to the official installation
cp -r custom_components/* /path/to/official-mcp/src/usecase/custom_components/

# Verify files were copied:
ls -la /path/to/official-mcp/src/usecase/custom_components/
```

### 5. Install Python Dependencies

```bash
# Navigate to official MCP directory
cd /path/to/official-mcp

# Install required packages
pip install fastmcp==0.4.0 aiohttp requests python-dotenv pydantic

# Or with Poetry:
poetry add fastmcp==0.4.0 aiohttp requests python-dotenv pydantic
```

### 6. Restart MCP Server

```bash
# For Docker:
docker restart cortex-mcp

# For Poetry/manual:
pkill -f "cortex-mcp.*main.py"
# Then restart via MCP client (Claude Desktop/Code)
```

### 7. Verify Installation

In the MCP client:
```
User types: /mcp
Expected output: "Connected to cortex-xsiam (90 tools)"
```

**Success criteria:** User should see **90 tools** (6 official + 84 custom)

## Troubleshooting

### Problem: Still only seeing 6 tools

**Solutions to try:**
1. Verify files copied correctly:
   ```bash
   ls -la /path/to/official-mcp/src/usecase/custom_components/
   ```

2. Check file permissions:
   ```bash
   chmod -R 755 /path/to/official-mcp/src/usecase/custom_components/
   ```

3. Verify Python dependencies:
   ```bash
   pip list | grep -E "fastmcp|aiohttp|pydantic"
   ```

4. Check for import errors:
   ```bash
   cd /path/to/official-mcp
   python -c "from usecase.custom_components import *"
   ```

5. Restart with debug logging:
   ```bash
   LOG_LEVEL=DEBUG python /path/to/official-mcp/src/main.py
   ```

### Problem: Import errors or module not found

**Solution:**
```bash
# Install missing dependencies
pip install fastmcp aiohttp requests python-dotenv pydantic

# Verify Python version (must be 3.12+)
python --version
```

### Problem: Permission denied errors

**Solution:**
```bash
# Fix ownership and permissions
sudo chown -R $USER /path/to/official-mcp/src/usecase/custom_components/
chmod -R 755 /path/to/official-mcp/src/usecase/custom_components/
```

## What You're Installing

The 84 custom tools include:

**Advanced Investigation (4 tools):**
- AI-powered case summaries
- Visual timeline generation
- Deep forensic analysis
- Correlation event breakdown

**Threat Hunting (6 tools):**
- XQL query execution
- Detection rule creation
- IOC enrichment (IP, domain, file, URL)

**Response Actions (11 tools):**
- Endpoint isolation
- Process termination
- File quarantine
- Malware scanning

**XSOAR Development (10 SDK tools):**
- Content creation and validation
- Integration development
- Playbook testing

**Development Guides (9 tools):**
- Integration pattern recognition
- Implementation guides
- Best practices

**And 44 more tools** for playbook automation, content generation, widget management, script execution, and more.

See `INSTALL_CORTEX_BOT_TOOLS.md` for the complete list.

## Testing the Installation

Once installed, test with these prompts:

```
"How many MCP tools are available?"
Expected: "90 tools"

"Generate an AI summary for case 350"
Expected: Tool executes (may fail if case doesn't exist, but tool should be available)

"Run test_all_tools in safe mode"
Expected: Comprehensive test of all 90 tools
```

## Important Notes

1. **Do NOT modify the official Cortex MCP Server files** - only add to the `custom_components` directory
2. **The official 6 tools remain unchanged** - we're only adding 84 new ones
3. **All credentials remain in the official MCP configuration** - no changes needed
4. **The installation is reversible** - delete the custom_components directory to remove

## Success Indicators

✅ User sees 90 tools in MCP client
✅ Can execute custom tools (e.g., "create an AI summary")
✅ No import errors in logs
✅ Official 6 tools still work normally

## Reference Documentation

Full details in:
- `INSTALL_CORTEX_BOT_TOOLS.md` - Complete installation guide
- `README.md` - Full project documentation with all tool descriptions
- `QUICKSTART.txt` - Quick reference card

---

**Your goal:** Successfully install the 84 custom tools so the user has 90 total tools available in their Cortex MCP Server.
