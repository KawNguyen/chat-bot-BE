import os
from typing import Optional

import httpx


class AIClient:
    # """OpenAI-compatible AI client for LM Studio.

    # Environment variables:
    # - `AI_API_URL`: URL to LM Studio API (e.g., http://localhost:1234/v1/chat/completions)
    # - `AI_MODEL`: model identifier (default `mistralai/mistral-7b-instruct-v0.3`)
    # - `AI_API_KEY`: optional Bearer token
    # """

    def __init__(self, api_url: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv("AI_API_URL")
        self.model = model or os.getenv("AI_MODEL", "mistralai/mistral-7b-instruct-v0.3")
        self.api_key = api_key or os.getenv("AI_API_KEY")
        if not self.api_url:
            raise ValueError("AI_API_URL must be set to call the model endpoint")

    async def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Send prompt to LM Studio using OpenAI-compatible API format.
        
        LM Studio uses the OpenAI chat completions format:
        POST /v1/chat/completions
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # OpenAI-compatible format that LM Studio expects
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Parse OpenAI-format response
        if isinstance(data, dict) and "choices" in data:
            choices = data["choices"]
            if choices and len(choices) > 0:
                choice = choices[0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
        
        # Fallback parsing
        return str(data)
