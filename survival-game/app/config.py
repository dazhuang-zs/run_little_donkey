"""
配置文件
处理环境变量、数据库配置等
"""

import os
from typing import Optional
from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "重生之月薪2000"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7天

    # 数据库配置
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """组装数据库连接URL"""
        if isinstance(v, str):
            return v

        # 默认使用SQLite
        return "sqlite:///./survival_game.db"

    # 游戏配置
    INITIAL_MONEY: int = 2000
    INITIAL_HEALTH: int = 100
    INITIAL_STRESS: int = 0
    INITIAL_HUNGER: int = 0
    INITIAL_ENERGY: int = 100
    INITIAL_JOB_LEVEL: int = 1
    INITIAL_JOB_SATISFACTION: int = 50
    INITIAL_RELATIONSHIP: int = 50

    # 游戏参数
    MAX_DAY: int = 30  # 游戏最大天数
    DAILY_BASIC_EXPENSE: int = 50  # 每日基本开销
    MONTHLY_RENT: int = 800  # 月租金

    # CORS配置
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()