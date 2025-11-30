from typing import Tuple, List
from loguru import logger
from src.core.models import WorldState, Action, ActionType, Message, TurnEvent
from src.config.settings import WorldConfig
from src.config.settings import WorldConfig

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
            ActionType.GENERATE_TREASURY: ("energy", 4),  # NEW: Sell energy for treasury
        }
        
        if action not in cost_map:
            # Social actions and pass are free
            return True, "", 0, ""
        
        cost_resource, base_cost = cost_map[action]
        
        # Phase 1.8: Output Modifiers means COST IS FIXED
        actual_cost = base_cost
        
        current_amount = getattr(self.state, cost_resource)
        
        # Check affordability
        can_afford = current_amount >= actual_cost
        
        if not can_afford:
            return False, cost_resource, actual_cost, f"Cannot afford {action.value} (needs {actual_cost} {cost_resource}, you have {current_amount})"
                
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
            
        # Resource actions MUST target "world" (except boost_morale which can target 'population')
        if action.type in [
            ActionType.IMPROVE_FOOD, ActionType.IMPROVE_ENERGY,
            ActionType.IMPROVE_INFRASTRUCTURE,
            ActionType.GENERATE_TREASURY
        ]:
            if action.target != "world":
                return False, "Resource actions must target 'world'."
        
        elif action.type == ActionType.BOOST_MORALE:
            if action.target not in ["world", "population"]:
                return False, "boost_morale must target 'world' or 'population'."
                
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

    def apply_action(self, agent_name: str, action: Action, valid_agents: List[str]) -> Tuple[bool, TurnEvent]:
        """
        Applies an action to the world state.
        Returns (success, message).
        """
        is_valid, error_msg = self.is_valid_action(action, agent_name, valid_agents)
        if not is_valid:
            logger.warning(f"{agent_name}'s action failed: {error_msg}")
            return False, TurnEvent(message=f"{agent_name}'s action failed: {error_msg}", visibility="public", actor=agent_name)

        message = ""
        success = True

        # Resource Actions (Cost is now FIXED, Output is MODIFIED)
        if action.type == ActionType.IMPROVE_FOOD:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, TurnEvent(message=error, visibility="public", actor=agent_name)
            
            # Deduct fixed cost
            self.state.energy -= actual_cost
            
            # Calculate Output with Modifier
            modifier = self.state.cost_modifiers.pop(agent_name, 1.0) # Consume modifier
            base_output = 8
            actual_output = int(base_output * modifier)
            
            self.state.food += actual_output
            
            status_msg = ""
            if modifier > 1.0: status_msg = " [SUPPORTED - +50% output]"
            elif modifier < 1.0: status_msg = " [OPPOSED - -50% output]"
            
            message = f"{agent_name} improved food by {actual_output} (cost: {actual_cost} energy){status_msg}."

        elif action.type == ActionType.IMPROVE_ENERGY:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, TurnEvent(message=error, visibility="public", actor=agent_name)
            
            self.state.treasury -= actual_cost
            
            # Calculate Output with Modifier
            modifier = self.state.cost_modifiers.pop(agent_name, 1.0)
            base_output = 8
            actual_output = int(base_output * modifier)
            
            self.state.energy += actual_output
            
            status_msg = ""
            if modifier > 1.0: status_msg = " [SUPPORTED - +50% output]"
            elif modifier < 1.0: status_msg = " [OPPOSED - -50% output]"
            
            message = f"{agent_name} improved energy by {actual_output} (cost: {actual_cost} treasury){status_msg}."

        elif action.type == ActionType.IMPROVE_INFRASTRUCTURE:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, TurnEvent(message=error, visibility="public", actor=agent_name)
            
            self.state.treasury -= actual_cost
            
            # Calculate Output with Modifier
            modifier = self.state.cost_modifiers.pop(agent_name, 1.0)
            base_output = 8
            actual_output = int(base_output * modifier)
            
            self.state.infrastructure += actual_output
            
            status_msg = ""
            if modifier > 1.0: status_msg = " [SUPPORTED - +50% output]"
            elif modifier < 1.0: status_msg = " [OPPOSED - -50% output]"
            
            message = f"{agent_name} improved infrastructure by {actual_output} (cost: {actual_cost} treasury){status_msg}."

        elif action.type == ActionType.BOOST_MORALE:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, TurnEvent(message=error, visibility="public", actor=agent_name)
            
            self.state.food -= actual_cost
            
            # Calculate Output with Modifier
            modifier = self.state.cost_modifiers.pop(agent_name, 1.0)
            base_output = 8
            actual_output = int(base_output * modifier)
            
            self.state.morale += actual_output
            
            status_msg = ""
            if modifier > 1.0: status_msg = " [SUPPORTED - +50% output]"
            elif modifier < 1.0: status_msg = " [OPPOSED - -50% output]"
            
            message = f"{agent_name} boosted morale by {actual_output} (cost: {actual_cost} food){status_msg}."

        elif action.type == ActionType.GENERATE_TREASURY:
            can_afford, cost_resource, actual_cost, error = self._can_afford_action(action.type, agent_name)
            if not can_afford:
                return False, TurnEvent(message=error, visibility="public", actor=agent_name)
            
            # Convert energy to treasury at rate: 4 energy → 3 treasury (Base)
            self.state.energy -= actual_cost
            
            # Calculate Output with Modifier
            modifier = self.state.cost_modifiers.pop(agent_name, 1.0)
            base_output = 3
            actual_output = int(base_output * modifier)
            
            self.state.treasury += actual_output
            
            status_msg = ""
            if modifier > 1.0: status_msg = " [SUPPORTED - +50% output]"
            elif modifier < 1.0: status_msg = " [OPPOSED - -50% output]"
            
            message = f"{agent_name} generated {actual_output} treasury by selling energy (cost: {actual_cost} energy){status_msg}."
            
        # Social Actions (free, but affect cost modifiers)
        elif action.type == ActionType.SUPPORT_AGENT:
            # Apply 50% cost reduction for target's next action
            normalized_target = self._normalize_agent_name(action.target)
            target_agent = next((a for a in valid_agents if self._normalize_agent_name(a) == normalized_target), None)
            
            if target_agent:
                self.state.cost_modifiers[target_agent] = 1.5
                self.state.morale += 5
                message = f"{agent_name} supported {target_agent} (+5 morale, {target_agent}'s next action is 50% MORE effective)."

        elif action.type == ActionType.OPPOSE_AGENT:
            normalized_target = self._normalize_agent_name(action.target)
            target_agent = next((a for a in valid_agents if self._normalize_agent_name(a) == normalized_target), None)
            
            if target_agent:
                self.state.cost_modifiers[target_agent] = 0.5
                self.state.morale -= 3
                message = f"{agent_name} opposed {target_agent} (-3 morale, {target_agent}'s next action is 50% LESS effective)."

        elif action.type == ActionType.SEND_MESSAGE:
            if action.message and action.target:
                msg = Message(
                    sender=agent_name,
                    recipient=action.target,
                    content=action.message,
                    turn_sent=self.state.turn
                )
                self.state.message_queue.append(msg)
                message = f"{agent_name} sent a message to {action.target}: \"{action.message}\""
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
        
        # Construct TurnEvent
        visibility = "private" if action.type == ActionType.SEND_MESSAGE else "public"
        target_agent = action.target if visibility == "private" else None
        
        event = TurnEvent(
            message=message,
            visibility=visibility,
            actor=agent_name,
            target=target_agent
        )
        
        return success, event

    def check_terminal_state(self) -> Tuple[bool, str]:
        """
        Checks if the world has reached a terminal (game-over) state.
        Returns (is_terminal, reason).
        
        Terminal conditions:
        - Food = 0 (starvation)
        - Energy = 0 (collapse)
        - Treasury = 0 AND infrastructure < 20 (economic failure)
        """
        if self.state.food <= 0:
            return True, "GAME OVER: Food supply exhausted - population starved"
        
        if self.state.energy <= 0:
            return True, "GAME OVER: Energy depleted - system collapse"
        
        if self.state.treasury <= 0 and self.state.infrastructure < 20:
            return True, "GAME OVER: Economic collapse - no treasury and failing infrastructure"
        
        # Critical morale = societal breakdown
        if self.state.morale <= 5:
            return True, "GAME OVER: Morale critical - society has collapsed"
        
        return False, ""

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
