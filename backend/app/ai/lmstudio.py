import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from .provider import AIProvider

logger = logging.getLogger("LMStudioProvider")

class LMStudioProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.active = False
        self._cancel_flag = False

    async def initialize(self) -> bool:
        self.active = await self.health_check()
        return self.active

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LM Studio health check failed: {e}")
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
        if not model:
            models = await self.list_models()
            model = models[0] if models else "local-model"
        
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
            logger.error(f"Chat failed: {e}")
            return f"Error communicating with local AI: {e}"

    async def stream_chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None):
        if not model:
            models = await self.list_models()
            model = models[0] if models else "local-model"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
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
                            delta = data_json["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            yield f" [Stream Error: {e}]"

    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], model: Optional[str] = None) -> Dict[str, Any]:
        if not model:
            models = await self.list_models()
            model = models[0] if models else "local-model"
            
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
            logger.error(f"Tool execution failed: {e}")
            return {"content": f"Error: {e}"}

    async def generate_structured(self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        if not model:
            models = await self.list_models()
            model = models[0] if models else "local-model"
            
        system_instruction = (
            "You are a structured reasoning engine. You must respond ONLY with a single valid JSON object that satisfies this JSON schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            "Do not include any conversational filler or markdown formatting outside the JSON object. Output raw JSON ONLY."
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
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema}
            }
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # Robust JSON extraction
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
                # Find outermost { ... }
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(content[start:end+1])
                raise
        except Exception as e:
            logger.warning(f"json_schema generation failed in LM Studio ({e}), attempting prompt-only JSON...")
            try:
                # Fallback to plain prompt without response_format
                fallback_payload = {
                    "model": model,
                    "messages": structured_messages,
                    "temperature": 0.1
                }
                fb_res = await self.client.post(f"{self.base_url}/chat/completions", json=fallback_payload)
                fb_res.raise_for_status()
                fb_content = fb_res.json()["choices"][0]["message"]["content"]
                start = fb_content.find('{')
                end = fb_content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(fb_content[start:end+1])
            except Exception as fb_err:
                logger.error(f"Structured generation fallback failed: {fb_err}")
            return {}

    async def vision(self, prompt: str, base64_image: str, model: Optional[str] = None) -> str:
        if not model:
            models = await self.list_models()
            model = models[0] if models else "local-model"
            
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
            logger.error(f"Vision failed: {e}")
            return f"Error communicating with local AI vision: {e}"

    async def cancel(self):
        self._cancel_flag = True

    async def shutdown(self):
        await self.client.aclose()
