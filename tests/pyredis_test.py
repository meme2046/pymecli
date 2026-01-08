import asyncio
import csv
import json
import time
from typing import Any, Awaitable, List, cast

from utils.pyredis import get_redis_client

r = get_redis_client()


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

            pipe.zadd(f"by_time_{key_prefix}", {id: time.time()})

            count += 1

        await pipe.execute()
        print(f"总共写入 {count} 条")


async def get_latest_n(key_prefix="bitget_grid", n=5000) -> List[Any]:
    ids = await r.zrevrange(f"by_time_{key_prefix}", 0, n - 1)
    if not ids:
        return []
    pipe = r.pipeline()
    for id in ids:
        pipe.hgetall(f"{key_prefix}:{id}")
    return await pipe.execute()


async def main(key_prefix: str):
    # csv_to_redis()
    result = await get_latest_n(key_prefix, n=5000)
    print(f"获取到 {len(result)} 条记录")
    print(json.dumps(result))


async def main_test(key: str):
    result = await cast(Awaitable[dict[Any, Any]], r.hgetall(key))
    print(result)


if __name__ == "__main__":
    # csv_to_redis()
    # main()
    # asyncio.run(main("bitget_sf"))
    # result = asyncio.run(main_test("test"))
    asyncio.run(
        csv_to_redis(
            key_prefix="bitget_sf",
            fp="d:/github/meme2046/data/bitget_sf_0.csv",
            id1="spot_order_id",
            id2="futures_order_id",
        )
    )
