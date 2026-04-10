"""
游戏状态模型
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class GameStateBase(BaseModel):
    """游戏状态基础模型"""
    day: int = 1
    time_of_day: str = "morning"
    money: int = 2000
    health: int = 100
    stress: int = 0
    hunger: int = 0
    energy: int = 100
    job_level: int = 1
    job_satisfaction: int = 50
    relationship: int = 50
    is_game_over: bool = False


class GameStateCreate(GameStateBase):
    """创建游戏状态模型"""
    player_id: int

    @field_validator('health', 'stress', 'hunger', 'energy', 'job_satisfaction', 'relationship')
    @classmethod
    def validate_resource_range(cls, v, info):
        """验证资源值范围"""
        field_name = info.field_name
        if field_name in ['health', 'energy']:
            if not 0 <= v <= 100:
                raise ValueError(f'{field_name}必须在0-100之间')
        elif field_name in ['stress', 'hunger']:
            if not 0 <= v <= 100:
                raise ValueError(f'{field_name}必须在0-100之间')
        elif field_name == 'job_satisfaction':
            if not 0 <= v <= 100:
                raise ValueError(f'工作满意度必须在0-100之间')
        elif field_name == 'relationship':
            if not 0 <= v <= 100:
                raise ValueError(f'人际关系必须在0-100之间')
        return v

    @field_validator('money')
    @classmethod
    def validate_money(cls, v):
        """验证金钱值"""
        if v < -10000:  # 允许一定的负债
            raise ValueError('金钱值不能低于-10000')
        return v


class GameStateUpdate(BaseModel):
    """更新游戏状态模型"""
    day: Optional[int] = None
    time_of_day: Optional[str] = None
    money: Optional[int] = None
    health: Optional[int] = None
    stress: Optional[int] = None
    hunger: Optional[int] = None
    energy: Optional[int] = None
    job_level: Optional[int] = None
    job_satisfaction: Optional[int] = None
    relationship: Optional[int] = None
    is_game_over: Optional[bool] = None


class GameStateInDB(GameStateBase):
    """数据库中的游戏状态模型"""
    id: int
    player_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameState(GameStateBase):
    """返回给客户端的游戏状态模型"""
    id: int
    player_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionRequest(BaseModel):
    """执行动作请求模型"""
    action_code: str


class ActionResult(BaseModel):
    """动作执行结果模型"""
    action_name: str
    cost_money: int = 0
    cost_energy: int = 0
    effect_money: int = 0
    effect_health: int = 0
    effect_stress: int = 0
    effect_hunger: int = 0
    effect_job_satisfaction: int = 0
    effect_relationship: int = 0


class ActionResponse(BaseModel):
    """动作执行响应模型"""
    success: bool = True
    message: str = ""
    data: Optional[dict] = None