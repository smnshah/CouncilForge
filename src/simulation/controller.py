from loguru import logger
from src.config.loader import load_config
from src.world.engine import World
from src.agents.llm_agent import LLMAgent
from src.llm.client import LLMClient
from src.core.models import Action, ActionType

class SimulationController:
    def __init__(self):
        self.config = load_config()
        self.world = World(self.config.world)
        self.llm_client = LLMClient(
            model_name=self.config.simulation.model_name,
            retries=self.config.simulation.llm_retries
        )
        self.agents = [
            LLMAgent(persona, self.llm_client, history_depth=self.config.simulation.history_depth) 
            for persona in self.config.personas
        ]
        logger.info(f"Initialized simulation with {len(self.agents)} agents.")

    def run(self):
        logger.info("Starting simulation loop...")
        
        max_turns = self.config.simulation.max_turns
        consecutive_passes = 0
        agents_count = len(self.agents)

        while self.world.state.turn < max_turns:
            current_turn = self.world.state.turn
            logger.info(f"--- Turn {current_turn + 1} ---")
            
            turn_passes = 0
            turn_events = []
            
            for agent in self.agents:
                # 1. Observe
                observation = self.world.get_view()
                
                # 2. Decide
                logger.info(f"{agent.persona.name} is thinking...")
                action = agent.decide(observation)
                
                # 3. Apply
                success, message = self.world.apply_action(agent.persona.name, action)
                turn_events.append(f"Turn {current_turn + 1}: {message}")
                
                if action.type == ActionType.PASS:
                    turn_passes += 1
            
            # Broadcast turn summary to all agents
            turn_summary = "\n".join(turn_events)
            for agent in self.agents:
                agent.update_history(turn_summary)
            
            # Check termination condition (all agents passed)
            if turn_passes == agents_count:
                consecutive_passes += 1
                if consecutive_passes >= 2: # Stop if everyone passes for 2 turns
                    logger.info("All agents passed for 2 consecutive turns. Stopping simulation.")
                    break
            else:
                consecutive_passes = 0

            self.world.increment_turn()

        logger.info("Simulation ended.")
        self.llm_client.close()
