"""
AI视频解说生成器 - FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

# 创建应用
app = FastAPI(
    title="AI视频解说生成器",
    description="基于AI的视频解说生成服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI视频解说生成器服务运行中"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


# 导入路由
from app.api import videos, scripts, audio, projects

app.include_router(videos.router, prefix="/api/videos", tags=["视频"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["脚本"])
app.include_router(audio.router, prefix="/api/audio", tags=["音频"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)