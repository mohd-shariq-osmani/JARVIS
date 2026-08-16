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
1. WINDOW CONTROL: To minimize, maximize, restore, close, or resize windows, use `minimize_window`, `maximize_window`, `restore_window`, `close_window`, or `resize_window`.
2. WEB & SEARCH: To search for information or query ChatGPT in the browser, use `search_web(query=..., engine="google"|"chatgpt")` or `open_website(url=...)`. Use `computer_type_and_enter` or `computer_press_key("enter")` to type and submit queries.
3. KEYBOARD & MOUSE: If the user asks for keyboard shortcuts (e.g. "Copy", "Paste"), use `computer_hotkey`. For typing literal text, use `computer_type` or `computer_type_and_enter`.
4. HARDWARE: For Wi-Fi or Bluetooth, use `toggle_system_radio`. For GPU, use `get_gpu_usage`. For peripheral battery, use `get_bluetooth_battery`.
5. MEMORY: When asked to remember a fact or preference, use `remember`. To recall past facts, use `search_memory`.

CRITICAL INSTRUCTION FOR VOICE: Keep your spoken responses EXTREMELY brief. When asked to perform a task, execute the tool and simply respond with a short confirmation like "Minimizing window", "Opening ChatGPT", "Remembered", or "Task completed". Do not explain what tool you used and do not provide lengthy conversational filler.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"System context: {context}\n\nUser request: {user_input}"}
        ]

        # Record user interaction in session context
        await self.memory.add_session_context(f"User: {user_input}")

        # Get available tool schemas
        available_tools = self.tools.get_tool_schemas()

        final_response = ""
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
                    final_response = response.get("content", "")
                    break
            
            if not final_response:
                final_response = "Task too complex or looped too many times."
        else:
            # No tools available, simple chat
            final_response = await self.ai.chat(messages)

        await self.memory.add_session_context(f"JARVIS: {final_response}")
        return final_response
