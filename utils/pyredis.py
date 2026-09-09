import os

import redis as redis_sync
import redis.asyncio as redis


def get_redis_client(
    url: str = os.getenv("REDIS_URL", "redis://192.168.123.7:6379/0"),
    decode_responses: bool = True,
) -> redis.Redis:
    return redis.Redis.from_url(url, decode_responses=decode_responses)


def get_redis_client_sync(
    url: str = os.getenv("REDIS_URL", "redis://192.168.123.7:6379/0"),
    decode_responses: bool = True,
) -> redis_sync.Redis:
    return redis_sync.Redis.from_url(url, decode_responses=decode_responses)
