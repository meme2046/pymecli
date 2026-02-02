import os
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

from utils import logger
from utils.pd import deduplicated, dt_to_timestamp
from utils.pyredis import get_redis_client


def get_database_engine(env_path: str) -> Engine:
    """创建数据库引擎"""
    load_dotenv(env_path)
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    database = os.getenv("MYSQL_DATABASE")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")

    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
        connect_args={
            # 对于MySQL，可以在连接参数中指定时区
            # "init_command": "SET time_zone='+00:00'",  # UTC时间
            # 或者使用本地时区，例如：
            # "init_command": "SET time_zone='+08:00'",  # 中国标准时间
        },
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

    return engine


def mysql_to_csv(
    engine: Engine,
    csv_path: str,
    table: str,
    query: str,
    update_status: int,
    d_column_names: list[str],
    pd_dtype: dict | None = None,
    del_column_names: list[str] = ["id"],
) -> int:
    # 查询数据
    data_frame = pd.read_sql(query, engine, dtype=pd_dtype)
    # 提取 'id' 列
    ids = data_frame["id"].tolist()
    # 删除不需要的列
    data_frame = data_frame.drop(columns=del_column_names)

    # 根据 'open_at' 列降序排序
    # data_frame = data_frame.sort_values(by="open_at", ascending=False)

    # 将数据追加写入 CSV 文件
    data_frame.to_csv(
        csv_path,
        mode="a",
        header=not os.path.exists(csv_path),
        index=False,
        encoding="utf-8",
    )
    # csv去重,保留最后加入的数据
    deduplicated(csv_path, d_column_names, "last", pd_dtype)

    # 根据提取的 'id' 列更新数据库中 up_status 字段
    if ids:
        # 使用 text() 构建查询时，确保 :ids 是一个列表
        update_query = text(
            f"UPDATE {table} SET up_status = :status WHERE id IN ({','.join(map(str, ids))});"
        )
        with engine.connect() as connection:
            with connection.begin():
                result = connection.execute(
                    update_query,
                    {"status": update_status},
                )

                return result.rowcount

    return 0


async def mysql_to_redis_and_csv(
    engine: Engine,
    key_prefix: str,
    csv_fp: str,
    table: str,
    query: str,
    update_status: int,
    d_column_names: list[str],
    pd_dtype: dict | None = None,
    del_column_names: list[str] = ["id", "created_at", "updated_at", "deleted_at"],
) -> int:
    # 查询数据
    df = pd.read_sql(query, engine, dtype=pd_dtype)
    df["open_at"] = df["open_at"].fillna(df["created_at"])
    # 提取 'id' 列
    ids = df["id"].tolist()
    # 删除不需要的列
    columns_to_drop = [col for col in del_column_names if col in df.columns]
    df = df.drop(columns=columns_to_drop)

    datetime_cols = [
        "open_at",
        "close_at",
        "spot_close_at",
        "futures_close_at",
        "long_close_at",
        "short_close_at",
    ]

    logger.debug(df.head())
    logger.debug(df.dtypes)

    for col in datetime_cols:
        if col in df.columns:
            df[col] = dt_to_timestamp(df[col])
            # df[col] = dt_to_timestamp(pd.to_datetime(df[col], errors="coerce"))

    # 数据写入redis
    r = get_redis_client()
    pipe = r.pipeline()  # 启用 pipeline
    count = 0
    n1, n2 = d_column_names

    for _, row in df.iterrows():
        idx1 = row[n1]
        idx2 = row[n2]
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
    logger.debug(f"🧱 to redis: {count}")

    df.to_csv(
        csv_fp,
        mode="a",
        header=not os.path.exists(csv_fp),
        index=False,
        encoding="utf-8",
    )

    deduplicated(
        csv_fp,
        d_column_names,
        "last",
        pd_dtype={
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
            "long_order_id": str,
            "short_order_id": str,
            "long_tracking_no": str,
            "short_tracking_no": str,
            "long_close_at": str,
            "short_close_at": str,
        },
    )

    logger.debug(f"𝄜 to csv: {count}")

    # 根据提取的 'id' 列更新数据库中 up_status 字段
    if ids:
        # 使用 text() 构建查询时，确保 :ids 是一个列表
        update_query = text(
            f"UPDATE {table} SET up_status = :status WHERE id IN ({','.join(map(str, ids))});"
        )
        with engine.connect() as connection:
            with connection.begin():
                result = connection.execute(
                    update_query,
                    {"status": update_status},
                )

                return result.rowcount

    return 0
