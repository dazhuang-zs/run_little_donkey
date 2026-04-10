"""
玩家模型
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class PlayerBase(BaseModel):
    """玩家基础模型"""
    username: str
    email: Optional[EmailStr] = None


class PlayerCreate(PlayerBase):
    """创建玩家模型"""
    password: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        """用户名只能包含字母、数字和下划线"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """密码强度验证"""
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class PlayerUpdate(BaseModel):
    """更新玩家模型"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class PlayerInDB(PlayerBase):
    """数据库中的玩家模型"""
    id: int
    password_hash: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    is_active: bool = True
    total_games_played: int = 0
    best_score: int = 0

    model_config = {"from_attributes": True}


class Player(PlayerBase):
    """返回给客户端的玩家模型"""
    id: int
    created_at: datetime
    last_login_at: Optional[datetime] = None
    is_active: bool
    total_games_played: int
    best_score: int

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: str  # 用户ID
    exp: int  # 过期时间


