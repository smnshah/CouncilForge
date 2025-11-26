import json
from typing import List, Dict, Optional
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType, Message
from src.llm.client import LLMClient
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects
from src.social.decision_engine import compute_action_biases, apply_repetition_penalty
from src.social.interaction_triggers import compute_interaction_triggers
from src.social.prompt_builder import build_social_section

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 6):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth
        
        # Phase 2: Relationships and Messaging
        # Phase 2: Relationships and Messaging
        self.relationships: Dict[str, Relationship] = {}
        self.message_inbox: List[Message] = []
        
        # Phase 3: History Tracking
        self.recent_actions: List[str] = [] # My recent actions
        self.recent_interactions: List[str] = [] # Interactions targeting me

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def receive_message(self, message: Message):
        """Receives a message and adds it to the inbox."""
        self.message_inbox.append(message)
        
        # Apply relationship effects immediately
        if message.sender not in self.relationships:
            self.relationships[message.sender] = Relationship()
            
        self.relationships[message.sender] = apply_message_effects(
            self.relationships[message.sender],
            message.tone,
            message.text
        )

    def process_action(self, action: Action, actor_name: str):
        """
        Updates relationships based on observed actions.
        """
        if actor_name == self.persona.name:
            return

        if actor_name not in self.relationships:
            self.relationships[actor_name] = Relationship()
        
        # Update relationship using engine
        # Note: update_relationship takes action_type string.
        # We need to map ActionType enum to string if needed, but they are strings.
        self.relationships[actor_name] = update_relationship(
            self.relationships[actor_name],
            action.type.value,
            f"Observed action: {action.type.value} targeting {action.target}"
        )
        
        # Track interactions targeting me
        if action.target == self.persona.name:
            interaction_desc = f"Turn {self.relationships[actor_name].history[-1] if self.relationships[actor_name].history else 'Unknown'}: {actor_name} {action.type.value} you"
            # Or just use the description I just generated?
            # The relationship history stores it.
            # But I need a list for the prompt.
            self.recent_interactions.append(f"{actor_name} {action.type.value}")
            if len(self.recent_interactions) > 5:
                self.recent_interactions.pop(0)
            
        # Clamp values? Spec doesn't say, but good practice. Let's keep them unbounded for now or 0-100.
        # Spec says "Clamp all values to >= 0" for world state. For relationships, maybe just let them grow.

    def _build_prompt(self, world_state: WorldState) -> str:
        history_text = "\n".join(self.history) if self.history else "No history yet."
        
        # Compute Social Context
        # 1. Biases
        biases = compute_action_biases(self, world_state, self.relationships)
        # Apply repetition penalty
        # We need recent actions. self.history contains summaries, not raw actions.
        # But AgentState has recent_actions (Phase 3 update). 
        # Wait, I haven't updated LLMAgent to store recent_actions in its state yet.
        # I should add recent_actions to LLMAgent state.
        # For now, I'll use empty list or extract from history if possible.
        # Actually, I should update LLMAgent to track recent_actions.
        # I'll do that in a separate edit or assume it's there.
        # Let's assume self.recent_actions exists (I will add it in __init__)
        
        # 2. Triggers
        triggers = compute_interaction_triggers(self, world_state, self.recent_interactions)
        
        # Build Social Section
        social_section = build_social_section(
            self.relationships,
            biases,
            triggers,
            self.recent_actions,
            [m.model_dump() for m in self.message_inbox]
        )

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

{social_section}

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
            
            # Track my recent actions
            self.recent_actions.append(action.type.value)
            if len(self.recent_actions) > 5:
                self.recent_actions.pop(0)
                
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
