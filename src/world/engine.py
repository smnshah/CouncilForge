from typing import Tuple, List
from loguru import logger
from src.core.models import WorldState, Action, ActionType, Message
from src.config.settings import WorldConfig
from src.social.message_parser import parse_message_tone

class World:
    def __init__(self, config: WorldConfig):
        self.state = WorldState(
            resource_level=config.initial_resource_level,
            stability=config.initial_stability,
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
        Computes derived metrics based on current state.
        crisis_level = max(0, 100 - (resource_level + food + energy + infrastructure + morale) // 5)
        overall_health = (resource_level + stability + food + energy + morale) // 5
        """
        # Clamp values to >= 0
        self.state.resource_level = max(0, self.state.resource_level)
        self.state.stability = max(0, self.state.stability)
        self.state.food = max(0, self.state.food)
        self.state.energy = max(0, self.state.energy)
        self.state.infrastructure = max(0, self.state.infrastructure)
        self.state.morale = max(0, self.state.morale)

        # Calculate metrics
        avg_resources = (
            self.state.resource_level + 
            self.state.food + 
            self.state.energy + 
            self.state.infrastructure + 
            self.state.morale
        ) // 5
        
        self.state.crisis_level = max(0, 100 - avg_resources)
        
        self.state.overall_health = (
            self.state.resource_level + 
            self.state.stability + 
            self.state.food + 
            self.state.energy + 
            self.state.morale
        ) // 5

    def is_valid_action(self, action: Action, agent_name: str, valid_agents: List[str]) -> Tuple[bool, str]:
        """
        Checks if an action is valid given the current state.
        Returns (is_valid, error_message).
        """
        # 1. Target Validation
        if action.target in [None, "", "null", "everyone", "anyone"]:
            return False, f"Invalid target '{action.target}'. Must be specific agent or 'world'."
            
        if action.type in [
            ActionType.IMPROVE_RESOURCE, ActionType.CONSUME_RESOURCE, 
            ActionType.BOOST_MORALE, ActionType.STRENGTHEN_INFRASTRUCTURE
        ]:
            if action.target != "world":
                return False, "Resource actions must target 'world'."
                
        elif action.type == ActionType.PROPOSE_POLICY:
             if action.target != "world":
                 return False, "Policy proposals must target 'world'."
                 
        elif action.type == ActionType.PASS:
            pass # No target validation needed
            
        else:
            # Social actions must target a valid agent
            if action.target not in valid_agents:
                return False, f"Target '{action.target}' is not a valid agent."
            if action.target == agent_name:
                return False, "Cannot target self."

        # 2. Policy Cooldown
        if action.type == ActionType.PROPOSE_POLICY:
            last_turn = self.state.policy_cooldowns.get(agent_name, -100)
            if self.state.turn - last_turn < 3:
                return False, "Policy proposal is on cooldown (3 turns)."
                
        # 3. Resource Validation (Optional but good)
        if action.type == ActionType.CONSUME_RESOURCE:
             # Check if we have enough resources? 
             # Spec doesn't strictly say we can't consume if 0, but "Clamp all values to >= 0" implies we can try but it stays 0.
             # However, usually you can't consume what you don't have.
             # "Invalid actions → convert to 'pass'"
             # Let's say if a specific resource is 0, we can't consume it.
             pass
        
        return True, ""

    def apply_action(self, agent_name: str, action: Action, valid_agents: List[str]) -> Tuple[bool, str]:
        """
        Applies an action to the world state.
        Returns (success, message).
        """
        is_valid, error_msg = self.is_valid_action(action, agent_name, valid_agents)
        if not is_valid:
            return False, f"Action {action.type} invalid: {error_msg}"

        message = ""
        success = True
        amount = action.amount if action.amount else 5

        if action.type == ActionType.IMPROVE_RESOURCE or action.type == ActionType.INCREASE_RESOURCE:
            target_resource = action.resource if action.resource else "resource_level"
            if target_resource == "food":
                self.state.food += amount
            elif target_resource == "energy":
                self.state.energy += amount
            elif target_resource == "infrastructure":
                self.state.infrastructure += amount
            else:
                self.state.resource_level += amount
            message = f"{agent_name} improved {target_resource} by {amount}."

        elif action.type == ActionType.CONSUME_RESOURCE or action.type == ActionType.DECREASE_RESOURCE:
            target_resource = action.resource if action.resource else "resource_level"
            if target_resource == "food":
                self.state.food -= amount
            elif target_resource == "energy":
                self.state.energy -= amount
            elif target_resource == "infrastructure":
                self.state.infrastructure -= amount
            else:
                self.state.resource_level -= amount
            message = f"{agent_name} consumed {target_resource} by {amount}."

        elif action.type == ActionType.BOOST_MORALE:
            self.state.morale += amount
            message = f"{agent_name} boosted morale by {amount}."

        elif action.type == ActionType.STRENGTHEN_INFRASTRUCTURE:
            self.state.infrastructure += amount
            message = f"{agent_name} strengthened infrastructure by {amount}."

        elif action.type == ActionType.SUPPORT_AGENT:
            self.state.stability += 5
            message = f"{agent_name} supported {action.target}."

        elif action.type == ActionType.OPPOSE_AGENT:
            self.state.stability -= 5
            message = f"{agent_name} opposed {action.target}."

        elif action.type == ActionType.NEGOTIATE:
            # Social action, mainly affects relationships (handled in agent) but might affect stability?
            # Spec says "Negotiate → trust + small".
            # World engine might just log it, or maybe small stability boost?
            # "World engine must handle each new action cleanly and with minimal side effects"
            message = f"{agent_name} negotiated with {action.target}."

        elif action.type == ActionType.REQUEST_HELP:
            message = f"{agent_name} requested help from {action.target}."

        elif action.type == ActionType.TRADE:
            # Trade might involve resource transfer?
            # Spec: "Trade → trust + medium (if successful)"
            # For now, just log.
            message = f"{agent_name} proposed trade with {action.target}."

        elif action.type == ActionType.SABOTAGE:
            self.state.stability -= 10
            message = f"{agent_name} sabotaged {action.target}!"

        # Phase 4 Actions
        elif action.type == ActionType.FORM_ALLIANCE:
            self.state.stability += 5
            message = f"{agent_name} formed an alliance with {action.target}."
            
        elif action.type == ActionType.DENOUNCE_AGENT:
            self.state.stability -= 5
            message = f"{agent_name} denounced {action.target}."
            
        elif action.type == ActionType.OFFER_CONCESSION:
            message = f"{agent_name} offered a concession to {action.target}."
            
        elif action.type == ActionType.DEMAND_CONCESSION:
            self.state.stability -= 2
            message = f"{agent_name} demanded a concession from {action.target}."
            
        elif action.type == ActionType.ACCUSE_AGENT:
            self.state.stability -= 5
            message = f"{agent_name} accused {action.target}."
            
        elif action.type == ActionType.OFFER_PROTECTION:
            self.state.stability += 5
            message = f"{agent_name} offered protection to {action.target}."
            
        elif action.type == ActionType.SPREAD_RUMOR:
            self.state.stability -= 5
            message = f"{agent_name} spread a rumor about {action.target}."
            
        elif action.type == ActionType.PROPOSE_POLICY:
            self.state.stability += 2
            self.state.policy_cooldowns[agent_name] = self.state.turn
            message = f"{agent_name} proposed a policy: {action.message if action.message else 'Unknown'}."

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
        
        # Append derived metrics to message for clarity? No, just log.
        logger.info(message)
        return success, message

    def increment_turn(self):
        self.state.turn += 1
        
        # World Entropy: Decay resources
        decay_amount = 2
        self.state.food = max(0, self.state.food - decay_amount)
        self.state.energy = max(0, self.state.energy - decay_amount)
        self.state.infrastructure = max(0, self.state.infrastructure - decay_amount)
        
        logger.info(f"World Entropy: Resources decayed by {decay_amount}.")
        
        # Recalculate metrics after decay
        self._calculate_derived_metrics()
