import pytest
import yaml
from src.config.loader import load_config
from src.config.settings import Config

def test_load_config_valid(tmp_path):
    """Test config loading with Phase 1.5 settings."""
    # Create temp config files
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    settings_data = {
        "simulation": {
            "max_turns": 5,
            "model_name": "test-model",
            "llm_retries": 1,
            "log_level": "DEBUG",
            "history_depth": 2
        },
        "world": {
            "initial_treasury": 100,  # Phase 1.5: treasury instead of resource_level
            "initial_food": 100,
            "initial_energy": 100,
            "initial_infrastructure": 100,
            "initial_morale": 100
        }
    }
    
    personas_data = {
        "personas": [
            {
                "name": "Test Agent",
                "description": "Desc",
                "goals": ["Goal"],
                "behavior_biases": ["Bias"]
            }
        ]
    }
    
    with open(config_dir / "settings.yaml", "w") as f:
        yaml.dump(settings_data, f)
        
    with open(config_dir / "personas.yaml", "w") as f:
        yaml.dump(personas_data, f)
        
    # Test loading
    config = load_config(str(config_dir))
    
    assert isinstance(config, Config)
    assert config.simulation.max_turns == 5
    assert config.world.initial_treasury == 100  # Phase 1.5
    assert config.world.initial_food == 100
    assert len(config.personas) == 1
    assert config.personas[0].name == "Test Agent"

def test_load_config_missing_file(tmp_path):
    """Test error handling for missing config files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Missing settings.yaml
    with pytest.raises(FileNotFoundError):
        load_config(str(config_dir))
