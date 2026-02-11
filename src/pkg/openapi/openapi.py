import logging
import os
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


def deep_merge(source: dict[str, Any], destination: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merges the 'source' dictionary into the 'destination' dictionary.

    Args:
        source (dict[str, Any]): The source dictionary to merge from
        destination (dict[str, Any]): The destination dictionary to merge into

    Returns:
        dict[str, Any]: The merged dictionary (modifies destination in-place and returns it)

    Example:
        >>> source = {'a': {'b': 2}}
        >>> dest = {'a': {'c': 3}}
        >>> result = deep_merge(source, dest)
        >>> print(result)
        {'a': {'b': 2, 'c': 3}}
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # Get the node in the destination or create a new one
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination


def bundle_specs(template_file: Path, *specs_dirs: Path) -> Optional[dict[str, Any]]:
    """
    Loads a main template, walks directories of specs, merges them,
    and returns a single bundled OpenAPI specification.

    Args:
        template_file (Path): Path to the main OpenAPI template file
        *specs_dirs (Path): Directories containing OpenAPI specification files to merge

    Returns:
        Optional[dict[str, Any]]: The bundled OpenAPI specification as a dictionary,
                                 or None if an error occurred

    Raises:
        FileNotFoundError: If the template file or specs directories don't exist
        yaml.YAMLError: If there's an error parsing YAML files

    """
    try:
        # 1. Load the main template
        logger.debug(f"Loading main template from '{template_file}'...")
        with open(template_file) as f:
            main_spec = yaml.safe_load(f)

        # Ensure top-level keys exist
        main_spec.setdefault('paths', {})
        main_spec.setdefault('components', {}).setdefault('schemas', {})

        # 2. Iterate over each specs directory and merge files from each one
        total_merged_files_count = 0

        for specs_dir in specs_dirs:
            logger.debug(f"Discovering and merging specs from '{specs_dir}'...")
            merged_files_count = 0

            for root, _, files in os.walk(specs_dir):
                for file in files:
                    if file.endswith(('.yaml', '.yml')):
                        file_path = os.path.join(root, file)
                        logger.debug(f"Merging '{file_path}'")

                        try:
                            with open(file_path) as f:
                                spec_to_merge = yaml.safe_load(f)

                            # Merge the contents into the main spec
                            main_spec = deep_merge(spec_to_merge, main_spec)
                            merged_files_count += 1

                        except yaml.YAMLError as e:
                            logger.error(f"Error parsing YAML file '{file_path}': {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing file '{file_path}': {e}")
                            continue

            logger.info(f"Successfully merged {merged_files_count} specification files from '{specs_dir}'")
            total_merged_files_count += merged_files_count

        logger.info(f"Total: Successfully merged {total_merged_files_count} specification files from {len(specs_dirs)} directories")
        return main_spec

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None
