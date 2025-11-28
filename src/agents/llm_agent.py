"""
LLM Agent - Simplified Phase 1.5 Implementation

Streamlined agent with minimal prompt complexity for llama3.1:8b compatibility.
Focuses on clear, concise prompts with explicit action costs and examples.
"""

import json
from typing import List, Dict
import traceback
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType
from src.llm.client import LLMClient
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 2):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth
        
        # Simple relationship tracking (trust/resentment only)
        self.relationships: Dict[str, Relationship] = {}

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def receive_message(self, message):
        """
        Receives a message and updates relationships.
        Phase 1.5: Simplified - just update relationship based on tone.
        """
        from src.core.models import Message
        
        if message.sender not in self.relationships:
            self.relationships[message.sender] = Relationship()
            
        self.relationships[message.sender] = apply_message_effects(
            self.relationships[message.sender],
            message.tone
        )

    def process_action(self, action: Action, actor_name: str):
        """
        Updates relationships based on observed actions.
        """
        if actor_name == self.persona.name:
            return

        if actor_name not in self.relationships:
            self.relationships[actor_name] = Relationship()
        
        # Update relationship based on action type
        self.relationships[actor_name] = update_relationship(
            self.relationships[actor_name],
            action.type.value,
            f"Turn action: {action.type.value}"
       )

    def _build_prompt(self, world_state: WorldState, valid_targets: List[str]) -> str:
        """
        Builds a streamlined prompt for llama 8b model.
        
        New structure:
        1. Persona (concise)
        2. World State (simple table)
        3. Recent History (last 2 turns)
        4. Relationships (if significant)
        5. Available Actions (with costs)
        6. JSON Schema (with examples)
        7. Instructions (explicit steps)
        """
        
        # 1. Persona Section
        persona_section = f"""You are {self.persona.name}.
Archetype: {self.persona.archetype}
Traits: {self.persona.dominant_trait}, {self.persona.secondary_trait}
Goals: {', '.join(self.persona.goals)}"""

        # 2. World State (Simple Table)
        world_section = f"""
=== WORLD STATE (Turn {world_state.turn + 1}) ===
Treasury: {world_state.treasury}
Food: {world_state.food}
Energy: {world_state.energy}
Infrastructure: {world_state.infrastructure}
Morale: {world_state.morale}
Crisis: {world_state.crisis_level} {"(HIGH)" if world_state.crisis_level > 60 else "(MEDIUM)" if world_state.crisis_level > 30 else "(LOW)"}

Note: Resources decay by 2 each turn due to natural consumption."""

        # 3. Recent History
        history_text = "\\n".join(self.history[-2:]) if self.history else "No history yet."
        history_section = f"""
=== RECENT HISTORY ===
{history_text}"""

        # 4. Relationships (only if significant)
        relationships_section = ""
        if self.relationships:
            rel_lines = []
            for agent, rel in self.relationships.items():
                if abs(rel.score) > 3:  # Only show significant relationships
                    trust_str = f"+{rel.trust} trust" if rel.trust > 0 else f"{rel.trust} trust" if rel.trust < 0 else "0 trust"
                    resent_str = f"+{rel.resentment} resentment" if rel.resentment > 0 else f"{rel.resentment} resentment" if rel.resentment < 0 else "0 resentment"
                    rel_lines.append(f"{agent}: {trust_str}, {resent_str}")
            
            if rel_lines:
                relationships_section = f"""
=== YOUR RELATIONSHIPS ===
{chr(10).join(rel_lines)}"""

        # 5. Available Actions (with costs clearly shown)
        # Format other agents as a list - use just first names for clarity
        simplified_targets = [name.split()[0] for name in valid_targets] if valid_targets else []
        targets_str = ", ".join(simplified_targets) if simplified_targets else "None"
        
        actions_section = f"""
=== AVAILABLE ACTIONS ===
You must choose ONE action:

RESOURCE ACTIONS (Have Costs):
1. improve_food - Gain +8 food, costs 3 energy
2. improve_energy - Gain +8 energy, costs 3 treasury
3. improve_infrastructure - Gain +8 infrastructure, costs 4 treasury
4. boost_morale - Gain +8 morale, costs 2 food

SOCIAL ACTIONS (Free):
5. support_agent - Support another agent (improves relations, +5 morale)
    Available targets: {targets_str}
6. oppose_agent - Oppose another agent (damages relations, -3 morale)
    Available targets: {targets_str}
7. send_message - Send message to another agent (builds relationships)
    Available targets: {targets_str}

OTHER:
8. pass - Do nothing this turn (no cost, no benefit)

IMPORTANT: Check if you can afford the cost before choosing resource actions!"""

        # 6. JSON Schema with Examples
        schema_section = """
=== OUTPUT FORMAT ===
You MUST output ONLY valid JSON in this exact format:

Example 1 (Resource Action):
{
  "reasoning": "Energy is at 48 and food is declining. Cost 3 energy to gain 8 food.",
  "type": "improve_food",
  "target": "world"
}

Example 2 (Social Action):
{
  "reasoning": "Thorne has shown hostility. I should respond to maintain my position.",
  "type": "oppose_agent",
  "target": "Thorne"
}

Example 3 (Message):
{
  "reasoning": "Lyra and I share common goals. Building alliance.",
  "type": "send_message",
  "target": "Lyra",
  "message": "We should work together on infrastructure projects"
}

Example 4 (Cannot Afford):
{
  "reasoning": "Treasury is low (28), cannot afford improve_energy. Must pass or choose social action.",
  "type": "pass",
  "target": "world"
}"""

        # 7. Instructions
        instructions_section = """
=== INSTRUCTIONS ===
1. Consider your goals and the current world state
2. Check resource costs - you CANNOT choose actions you can't afford
3. Choose the BEST action from the 8 options above
4. Output ONLY the JSON, nothing else - no extra text before or after"""

        # Combine all sections
        full_prompt = f"""{persona_section}
{world_section}
{history_section}
{relationships_section}
{actions_section}
{schema_section}
{instructions_section}"""

        return full_prompt

    def decide(self, world_state: WorldState, valid_targets: List[str]) -> Action:
        """
        Decides on an action based on the current world state.
        Returns an Action object.
        """
        # Build the prompt
        prompt = self._build_prompt(world_state, valid_targets)
        
        try:
            # Generate action via LLM
            action = self.llm_client.generate_action(prompt, self.persona.name)
            return action
            
        except Exception as e:
            print(f"DEBUG: LLMAgent decide error: {e}")
            traceback.print_exc()
            return Action(
                type=ActionType.PASS,
                target="world",
                reason=f"Error generating action: {str(e)}"
            )
