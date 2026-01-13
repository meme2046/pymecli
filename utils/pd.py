import os
from typing import Literal

import pandas as pd
from pandas import DataFrame


def deduplicated(
    file_path: str,
    column_names: list[str],
    keep: Literal["first", "last"] = "last",
    pd_dtype: dict | None = None,
):
    if os.path.exists(file_path):
        existing_df: DataFrame = pd.read_csv(
            file_path, encoding="utf-8", dtype=pd_dtype
        )
        existing_df.drop_duplicates(subset=column_names, keep=keep, inplace=True)
        existing_df.to_csv(file_path, index=False, encoding="utf-8")
        return existing_df


def dt_to_timestamp(dt_series, timezone="Asia/Shanghai"):
    """
    将 datetime64[ns] Series 转为秒级时间戳(int),NaT → None
    """
    # 转为 int64 纳秒，NaT 会变成 -9223372036854775808
    nanos = dt_series.dt.tz_localize(timezone).astype("int64")
    # // 10**9 # 秒 seconds
    # // 10**6 # 毫秒 millis
    # // 10**3 # 微秒 micros
    # 替换 NaT 为 NaN，再转为可空整数
    # millis = (nanos // 10**6).where(nanos != -9223372036854775808, pd.NA)
    millis = (nanos // 10**6).where(nanos > 0, pd.NA)
    return millis.astype("Int64")  # 可空整数类型


def dt_to_str(dt_series):
    """
    将 datetime64[ns] Series 转为字符串,NaT → ""
    """
    return (
        dt_series.dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        .str[:-3]  # 保留3位毫秒：.568
        .fillna("")
    )
