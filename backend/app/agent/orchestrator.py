import logging
from typing import Dict, Any, List

from .complexity import ComplexityDetector
from .engine import TaskEngine

logger = logging.getLogger("AgentOrchestrator")

class AgentOrchestrator:
    def __init__(self, ai_provider, tool_registry, memory_manager):
        self.ai = ai_provider
        self.tools = tool_registry
        self.memory = memory_manager
        
        # New components for Task Engine upgrade
        self.complexity = ComplexityDetector(self.ai)
        self.engine = TaskEngine(self.ai, self.tools)

    async def handle_request(self, user_input: str) -> str:
        # Construct context
        context = await self.memory.get_context(user_input)
        
        # Route to complex engine if needed
        is_complex = await self.complexity.detect(user_input)
        if is_complex:
            logger.info("Routing request to Complex Task Engine")
            return await self.engine.execute_task(user_input, context)
            
        logger.info("Routing request to Simple Direct execution")
        
        # Prepare system prompt for Simple mode
        system_prompt = """You are JARVIS, a highly capable AI assistant running on a local desktop environment.
You can execute tools. If you need to perform an action, use a tool. Never fake tool execution.

CRITICAL INSTRUCTIONS FOR TOOLS:
1. KEYBOARD HOTKEYS: If the user asks you to perform a keyboard shortcut (e.g., "Switch to tab 1", "Copy", "Paste"), you MUST use the `computer_hotkey` tool (e.g. keys: ["ctrl", "1"]). DO NOT use `computer_type` for shortcuts. `computer_type` is ONLY for typing literal strings of text.
2. SYSTEM HARDWARE: When asked to turn Wi-Fi or Bluetooth on or off, you MUST use the `toggle_system_radio` tool. When asked for GPU usage, use `get_gpu_usage`. When asked for mouse or peripheral battery, use `get_bluetooth_battery`. Do not try to use vision or PowerShell commands for these tasks.

CRITICAL INSTRUCTION FOR VOICE: Keep your spoken responses EXTREMELY brief. When asked to perform a task, execute the tool and simply respond with a short confirmation like "Opening settings" or "Task completed". Do not explain what tool you used, do not ask follow-up questions, and do not provide lengthy conversational filler. You are a fast, efficient voice assistant.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"System context: {context}\n\nUser request: {user_input}"}
        ]

        # Get available tool schemas
        available_tools = self.tools.get_tool_schemas()

        if available_tools:
            max_iterations = 5
            for _ in range(max_iterations):
                # Let model decide if a tool is needed
                response = await self.ai.generate_with_tools(messages, available_tools)
                
                if response.get("tool_calls"):
                    # Add assistant's tool call message BEFORE executing tools to maintain conversation history structure
                    messages.append(response) 
                    
                    for tool_call in response["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        tool_args = tool_call["function"]["arguments"]
                        
                        logger.info(f"Executing tool {tool_name} with args {tool_args}")
                        
                        # Execute tool
                        result = await self.tools.execute_tool(tool_name, tool_args)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": str(result)
                        })
                    # Loop continues, model will process the tool results in the next iteration
                else:
                    # Model provided a final response without tools
                    return response.get("content", "")
            
            # If we hit max iterations, just return the last message or a fallback
            return "Task too complex or looped too many times."
        else:
            # No tools available, simple chat
            return await self.ai.chat(messages)
