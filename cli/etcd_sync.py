"""
MySQL / JSON <-> Etcd 数据同步 CLI。

四个子命令:
    mysql2etcd  将 MySQL kvs 表的 k, v 写入 etcd
    etcd2mysql  将 etcd 指定前缀的 key/value 写入 MySQL kvs 表
    etcd2json   将 etcd 指定前缀的 key/value 导出为 JSON 文件
    json2etcd   将 JSON 文件中的 key/value 写入 etcd
"""

import json
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


# ---------------------------------------------------------------------------
# 智能 JSON 转换（etcd ↔ 文件）
# ---------------------------------------------------------------------------

def _try_json_loads(s: str):
    """尝试把字符串当 JSON 解析，成功返回对象，失败返回原字符串。

    只接受以 { / [ 开头的内容，避免把 "123" "true" 这类普通值也误解析。
    """
    s = s.strip()
    if not s or s[0] not in "{[":
        return s
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


def _json_or_str(v) -> str:
    """dict/list → 紧凑 JSON 字符串；其他 → str(v)。"""
    if isinstance(v, (dict, list)):
        # separators=(",", ":") 去掉空格，保持 etcd 里原样
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return str(v)


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

    try:
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
    finally:
        engine.dispose()
        etcd.close()


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

    try:
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
    finally:
        engine.dispose()
        etcd.close()


@app.command("etcd2json")
def etcd_to_json(
    prefix: str = typer.Argument(
        "",
        help="etcd key 前缀（空字符串表示全量）",
    ),
    env_path: str = typer.Option(
        ".env",
        "--env",
        "-e",
        help="dotenv 文件路径",
    ),
    file_path: str = typer.Option(
        ...,
        "--file-path",
        "-f",
        help="输出 JSON 文件路径",
    ),
):
    """将 etcd 中指定前缀的 key/value 导出为 JSON 文件。

    智能转换：如果 etcd value 是 JSON 字符串（以 { 或 [ 开头），
    会自动解析为真正的 JSON 对象写入文件，编辑更方便；
    普通字符串保持原样。
    """
    etcd = get_etcd_client(env_path)

    try:
        data: dict = {}
        iterator = etcd.get_all() if not prefix else etcd.get_prefix(prefix)
        for value, meta in iterator:
            k = meta.key.decode("utf-8")
            raw = value.decode("utf-8") if isinstance(value, bytes) else value
            data[k] = _try_json_loads(raw)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 已导出 {len(data)} 条到 {file_path}")
    except OSError as e:
        logger.error("写入文件失败: %s", e)
        raise typer.Exit(1)
    finally:
        etcd.close()


@app.command("json2etcd")
def json_to_etcd(
    prefix: str = typer.Argument(
        "",
        help="写入 etcd 时给所有 key 加上的前缀（空表示不加）",
    ),
    env_path: str = typer.Option(
        ".env",
        "--env",
        "-e",
        help="dotenv 文件路径",
    ),
    file_path: str = typer.Option(
        ...,
        "--file-path",
        "-f",
        help="输入 JSON 文件路径",
    ),
):
    """将 JSON 文件中的 key/value 写入 etcd。

    智能转换：dict/list 会自动序列化为紧凑 JSON 字符串写入 etcd；
    字符串/数字/布尔保持 str() 转换。
    --prefix 会加到每个 key 前面（如果 key 本身已带该前缀则不重复加）。
    """
    etcd = get_etcd_client(env_path)

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        logger.error("读取文件失败: %s", e)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        logger.error("JSON 解析失败: %s", e)
        raise typer.Exit(1)

    if not isinstance(data, dict):
        logger.error("JSON 顶层必须是对象 (dict)")
        raise typer.Exit(1)

    try:
        count = 0
        for k, v in data.items():
            # 处理前缀：已带则不重复加
            full_key = k
            if prefix and not k.startswith(prefix):
                full_key = prefix.rstrip("/") + "/" + k.lstrip("/")

            etcd.put(full_key, _json_or_str(v))
            logger.debug("put: %s -> %s", full_key, v)
            count += 1

        logger.info(f"✅ 已写入 {count} 条到 etcd")
    finally:
        etcd.close()


if __name__ == "__main__":
    app()
