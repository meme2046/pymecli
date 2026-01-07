import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from models.response import SuccessResponse

router = APIRouter()


@router.get(
    "/json",
    summary="根据redis.key获取数据",
    response_description="返回json数据",
)
async def json_by_key(
    request: Request,
    key: str = Query(..., description="redis.key"),
):
    value = await request.app.state.redis_client.get(key)

    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in Redis")

    json_data = json.loads(value)

    return SuccessResponse(data=json_data)


@router.get(
    "/plaintext",
    summary="根据redis.key获取数据",
    response_description="返回plaintext数据",
    # response_class=PlainTextResponse,
)
async def plaintext_by_key(
    request: Request,
    key: str = Query(..., description="redis.key"),
):
    r = request.app.state.redis_client
    key_type = await r.type(key)
    print(f"Key type: {key_type}")

    if key_type == "string":  # 或 'string' 取决于客户端
        value = await r.get(key)
        return PlainTextResponse(
            content=value, headers={"Content-Type": "text/plain; charset=utf-8"}
        )
    elif key_type == "hash":
        value = await r.hgetall(key)
    elif key_type == "list":
        value = await r.lrange(key, 0, -1)
    elif key_type == "set":
        value = await r.smembers(key)
    elif key_type == "zset":
        value = await r.zrange(key, 0, -1, withscores=True)
    else:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in Redis")

    return SuccessResponse(data=value)


@router.get(
    "/byset",
    summary="根据redis.key获取数据",
)
async def plaintext_by_set(
    request: Request,
    key: str = Query(..., description="redis.key"),
    cursor: int = Query(0, description="从第几条开始取数据"),
    n: int = Query(10000, description="取多少数据"),
):
    r = request.app.state.redis_client
    key_type = await r.type(f"by_time_{key}")
    print(f"Key type: {key_type}")
    if key_type not in ["zset", "set"]:
        raise HTTPException(
            status_code=404, detail=f"key:<{key}> type not in [zset,set]"
        )

    ids = await r.zrevrange(f"by_time_{key}", cursor, n - 1)
    if not ids:
        return SuccessResponse(data=[])

    pipe = r.pipeline()
    for id in ids:
        pipe.hgetall(f"{key}:{id}")
    value = await pipe.execute()
    filtered_value = [v for v in value if v]

    return SuccessResponse(data=filtered_value)
