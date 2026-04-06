"""
结局模型
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EndingBase(BaseModel):
    """结局基础模型"""
    ending_code: str
    title: str
    description: str
    condition_type: str  # health, money, stress, etc.
    condition_value: Optional[int] = None
    is_bad_ending: bool = False
    score: int = 0


class EndingCreate(EndingBase):
    """创建结局模型"""
    pass


class EndingInDB(EndingBase):
    """数据库中的结局模型"""
    id: int

    class Config:
        orm_mode = True


class Ending(EndingBase):
    """返回给客户端的结局模型"""
    id: int

    class Config:
        orm_mode = True


class PlayerEndingBase(BaseModel):
    """玩家结局记录基础模型"""
    player_id: int
    game_state_id: int
    ending_id: int
    score: int = 0


class PlayerEndingCreate(PlayerEndingBase):
    """创建玩家结局记录模型"""
    pass


class PlayerEndingInDB(PlayerEndingBase):
    """数据库中的玩家结局记录模型"""
    id: int
    achieved_at: datetime

    class Config:
        orm_mode = True


class LeaderboardEntry(BaseModel):
    """排行榜条目模型"""
    rank: int
    player_id: int
    username: str
    ending_title: str
    score: int
    total_days: int
    achieved_at: datetime


class LeaderboardResponse(BaseModel):
    """排行榜响应模型"""
    success: bool = True
    data: Optional[dict] = None