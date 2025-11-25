import json
from typing import List
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType
from src.llm.client import LLMClient

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 2):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def _build_prompt(self, world_state: WorldState) -> str:
        history_text = "\n".join(self.history) if self.history else "No history yet."
        
        return f"""
You are {self.persona.name}.
Description: {self.persona.description}
Goals: {', '.join(self.persona.goals)}
Biases: {', '.join(self.persona.behavior_biases)}

Current World State:
- Turn: {world_state.turn}
- Resource Level: {world_state.resource_level}
- Stability: {world_state.stability}

Recent History:
{history_text}

Allowed Actions:
- increase_resource: Increases world resources by 10.
- decrease_resource: Decreases world resources by 10.
- support_agent: Increases world stability by 5. Target: 'world' or agent name.
- oppose_agent: Decreases world stability by 5. Target: 'world' or agent name.
- pass: Do nothing. Target: "none".

Instructions:
1. Analyze the situation based on your persona and goals.
2. Choose ONE action from the allowed list.
3. Output ONLY a valid JSON object matching this schema:
{{
  "type": "action_type",
  "target": "target_name",
  "reason": "short explanation"
}}

Example:
{{
  "type": "increase_resource",
  "target": "world",
  "reason": "We need more supplies to survive."
}}
"""

    def decide(self, world_state: WorldState) -> Action:
        prompt = self._build_prompt(world_state)
        action = self.llm_client.generate_action(prompt)
        return action
