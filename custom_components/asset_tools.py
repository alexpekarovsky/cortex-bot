"""Asset and vulnerability tools — overrides broken PANW builtin OpenAPI tools."""
import json
import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError, PAPIClientError, PAPIClientRequestError,
    PAPIConnectionError, PAPIResponseError, PAPIServerError,
)
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)

PAPI_ERRORS = (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
               PAPIClientRequestError, PAPIResponseError, PAPIClientError)


def _parse(data):
    if data is None:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return data


async def _api_call(ctx, path, data, tool_name):
    try:
        fetcher = await get_fetcher(ctx)
        omit = "/public_api/" in path
        resp = await fetcher.send_request(path=path, method="POST", data=data, omit_papi_prefix=omit)
        return create_response(data=resp)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"{tool_name} failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_assets(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Filters for assets. Use {"filters": [{"field": "<field>", '
                    '"operator": "<op>", "value": "<val>"}], '
                    '"search_from": 0, "search_to": 100} format. Empty for all.'
    )] = None,
) -> str:
    """Retrieves asset information from the asset inventory.
    Returns asset details including hostname, IP, OS, risk score, and more."""
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/assets/get_assets/",
                           {"request_data": request_data or {}}, "get_assets")


async def get_asset_by_id(
    ctx: Context,
    asset_id: Annotated[str, Field(description="The asset ID to look up")],
) -> str:
    """Retrieves detailed information for a specific asset by its ID."""
    try:
        fetcher = await get_fetcher(ctx)
        resp = await fetcher.send_request(
            path=f"/public_api/v1/assets/{asset_id}/",
            method="POST",
            data={"request_data": {}},
            omit_papi_prefix=True
        )
        return create_response(data=resp)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_asset_by_id failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_vulnerabilities(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Filters for vulnerabilities. Use {"filters": [...], '
                    '"search_from": 0, "search_to": 100} format. Empty for all.'
    )] = None,
) -> str:
    """Retrieves vulnerability information from the vulnerability assessment module."""
    request_data = _parse(request_data) or {}
    if "use_page_token" not in request_data:
        request_data["use_page_token"] = True
    return await _api_call(ctx, "/public_api/uvem/v1/get_vulnerabilities",
                           {"request_data": request_data}, "get_vulnerabilities")


async def get_assessment_profile_results(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Assessment profile filters. Empty for all results.'
    )] = None,
) -> str:
    """Retrieves security assessment profile results."""
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/compliance/get_assessment_results/",
                           {"request_data": request_data or {}}, "get_assessment_profile_results")


class AssetToolsModule(BaseModule):
    """Asset and vulnerability tools — overrides broken PANW builtins."""
    def register_tools(self):
        self._add_tool(get_assets)
        self._add_tool(get_asset_by_id)
        self._add_tool(get_vulnerabilities)
        self._add_tool(get_assessment_profile_results)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
