import asyncio

import typer

from crypto.gate import grid_close, grid_open
from utils.mysql import get_database_engine
from utils.pyredis import get_redis_client

app = typer.Typer()

@app.command()
def rsync(
    env_path: str = typer.Argument(
        ".env",
        help="dotenv环境变量路径",
    ),
):
    """同步mysql中grid数据到redis"""
    engine = get_database_engine(env_path)
    redis = get_redis_client(env_path=env_path)
    try:

        async def _run():
            try:
                await grid_open(engine, redis)
                await grid_close(engine, redis)
            finally:
                await redis.close()

        asyncio.run(_run())
    finally:
        engine.dispose()
