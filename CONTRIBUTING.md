# Contributing to Cortex XSIAM MCP Server

Thank you for your interest in contributing to the Cortex XSIAM MCP Server! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Adding New Tools](#adding-new-tools)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cortex-mcp.git
   cd cortex-mcp
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/PaloAltoNetworks/cortex-mcp.git
   ```

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Poetry (dependency management)
- Docker (optional, for container testing)

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Cortex XSIAM API credentials
   ```

### Running the Server

```bash
python src/main.py
```

### Running Tests

```bash
poetry run pytest
```

## Making Changes

1. **Create a new branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our [style guidelines](#style-guidelines)

3. **Write or update tests** for your changes

4. **Run the test suite** to ensure nothing is broken:
   ```bash
   poetry run pytest
   ```

5. **Format your code**:
   ```bash
   poetry run black .
   poetry run ruff check --fix .
   ```

## Adding New Tools

The MCP server supports two types of tools:

### Python Tools

Create a new Python file in `src/usecase/custom_components/`:

```python
import logging
from typing import Annotated
from fastmcp import Context, FastMCP
from pydantic import Field
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher
from pkg.util import create_response

logger = logging.getLogger(__name__)

async def my_new_tool(
    ctx: Context,
    param1: Annotated[str, Field(description="Description of parameter")],
) -> str:
    """
    Tool description shown to the AI assistant.

    Use this tool when:
    - Scenario 1
    - Scenario 2

    Args:
        ctx: The FastMCP context
        param1: Description of the parameter

    Returns:
        JSON response with the result
    """
    fetcher = await get_fetcher(ctx)
    response = await fetcher.send_request("/your/api/endpoint", data={})
    return create_response(data=response)

class MyNewModule(BaseModule):
    def register_tools(self):
        self._add_tool(my_new_tool)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
```

### OpenAPI Tools

Create a new YAML file in `src/usecase/custom_components/openapi/`:

```yaml
openapi: 3.0.0
paths:
  /public_api/v1/your/endpoint:
    post:
      summary: Short description
      description: |-
        Detailed description of what the tool does.

        Use this when:
        - Scenario 1
        - Scenario 2
      operationId: my_new_tool
      tags:
        - Category
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                request_data:
                  type: object
      responses:
        '200':
          description: Success
```

### Tool Guidelines

1. **Descriptive names**: Use clear, action-oriented names (e.g., `isolate_endpoint`, `get_cases`)
2. **Comprehensive descriptions**: Include when to use, when not to use, and examples
3. **Error handling**: Always handle exceptions gracefully
4. **Logging**: Add appropriate logging for debugging
5. **Type hints**: Use proper type annotations for all parameters

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_util.py

# Run with coverage
poetry run pytest --cov=src
```

### Writing Tests

- Place tests in the `tests/` directory
- Use `pytest` fixtures for common setup
- Mock external API calls
- Test both success and error cases

Example test:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_my_new_tool():
    # Arrange
    mock_ctx = AsyncMock()

    # Act
    with patch('usecase.fetcher.get_fetcher') as mock_fetcher:
        mock_fetcher.return_value.send_request = AsyncMock(return_value={"reply": {}})
        result = await my_new_tool(mock_ctx, param1="test")

    # Assert
    assert "success" in result
```

## Submitting Changes

1. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "feat: add new endpoint isolation tool"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes you made and why
   - Include screenshots for UI changes (if applicable)

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Pull Request Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New features include tests
- [ ] Documentation is updated (if needed)
- [ ] Commit messages follow conventional commits format

## Style Guidelines

### Python

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 120)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Add type hints to all functions
- Write docstrings for public functions and classes

### YAML (OpenAPI)

- Use 2-space indentation
- Include comprehensive descriptions
- Document all parameters and responses
- Follow OpenAPI 3.0 specification

### Documentation

- Use clear, concise language
- Include code examples where helpful
- Keep README and guides up to date

## Questions?

If you have questions or need help, please:

1. Check existing [issues](https://github.com/PaloAltoNetworks/cortex-mcp/issues)
2. Open a new issue with the `question` label
3. Join our community discussions

Thank you for contributing!
