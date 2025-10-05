from dataclasses import dataclass


@dataclass
class MCPContext:
    auth_headers: dict[str, str]
