# Cortex MCP CLI

A command-line interface for managing the Cortex MCP (Model Context Protocol) application.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Commands](#commands)
- [Environment Variables](#environment-variables)
- [Usage Examples](#usage-examples)
- [Configuration Priority](#configuration-priority)
- [Troubleshooting](#troubleshooting)
- [Help](#help)

## Overview

This CLI provides three main commands:
- `start`: Start the MCP server
- `update`: Update cortex content tools from the Cortex API  
- `version`: Display the current version of the Cortex MCP Server

## Commands

### start
Start the MCP server with specified configuration.

```bash
python src/cli.py start [OPTIONS]
```

**Options:**
- `--api_key_id <ID>`: The ID of the API key 
- `--api_key_secret <SECRET>`: The API key secret 
- `--server-url <URL>`: The Cortex PAPI server URL
- `--log-level <LEVEL>`: Log level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL, default: DEBUG)

### update
Update a folder containing cortex content (default is remote_components folder).

> **Note:** The remote_components folder contains MCP components that are managed by Cortex remote repositories.

```bash
python src/cli.py update [OPTIONS]
```

**Options:**
- `--api_key_id <ID>`: The ID of the API key 
- `--api_key_secret <SECRET>`: The API key secret 
- `--server-url <URL>`: The Cortex PAPI server URL 
- `--folder <PATH>`: The path to the content folder to be updated (default: remote_components)

### version
Display the current version of the Cortex MCP Server

```bash
python src/cli.py version
```

## Environment Variables

The following environment variables can be set instead of using command-line flags:

### Required Environment Variables
- `CORTEX_MCP_PAPI_AUTH_ID`: API key ID 
- `CORTEX_MCP_PAPI_AUTH_HEADER`: API key secret 
- `CORTEX_MCP_PAPI_URL`: Cortex PAPI server URL

### Optional Environment Variables
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CORTEX_MCP_UPDATE_FOLDER`: Path to the content folder for updates

## Usage Examples

### Starting the server with environment variables:

```bash
export CORTEX_MCP_PAPI_AUTH_ID=12345
export CORTEX_MCP_PAPI_AUTH_HEADER="your-api-key-secret"
export CORTEX_MCP_PAPI_URL="https://api-your-cortex-server.com"
export LOG_LEVEL="INFO"

python src/cli.py start
```


```bash
python src/cli.py start \
    --api_key_id 12345 \
    --api_key_secret "your-api-key-secret" \
    --server-url "https://your-cortex-server.com" \
    --log-level INFO
```

### Updating remote components:

```bash
# Using default folder
python src/cli.py update

# Using custom folder
python src/cli.py update --folder /path/to/custom/folder
```

## Configuration Priority

Command-line arguments take precedence over environment variables. If neither is provided for required parameters, the application will exit with an error.

## Troubleshooting

### Common Issues

**API Authentication Errors:**
- Ensure your API key ID and secret are correct
- Verify the server URL is accessible
- Check that your API key has the necessary permissions

**Update Command Fails:**
- Verify the target folder exists and is writable
- Check network connectivity to the Cortex API

**Server Won't Start:**
- Check that no other process is using the same port
- Verify all required environment variables are set
- Check the log output for specific error messages

## Help

For general help:
```bash
python src/cli.py --help
```

For help with a specific command:
```bash
python src/cli.py start --help
python src/cli.py update --help
```
