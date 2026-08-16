import re
import logging
from typing import Dict, Any, List

from .complexity import ComplexityDetector
from .engine import TaskEngine

logger = logging.getLogger("AgentOrchestrator")

def compact_jarvis_response(text: str) -> str:
    """Cleans and strips unnecessary conversational fluff, disclaimers, and trailing questions."""
    if not text:
        return ""
    cleaned = text.strip()
    fluff_patterns = [
        r'(?i)\s*is there anything else (?:i can|you need|you would like me to|you need assistance with)\s*(?:assist|help|do|assist you with|for you)?[^.?!\n]*[.?!\n]?',
        r'(?i)\s*let me know if you (?:need|have|require)[^.?!\n]*[.?!\n]?',
        r'(?i)\s*feel free to ask[^.?!\n]*[.?!\n]?',
        r'(?i)\s*please let me know if[^.?!\n]*[.?!\n]?',
        r'(?i)\s*how else (?:may|can) i (?:help|assist)[^.?!\n]*[.?!\n]?',
        r'(?i)\s*as an ai (?:assistant|language model)[^,.]*[,.]?',
        r'(?i)\s*i would be happy to help[^.?!\n]*[.?!\n]?',
    ]
    for pat in fluff_patterns:
        cleaned = re.sub(pat, '', cleaned)
    cleaned = cleaned.strip()
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
    if len(sentences) > 2:
        cleaned = ' '.join(sentences[:2])
    return cleaned.strip()

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
            res = await self.engine.execute_task(user_input, context)
            return compact_jarvis_response(res)
            
        logger.info("Routing request to Simple Direct execution")
        
        # Prepare system prompt for Simple mode
        system_prompt = """You are JARVIS, an advanced AI desktop assistant.

CORE OBJECTIVE: Be hyper-concise, elegant, and factual like JARVIS in Iron Man.
- Strictly 1 sentence (maximum 2 short sentences).
- State ONLY the direct fact or action confirmation.
- NEVER include filler questions ("Is there anything else...", "Let me know if...").

CRITICAL TOOL INVOCATION RULES:
- When asked to open, view, or launch a file (e.g. image, screenshot, HTML, PDF, video), directly call `open_file(filepath=...)`!
- `open_file` automatically finds the file if given descriptions like 'html in downloads' or 'image in download folder'.
- When asked to open a folder or drive, directly call `open_folder(folder_path=...)` (e.g. 'Downloads', 'Desktop', 'D:\\').
- When asked to create a folder, directly call `create_folder(folder_path=...)` (e.g. 'Downloads/pen fight', 'Desktop/NewProject').
- NEVER claim you opened or created something in text without calling the tool!

AVAILABLE ACTIONS:
- Folder & Directory: `open_folder(folder_path=...)` | `create_folder(folder_path=...)` | `list_drives()`
- Files & Screenshot: `open_file(filepath=...)` | `read_file(filepath=...)` | `write_file(filepath=..., content=...)` | `analyze_screen()`
- Volume & Media: `set_system_volume(...)` | `media_control(...)` | `play_youtube(...)` | `play_spotify(...)`
- Power & System: `lock_workstation()` | `sleep_pc()` | `get_battery_status()` | `set_screen_brightness(...)`
- Live Facts: `get_current_time(location=...)` | `get_weather(city=...)` | `get_financial_quote(symbol=...)` | `convert_currency_or_units(...)` | `search_information(query=...)`
- Apps & Windows: `open_application(...)` | `close_application(...)` | `focus_window(...)` | `minimize_window(...)`
- Reminders & Notes: `schedule_task(...)` | `edit_scheduled_task(...)` | `cancel_scheduled_task(...)` | `add_note(...)` | `list_notes()`
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"System context: {context}\n\nUser request: {user_input}"}
        ]

        # Record user interaction in session context
        await self.memory.add_session_context(f"User: {user_input}")

        # Get available tool schemas
        available_tools = self.tools.get_tool_schemas()

        executed_tools = []
        final_response = ""
        if available_tools:
            max_iterations = 5
            for _ in range(max_iterations):
                # Let model decide if a tool is needed
                response = await self.ai.generate_with_tools(messages, available_tools)
                
                if response.get("tool_calls"):
                    # Sanitize assistant message for standard OpenAI API compatibility (prevent 400 Bad Request)
                    clean_assistant_msg = {
                        "role": "assistant",
                        "content": response.get("content") or None,
                        "tool_calls": response.get("tool_calls")
                    }
                    messages.append(clean_assistant_msg)
                    
                    for tool_call in response["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        tool_args = tool_call["function"]["arguments"]
                        executed_tools.append((tool_name, tool_args))
                        
                        logger.info(f"Executing tool {tool_name} with args {tool_args}")
                        
                        # Execute tool
                        result = await self.tools.execute_tool(tool_name, tool_args)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(result)
                        })
                    # Loop continues, model will process the tool results in the next iteration
                else:
                    # Model provided a final response without tools
                    final_response = response.get("content", "")
                    break
            
            if not final_response:
                final_response = "Task completed."
        else:
            # No tools available, simple chat
            final_response = await self.ai.chat(messages)

        # GUARANTEED ACTION INTERCEPTOR:
        # Prevent local model hallucinations where model says "Opened file: foo" without calling open_file
        user_lowered = user_input.lower()
        has_open_file = any(name == "open_file" for name, _ in executed_tools)
        has_open_folder = any(name == "open_folder" for name, _ in executed_tools)
        
        # Check folder opening intent
        if not has_open_folder and any(k in user_lowered for k in ["download folder", "downloads folder", "open downloads", "open download", "open desktop", "open documents"]):
            if "download" in user_lowered:
                logger.info("Interceptor: opening Downloads folder in Explorer")
                await self.tools.execute_tool("open_folder", {"folder_path": "Downloads"})
            elif "desktop" in user_lowered:
                logger.info("Interceptor: opening Desktop folder in Explorer")
                await self.tools.execute_tool("open_folder", {"folder_path": "Desktop"})
            elif "document" in user_lowered:
                logger.info("Interceptor: opening Documents folder in Explorer")
                await self.tools.execute_tool("open_folder", {"folder_path": "Documents"})

        # Check file opening intent
        if not has_open_file:
            wants_open_file = any(k in user_lowered for k in ["open", "show", "view", "launch", "display"]) and any(k in user_lowered for k in ["file", "image", "photo", "picture", "screenshot", "html", "video", "doc", "pdf", "recording", "voice", "notes", ".png", ".jpg", ".html", ".mp4", ".pdf", ".txt"])
            
            # Check if model response mentions a file name
            file_match = re.search(r'(?i)\b(?:opened|opening|file|image|screenshot|viewer)\s*[:\-]?\s*([a-zA-Z0-9_\-\s\(\)]+\.[a-zA-Z0-9]{2,5})\b', final_response)
            if file_match:
                extracted_file = file_match.group(1).strip()
                logger.info(f"Interceptor: opening extracted file '{extracted_file}'")
                await self.tools.execute_tool("open_file", {"filepath": extracted_file})
            elif wants_open_file:
                logger.info(f"Interceptor: opening target '{user_input}'")
                await self.tools.execute_tool("open_file", {"filepath": user_input})

        final_response = compact_jarvis_response(final_response)
        await self.memory.add_session_context(f"JARVIS: {final_response}")
        return final_response
