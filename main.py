import sys
from loguru import logger
from src.utils.logging import setup_logging
from src.simulation.controller import SimulationController

def main():
    setup_logging()
    
    try:
        controller = SimulationController()
        controller.run()
    except Exception as e:
        logger.exception(f"Simulation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
