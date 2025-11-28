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

    def _can_afford_action(self, action: ActionType) -> Tuple[bool, str, int, str]:
        """
        Checks if the world can afford an action's cost.
        Returns (can_afford, cost_resource, cost_amount, error_message)
        
        Action Costs:
        - improve_food: 3 energy
        - improve_energy: 3 treasury
        - improve_infrastructure: 4 treasury
        - boost_morale: 2 food
        - social actions: free
        - pass: free
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
        
        cost_resource, cost_amount = cost_map[action]
        current_amount = getattr(self.state, cost_resource)
        
        if current_amount < cost_amount:
            return False, cost_resource, cost_amount, f"Insufficient {cost_resource}: need {cost_amount}, have {current_amount}"
        
        return True, cost_resource, cost_amount, ""

    def _normalize_agent_name(self, name: str) -> str:
        """
        Normalize agent name to just first name for flexible matching.
        'Eldric the Conservative' -> 'eldric'
        'Eldric' -> 'eldric'
        """
        if not name:
            return ""
        return name.split()[0].lower()

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
        can_afford, cost_resource, cost_amount, error_msg = self._can_afford_action(action.type)
        if not can_afford:
            return False, f"Cannot afford action: {error_msg}"
                
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

        # Resource Actions (with costs)
        if action.type == ActionType.IMPROVE_FOOD:
            self.state.energy -= 3  # Cost
            self.state.food += 8    # Benefit
            message = f"{agent_name} improved food by 8 (cost: 3 energy)."

        elif action.type == ActionType.IMPROVE_ENERGY:
            self.state.treasury -= 3  # Cost
            self.state.energy += 8     # Benefit
            message = f"{agent_name} improved energy by 8 (cost: 3 treasury)."

        elif action.type == ActionType.IMPROVE_INFRASTRUCTURE:
            self.state.treasury -= 4  # Cost
            self.state.infrastructure += 8  # Benefit
            message = f"{agent_name} improved infrastructure by 8 (cost: 4 treasury)."

        elif action.type == ActionType.BOOST_MORALE:
            self.state.food -= 2  # Cost
            self.state.morale += 8  # Benefit
            message = f"{agent_name} boosted morale by 8 (cost: 2 food)."

        # Social Actions (free)
        elif action.type == ActionType.SUPPORT_AGENT:
            self.state.morale += 5
            message = f"{agent_name} supported {action.target} (+5 morale)."

        elif action.type == ActionType.OPPOSE_AGENT:
            self.state.morale -= 3
            message = f"{agent_name} opposed {action.target} (-3 morale)."

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
