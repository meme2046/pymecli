import asyncio

import typer

from crypto.bitget import (
    bitget_ff_close,
    bitget_ff_open,
    bitget_ff_pending,
    bitget_sf_close,
    bitget_sf_open,
    grid_close,
    grid_open,
    mix_tickers,
    spot_tickers,
)
from utils.mysql import get_database_engine

app = typer.Typer()


@app.command()
def sync(env_path: str = "d:/.env"):
    """同步mysql中grid数据到csv文件"""
    engine = get_database_engine(env_path)
    grid_csv_fp = "d:/github/meme2046/data/bitget_grid_0.csv"
    sf_csv_fp = "d:/github/meme2046/data/bitget_sf_0.csv"
    ff_csv_fp = "d:/github/meme2046/data/bitget_ff_0.csv"

    asyncio.run(grid_open(engine, grid_csv_fp))
    asyncio.run(grid_close(engine, grid_csv_fp))

    asyncio.run(bitget_sf_open(engine, sf_csv_fp))
    asyncio.run(bitget_sf_close(engine, sf_csv_fp))

    asyncio.run(bitget_ff_open(engine, ff_csv_fp))
    asyncio.run(bitget_ff_pending(engine, ff_csv_fp))
    asyncio.run(bitget_ff_close(engine, ff_csv_fp))


@app.command()
def spot(
    symbols: str,
    proxy: str = typer.Option(
        None, "--proxy", "-p", help="代理服务器地址，例如: http://127.0.0.1:7890"
    ),
):
    """
    从bitget获取加密货币现货价格.

    参数:
    symbols:加密货币符号,可以是多个,用逗号分隔,例如:"BTCUSDT,ETHUSDT"
    """
    spot_tickers(symbols.split(","), proxy)


@app.command()
def mix(
    symbols: str,
    proxy: str = typer.Option(
        None, "--proxy", "-p", help="代理服务器地址，例如: http://127.0.0.1:7890"
    ),
):
    """
    从bitget获取加密货币合约价格.

    参数:
    symbols:加密货币符号,可以是多个,用逗号分隔,例如:"BTCUSDT,ETHUSDT"
    """
    mix_tickers(symbols.split(","), proxy)
