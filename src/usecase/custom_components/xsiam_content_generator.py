"""
XSIAM Content Generator Tools

Tools for creating XSIAM-specific content types with correct schemas.
Auto-saves to $CONTENT_REPO/{PackName}/ (default: ~/content/Packs/)

Supported content types:
- CaseLayout: UI layout for Cases (group: "case")
- CaseField: Custom fields for Cases
- CaseLayoutRule: Layout routing rules
- ParsingRule: Log parsing rules (YML + XIF)
- ModelingRule: XDM field mapping (YML + XIF)
- AssetsModelingRule: Asset data modeling (YML + XIF)
- XSIAMDashboard: XSIAM-specific dashboards
- XSIAMReport: XSIAM-specific reports
- AgentIXAction: AI-accessible actions wrapping XSOAR content
- AgentIXAgent: AI assistant configurations

Note: CorrelationRule is NOT included - use insert_correlation_rule API tool instead.
"""

import json
import logging
import os
import re
import subprocess
import yaml
from pathlib import Path
from typing import Annotated, Optional, List

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

# Path to .env file for SDK credentials - use env var or fall back to default
ENV_FILE = os.path.expanduser(os.getenv("CORTEX_MCP_ENV_FILE", "~/.cortex-mcp/.env"))

# Default content repository path - use env var or fall back to default
CONTENT_REPO = os.path.expanduser(os.getenv("CONTENT_REPO", "~/content/Packs"))

# Directory names for each content type
CONTENT_DIRS = {
    "CaseLayout": "CaseLayouts",
    "CaseField": "CaseFields",
    "CaseLayoutRule": "CaseLayoutRules",
    "ParsingRule": "ParsingRules",
    "ModelingRule": "ModelingRules",
    "AssetsModelingRule": "AssetsModelingRules",
    "XSIAMDashboard": "XSIAMDashboards",
    "XSIAMReport": "XSIAMReports",
    "AgentIXAction": "AgentixActions",
    "AgentIXAgent": "AgentixAgents",
}

# File prefixes for each content type
FILE_PREFIXES = {
    "CaseLayout": "layoutscontainer-",
    "CaseField": "casefield-",
    "CaseLayoutRule": "caselayoutrule-",
    "XSIAMDashboard": "xsiamdashboard-",
    "XSIAMReport": "xsiamreport-",
}

# Default tabs for CaseLayout
DEFAULT_CASE_TABS = [
    {"id": "overview", "name": "Overview", "type": "overview"},
    {"id": "assets_and_artifacts", "name": "Key Assets & Artifacts", "type": "assets_and_artifacts"},
    {"id": "alerts_and_insights", "name": "Alerts & Insights", "type": "alerts_and_insights"},
    {"id": "timeline", "name": "Timeline", "type": "timeline"},
    {"id": "war_room", "name": "War Room", "type": "war_room"},
    {"id": "executions", "name": "Executions", "type": "executions"},
]


def run_sdk_upload(path: str, use_zip: bool = False) -> dict:
    """
    Run demisto-sdk upload command for a content item or pack.

    Args:
        path: Path to the content item or pack to upload.
        use_zip: If True, use -z flag for pack upload.

    Returns:
        dict with success status and output/error.
    """
    try:
        # Build the command
        cmd = f'''source {ENV_FILE} && \
export DEMISTO_BASE_URL="$CORTEX_MCP_PAPI_URL" \
DEMISTO_API_KEY="$CORTEX_MCP_PAPI_AUTH_HEADER" \
XSIAM_AUTH_ID="$CORTEX_MCP_PAPI_AUTH_ID" && \
DEMISTO_SDK_IGNORE_CONTENT_WARNING=1 uvx demisto-sdk upload -i {path} --marketplace marketplacev2'''

        if use_zip:
            cmd += ' -z'

        result = subprocess.run(
            ['bash', '-c', cmd],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=CONTENT_REPO
        )

        # Combine stdout and stderr
        output = result.stdout + result.stderr

        # Check for explicit success/failure markers in output
        if "SUCCESSFUL UPLOADS" in output and "FAILED UPLOADS" not in output:
            return {
                "uploaded": True,
                "message": "Upload successful"
            }
        elif "FAILED UPLOADS" in output:
            # Extract the error message from the output
            error_start = output.find("FAILED UPLOADS")
            error_section = output[error_start:error_start+500] if error_start != -1 else output[-500:]
            return {
                "uploaded": False,
                "error": error_section
            }
        elif result.returncode == 0:
            return {
                "uploaded": True,
                "message": "Upload completed"
            }
        else:
            return {
                "uploaded": False,
                "error": output[-500:] if len(output) > 500 else output
            }
    except subprocess.TimeoutExpired:
        return {"uploaded": False, "error": "Upload timed out after 120 seconds"}
    except Exception as e:
        return {"uploaded": False, "error": str(e)}


