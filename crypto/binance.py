from decimal import Decimal

import requests
from sqlalchemy import Engine

from utils import logger
from utils.mysql import mysql_to_redis


def spot_tickers(symbols: list, proxy: str | None = None):
    url = "https://api.binance.com/api/v3/ticker/price"
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }
    response = requests.get(url, proxies=proxies)

    resp_json = response.json()
    symbols_list = [
        s.lower() + "usdt" if not s.lower().endswith("usdt") else s.lower()
        for s in symbols
    ]
    if response.status_code == 200:
        results = []
        for item in resp_json:
            if item["symbol"].lower() in symbols_list:
                price = Decimal(item["price"])
                results.append(
                    f"{item['symbol'].upper().rstrip('USDT')}:{format(price, 'f')}"
                )
        logger.info(f"[{','.join(results)}]")
    else:
        logger.error(
            f"📌 请求失败,状态码:{response.status_code},错误信息:{resp_json.get('msg')}"
        )


async def grid_open(engine: Engine, redis_client=None):
    query = "select * from binance_spot where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    key_prefix = "binance_grid"
    table = "binance_spot"

    row_count = await mysql_to_redis(
        engine,
        key_prefix,
        table,
        query,
        update_status=1,
        d_column_names=["order_id", "client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
        },
        redis_client=redis_client,
    )

    logger.info(f"🧮 binance grid open count:({row_count})")


async def grid_close(engine: Engine, redis_client=None):
    query = "select * from binance_spot where profit is not null and up_status in (0,1) and deleted_at is null;"
    key_prefix = "binance_grid"
    table = "binance_spot"

    row_count = await mysql_to_redis(
        engine,
        key_prefix,
        table,
        query,
        update_status=2,
        d_column_names=["order_id", "client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
        },
        redis_client=redis_client,
    )

    logger.info(f"🧮 binance grid close count:({row_count})")
