import json

from fastapi import APIRouter, HTTPException, Query, Request

from models.response import SuccessResponse

router = APIRouter()


@router.get(
    "/redis",
    summary="根据redis.key获取数据",
    response_description="返回json数据",
)
async def redis(
    request: Request,
    key: str = Query(..., description="redis.key"),
):
    value = await request.app.state.redis_client.get(key)

    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in Redis")

    json_data = json.loads(value)

    return SuccessResponse(data=json_data)
