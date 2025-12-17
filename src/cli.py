import argparse
import asyncio
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Optional

import requests

from config.config import get_config, reload_config
from main import async_main
from pkg.setup_logging import setup_logging
from pkg.util import MAIN_DIR, REMOTE_DIR
from usecase.fetcher import Fetcher, get_papi_url
from version import __version__

config = get_config()
logger = logging.getLogger("CORTEX MCP CLI")

# --- CLI Setup Functions ---

def setup_api_arguments(subparser: argparse.ArgumentParser):
    """
    Add API-related arguments to a subparser.

    Args:
        subparser: The argparse subparser to add arguments to
    """
    subparser.add_argument(
        '--api_key_id',
        type=int,
        default=config.papi_auth_id_key,
        help='The ID of the api key (default: environment variable: CORTEX_MCP_PAPI_AUTH_ID).'
    )
    subparser.add_argument(
        '--api_key_secret',
        type=str,
        default=config.papi_auth_header_key,
        help='The API key (default: environment variable: CORTEX_MCP_PAPI_AUTH_HEADER).'
    )
    subparser.add_argument(
        '--server-url',
        type=str,
        default=config.papi_url_env_key,
        help='The server url (default: environment variable: CORTEX_MCP_PAPI_URL).'
    )


def setup_commands(subparsers: argparse._SubParsersAction):
    """
    Defines the CLI commands, their arguments, and the functions they call.
    This function fulfills the "commands" part of your request.

    Args:
        subparsers: The argparse subparsers object to add commands to
    """
    # --- 'start' command ---
    start_parser: argparse.ArgumentParser = subparsers.add_parser('start', help='Start the MCP server.')
    setup_api_arguments(start_parser)
    start_parser.add_argument(
        "--log-level",
        help="Log level (default: info)",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
    )

    start_parser.set_defaults(func=start_server)

    # --- 'update' command ---
    update_parser: argparse.ArgumentParser = subparsers.add_parser('update',
                                                                   help='Update a folder containing cortex content (default is remote_tools folder).')
    setup_api_arguments(update_parser)

    update_parser.add_argument(
        '--folder',
        default=config.update_folder,
        type=str,
        help='The path to the content folder to be updated (default: environment variable: CORTEX_MCP_UPDATE_FOLDER).'
    )
    update_parser.set_defaults(func=update_tools)

    # --- 'version' command ---
    version_parser: argparse.ArgumentParser = subparsers.add_parser('version',
                                                                   help='display version information.')
    version_parser.set_defaults(func=display_version)

def setup_env(args: argparse.Namespace):
    """
    Setup environment variables for MCP server configuration.

    Args:
        args: Parsed command line arguments

    Raises:
        SystemExit: If required arguments are missing
    """
    # Validate required API key arguments
    if not args.api_key_id:
        logger.error("[Python] Error: API key ID is required. Please provide --api_key_id or set CORTEX_MCP_PAPI_AUTH_ID environment variable.")
        sys.exit(1)
    os.environ["CORTEX_MCP_PAPI_AUTH_ID"] = str(args.api_key_id)

    if not args.api_key_secret:
        logger.error("[Python] Error: API key is required. Please provide --api_key_secret or set CORTEX_MCP_PAPI_AUTH_HEADER environment variable.")
        sys.exit(1)
    os.environ["CORTEX_MCP_PAPI_AUTH_HEADER"] = args.api_key_secret

    if not args.server_url:
        logger.error("[Python] Error: PAPI Server URL is required. Please provide --server_url or set CORTEX_MCP_PAPI_URL environment variable.")
        sys.exit(1)
    os.environ["CORTEX_MCP_PAPI_URL"] = args.server_url

    if hasattr(args, "log_level") and args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level

    if hasattr(args, "folder") and args.folder:
        os.environ["CORTEX_MCP_UPDATE_FOLDER"] = args.folder

    global config
    config = reload_config()


