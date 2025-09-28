# Cortex MCP CLI

A command-line interface for managing the Cortex MCP (Model Context Protocol) application.

## Overview

This CLI provides two main commands:
- `start`: Start the MCP server
- `update`: Update cortex content tools from the Cortex API

## Commands

### start
    Start the MCP server with specified configuration.

    python src/cli.py start [OPTIONS]

    Options:

        --api_key_id <ID>: The ID of the API key 
        --api_key_secret <SECRET>: The API key secret 
        --server-url <URL>: The Cortex PAPI server URL
        --log-level <LEVEL>: Log level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL, default: DEBUG)

### update
    Update a folder containing cortex content (default is remote_tools folder).

    python src/cli.py update [OPTIONS]

    Options:

        --api_key_id <ID>: The ID of the API key 
        --api_key_secret <SECRET>: The API key secret 
        --server-url <URL>: The Cortex PAPI server URL 
        --folder <PATH>: The path to the content folder to be updated 

### Environment Variables
    The following environment variables can be set instead of using command-line flags:

    Required Environment Variables

        CORTEX_MCP_PAPI_AUTH_ID: API key ID 
        CORTEX_MCP_PAPI_AUTH_HEADER: API key secret 
        CORTEX_MCP_PAPI_URL: Cortex PAPI server URL

    Optional Environment Variables
    
        LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        CORTEX_MCP_UPDATE_FOLDER: Path to the content folder for updates


### Usage Examples
    Starting the server with environment variables:
    
        export CORTEX_MCP_PAPI_AUTH_ID=12345
        export CORTEX_MCP_PAPI_AUTH_HEADER="your-api-key-secret"
        export CORTEX_MCP_PAPI_URL="https://api-your-cortex-server.com"
        export LOG_LEVEL="INFO"
    
        python src/cli.py start
    
    Starting the server with command-line arguments:

        python src/cli.py start --api_key_id 12345 --api_key_secret "your-api-key-secret" --server-url "https://your-cortex-server.com" --log-level INFO
    
### Configuration Priority
    Command-line arguments take precedence over environment variables. If neither is provided for required parameters, the application will exit with an error.

### Help
    For general help:

        python src/cli.py --help
        
    For help with a specific command:
    
        python src/cli.py start --help
        python src/cli.py update --help