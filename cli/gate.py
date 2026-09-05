import asyncio

import typer

from crypto.gate import grid_close, grid_open
from utils.mysql import get_database_engine

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
    asyncio.run(grid_open(engine))
    asyncio.run(grid_close(engine))
