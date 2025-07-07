import sys
from loguru import logger

# Configure the logger to output structured JSON logs
# This is the standard and robust way to configure loguru for cloud environments.
logger.remove()
logger.add(
    sys.stdout,
    serialize=True,  # Let loguru handle the JSON conversion
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n\n",
    backtrace=True,
    diagnose=True,
)

# Export the configured logger
log = logger
