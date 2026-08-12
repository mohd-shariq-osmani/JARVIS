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
                # Check if all dependencies are completed
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
        if not context.plan:
            return False
        return all(step.completed for step in context.plan.steps)

    async def execute_task(self, user_goal: str, memory_context: str) -> str:
        logger.info(f"Starting complex task engine for goal: {user_goal}")
        
        context = TaskContext(state=TaskState.RUNNING, memory_context=memory_context)
        
        # Initial Planning
        available_tools = self.tools.get_tool_schemas()
        context.plan = await self.planner.plan(user_goal, context, available_tools)
        
        if not context.plan:
            context.state = TaskState.FAILED
            return "Failed to generate an initial plan for the task."

        max_loops = 15  # Safety threshold
        loops = 0
        
        while context.state == TaskState.RUNNING and loops < max_loops:
            loops += 1
            
            # Replan if needed
            if context.plan is None:
                context.plan = await self.planner.replan(user_goal, context, available_tools)
                if not context.plan:
                    context.state = TaskState.FAILED
                    return "Failed to replan."

            # Find next step
            step = self._get_next_ready_step(context)
            
            if not step:
                # No more ready steps. Are we done?
                if self._all_steps_completed(context):
                    # Verification phase
                    verification = await self.verifier.verify(user_goal, context)
                    if verification.verified:
                        context.state = TaskState.COMPLETED
                        return f"Task completed successfully. Verification: {verification.reasoning}"
                    else:
                        logger.info("Verification failed. Forcing a replan.")
                        context.plan = None
                        context.history.append({"event": "verification_failed", "reasoning": verification.reasoning})
                        continue
                else:
                    context.state = TaskState.FAILED
                    return "Deadlock detected: Not all steps completed, but no step is ready to run."

            # Execute step
            result = await self.executor.execute_step(step, context)
            
            # Evaluate result
            evaluation = await self.evaluator.evaluate(step, result)
            
            # Update history
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
                logger.info(f"Retrying step {step.id}")
                # We simply loop again, the step is not completed, so it will be picked up again
                # A retry counter should ideally be implemented to prevent infinite loops on RETRY
                
            elif evaluation.verdict == EvaluationVerdict.REPLAN:
                logger.info(f"Replanning required after step {step.id} failure.")
                context.plan = None
                
            elif evaluation.verdict == EvaluationVerdict.FAIL:
                logger.error(f"Step {step.id} failed catastrophically.")
                context.state = TaskState.FAILED
                return f"Task failed at step: {step.description}. Reason: {evaluation.reasoning}"
                
        if context.state != TaskState.COMPLETED:
            return "Task engine exceeded maximum iterations or was interrupted."
            
        return "Task completed."
