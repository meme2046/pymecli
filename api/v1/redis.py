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
    r = request.app.state.redis_client
    key_type = await r.type(key)

    if key_type == "string":  # 或 'string' 取决于客户端
        value = await r.get(key)
        value = json.loads(value)
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
    # print(f"Key type: {key_type}")

    if key_type == "string":  # 或 'string' 取决于客户端
        value = await r.get(key)
        return PlainTextResponse(
            content=value, headers={"Content-Type": "text/plain; charset=utf-8"}
        )
    elif key_type == "none":
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in Redis")
    else:
        raise HTTPException(
            status_code=400, detail=f"key:<{key}>,value type not string"
        )


@router.get(
    "/byset",
    summary="根据redis.key获取数据",
)
async def list_by_set(
    request: Request,
    key: str = Query(..., description="redis.key"),
    cursor: int = Query(0, description="从第几条开始取数据"),
    size: int = Query(5000, description="取多少数据"),
):
    r = request.app.state.redis_client
    key_type = await r.type(f"by_time:{key}")

    if key_type == "none":
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in Redis")

    if key_type not in ["zset", "set"]:
        raise HTTPException(
            status_code=400, detail=f"key:<{key}>,value type not in [zset,set]"
        )

    ids = await r.zrevrange(f"by_time:{key}", cursor, cursor + size - 1)
    if not ids:
        return SuccessResponse(data=[])

    pipe = r.pipeline()
    for id in ids:
        pipe.hgetall(f"{key}:{id}")
    value = await pipe.execute()
    filtered_value = [v for v in value if v]

    return SuccessResponse(data=filtered_value)
