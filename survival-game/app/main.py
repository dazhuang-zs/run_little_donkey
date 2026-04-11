"""
FastAPI 主应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.database import engine, Base
from app.routers import auth, game, events

# 创建数据库表（开发环境）
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 包含路由
app.include_router(auth.router, prefix=settings.API_V1_PREFIX + "/auth", tags=["认证"])
app.include_router(game.router, prefix=settings.API_V1_PREFIX + "/game", tags=["游戏"])
app.include_router(events.router, prefix=settings.API_V1_PREFIX + "/events", tags=["事件"])


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "欢迎使用《重生之月薪2000》游戏API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 开发环境下直接运行
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )