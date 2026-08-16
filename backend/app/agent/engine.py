import logging
import asyncio
from typing import Dict, Any, Optional

from .models import TaskContext, TaskState, EvaluationVerdict
from .planner import TaskPlanner
from .executor import TaskExecutor
from .evaluator import TaskEvaluator
from .verifier import TaskVerifier

logger = logging.getLogger("TaskEngine")

class TaskEngine:
    def __init__(self, ai_provider, tool_registry):
        self.ai = ai_provider
        self.tools = tool_registry
        self.planner = TaskPlanner(ai_provider)
        self.executor = TaskExecutor(ai_provider, tool_registry)
        self.evaluator = TaskEvaluator(ai_provider)
        self.verifier = TaskVerifier(ai_provider)

    def _get_next_ready_step(self, context: TaskContext):
        if not context.plan:
            return None
            
        for step in context.plan.steps:
            if not step.completed:
                deps_met = True
                for dep_id in step.dependencies:
                    dep_step = next((s for s in context.plan.steps if s.id == dep_id), None)
                    if dep_step and not dep_step.completed:
                        deps_met = False
                        break
                
                if deps_met:
                    return step
        return None

    def _all_steps_completed(self, context: TaskContext) -> bool:
        if not context.plan or not context.plan.steps:
            return False
        return all(step.completed for step in context.plan.steps)

    async def _synthesize_final_response(self, user_goal: str, context: TaskContext) -> str:
        """Synthesizes a user-friendly summary of all steps and findings."""
        history_summary = ""
        for i, event in enumerate(context.history):
            if "step" in event and "result" in event:
                history_summary += f"Step {i+1} [{event['step']}]:\n{event['result']}\n\n"

        prompt = [
            {"role": "system", "content": "You are JARVIS. You have executed a task for the user. Synthesize the final outcome into 1 concise, factual sentence. Do not list internal steps, debugging codes, or ask follow-up questions."},
            {"role": "user", "content": f"User Goal: {user_goal}\n\nExecution Log:\n{history_summary}\n\nProvide the compact final response:"}
        ]
        
        try:
            res = await self.ai.chat(prompt)
            return res.strip()
        except Exception:
            return f"Completed: {user_goal}."

    async def execute_task(self, user_goal: str, memory_context: str) -> str:
        logger.info(f"Starting complex task engine for goal: {user_goal}")
        
        context = TaskContext(state=TaskState.RUNNING, memory_context=memory_context)
        available_tools = self.tools.get_tool_schemas()
        
        # Initial Planning
        context.plan = await self.planner.plan(user_goal, context, available_tools)
        
        if not context.plan:
            context.state = TaskState.FAILED
            return "Failed to generate a plan for the task."

        max_loops = 15
        loops = 0
        step_retry_counts: Dict[str, int] = {}
        
        while context.state == TaskState.RUNNING and loops < max_loops:
            loops += 1
            
            # Replan if needed
            if context.plan is None:
                context.plan = await self.planner.replan(user_goal, context, available_tools)
                if not context.plan:
                    context.state = TaskState.FAILED
                    return "Failed to replan task."

            # Find next ready step
            step = self._get_next_ready_step(context)
            
            if not step:
                if self._all_steps_completed(context):
                    # Verification phase
                    verification = await self.verifier.verify(user_goal, context)
                    if verification.verified:
                        context.state = TaskState.COMPLETED
                        return await self._synthesize_final_response(user_goal, context)
                    else:
                        logger.info(f"Verification indicated missing items: {verification.missing}. Replanning...")
                        context.plan = None
                        context.history.append({"event": "verification_failed", "reasoning": verification.reasoning})
                        continue
                else:
                    # Fallback to first uncompleted step if dependency IDs were misnamed by LLM
                    uncompleted = [s for s in context.plan.steps if not s.completed]
                    if uncompleted:
                        step = uncompleted[0]
                    else:
                        context.state = TaskState.FAILED
                        return "Execution error: Dependent steps could not resolve."

            # Execute step
            result = await self.executor.execute_step(step, context)
            
            # Evaluate step result
            evaluation = await self.evaluator.evaluate(step, result)
            
            context.history.append({
                "step": step.description,
                "result": result,
                "verdict": evaluation.verdict,
                "reasoning": evaluation.reasoning
            })

            if evaluation.verdict == EvaluationVerdict.SUCCESS:
                step.completed = True
                step.result = result
            
            elif evaluation.verdict == EvaluationVerdict.RETRY:
                count = step_retry_counts.get(step.id, 0) + 1
                step_retry_counts[step.id] = count
                if count >= 3:
                    logger.warning(f"Step {step.id} exceeded retry limit. Replanning...")
                    context.plan = None
                else:
                    logger.info(f"Retrying step {step.id} (attempt {count})...")
                
            elif evaluation.verdict == EvaluationVerdict.REPLAN:
                logger.info(f"Replanning requested after step {step.id}.")
                context.plan = None
                
            elif evaluation.verdict == EvaluationVerdict.FAIL:
                logger.warning(f"Step {step.id} failed: {evaluation.reasoning}")
                context.state = TaskState.FAILED
                if context.history:
                    return await self._synthesize_final_response(user_goal, context)
                return f"Unable to complete task: {evaluation.reasoning}"
                
        if context.state != TaskState.COMPLETED:
            if context.history:
                return await self._synthesize_final_response(user_goal, context)
            return "Task completed."
            
        return "Task completed."
