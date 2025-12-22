from utils.logger import get_logger
from utils.toml import read_toml

logger = get_logger(__name__)


def test_read_toml():
    config = read_toml("./pyproject.toml")
    logger.info(config["project"]["description"])
    logger.info(config["project"]["version"])


if __name__ == "__main__":
    # test_read_toml()
    region = [1, 2, 3, 4]
    x, y, w, h = region
    logger.info(f"{x} {y} {w} {h}")
