# Installation Guide - Cortex Bot Custom Tools

Complete installation guide for adding 84 custom tools to your official Palo Alto Networks Cortex MCP Server.

**Tested and verified:** This procedure successfully installed all 90 tools with 100% success rate.

---

## Prerequisites

Before you begin, verify you have:

### Required

| Requirement | Version | Verification Command | Where to Get |
|-------------|---------|---------------------|--------------|
| **Official PANW Cortex MCP Server** | Latest | Check Claude shows 6 base tools | [PANW Installation Guide](https://docs-cortex.paloaltonetworks.com/r/Cortex/Cortex-MCP-server/Create-custom-Cortex-MCP-server-tools) |
| **Python** | 3.12+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Git** | Any | `git --version` | [git-scm.com](https://git-scm.com/) |
| **Cortex XSIAM API Credentials** | N/A | See below | [XSIAM API Guide](https://docs-cortex.paloaltonetworks.com/r/Cortex-XSIAM/Cortex-XSIAM-Administrator-Guide/Get-Started-with-APIs) |

### Verify Official MCP Server is Working

```bash
# Open Claude Desktop or Claude Code
# Type: "List all MCP tools"

# Expected output:
Connected to cortex-xsiam (6 tools)
- get_cases
- get_issues
- get_assets
- get_filtered_endpoints
- get_assessment_profile_results
- get_vulnerabilities
```

✅ **If you see 6 tools, proceed to installation.**
❌ **If not, install official PANW MCP server first.**

---

## Installation Steps

### Step 1: Download Custom Tools Package

**Option A: From GitHub Release**
```bash
# Download the latest release
wget https://github.com/alexpekarovsky/cortex-bot/releases/latest/download/cortex-bot.zip

# Extract
unzip cortex-bot.zip
cd cortex-bot
```

**Option B: Clone Repository**
```bash
# Clone from GitHub
git clone https://github.com/alexpekarovsky/cortex-bot.git
cd cortex-bot
```

**Expected after extraction:**
```
cortex-bot/
├── README.md
├── LICENSE
├── .env.example
├── pyproject.toml
├── .gitignore
└── custom_components/
    ├── __init__.py
    ├── *.py (28 Python tools)
    └── openapi/*.yaml (25 YAML tools)
```

✅ **Verify:** `ls -la custom_components/*.py | wc -l` should show **28 files**

---

### Step 2: Locate Your Official MCP Installation

Find where the official PANW Cortex MCP server is installed:

```bash
# Common installation locations:
# - Poetry: ~/cortex-mcp or ~/.local/share/cortex-mcp
# - Docker: /opt/cortex-mcp
# - Manual: wherever you extracted it

# Search for it:
find ~ -name "cortex*mcp" -type d 2>/dev/null | grep -v ".claude\|venv\|__pycache__"
```

**Expected output:**
```
/Users/yourname/cortex-mcp
```

**Verify it's the right directory:**
```bash
ls /path/to/cortex-mcp/src/main.py
```

✅ **Should exist** - this confirms you found the MCP server

---

### Step 3: Copy Custom Tools

```bash
# Copy custom_components folder to official installation
cp -r custom_components/* /path/to/cortex-mcp/src/usecase/custom_components/

# Example for typical Poetry installation:
# cp -r custom_components/* ~/cortex-mcp/src/usecase/custom_components/
```

**Expected output:**
```
(No output if successful, or list of files copied)
```

**Verify files were copied:**
```bash
ls /path/to/cortex-mcp/src/usecase/custom_components/*.py | wc -l
```

✅ **Should show: 28** (or more if PANW adds built-in custom tools)

```bash
ls /path/to/cortex-mcp/src/usecase/custom_components/openapi/*.yaml | wc -l
```

✅ **Should show: 25** (or more)

**Troubleshooting:**

❌ **"No such file or directory: .../custom_components"**
- The official MCP installation might not have this directory yet
- Create it: `mkdir -p /path/to/cortex-mcp/src/usecase/custom_components`
- Then retry the copy command

❌ **"Permission denied"**
- You may need elevated permissions
- Try: `sudo cp -r custom_components/* ...`
- Or: `chmod -R u+w /path/to/cortex-mcp/src/usecase/`

---

### Step 4: Restart MCP Server

The MCP server needs to reload to discover the new tools.

**For Poetry/Manual Installation:**
```bash
# Kill the running server (it will auto-restart)
pkill -f "cortex.*main.py"

# Wait 2-3 seconds for restart
sleep 3

# Verify it's running again
ps aux | grep "cortex.*main.py" | grep -v grep
```

✅ **Expected:** Should see the Python process running

**For Docker Installation:**
```bash
# Restart the container
docker restart cortex-mcp

# Verify it's running
docker ps | grep cortex-mcp
```

✅ **Expected:** Container shows as "Up" status

**Troubleshooting:**

❌ **Server doesn't restart automatically**
- Manually start it:
  ```bash
  cd /path/to/cortex-mcp
  source venv/bin/activate  # If using Poetry
  python src/main.py
  ```

❌ **Import errors in logs**
- Check the log file: `tail -50 /path/to/cortex-mcp/cortex-mcp.log`
- Common issue: Missing dependencies
- Solution: Reinstall in the official MCP directory

---

### Step 5: Verify Installation

Open Claude Desktop or Claude Code and reconnect to the MCP server.

**In Claude, type:**
```
List all available cortex-xsiam MCP tools
```

**Expected output:**
```
Connected to cortex-xsiam (90 tools)

The following 90 tools are available:

Case Management (5 tools):
- get_cases
- get_incident_extra_data
- update_incident
- update_case_ai_summary
- update_case_timeline

Issue Management (4 tools):
- get_issues
- get_alert_multi_events
- get_contributing_events
- update_issue

... (continues with all 90 tools)
```

✅ **Success:** You see **90 tools** (6 base + 84 custom)
❌ **Problem:** You see only 6 tools (custom tools didn't load)

**If only 6 tools appear:**

1. **Check files were copied:**
   ```bash
   ls -la /path/to/cortex-mcp/src/usecase/custom_components/ | grep -E "\.py$|\.yaml$"
   ```
   Should see 53+ files

2. **Check for import errors:**
   ```bash
   tail -100 /path/to/cortex-mcp/cortex-mcp.log | grep -i error
   ```

3. **Verify Python version:**
   ```bash
   cd /path/to/cortex-mcp
   source venv/bin/activate
   python --version  # Should be 3.12 or higher
   ```

4. **Reinstall dependencies:**
   ```bash
   cd /path/to/cortex-mcp
   source venv/bin/activate
   poetry install  # or pip install -r requirements.txt
   ```

---

## Step 6: Test Basic Functionality

Verify the tools work by testing each category:

### Test 1: Case Management
```
Ask Claude: "Show me all my XSIAM cases from the last 7 days"
```

✅ **Expected:** List of cases with IDs, severities, and descriptions
❌ **If fails:** Check API credentials are configured

### Test 2: Threat Hunting
```
Ask Claude: "Run an XQL query to find all process events in the last hour"
```

✅ **Expected:** XQL query executes and returns results
❌ **If fails:** Verify XSIAM API connection

### Test 3: Enrichment
```
Ask Claude: "Enrich IP address 8.8.8.8"
```

✅ **Expected:** IP reputation data from threat intelligence sources
❌ **If fails:** Check threat intel integrations are configured in XSIAM

### Test 4: Response Actions
```
Ask Claude: "List all my endpoints"
```

✅ **Expected:** List of endpoints with hostnames, IPs, and status
❌ **If fails:** Check API permissions include endpoint read access

### Test 5: SDK Tools (If SDK Installed)
```
Ask Claude: "List available XSOAR integration scripts"
```

✅ **Expected:** List of scripts from script library
❌ **If fails:** demisto-sdk not installed (see Step 7 below)

---

## Step 7: Install Demisto SDK (REQUIRED)

**MANDATORY:** The following 10 SDK tools will NOT work without demisto-sdk:
- sdk_upload, sdk_validate, sdk_lint
- sdk_init, sdk_download, sdk_run
- sdk_run_playbook, sdk_generate_docs
- sdk_split, sdk_unify

**Install demisto-sdk now.** The other 80 tools work without it, but you'll want SDK tools for creating/uploading content.

SDK tools **automatically use your MCP credentials** - no separate configuration needed.

### Step 7.1: Choose Installation Method

**Method A: Using uvx (Recommended)**

Install uv package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
which uvx
# Expected: /Users/yourname/.cargo/bin/uvx

uvx demisto-sdk --version
# Expected: demisto-sdk 1.x.x
```

**Method B: Direct Installation**

Install demisto-sdk directly:
```bash
pip3 install demisto-sdk
demisto-sdk --version
# Expected: demisto-sdk 1.x.x
```

**Note:** Requires Python 3.9-3.12. May conflict with MCP's Python 3.12+. Method A (uvx) handles this automatically.

### Step 7.2: Setup Content Repository

Create content directory (REQUIRED):
```bash
mkdir -p ~/content/Packs
```

Or use custom location:
```bash
export CONTENT_PATH=/your/custom/path
mkdir -p $CONTENT_PATH/Packs
```

### Step 7.3: Test SDK Tools

In Claude:
```
Ask Claude: "List available XSOAR scripts"
```

✅ **Expected:** List of scripts from script library
❌ **If fails:** Run `which uvx` or `demisto-sdk --version` to verify installation

---

## Installation Success Checklist

Before considering installation complete, verify:

- [ ] **90 tools visible** in Claude (not 6)
- [ ] **Can list cases** without authentication errors
- [ ] **Can run XQL queries** and get results
- [ ] **Enrichment works** (test with known good IP like 8.8.8.8)
- [ ] **Can list endpoints** in your environment
- [ ] **SDK tools respond** (at minimum, list scripts works)
- [ ] **No import errors** in MCP server logs

**If all checked:** 🎉 Installation successful! You're ready to use all 90 tools.

---

## Common Issues and Solutions

### Issue: "Only 6 tools appear, not 90"

**Cause:** Custom tools didn't load

**Solution:**
1. Verify files were copied:
   ```bash
   ls /path/to/cortex-mcp/src/usecase/custom_components/*.py
   ```
   Should see 28 Python files

2. Check MCP server logs for errors:
   ```bash
   tail -100 /path/to/cortex-mcp/cortex-mcp.log
   ```

3. Restart MCP server:
   ```bash
   pkill -f cortex.*main.py
   ```

### Issue: "401 Unauthorized" errors

**Cause:** API credentials not configured or incorrect

**Solution:**
1. Check credentials file exists:
   ```bash
   cat /path/to/cortex-mcp/.env | grep CORTEX_MCP_PAPI
   ```

2. Verify credentials are correct in your XSIAM tenant

3. Restart MCP server after updating credentials

### Issue: "Module import errors"

**Cause:** Dependencies not installed or wrong Python version

**Solution:**
```bash
cd /path/to/cortex-mcp
source venv/bin/activate
python --version  # Should be 3.12+
poetry install  # Reinstall dependencies
pkill -f cortex.*main.py  # Restart
```

### Issue: "SDK tools don't work"

**Cause:** uv package manager not installed

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
which uvx
# Should show: /Users/yourname/.cargo/bin/uvx

# Retry SDK command in Claude
```

### Issue: "Cannot find MCP installation directory"

**Cause:** Unclear where PANW MCP was installed

**Solution:**
```bash
# Search for it
find ~ -name "main.py" -path "*/cortex*/src/main.py" 2>/dev/null

# Check common locations:
ls ~/cortex-mcp/src/main.py 2>/dev/null
ls ~/.local/share/cortex-mcp/src/main.py 2>/dev/null
ls /opt/cortex-mcp/src/main.py 2>/dev/null

# If installed via Docker:
docker ps | grep cortex
# Then: docker exec -it cortex-mcp ls /app/src/main.py
```

---

## Next Steps

Once installation is complete:

1. **Explore the tools:**
   ```
   Ask Claude: "What can you do with these XSIAM tools?"
   ```

2. **Try a real task:**
   ```
   "Investigate case 123 and generate an AI summary"
   "Hunt for PowerShell execution on domain controllers"
   "Create a phishing investigation playbook"
   ```

3. **Review documentation:**
   - See `README.md` for complete tool reference
   - See `README.md` for use cases and examples
   - See `README.md` for architecture and FAQ

4. **Join the community:**
   - Report issues on GitHub
   - Contribute new tools
   - Share your use cases

---

## Quick Reference

**Installation Summary:**
```bash
# 1. Download/clone
git clone https://github.com/alexpekarovsky/cortex-bot.git

# 2. Copy
cp -r custom_components/* ~/cortex-mcp/src/usecase/custom_components/

# 3. Restart
pkill -f cortex.*main.py

# 4. Verify
# In Claude: "List all tools"
# Should see: 90 tools
```

**Success Criteria:**
- 90 tools visible
- Can list cases
- Can run XQL queries
- Enrichment works
- SDK tools respond

**Get Help:**
- GitHub Issues: [link]
- Documentation: README.md
- PANW Support: [PANW Docs](https://docs-cortex.paloaltonetworks.com/)

---

**Estimated installation time:** 5-10 minutes

**Difficulty:** Easy (if official PANW MCP is already working)
