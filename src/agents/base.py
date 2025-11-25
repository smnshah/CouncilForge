from abc import ABC, abstractmethod
from src.core.models import WorldState, Action, Persona

class BaseAgent(ABC):
    def __init__(self, persona: Persona):
        self.persona = persona

    @abstractmethod
    def decide(self, world_state: WorldState) -> Action:
        """
        Decides on an action based on the current world state.
        """
        pass
