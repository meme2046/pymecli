import os

from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)


def env_print():
    load_dotenv()
    logger.info(os.getenv("MYSQL_URL"))
    logger.info(os.getenv("REDIS_URL"))
    logger.info(os.getenv("AR_BASE_URL"))
    logger.info(os.getenv("TELE_API_ID"))


if __name__ == "__main__":
    env_print()
