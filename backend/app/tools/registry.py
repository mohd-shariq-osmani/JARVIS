import json
import logging
from typing import Dict, Any, List, Callable

logger = logging.getLogger("ToolRegistry")

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any], func: Callable, permission_level: int = 0):
        self._tools[name] = {
            "description": description,
            "parameters": parameters,
            "func": func,
            "permission_level": permission_level
        }
        logger.info(f"Registered tool: {name}")

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for name, data in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": data["description"],
                    "parameters": data["parameters"]
                }
            })
        return schemas

    async def execute_tool(self, name: str, args_str: str) -> str:
        if name not in self._tools:
            return f"Error: Tool '{name}' not found."
            
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
            # Permission check would go here in a real implementation
            func = self._tools[name]["func"]
            result = await func(**args)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution failed for {name}: {e}")
            return f"Error executing tool: {e}"
