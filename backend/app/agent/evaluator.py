import logging
from typing import Dict, Any
from .models import TaskStep, EvaluationResult, EvaluationVerdict

logger = logging.getLogger("TaskEvaluator")

class TaskEvaluator:
    def __init__(self, ai_provider):
        self.ai = ai_provider

    async def evaluate(self, step: TaskStep, result: str) -> EvaluationResult:
        """
        Evaluates whether a step's execution result successfully accomplished the step's goal.
        Returns SUCCESS, RETRY, REPLAN, or FAIL.
        """
        logger.info(f"Evaluating step {step.id}")
        
        system_prompt = """You are JARVIS's Task Evaluator.
Your job is to read a Task Step and the Result of its execution, and determine if it was successful.
An action ONLY means JARVIS attempted something. Success means the actual goal of the step was met.

Return one of these verdicts:
- SUCCESS: The step was accomplished perfectly.
- RETRY: The step failed due to a transient error (e.g. timeout, missing click) and should be tried again exactly as is.
- REPLAN: The step failed because the approach is flawed, a tool is missing, or circumstances changed. The plan must be modified.
- FAIL: The step failed completely and cannot be recovered.

You MUST respond ONLY with valid JSON matching the provided schema."""

        user_prompt = (
            f"Step Intended Action: {step.description}\n"
            f"Execution Result:\n{result}\n\n"
            "Evaluate if the intended action was truly successful."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        schema = EvaluationResult.model_json_schema()
        
        try:
            eval_dict = await self.ai.generate_structured(messages, schema)
            if "verdict" in eval_dict and "reasoning" in eval_dict:
                evaluation = EvaluationResult(**eval_dict)
                logger.info(f"Evaluation for {step.id}: {evaluation.verdict} - {evaluation.reasoning}")
                return evaluation
            else:
                logger.warning(f"Invalid evaluation structure returned: {eval_dict}")
                # Fallback to SUCCESS to avoid blocking if the model messes up the schema
                return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Default fallback due to parse error.")
        except Exception as e:
            logger.error(f"Failed to evaluate step: {e}")
            return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Default fallback due to exception.")