def sanitize_name(name: str) -> str:
    """Sanitize name for use in file paths and IDs."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.replace(' ', '_'))


def ensure_pack_exists(pack_name: str) -> Path:
    """
    Create pack directory with pack_metadata.json if it doesn't exist.

    Returns:
        Path to the pack directory.
    """
    pack_path = Path(CONTENT_REPO) / pack_name

    if not pack_path.exists():
        pack_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created pack directory: {pack_path}")

        # Create pack_metadata.json (minimal format with agentix support)
        metadata = {
            "name": pack_name,
            "description": f"Content pack: {pack_name}",
            "support": "community",
            "currentVersion": "1.0.0",
            "author": "MCP Content Generator",
            "categories": ["Utilities"],
            "tags": [],
            "useCases": [],
            "keywords": [],
            "supportedModules": ["xsiam", "agentix"]
        }
        metadata_path = pack_path / "pack_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        logger.info(f"Created pack_metadata.json: {metadata_path}")

        # Create required files
        (pack_path / ".pack-ignore").touch()
        (pack_path / ".secrets-ignore").touch()
        (pack_path / "README.md").write_text(f"# {pack_name}\n\nGenerated by XSIAM Content Generator.\n")

    return pack_path


def ensure_content_dir(pack_path: Path, content_type: str) -> Path:
    """
    Create content type directory if it doesn't exist.

    Args:
        pack_path: Path to the pack directory.
        content_type: Type of content (e.g., "CaseLayout").

    Returns:
        Path to the content type directory.
    """
    dir_name = CONTENT_DIRS.get(content_type, content_type)
    content_dir = pack_path / dir_name
    content_dir.mkdir(parents=True, exist_ok=True)
    return content_dir


# =============================================================================
# TOOL: create_case_layout
# =============================================================================

async def create_case_layout(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the layout in")],
    layout_name: Annotated[str, Field(description="Name of the case layout")],
    description: Annotated[Optional[str], Field(description="Description of the layout")] = None,
    tabs: Annotated[Optional[str], Field(description="JSON array of tab definitions. Each tab has: id, name, type. Default includes overview, war_room, etc.")] = None,
    upload: Annotated[bool, Field(description="If True, upload to XSIAM after creation")] = False,
) -> str:
    """
    Creates a CaseLayout JSON file for XSIAM.

    CaseLayouts define the UI structure for viewing Cases in XSIAM.
    The key differentiator from incident layouts is "group": "case".

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack (e.g., "MyPack").
        layout_name: Display name for the layout.
        description: Optional description.
        tabs: Optional JSON array of tab definitions.
        upload: If True, automatically upload to XSIAM.

    Returns:
        JSON response with file path and content.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "CaseLayout")

        # Parse tabs if provided
        tab_list = DEFAULT_CASE_TABS
        if tabs:
            try:
                tab_list = json.loads(tabs)
            except json.JSONDecodeError:
                return create_response(
                    data={"error": "Invalid JSON for tabs parameter"},
                    is_error=True
                )

        layout_id = sanitize_name(layout_name)

        layout_data = {
            "description": description or f"Case layout: {layout_name}",
            "detailsV2": {
                "tabs": tab_list
            },
            "group": "case",  # KEY: This makes it a CaseLayout
            "id": layout_name,
            "name": layout_name,
            "system": False,
            "version": -1,
            "fromVersion": "8.7.0",
            "marketplaces": ["marketplacev2"]
        }

        file_name = f"{FILE_PREFIXES['CaseLayout']}{layout_id}.json"
        file_path = content_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(layout_data, f, indent=4)

        logger.info(f"Created CaseLayout: {file_path}")

        result = {
            "success": True,
            "content_type": "CaseLayout",
            "file_path": str(file_path),
            "layout_name": layout_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(str(file_path))
            result["upload"] = upload_result
        else:
            result["upload_command"] = f"demisto-sdk upload -i {file_path} --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create CaseLayout: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_case_field
# =============================================================================

async def create_case_field(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the field in")],
    field_id: Annotated[str, Field(description="Unique ID for the field (lowercase, no spaces)")],
    field_name: Annotated[str, Field(description="Display name for the field")],
    field_type: Annotated[str, Field(description="Field type: shortText, longText, number, date, boolean, singleSelect, multiSelect, grid")] = "shortText",
    description: Annotated[Optional[str], Field(description="Description of the field")] = None,
    select_values: Annotated[Optional[str], Field(description="JSON array of values for singleSelect/multiSelect fields")] = None,
    upload: Annotated[bool, Field(description="If True, upload to XSIAM after creation")] = False,
) -> str:
    """
    Creates a CaseField JSON file for XSIAM.

    CaseFields are custom fields that appear on Cases. They replace IncidentFields
    in the XSIAM world. Use "marketplacev2" marketplace.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        field_id: Unique identifier (will be used as cliName).
        field_name: Display name.
        field_type: Type of field.
        description: Optional description.
        select_values: JSON array for select fields.

    Returns:
        JSON response with file path and content.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "CaseField")

        # Sanitize field_id
        clean_field_id = sanitize_name(field_id).lower()

        # Valid field types
        valid_types = ["shortText", "longText", "number", "date", "boolean",
                       "singleSelect", "multiSelect", "grid", "html", "markdown"]
        if field_type not in valid_types:
            return create_response(
                data={"error": f"Invalid field_type. Must be one of: {valid_types}"},
                is_error=True
            )

        field_data = {
            "id": clean_field_id,
            "name": field_name,
            "cliName": clean_field_id,
            "type": field_type,
            "description": description or f"Custom case field: {field_name}",
            "group": 0,
            "hidden": False,
            "required": False,
            "isReadOnly": False,
            "system": False,
            "associatedToAll": True,
            "version": -1,
            "fromVersion": "8.7.0",
            "marketplaces": ["marketplacev2"]
        }

        # Add select values if provided
        if select_values and field_type in ["singleSelect", "multiSelect"]:
            try:
                field_data["selectValues"] = json.loads(select_values)
            except json.JSONDecodeError:
                return create_response(
                    data={"error": "Invalid JSON for select_values parameter"},
                    is_error=True
                )

        file_name = f"{FILE_PREFIXES['CaseField']}{clean_field_id}.json"
        file_path = content_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(field_data, f, indent=4)

        logger.info(f"Created CaseField: {file_path}")

        result = {
            "success": True,
            "content_type": "CaseField",
            "file_path": str(file_path),
            "field_id": clean_field_id,
            "field_name": field_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(str(file_path))
            result["upload"] = upload_result
        else:
            result["upload_command"] = f"demisto-sdk upload -i {file_path} --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create CaseField: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_case_layout_rule
# =============================================================================

async def create_case_layout_rule(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the rule in")],
    rule_name: Annotated[str, Field(description="Name of the layout rule")],
    layout_id: Annotated[str, Field(description="ID of the CaseLayout to apply")],
    description: Annotated[Optional[str], Field(description="Description of the rule")] = None,
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates a CaseLayoutRule JSON file for XSIAM.

    CaseLayoutRules determine which CaseLayout to use based on conditions.
    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        rule_name: Name of the rule.
        layout_id: ID of the target CaseLayout.
        description: Optional description.

    Returns:
        JSON response with file path and content.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "CaseLayoutRule")

        rule_id = sanitize_name(rule_name).lower()

        rule_data = {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "layout_id": layout_id,
            "description": description or f"Layout rule: {rule_name}",
            "fromVersion": "8.7.0",
            "marketplaces": ["marketplacev2"],
            "alerts_filter": {
                "filter": {
                    "AND": [
                        {
                            "SEARCH_FIELD": "type",
                            "SEARCH_TYPE": "EQ",
                            "SEARCH_VALUE": "default"
                        }
                    ]
                }
            }
        }

        file_name = f"{FILE_PREFIXES['CaseLayoutRule']}{rule_id}.json"
        file_path = content_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(rule_data, f, indent=4)

        logger.info(f"Created CaseLayoutRule: {file_path}")

        result = {
            "success": True,
            "content_type": "CaseLayoutRule",
            "file_path": str(file_path),
            "rule_name": rule_name,
            "pack_name": pack_name,
        }

        if upload:
            # CaseLayoutRules require pack upload with -z flag
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "CaseLayoutRules require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create CaseLayoutRule: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_parsing_rule
# =============================================================================

async def create_parsing_rule(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the rule in")],
    rule_name: Annotated[str, Field(description="Name of the parsing rule")],
    vendor: Annotated[str, Field(description="Vendor name for the INGEST directive")],
    product: Annotated[str, Field(description="Product name for the INGEST directive")],
    target_dataset: Annotated[str, Field(description="Target dataset name (e.g., vendor_product_raw)")],
    xql_rules: Annotated[str, Field(description="XQL parsing rules (the content after the INGEST directive)")],
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates a ParsingRule with YML and XIF files for XSIAM.

    ParsingRules define how to parse raw logs into structured data.
    Creates both:
    - {RuleName}/{RuleName}.yml (metadata)
    - {RuleName}/{RuleName}.xif (XQL rules)

    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        rule_name: Name of the rule (used for directory and files).
        vendor: Vendor name (e.g., "paloalto").
        product: Product name (e.g., "firewall").
        target_dataset: Target dataset (e.g., "paloalto_firewall_raw").
        xql_rules: XQL parsing logic (without the INGEST directive).

    Returns:
        JSON response with file paths and content.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "ParsingRule")

        # Create rule directory
        safe_rule_name = sanitize_name(rule_name)
        rule_dir = content_dir / safe_rule_name
        rule_dir.mkdir(parents=True, exist_ok=True)

        rule_id = safe_rule_name.lower()

        # Create YML file (field order matches HelloWorld: fromversion, id, name, tags, rules, samples)
        yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
tags: []
rules: ''
samples: ''
"""
        yml_path = rule_dir / f"{safe_rule_name}.yml"
        yml_path.write_text(yml_content)

        # Create XIF file with INGEST directive (content_id required for this XSIAM tenant)
        content_id = rule_id.lower()
        xif_content = f"""[INGEST:vendor="{vendor}", product="{product}", target_dataset="{target_dataset}", no_hit=keep, content_id="{content_id}"]
{xql_rules}
"""
        xif_path = rule_dir / f"{safe_rule_name}.xif"
        xif_path.write_text(xif_content)

        logger.info(f"Created ParsingRule: {rule_dir}")

        result = {
            "success": True,
            "content_type": "ParsingRule",
            "directory": str(rule_dir),
            "files": {
                "yml": str(yml_path),
                "xif": str(xif_path)
            },
            "rule_name": rule_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "ParsingRules require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create ParsingRule: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_modeling_rule
# =============================================================================

async def create_modeling_rule(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the rule in")],
    rule_name: Annotated[str, Field(description="Name of the modeling rule")],
    dataset: Annotated[str, Field(description="Source dataset name")],
    model: Annotated[str, Field(description="XDM model name (e.g., Audit, Network, Endpoint, Auth)")],
    xql_rules: Annotated[str, Field(description="XQL modeling rules mapping source fields to XDM fields")],
    schema_json: Annotated[Optional[str], Field(description="Optional JSON schema defining source fields")] = None,
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates a ModelingRule with YML and XIF files for XSIAM.

    ModelingRules define how to map parsed data to the XDM (Cortex Data Model).
    Creates:
    - {RuleName}/{RuleName}.yml (metadata)
    - {RuleName}/{RuleName}.xif (XQL rules)

    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        rule_name: Name of the rule.
        dataset: Source dataset to model.
        model: Target XDM model (Audit, Network, Endpoint, Auth, etc.).
        xql_rules: XQL modeling logic (alter xdm.field = source_field).
        schema_json: Optional schema definition.

    Returns:
        JSON response with file paths.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "ModelingRule")

        # Create rule directory
        safe_rule_name = sanitize_name(rule_name)
        rule_dir = content_dir / safe_rule_name
        rule_dir.mkdir(parents=True, exist_ok=True)

        rule_id = safe_rule_name.lower()

        # Create YML file
        yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags: ''
"""
        yml_path = rule_dir / f"{safe_rule_name}.yml"
        yml_path.write_text(yml_content)

        # Create XIF file with MODEL directive (no quotes around dataset, no model param)
        xif_content = f"""[MODEL: dataset = {dataset}]
{xql_rules}
"""
        xif_path = rule_dir / f"{safe_rule_name}.xif"
        xif_path.write_text(xif_content)

        # Create schema file (provided or default)
        schema_path = rule_dir / f"{safe_rule_name}_schema.json"
        if schema_json:
            try:
                schema_data = json.loads(schema_json)
            except json.JSONDecodeError:
                logger.warning("Invalid schema_json provided, using default schema")
                schema_data = {
                    dataset: {
                        "_raw_log": {
                            "type": "string",
                            "is_array": False
                        }
                    }
                }
        else:
            # Create default schema
            schema_data = {
                dataset: {
                    "_raw_log": {
                        "type": "string",
                        "is_array": False
                    }
                }
            }

        with open(schema_path, 'w') as f:
            json.dump(schema_data, f, indent=4)

        logger.info(f"Created ModelingRule: {rule_dir}")

        result = {
            "success": True,
            "content_type": "ModelingRule",
            "directory": str(rule_dir),
            "files": {
                "yml": str(yml_path),
                "xif": str(xif_path),
                "schema": str(schema_path)
            },
            "rule_name": rule_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "ModelingRules require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create ModelingRule: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_assets_modeling_rule
# =============================================================================

async def create_assets_modeling_rule(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the rule in")],
    rule_name: Annotated[str, Field(description="Name of the assets modeling rule")],
    dataset: Annotated[str, Field(description="Source dataset name")],
    xql_rules: Annotated[str, Field(description="XQL rules mapping to xdm.asset.* fields")],
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates an AssetsModelingRule with YML and XIF files for XSIAM.

    AssetsModelingRules define how to map data to the Assets model for
    asset inventory and management. Uses model="Assets".

    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        rule_name: Name of the rule.
        dataset: Source dataset.
        xql_rules: XQL rules for asset mapping.

    Returns:
        JSON response with file paths.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "AssetsModelingRule")

        # Create rule directory
        safe_rule_name = sanitize_name(rule_name)
        rule_dir = content_dir / safe_rule_name
        rule_dir.mkdir(parents=True, exist_ok=True)

        rule_id = safe_rule_name.lower()

        # Create YML file
        yml_content = f"""fromversion: 8.7.0
id: {rule_id}
name: {rule_name}
rules: ''
schema: ''
tags: ''
"""
        yml_path = rule_dir / f"{safe_rule_name}.yml"
        yml_path.write_text(yml_content)

        # Create XIF file with Assets model (no quotes around dataset, no model param)
        xif_content = f"""[MODEL: dataset = {dataset}]
{xql_rules}
"""
        xif_path = rule_dir / f"{safe_rule_name}.xif"
        xif_path.write_text(xif_content)

        # Create default schema file for Assets model
        schema_data = {
            dataset: {
                "_raw_log": {
                    "type": "string",
                    "is_array": False
                }
            }
        }
        schema_path = rule_dir / f"{safe_rule_name}_schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema_data, f, indent=4)

        logger.info(f"Created AssetsModelingRule: {rule_dir}")

        result = {
            "success": True,
            "content_type": "AssetsModelingRule",
            "directory": str(rule_dir),
            "files": {
                "yml": str(yml_path),
                "xif": str(xif_path),
                "schema": str(schema_path)
            },
            "rule_name": rule_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "AssetsModelingRules require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create AssetsModelingRule: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_xsiam_dashboard
# =============================================================================

async def create_xsiam_dashboard(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the dashboard in")],
    dashboard_name: Annotated[str, Field(description="Name of the dashboard")],
    description: Annotated[Optional[str], Field(description="Description of the dashboard")] = None,
    xql_query: Annotated[Optional[str], Field(description="XQL query for default widget (e.g., 'dataset = alerts | comp count() as total')")] = None,
    widget_title: Annotated[Optional[str], Field(description="Title for the widget")] = None,
    widget_type: Annotated[str, Field(description="Widget visualization type: single, table, pie, bar, line, column")] = "single",
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates an XSIAMDashboard JSON file with optional XQL widget.

    XSIAMDashboards are XSIAM-specific dashboards (different from classic XSOAR dashboards).

    If xql_query is provided, creates a dashboard with a functional widget.
    If xql_query is omitted, creates an empty dashboard template.

    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        dashboard_name: Name of the dashboard.
        description: Optional description.
        xql_query: Optional XQL query for default widget.
        widget_title: Optional widget title (defaults to dashboard name).
        widget_type: Visualization type (single, table, pie, bar, line, column).
        upload: If True, upload to XSIAM.

    Returns:
        JSON response with file path.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "XSIAMDashboard")

        dashboard_id = sanitize_name(dashboard_name).lower()

        # Build layout and widgets if XQL query provided
        layout = []
        widgets_data = []

        if xql_query:
            import time
            widget_key = f"xql_{int(time.time())}"
            widget_title_text = widget_title or dashboard_name

            # Add view graph command to XQL if not already present
            final_query = xql_query
            view_commands = []
            xaxis_field = None
            yaxis_field = None

            if "| view graph" not in xql_query.lower():
                # For aggregation queries, try to detect group by field
                if " by " in xql_query:
                    # Extract field after "by" for xaxis
                    parts = xql_query.split(" by ")
                    if len(parts) > 1:
                        xaxis_field = parts[-1].strip().split()[0]
                        # Extract count field for yaxis (look for "as fieldname")
                        yaxis_field = "count"
                        if " as " in xql_query:
                            as_parts = xql_query.split(" as ")
                            if len(as_parts) > 1:
                                yaxis_field = as_parts[-1].strip().split()[0]

                # Append appropriate view graph command based on widget type
                if widget_type == "single":
                    final_query += " | view graph type = single"
                    if yaxis_field:
                        final_query += f" yaxis = {yaxis_field}"
                        view_commands.append({"command": {"op": "=", "name": "yaxis", "value": yaxis_field}})
                elif widget_type == "table":
                    final_query += " | view graph type = table"
                elif widget_type in ["pie", "bar", "line", "column"]:
                    if xaxis_field and yaxis_field:
                        final_query += f" | view graph type = {widget_type} xaxis = {xaxis_field} yaxis = {yaxis_field}"
                        view_commands.extend([
                            {"command": {"op": "=", "name": "xaxis", "value": xaxis_field}},
                            {"command": {"op": "=", "name": "yaxis", "value": yaxis_field}}
                        ])
                    else:
                        final_query += f" | view graph type = {widget_type}"

            # Create widget for layout
            layout.append({
                "id": "row-1",
                "data": [{
                    "key": widget_key,
                    "data": {
                        "type": "Custom XQL",
                        "title": widget_title_text,
                        "width": 100,
                        "height": 400,
                        "phrase": final_query,
                        "time_frame": {"relativeTime": 86400000},
                        "viewOptions": {"type": widget_type, "commands": view_commands}
                    }
                }]
            })

            # Create widget data entry
            widgets_data.append({
                "widget_key": widget_key,
                "title": widget_title_text,
                "creation_time": int(time.time() * 1000),
                "description": description,
                "data": {
                    "phrase": final_query,
                    "time_frame": {"relativeTime": 86400000},
                    "viewOptions": {"type": widget_type, "commands": []}
                },
                "support_time_range": True,
                "additional_info": {
                    "query_tables": [],
                    "query_uses_library": False
                }
            })

        dashboard_data = {
            "fromVersion": "8.7.0",
            "toVersion": "99.99.99",
            "dashboards_data": [
                {
                    "global_id": dashboard_id,
                    "status": "ENABLED",
                    "name": dashboard_name,
                    "description": description or f"XSIAM Dashboard: {dashboard_name}",
                    "default_dashboard_id": None,
                    "layout": layout,
                    "metadata": {"params": []}
                }
            ],
            "widgets_data": widgets_data
        }

        file_name = f"{FILE_PREFIXES['XSIAMDashboard']}{dashboard_id}.json"
        file_path = content_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(dashboard_data, f, indent=4)

        logger.info(f"Created XSIAMDashboard: {file_path}")

        result = {
            "success": True,
            "content_type": "XSIAMDashboard",
            "file_path": str(file_path),
            "dashboard_name": dashboard_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "XSIAMDashboards require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create XSIAMDashboard: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_xsiam_report
# =============================================================================

async def create_xsiam_report(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the report in")],
    report_name: Annotated[str, Field(description="Name of the report")],
    description: Annotated[Optional[str], Field(description="Description of the report")] = None,
    xql_query: Annotated[Optional[str], Field(description="XQL query for default widget (e.g., 'dataset = alerts | comp count() as total by severity')")] = None,
    widget_title: Annotated[Optional[str], Field(description="Title for the widget")] = None,
    widget_type: Annotated[str, Field(description="Widget visualization type: single, table, pie, bar, line, column")] = "table",
    dashboard_id: Annotated[Optional[str], Field(description="ID of associated XSIAMDashboard")] = None,
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM (requires -z flag)")] = False,
) -> str:
    """
    Creates an XSIAMReport JSON file with optional XQL widget.

    XSIAMReports are XSIAM-specific reports that can be scheduled or run on-demand.

    If xql_query is provided, creates a report with a functional widget.
    If xql_query is omitted, creates an empty report template.

    Note: Requires pack upload (-z flag) to deploy.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        report_name: Name of the report.
        description: Optional description.
        xql_query: Optional XQL query for default widget.
        widget_title: Optional widget title (defaults to report name).
        widget_type: Visualization type (single, table, pie, bar, line, column).
        dashboard_id: Optional associated dashboard.
        upload: If True, upload to XSIAM.

    Returns:
        JSON response with file path.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "XSIAMReport")

        report_id = sanitize_name(report_name).lower()

        # Build layout and widgets if XQL query provided
        layout = []
        widgets_data = []

        if xql_query:
            import time
            widget_key = f"xql_{int(time.time())}"
            widget_title_text = widget_title or report_name

            # Add view graph command to XQL if not already present
            final_query = xql_query
            view_commands = []
            xaxis_field = None
            yaxis_field = None

            if "| view graph" not in xql_query.lower():
                # For aggregation queries, try to detect group by field
                if " by " in xql_query:
                    # Extract field after "by" for xaxis
                    parts = xql_query.split(" by ")
                    if len(parts) > 1:
                        xaxis_field = parts[-1].strip().split()[0]
                        # Extract count field for yaxis (look for "as fieldname")
                        yaxis_field = "count"
                        if " as " in xql_query:
                            as_parts = xql_query.split(" as ")
                            if len(as_parts) > 1:
                                yaxis_field = as_parts[-1].strip().split()[0]

                # Append appropriate view graph command based on widget type
                if widget_type == "single":
                    final_query += " | view graph type = single"
                    if yaxis_field:
                        final_query += f" yaxis = {yaxis_field}"
                        view_commands.append({"command": {"op": "=", "name": "yaxis", "value": yaxis_field}})
                elif widget_type == "table":
                    final_query += " | view graph type = table"
                elif widget_type in ["pie", "bar", "line", "column"]:
                    if xaxis_field and yaxis_field:
                        final_query += f" | view graph type = {widget_type} xaxis = {xaxis_field} yaxis = {yaxis_field}"
                        view_commands.extend([
                            {"command": {"op": "=", "name": "xaxis", "value": xaxis_field}},
                            {"command": {"op": "=", "name": "yaxis", "value": yaxis_field}}
                        ])
                    else:
                        final_query += f" | view graph type = {widget_type}"

            # Create widget for layout
            layout.append({
                "id": "row-1",
                "data": [{
                    "key": widget_key,
                    "data": {
                        "type": "Custom XQL",
                        "title": widget_title_text,
                        "width": 100,
                        "height": 400,
                        "phrase": final_query,
                        "time_frame": {"relativeTime": 86400000},
                        "viewOptions": {"type": widget_type, "commands": view_commands}
                    }
                }]
            })

            # Create widget data entry
            widgets_data.append({
                "widget_key": widget_key,
                "title": widget_title_text,
                "creation_time": int(time.time() * 1000),
                "description": description,
                "data": {
                    "phrase": final_query,
                    "time_frame": {"relativeTime": 86400000},
                    "viewOptions": {"type": widget_type, "commands": []}
                },
                "support_time_range": True,
                "additional_info": {
                    "query_tables": [],
                    "query_uses_library": False
                }
            })

        # XSIAMReport uses templates_data wrapper (based on working examples from demisto/content)
        template = {
            "global_id": report_id,
            "report_name": report_name,
            "report_description": description or f"XSIAM Report: {report_name}",
            "fromVersion": "8.7.0",
            "layout": layout,
            "default_template_id": 1,
            "time_frame": {"relativeTime": 86400000},  # 1 day default
            "time_offset": 0,
            "metadata": json.dumps({"params": []})  # JSON string, not object!
        }

        # Optional dashboard_id
        if dashboard_id:
            template["dashboard_id"] = dashboard_id

        report_data = {
            "templates_data": [template],
            "fromVersion": "8.7.0",
            "widgets_data": widgets_data
        }

        file_name = f"{FILE_PREFIXES['XSIAMReport']}{report_id}.json"
        file_path = content_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=4)

        logger.info(f"Created XSIAMReport: {file_path}")

        result = {
            "success": True,
            "content_type": "XSIAMReport",
            "file_path": str(file_path),
            "report_name": report_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "XSIAMReports require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create XSIAMReport: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_agentix_action
# =============================================================================

async def create_agentix_action(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the action in")],
    action_name: Annotated[str, Field(description="Name of the AgentIX action")],
    display_name: Annotated[str, Field(description="Display name shown in UI")],
    description: Annotated[str, Field(description="Description of what this action does")],
    underlying_type: Annotated[str, Field(description="Type of underlying content: command, script, or playbook")],
    underlying_id: Annotated[str, Field(description="ID of the underlying content item")],
    underlying_name: Annotated[str, Field(description="Name of the underlying content item")],
    requires_user_approval: Annotated[bool, Field(description="If True, requires user approval before execution. Use True for destructive/sensitive actions (delete, terminate, isolate, modify). Use False for trusted actions that can run automatically.")] = False,
    underlying_command: Annotated[Optional[str], Field(description="Command name (only for type=command)")] = None,
    args: Annotated[Optional[str], Field(description='JSON array of arguments. Format: [{"name": "ip", "required": true, "description": "IP address", "type": "string", "underlyingargname": "ip"}]')] = None,
    outputs: Annotated[Optional[str], Field(description='JSON array of outputs. Format: [{"name": "IP.Address", "description": "IP address", "type": "string", "underlyingoutputcontextpath": "IP.Address"}]')] = None,
    tags: Annotated[Optional[List[str]], Field(description="List of tags for categorization")] = None,
    category: Annotated[Optional[str], Field(description="Action category")] = None,
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM")] = False,
) -> str:
    """
    Creates an AgentIXAction YAML file for XSIAM.

    AgentIXActions wrap existing XSOAR content (commands, scripts, playbooks)
    to make them accessible to AI agents in the AgentIX platform.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        action_name: Name of the action (used as ID).
        display_name: Display name in UI.
        description: What the action does.
        underlying_type: "command", "script", or "playbook".
        underlying_id: ID of the underlying content.
        underlying_name: Name of the underlying content.
        requires_user_approval: If True, requires user approval before execution (default: False).
                                Use True for destructive/sensitive actions, False for trusted actions.
        underlying_command: Command name (required if underlying_type="command").
        args: JSON array of arguments (optional). Format:
              [{"name": "ip", "required": true, "description": "IP to enrich", "type": "string", "underlyingargname": "ip"}]
        outputs: JSON array of outputs (optional). Format:
                 [{"name": "IP.Address", "description": "IP address", "type": "string", "underlyingoutputcontextpath": "IP.Address"}]
        tags: List of tags for categorization.
        category: Optional category.
        upload: If True, upload to XSIAM.

    Returns:
        JSON response with file path.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "AgentIXAction")

        action_id = sanitize_name(action_name).lower()

        # Parse args and outputs if provided
        args_list = []
        if args:
            try:
                args_list = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                logger.warning("Invalid args JSON, using empty array")

        outputs_list = []
        if outputs:
            try:
                outputs_list = json.loads(outputs) if isinstance(outputs, str) else outputs
            except json.JSONDecodeError:
                logger.warning("Invalid outputs JSON, using empty array")

        # Build AgentIXAction YAML structure (based on TestSuite example)
        action_data = {
            "commonfields": {
                "id": action_id,
                "version": -1
            },
            "display": display_name,
            "name": action_name,
            "tags": tags or [],
            "category": category or "Utilities",
            "description": description,
            "args": args_list,
            "outputs": outputs_list,
            "underlyingcontentitem": {
                "id": underlying_id,
                "name": underlying_name,
                "type": underlying_type,
                "version": -1
            },
            "requiresuserapproval": requires_user_approval,
            "marketplaces": ["platform"],
            "supportedModules": ["agentix"]
        }

        # Add command field if type is command
        if underlying_type == "command" and underlying_command:
            action_data["underlyingcontentitem"]["command"] = underlying_command

        file_path = content_dir / f"{action_id}.yml"

        with open(file_path, 'w') as f:
            yaml.dump(action_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created AgentIXAction: {file_path}")

        result = {
            "success": True,
            "content_type": "AgentIXAction",
            "file_path": str(file_path),
            "action_name": action_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "AgentIXActions require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create AgentIXAction: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: create_agentix_agent
# =============================================================================

async def create_agentix_agent(
    ctx: Context,
    pack_name: Annotated[str, Field(description="Name of the pack to create the agent in")],
    agent_name: Annotated[str, Field(description="Name of the AgentIX agent")],
    description: Annotated[str, Field(description="Description of the agent's purpose")],
    color: Annotated[str, Field(description="Hex color code for UI (e.g., '#3498DB')")],
    visibility: Annotated[str, Field(description="Agent visibility: 'public' or 'private'")],
    category: Annotated[Optional[str], Field(description="Agent category")] = None,
    action_ids: Annotated[Optional[List[str]], Field(description="List of action IDs available to this agent")] = None,
    system_instructions: Annotated[Optional[str], Field(description="System instructions for the agent")] = None,
    conversation_starters: Annotated[Optional[List[str]], Field(description="Example conversation starters")] = None,
    upload: Annotated[bool, Field(description="If True, upload pack to XSIAM")] = False,
) -> str:
    """
    Creates an AgentIXAgent YAML file for XSIAM.

    AgentIXAgents define AI assistant configurations including behavior,
    available actions, and conversation starters.

    Args:
        ctx: FastMCP context.
        pack_name: Name of the pack.
        agent_name: Name of the agent.
        description: Agent description.
        color: Hex color code (e.g., '#3498DB').
        visibility: 'public' or 'private'.
        category: Optional category.
        action_ids: List of action IDs the agent can use.
        system_instructions: Instructions defining agent behavior.
        conversation_starters: Example prompts for users.
        upload: If True, upload to XSIAM.

    Returns:
        JSON response with file path.
    """
    try:
        pack_path = ensure_pack_exists(pack_name)
        content_dir = ensure_content_dir(pack_path, "AgentIXAgent")

        agent_id = sanitize_name(agent_name).lower()

        # Build AgentIXAgent YAML structure
        agent_data = {
            "commonfields": {
                "id": agent_id,
                "version": -1
            },
            "name": agent_name,
            "description": description,
            "color": color,
            "visibility": visibility,
            "marketplaces": ["platform"],
            "supportedModules": ["agentix"]
        }

        # Optional fields
        if category:
            agent_data["category"] = category
        if action_ids:
            agent_data["actionids"] = action_ids
        if system_instructions:
            agent_data["systeminstructions"] = system_instructions
        if conversation_starters:
            agent_data["conversationstarters"] = conversation_starters

        file_path = content_dir / f"{agent_id}.yml"

        with open(file_path, 'w') as f:
            yaml.dump(agent_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created AgentIXAgent: {file_path}")

        result = {
            "success": True,
            "content_type": "AgentIXAgent",
            "file_path": str(file_path),
            "agent_name": agent_name,
            "pack_name": pack_name,
        }

        if upload:
            upload_result = run_sdk_upload(pack_name, use_zip=True)
            result["upload"] = upload_result
        else:
            result["note"] = "AgentIXAgents require pack upload: demisto-sdk upload -i Packs/{pack} -z --marketplace marketplacev2"

        return create_response(data=result)

    except Exception as e:
        logger.exception(f"Failed to create AgentIXAgent: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


# =============================================================================
# TOOL: get_xsiam_content_guide
# =============================================================================

async def get_xsiam_content_guide(ctx: Context) -> str:
    """
    Returns a comprehensive guide for XSIAM content types.

    Covers:
    - Case vs Issue terminology
    - Each content type and its purpose
    - File structure requirements
    - Upload requirements
    - Example usage

    Returns:
        Markdown guide.
    """
    guide = """
# XSIAM Content Types Guide

## Terminology: Cases vs Issues

| XSOAR Legacy | XSIAM Current | Description |
|--------------|---------------|-------------|
| Incident | **Case** | Container for related security events |
| IncidentField | **CaseField** | Custom fields on Cases |
| IncidentLayout | **CaseLayout** | UI layout for Cases |
| Alert | **Issue** | Individual security event |
| (none) | IssueField | NOT SUPPORTED: Doesn't exist - issues use alert schema from integrations |

---

## Content Types

### 1. CaseLayout (`group: "case"`)
UI layout defining how Cases are displayed.

**Key Points:**
- Use `"group": "case"` to distinguish from incident layouts
- Can upload individually
- File: `CaseLayouts/layoutscontainer-{name}.json`

**Example:**
```python
create_case_layout(
    pack_name="MyPack",
    layout_name="Custom Investigation Layout"
)
```

---

### 2. CaseField
Custom fields that appear on Cases.

**Key Points:**
- Types: shortText, longText, number, date, boolean, singleSelect, multiSelect, grid
- Requires `associatedToAll: true` for all cases
- File: `CaseFields/casefield-{id}.json`

**Example:**
```python
create_case_field(
    pack_name="MyPack",
    field_id="investigation_status",
    field_name="Investigation Status",
    field_type="singleSelect",
    select_values='["Not Started", "In Progress", "Completed"]'
)
```

---

### 3. CaseLayoutRule
Routes cases to specific layouts based on conditions.

**Key Points:**
- Requires pack upload (`-z` flag)
- Links rule to CaseLayout by layout_id
- File: `CaseLayoutRules/caselayoutrule-{name}.json`

---

### 4. ParsingRule
Parses raw logs into structured data.

**Key Points:**
- Requires TWO files: YML + XIF
- XIF contains the INGEST directive and XQL rules
- Requires pack upload (`-z` flag)
- Directory: `ParsingRules/{RuleName}/`

**Example:**
```python
create_parsing_rule(
    pack_name="MyPack",
    rule_name="MyAppLogs",
    vendor="mycompany",
    product="myapp",
    target_dataset="mycompany_myapp_raw",
    xql_rules='filter _raw_log ~= "ERROR"\\n| alter severity = "high";'
)
```

---

### 5. ModelingRule
Maps parsed data to XDM (Cortex Data Model).

**Key Points:**
- Requires TWO files: YML + XIF
- XIF contains the MODEL directive
- Models: Audit, Network, Endpoint, Auth, etc.
- Requires pack upload (`-z` flag)
- Directory: `ModelingRules/{RuleName}/`

**Example:**
```python
create_modeling_rule(
    pack_name="MyPack",
    rule_name="MyAppAudit",
    dataset="mycompany_myapp_raw",
    model="Audit",
    xql_rules='alter xdm.event.type = "AUDIT"\\n| alter xdm.event.description = message;'
)
```

---

### 6. AssetsModelingRule
Maps data to the Assets model for inventory.

**Key Points:**
- Similar to ModelingRule but uses model="Assets"
- Maps to xdm.asset.* fields
- Directory: `AssetsModelingRules/{RuleName}/`

---

### 7. XSIAMDashboard
XSIAM-specific dashboards.

**Key Points:**
- Different from classic XSOAR dashboards
- Requires pack upload (`-z` flag)
- File: `XSIAMDashboards/xsiamdashboard-{name}.json`

---

### 8. XSIAMReport
XSIAM-specific reports.

**Key Points:**
- Can be linked to XSIAMDashboard
- Requires pack upload (`-z` flag)
- File: `XSIAMReports/xsiamreport-{name}.json`

---

### 9. CorrelationRule (Use API Tool!)
Custom detection rules.

**Use the `insert_correlation_rule` API tool instead** - it creates rules directly
via the XSIAM API without needing SDK upload.

---

## Upload Commands

**Individual files (CaseLayout, CaseField):**
```bash
demisto-sdk upload -i Packs/MyPack/CaseLayouts/layoutscontainer-xxx.json --marketplace marketplacev2
```

**Pack upload (most XSIAM content):**
```bash
demisto-sdk upload -i Packs/MyPack -z --marketplace marketplacev2
```

---

## Pack Structure

```
Packs/MyPack/
├── pack_metadata.json          # marketplaces: ["marketplacev2"]
├── .pack-ignore
├── .secrets-ignore
├── README.md
├── CaseLayouts/
│   └── layoutscontainer-*.json
├── CaseFields/
│   └── casefield-*.json
├── CaseLayoutRules/
│   └── caselayoutrule-*.json
├── ParsingRules/
│   └── {RuleName}/
│       ├── {RuleName}.yml
│       └── {RuleName}.xif
├── ModelingRules/
│   └── {RuleName}/
│       ├── {RuleName}.yml
│       └── {RuleName}.xif
├── AssetsModelingRules/
│   └── {RuleName}/
│       ├── {RuleName}.yml
│       └── {RuleName}.xif
├── XSIAMDashboards/
│   └── xsiamdashboard-*.json
└── XSIAMReports/
    └── xsiamreport-*.json
```

---

## Tips

1. **Always use `marketplacev2`** in pack_metadata.json for XSIAM content
2. **ParsingRules and ModelingRules need `.xif` files** - the YML alone won't work
3. **Most XSIAM content requires pack upload** with `-z` flag
4. **For CorrelationRules, use the API** - `insert_correlation_rule` tool is faster
5. **Test with SDK validate first**: `demisto-sdk validate -i Packs/MyPack`
"""

    return create_response(data={
        "guide": guide,
        "content_types": list(CONTENT_DIRS.keys()),
        "content_repo_path": CONTENT_REPO
    })


# =============================================================================
# MODULE REGISTRATION
# =============================================================================

class XSIAMContentGeneratorModule(BaseModule):
    """Module for XSIAM content generation tools."""

    def register_tools(self):
        self._add_tool(create_case_layout)
        self._add_tool(create_case_field)
        self._add_tool(create_case_layout_rule)
        self._add_tool(create_parsing_rule)
        self._add_tool(create_modeling_rule)
        self._add_tool(create_assets_modeling_rule)
        self._add_tool(create_xsiam_dashboard)
        self._add_tool(create_xsiam_report)
        self._add_tool(create_agentix_action)
        self._add_tool(create_agentix_agent)
        self._add_tool(get_xsiam_content_guide)

    def register_resources(self):
        pass
