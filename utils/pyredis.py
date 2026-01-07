import os

import redis.asyncio as redis


def get_redis_client(
    host=os.getenv("REDIS_HOST", "192.168.123.7"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
) -> redis.Redis:
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=decode_responses,
    )
