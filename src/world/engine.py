from typing import Tuple
from loguru import logger
from src.core.models import WorldState, Action, ActionType
from src.config.settings import WorldConfig

class World:
    def __init__(self, config: WorldConfig):
        self.state = WorldState(
            resource_level=config.initial_resource_level,
            stability=config.initial_stability,
            turn=0
        )
        self.config = config

    def get_view(self) -> WorldState:
        """
        Returns a read-only view of the world state.
        For Phase 1, this is just a copy of the full state.
        """
        return self.state.model_copy()

    def is_valid_action(self, action: Action) -> bool:
        """
        Checks if an action is valid given the current state.
        """
        if action.type == ActionType.DECREASE_RESOURCE and self.state.resource_level <= 0:
            return False
        # Add more validation logic here if needed
        return True

    def apply_action(self, agent_name: str, action: Action) -> Tuple[bool, str]:
        """
        Applies an action to the world state.
        Returns (success, message).
        """
        if not self.is_valid_action(action):
            return False, f"Action {action.type} invalid in current state."

        message = ""
        success = True

        if action.type == ActionType.INCREASE_RESOURCE:
            self.state.resource_level += 10
            message = f"{agent_name} increased resources. Level: {self.state.resource_level}"
        
        elif action.type == ActionType.DECREASE_RESOURCE:
            self.state.resource_level = max(0, self.state.resource_level - 10)
            message = f"{agent_name} decreased resources. Level: {self.state.resource_level}"
        
        elif action.type == ActionType.SUPPORT_AGENT:
            self.state.stability += 5
            message = f"{agent_name} supported {action.target}. Stability: {self.state.stability}"
        
        elif action.type == ActionType.OPPOSE_AGENT:
            self.state.stability = max(0, self.state.stability - 5)
            message = f"{agent_name} opposed {action.target}. Stability: {self.state.stability}"
        
        elif action.type == ActionType.PASS:
            message = f"{agent_name} passed."
        
        else:
            success = False
            message = f"Unknown action type: {action.type}"

        logger.info(message)
        return success, message

    def increment_turn(self):
        self.state.turn += 1
