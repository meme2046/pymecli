import asyncio

import typer

from crypto.gate import grid_close, grid_open
from utils.mysql import get_database_engine

app = typer.Typer()


# @app.command()
# def sync(
#     env_path: str = "d:/.env", csv_path: str = "d:/github/meme2046/data/gate_0.csv"
# ):
#     """同步mysql中grid数据到csv文件"""
#     engine = get_database_engine(env_path)
#     gate_open(engine, csv_path)
#     gate_close(engine, csv_path)


@app.command()
def rsync(env_path: str = "d:/.env"):
    """同步mysql中grid数据到csv文件"""
    engine = get_database_engine(env_path)
    grid_csv_fp = "d:/github/meme2046/data/gate_grid_0.csv"
    asyncio.run(grid_open(engine, grid_csv_fp))
    asyncio.run(grid_close(engine, grid_csv_fp))
