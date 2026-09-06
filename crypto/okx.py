from sqlalchemy import Engine

from utils import logger
from utils.mysql import mysql_to_redis


async def grid_open(engine: Engine):
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
    )

    logger.info(f"🧮 okx grid open count:({row_count})")


async def grid_close(engine: Engine):
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
    )

    logger.info(f"🧮 okx grid close count:({row_count})")