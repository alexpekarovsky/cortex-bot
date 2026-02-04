# R&D Enhancement Request: config.py Environment Variable Priority

## Problem

Shell environment variables override `.env` file values, making multi-tenant credential switching difficult.

**Current behavior:**
- User edits `.env` file with new tenant credentials
- Server still uses old credentials from shell environment variables
- Requires full application restart or manual `unset` commands

---

## Requested Change

**File:** `src/config/config.py`

**Add at top (lines 1-8):**
```python
from pathlib import Path
from dotenv import load_dotenv

env_file_path = Path(__file__).parent.parent.parent / ".env"
if env_file_path.exists():
    load_dotenv(env_file_path, override=True)
```

**Update SettingsConfigDict (line ~37):**
```python
model_config = SettingsConfigDict(
    env_file=".env",
    extra="ignore",
    env_nested_delimiter=None  # Prevents ${VAR:-default} parsing
)
```

---

## Impact

**Pros:**
- ✅ Simplified tenant switching (edit `.env`, reconnect)
- ✅ `.env` file becomes single source of truth
- ✅ Industry-standard pattern (dotenv override)
- ✅ Backward compatible

**Cons:**
- ⚠️ Changes env var priority order (minor breaking change)
- ⚠️ Requires `python-dotenv` dependency (likely already present)

---

## Dependency

```
python-dotenv>=1.0.0
```

---

**Submitted:** January 12, 2026
**Submitter:** Alex Pekarovsky (tilarium@gmail.com)
