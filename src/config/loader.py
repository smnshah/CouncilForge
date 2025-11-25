import yaml
from pathlib import Path
from src.config.settings import Config, SimulationSettings, WorldConfig
from src.core.models import Persona

def load_config(config_dir: str = "config") -> Config:
    """
    Loads configuration from YAML files in the specified directory.
    Expects settings.yaml and personas.yaml.
    """
    config_path = Path(config_dir)
    
    # Load settings
    with open(config_path / "settings.yaml", "r") as f:
        settings_data = yaml.safe_load(f)
        
    simulation_config = SimulationSettings(**settings_data.get("simulation", {}))
    world_config = WorldConfig(**settings_data.get("world", {}))
    
    # Load personas
    with open(config_path / "personas.yaml", "r") as f:
        personas_data = yaml.safe_load(f)
        
    personas = [Persona(**p) for p in personas_data.get("personas", [])]
    
    return Config(
        simulation=simulation_config,
        world=world_config,
        personas=personas
    )
