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
            initial_treasury=25,  # Phase 1.7: Scarcity pressure
            initial_food=35,
            initial_energy=35,
            initial_infrastructure=40,
            initial_morale=45
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
    def __init__(self, *args, **kwargs):
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
    
    # 3. Check world state changes (Phase 1.7 behavior)
    # Agent1 improves food every turn (3 turns):
    #   Each action: +8 food, -3 energy (or less if supported)
    # Agent2 supports Agent1 in Turn 2-3, sends message Turn 1
    # World entropy: -2 per turn for 3 turns = -6 from each resource
    
    # Food calculation (Phase 1.7 starts at 35):
    # Initial: 35
    # Turn 1: +8 food, -2 entropy = 41
    # Turn 2: +8 food, -2 entropy = 47  
    # Turn 3: +8 food (supported), -2 entropy = 53
    # Expected: 53
    assert controller.world.state.food >= 53
    
    # Energy calculation (Phase 1.7 starts at 35):
    # Initial: 35
    # Turn 1: -3 energy cost, -2 entropy = 30
    # Turn 2: -3 energy cost, -2 entropy = 25
    # Turn 3: -1 energy cost (supported 50% less), -2 entropy = 22
    # Expected: 22
    assert controller.world.state.energy >= 22
    
    # 4. Check social interactions
    # Agent2 supported Agent1 in turns 2 and 3
    # Each support adds +5 morale
    # Phase 1.7 initial morale: 45
    # Turn 1: -2 entropy = 43, no morale change (message sent)
    # Turn 2: +5 support, -2 entropy = 46
    # Turn 3: +5 support, -2 entropy = 49
    # But morale doesn't decay, so: 45 + 5 + 5 = 55
    assert controller.world.state.morale >= 55
    
    # 5. Relationship tracking
    # Agent1 received message from Agent2 (Turn 1) and was supported twice (Turn 2, 3)
    assert "Agent2" in controller.agents[0].relationships
    # Support actions build trust
    assert controller.agents[0].relationships["Agent2"].trust >= 9
    assert controller.agents[0].relationships["Agent2"].resentment <= -5 or controller.agents[0].relationships["Agent2"].resentment == 0

    # Treasury calculation (Phase 1.7 starts at 25):
    # Initial: 25
    # No treasury used (no improve_energy or improve_infrastructure)
    # World entropy: -2 per turn * 3 turns = -6
    # Final: 25 - 6 = 19
    assert controller.world.state.treasury == 19
