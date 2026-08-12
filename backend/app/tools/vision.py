import logging
import base64
import os
from typing import Any

logger = logging.getLogger("VisionTools")

def register_vision_tools(registry, computer_provider, ai_provider):
    async def analyze_screen(prompt: str = "Describe what is on my screen in detail.") -> str:
        """
        Takes a screenshot of the computer and analyzes it using the AI provider's vision capabilities.
        """
        try:
            # 1. Take a screenshot
            screenshot_result = await computer_provider.screenshot()
            
            # The computer_provider.screenshot() returns something like "Screenshot saved to <path>"
            if "Screenshot saved to " not in screenshot_result:
                return f"Failed to capture screen: {screenshot_result}"
                
            path = screenshot_result.split("Screenshot saved to ")[1].strip()
            
            if not os.path.exists(path):
                return "Failed to find the captured screenshot on disk."
                
            # 2. Read and encode the image
            with open(path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                
            # 3. Send to AI Provider
            logger.info(f"Sending screenshot to AI Provider with prompt: {prompt}")
            analysis = await ai_provider.vision(prompt, base64_image)
            
            return f"Screen Analysis: {analysis}"
        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return f"Error analyzing screen: {e}"

    registry.register(
        name="analyze_screen",
        description="Takes a screenshot of the user's primary monitor and passes it to the AI for visual analysis.",
        parameters={
            "type": "object", 
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "What you want to know about the screen. Defaults to 'Describe what is on my screen in detail.'"
                }
            }
        },
        func=analyze_screen,
        permission_level=1
    )
