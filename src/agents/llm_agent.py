import json
from typing import List, Dict, Optional
import traceback
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType, Message
from src.llm.client import LLMClient
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects
from src.social.decision_engine import compute_action_biases, apply_repetition_penalty, get_top_actions, get_recommended_targets
from src.social.interaction_triggers import compute_interaction_triggers
from src.social.prompt_builder import build_social_section
from src.social.emotion_engine import get_default_emotions, update_emotions, get_emotional_bias
from src.social.interpersonal_goals import get_default_goals, update_goals

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 6):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth
        
        # Phase 2: Relationships and Messaging
        # Phase 2: Relationships and Messaging
        self.relationships: Dict[str, Relationship] = {}
        self.messages_received: List[Message] = []
        
        # Phase 3: History Tracking
        self.recent_actions: List[str] = [] # My recent actions
        self.recent_interactions: List[str] = [] # Interactions targeting me
        
        # Phase 4: Emotions and Goals
        # emotions[agent_name] = {trust: float, ...}
        self.emotions: Dict[str, Dict[str, float]] = {}
        self.goals: Dict[str, Optional[str]] = get_default_goals()

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def receive_message(self, message: Message):
        """Receives a message and adds it to the inbox."""
        self.messages_received.append(message)
        
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
        self.relationships[actor_name] = update_relationship(
            self.relationships[actor_name],
            action.type.value,
            f"Observed action: {action.type.value} targeting {action.target}"
        )
        
        # Update emotions
        if actor_name not in self.emotions:
            self.emotions[actor_name] = get_default_emotions()
            
        is_target = (action.target == self.persona.name)
        self.emotions[actor_name] = update_emotions(
            self.emotions[actor_name],
            action.type.value,
            is_target
        )
        
        # Track interactions targeting me
        if is_target:
            interaction_desc = f"Turn {self.relationships[actor_name].history[-1] if self.relationships[actor_name].history else 'Unknown'}: {actor_name} {action.type.value} you"
            self.recent_interactions.append(f"{actor_name} {action.type.value}")
            if len(self.recent_interactions) > 5:
                self.recent_interactions.pop(0)

    def _build_prompt(self, world_state: WorldState, valid_targets: List[str]) -> str:
        # Lite History (Last 2 turns)
        history_text = "\n".join(self.history[-2:]) if self.history else "No history yet."
        
        # Compute Biases & Top Actions
        avg_emotions = get_default_emotions()
        if self.emotions:
            count = len(self.emotions)
            for em in self.emotions.values():
                for k, v in em.items():
                    avg_emotions[k] += v
            for k in avg_emotions:
                avg_emotions[k] /= count
        
        biases = compute_action_biases(self, world_state, self.relationships, avg_emotions, self.goals)
        biases = apply_repetition_penalty(biases, self.recent_actions)
        
        top_actions = get_top_actions(biases, top_n=5)
        top_actions_str = ", ".join(top_actions)
        
        # Recommended Targets
        recommendations = get_recommended_targets(self, self.relationships)
        rec_targets_str = ""
        for cat, target in recommendations.items():
            rec_targets_str += f"- For {cat}: {target}\n"
        if not rec_targets_str:
            rec_targets_str = "- None (No strong relationships yet)"

        # Lite Relationships (Score > 5 or recent)
        relationships_text = "Key Relationships:\n"
        has_rels = False
        if self.relationships:
            for agent, rel in self.relationships.items():
                if abs(rel.score) > 5:
                    relationships_text += f"- {agent}: Trust {rel.trust}, Resentment {rel.resentment}\n"
                    has_rels = True
        if not has_rels:
            relationships_text += "No significant relationships.\n"

        return f"""
You are {self.persona.name}.
Archetype: {self.persona.archetype}
Traits: {self.persona.dominant_trait}, {self.persona.secondary_trait}
Goals: {', '.join(self.persona.goals)}

World State:
- Food: {world_state.food}, Energy: {world_state.energy}, Infra: {world_state.infrastructure}
- Stability: {world_state.stability}, Crisis: {world_state.crisis_level}

{relationships_text}

Recent History:
{history_text}

YOUR RECOMMENDED ACTIONS (Choose ONE):
[{top_actions_str}]

RECOMMENDED TARGETS:
{rec_targets_str}

Output Schema:
{{
  "reasoning": "1-2 sentences explaining why you chose this action.",
  "type": "action_type",
  "target": "target_name",
  "resource": "resource_name_if_applicable",
  "amount": 5,
  "message": "message_content_if_applicable"
}}

Instructions:
1. Choose ONE action from the Recommended Actions list.
2. Use a Recommended Target if applicable.
3. Resource actions MUST target "world".
4. Social actions MUST target a specific agent.
5. Output ONLY valid JSON.
"""

    def decide(self, world_state: WorldState, valid_targets: List[str]) -> Action:
        # 1. Update Goals based on current emotions and world state
        # Ensure self emotions exist
        if "self" not in self.emotions:
            self.emotions["self"] = get_default_emotions()
            
        my_ambition = self.emotions["self"]["ambition"]
        
        # Iterate over all agents we have emotions toward
        for target_name, emotions in self.emotions.items():
            if target_name == "self":
                continue
                
            self.goals = update_goals(
                self.goals,
                emotions,
                target_name,
                world_state.stability,
                my_ambition
            )
            
            
        # 2. Build Prompt
        prompt = self._build_prompt(world_state, valid_targets)
        
        # Clear inbox
        self.messages_received.clear()
        
        try:
            # 3. Generate Action
            action = self.llm_client.generate_action(prompt, self.persona.name)
            
            # 4. Update History
            self.recent_actions.append(action.type.value)
            if len(self.recent_actions) > 5:
                self.recent_actions.pop(0)
                
            return action
        except Exception as e:
            print(f"DEBUG: LLMAgent decide error: {e}")
            traceback.print_exc()
            return Action(
                type=ActionType.PASS,
                target="none",
                reason=f"Error generating action: {str(e)}"
            )
