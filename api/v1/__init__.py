from fastapi import APIRouter

from api.v1.clash import router as clash_router
from api.v1.redis import router as redis_router

api_router = APIRouter()

api_router.include_router(clash_router, prefix="/clash")
api_router.include_router(redis_router, prefix="/redis")
