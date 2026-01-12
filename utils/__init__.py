import logging

from utils.logger import get_logger

# logger = get_logger(__name__, level=logging.DEBUG if os.getenv("DEV") else logging.INFO)

logger = get_logger(__name__, logging.INFO)
