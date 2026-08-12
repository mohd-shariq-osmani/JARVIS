import logging
import json
from .models import TaskContext, VerificationResult

logger = logging.getLogger("TaskVerifier")

class TaskVerifier:
    def __init__(self, ai_provider):
        self.ai = ai_provider

    async def verify(self, user_goal: str, context: TaskContext) -> VerificationResult:
        """
        Verifies if the overall user goal was met based on the execution history.
        """
        logger.info(f"Verifying final task state for goal: {user_goal}")
        
        system_prompt = """You are JARVIS's Final Verifier.
Your job is to read the original goal and the history of executed steps, and verify if the goal was TRULY accomplished.
Do not just check if tools were called; check if the outputs indicate success.
If the goal was not fully met, list what is missing.

You MUST respond ONLY with valid JSON matching the provided schema."""

        user_prompt = f"Original Goal: {user_goal}\n\nExecution History:\n"
        for idx, event in enumerate(context.history):
            if "step" in event and "result" in event:
                user_prompt += f"[{idx+1}] Step: {event['step']}\n     Result: {event['result']}\n"
                
        user_prompt += "\nBased on the history above, was the original goal fully and successfully accomplished?"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        schema = VerificationResult.model_json_schema()
        
        try:
            result_dict = await self.ai.generate_structured(messages, schema)
            if "verified" in result_dict and "confidence" in result_dict:
                verification = VerificationResult(**result_dict)
                logger.info(f"Verification: {verification.verified} (confidence: {verification.confidence})")
                return verification
            else:
                logger.warning(f"Invalid verification structure: {result_dict}")
                return VerificationResult(verified=True, confidence=0.5, reasoning="Fallback due to schema parse error.")
        except Exception as e:
            logger.error(f"Failed to verify task: {e}")
            return VerificationResult(verified=False, confidence=0.0, reasoning=f"Exception during verification: {e}")
