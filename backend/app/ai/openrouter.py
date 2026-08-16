import httpx
import json
import logging
import os
from typing import List, Dict, Any, Optional
from .provider import AIProvider

logger = logging.getLogger("OpenRouterProvider")

class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "http://localhost:5173", # standard for dev
                "X-Title": "JARVIS Local Assistant"
            }
        )
        self.active = False
        self._cancel_flag = False

    async def initialize(self) -> bool:
        if not self.api_key:
            logger.warning("OpenRouter initialized without API key.")
            return False
        self.active = await self.health_check()
        return self.active

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            # OpenRouter doesn't have a simple health endpoint, testing models
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            return []
        except Exception:
            return []

    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: OpenRouter API Key missing."
        
        # Default model if not specified
        model = model or "google/gemma-7b-it"
        
        payload = {
            "model": model,
            "messages": messages,
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Cloud Chat failed: {e}")
            return f"Error communicating with Cloud AI: {e}"

    async def stream_chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None):
        if not self.api_key:
            yield "Error: OpenRouter API Key missing."
            return

        model = model or "google/gemma-7b-it"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        self._cancel_flag = False

        try:
            async with self.client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if self._cancel_flag:
                        break
                    
                    if chunk.startswith("data: "):
                        data_str = chunk[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Cloud Stream failed: {e}")
            yield f" [Cloud Stream Error: {e}]"

    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], model: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"content": "Error: OpenRouter API Key missing."}

        model = model or "google/gemma-7b-it"
        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto"
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except Exception as e:
            logger.error(f"Cloud Tool execution failed: {e}")
            return {"content": f"Cloud Error: {e}"}

    async def generate_structured(self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        model = model or "google/gemma-4-26b-a4b-it:free"
        
        system_instruction = (
            "You are a structured reasoning engine. You must respond ONLY with a single valid JSON object that satisfies this JSON schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            "Do not include any markdown code blocks, conversational text, or explanation outside the JSON object. Output raw JSON ONLY."
        )
        
        structured_messages = []
        system_added = False
        for msg in messages:
            if msg["role"] == "system":
                structured_messages.append({"role": "system", "content": f"{msg['content']}\n\n{system_instruction}"})
                system_added = True
            else:
                structured_messages.append(msg)
                
        if not system_added:
            structured_messages.insert(0, {"role": "system", "content": system_instruction})
            
        payload = {
            "model": model,
            "messages": structured_messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            content_clean = content.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            elif content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]
            content_clean = content_clean.strip()
            
            try:
                return json.loads(content_clean)
            except json.JSONDecodeError:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(content[start:end+1])
                raise
        except Exception as e:
            logger.error(f"Cloud Structured generation failed: {e}")
            return {}

    async def vision(self, prompt: str, base64_image: str, model: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: OpenRouter API Key missing."
            
        model = model or "google/gemma-4-e4b" # or a known openrouter vision model
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Cloud Vision failed: {e}")
            return f"Error communicating with Cloud AI vision: {e}"

    async def cancel(self):
        self._cancel_flag = True

    async def shutdown(self):
        await self.client.aclose()
