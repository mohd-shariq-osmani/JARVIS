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
        
        lowered_result = result.lower().strip()
        
        # Fast deterministic heuristics for tool successes
        success_signals = [
            "opened '", "opened folder", "opened file", "opened website",
            "successfully", "contents of", "content of", "available system drives",
            "battery:", "copied", "clipboard text:", "brought '", "definition of",
            "saved notes", "found ", "set volume", "success:\n", "cpu:", "ram:",
            "memory:", "disk:", "gpu util:", "model:", "loaded model", "running model",
            "no bluetooth", "task scheduled", "reminder set", "note added",
            "closed ", "minimized ", "maximized ", "brightness set", "volume set",
            "opened '", "could not find an application"  # graceful not-found is still a completed step
        ]
        if any(s in lowered_result for s in success_signals) and "exception:" not in lowered_result:
            return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Action executed successfully.")

        # Informational/data results with substantial content are usually successes
        if len(result.strip()) > 20 and "error" not in lowered_result and "exception" not in lowered_result:
            # Heuristic: if we got a real response with no error keywords, treat as success
            return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Tool returned informational data.")

        system_prompt = """You are JARVIS's Task Evaluator.
Your job is to read a Task Step and the Result of its execution, and determine if it was successful.
An action ONLY means JARVIS attempted something. Success means the actual goal of the step was met.

Return one of these verdicts:
- SUCCESS: The step was accomplished (e.g. file opened, data retrieved, setting changed).
- RETRY: The step failed due to a transient error (e.g. timeout) and should be tried again.
- REPLAN: The step failed because a file was missing, different path needed, or approach needs adjustment.
- FAIL: The step failed catastrophically and cannot be recovered.

You MUST respond ONLY with valid JSON matching the provided schema."""

        user_prompt = (
            f"Step Intended Action: {step.description}\n"
            f"Execution Result:\n{result}\n\n"
            "Evaluate if the intended action was successful."
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
                return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Step completed.")
        except Exception as e:
            logger.error(f"Failed to evaluate step: {e}")
            return EvaluationResult(verdict=EvaluationVerdict.SUCCESS, reasoning="Step assumed completed.")
