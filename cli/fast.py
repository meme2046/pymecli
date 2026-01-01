import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
import typer
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.v1 import api_router
from core.clash import ClashConfig, init_generator
from core.config import settings
from models.response import SuccessResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用生命周期的上下文管理器"""
    redis_pool = redis.ConnectionPool(
        host=os.getenv("REDIS_HOST", "192.168.123.7"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD"),
        max_connections=20,  # 根据需要调整最大连接数
        decode_responses=True,
    )
    redis_client = redis.Redis(connection_pool=redis_pool)

    # 启动时
    app.state.redis_client = redis_client
    yield
    # 关闭时
    if redis_client:
        await redis_client.aclose()


typer_app = typer.Typer()


app = FastAPI(
    title=settings.NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

# 注册 v1 版本的所有路由
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议设置具体的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 headers
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "success": False, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # 将错误信息转换为可序列化的格式
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "type": error.get("type"),
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "input": error.get("input"),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": errors,
            "success": False,
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "success": False,
            "data": None,
        },
    )


@app.get("/")
async def root():
    return SuccessResponse(data=f"Welcome to {settings.DESCRIPTION}")


@app.get("/ping", response_class=PlainTextResponse)
async def pingpong():
    return "pong"


@typer_app.command()
def run_app(
    host: str = typer.Argument(
        "0.0.0.0",
        help="fastapi监听的<ip>地址",
    ),
    port: int = typer.Option(
        80,
        "--port",
        help="fastapi监听的端口号",
    ),
    ssl_keyfile: str = typer.Option(
        None,
        "--ssl-keyfile",
        "-sk",
        help="ssl keyfile",
    ),
    ssl_certfile: str = typer.Option(
        None,
        "--ssl-certfile",
        "-sc",
        help="ssl certfile",
    ),
    rule: str = typer.Option(
        "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release",
        "--rule",
        "-r",
        help="clash Rule base URL",
    ),
    my_rule: str = typer.Option(
        "https://raw.githubusercontent.com/meme2046/data/refs/heads/main/clash",
        "--my-rule",
        "-mr",
        help="my clash rule base URL(自定义规则)",
    ),
    proxy: str = typer.Option(
        None,
        "--proxy",
        "-p",
        help="服务器代理,传入则通过代理转换Clash订阅,比如:socks5://127.0.0.1:7890",
    ),
):
    clash_config = ClashConfig(rule, my_rule, proxy)
    init_generator(clash_config)

    uvicorn.run(
        "cli.fast:app",
        host=host,
        port=port,
        reload=False,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
