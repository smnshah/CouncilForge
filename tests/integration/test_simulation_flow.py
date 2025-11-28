import pytest
from unittest.mock import MagicMock, patch
from src.simulation.controller import SimulationController
from src.core.models import Action, ActionType, Persona
from src.config.settings import Config, SimulationSettings, WorldConfig

# Mock Config
@pytest.fixture
def mock_config():
    """Create a Phase 1.5 compatible mock config."""
    return Config(
        simulation=SimulationSettings(
            max_turns=3,
            model_name="test-model",
            llm_retries=1,
            log_level="DEBUG",
            history_depth=2
        ),
        world=WorldConfig(
            initial_treasury=50,  # Phase 1.5: treasury instead of resource_level
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
                archetype="Guardian",
                core_values=["V1"],
                dominant_trait="Cautious",
                secondary_trait="Protective",
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
                archetype="Visionary",
                core_values=["V2"],
                dominant_trait="Ambitious",
                secondary_trait="Impulsive",
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
    """Mock LLM client that returns Phase 1.5 compatible actions."""
    def __init__(self, model_name, retries):
        self.turn_count = 0
    
    def generate_action(self, prompt, agent_name=None):
        """Return deterministic Phase 1.5 actions."""
        self.turn_count += 1
        
        # Agent1: Improves food (which costs energy)
        if "You are Agent1" in prompt or agent_name == "Agent1":
            return Action(
                type=ActionType.IMPROVE_FOOD,
                target="world",
                reason="Agent1 improves food"
            )
        # Agent2: Supports Agent1 (social action, free)
        else:
            if self.turn_count == 2:
                # Turn 2: Send a message
                return Action(
                    type=ActionType.SEND_MESSAGE,
                    target="Agent1",
                    message="Great work on the food supply!",
                    reason="Agent2 sends encouragement"
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
    """Test full simulation flow with Phase 1.5 implementation."""
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
    
    # 3. Check world state changes (Phase 1.5 behavior)
    # Agent1 improves food every turn (3 turns):
    #   Each action: +8 food, -3 energy
    #   3 actions: +24 food, -9 energy
    # World entropy: -2 per turn for 3 turns = -6 from each resource
    # Food: 50 + 24 - 6 = 68
    # Energy: 50 - 9 - 6 = 35
    assert controller.world.state.food == 68
    assert controller.world.state.energy == 35
    
    # Agent2 supports Agent1 in Turn 1 and 3, sends message Turn 2
    # Support actions: +5 morale each
    # 2 support actions = +10 morale
    # Morale doesn't decay, so: 50 + 10 = 60
    assert controller.world.state.morale == 60
    
    # 4. Check relationships (Phase 1.5: smaller deltas)
    # Agent1 received support from Agent2
    agent1 = controller.agent_map["Agent1"]
    assert "Agent2" in agent1.relationships
    
    # Phase 1.5 relationship deltas:
    # Support: +3 trust, -2 resentment
    # Message (friendly): +3 trust, -1 resentment
    # Turn 1: Support (+3 trust, -2 resentment)
    # Turn 2: Message (+3 trust, -1 resentment)
    # Turn 3: Support (+3 trust, -2 resentment)
    # Total: +9 trust, -5 resentment
    assert agent1.relationships["Agent2"].trust == 9
    assert agent1.relationships["Agent2"].resentment == -5
    
    # 5. Treasury should have decayed
    # Initial: 50
    # No treasury used (no improve_energy or improve_infrastructure)
    # World entropy: -2 per turn * 3 turns = -6
    # Final: 50 - 6 = 44
    assert controller.world.state.treasury == 44
