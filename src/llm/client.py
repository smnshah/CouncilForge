import json
import httpx
import os
from loguru import logger
from typing import Optional
from src.core.models import Action, ActionType
from groq import Groq

class LLMClient:
    """Unified LLM client: dev mode (Ollama) or prod mode (Groq API)."""
    
    def __init__(self, model_name: str, mode: str = "dev", retries: int = 3):
        self.model_name = model_name
        self.retries = retries
        self.mode = mode
        
        # Mode determines provider
        if mode == "prod":
            # Production: use Groq API (requires GROQ_API_KEY)
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment. Set it in .env or export it.")
            
            self.groq_client = Groq(api_key=api_key)
            logger.info(f"[PROD MODE] Using Groq API with model: {model_name}")
        else:
            # Dev: use local Ollama
            self.client = httpx.Client(base_url="http://localhost:11434", timeout=30.0)
            logger.info(f"[DEV MODE] Using Ollama with model: {model_name}")

    def generate_action(self, prompt: str, agent_name: Optional[str] = None) -> Action:
        """Generate action using configured provider."""
        for attempt in range(self.retries):
            try:
                if self.mode == "prod":
                    # Groq API call
                    completion = self.groq_client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a political agent. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1500,
                        response_format={"type": "json_object"}
                    )
                    response_text = completion.choices[0].message.content
                else:
                    # Ollama API call
                    response = self.client.post(
                        "/api/generate",
                        json={"model": self.model_name, "prompt": prompt, "stream": False, "format": "json"}
                    )
                    response.raise_for_status()
                    response_text = response.json().get("response", "")
                
                # Parse and validate
                action = Action(**json.loads(response_text))
                return action

            except Exception as e:
                logger.warning(f"{self.mode.upper()} failed (Attempt {attempt + 1}): {e}")
                continue
        
        logger.error(f"All {self.mode} retries failed. Defaulting to PASS.")
        return Action(type=ActionType.PASS, target="world", reason="LLM failure")

    def close(self):
        if self.mode == "dev":
            self.client.close()
