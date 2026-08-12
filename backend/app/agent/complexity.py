import logging
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
        system_prompt = """You are a routing agent for JARVIS. Your job is to classify user requests into SIMPLE or COMPLEX.

SIMPLE tasks are direct and require little to no planning:
- "Open Chrome"
- "Check my GPU"
- "Search for RTX 5090 benchmarks"
- "Turn off Wi-Fi"
- "What time is it?"

COMPLEX tasks require multi-step planning, dependencies, observation, evaluation, and iteration:
- "Search for benchmarks, compare 5 sources, create a report, save it, and email it to me."
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
            logger.info(f"Complexity analysis for '{user_input}': {result}")
            return result.get("is_complex", False)
        except Exception as e:
            logger.error(f"Failed to detect complexity: {e}")
            # Default to simple on failure to avoid blocking basic commands
            return False
