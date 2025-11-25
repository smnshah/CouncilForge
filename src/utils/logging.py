import sys
from loguru import logger

def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configures loguru logger.
    """
    logger.remove()  # Remove default handler
    
    # Ensure log directory exists
    import os
    os.makedirs(log_dir, exist_ok=True)
    
    # Console handler (Narrative/Info)
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
        filter=lambda record: record["level"].name == "INFO" or record["level"].name == "WARNING" or record["level"].name == "ERROR"
    )

    # File handler (Debug/Trace) - New file per run, keep for 7 days
    log_file = f"{log_dir}/simulation_{{time:YYYY-MM-DD_HH-mm-ss}}.log"
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB", # Rotate if single file gets too big (unlikely for single run but good practice)
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )

    logger.info("Logging initialized.")
