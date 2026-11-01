import asyncio

import typer

from crypto.binance import grid_close, grid_open, spot_tickers
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


@app.command()
def spot(
    symbols: str,
    proxy: str = typer.Option(
        None, "--proxy", "-p", help="代理服务器地址，例如: http://127.0.0.1:7890"
    ),
):
    """
    从binance获取加密货币现货价格.

    参数:
    symbols:加密货币符号,可以是多个,用逗号分隔,例如:"BTCUSDT,ETHUSDT"
    """
    spot_tickers(symbols.split(","), proxy)
