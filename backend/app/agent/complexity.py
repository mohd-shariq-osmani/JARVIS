import logging
import re
from typing import Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("ComplexityDetector")

class ComplexityAnalysis(BaseModel):
    is_complex: bool = Field(description="True if the task requires multi-step planning, dependencies, or deep reasoning. False if it's a simple, direct command.")
    reason: str = Field(description="Reasoning for this classification")

class ComplexityDetector:
    def __init__(self, ai_provider):
        self.ai = ai_provider

    async def detect(self, user_input: str) -> bool:
        lowered = user_input.lower().strip()

        # Fast heuristic checks for obvious multi-stage complex commands
        complex_signals = [
            " and then ", " first ", " step by step", "multi-step", "workflow",
            "clean up my", "organize my", "prepare my pc for", "compare and ",
            "generate a report", "create a file and ", "search and summarize"
        ]
        
        has_complex_signal = any(signal in lowered for signal in complex_signals)
        if has_complex_signal and len(lowered.split()) > 6:
            logger.info(f"Fast-path complexity detected for: '{user_input}'")
            return True

        # Fast heuristic checks for direct commands
        simple_prefixes = [
            "open ", "can you open ", "please open ", "show me ", "show ", "read ",
            "play ", "set a reminder", "schedule ", "what is ", "what time",
            "check my", "tell me", "how is", "convert ", "define ", "launch ",
            "close ", "minimize ", "maximize ", "mute ", "unmute ", "volume "
        ]
        if any(lowered.startswith(p) for p in simple_prefixes) and not has_complex_signal:
            return False

        # Direct file / folder / app action phrases (e.g. "there is a ... can you open it", "open image in downloads")
        direct_action_verbs = ["open", "launch", "read", "show", "view", "play", "start", "see", "display"]
        if any(v in lowered for v in direct_action_verbs) and not has_complex_signal:
            logger.info(f"Direct action detected for: '{user_input}'")
            return False

        system_prompt = """You are a routing agent for JARVIS. Your job is to classify user requests into SIMPLE or COMPLEX.

SIMPLE tasks are direct and require single tool calls or direct answers:
- "Open Chrome"
- "There is an image in downloads can you open it"
- "Check my GPU"
- "Edit the reminder of drinking water to 1:45 PM"
- "Remove that reminder"
- "Set a reminder to drink water at 1:45 PM"
- "What time is it in Tokyo?"
- "What is the weather?"

COMPLEX tasks require multi-step planning, sequential dependencies, observation, evaluation, or multi-stage execution:
- "Search for benchmarks, compare 5 sources, create a report, save it, and notify me."
- "Clean up my Downloads folder and group files by type."
- "Prepare my PC for gaming."
- "Find the three best local TTS models, compare quality and speed, and recommend one."

Respond ONLY with valid JSON matching the schema."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this request: '{user_input}'"}
        ]

        schema = ComplexityAnalysis.model_json_schema()
        
        try:
            result = await self.ai.generate_structured(messages, schema)
            if isinstance(result, dict) and "is_complex" in result:
                logger.info(f"Complexity analysis for '{user_input}': {result}")
                return bool(result.get("is_complex", False))
            return False
        except Exception as e:
            logger.error(f"Failed to detect complexity via AI: {e}")
            return False
