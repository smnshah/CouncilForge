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
        # Map agent names to instances for easy lookup
        self.agent_map = {agent.persona.name: agent for agent in self.agents}
        logger.info(f"Initialized simulation with {len(self.agents)} agents.")

    def run(self):
        logger.info("Starting simulation loop...")
        
        max_turns = self.config.simulation.max_turns
        consecutive_passes = 0
        agents_count = len(self.agents)

        while self.world.state.turn < max_turns:
            current_turn = self.world.state.turn
            logger.info(f"--- Turn {current_turn + 1} ---")
            
            # 0. Distribute Messages
            # Messages sent in previous turn are now delivered
            if self.world.state.message_queue:
                logger.info(f"Distributing {len(self.world.state.message_queue)} messages...")
                for msg in self.world.state.message_queue:
                    recipient = self.agent_map.get(msg.recipient)
                    if recipient:
                        recipient.receive_message(msg)
                    else:
                        logger.warning(f"Message sent to unknown agent: {msg.recipient}")
                
                # Clear queue after delivery
                self.world.state.message_queue = []

            turn_passes = 0
            turn_events = []
            
            for agent in self.agents:
                # 1. Observe
                observation = self.world.get_view()
                
                # 2. Decide
                logger.info(f"{agent.persona.name} is thinking...")
                # Get list of other agents as valid targets
                valid_targets = [a.persona.name for a in self.agents if a.persona.name != agent.persona.name]
                action = agent.decide(observation, valid_targets)
                
                # 3. Apply
                valid_agents = [a.persona.name for a in self.agents]
                success, message = self.world.apply_action(agent.persona.name, action, valid_agents)
                turn_events.append(f"Turn {current_turn + 1}: {message}")
                
                # 4. Broadcast Action to other agents (for relationship updates)
                if success:
                    for other_agent in self.agents:
                        other_agent.process_action(action, agent.persona.name)
                
                if action.type == ActionType.PASS:
                    turn_passes += 1
            
            # Broadcast turn summary to all agents (History)
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
