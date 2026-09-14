import asyncio

import typer

from crypto.okx import grid_close, grid_open
from utils.mysql import get_database_engine
from utils.pyredis import get_redis_client

app = typer.Typer()


@app.command()
def sync(
    env_path: str = typer.Argument(
        ".env",
        help="dotenv环境变量路径",
    ),
):
    """同步mysql中grid数据到redis"""
    engine = get_database_engine(env_path)
    redis = get_redis_client()
    try:

        async def _run():
            await grid_open(engine, redis)
            await grid_close(engine, redis)

        asyncio.run(_run())
    finally:
        engine.dispose()
        asyncio.run(redis.close())