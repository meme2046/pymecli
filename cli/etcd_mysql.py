"""
MySQL <-> Etcd 数据同步 CLI。

两个子命令:
    mysql2etcd  将 MySQL kvs 表的 k, v 写入 etcd
    etcd2mysql  将 etcd 指定前缀的 key/value 写入 MySQL kvs 表
"""

import logging
import os

import typer
from sqlalchemy import text

from utils.etcd import get_etcd_client
from utils.logger import get_logger
from utils.mysql import get_database_engine

app = typer.Typer(help="MySQL <-> Etcd 数据同步工具")
logger = get_logger(__name__, level=logging.INFO)

DEFAULT_TABLE = "kvs"


@app.command("mysql2etcd")
def mysql_to_etcd(
    prefix: str = typer.Argument(
        "",
        help="MySQL k 列的前缀过滤（空字符串表示全量）",
    ),
    env_path: str = typer.Option(
        ".env",
        "--env",
        "-e",
        help="dotenv 文件路径",
    ),
    table: str = typer.Option(
        DEFAULT_TABLE,
        "--table",
        "-t",
        help="MySQL 表名，包含 k, v 字段",
    ),
    key_col: str = typer.Option(
        "k",
        "--key-col",
        help="MySQL 中作为 etcd key 的列名",
    ),
    val_col: str = typer.Option(
        "v",
        "--val-col",
        help="MySQL 中作为 etcd value 的列名",
    ),
):
    """
    将 MySQL 表中的 k, v 全量同步到 etcd。

    每行记录会以 k 为 key、v 为 value 写入 etcd（覆盖已有值）。
    """
    engine = get_database_engine(env_path)
    etcd = get_etcd_client(env_path)

    count = 0
    with engine.connect() as conn:
        if prefix:
            query = text(
                f"SELECT {key_col}, {val_col} FROM {table} WHERE {key_col} LIKE :p"
            )
            rows = conn.execute(query, {"p": f"{prefix}%"}).fetchall()
        else:
            query = text(f"SELECT {key_col}, {val_col} FROM {table}")
            rows = conn.execute(query).fetchall()

        for row in rows:
            k, v = str(row[0]), str(row[1])
            etcd.put(k, v)
            logger.debug(f"put: {k} -> {v}")
            count += 1

    logger.info(f"✅ 已写入 {count} 条到 etcd")


@app.command("etcd2mysql")
def etcd_to_mysql(
    prefix: str = typer.Argument(
        ...,
        help="etcd key 前缀（空字符串表示全量）",
    ),
    env_path: str = typer.Option(
        ".env",
        "--env",
        "-e",
        help="dotenv 文件路径",
    ),
    table: str = typer.Option(
        DEFAULT_TABLE,
        "--table",
        "-t",
        help="MySQL 表名，包含 k, v 字段",
    ),
    key_col: str = typer.Option(
        "k",
        "--key-col",
        help="MySQL 中作为 key 的列名",
    ),
    val_col: str = typer.Option(
        "v",
        "--val-col",
        help="MySQL 中作为 value 的列名",
    ),
):
    """
    将 etcd 中指定前缀的 key/value 同步到 MySQL。

    如果 k 已存在则更新 v, 不存在则新增。
    """
    engine = get_database_engine(env_path)
    etcd = get_etcd_client(env_path)

    # get_prefix 不支持空前缀，全量时用 get_all
    count = 0
    with engine.connect() as conn:
        iterator = etcd.get_all() if not prefix else etcd.get_prefix(prefix)
        for value, meta in iterator:
            k = meta.key.decode("utf-8")
            v = value.decode("utf-8") if isinstance(value, bytes) else value

            # 检查是否存在
            check_sql = text(
                f"SELECT id FROM {table} WHERE {key_col} = :k LIMIT 1"
            )
            existing = conn.execute(check_sql, {"k": k}).fetchone()

            if existing:
                update_sql = text(
                    f"UPDATE {table} SET {val_col} = :v WHERE {key_col} = :k"
                )
                conn.execute(update_sql, {"v": v, "k": k})
                logger.debug(f"update: {k}")
            else:
                insert_sql = text(
                    f"INSERT INTO {table} ({key_col}, {val_col}) VALUES (:k, :v)"
                )
                conn.execute(insert_sql, {"k": k, "v": v})
                logger.debug(f"insert: {k}")

            count += 1

        conn.commit()

    logger.info(f"✅ 已同步 {count} 条到 MySQL")


if __name__ == "__main__":
    app()
