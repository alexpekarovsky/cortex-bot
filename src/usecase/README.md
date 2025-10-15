# Custom MCP components

There are 2 ways to add custom MCP components:

## OpenAPI

Currently, there is no official OpenAPI specification for the Cortex API, 
but it is rather simple to create an OpenAPI specification for a specific API endpoint, given the integration between the Cortex MCP server infrastructure based on FastMCP and OpenAPI (see https://gofastmcp.com/integrations/openapi#openapi-fastmcp for more details).

To get started, visit the [Cortex API documentation](https://docs-cortex.paloaltonetworks.com/r/Cortex-Cloud-Platform-APIs/Cortex-Cloud-Platform-APIs).
Then proceed with the following steps:
1. Create a yaml file under `/custom_components/openapi` directory with the name of the MCP component, e.g., `custom_cortex_component.yaml`
2. Your custom OpenAPI component should be based on the Cortex API documentation structure for a specific endpoint. Use the builtin files under `/builtin_components/openapi` for reference.
3. After defining the OpenAPI specification, the component is ready to go. The MCP server will collect it automatically.
4. Test the new MCP component by running the MCP server.

## Python

You can use Python to add more elaborate MCP components that require custom logic. 
MCP components written in Python are defined in a Module. To add a module, follow these steps:
1. Create a new Python file under `/custom_components` directory.
2. Define a class that inherits from the base module class (`BaseModule`) with the necessary methods. See builtin modules under `builtin_components` for reference.
3. The MCP server will automatically collect the new MCP components.
4. Test the new MCP component by adding an end-to-end test in the `tests/e2e` directory or run the MCP server.

