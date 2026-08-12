import logging
import json
from typing import Dict, Any, List, Optional
from .models import TaskPlan, TaskStep, TaskContext

logger = logging.getLogger("TaskPlanner")

class TaskPlanner:
    def __init__(self, ai_provider):
        self.ai = ai_provider

    async def plan(self, user_goal: str, context: TaskContext, available_tools: Dict[str, Any]) -> Optional[TaskPlan]:
        system_prompt = f"""You are JARVIS's Task Planner.
Your job is to break down the user's complex goal into a sequence of actionable steps.

Available tools:
{json.dumps(available_tools, indent=2)}

Rules for planning:
1. Each step must be clearly defined and executable.
2. If a step depends on the result of another step, define the dependency explicitly using step IDs.
3. Steps should map to available tools when possible.
4. Keep the plan as simple as possible while ensuring the goal is met.
5. You MUST output the plan matching the provided JSON schema.
"""

        user_prompt = f"Goal: {user_goal}\nMemory/Context: {context.memory_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        schema = TaskPlan.model_json_schema()
        
        try:
            result = await self.ai.generate_structured(messages, schema)
            
            # Since result is a dict, we can instantiate a TaskPlan directly, 
            # but we need to safely handle potential validation errors.
            if "objective" in result and "steps" in result:
                plan = TaskPlan(**result)
                logger.info(f"Generated plan for '{user_goal}' with {len(plan.steps)} steps.")
                return plan
            else:
                logger.error(f"LLM returned invalid plan structure: {result}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate task plan: {e}")
            return None

    async def replan(self, user_goal: str, context: TaskContext, available_tools: Dict[str, Any]) -> Optional[TaskPlan]:
        # Same as plan, but we inject the current failed plan and history
        system_prompt = f"""You are JARVIS's Task Planner. The previous plan failed or needs to be adjusted.
Review the history, understand why it failed, and generate a NEW or UPDATED plan to achieve the goal.

Available tools:
{json.dumps(available_tools, indent=2)}

You MUST output the new plan matching the provided JSON schema.
"""

        user_prompt = f"Goal: {user_goal}\n"
        if context.plan:
            user_prompt += f"Previous Plan Objective: {context.plan.objective}\n"
        user_prompt += f"Execution History:\n{json.dumps(context.history, indent=2)}\n"
        user_prompt += f"Memory/Context: {context.memory_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        schema = TaskPlan.model_json_schema()
        
        try:
            result = await self.ai.generate_structured(messages, schema)
            if "objective" in result and "steps" in result:
                plan = TaskPlan(**result)
                logger.info(f"Generated REPLAN for '{user_goal}' with {len(plan.steps)} steps.")
                return plan
            return None
        except Exception as e:
            logger.error(f"Failed to replan: {e}")
            return None
