from usecase.base_module import BaseModule


class BrokenModule(BaseModule):
    """Module that raises exceptions during initialization"""

    def __init__(self, mcp):
        super().__init__(mcp)
        raise RuntimeError("Intentional test error")

    def register_tools(self):
        raise RuntimeError("Intentional test error")

    def register_resources(self):
        raise RuntimeError("Intentional test error")
