import asyncio
import csv
import logging
import os
import time
from typing import Any, List

import pandas as pd
import typer

from utils.logger import get_logger
from utils.path import gen_fp_with_suffix
from utils.pd import dt_to_timestamp
from utils.pyredis import get_redis_client

app = typer.Typer()

r = get_redis_client()
logger = get_logger(__name__, level=logging.INFO)


async def csv_to_redis(
    key_prefix: str = "bitget_grid",
    fp: str = "d:/github/meme2046/data/bitget_0.csv",
    id1="order_id",
    id2="client_order_id",
):
    pipe = r.pipeline()  # 启用 pipeline
    count = 0

    with open(fp, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            idx1 = row[id1]
            idx2 = row[id2]
            if not idx1 or not idx2:
                raise ValueError("无效的行")
            id = f"{idx1}_{idx2}"

            key = f"{key_prefix}:{id}"
            # HSET 自动覆盖已有字段
            pipe.hset(key, mapping=row)

            pipe.zadd(f"by_time:{key_prefix}", {id: time.time()})

            count += 1

        await pipe.execute()
        logger.info(f"写入『{count}』条")


async def csv_pd_redis(
    id1="order_id",
    id2="client_order_id",
    key_prefix: str = "bitget_sf",
    fp: str = "d:/github/meme2046/data/bitget_sf_0.csv",
):
    if os.path.exists(fp):
        df: pd.DataFrame = pd.read_csv(
            fp,
            encoding="utf-8",
            dtype={
                "order_id": str,
                "fx_order_id": str,
                "spot_order_id": str,
                "futures_order_id": str,
                "spot_tracking_no": str,
                "futures_tracking_no": str,
                "open_at": str,
                "close_at": str,
                "spot_close_at": str,
                "futures_close_at": str,
            },
        )

        # 如果open_at 为空，则设置为 created_at
        # df["open_at"] = df["open_at"].fillna(df["created_at"])
        del_column_names = ["created_at", "updated_at", "deleted_at"]
        # 只删除存在的列
        columns_to_drop = [col for col in del_column_names if col in df.columns]
        df = df.drop(columns=columns_to_drop)

        # datetime_cols = ["open_at", "close_at", "spot_close_at", "futures_close_at"]
        # for col in datetime_cols:
        #     if col in df.columns:
        #         # 处理不同的日期时间格式，使用 format='mixed' 让 pandas 自动推断格式
        #         df[col] = pd.to_datetime(df[col], format="mixed")
        #         df[col] = dt_to_timestamp(df[col])

        pipe = r.pipeline()  # 启用 pipeline
        count = 0

        for _, row in df.iterrows():
            idx1 = row[id1]
            idx2 = row[id2]
            if not idx1 or not idx2:
                raise ValueError("ERR:id行无效")
            id = f"{idx1}_{idx2}"
            key = f"{key_prefix}:{id}"

            # 转换行数据为字典（处理 NaN 为 None 或空字符串）
            row_dict = row.where(pd.notna(row), "").to_dict()

            # 1. 写入完整数据到 Hash（自动覆盖）
            pipe.hset(key, mapping=row_dict)
            # 2. 写入 ZSet 索引：score = Unix 时间戳
            pipe.zadd(f"by_time:{key_prefix}", {id: time.time()})
            count += 1

        await pipe.execute()
        logger.info(f"🧱 to redis:『{count}』")


async def get_latest_n(key_prefix="bitget_grid", n=5000) -> List[Any]:
    ids = await r.zrevrange(f"by_time:{key_prefix}", 0, n - 1)
    if not ids:
        return []
    pipe = r.pipeline()
    for id in ids:
        pipe.hgetall(f"{key_prefix}:{id}")
    return await pipe.execute()


async def count_async(key_prefix="bitget_sf"):
    ids = await r.zrevrange(f"by_time:{key_prefix}", 0, -1)
    logger.info(f"记录数:『{len(ids)}』")
    # ⌞⌝ 『』


@app.command()
def count(
    key_prefix: str = typer.Argument(
        "bitget_sf",
        help="redis zset key前缀",
    ),
):
    """
    查询by_time:{key_prefix} redis zset中的记录数

    :param key_prefix: 传入会自动组合为 by_time:{key_prefix}
    :type key_prefix: str

    """
    async def _cmd():
        try:
            await count_async(key_prefix)
        finally:
            await r.close()

    asyncio.run(_cmd())


@app.command()
def csv2redis(
    id1: str,
    id2: str,
    kp: str = typer.Option(
        "bitget_sf",
        "--key-prefix",
        "-kp",
        help="存入redis的key前缀",
    ),
    fp: str = typer.Option(
        "d:/github/meme2046/data/bitget_sf_0.csv",
        "--file-path",
        "-fp",
        help="csv文件路径",
    ),
):
    """
    csv -> redis

    :param id1: id1的列名,会按照当前记录的id1、id2生成redis.key
    :type id1: str
    :param id2: id2的列名,会按照当前记录的id1、id2生成redis.key
    :type id2: str
    :param kp: 说明
    :type kp: 写入redis的key_prefix
    :param fp: 说明
    :type fp: csv文件路径
    """
    async def _cmd():
        try:
            await csv_pd_redis(
                id1,
                id2,
                kp,
                fp,
            )
        finally:
            await r.close()

    asyncio.run(_cmd())


@app.command()
def convert(
    fp: str = typer.Argument(
        "d:/github/meme2046/data/deprecated/bitget_sf_0.csv",
        help="csv文件路径",
    ),
):
    """
    csv -> csv
    主要是将时间字符串转为时间戳,删除一些列

    :param fp: csv文件路径
    :type fp: str
    """
    if not os.path.exists(fp):
        logger.error(f"文件不存在:『{fp}』")
        return

    df: pd.DataFrame = pd.read_csv(
        fp,
        encoding="utf-8",
        dtype={
            "order_id": str,
            "fx_order_id": str,
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
        },
    )

    df["open_at"] = df["open_at"].fillna(df["created_at"])
    del_column_names = ["created_at", "updated_at", "deleted_at"]
    columns_to_drop = [col for col in del_column_names if col in df.columns]
    df = df.drop(columns=columns_to_drop)

    datetime_cols = [
        "created_at",
        "open_at",
        "close_at",
        "spot_close_at",
        "futures_close_at",
    ]
    for col in datetime_cols:
        if col in df.columns:
            # 处理不同的日期时间格式，使用 format='mixed' 让 pandas 自动推断格式
            df[col] = pd.to_datetime(df[col], format="mixed")
            df[col] = dt_to_timestamp(df[col])

    out_fp = gen_fp_with_suffix(fp, "tmp")

    df.to_csv(
        out_fp,
        mode="a",
        header=not os.path.exists(out_fp),
        index=False,
        encoding="utf-8",
    )
