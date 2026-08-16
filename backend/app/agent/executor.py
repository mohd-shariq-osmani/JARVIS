import logging
import json
from typing import Dict, Any, List
from .models import TaskStep, TaskContext

logger = logging.getLogger("TaskExecutor")

class TaskExecutor:
    def __init__(self, ai_provider, tool_registry):
        self.ai = ai_provider
        self.tools = tool_registry

    async def execute_step(self, step: TaskStep, context: TaskContext) -> str:
        """
        Executes a specific step by prompting the AI to select the appropriate tool(s)
        based on the step description and returning the result.
        """
        logger.info(f"Executing step {step.id}: {step.description}")
        
        system_prompt = """You are JARVIS's Step Executor.
Your job is to execute a SPECIFIC task step by calling the appropriate tool(s).
Do not try to plan ahead, just execute the exact step requested.
If the step can be completed without a tool, just explain the result.
If a tool is needed, call it. When tool results are provided, provide a clear, concise confirmation of what was accomplished.
"""
        user_prompt = (
            f"Step to execute: {step.description}\n"
            f"Overall Objective: {context.plan.objective if context.plan else 'Unknown'}\n"
            "History of recent events:\n"
        )
        
        for event in context.history[-3:]:
            if "step" in event and "result" in event:
                user_prompt += f"- {event['step']}: {event['result']}\n"
                
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        available_tools = self.tools.get_tool_schemas()
        max_step_iterations = 3
        step_outputs = []
        
        for _ in range(max_step_iterations):
            try:
                response = await self.ai.generate_with_tools(messages, available_tools)
                
                if response.get("tool_calls"):
                    clean_assistant_msg = {
                        "role": "assistant",
                        "content": response.get("content") or None,
                        "tool_calls": response.get("tool_calls")
                    }
                    messages.append(clean_assistant_msg)
                    
                    for tool_call in response["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        tool_args = tool_call["function"]["arguments"]
                        
                        logger.info(f"Executor calling tool {tool_name} with args {tool_args}")
                        
                        try:
                            result = await self.tools.execute_tool(tool_name, tool_args)
                            tool_res_str = f"Tool '{tool_name}' returned: {result}"
                        except Exception as e:
                            tool_res_str = f"Tool '{tool_name}' failed with error: {e}"
                            result = tool_res_str
                            
                        step_outputs.append(tool_res_str)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": str(result)
                        })
                else:
                    final_text = response.get("content", "")
                    if final_text:
                        step_outputs.append(final_text)
                    break
            except Exception as e:
                logger.error(f"Execution iteration failed for step {step.id}: {e}")
                step_outputs.append(f"Execution error: {str(e)}")
                break
                
        return "\n".join(step_outputs) if step_outputs else "Step completed."
