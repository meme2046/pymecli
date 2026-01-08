from sqlalchemy import Engine

from utils.mysql import mysql_to_csv, mysql_to_redis


def gate_open(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from gate where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "gate",
        query,
        update_status=1,
        d_column_names=["client_order_id"],
        pd_dtype={"order_id": str, "fx_order_id": str},
    )
    print(f"🧮 gate open count:({row_count})")


async def gate_redis_open(engine: Engine):
    query = "select * from gate where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    key_prefix = "gate_grid"
    table = "gate"

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
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
        },
    )

    print(f"🧮 gate open count:({row_count})")


async def gate_redis_close(engine: Engine):
    query = "select * from gate where profit is not null and up_status in (0,1) and deleted_at is null;"
    key_prefix = "gate_grid"
    table = "gate"

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
            "open_at": "datetime64[ns]",
            "close_at": "datetime64[ns]",
        },
    )
    print(f"🧮 gate close count:({row_count})")


def gate_close(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from gate where profit is not null and up_status in (0,1) and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "gate",
        query,
        update_status=2,
        d_column_names=["client_order_id"],
        pd_dtype={"order_id": str, "fx_order_id": str},
    )
    print(f"🧮 gate close count:({row_count})")


if __name__ == "__main__":
    pass
