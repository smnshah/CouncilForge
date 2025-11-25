from typing import List
from pydantic import BaseModel
from src.core.models import Persona

class WorldConfig(BaseModel):
    initial_resource_level: int = 50
    initial_stability: int = 50

class SimulationSettings(BaseModel):
    max_turns: int = 10
    model_name: str = "llama3.1:8b"
    llm_retries: int = 3
    log_level: str = "INFO"
    history_depth: int = 2

class Config(BaseModel):
    simulation: SimulationSettings
    world: WorldConfig
    personas: List[Persona]
