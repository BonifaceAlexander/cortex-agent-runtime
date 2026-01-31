from typing import Dict, Callable, Any, Optional
import inspect

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """Register a python function as a tool"""
        self._tools[name] = func

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def execute(self, name: str, input_data: Dict[str, Any]) -> Any:
        """
        Execute a registered tool.
        Automatic support for simple argument mapping.
        """
        func = self.get_tool(name)
        if not func:
            raise ValueError(f"Tool '{name}' not found in registry.")

        # Simple signature introspection to match args
        sig = inspect.signature(func)
        
        # If function takes **kwargs or a single Dict, pass raw input
        # Otherwise, try to unpack
        try:
             # Basic implementation: pass kwargs that match signature
             valid_params = [p.name for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)]
             filtered_input = {k: v for k, v in input_data.items() if k in valid_params}
             return func(**filtered_input)
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{name}': {e}")
