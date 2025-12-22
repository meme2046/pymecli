import os
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from utils.elapsed import timeit
from utils.logger import get_logger
from utils.mysql import get_database_engine
from utils.pd import deduplicated

logger = get_logger(__name__)


@timeit
def main():
    result = deduplicated("./tests/test_0.csv", ["draw"], "last")
    logger.info(result)


def convert_col_to_str(x):
    # 如果是NaN或None，返回空字符串
    if pd.isna(x) or x is None:
        return ""

    # 如果是数字，转换为整数字符串
    if isinstance(x, (int, float)):
        return str(int(x))

    # 如果是字符串但表示数字，也转换为整数字符串
    if isinstance(x, str) and x.replace(".", "", 1).isdigit():
        return str(int(float(x)))

    # 其他情况，直接转为字符串
    return str(x)


@timeit
def pd_str(csv_path: str, columns: list[str]):
    """
    将CSV文件中的指定列转换为字符串类型

    Args:
        csv_path (str): CSV文件路径
        columns (list[str]): 需要转换为字符串的列名列表

    Returns:
        DataFrame: 转换后的DataFrame
    """
    if os.path.exists(csv_path):
        # 读取CSV文件
        df = pd.read_csv(csv_path, encoding="utf-8")

        # 将指定列转换为字符串类型
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_col_to_str)
                df[col] = df[col].astype(str)

        # 保存回CSV文件
        path_obj = Path(csv_path)
        out_fp = str(path_obj.with_name(path_obj.stem + "_c" + path_obj.suffix))
        df.to_csv(out_fp, index=False, encoding="utf-8")

        return df
    else:
        raise FileNotFoundError(f"文件 {csv_path} 不存在")


def pd_db_str(
    csv_path: str,
    env_path: str = ".env",
    table_name: str = "bitget",
    column_name: str = "buy_px",
):
    """
    pd_re 读取csv内容遍历,到mysql查询对应的数据,然后修改csv中的对应值

    :param csv_path: 说明
    :type csv_path: str
    :param env_path: 说明
    :type env_path: str
    """
    engine = get_database_engine(env_path)

    # 读取CSV文件
    df = pd.read_csv(
        csv_path,
        encoding="utf-8",
        dtype={"buy_px": str, "sell_px": str, "fx_order_id": str, "order_id": str},
    )

    # 遍历每一行数据
    for index, row in df.iterrows():
        order_id = row["order_id"]
        client_order_id = row["client_order_id"]

        if not order_id or not client_order_id:
            continue

        # 注意：这里的表名需要替换为实际的表名
        query = f"""
        SELECT `{column_name}`
        FROM `{table_name}`
        WHERE order_id = %s AND client_order_id = %s
        LIMIT 1
        """

        # 执行查询
        result_df = pd.read_sql(
            query,
            engine,
            params=(order_id, client_order_id),
            # dtype={column_name: str},
        )
        v = result_df.iloc[0][column_name]

        if not result_df.empty:
            if str(v) == "None":
                df.loc[cast(int, index), column_name] = ""
            else:
                print(np.format_float_positional(v))
                df.loc[cast(int, index), column_name] = np.format_float_positional(v)

    path_obj = Path(csv_path)
    out_fp = str(path_obj.with_name(path_obj.stem + "_updated" + path_obj.suffix))
    df.to_csv(out_fp, index=False, encoding="utf-8")

    return df


def test():
    columns = ["buy_px", "sell_px"]
    dtype = {col: str for col in columns}
    print(dtype)


if __name__ == "__main__":
    gate_0_fp = "d:/github/meme2046/data/gate_0.csv"
    bitget_0_fp = "d:/github/meme2046/data/bitget_0.csv"
    bitget_0_fp_0 = "d:/github/meme2046/data/bitget_0_c.csv"
    # pd_str(gate_0_fp, ["fx_order_id"])
    pd_db_str(bitget_0_fp, "d:/.env", "bitget", "buy_px")
