from decimal import Decimal

import requests
from sqlalchemy import Engine

from utils import logger
from utils.mysql import mysql_to_csv, mysql_to_redis_and_csv


def tickers(url: str, symbols: list, proxy: str | None = None):
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
    if response.status_code == 200 and resp_json.get("code") == "00000":
        data = resp_json.get("data", [])
        results = []
        for item in data:
            if item["symbol"].lower() in symbols_list:
                price = Decimal(item["lastPr"])
                results.append(
                    f"{item['symbol'].upper().rstrip('USDT')}:{format(price, 'f')}"
                )
        logger.info(f"[{','.join(results)}]")
    else:
        logger.error(
            f"📌 请求失败,状态码:{response.status_code},错误信息:{resp_json.get('msg')}"
        )


def mix_tickers(symbols: list, proxy: str | None = None):
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    tickers(url, symbols, proxy)


def spot_tickers(symbols: list, proxy: str | None = None):
    url = "https://api.bitget.com/api/v2/spot/market/tickers"
    tickers(url, symbols, proxy)


async def bitget_sf_open(engine: Engine, csv_fp: str):
    query = "select * from bitget_sf where spot_open_usdt is not null and futures_open_usdt is not null and pnl is null and up_status = 0 and deleted_at is null;"
    key_prefix = "bitget_sf"
    table = "bitget_sf"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_fp,
        table,
        query,
        update_status=1,
        d_column_names=["spot_order_id", "futures_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
            "spot_close_at": "datetime64[ns]",
            "futures_close_at": "datetime64[ns]",
        },
    )

    logger.info(f"🚀 bitget SF open count:({row_count})")


async def bitget_ff_open(engine: Engine, csv_fp: str):
    key_prefix = "bitget_ff"
    table = "bitget_ff"
    query = f"select * from {table} where long_open_usdt is not null and short_open_usdt is not null and pnl is null and up_status = 0 and deleted_at is null;"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_fp,
        table,
        query,
        update_status=1,
        d_column_names=["long_order_id", "short_order_id"],
        pd_dtype={
            "long_order_id": str,
            "short_order_id": str,
            "long_tracking_no": str,
            "short_tracking_no": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
            "long_close_at": "datetime64[ns]",
            "short_close_at": "datetime64[ns]",
        },
    )

    logger.info(f"💰 bitget FF open count:({row_count})")


async def bitget_sf_close(engine: Engine, csv_path: str):
    query = "select * from bitget_sf where pnl is not null and up_status in (0,1);"
    key_prefix = "bitget_sf"
    table = "bitget_sf"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_path,
        table,
        query,
        update_status=2,
        d_column_names=["spot_order_id", "futures_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
            "spot_close_at": "datetime64[ns]",
            "futures_close_at": "datetime64[ns]",
        },
    )

    logger.info(f"🚀 bitget SF close count:({row_count})")


async def bitget_ff_close(engine: Engine, csv_path: str):
    key_prefix = "bitget_ff"
    table = "bitget_ff"
    query = f"select * from {table} where pnl is not null and up_status in (0,1);"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_path,
        table,
        query,
        update_status=2,
        d_column_names=["long_order_id", "short_order_id"],
        pd_dtype={
            "long_order_id": str,
            "short_order_id": str,
            "long_tracking_no": str,
            "short_tracking_no": str,
            "created_at": "datetime64[ns]",
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
            "long_close_at": "datetime64[ns]",
            "short_close_at": "datetime64[ns]",
        },
    )

    logger.info(f"💰 bitget FF close count:({row_count})")


async def grid_open(engine: Engine, csv_path: str):
    query = "select * from bitget where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    key_prefix = "bitget_grid"
    table = "bitget"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_path,
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
    )

    logger.info(f"🧮 bitget grid open count:({row_count})")


async def grid_close(engine: Engine, csv_path: str):
    query = "select * from bitget where profit is not null and up_status in (0,1) and deleted_at is null;"
    key_prefix = "bitget_grid"
    table = "bitget"

    row_count = await mysql_to_redis_and_csv(
        engine,
        key_prefix,
        csv_path,
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
    )

    logger.info(f"🧮 bitget grid close count:({row_count})")


def bitget_sf_csv_open(engine: Engine, csv_path: str):
    query = "select * from bitget_sf where spot_open_usdt is not null and futures_open_usdt is not null and pnl is null and up_status = 0 and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget_sf",
        query,
        update_status=1,
        d_column_names=["spot_client_order_id", "futures_client_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
        },
    )

    logger.info(f"🚀 bitget sf open count:({row_count})")


def bitget_sf_csv_close(engine: Engine, csv_path: str):
    query = "select * from bitget_sf where pnl is not null and up_status in (0,1);"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget_sf",
        query,
        update_status=2,
        d_column_names=["spot_client_order_id", "futures_client_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
        },
    )

    logger.info(f"🚀 bitget sf close count:({row_count})")


def grid_csv_open(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from bitget where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget",
        query,
        update_status=1,
        d_column_names=["client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
        },
    )
    logger.info(f"🧮 bitget open count:({row_count})")


def grid_csv_close(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from bitget where profit is not null and up_status in (0,1) and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget",
        query,
        update_status=2,
        d_column_names=["client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
        },
    )
    logger.info(f"🧮 bitget close count:({row_count})")
