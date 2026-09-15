import os
from urllib.parse import urlsplit, urlunsplit

import redis as redis_sync
import redis.asyncio as redis
from dotenv import load_dotenv

DEFAULT_REDIS_URL = "redis://192.168.123.7:6379/0"


def prepare_redis_url(url: str) -> str:
    """规范化 Redis URL，追加 protocol=2 兼容 Redis 7"""
    if "protocol=" in url:
        return url
    parts = urlsplit(url)
    query = parts.query + ("&" if parts.query else "") + "protocol=2"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


# 向后兼容别名
_force_resp2 = prepare_redis_url


def get_redis_client(
    url: str | None = None,
    decode_responses: bool = True,
    env_path: str = ".env",
) -> redis.Redis:
    load_dotenv(env_path)
    redis_url = url or os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    return redis.Redis.from_url(
        _force_resp2(redis_url), decode_responses=decode_responses
    )


def get_redis_client_sync(
    url: str | None = None,
    decode_responses: bool = True,
    env_path: str = ".env",
) -> redis_sync.Redis:
    load_dotenv(env_path)
    redis_url = url or os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    return redis_sync.Redis.from_url(
        _force_resp2(redis_url), decode_responses=decode_responses
    )
