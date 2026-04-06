"""
动作模型
"""

from pydantic import BaseModel


class ActionBase(BaseModel):
    """动作基础模型"""
    action_code: str
    name: str
    description: Optional[str] = None
    cost_money: int = 0
    cost_energy: int = 0
    effect_health: int = 0
    effect_stress: int = 0
    effect_hunger: int = 0
    effect_job_satisfaction: int = 0
    effect_relationship: int = 0
    cooldown_hours: int = 0
    is_available: bool = True


class ActionCreate(ActionBase):
    """创建动作模型"""
    pass


class ActionInDB(ActionBase):
    """数据库中的动作模型"""
    id: int

    class Config:
        orm_mode = True


class Action(ActionBase):
    """返回给客户端的动作模型"""
    id: int

    class Config:
        orm_mode = True


class PlayerActionBase(BaseModel):
    """玩家动作执行记录基础模型"""
    player_id: int
    game_state_id: int
    action_id: int
    cost_money: int
    cost_energy: int


class PlayerActionCreate(PlayerActionBase):
    """创建玩家动作执行记录模型"""
    pass


class PlayerActionInDB(PlayerActionBase):
    """数据库中的玩家动作执行记录模型"""
    id: int
    executed_at: datetime

    class Config:
        orm_mode = True


from datetime import datetime
from typing import Optional