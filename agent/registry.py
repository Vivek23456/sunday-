from typing import Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, function: Callable):
        self._tools[name] = function

    def execute(self, name: str, arguments: dict):
        tool = self._tools.get(name)

        if tool is None:
            return f"Unknown tool: {name}"

        return tool(**arguments)

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools.keys())


registry = ToolRegistry()