"""全局配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """全局配置"""

    APP_NAME: str = "Smart Trip Planner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 腾讯地图 API
    TENCENT_MAP_API_KEY: str = ""
    TENCENT_MAP_BASE_URL: str = "https://apis.map.qq.com"

    # 大模型 API
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # QClaw
    QCLAW_ENABLED: bool = False
    QCLAW_API_KEY: Optional[str] = None
    QCLAW_BASE_URL: str = "https://api.qclaw.com/v1"

    # 缓存
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 86400
    CACHE_MAX_SIZE: int = 2000

    # 算法参数
    MAX_ATTRACTION_PER_DAY: int = 6
    MAX_TRIP_DAYS: int = 7
    ROUTE_OPTIMIZATION_TIMEOUT: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
