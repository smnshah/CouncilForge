import json
import httpx
from loguru import logger
from typing import Optional, Dict, Any
from src.core.models import Action, ActionType

class LLMClient:
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434", retries: int = 3):
        self.model_name = model_name
        self.base_url = base_url
        self.retries = retries
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def generate_action(self, prompt: str) -> Action:
        """
        Sends a prompt to the LLM and expects a JSON response matching the Action schema.
        Retries on failure or invalid JSON.
        Returns a PASS action if all retries fail.
        """
        for attempt in range(self.retries):
            try:
                logger.debug(f"LLM Request (Attempt {attempt + 1}/{self.retries}):\n{prompt}")
                
                response = self.client.post(
                    "/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json" # Force JSON mode in Ollama
                    }
                )
                response.raise_for_status()
                result = response.json()
                response_text = result.get("response", "")
                
                logger.debug(f"LLM Response:\n{response_text}")
                
                # Parse JSON
                action_data = json.loads(response_text)
                
                # Validate with Pydantic
                action = Action(**action_data)
                return action

            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"LLM Generation failed (Attempt {attempt + 1}): {e}")
                continue
        
        logger.error("All LLM retries failed. Defaulting to PASS.")
        return Action(type=ActionType.PASS, target="world", reason="LLM failure or invalid output")

    def close(self):
        self.client.close()
