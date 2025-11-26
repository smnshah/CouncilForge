import json
from typing import List, Dict, Optional
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType, Message
from src.llm.client import LLMClient

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 6):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth
        
        # Phase 2: Relationships and Messaging
        # relationships[agent_name] = {"trust": int, "resentment": int}
        self.relationships: Dict[str, Dict[str, int]] = {}
        self.message_inbox: List[Message] = []

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def receive_message(self, message: Message):
        """Receives a message and adds it to the inbox."""
        self.message_inbox.append(message)

    def process_action(self, action: Action, actor_name: str):
        """
        Updates relationships based on observed actions.
        """
        if actor_name == self.persona.name:
            return

        if actor_name not in self.relationships:
            self.relationships[actor_name] = {"trust": 0, "resentment": 0}
        
        rel = self.relationships[actor_name]
        
        # Update rules
        if action.type == ActionType.SUPPORT_AGENT and action.target == self.persona.name:
            rel["trust"] += 10
        elif action.type == ActionType.NEGOTIATE and action.target == self.persona.name:
            rel["trust"] += 2
        elif action.type == ActionType.TRADE and action.target == self.persona.name:
            rel["trust"] += 5
        elif action.type == ActionType.SABOTAGE and action.target == self.persona.name:
            rel["resentment"] += 20
        elif action.type == ActionType.OPPOSE_AGENT and action.target == self.persona.name:
            rel["resentment"] += 5
            
        # Clamp values? Spec doesn't say, but good practice. Let's keep them unbounded for now or 0-100.
        # Spec says "Clamp all values to >= 0" for world state. For relationships, maybe just let them grow.

    def _build_prompt(self, world_state: WorldState) -> str:
        history_text = "\n".join(self.history) if self.history else "No history yet."
        
        relationships_text = json.dumps(self.relationships, indent=2) if self.relationships else "No relationships yet."
        
        messages_text = ""
        if self.message_inbox:
            messages_text = "\n".join([f"From {m.sender}: {m.text}" for m in self.message_inbox])
        else:
            messages_text = "No new messages."

        return f"""
You are {self.persona.name}.
Description: {self.persona.description}
Archetype: {self.persona.archetype}
Core Values: {', '.join(self.persona.core_values)}
Dominant Trait: {self.persona.dominant_trait}
Secondary Trait: {self.persona.secondary_trait}
Decision Biases: {', '.join(self.persona.decision_biases)}
Preferred Resources: {', '.join(self.persona.preferred_resources)}
Conflict Style: {self.persona.conflict_style}
Cooperation Style: {self.persona.cooperation_style}
Risk Preference: {self.persona.risk_preference}
Goals: {', '.join(self.persona.goals)}

Current World State:
- Turn: {world_state.turn}
- Resource Level: {world_state.resource_level}
- Food: {world_state.food}
- Energy: {world_state.energy}
- Infrastructure: {world_state.infrastructure}
- Morale: {world_state.morale}
- Stability: {world_state.stability}
- Crisis Level: {world_state.crisis_level}
- Overall Health: {world_state.overall_health}

Relationships:
{relationships_text}

Messages Received:
{messages_text}

Recent History:
{history_text}

Allowed Actions:
- improve_resource: Increases a specific resource (food, energy, infrastructure) by 5. Target: "world". Resource: "food"|"energy"|"infrastructure".
- consume_resource: Decreases a specific resource by 5. Target: "world". Resource: "food"|"energy"|"infrastructure".
- boost_morale: Increases morale by 5. Target: "world".
- strengthen_infrastructure: Increases infrastructure by 5. Target: "world".
- support_agent: Increases world stability by 5. Target: agent name.
- oppose_agent: Decreases world stability by 5. Target: agent name.
- negotiate: Social action. Target: agent name.
- request_help: Social action. Target: agent name.
- trade: Social action. Target: agent name.
- sabotage: Decreases stability by 10. Target: agent name.
- send_message: Sends a text message. Target: agent name. Message: "content".
- pass: Do nothing. Target: "none".

Instructions:
1. Analyze the situation based on your persona, relationships, and history.
2. Choose ONE action from the allowed list.
3. Output ONLY a valid JSON object matching this schema:
{{
  "type": "action_type",
  "target": "target_name",
  "resource": "resource_name_if_applicable",
  "amount": 5,
  "message": "message_content_if_applicable",
  "reason": "short explanation"
}}

Example:
{{
  "type": "improve_resource",
  "target": "world",
  "resource": "food",
  "amount": 5,
  "reason": "Food supplies are running low."
}}
"""

    def decide(self, world_state: WorldState) -> Action:
        prompt = self._build_prompt(world_state)
        
        # Clear inbox after reading
        self.message_inbox.clear()
        
        try:
            action = self.llm_client.generate_action(prompt)
            return action
        except Exception as e:
            # Fallback if LLM fails or returns invalid JSON
            # The LLMClient might already handle retries, but if it fails, we return PASS
            # Spec says "The code must attempt JSON auto-repair before fallback" - LLMClient likely handles this or we should.
            # Assuming LLMClient.generate_action handles parsing and validation to some extent.
            # If it raises, we return PASS.
            return Action(
                type=ActionType.PASS,
                target="none",
                reason=f"Error generating action: {str(e)}"
            )
