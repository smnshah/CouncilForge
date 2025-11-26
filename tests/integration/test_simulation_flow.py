import pytest
from unittest.mock import MagicMock, patch
from src.simulation.controller import SimulationController
from src.core.models import Action, ActionType, Persona
from src.config.settings import Config, SimulationSettings, WorldConfig

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
            initial_stability=50,
            initial_food=50,
            initial_energy=50,
            initial_infrastructure=50,
            initial_morale=50
        ),
        personas=[
            Persona(
                name="Agent1", 
                description="D1", 
                goals=["G1"], 
                behavior_biases=["B1"],
                archetype="A1",
                core_values=["V1"],
                dominant_trait="T1",
                secondary_trait="T2",
                decision_biases=["DB1"],
                preferred_resources=["food"],
                conflict_style="diplomatic",
                cooperation_style="helpful",
                risk_preference="low"
            ),
            Persona(
                name="Agent2", 
                description="D2", 
                goals=["G2"], 
                behavior_biases=["B2"],
                archetype="A2",
                core_values=["V2"],
                dominant_trait="T3",
                secondary_trait="T4",
                decision_biases=["DB2"],
                preferred_resources=["energy"],
                conflict_style="aggressive",
                cooperation_style="selfish",
                risk_preference="high"
            )
        ]
    )

# Mock LLM Client
class MockLLMClient:
    def __init__(self, model_name, retries):
        self.turn_count = 0
    
    def generate_action(self, prompt):
        self.turn_count += 1
        # Return deterministic actions based on prompt content or just cycling
        if "You are Agent1" in prompt:
            return Action(
                type=ActionType.IMPROVE_RESOURCE,
                target="world",
                resource="food",
                amount=5,
                reason="Agent1 improves food"
            )
        else:
            return Action(
                type=ActionType.SUPPORT_AGENT,
                target="Agent1",
                reason="Agent2 supports Agent1"
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
    
    # 3. Check world state changes
    # Agent1 improves food every turn (3 turns) -> +15 food
    # Initial 50 -> 65
    assert controller.world.state.food == 65
    
    # Agent2 supports Agent1 every turn -> +15 stability
    # Initial 50 -> 65
    assert controller.world.state.stability == 65
    
    # 4. Check relationships
    # Agent1 received support from Agent2
    agent1 = controller.agent_map["Agent1"]
    assert "Agent2" in agent1.relationships
    # 3 turns of support * 10 trust = 30 trust
    assert agent1.relationships["Agent2"]["trust"] == 30
