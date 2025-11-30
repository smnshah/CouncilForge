"""
LLM Agent - Phase 1.7.1: LLM-Code Separation

Code handles: arithmetic, trends, patterns, constraints
LLM handles: political reasoning, alliances, personality
"""

import json
from typing import List, Dict, Tuple, Optional
import traceback
from src.agents.base import BaseAgent
from src.core.models import WorldState, Action, Persona, ActionType
from src.llm.client import LLMClient
from src.social.relationship_engine import Relationship, update_relationship, apply_message_effects

# Resource action costs: (resource_name, base_cost)
RESOURCE_COSTS = {
    'improve_food': ('energy', 3),
    'improve_energy': ('treasury', 3),
    'improve_infrastructure': ('treasury', 4),
    'boost_morale': ('food', 2),
    'generate_treasury': ('energy', 4),
}

class LLMAgent(BaseAgent):
    def __init__(self, persona: Persona, llm_client: LLMClient, history_depth: int = 2):
        super().__init__(persona)
        self.llm_client = llm_client
        self.history: List[str] = []
        self.history_depth = history_depth
        
        # Simple relationship tracking (trust/resentment only)
        self.relationships: Dict[str, Relationship] = {}
        
        # Phase 1.7.1: Track resource history for trend detection (CODE does this, not LLM)
        self.resource_history: List[Dict[str, int]] = []
        
        # Phase 1.7.1: Track recent actions for pattern detection (CODE does this, not LLM)
        self.recent_actions: List[str] = []
        
        # Store received messages for the current turn
        self.messages_received: List[str] = []


    def update_resource_history(self, world_state: WorldState):
        """
        Phase 1.7.1: CODE tracks resource history, not LLM.
        Stores snapshots of world resources for trend calculation.
        """
        snapshot = {
            'treasury': world_state.treasury,
            'food': world_state.food,
            'energy': world_state.energy,
            'infrastructure': world_state.infrastructure,
            'morale': world_state.morale,
        }
        self.resource_history.append(snapshot)
        # Keep only last 4 turns for trend calculation
        if len(self.resource_history) > 4:
            self.resource_history.pop(0)

    def update_history(self, turn_summary: str):
        """Adds a turn summary to the agent's history, maintaining the limit."""
        self.history.append(turn_summary)
        if len(self.history) > self.history_depth:
            self.history.pop(0)

    def receive_message(self, message):
        """
        Receives a message and updates relationships.
        Stores message for display in the next prompt.
        """
        # Store message content for the prompt
        self.messages_received.append(f"From {message.sender}: \"{message.content}\"")
        
        if message.sender not in self.relationships:
            self.relationships[message.sender] = Relationship()
            
        # Apply simplified message effects (contact bonus)
        self.relationships[message.sender] = apply_message_effects(
            self.relationships[message.sender],
            message.content
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
    
    def _calculate_cost(self, base_cost: int, world_state: WorldState) -> int:
        """
        Phase 1.7.1: CODE calculates costs with modifiers, not LLM.
        Returns the actual cost after applying support/oppose modifiers.
        """
        modifier = world_state.cost_modifiers.get(self.persona.name, 1.0)
        return int(base_cost * modifier)
    
    def _check_affordability(self, action_name: str, world_state: WorldState) -> Tuple[bool, str]:
        """
        Phase 1.7.1: CODE checks affordability, not LLM.
        Returns (can_afford, display_string).
        """
        if action_name not in RESOURCE_COSTS:
            return (True, f"✓ {action_name} - FREE")
        
        resource_name, base_cost = RESOURCE_COSTS[action_name]
        actual_cost = self._calculate_cost(base_cost, world_state)
        current_amount = getattr(world_state, resource_name)
        
        can_afford = current_amount >= actual_cost
        
        if can_afford:
            return (True, f"✓ {action_name} - costs {actual_cost} {resource_name} (you have {current_amount})")
        else:
            return (False, f"✗ {action_name} - costs {actual_cost} {resource_name} (you only have {current_amount} ❌)")
    
    def _build_affordability_table(self, world_state: WorldState) -> str:
        """
        Phase 1.7.1: CODE builds affordability table, not LLM.
        Shows agent exactly what they can and cannot afford.
        """
        lines = []
        lines.append("=== WHAT YOU CAN AFFORD THIS TURN ===")
        lines.append("✓ support_agent - FREE")
        lines.append("✓ oppose_agent - FREE")
        lines.append("✓ send_message - FREE")
        lines.append("✓ pass - FREE")
        
        # Check each resource action
        for action_name in ['improve_food', 'improve_energy', 'improve_infrastructure', 'boost_morale', 'generate_treasury']:
            can_afford, display = self._check_affordability(action_name, world_state)
            lines.append(display)
        
        return "\n".join(lines)
    
    def _build_trend_display(self, world_state: WorldState) -> str:
        """
        Phase 1.7.1: CODE calculates trends, not LLM.
        Shows resource changes over last 3 turns with status indicators.
        """
        if len(self.resource_history) < 2:
            return ""
        
        lines = []
        lines.append("\n=== RESOURCE TRENDS (Last 3 Turns) ===")
        
        for resource in ['treasury', 'food', 'energy', 'infrastructure']:
            recent = [h[resource] for h in self.resource_history[-3:]]
            if len(recent) < 2:
                continue
                
            # Calculate trend
            deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
            
            # Determine status
            if all(d < -3 for d in deltas):
                status = "⚠️ COLLAPSING"
            elif all(d < 0 for d in deltas):
                status = "↓ declining"
            elif all(d > 3 for d in deltas):
                status = "↑ rising fast"
            elif all(d > 0 for d in deltas):
                status = "↑ rising"
            else:
                status = "~ mixed"
            
            trend_str = " → ".join(str(v) for v in recent)
            lines.append(f"{resource.upper()}: {trend_str} {status}")
        
        return "\n".join(lines)
    
    def _detect_patterns(self) -> Optional[str]:
        """
        Phase 1.7.1: CODE detects action patterns, not LLM.
        Warns agent if they're stuck in a loop.
        """
        if len(self.recent_actions) < 3:
            return None
        
        last_3 = self.recent_actions[-3:]
        if len(set(last_3)) == 1:  # All same action
            action_name = last_3[0]
            return f"Recently, you have repeatedly chosen the action: {action_name}. To stay competitive and responsive to the changing situation, YOU MUST avoid repeating these actions this turn unless absolutely necessary."
        
        return None
    
    def _get_modifier_status(self, world_state: WorldState) -> str:
        """Show if agent has cost modifier active."""
        if self.persona.name in world_state.cost_modifiers:
            modifier = world_state.cost_modifiers[self.persona.name]
            if modifier == 0.5:
                return "\n*** YOU ARE SUPPORTED: Your next resource action costs 50% less! ***"
            elif modifier == 1.5:
                return "\n*** YOU ARE OPPOSED: Your next resource action costs 50% more! ***"
        return ""

    def _build_prompt(self, world_state: WorldState, valid_targets: List[str], current_turn_targeting: List[Dict] = None) -> str:
        """
        Phase 1.7.1: LLM-Code Separation
        
        CODE provides: affordability, trends, patterns, compact data, real-time targeting
        LLM focuses on: political strategy, alliances, personality
        """
        current_turn_targeting = current_turn_targeting or []
        
        # 1. Persona Section (unchanged - LLM's domain)
        voice_section = f"\nVoice: {self.persona.voice_instructions}" if self.persona.voice_instructions else ""
        persona_section = f"""You are {self.persona.name}.
Archetype: {self.persona.archetype}
Traits: {self.persona.dominant_trait}, {self.persona.secondary_trait}{voice_section}
Goals: {', '.join(self.persona.goals)}"""

        # 1.5. MESSAGES RECEIVED (New)
        messages_section = ""
        if self.messages_received:
            messages_section = "\n\n=== MESSAGES RECEIVED ===\n" + "\n".join(self.messages_received)

        # 2. World State - COMPACT TABLE FORMAT (code provides structure)
        modifier_status = self._get_modifier_status(world_state)
        world_section = f"""
=== CURRENT RESOURCES ===
TREASURY={world_state.treasury}  FOOD={world_state.food}  ENERGY={world_state.energy}  INFRA={world_state.infrastructure}  MORALE={world_state.morale}  CRISIS={world_state.crisis_level}
{modifier_status}"""

        # 2.5. WHAT JUST HAPPENED TO YOU (Real-time targeting awareness)
        targeting_section = ""
        if current_turn_targeting:
            targeting_lines = []
            for event in current_turn_targeting:
                if event['type'] == 'support_agent':
                    targeting_lines.append(f"• {event['actor']} supported you → your next action costs 50% less")
                elif event['type'] == 'oppose_agent':
                    targeting_lines.append(f"• {event['actor']} opposed you → your next action costs 50% more")
                elif event['type'] == 'send_message':
                    targeting_lines.append(f"• {event['actor']} sent you a message")
            
            if targeting_lines:
                targeting_section = "\n\n=== WHAT JUST HAPPENED TO YOU ===\n" + "\n".join(targeting_lines)

        # 3. TRENDS - CODE CALCULATES, LLM READS
        trend_section = self._build_trend_display(world_state)

        # 4. AFFORDABILITY - CODE CALCULATES, LLM READS (no arithmetic needed!)
        affordability_section = "\n" + self._build_affordability_table(world_state)
        
        # 5. PATTERN WARNING - CODE DETECTS, LLM RESPONDS
        pattern_warning = self._detect_patterns()
        pattern_section = f"\n{pattern_warning}" if pattern_warning else ""

        # 6. Recent History
        history_text = "\\n".join(self.history[-2:]) if self.history else "No history yet."
        history_section = f"""
=== RECENT HISTORY ===
{history_text}"""

        # 7. Relationships (ultra-concise)
        relationships_section = ""
        if self.relationships:
            rel_lines = []
            for agent, rel in self.relationships.items():
                score = rel.score
                if abs(score) >= 5:  # Only show meaningful relationships
                    if score > 10:
                        rel_lines.append(f"• {agent}: ally (+{score})")
                    elif score < -10:
                        rel_lines.append(f"• {agent}: rival ({score})")
                    else:
                        rel_lines.append(f"• {agent}: neutral ({score:+d})")
            if rel_lines:
                relationships_section = "\n\n=== RELATIONSHIPS ===\n" + "\n".join(rel_lines)
        simplified_targets = [name.split()[0] for name in valid_targets] if valid_targets else []
        targets_str = ", ".join(simplified_targets) if simplified_targets else "None"
        
        actions_section = f"""
=== AVAILABLE ACTIONS ===
POLITICAL MOVES (always free):
• support_agent → Empower an ally (50% discount + builds trust)
• oppose_agent → Sabotage a rival (50% penalty + weakens them)
• send_message → Coordinate strategy, form alliances, negotiate deals
  Targets: {targets_str}

RESOURCE MOVES (check affordability table):
• improve_food, improve_energy, improve_infrastructure
• boost_morale
• generate_treasury - Convert energy to treasury (4 energy → 3 treasury)

OTHER:
• pass - Do nothing this turn"""

        # 9. JSON Schema - STRATEGIC EXAMPLES
        schema_section = """
=== OUTPUT FORMAT ===
Output ONLY valid JSON. Do not use markdown code blocks (```json).
IMPORTANT: Replace TARGET AGENT with a valid name from the 'Available Targets' list above.

Example 1 (Strategic Messaging):
{
  "type": "send_message",
  "target": "TARGET AGENT",
  "content": "Let's form an alliance to boost infrastructure.",
  "reasoning": "TARGET AGENT and I both need treasury stability. I'll message them to coordinate against our rivals."
}

Example 2 (Reciprocity):
{
  "type": "support_agent",
  "target": "TARGET AGENT",
  "reasoning": "TARGET AGENT supported me last turn. I'll reciprocate to strengthen our alliance."
}

Example 3 (Resource Action):
{
  "type": "improve_infrastructure",
  "target": "world",
  "reasoning": "Affordability table shows I can afford improve_infrastructure. This aligns with my goal."
}"""

        # 10. Instructions - FOCUS ON STRATEGY, NOT ARITHMETIC
        strategy_tip = ""
        if self.recent_actions and self.recent_actions[-1] == 'send_message':
            strategy_tip = "\nSTRATEGY TIP: You just sent a message. Consider backing up your words with a concrete action (support/oppose/resource) to show strength, unless you need to continue the conversation to secure a deal."

        instructions_section = f"""
=== DECISION PROCESS ===
1. Review your GOALS - what are you trying to achieve?
2. Check the AFFORDABILITY TABLE - what resource actions can you afford?
3. Consider RELATIONSHIPS - who are your allies and rivals?
4. Consider TRENDS - which resources are collapsing or rising?
5. Choose the action that best serves your goals. While messaging drives the simulation, actions drive the MECHANICS.
{strategy_tip}

IMPORTANT:
• Social actions are FREE and always available
• The affordability table shows EXACTLY what you can afford (no calculation needed)
• Focus on your goals and political strategy
• Output ONLY the JSON, nothing else"""

        # Combine all sections
        full_prompt = f"""{persona_section}
{messages_section}
{world_section}{targeting_section}
{trend_section}
{affordability_section}
{pattern_section}
{history_section}
{relationships_section}
{actions_section}
{schema_section}
{instructions_section}"""

        return full_prompt

    def decide(self, world_state: WorldState, valid_targets: List[str], current_turn_targeting: List[Dict] = None) -> Action:
        """
        Decides on an action based on the current world state.
        Includes awareness of what happened to this agent during the current turn.
        """
        current_turn_targeting = current_turn_targeting or []
        
        # Phase 1.7.1: Track resource history (CODE does this, not LLM)
        self.update_resource_history(world_state)
        
        # Build the prompt with real-time targeting awareness
        prompt = self._build_prompt(world_state, valid_targets, current_turn_targeting)
        
        # Clear messages after reading them
        self.messages_received = []
        
        try:
            # Generate action via LLM  
            action = self.llm_client.generate_action(prompt, self.persona.name)
            
            # Phase 1.7.1: Track action for pattern detection (CODE does this, not LLM)
            self.recent_actions.append(action.type.value)
            if len(self.recent_actions) > 5:
                self.recent_actions.pop(0)
            
            return action
            
        except Exception as e:
            print(f"DEBUG: LLMAgent decide error: {e}")
            traceback.print_exc()
            return Action(
                type=ActionType.PASS,
                target="world",
                reason=f"Error generating action: {str(e)}"
            )
