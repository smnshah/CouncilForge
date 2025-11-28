from typing import Tuple, List
from loguru import logger
from src.core.models import WorldState, Action, ActionType, Message
from src.config.settings import WorldConfig
from src.social.message_parser import parse_message_tone

class World:
    """
    World Engine - Manages world state and applies agent actions.
    
    Phase 1.5 Design:
    - 8 core actions with simple cost system
    - Treasury resource for economic actions
    - Natural resource decay each turn
    """
    
    def __init__(self, config: WorldConfig):
        """Initialize world with configuration."""
        self.state = WorldState(
            treasury=config.initial_treasury,
            food=config.initial_food,
            energy=config.initial_energy,
            infrastructure=config.initial_infrastructure,
            morale=config.initial_morale,
            turn=0
        )
        self.config = config
        self._calculate_derived_metrics()

    def get_view(self) -> WorldState:
        """
        Returns a read-only view of the world state.
        """
        return self.state.model_copy()

    def _calculate_derived_metrics(self):
        """
        Computes derived metrics and clamps resources to >= 0.
        crisis_level = max(0, 100 - average of all resources)
        """
        # Clamp all resources to >= 0
        self.state.treasury = max(0, self.state.treasury)
        self.state.food = max(0, self.state.food)
        self.state.energy = max(0, self.state.energy)
        self.state.infrastructure = max(0, self.state.infrastructure)
        self.state.morale = max(0, self.state.morale)

        # Calculate crisis level
        avg_resources = (
            self.state.treasury + 
            self.state.food + 
            self.state.energy + 
            self.state.infrastructure + 
            self.state.morale
        ) // 5
        
        self.state.crisis_level = max(0, 100 - avg_resources)

    def _can_afford_action(self, action: ActionType, agent_name: str) -> Tuple[bool, str, int, str]:
        """
        Checks if the world can afford an action's cost.
        Applies cost modifiers from support/oppose effects.
        Returns (can_afford, cost_resource, cost_amount, error_message)
        
        Action Costs (base):
        - improve_food: 3 energy
        - improve_energy: 3 treasury
        - improve_infrastructure: 4 treasury
        - boost_morale: 2 food
        
        Modifiers:
        - Supported: 0.5x cost (50% discount)
        - Opposed: 1.5x cost (50% penalty)
        """
        cost_map = {
            ActionType.IMPROVE_FOOD: ("energy", 3),
            ActionType.IMPROVE_ENERGY: ("treasury", 3),
            ActionType.IMPROVE_INFRASTRUCTURE: ("treasury", 4),
            ActionType.BOOST_MORALE: ("food", 2),
        }
        
        if action not in cost_map:
            # Social actions and pass are free
            return True, "", 0, ""
        
        cost_resource, base_cost = cost_map[action]
        
        # Apply cost modifier if agent has one
        modifier = self.state.cost_modifiers.get(agent_name, 1.0)
        actual_cost = int(base_cost * modifier)
        
        current_amount = getattr(self.state, cost_resource)
        
        if current_amount < actual_cost:
            return False, cost_resource, actual_cost, f"Insufficient {cost_resource}: need {actual_cost}, have {current_amount}"
        
        return True, cost_resource, actual_cost, ""

    def _normalize_agent_name(self, name: str) -> str:
        """
        Normalize agent name to just first name for flexible matching.
        'Eldric the Conservative' -> 'eldric'
        'Eldric' -> 'eldric'
        """
        if not name:
            return ""
        return name.split()[0].lower()

    def _get_modifier_text(self, agent_name: str) -> str:
        """Get modifier status text for logging."""
        modifier = self.state.cost_modifiers.get(agent_name, 1.0)
        if modifier == 0.5:
            return " [SUPPORTED - paid 50% less]"
        elif modifier == 1.5:
            return " [OPPOSED - paid 50% more]"
        return ""
    
    def _clear_modifier(self, agent_name: str):
        """Clear cost modifier after use (one-time effect)."""
        if agent_name in self.state.cost_modifiers:
            del self.state.cost_modifiers[agent_name]

    def is_valid_action(self, action: Action, agent_name: str, valid_agents: List[str]) -> Tuple[bool, str]:
        """
        Checks if an action is valid given the current state.
        Returns (is_valid, error_message).
        """
        # 1. Target Validation
        if action.target in [None, "", "null", "everyone", "anyone"]:
            return False, f"Invalid target '{action.target}'. Must be specific agent or 'world'."
            
        # Resource actions MUST target "world"
        if action.type in [
            ActionType.IMPROVE_FOOD, ActionType.IMPROVE_ENERGY,
            ActionType.IMPROVE_INFRASTRUCTURE, ActionType.BOOST_MORALE
        ]:
            if action.target != "world":
                return False, "Resource actions must target 'world'."
                
        # Social actions MUST target a valid agent
        elif action.type in [ActionType.SUPPORT_AGENT, ActionType.OPPOSE_AGENT]:
            # Normalize names for flexible matching (accept "Eldric" or "Eldric the Conservative")
            normalized_target = self._normalize_agent_name(action.target)
            normalized_valid = [self._normalize_agent_name(name) for name in valid_agents]
            
            if normalized_target not in normalized_valid:
                return False, f"Target '{action.target}' is not a valid agent."
            if self._normalize_agent_name(action.target) == self._normalize_agent_name(agent_name):
                return False, "Cannot target self."
                
        # Message action MUST have target and message content
        elif action.type == ActionType.SEND_MESSAGE:
            # Normalize names for flexible matching
            normalized_target = self._normalize_agent_name(action.target)
            normalized_valid = [self._normalize_agent_name(name) for name in valid_agents]
            
            if normalized_target not in normalized_valid:
                return False, f"Target '{action.target}' is not a valid agent."
            if self._normalize_agent_name(action.target) == self._normalize_agent_name(agent_name):
                return False, "Cannot send message to self."
            if not action.message:
                return False, "Message content required."
                
        # Pass is always valid
        elif action.type == ActionType.PASS:
            pass
            
        else:
            return False, f"Unknown action type: {action.type}"
        
        # 2. Cost Check
        can_afford, cost_resource, cost_amount, error_msg = self._can_afford_action(action.type, agent_name)
        if not can_afford:
            return False, f"Action validation failed: {error_msg}"
                
        return True, ""

    def apply_action(self, agent_name: str, action: Action, valid_agents: List[str]) -> Tuple[bool, str]:
        """
        Applies an action to the world state.
        Returns (success, message).
        """
        is_valid, error_msg = self.is_valid_action(action, agent_name, valid_agents)
        if not is_valid:
            logger.warning(f"{agent_name}'s action failed: {error_msg}")
            return False, f"{agent_name}'s action failed: {error_msg}"

        message = ""
        success = True

        # Resource Actions (with costs and modifiers)
        if action.type == ActionType.IMPROVE_FOOD:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, error
            
            # Deduct actual cost (with modifier applied)
            self.state.energy -= actual_cost
            self.state.food += 8
            
            # Show modifier status if applied
            modifier_text = self._get_modifier_text(agent_name)
            message = f"{agent_name} improved food by 8 (cost: {actual_cost} energy){modifier_text}."
            
            # Clear modifier after use
            self._clear_modifier(agent_name)

        elif action.type == ActionType.IMPROVE_ENERGY:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, error
            
            self.state.treasury -= actual_cost
            self.state.energy += 8
            
            modifier_text = self._get_modifier_text(agent_name)
            message = f"{agent_name} improved energy by 8 (cost: {actual_cost} treasury){modifier_text}."
            
            self._clear_modifier(agent_name)

        elif action.type == ActionType.IMPROVE_INFRASTRUCTURE:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, error
            
            self.state.treasury -= actual_cost
            self.state.infrastructure += 8
            
            modifier_text = self._get_modifier_text(agent_name)
            message = f"{agent_name} improved infrastructure by 8 (cost: {actual_cost} treasury){modifier_text}."
            
            self._clear_modifier(agent_name)

        elif action.type == ActionType.BOOST_MORALE:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, error
            
            self.state.food -= actual_cost
            self.state.morale += 8
            
            modifier_text = self._get_modifier_text(agent_name)
            message = f"{agent_name} boosted morale by 8 (cost: {actual_cost} food){modifier_text}."
            
            self._clear_modifier(agent_name)

        # Social Actions (free, but affect cost modifiers)
        elif action.type == ActionType.SUPPORT_AGENT:
            # Apply 50% cost reduction for target's next action
            normalized_target = self._normalize_agent_name(action.target)
            target_agent = next((a for a in valid_agents if self._normalize_agent_name(a) == normalized_target), None)
            
            if target_agent:
                self.state.cost_modifiers[target_agent] = 0.5
                self.state.morale += 5
                message = f"{agent_name} supported {target_agent} (+5 morale, {target_agent}'s next action costs 50% less)."

        elif action.type == ActionType.OPPOSE_AGENT:
            # Apply 50% cost increase for target's next action
            normalized_target = self._normalize_agent_name(action.target)
            target_agent = next((a for a in valid_agents if self._normalize_agent_name(a) == normalized_target), None)
            
            if target_agent:
                self.state.cost_modifiers[target_agent] = 1.5
                self.state.morale -= 3
                message = f"{agent_name} opposed {target_agent} (-3 morale, {target_agent}'s next action costs 50% more)."

        elif action.type == ActionType.SEND_MESSAGE:
            if action.message and action.target:
                msg = Message(
                    sender=agent_name,
                    recipient=action.target,
                    text=action.message,
                    tone=parse_message_tone(action.message),
                    turn_sent=self.state.turn
                )
                self.state.message_queue.append(msg)
                message = f"{agent_name} sent a message to {action.target}."
            else:
                success = False
                message = "Message content or target missing."

        elif action.type == ActionType.PASS:
            message = f"{agent_name} passed."

        else:
            success = False
            message = f"Unknown action type: {action.type}"

        # Recalculate metrics and clamp
        self._calculate_derived_metrics()
        
        logger.info(message)
        return success, message

    def increment_turn(self):
        """
        Increments the turn counter and applies world entropy (resource decay).
        """
        self.state.turn += 1
        
        # World Entropy: Decay resources by 2 each turn
        decay_amount = 2
        self.state.treasury = max(0, self.state.treasury - decay_amount)
        self.state.food = max(0, self.state.food - decay_amount)
        self.state.energy = max(0, self.state.energy - decay_amount)
        self.state.infrastructure = max(0, self.state.infrastructure - decay_amount)
        
        logger.info(f"World Entropy: Resources decayed by {decay_amount}.")
        
        # Recalculate metrics after decay
        self._calculate_derived_metrics()
