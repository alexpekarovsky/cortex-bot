"""Monkey-patch PAPIClient.request() to be compatible with FastMCP OpenAPI handler.

The PANW PAPIClient.request() returns a parsed dict, but FastMCP's OpenAPI
handler expects httpx Response objects (calls .raise_for_status() and .json()).
This patch wraps the dict in a class that IS a dict but also has Response methods.
"""
import logging

from fastmcp import FastMCP
from pkg.client import PAPIClient
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

_original_request = PAPIClient.request


class DictResponse(dict):
    """A dict that also has httpx Response methods for FastMCP OpenAPI compatibility."""

    def __init__(self, data):
        super().__init__(data)
        self.status_code = 200
        self.headers = {"content-type": "application/json"}
        self.text = ""

    def raise_for_status(self):
        pass  # PAPIClient already raises on errors before returning

    def json(self):
        return dict(self)


async def _patched_request(self, method, url, **kwargs):
    """Wraps the original request result in DictResponse for OpenAPI compatibility."""
    result = await _original_request(self, method, url, **kwargs)
    if isinstance(result, dict) and not isinstance(result, DictResponse):
        return DictResponse(result)
    return result


PAPIClient.request = _patched_request


class ClientPatchModule(BaseModule):
    """Patches PAPIClient to return OpenAPI-compatible responses."""
    def register_tools(self):
        pass

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
        logger.info("ClientPatchModule: PAPIClient.request patched for OpenAPI compatibility")
