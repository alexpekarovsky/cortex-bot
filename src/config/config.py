from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    A simple, flat configuration model using Pydantic.
    It loads settings from environment variables.
    """

    # --- Server Settings ---
    mcp_transport: str = Field("stdio", validation_alias="MCP_TRANSPORT")
    mcp_host: str = Field("0.0.0.0", validation_alias="MCP_HOST")
    mcp_port: int = Field(8080, validation_alias="MCP_PORT")
    mcp_path: str = Field("/api/v1/stream/mcp", validation_alias="MCP_PATH")
    elicitation_enabled: bool = Field(False, validation_alias="MCP_ELICITATION_ENABLED")
    write_tools_enabled: bool = Field(False, validation_alias="MCP_WRITE_TOOLS_ENABLED")
    isolate_endpoint_tool_enabled: bool = Field(False, validation_alias="MCP_ISOLATE_ENDPOINT_TOOL_ENABLED")

    # --- PAPI Settings ---
    papi_url_env_key: str = Field("CORTEX_MCP_PAPI_URL", validation_alias="PAPI_URL_ENV_KEY")
    papi_auth_header_key: str = Field("CORTEX_MCP_PAPI_AUTH_HEADER", validation_alias="PAPI_AUTH_HEADER_KEY")
    papi_auth_id_key: str = Field("CORTEX_MCP_PAPI_AUTH_ID", validation_alias="PAPI_AUTH_ID_KEY")

    max_objects_to_retrieve: int = Field(50, validation_alias="MAX_OBJECTS_TO_RETRIEVE")

    # --- Log Settings ---
    log_enable_uvicorn_access_logs: bool = Field(True, validation_alias="LOG_ENABLE_UVICORN_ACCESS_LOGS")
    log_level: str = Field("DEBUG", validation_alias="LOG_LEVEL")

    # This configuration tells Pydantic to:
    # 1. Load variables from a file named '.env' (for local development).
    # 2. Ignore any extra environment variables that aren't defined in this class.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Settings()
