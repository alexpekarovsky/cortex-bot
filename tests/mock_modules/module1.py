from fastmcp import FastMCP

from usecase.base_module import BaseModule


class MockModule(BaseModule):
    """Mock module for testing purposes"""

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
        self.register_tools_called = False
        self.register_resources_called = False

    def register_tools(self):
        self.register_tools_called = True

    def register_resources(self):
        self.register_resources_called = True
