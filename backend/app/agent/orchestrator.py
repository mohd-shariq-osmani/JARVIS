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
        system_prompt = """You are JARVIS, an advanced, highly intelligent AI desktop assistant.
You can execute tools and interact with the local operating system, web, and hardware. Never fake tool execution.

CRITICAL DIRECTIVES:
1. ALWAYS PROVIDE THE ACTUAL ANSWER: When the user asks a question (such as the weather, system specs, GPU stats, battery levels, online information, or calculations), ALWAYS execute the appropriate tool, read the tool's output, and speak/output the actual data directly to the user. Do NOT merely say "Searching" or "Task completed" without answering the question.
2. WEATHER: When asked about the weather, ALWAYS use `get_weather(city=...)` to retrieve the live temperature, conditions, and forecast.
3. LIVE WEB & INFORMATION: When asked for live news, facts, or data, use `search_information(query=...)` or `fetch_url_content(url=...)`.
4. CHATGPT & BROWSER: If the user asks to open ChatGPT or search something on ChatGPT in the browser, use `open_and_prompt_chatgpt(prompt=...)` or `search_web(query=..., engine="chatgpt")`.
5. WINDOW MANAGEMENT: Use `minimize_window`, `maximize_window`, `restore_window`, `close_window`, or `resize_window` for window control.
6. KEYBOARD & MOUSE: Use `computer_hotkey` for shortcuts, and `computer_type_and_enter` or `computer_press_key` for keyboard interactions.
7. VOICE TONE: Speak naturally, concisely, and intelligently like JARVIS in Iron Man. Deliver the exact requested information clearly and elegantly.
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
