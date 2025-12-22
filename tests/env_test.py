import os

from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)


def env_print():
    load_dotenv("d:/.env")
    logger.info(os.getenv("UNI_CLI_MYSQL_HOST"))


if __name__ == "__main__":
    env_print()
