import asyncio

import typer

from crypto.gate import gate_close, gate_open, gate_redis_close, gate_redis_open
from utils.mysql import get_database_engine

app = typer.Typer()


@app.command()
def sync(
    env_path: str = "d:/.env", csv_path: str = "d:/github/meme2046/data/gate_0.csv"
):
    """同步mysql中grid数据到csv文件"""
    engine = get_database_engine(env_path)
    gate_open(engine, csv_path)
    gate_close(engine, csv_path)


@app.command()
def rsync(env_path: str = "d:/.env"):
    """同步mysql中grid数据到csv文件"""
    engine = get_database_engine(env_path)
    asyncio.run(gate_redis_open(engine))
    asyncio.run(gate_redis_close(engine))