def parse_args() -> argparse.Namespace:
    """
    Sets up the argument parser and parses the command-line arguments.

    Returns:
        Parsed command line arguments
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog='mcp_cli',
        description='A command-line interface for managing the Cortex MCP application.',
        epilog='For help with a specific command, type: mcp_cli <command> --help'
    )
    subparsers: argparse._SubParsersAction = parser.add_subparsers(dest='command', required=True,
                                                                   help='Available commands')
    setup_commands(subparsers)
    return parser.parse_args()


# --- Action Implementations ---

async def start_server(args: argparse.Namespace):
    """
    Contains the logic for the 'start' command.

    Args:
        args: Parsed command line arguments
    """
    setup_env(args)
    logger.info("--- Starting MCP Server ---",)
    try:
        await async_main(config.mcp_transport)
    except asyncio.CancelledError:
        logger.error("\n[Python] Server closed successfully.")
    except KeyboardInterrupt:
        logger.error("\n[Python] Server interrupted by user.")
    except Exception as error:
        logger.error(f"\n[Shell] Failed to execute the MCP server as expected: {error}")


# --- Update Folder Helper Functions ---

async def download_update_package() -> str:
    """
    Downloads the update package from the Cortex API.

    Returns:
        Path to the downloaded temporary zip file

    Raises:
        requests.exceptions.RequestException: If the download fails
    """
    logger.info("[Python] Requesting content update from Cortex API...")

    url = get_papi_url(config.papi_url_env_key)
    download_endpoint: str = f"{url}/public_api/v1/mcp/download/"

    fetcher: Fetcher = Fetcher(
        url=url,
        api_key_id=config.papi_auth_id_key,
        api_key=config.papi_auth_header_key
    )

    # Send POST request to download the zip file
    response: io.BytesIO = await fetcher.send_request(
        path=download_endpoint,
        data=json.dumps({"request_data": {"is_update": True}}),
        stream=True
    )

    logger.info("[Python] Download successful. Saving to temporary file...")

    # Create a temporary file to store the downloaded zip
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        temp_zip_path: str = temp_zip.name
        temp_zip.write(response.read())

    return temp_zip_path

def safe_extract(zip_ref: zipfile.ZipFile, extract_to: str):
    """
    Extracts the contents of the zip file from the Cortex MCP server ZIP file.
    Includes prevention against a malicious file zip slip.

    Args:
        zip_ref: Cortex MCP server ZIP file.
        extract_to: Path to the directory to extract the zip file.
    """
    for member in zip_ref.infolist():
        if os.path.isabs(member.filename) or ".." in member.filename:
            raise ValueError(f"Unsafe path: {member.filename}")
    zip_ref.extractall(extract_to)

def extract_remote_tools(zip_path: str) -> tuple[str, str]:
    """
    Extracts the zip file and returns the path to the remote_tools directory.

    Args:
        zip_path: Path to the zip file to extract

    Returns:
        Tuple containing (temp_extract_dir, extracted_remote_tools_path)

    Raises:
        zipfile.BadZipFile: If the zip file is invalid
        FileNotFoundError: If remote_tools directory is not found
    """
    logger.info("[Python] Extracting content...")

    # Create temporary directory for extraction
    temp_extract_dir: str = tempfile.mkdtemp()

    # Extract the zip file to temporary directory
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        safe_extract(zip_ref, temp_extract_dir)

    # Define the known path to remote tools in the extracted content
    extracted_remote_tools_path: str = os.path.join(temp_extract_dir, REMOTE_DIR.relative_to(MAIN_DIR.parent).as_posix())

    if not os.path.exists(extracted_remote_tools_path):
        raise FileNotFoundError(
            f"Could not find remote_tools directory at expected path: {extracted_remote_tools_path}")

    logger.info(f"[Python] Found remote_tools directory at: {extracted_remote_tools_path}")
    return temp_extract_dir, extracted_remote_tools_path


def backup_existing_remote_tools(target_path: str) -> Optional[str]:
    """
    Creates a backup of the existing remote_tools directory.

    Args:
        target_path: Path to the target remote_tools directory

    Returns:
        Path to the backup directory, or None if no backup was needed
    """
    if not os.path.exists(target_path):
        return None

    backup_path: str = f"{target_path}_backup_{int(time.time())}"
    logger.info(f"[Python] Backing up existing remote_tools to: {backup_path}")
    shutil.move(target_path, backup_path)
    return backup_path


def replace_remote_tools(extracted_path: str, target_path: str, backup_path: Optional[str] = None):
    """
    Replaces the target remote_tools directory with the extracted one.

    Args:
        extracted_path: Path to the extracted remote_tools directory
        target_path: Path where the remote_tools should be placed
        backup_path: Path to the backup directory for rollback (optional)

    Raises:
        Exception: If the replacement fails, will attempt to restore backup
    """
    try:
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Move the new remote_tools directory to the target location
        shutil.move(extracted_path, target_path)
        logger.info(f"[Python] Successfully replaced remote_tools directory at: {target_path}")

        # Remove backup if everything succeeded
        if backup_path and os.path.exists(backup_path):
            shutil.rmtree(backup_path)
            logger.info("[Python] Removed backup directory.")

    except Exception as e:
        # Restore backup if something went wrong
        if backup_path and os.path.exists(backup_path):
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.move(backup_path, target_path)
            logger.info("[Python] Restored backup due to error.")
        raise e


def show_updated_contents(target_path: str):
    """
    Displays the contents of the updated remote_tools directory.

    Args:
        target_path: Path to the remote_tools directory
    """
    logger.info("\n[Shell] Listing contents of the updated remote_tools directory...")
    try:
        if sys.platform == 'win32':
            subprocess.run(['dir', target_path], shell=True, check=True)
        else:
            subprocess.run(['ls', '-l', target_path], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[Python] Error: A shell command failed with exit code {e.returncode}.")
    except FileNotFoundError:
        logger.error("[Python] Error: 'ls' or 'dir' command not found. Are they in your PATH?")


def cleanup_temp_files(temp_zip_path: Optional[str] = None, temp_extract_dir: Optional[str] = None):
    """
    Cleans up temporary files and directories.

    Args:
        temp_zip_path: Path to temporary zip file (optional)
        temp_extract_dir: Path to temporary extraction directory (optional)
    """
    logger.info("\n[Python] Cleaning up temporary files...")

    if temp_zip_path and os.path.exists(temp_zip_path):
        try:
            os.unlink(temp_zip_path)
            logger.info("[Python] Temporary zip file cleaned up.")
        except OSError as e:
            logger.error(f"[Python] Warning: Could not remove temporary file {temp_zip_path}: {e}")

    if temp_extract_dir and os.path.exists(temp_extract_dir):
        try:
            shutil.rmtree(temp_extract_dir)
            logger.info("[Python] Temporary extraction directory cleaned up.")
        except OSError as e:
            logger.warning(f"[Python] Warning: Could not remove temporary directory {temp_extract_dir}: {e}")


async def update_tools(args: argparse.Namespace):
    """
    Contains the logic for the 'update' command.
    Updates the remote_tools directory with content from the Cortex API.

    Args:
        args: Parsed command line arguments
    """
    setup_env(args)
    logger.info("--- Updating Content Folder ---")

    # Define the target remote_tools path in the filesystem
    target_remote_tools_path: str = config.update_folder
    logger.info(f"[Python] Validating path: {target_remote_tools_path}...")
    if not os.path.isdir(target_remote_tools_path):
        logger.error(f"[Python] Error: The specified folder '{target_remote_tools_path}' does not exist.")
        return

    logger.info("[Python] cortex tools directory detected. Commencing update...")

    temp_zip_path: Optional[str] = None
    temp_extract_dir: Optional[str] = None

    try:
        # Download the update package
        temp_zip_path = await download_update_package()

        # Extract and locate remote_tools directory
        temp_extract_dir, extracted_remote_tools_path = extract_remote_tools(temp_zip_path)

        # Backup existing remote_tools directory
        backup_path: Optional[str] = backup_existing_remote_tools(target_remote_tools_path)

        # Replace with new remote_tools directory
        replace_remote_tools(extracted_remote_tools_path, target_remote_tools_path, backup_path)

        # Show the updated contents
        show_updated_contents(target_remote_tools_path)

        logger.info("\n[Python] remote_tools update process complete.")

    except requests.exceptions.RequestException as e:
        logger.error(f"[Python] Error: Failed to download content from API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"[Python] HTTP Status Code: {e.response.status_code}")
            logger.error(f"[Python] Response: {e.response.text}")
    except zipfile.BadZipFile:
        logger.error("[Python] Error: Downloaded file is not a valid zip archive.")
    except FileNotFoundError as e:
        logger.error(f"[Python] Error: {e}")
    except Exception as e:
        logger.error(f"[Python] Unexpected error during update: {e}")
    finally:
        # Always clean up temporary files
        cleanup_temp_files(temp_zip_path, temp_extract_dir)

async def display_version(_: argparse.Namespace):
    logger.info(f"[Python] Cortex MCP Server Version: {__version__}")

def main_cli():
    """
    Main entry point for the CLI script.
    """
    setup_logging(config)
    args: argparse.Namespace = parse_args()
    try:
        asyncio.run(args.func(args))
    except KeyboardInterrupt:
        logger.info("\n[Python] Application interrupted by user.")
    except Exception as e:
        logger.error(f"\n[Python] Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main_cli()

