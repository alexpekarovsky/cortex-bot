import logging
from abc import ABC, abstractmethod
from typing import Callable

from fastmcp import FastMCP
from fastmcp.resources import Resource
from fastmcp.tools import Tool

logger = logging.getLogger(__name__)


class BaseModule(ABC):
    """
    Abstract base class for MCP (Model Context Protocol) modules.

    This class provides a foundation for creating modules that can register
    tools and resources with a FastMCP instance. All concrete module implementations
    should inherit from this class and implement the required abstract methods.

    Attributes:
        mcp (FastMCP): The FastMCP instance used for registering tools and resources.
    """

    def __init__(self, mcp: FastMCP):
        """
        Initialize the BaseModule with a FastMCP instance.

        Args:
            mcp (FastMCP): The FastMCP instance that will be used to register
                          tools and resources.
        """
        self.mcp = mcp

    @abstractmethod
    def register_tools(self):
        """
        Register tools with the MCP instance.

        This method must be implemented by subclasses to define what tools
        the module provides. Tools are callable functions that can be invoked
        by the MCP system.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        pass

    @abstractmethod
    def register_resources(self):
        """
        Register resources with the MCP instance.

        This method must be implemented by subclasses to define what resources
        the module provides. Resources are data sources that can be accessed
        by the MCP system.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        pass

    def _add_tool(self, fn: Callable, description: str = None):
        """
        Add a tool to the MCP instance.

        This is a helper method that wraps a callable function as a Tool
        and registers it with the MCP instance.

        Args:
            fn (Callable): The function to be registered as a tool.
            description (str, optional): Description of the tool. If not provided,
                                       the function's docstring will be used.

        Example:
            self._add_tool(my_function, "A tool that does something useful")
        """
        tool = Tool.from_function(fn, description)
        self.mcp.add_tool(tool)
        logger.debug(f"Added tool: {tool.name}")

    def _add_resource(self, fn: Callable, uri: str, name: str, description: str, mime_type: str = 'application/json'):
        """
        Add a resource to the MCP instance.

        This is a helper method that wraps a callable function as a Resource
        and registers it with the MCP instance.

        Args:
            fn (Callable): The function that provides the resource data.
            uri (str): The URI identifier for the resource.
            name (str): The human-readable name of the resource.
            description (str): A description of what the resource provides.
            mime_type (str, optional): The MIME type of the resource data.
                                     Defaults to 'application/json'.

        Example:
            self._add_resource(
                get_data_fn,
                "mymodule://data",
                "My Data",
                "Provides access to my module's data",
                "application/json"
            )
        """
        resource = Resource.from_function(fn, uri, name=name, description=description, mime_type=mime_type)
        self.mcp.add_resource(resource)
        logger.debug(f"Added resource: {resource.name}")
