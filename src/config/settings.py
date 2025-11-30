from typing import List
from pydantic import BaseModel
from src.core.models import Persona

class WorldConfig(BaseModel):
    initial_treasury: int = 50
    initial_food: int = 50
    initial_energy: int = 50
    initial_infrastructure: int = 50
    initial_morale: int = 50

class SimulationSettings(BaseModel):
    mode: str = "dev"
    max_turns: int = 10
    dev_model: str = "llama3.1:8b"
    prod_model: str = "llama-3.3-70b-versatile"
    llm_retries: int = 3
    log_level: str = "INFO"
    history_depth: int = 6
    
    @property
    def model_name(self) -> str:
        """Returns the appropriate model based on mode."""
        return self.prod_model if self.mode == "prod" else self.dev_model

class Config(BaseModel):
    simulation: SimulationSettings
    world: WorldConfig
    personas: List[Persona]
