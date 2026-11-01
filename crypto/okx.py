from decimal import Decimal

import requests
from sqlalchemy import Engine

from utils import logger
from utils.mysql import mysql_to_redis


def spot_tickers(symbols: list, proxy: str | None = None):
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }
    response = requests.get(url, proxies=proxies)

    resp_json = response.json()
    inst_ids = []
    for s in symbols:
        s = s.lower().replace("-", "")
        if not s.endswith("usdt"):
            s += "usdt"
        inst_ids.append(s[:-4] + "-usdt")
    if response.status_code == 200 and resp_json.get("code") == "0":
        results = []
        for item in resp_json.get("data", []):
            if item["instId"].lower() in inst_ids:
                price = Decimal(item["last"])
                results.append(
                    f"{item['instId'].upper().replace('-USDT', '')}:{format(price, 'f')}"
                )
        logger.info(f"[{','.join(results)}]")
    else:
        logger.error(
            f"📌 请求失败,状态码:{response.status_code},错误信息:{resp_json.get('msg')}"
        )


async def grid_open(engine: Engine, redis_client=None):
    query = "select * from okx_spot where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    key_prefix = "okx_grid"
    table = "okx_spot"

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

    logger.info(f"🧮 okx grid open count:({row_count})")


async def grid_close(engine: Engine, redis_client=None):
    query = "select * from okx_spot where profit is not null and up_status in (0,1) and deleted_at is null;"
    key_prefix = "okx_grid"
    table = "okx_spot"

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

    logger.info(f"🧮 okx grid close count:({row_count})")