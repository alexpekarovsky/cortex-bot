# cortex-mcp

A Python based integration for Cortex MCP (Model Context Protocol).

## Getting Started

### Prerequisites

- Python 3.12 or higher / container environment
- Cortex API credentials (API key and API key ID)

### Installation

#### Option 1: Using Docker

Create a `.env` file with the following environment variables:
```
CORTEX_MCP_PAPI_URL=https://api.cortex.example.com,
CORTEX_MCP_PAPI_AUTH_HEADER=<your_api_key>, 
CORTEX_MCP_PAPI_AUTH_ID=<your_api_key_id>,
(optional)MCP_TRANSPORT=stdio/streamable-http
(optional, for streamable-http)MCP_HOST=0.0.0.0
(optional, for streamable-http)MCP_PORT=8080
(optional, for streamable-http)MCP_PATH=/api/v1/stream/mcp
```

Build and run the Docker container:

```bash
docker build -t cortex-mcp .
```

```bash
docker run --env-file .env -it cortex-mcp
```

For streamable-http, according to the http configuration from the env file:

```bash
docker run -p 8080:8080 --env-file .env -it cortex-mcp
```

#### Option 2: Using Poetry (Virtual Environment)

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install project dependencies:
```bash
poetry install
```

## Usage

### CLI
See the [CLI](src/README.md) readme

### Virtual Environment
1. Provide the required variables in the python runtime environment:
```
CORTEX_MCP_PAPI_URL (Cortex API URL)
CORTEX_MCP_PAPI_AUTH_HEADER (Cortex API key) 
CORTEX_MCP_PAPI_AUTH_ID (Cortex API key ID)
```

2. Run the server
```bash
python src/main.py
```

### Claude Desktop

Open the Claude configuration file (accessible from the `Developer` pane in Claude Desktop settings) and add the following MCP server configuration:

Local (the package would have to be installed locally beforehand):
```json
{
  "mcpServers": {
    "Cortex MCP Server": {
      "command": "python",
      "args": [
        "/path/to/cortex-mcp/src/main.py"
      ],
       "env": {
          "CORTEX_MCP_PAPI_URL": "https://api.cortex.example.com",
          "CORTEX_MCP_PAPI_AUTH_HEADER": "<your_api_key>", 
          "CORTEX_MCP_PAPI_AUTH_ID": "<your_api_key_id",
          "MCP_TRANSPORT": "stdio/streamable-http"
   }
    }
  }
}
```


Container:
```json
{
  "mcpServers": {
    "Cortex MCP Server": {
      "command": "docker",
      "args": [
        "run",
        "--env-file",
        "/path/to/.env",
        "-i",
        "--rm",
        "cortex-mcp"
      ]
    }
  }
}
```

Streamable HTTP:
```json
{
  "mcpServers": {
    "Cortex MCP Server": {
     "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://0.0.0.0:8080/api/v1/stream/mcp",
        "--transport",
        "http-only",
        "--allow-http"
      ]
    }
  }
}
```


## Development

### Project Structure
```
src/
├── cli.py                           # Command line interface
├── main.py                          # Main application entry point
├── config/                          # Configuration modules
├── entities/                        # Data models and entity classes
├── pkg/                             # Internal package utilities and helpers
├── service/                         # Service layer implementations
└── usecase/                         # Business logic and use cases
    ├── builtin_components/          # MCP components that come with the package
    │   ├── openapi/
    │   └── python modules
    ├── custom_components/           # MCP components that are user-defined 
    │   ├── openapi/
    │   └── python modules
    └── remote_components/           # MCP components hosted or imported from remote repositories
        ├── openapi/
        └── python modules

tests/
├── e2e/                             # End-to-end tests
└── individual test files
```

### Adding custom MCP components

To add custom MCP components, follow this [guide](src/usecase/README.md).

### Coding

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black .
poetry run isort .
```

Debug:
The best way to debug MCP servers is with the [MCP inspector](https://github.com/modelcontextprotocol/inspector).
Aside from that, end-to-end tests can be run and added under `tests/e2e`.

<!---Protected_by_PANW_Code_Armor_2024 - eGRyfC94ZHIvY29ydGV4LW1jcHwzMzA0fG1hc3Rlcg== --->
