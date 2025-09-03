from dataclasses import dataclass
from typing import Dict


@dataclass
class MCPContext:
    auth_headers: Dict[str, str]
