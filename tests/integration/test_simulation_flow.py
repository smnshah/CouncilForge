import pytest
from unittest.mock import MagicMock, patch
from src.simulation.controller import SimulationController
from src.core.models import Action, ActionType
from src.config.settings import Config, SimulationSettings, WorldConfig
from src.core.models import Persona

# Mock Config
@pytest.fixture
def mock_config():
    return Config(
        simulation=SimulationSettings(
            max_turns=3,
            model_name="test-model",
            llm_retries=1,
            log_level="DEBUG",
            history_depth=2
        ),
        world=WorldConfig(
            initial_resource_level=50,
            initial_stability=50
        ),
        personas=[
            Persona(name="Agent1", description="D1", goals=["G1"], behavior_biases=["B1"]),
            Persona(name="Agent2", description="D2", goals=["G2"], behavior_biases=["B2"])
        ]
    )

# Mock LLM Client
class MockLLMClient:
    def __init__(self, model_name, retries):
        pass
    
    def generate_action(self, prompt):
        # Return a deterministic action
        return Action(
            type=ActionType.INCREASE_RESOURCE,
            target="world",
            reason="Mocked action"
        )
    
    def close(self):
        pass

@patch('src.simulation.controller.load_config')
@patch('src.simulation.controller.LLMClient', side_effect=MockLLMClient)
def test_simulation_flow(mock_llm_class, mock_load_config, mock_config):
    # Setup mocks
    mock_load_config.return_value = mock_config
    
    # Initialize controller
    controller = SimulationController()
    
    # Run simulation
    controller.run()
    
    # Assertions
    # 1. World state should have advanced to max_turns
    assert controller.world.state.turn == 3
    
    # 2. Agents should have been initialized
    assert len(controller.agents) == 2
    
    # 3. LLM Client should have been called
    assert mock_llm_class.called
