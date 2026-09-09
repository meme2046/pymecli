import os
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

from utils import logger
from utils.pd import deduplicated, dt_to_timestamp
from utils.pyredis import get_redis_client

# Go go-sql-driver/mysql 专有参数，Python pymysql / SQLAlchemy 不支持
_GO_DSN_PARAMS = {
    "parseTime", "loc", "timeout", "readTimeout", "writeTimeout",
    "allowNativePasswords", "tls", "serverCert", "clientCert",
    "clientKey", "multiStatements", "columnsWithAlias", "interpolateParams"}


def _strip_go_params(query: str) -> str:
    """从 query string 中移除 Go DSN 专有参数"""
    if not query:
        return query
    kept = [(k, v) for k, v in parse_qsl(query) if k not in _GO_DSN_PARAMS]
    return urlencode(kept)


def _to_sqlalchemy_url(dsn: str) -> str:
    """
    将 Go/Node 通用 MySQL DSN 转为 SQLAlchemy URL。

    输入格式(Go go-sql-driver/mysql DSN 或 Node mysql URI):
        root:password@192.168.123.7:3366/bot_tx?charset=utf8mb4&parseTime=True&loc=Local
        root:password@tcp(192.168.123.7:3366)/bot_tx?charset=utf8mb4
        mysql://root:password@192.168.123.7:3306/mydb

    输出格式(SQLAlchemy):
        mysql+pymysql://root:password@192.168.123.7:3366/bot_tx?charset=utf8mb4
    """
    # 如果已经是完整的 scheme:// URL，直接处理
    if "://" in dsn:
        parts = urlsplit(dsn)
        # mysql:// → mysql+pymysql://
        scheme = parts.scheme
        if scheme == "mysql":
            scheme = "mysql+pymysql"
        return urlunsplit((scheme, parts.netloc, parts.path, _strip_go_params(parts.query), ""))

    # Go DSN 格式：[user[:password]@][tcp(]host[:port][)]/db[?params]
    # 去掉 tcp() 包装
    dsn = re.sub(r"tcp\(([^)]+)\)", r"\1", dsn)

    # user:pass@host:port/db?query → mysql+pymysql://user:pass@host:port/db?query
    url = f"mysql+pymysql://{dsn}"
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, _strip_go_params(parts.query), ""))


def get_database_engine(env_path: str = ".env") -> Engine:
    """创建数据库引擎"""
    load_dotenv(env_path)
    dsn = os.getenv(
        "MYSQL_URL",
        "root:@127.0.0.1:3306/?charset=utf8mb4",
    )
    url = _to_sqlalchemy_url(dsn)

    engine = create_engine(url, connect_args={})

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

    return _update_status(engine, table, ids, update_status)


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

        # 转换行数据为字典(处理 NaN 为 None 或空字符串)
        row_dict = row.where(pd.notna(row), "").to_dict()

        # 1. 写入完整数据到 Hash(自动覆盖)
        pipe.hset(key, mapping=row_dict)
        # 2. 写入 ZSet 索引：score = 开仓时间戳(空值用 0 兜底)
        score = row["open_at"]
        if score is None or pd.isna(score):
            score = 0
        pipe.zadd(f"by_time:{key_prefix}", {id: score})
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

    return _update_status(engine, table, ids, update_status)


async def mysql_to_redis(
    engine: Engine,
    key_prefix: str,
    table: str,
    query: str,
    update_status: int,
    d_column_names: list[str],
    pd_dtype: dict | None = None,
    del_column_names: list[str] = ["id", "created_at", "updated_at", "deleted_at"],
) -> int:
    df = pd.read_sql(query, engine, dtype=pd_dtype)
    df["open_at"] = df["open_at"].fillna(df["created_at"])
    ids = df["id"].tolist()
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

    r = get_redis_client()
    pipe = r.pipeline()
    count = 0
    n1, n2 = d_column_names

    for _, row in df.iterrows():
        idx1 = row[n1]
        idx2 = row[n2]
        if not idx1 or not idx2:
            raise ValueError("ERR:id行无效")
        id = f"{idx1}_{idx2}"
        key = f"{key_prefix}:{id}"

        row_dict = row.where(pd.notna(row), "").to_dict()

        pipe.hset(key, mapping=row_dict)
        score = row["open_at"]
        if score is None or pd.isna(score):
            score = 0
        pipe.zadd(f"by_time:{key_prefix}", {id: score})
        count += 1

    await pipe.execute()
    logger.debug(f"🧱 to redis: {count}")

    return _update_status(engine, table, ids, update_status)


def _update_status(engine: Engine, table: str, ids: list, update_status: int) -> int:
    if ids:
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
