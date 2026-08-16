import logging
import json
from typing import Dict, Any, List, Optional
from .models import TaskPlan, TaskStep, TaskContext

logger = logging.getLogger("TaskPlanner")

class TaskPlanner:
    def __init__(self, ai_provider):
        self.ai = ai_provider

    def _normalize_plan_dict(self, result: Any, user_goal: str) -> Optional[TaskPlan]:
        if not isinstance(result, dict):
            return None

        # Unwrap if nested under 'plan' or 'task_plan'
        data = result.get("plan") or result.get("task_plan") or result
        if not isinstance(data, dict):
            return None

        objective = str(data.get("objective") or user_goal)
        raw_steps = data.get("steps") or []
        if not isinstance(raw_steps, list):
            return None

        normalized_steps: List[TaskStep] = []
        for i, step in enumerate(raw_steps):
            if isinstance(step, dict):
                step_id = str(step.get("id") or f"step_{i+1}")
                desc = str(step.get("description") or step.get("action") or step.get("task") or f"Step {i+1}")
                raw_deps = step.get("dependencies") or []
                deps = [str(d) for d in raw_deps] if isinstance(raw_deps, list) else []
                normalized_steps.append(TaskStep(id=step_id, description=desc, dependencies=deps))
            elif isinstance(step, str):
                normalized_steps.append(TaskStep(id=f"step_{i+1}", description=step, dependencies=[]))

        if normalized_steps:
            return TaskPlan(objective=objective, steps=normalized_steps)
        return None

    async def plan(self, user_goal: str, context: TaskContext, available_tools: Dict[str, Any]) -> Optional[TaskPlan]:
        system_prompt = f"""You are JARVIS's Task Planner.
Your job is to break down the user's complex goal into a sequence of actionable steps.

Available tools:
{json.dumps(available_tools, indent=2)}

Rules for planning:
1. Each step must be clearly defined and actionable.
2. If a step depends on the result of another step, define the dependency explicitly using step IDs.
3. Steps should map to available tools when possible.
4. Keep the plan concise and direct (3-6 steps max).
5. You MUST output a valid JSON object matching the schema with 'objective' and 'steps'."""

        user_prompt = f"Goal: {user_goal}\nMemory/Context: {context.memory_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        schema = TaskPlan.model_json_schema()
        
        try:
            result = await self.ai.generate_structured(messages, schema)
            plan = self._normalize_plan_dict(result, user_goal)
            if plan:
                logger.info(f"Generated plan for '{user_goal}' with {len(plan.steps)} steps.")
                return plan
            
            logger.warning(f"Failed to normalize plan structure from LLM output: {result}. Using fallback decomposition.")
            # Fallback decomposition if structured generation struggled
            return TaskPlan(
                objective=user_goal,
                steps=[
                    TaskStep(id="step_1", description=f"Analyze and execute: {user_goal}", dependencies=[])
                ]
            )
        except Exception as e:
            logger.error(f"Failed to generate task plan: {e}")
            return TaskPlan(
                objective=user_goal,
                steps=[
                    TaskStep(id="step_1", description=f"Execute: {user_goal}", dependencies=[])
                ]
            )

    async def replan(self, user_goal: str, context: TaskContext, available_tools: Dict[str, Any]) -> Optional[TaskPlan]:
        system_prompt = f"""You are JARVIS's Task Planner. The previous plan failed or needs to be adjusted.
Review the history, understand why it failed, and generate a NEW or UPDATED plan to achieve the goal.

Available tools:
{json.dumps(available_tools, indent=2)}

You MUST output a valid JSON object with 'objective' and 'steps'."""

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
            plan = self._normalize_plan_dict(result, user_goal)
            if plan:
                logger.info(f"Generated REPLAN for '{user_goal}' with {len(plan.steps)} steps.")
                return plan
            # Fallback: single step replan so the engine never hard-fails from replan returning None
            logger.warning("Replan returned unusable structure. Using single-step fallback.")
            return TaskPlan(
                objective=user_goal,
                steps=[TaskStep(id="step_r1", description=f"Re-attempt: {user_goal}", dependencies=[])]
            )
        except Exception as e:
            logger.error(f"Failed to replan: {e}")
            # Always return a minimal fallback so the engine can attempt recovery
            return TaskPlan(
                objective=user_goal,
                steps=[TaskStep(id="step_r1", description=f"Re-attempt: {user_goal}", dependencies=[])]
            )
