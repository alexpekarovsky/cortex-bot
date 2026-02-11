import importlib.util as importlib_util
import inspect
import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

from pkg.util import BUILTINS_DIR, CUSTOM_DIR, REMOTE_DIR
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

def discover_and_register_modules(mcp: FastMCP) -> list[BaseModule]:
    """
    Discover all Python files in usecase directories, find classes that implement BaseModule,
    instantiate them, and call their register_tools method.

    Args:
        mcp: The FastMCP instance to pass to BaseModule constructors

    Returns:
        List[BaseModule]: List of instantiated and registered modules

    Raises:
        ImportError: If a module cannot be imported
        ValueError: If a module file cannot be processed
    """
    usecase_dirs = [BUILTINS_DIR, CUSTOM_DIR, REMOTE_DIR]
    discovered_modules = []

    for usecase_dir in usecase_dirs:
        if not usecase_dir.exists():
            continue

        modules = _discover_modules_in_directory(usecase_dir, mcp)
        discovered_modules.extend(modules)

    return discovered_modules


def _discover_modules_in_directory(directory: Path, mcp: FastMCP) -> list[BaseModule]:
    """
    Discover BaseModule implementations in a specific directory.

    Args:
        directory: Directory to search for Python modules
        mcp: The FastMCP instance to pass to BaseModule constructors

    Returns:
        List[BaseModule]: List of instantiated modules from this directory
    """
    modules = []

    # Find all Python files recursively
    python_files = directory.rglob("*.py")

    for python_file in python_files:
        # Skip __init__.py files
        if python_file.name == "__init__.py":
            continue

        try:
            module_classes = _load_base_module_classes(python_file)

            for module_class in module_classes:
                # Instantiate the module
                module_instance = module_class(mcp)

                # Register tools and resources
                module_instance.register_tools()
                module_instance.register_resources()

                modules.append(module_instance)

        except Exception as e:
            # Log the error but continue processing other files
            logger.error(f"Failed to process module {python_file}: {e}")

    return modules


def _load_base_module_classes(python_file: Path) -> list[type[BaseModule]]:
    """
    Load a Python file and extract all classes that inherit from BaseModule.

    Args:
        python_file: Path to the Python file to load

    Returns:
        List[Type[BaseModule]]: List of classes that inherit from BaseModule

    Raises:
        ImportError: If the module cannot be imported
    """
    module_classes = []

    try:
        # Create a module spec from the file
        spec = importlib_util.spec_from_file_location(
            f"dynamic_module_{python_file.stem}",
            python_file
        )

        if spec is None or spec.loader is None:
            return module_classes

        # Load the module
        module = importlib_util.module_from_spec(spec)

        # Add to sys.modules to handle relative imports
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Find all classes in the module that inherit from BaseModule
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of BaseModule but not BaseModule itself
            if (issubclass(obj, BaseModule) and
                    obj is not BaseModule and
                    obj.__module__ == module.__name__):
                module_classes.append(obj)

    except Exception as e:
        raise ImportError(f"Failed to load module from {python_file}: {e}") from e

    return module_classes
